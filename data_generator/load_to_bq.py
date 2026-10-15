"""
CareFlow BigQuery Loader

Loads a CSV hospital event log into:
    PROJECT.DATASET.raw_ehr_events

Default behaviour:
    WRITE_TRUNCATE - replace the existing table contents.

Use --append to add records instead.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google.api_core.exceptions import NotFound
from google.cloud import bigquery


# ---------------------------------------------------------
# 1. Project paths and configuration
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ENV_FILE = PROJECT_ROOT / ".env"

DEFAULT_INPUT_FILE = PROJECT_ROOT / "data" / "raw_events.csv"

TABLE_NAME = "raw_ehr_events"

REQUIRED_COLUMNS = [
    "case_id",
    "activity",
    "timestamp",
    "department",
    "resource",
]


# ---------------------------------------------------------
# 2. Logging configuration
# ---------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# 3. Explicit BigQuery schema
# ---------------------------------------------------------

BIGQUERY_SCHEMA = [
    bigquery.SchemaField(
        "case_id",
        "STRING",
        mode="REQUIRED",
    ),
    bigquery.SchemaField(
        "activity",
        "STRING",
        mode="REQUIRED",
    ),
    bigquery.SchemaField(
        "timestamp",
        "TIMESTAMP",
        mode="REQUIRED",
    ),
    bigquery.SchemaField(
        "department",
        "STRING",
        mode="NULLABLE",
    ),
    bigquery.SchemaField(
        "resource",
        "STRING",
        mode="NULLABLE",
    ),
]


# ---------------------------------------------------------
# 4. Read and validate the CSV
# ---------------------------------------------------------

def read_event_log(file_path: Path) -> pd.DataFrame:
    """Read the CSV, parse timestamps, and validate columns."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Input CSV does not exist: {file_path}"
        )

    logger.info("Reading input file: %s", file_path)

    dataframe = pd.read_csv(file_path)

    logger.info(
        "Rows read from CSV: %s",
        f"{len(dataframe):,}",
    )

    missing_columns = (
        set(REQUIRED_COLUMNS) - set(dataframe.columns)
    )

    if missing_columns:
        raise ValueError(
            "Input CSV is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    # Keep only the columns required by the BigQuery schema.
    dataframe = dataframe[REQUIRED_COLUMNS].copy()

    # Required identifiers and activities cannot be empty.
    for column in ["case_id", "activity"]:
        dataframe[column] = (
            dataframe[column]
            .astype("string")
            .str.strip()
        )

        if dataframe[column].isna().any():
            raise ValueError(
                f"Column '{column}' contains missing values."
            )

        if dataframe[column].eq("").any():
            raise ValueError(
                f"Column '{column}' contains empty strings."
            )

    # Parse timestamps explicitly.
    # Naive timestamps are interpreted as UTC.
    dataframe["timestamp"] = pd.to_datetime(
        dataframe["timestamp"],
        errors="raise",
        utc=True,
    )

    if dataframe["timestamp"].isna().any():
        raise ValueError(
            "The timestamp column contains missing values."
        )

    # Preserve optional text columns as nullable strings.
    for column in ["department", "resource"]:
        dataframe[column] = dataframe[column].astype("string")

        dataframe[column] = dataframe[column].where(
            dataframe[column].notna(),
            None,
        )

    logger.info(
        "Input validation passed. Rows ready to load: %s",
        f"{len(dataframe):,}",
    )

    return dataframe


# ---------------------------------------------------------
# 5. Load configuration and credentials
# ---------------------------------------------------------

def create_bigquery_client():
    """Create a BigQuery client using .env configuration."""

    load_dotenv(ENV_FILE)

    credentials_path = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS"
    )

    project_id = os.getenv("BQ_PROJECT")
    dataset_id = os.getenv("BQ_DATASET")

    if not credentials_path:
        raise ValueError(
            "GOOGLE_APPLICATION_CREDENTIALS is missing in .env"
        )

    if not project_id:
        raise ValueError(
            "BQ_PROJECT is missing in .env"
        )

    if not dataset_id:
        raise ValueError(
            "BQ_DATASET is missing in .env"
        )

    credentials_file = Path(credentials_path).expanduser()

    if not credentials_file.is_absolute():
        credentials_file = (
            PROJECT_ROOT / credentials_file
        ).resolve()

    if not credentials_file.is_file():
        raise FileNotFoundError(
            "Service account credentials file not found: "
            f"{credentials_file}"
        )

    # Set the environment variable before constructing the client.
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(
        credentials_file
    )

    client = bigquery.Client(project=project_id)

    logger.info(
        "BigQuery project configured: %s",
        project_id,
    )

    return client, project_id, dataset_id


# ---------------------------------------------------------
# 6. Create the dataset if necessary
# ---------------------------------------------------------

