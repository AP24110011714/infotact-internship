import argparse
import logging
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery
from google.api_core.exceptions import NotFound


# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# Explicit BigQuery schema
SCHEMA = [
    bigquery.SchemaField("case_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("activity", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("department", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("resource", "STRING", mode="NULLABLE"),
]

REQUIRED_COLUMNS = [
    "case_id",
    "activity",
    "timestamp",
    "department",
    "resource",
]


def load_configuration():
    """Read Google Cloud settings from .env."""
    load_dotenv(PROJECT_ROOT / ".env")

    credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    project_id = os.getenv("BQ_PROJECT")
    dataset_id = os.getenv("BQ_DATASET")
    location = os.getenv("BQ_LOCATION", "US")

    if not credentials or not project_id or not dataset_id:
        raise ValueError(
            "Configure GOOGLE_APPLICATION_CREDENTIALS, "
            "BQ_PROJECT, and BQ_DATASET in .env."
        )

    credentials = os.path.expandvars(
        os.path.expanduser(credentials)
    )

    if not Path(credentials).is_file():
        raise FileNotFoundError(
            f"Credentials file not found: {credentials}"
        )

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials

    logging.info("Google Cloud configuration loaded.")
    logging.info("Project ID: %s", project_id)
    logging.info("Dataset ID: %s", dataset_id)

    return project_id, dataset_id, location


def read_csv(file_path):
    """Read and validate the hospital event-log CSV."""
    if not file_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    df = pd.read_csv(file_path)

    missing = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required CSV columns: {missing}"
        )

    if df.empty:
        raise ValueError("The CSV contains no rows.")

    for column in ["case_id", "activity", "timestamp"]:
        if df[column].isna().any():
            raise ValueError(
                f"Required column '{column}' contains missing values."
            )

    # Parse timestamps and treat timezone-naive values as UTC.
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="raise",
        utc=True,
    )

    logging.info("CSV loaded: %s", file_path)
    logging.info("Rows read from CSV: %d", len(df))

    return df


def create_dataset_if_missing(
    client, project_id, dataset_id, location
):
    """Create the BigQuery dataset if it does not exist."""
    dataset_ref = f"{project_id}.{dataset_id}"

    try:
        client.get_dataset(dataset_ref)
        logging.info("Dataset already exists: %s", dataset_ref)

    except NotFound:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = location

        client.create_dataset(dataset, exists_ok=True)

        logging.info("Created dataset: %s", dataset_ref)


def count_table_rows(client, table_id):
    """Return the current table row count, or zero if absent."""
    try:
        client.get_table(table_id)

    except NotFound:
        return 0

    query = f"""
        SELECT COUNT(*) AS row_count
        FROM `{table_id}`
    """

    result = client.query(query).result()
    return next(iter(result)).row_count


def upload_to_bigquery(client, df, table_id, append=False):
    """Upload the DataFrame with an explicit schema."""
    if append:
        write_disposition = (
            bigquery.WriteDisposition.WRITE_APPEND
        )
    else:
        write_disposition = (
            bigquery.WriteDisposition.WRITE_TRUNCATE
        )

    job_config = bigquery.LoadJobConfig(
        schema=SCHEMA,
        write_disposition=write_disposition,
    )

    logging.info("Target table: %s", table_id)
    logging.info("Write mode: %s", write_disposition)

    job = client.load_table_from_dataframe(
        df,
        table_id,
        job_config=job_config,
    )

    job.result()

    logging.info("Upload job completed: %s", job.job_id)


def main():
    parser = argparse.ArgumentParser(
        description="Upload CareFlow event logs to BigQuery."
    )

    parser.add_argument(
        "--file",
        default="data/raw_events.csv",
        help="CSV file path relative to the project root.",
    )

    parser.add_argument(
        "--append",
        action="store_true",
        help="Append rows instead of replacing existing data.",
    )

    args = parser.parse_args()

    project_id, dataset_id, location = load_configuration()

    file_path = Path(args.file)

    if not file_path.is_absolute():
        file_path = PROJECT_ROOT / file_path

    df = read_csv(file_path)

    client = bigquery.Client(project=project_id)

    create_dataset_if_missing(
        client,
        project_id,
        dataset_id,
        location,
    )

    table_id = (
        f"{project_id}.{dataset_id}.raw_ehr_events"
    )

    rows_before = count_table_rows(client, table_id)
    logging.info("Rows before upload: %d", rows_before)

    upload_to_bigquery(
        client,
        df,
        table_id,
        append=args.append,
    )

    rows_after = count_table_rows(client, table_id)

    logging.info("Rows in CSV: %d", len(df))
    logging.info("Rows after upload: %d", rows_after)
    logging.info("BigQuery upload completed successfully.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.exception("BigQuery upload failed.")
        raise