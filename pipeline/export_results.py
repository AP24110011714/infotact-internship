"""
CareFlow Results Exporter

Reads the dbt mart tables from BigQuery:
    - transition_times
    - loopbacks
    - kpi_summary

Exports:
    1. Individual CSV copies to outputs/
    2. Combined careflow_summary CSV to outputs/
    3. Combined careflow_summary table to BigQuery

Configuration is loaded from the project's .env file.

The expected source-table columns are documented in
EXPECTED_COLUMNS. These should be checked against the
actual Member 2 dbt models before final integration.
"""

import logging
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google.api_core.exceptions import NotFound
from google.cloud import bigquery


# =========================================================
# 1. Project paths and configuration
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

OUTPUT_DIR = PROJECT_ROOT / "outputs"

TRANSITION_TABLE = "transition_times"
LOOPBACK_TABLE = "loopbacks"
KPI_TABLE = "kpi_summary"
SUMMARY_TABLE = "careflow_summary"


# =========================================================
# 2. SQL constants
# =========================================================

SQL_TRANSITION_TIMES = """
SELECT *
FROM `{project_id}.{dataset_id}.transition_times`
"""

SQL_LOOPBACKS = """
SELECT *
FROM `{project_id}.{dataset_id}.loopbacks`
"""

SQL_KPI_SUMMARY = """
SELECT *
FROM `{project_id}.{dataset_id}.kpi_summary`
"""


# =========================================================
# 2A. Expected source-table columns
# =========================================================
#
# IMPORTANT:
# These are the columns currently assumed by the
# Member 1 export contract.
#
# They must be checked against Member 2's actual dbt
# models before the final integration.
#
# The exporter will warn about missing columns but will
# continue processing the available data.
# =========================================================

EXPECTED_COLUMNS = {
    TRANSITION_TABLE: [
        "from_activity",
        "to_activity",
        "transition_count",
        "avg_wait_minutes",
    ],
    LOOPBACK_TABLE: [
        "case_id",
        "from_activity",
        "to_activity",
        "loop_count",
    ],
    KPI_TABLE: [
        "total_cases",
        "total_events",
        "avg_case_duration_minutes",
        "avg_wait_minutes",
        "loopback_rate",
    ],
}


# =========================================================
# 3. Logging configuration
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


# =========================================================
# 4. BigQuery client
# =========================================================

def create_bigquery_client():
    """Create a BigQuery client using the existing .env configuration."""

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

    credentials_file = Path(
        credentials_path
    ).expanduser()

    if not credentials_file.is_absolute():
        credentials_file = (
            PROJECT_ROOT / credentials_file
        ).resolve()

    if not credentials_file.is_file():
        raise FileNotFoundError(
            "Service account credentials file not found: "
            f"{credentials_file}"
        )

    os.environ[
        "GOOGLE_APPLICATION_CREDENTIALS"
    ] = str(credentials_file)

    client = bigquery.Client(
        project=project_id
    )

    logger.info(
        "BigQuery project configured: %s",
        project_id,
    )

    logger.info(
        "BigQuery dataset configured: %s",
        dataset_id,
    )

    return client, project_id, dataset_id


# =========================================================
# 5. Check source table
# =========================================================

def table_exists(
    client: bigquery.Client,
    project_id: str,
    dataset_id: str,
    table_name: str,
) -> bool:
    """Return True when a BigQuery table exists."""

    table_id = (
        f"{project_id}.{dataset_id}.{table_name}"
    )

    try:
        client.get_table(table_id)
        return True

    except NotFound:
        return False


# =========================================================
# 5A. Validate source-table columns
# =========================================================