def ensure_dataset(
    client: bigquery.Client,
    project_id: str,
    dataset_id: str,
) -> None:
    """Create the dataset if it does not already exist."""

    dataset_reference = (
        f"{project_id}.{dataset_id}"
    )

    try:
        client.get_dataset(dataset_reference)

        logger.info(
            "Dataset already exists: %s",
            dataset_reference,
        )

    except NotFound:
        dataset = bigquery.Dataset(dataset_reference)

        # Use the BigQuery US multi-region by default.
        # Change this if your project uses another location.
        dataset.location = os.getenv(
            "BQ_LOCATION",
            "US",
        )

        client.create_dataset(
            dataset,
            exists_ok=True,
        )

        logger.info(
            "Created dataset: %s",
            dataset_reference,
        )


# ---------------------------------------------------------
# 7. Count rows already present in BigQuery
# ---------------------------------------------------------

def get_table_row_count(
    client: bigquery.Client,
    table_id: str,
) -> int:
    """Return the current row count of the destination table."""

    try:
        client.get_table(table_id)

    except NotFound:
        return 0

    query = f"""
        SELECT COUNT(*) AS row_count
        FROM `{table_id}`
    """

    query_job = client.query(query)

    result = next(iter(query_job.result()))

    return int(result["row_count"])


# ---------------------------------------------------------
# 8. Load the DataFrame into BigQuery
# ---------------------------------------------------------

def load_to_bigquery(
    dataframe: pd.DataFrame,
    client: bigquery.Client,
    project_id: str,
    dataset_id: str,
    append: bool = False,
) -> None:
    """Load the event log and verify the final row count."""

    table_id = (
        f"{project_id}.{dataset_id}.{TABLE_NAME}"
    )

    # Record the destination's row count before loading.
    rows_before = get_table_row_count(
        client,
        table_id,
    )

    logger.info(
        "Rows in BigQuery before load: %s",
        f"{rows_before:,}",
    )

    if append:
        write_disposition = (
            bigquery.WriteDisposition.WRITE_APPEND
        )

        logger.info("Load mode: APPEND")

    else:
        write_disposition = (
            bigquery.WriteDisposition.WRITE_TRUNCATE
        )

        logger.info("Load mode: TRUNCATE / REPLACE")

    job_config = bigquery.LoadJobConfig(
        schema=BIGQUERY_SCHEMA,
        write_disposition=write_disposition,
    )

    logger.info(
        "Starting load into BigQuery table: %s",
        table_id,
    )

    load_job = client.load_table_from_dataframe(
        dataframe,
        table_id,
        job_config=job_config,
    )

    # Wait for the load job to finish and surface errors.
    load_job.result()

    logger.info(
        "BigQuery load job completed: %s",
        load_job.job_id,
    )

    # Count the destination rows after the load.
    rows_after = get_table_row_count(
        client,
        table_id,
    )

    logger.info(
        "Rows in BigQuery after load: %s",
        f"{rows_after:,}",
    )

    logger.info(
        "Rows read from CSV: %s",
        f"{len(dataframe):,}",
    )

    if append:
        expected_rows = rows_before + len(dataframe)

        if rows_after != expected_rows:
            raise RuntimeError(
                "Row-count verification failed. "
                f"Expected {expected_rows:,}, "
                f"found {rows_after:,}."
            )

    else:
        if rows_after != len(dataframe):
            raise RuntimeError(
                "Row-count verification failed. "
                f"Expected {len(dataframe):,}, "
                f"found {rows_after:,}."
            )

    logger.info(
        "SUCCESS: BigQuery row count verified."
    )

    logger.info(
        "Destination table: %s",
        table_id,
    )


# ---------------------------------------------------------
# 9. Command-line interface
# ---------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Load a CareFlow hospital event log into BigQuery."
        )
    )

    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_INPUT_FILE,
        help=(
            "Input CSV path. Defaults to data/raw_events.csv."
        ),
    )

    parser.add_argument(
        "--append",
        action="store_true",
        help=(
            "Append rows instead of replacing the table contents."
        ),
    )

    args = parser.parse_args()

    input_path = args.file

    if not input_path.is_absolute():
        input_path = (
            PROJECT_ROOT / input_path
        ).resolve()

    try:
        dataframe = read_event_log(input_path)

        client, project_id, dataset_id = (
            create_bigquery_client()
        )

        ensure_dataset(
            client,
            project_id,
            dataset_id,
        )

        load_to_bigquery(
            dataframe=dataframe,
            client=client,
            project_id=project_id,
            dataset_id=dataset_id,
            append=args.append,
        )

    except Exception as error:
        logger.error(
            "BigQuery load failed: %s",
            error,
        )

        sys.exit(1)


if __name__ == "__main__":
    main()


import argparse
import logging
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery


# Project directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

REQUIRED_COLUMNS = [
    "case_id",
    "activity",
    "timestamp",
    "department",
    "resource",
]

