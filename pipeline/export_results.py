
"""
CareFlow Task 4: Export BigQuery mart results.

Reads:
    transition_times
    loopbacks
    kpi_summary

Creates:
    outputs/transition_times.csv
    outputs/loopbacks.csv
    outputs/kpi_summary.csv
    outputs/careflow_summary.csv
    BigQuery table: careflow_summary

Configuration is loaded from the project's .env file.
"""

import logging
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google.api_core.exceptions import (
    BadRequest,
    Forbidden,
    GoogleAPIError,
    NotFound,
)
from google.cloud import bigquery


# ============================================================
# 1. PROJECT PATHS AND CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

load_dotenv(ENV_FILE, override=True)

BQ_PROJECT = os.getenv("BQ_PROJECT", "").strip()
BQ_DATASET = os.getenv("BQ_DATASET", "").strip()
BQ_LOCATION = os.getenv("BQ_LOCATION", "US").strip() or "US"

SOURCE_TABLES = (
    "transition_times",
    "loopbacks",
    "kpi_summary",
)

SUMMARY_TABLE = "careflow_summary"


# ============================================================
# 2. SQL CONSTANTS
# Keep all BigQuery SQL statements in this section.
# ============================================================

TRANSITION_TIMES_SQL = """
SELECT *
FROM `{project}.{dataset}.transition_times`
"""

LOOPBACKS_SQL = """
SELECT *
FROM `{project}.{dataset}.loopbacks`
"""

KPI_SUMMARY_SQL = """
SELECT *
FROM `{project}.{dataset}.kpi_summary`
"""

SQL_BY_TABLE = {
    "transition_times": TRANSITION_TIMES_SQL,
    "loopbacks": LOOPBACKS_SQL,
    "kpi_summary": KPI_SUMMARY_SQL,
}


# ============================================================
# 3. LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("careflow_export")


# ============================================================
# 4. BIGQUERY CLIENT
# ============================================================

def create_bigquery_client():
    """Create an authenticated BigQuery client using .env settings."""

    if not ENV_FILE.exists():
        raise FileNotFoundError(
            f".env file was not found: {ENV_FILE}"
        )

    if not BQ_PROJECT:
        raise ValueError(
            "BQ_PROJECT is missing from the .env file."
        )

    if not BQ_DATASET:
        raise ValueError(
            "BQ_DATASET is missing from the .env file."
        )

    credentials_path = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS", ""
    ).strip()

    if credentials_path:
        credential_file = Path(credentials_path)

        if not credential_file.is_absolute():
            credential_file = PROJECT_ROOT / credential_file

        if not credential_file.is_file():
            raise FileNotFoundError(
                "The credentials file configured in "
                "GOOGLE_APPLICATION_CREDENTIALS was not found. "
                "Check its path in .env."
            )

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(
            credential_file.resolve()
        )

    logger.info("BigQuery project: %s", BQ_PROJECT)
    logger.info("BigQuery dataset: %s", BQ_DATASET)
    logger.info("BigQuery location: %s", BQ_LOCATION)

    return bigquery.Client(
        project=BQ_PROJECT,
        location=BQ_LOCATION,
    )


# ============================================================
# 5. READ SOURCE TABLES
# ============================================================

def read_source_table(client, table_name):
    """
    Read a source table into a DataFrame.

    Returns None when the table is missing or cannot be read.
    Source column names are preserved; they are not assumed.
    """

    table_id = f"{BQ_PROJECT}.{BQ_DATASET}.{table_name}"

    sql = SQL_BY_TABLE[table_name].format(
        project=BQ_PROJECT,
        dataset=BQ_DATASET,
    )

    logger.info("Reading source table: %s", table_id)

    try:
        # Confirm that the individual table exists.
        client.get_table(table_id)

        dataframe = client.query(
            sql,
            location=BQ_LOCATION,
        ).to_dataframe()

        logger.info(
            "Read %s rows and %s columns from %s",
            len(dataframe),
            len(dataframe.columns),
            table_name,
        )

        if dataframe.empty:
            logger.warning(
                "Source table '%s' exists but contains no rows.",
                table_name,
            )

        logger.info(
            "Columns in %s: %s",
            table_name,
            list(dataframe.columns),
        )

        return dataframe

    except NotFound:
        logger.warning(
            "Source table '%s' was not found. Skipping it.",
            table_id,
        )
        return None

    except Forbidden:
        logger.error(
            "Permission denied while reading '%s'. "
            "Check BigQuery permissions.",
            table_id,
        )
        return None

    except (BadRequest, GoogleAPIError) as error:
        logger.error(
            "Could not read '%s': %s",
            table_id,
            error,
        )
        return None


# ============================================================
# 6. EXPORT INDIVIDUAL CSV FILES
# ============================================================