def validate_columns(
    dataframe: pd.DataFrame,
    table_name: str,
) -> bool:
    """
    Check whether the source table contains the expected columns.

    Missing columns generate a warning but do not stop the export.
    """

    expected = EXPECTED_COLUMNS.get(
        table_name,
        [],
    )

    if not expected:
        logger.warning(
            "No expected column definition found for '%s'.",
            table_name,
        )

        return True

    actual_columns = list(
        dataframe.columns
    )

    logger.info(
        "Columns found in %s: %s",
        table_name,
        actual_columns,
    )

    missing_columns = [
        column
        for column in expected
        if column not in actual_columns
    ]

    if missing_columns:
        logger.warning(
            "Source table '%s' is missing expected columns: %s",
            table_name,
            missing_columns,
        )

        return False

    logger.info(
        "Column validation passed for '%s'.",
        table_name,
    )

    return True


# =========================================================
# 6. Read source table
# =========================================================

def read_source_table(
    client: bigquery.Client,
    project_id: str,
    dataset_id: str,
    table_name: str,
    sql_template: str,
):
    """
    Read a source mart table from BigQuery.

    Returns:
        DataFrame when the table exists and can be read.
        None when the table is missing or cannot be read.
    """

    logger.info(
        "Checking source table: %s",
        table_name,
    )

    if not table_exists(
        client,
        project_id,
        dataset_id,
        table_name,
    ):
        logger.warning(
            "Source table '%s' is missing. "
            "Skipping this table.",
            table_name,
        )

        return None

    query = sql_template.format(
        project_id=project_id,
        dataset_id=dataset_id,
    )

    logger.info(
        "Reading source table: %s",
        table_name,
    )

    try:
        dataframe = client.query(
            query
        ).to_dataframe()

    except Exception as error:
        logger.error(
            "Failed to read '%s': %s",
            table_name,
            error,
        )

        return None

    logger.info(
        "Rows loaded from %s: %s",
        table_name,
        f"{len(dataframe):,}",
    )

    validate_columns(
        dataframe,
        table_name,
    )

    return dataframe


# =========================================================
# 7. Export DataFrame to CSV
# =========================================================