BQ_SCHEMA = [
    bigquery.SchemaField("case_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("activity", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("department", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("resource", "STRING", mode="NULLABLE"),
]


def get_configuration():
    """Load configuration from the project's .env file."""
    load_dotenv(PROJECT_ROOT / ".env")

    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    project_id = os.getenv("BQ_PROJECT")
    dataset_id = os.getenv("BQ_DATASET")
    location = os.getenv("BQ_LOCATION", "US")

    if not credentials_path or not project_id or not dataset_id:
        raise ValueError(
            "Set GOOGLE_APPLICATION_CREDENTIALS, BQ_PROJECT, "
            "and BQ_DATASET in the project's .env file."
        )

    # Expand Windows paths and environment variables.
    credentials_path = os.path.expandvars(
        os.path.expanduser(credentials_path)
    )

    if not Path(credentials_path).is_file():
        raise FileNotFoundError(
            f"Service-account JSON file not found: {credentials_path}"
        )

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

    return project_id, dataset_id, location


def load_csv(file_path):
    """Read the CSV and validate its required columns and timestamps."""
    if not file_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    df = pd.read_csv(file_path)

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"CSV is missing required columns: {missing_columns}"
        )

    if df.empty:
        raise ValueError("The CSV contains no rows.")

    for column in ["case_id", "activity"]:
        if df[column].isna().any():
            raise ValueError(
                f"Required column '{column}' contains missing values."
            )

    # Parse timestamps explicitly. Naive timestamps are treated as UTC.
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="raise",
        utc=True,
    )

    # Convert pandas timestamps into Python datetime objects for BigQuery.
    df["timestamp"] = df["timestamp"].dt.to_pydatetime()

    logging.info("CSV file: %s", file_path)
    logging.info("Rows read from CSV: %s", len(df))

    return df


def ensure_dataset(client, project_id, dataset_id, location):
    """Create the dataset if it does not exist."""
    dataset_ref = f"{project_id}.{dataset_id}"

    try:
        client.get_dataset(dataset_ref)
        logging.info("BigQuery dataset already exists: %s", dataset_ref)
    except Exception as exc:
        # Only create the dataset if BigQuery confirms it is absent.
        from google.api_core.exceptions import NotFound

        if not isinstance(exc, NotFound):
            raise

        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = location
        client.create_dataset(dataset, exists_ok=True)
        logging.info("Created BigQuery dataset: %s", dataset_ref)


def get_row_count(client, table_id):
    """Return the number of rows currently in the target table."""
    try:
        query = f"SELECT COUNT(*) AS row_count FROM `{table_id}`"
        result = client.query(query).result()
        return next(iter(result)).row_count
    except Exception as exc:
        from google.api_core.exceptions import NotFound

        if isinstance(exc, NotFound):
            return 0
        raise


def upload_dataframe(client, df, table_id, append=False):
    """Upload rows using an explicit schema and selected write mode."""
    write_mode = (
        bigquery.WriteDisposition.WRITE_APPEND
        if append
        else bigquery.WriteDisposition.WRITE_TRUNCATE
    )

    job_config = bigquery.LoadJobConfig(
        schema=BQ_SCHEMA,
        write_disposition=write_mode,
        source_format=bigquery.SourceFormat.PARQUET,
    )

    logging.info("Target table: %s", table_id)
    logging.info("Write mode: %s", write_mode)

    load_job = client.load_table_from_dataframe(
        df,
        table_id,
        job_config=job_config,
    )

    load_job.result()

    logging.info("BigQuery load job completed: %s", load_job.job_id)


def main():
    parser = argparse.ArgumentParser(
        description="Load CareFlow event-log CSV data into BigQuery."
    )

    parser.add_argument(
        "--file",
        default="data/raw_events.csv",
        help=(
            "Path to the CSV file, relative to the project directory "
            "unless an absolute path is provided."
        ),
    )

    parser.add_argument(
        "--append",
        action="store_true",
        help="Append rows instead of replacing the table.",
    )

    args = parser.parse_args()

    try:
        project_id, dataset_id, location = get_configuration()

        file_path = Path(args.file)
        if not file_path.is_absolute():
            file_path = PROJECT_ROOT / file_path

        df = load_csv(file_path)

        client = bigquery.Client(project=project_id)

        ensure_dataset(
            client,
            project_id,
            dataset_id,
            location,
        )

        table_id = f"{project_id}.{dataset_id}.raw_ehr_events"

        rows_before = get_row_count(client, table_id)
        logging.info("Rows in BigQuery before upload: %s", rows_before)

        upload_dataframe(
            client,
            df,
            table_id,
            append=args.append,
        )

        rows_after = get_row_count(client, table_id)
        logging.info("Rows in BigQuery after upload: %s", rows_after)
        logging.info("Rows read from CSV: %s", len(df))

        logging.info("BigQuery upload and verification completed.")

    except Exception:
        logging.exception("BigQuery upload failed.")
        raise


if __name__ == "__main__":
    main()

