
import os
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import bigquery

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

PROJECT = os.getenv("BQ_PROJECT")
DATASET = os.getenv("BQ_DATASET")
LOCATION = os.getenv("BQ_LOCATION", "US")

SQL_FILE = PROJECT_ROOT / "sql" / "create_careflow_marts.sql"

if not PROJECT or not DATASET:
    raise ValueError("BQ_PROJECT or BQ_DATASET is missing in .env")

if not SQL_FILE.exists():
    raise FileNotFoundError(f"SQL file not found: {SQL_FILE}")

client = bigquery.Client(
    project=PROJECT,
    location=LOCATION
)

print("Project:", PROJECT)
print("Dataset:", DATASET)
print("Reading SQL file...")

sql = SQL_FILE.read_text(encoding="utf-8")

print("Executing CareFlow mart creation SQL...")

job = client.query(
    sql,
    location=LOCATION
)

job.result()

print("\nSQL execution completed.")

tables = [
    "transition_times",
    "loopbacks",
    "kpi_summary"
]

print("\nVERIFYING CREATED TABLES:")

for name in tables:
    table_id = f"{PROJECT}.{DATASET}.{name}"

    try:
        table = client.get_table(table_id)
        print(f"SUCCESS: {name} | Rows: {table.num_rows}")
    except Exception as error:
        print(f"FAILED: {name} | {error}")

print("\nMart creation process finished.")