def export_csv(dataframe, filename):
    """Write a DataFrame to outputs/ and log the row count."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / filename

    try:
        dataframe.to_csv(output_path, index=False)

        logger.info(
            "Exported %s rows to %s",
            len(dataframe),
            output_path,
        )

        return True

    except (OSError, ValueError) as error:
        logger.error(
            "Failed to export %s: %s",
            output_path,
            error,
        )
        return False


# ============================================================
# 7. COMBINE THE AVAILABLE SOURCE TABLES
# ============================================================

def create_careflow_summary(source_data):
    """
    Combine available source DataFrames.

    Adds source_table so dashboard users can identify
    the mart each row came from.

    Different source schemas are preserved as separate columns.
    """

    available_frames = []

    for table_name in SOURCE_TABLES:
        dataframe = source_data.get(table_name)

        if dataframe is None:
            continue

        if dataframe.empty:
            logger.warning(
                "Not adding empty table '%s' to the summary.",
                table_name,
            )
            continue

        frame = dataframe.copy()
        frame.insert(0, "source_table", table_name)
        available_frames.append(frame)

    if not available_frames:
        logger.warning(
            "No source data is available. "
            "The combined summary will not be created."
        )
        return None

    summary = pd.concat(
        available_frames,
        ignore_index=True,
        sort=False,
    )

    logger.info(
        "Combined summary contains %s rows and %s columns.",
        len(summary),
        len(summary.columns),
    )

    return summary


# ============================================================
# 8. WRITE COMBINED SUMMARY TO BIGQUERY
# ============================================================

def write_summary_to_bigquery(client, dataframe):
    """Write careflow_summary to BigQuery, replacing old results."""

    table_id = f"{BQ_PROJECT}.{BQ_DATASET}.{SUMMARY_TABLE}"

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect=True,
    )

    try:
        logger.info(
            "Writing %s rows to BigQuery table %s",
            len(dataframe),
            table_id,
        )

        load_job = client.load_table_from_dataframe(
            dataframe,
            table_id,
            job_config=job_config,
            location=BQ_LOCATION,
        )

        load_job.result()

        destination = client.get_table(table_id)

        logger.info(
            "BigQuery export complete: %s rows in %s",
            destination.num_rows,
            table_id,
        )

        if destination.num_rows != len(dataframe):
            logger.warning(
                "Expected %s rows, but BigQuery reports %s rows.",
                len(dataframe),
                destination.num_rows,
            )

        return True

    except Forbidden:
        logger.error(
            "Permission denied while writing %s. "
            "Check dataset and BigQuery job permissions.",
            table_id,
        )
        return False

    except NotFound:
        logger.error(
            "The destination dataset was not found. "
            "Check BQ_PROJECT and BQ_DATASET in .env. "
            "Create the dataset only after verifying the project."
        )
        return False

    except (BadRequest, GoogleAPIError, ValueError) as error:
        logger.error(
            "Failed to write BigQuery summary: %s",
            error,
        )
        return False


# ============================================================
# 9. MAIN PIPELINE
# ============================================================

def main():
    logger.info("=" * 60)
    logger.info("CareFlow Results Export")
    logger.info("=" * 60)

    try:
        client = create_bigquery_client()

    except (ValueError, FileNotFoundError, GoogleAPIError) as error:
        logger.error("BigQuery client setup failed: %s", error)
        return 1

    dataset_id = f"{BQ_PROJECT}.{BQ_DATASET}"

    try:
        client.get_dataset(dataset_id)

    except NotFound:
        logger.error(
            "Dataset '%s' does not exist or is not accessible. "
            "Verify the project and dataset in Google Cloud Console.",
            dataset_id,
        )
        return 1

    except (Forbidden, GoogleAPIError) as error:
        logger.error(
            "Could not access dataset '%s': %s",
            dataset_id,
            error,
        )
        return 1

    source_data = {}

    # Read each source table and export its individual CSV.
    for table_name in SOURCE_TABLES:
        dataframe = read_source_table(client, table_name)
        source_data[table_name] = dataframe

        if dataframe is not None:
            export_csv(
                dataframe,
                f"{table_name}.csv",
            )

    # Create the combined summary from available source data.
    summary = create_careflow_summary(source_data)

    if summary is None:
        logger.warning(
            "No careflow_summary CSV or BigQuery table was created."
        )
        logger.info("Export finished with no available source data.")
        return 0

    csv_success = export_csv(
        summary,
        f"{SUMMARY_TABLE}.csv",
    )

    bq_success = write_summary_to_bigquery(
        client,
        summary,
    )

    if not csv_success or not bq_success:
        logger.error(
            "Export finished with one or more output failures."
        )
        return 1

    logger.info("=" * 60)
    logger.info("CareFlow export completed successfully.")
    logger.info("Total summary rows: %s", len(summary))
    logger.info("CSV output directory: %s", OUTPUT_DIR)
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