def export_csv(
    dataframe: pd.DataFrame,
    filename: str,
) -> None:
    """Write a DataFrame to the outputs directory."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = OUTPUT_DIR / filename

    dataframe.to_csv(
        output_file,
        index=False,
    )

    logger.info(
        "CSV exported: %s | rows=%s",
        output_file,
        f"{len(dataframe):,}",
    )


# =========================================================
# 8. Combine mart results
# =========================================================

def create_careflow_summary(
    transition_times,
    loopbacks,
    kpi_summary,
):
    """
    Combine available mart tables into one dashboard summary.

    A source_table column identifies the originating mart.
    """

    frames = []

    if transition_times is not None:
        dataframe = transition_times.copy()

        dataframe["source_table"] = (
            TRANSITION_TABLE
        )

        frames.append(dataframe)

    if loopbacks is not None:
        dataframe = loopbacks.copy()

        dataframe["source_table"] = (
            LOOPBACK_TABLE
        )

        frames.append(dataframe)

    if kpi_summary is not None:
        dataframe = kpi_summary.copy()

        dataframe["source_table"] = (
            KPI_TABLE
        )

        frames.append(dataframe)

    if not frames:
        logger.warning(
            "No source tables were available. "
            "careflow_summary will not be created."
        )

        return None

    combined = pd.concat(
        frames,
        ignore_index=True,
        sort=False,
    )

    logger.info(
        "Combined careflow_summary rows: %s",
        f"{len(combined):,}",
    )

    return combined


# =========================================================
# 9. Write summary to BigQuery
# =========================================================

def write_summary_to_bigquery(
    client: bigquery.Client,
    project_id: str,
    dataset_id: str,
    dataframe: pd.DataFrame,
) -> None:
    """Write the combined summary table to BigQuery."""

    table_id = (
        f"{project_id}.{dataset_id}.{SUMMARY_TABLE}"
    )

    logger.info(
        "Writing careflow_summary to BigQuery: %s",
        table_id,
    )

    rows_before = 0

    try:
        existing_table = client.get_table(
            table_id
        )

        query = f"""
        SELECT COUNT(*) AS row_count
        FROM `{table_id}`
        """

        result = next(
            iter(
                client.query(query).result()
            )
        )

        rows_before = int(
            result["row_count"]
        )

        logger.info(
            "Rows already in careflow_summary: %s",
            f"{rows_before:,}",
        )

    except NotFound:
        logger.info(
            "careflow_summary does not exist yet. "
            "It will be created."
        )

    job_config = bigquery.LoadJobConfig(
        write_disposition=(
            bigquery.WriteDisposition.WRITE_TRUNCATE
        )
    )

    load_job = client.load_table_from_dataframe(
        dataframe,
        table_id,
        job_config=job_config,
    )

    load_job.result()

    logger.info(
        "BigQuery write completed: %s",
        load_job.job_id,
    )

    rows_after = 0

    query = f"""
    SELECT COUNT(*) AS row_count
    FROM `{table_id}`
    """

    result = next(
        iter(
            client.query(query).result()
        )
    )

    rows_after = int(
        result["row_count"]
    )

    logger.info(
        "Rows written to careflow_summary: %s",
        f"{rows_after:,}",
    )

    if rows_after != len(dataframe):
        raise RuntimeError(
            "careflow_summary row-count verification failed. "
            f"Expected {len(dataframe):,}, "
            f"found {rows_after:,}."
        )

    logger.info(
        "SUCCESS: careflow_summary row count verified."
    )


# =========================================================
# 10. Main
# =========================================================

def main():
    logger.info("=" * 60)
    logger.info("CareFlow Results Export")
    logger.info("=" * 60)

    try:
        client, project_id, dataset_id = (
            create_bigquery_client()
        )

        # -------------------------------------------------
        # Read transition_times
        # -------------------------------------------------

        transition_times = read_source_table(
            client=client,
            project_id=project_id,
            dataset_id=dataset_id,
            table_name=TRANSITION_TABLE,
            sql_template=SQL_TRANSITION_TIMES,
        )

        # -------------------------------------------------
        # Read loopbacks
        # -------------------------------------------------

        loopbacks = read_source_table(
            client=client,
            project_id=project_id,
            dataset_id=dataset_id,
            table_name=LOOPBACK_TABLE,
            sql_template=SQL_LOOPBACKS,
        )

        # -------------------------------------------------
        # Read kpi_summary
        # -------------------------------------------------

        kpi_summary = read_source_table(
            client=client,
            project_id=project_id,
            dataset_id=dataset_id,
            table_name=KPI_TABLE,
            sql_template=SQL_KPI_SUMMARY,
        )

        # -------------------------------------------------
        # Export individual CSV files
        # -------------------------------------------------

        if transition_times is not None:
            export_csv(
                transition_times,
                "transition_times.csv",
            )

        if loopbacks is not None:
            export_csv(
                loopbacks,
                "loopbacks.csv",
            )

        if kpi_summary is not None:
            export_csv(
                kpi_summary,
                "kpi_summary.csv",
            )

        # -------------------------------------------------
        # Create combined summary
        # -------------------------------------------------

        careflow_summary = create_careflow_summary(
            transition_times=transition_times,
            loopbacks=loopbacks,
            kpi_summary=kpi_summary,
        )

        if careflow_summary is None:
            logger.warning(
                "No data available for careflow_summary."
            )

            return 0

        # -------------------------------------------------
        # Export combined CSV
        # -------------------------------------------------

        export_csv(
            careflow_summary,
            "careflow_summary.csv",
        )

        # -------------------------------------------------
        # Write combined table to BigQuery
        # -------------------------------------------------

        write_summary_to_bigquery(
            client=client,
            project_id=project_id,
            dataset_id=dataset_id,
            dataframe=careflow_summary,
        )

    except Exception as error:
        logger.error(
            "CareFlow results export failed: %s",
            error,
        )

        return 1

    logger.info("=" * 60)
    logger.info(
        "CareFlow Results Export Completed Successfully"
    )
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())