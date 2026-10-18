import argparse
import subprocess
import sys
import time
from pathlib import Path


# =========================================================
# CAREFLOW PIPELINE CONFIGURATION
# =========================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

GENERATE_SCRIPT = ROOT_DIR / "scripts" / "generate_event_log.py"
LOAD_SCRIPT = ROOT_DIR / "data_generator" / "load_to_bq.py"

DBT_DIR = ROOT_DIR / "dbt_project"

MINING_DIR = ROOT_DIR / "mining"
DISCOVER_SCRIPT = MINING_DIR / "discover.py"
CONFORMANCE_SCRIPT = MINING_DIR / "conformance.py"


# =========================================================
# LOGGING
# =========================================================

def log(message):
    print(f"[PIPELINE] {message}")


def warning(message):
    print(f"[WARNING] {message}")


def error(message):
    print(f"[ERROR] {message}")


# =========================================================
# COMMAND EXECUTION
# =========================================================

def run_command(name, command, cwd=None, dry_run=False):
    """
    Run a pipeline command using subprocess.

    Returns:
        True  -> command succeeded
        False -> command failed
    """

    log("=" * 70)
    log(f"STARTING: {name}")
    log(f"COMMAND : {' '.join(str(item) for item in command)}")

    if cwd:
        log(f"WORKDIR : {cwd}")

    if dry_run:
        log("DRY-RUN : command not executed")
        return True

    start_time = time.perf_counter()

    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=False
        )

        elapsed = time.perf_counter() - start_time

        if result.returncode == 0:
            log(f"SUCCESS : {name}")
            log(f"TIME    : {elapsed:.2f} seconds")
            return True

        error(f"FAILED  : {name}")
        error(f"RETURN CODE: {result.returncode}")
        error(f"TIME    : {elapsed:.2f} seconds")

        return False

    except FileNotFoundError as exc:
        elapsed = time.perf_counter() - start_time

        error(f"COMMAND NOT FOUND: {exc}")
        error(f"TIME    : {elapsed:.2f} seconds")

        return False

    except Exception as exc:
        elapsed = time.perf_counter() - start_time

        error(f"UNEXPECTED ERROR: {exc}")
        error(f"TIME    : {elapsed:.2f} seconds")

        return False


# =========================================================
# FILE / DIRECTORY CHECKS
# =========================================================

def check_file(path, step_name):
    """
    Check whether a required script exists.
    """

    if not path.exists():
        warning(
            f"{step_name} skipped: file not found -> {path}"
        )
        return False

    return True


def check_directory(path, step_name):
    """
    Check whether an optional directory exists.
    """

    if not path.exists():
        warning(
            f"{step_name} skipped: directory not found -> {path}"
        )
        return False

    return True


# =========================================================
# GENERATE EVENTS
# =========================================================

def generate_events(dry_run=False):

    if not check_file(GENERATE_SCRIPT, "Generate"):
        return True

    command = [
        sys.executable,
        str(GENERATE_SCRIPT)
    ]

    return run_command(
        "Generate Events",
        command,
        cwd=ROOT_DIR,
        dry_run=dry_run
    )


# =========================================================
# LOAD TO BIGQUERY
# =========================================================

def load_to_bigquery(dry_run=False):

    if not check_file(LOAD_SCRIPT, "BigQuery Load"):
        return True

    command = [
        sys.executable,
        str(LOAD_SCRIPT)
    ]

    return run_command(
        "Load to BigQuery",
        command,
        cwd=ROOT_DIR,
        dry_run=dry_run
    )


# =========================================================
# DBT
# =========================================================

def run_dbt(dry_run=False):

    if not check_directory(DBT_DIR, "dbt"):
        return True

    # -----------------------------------------------------
    # dbt run
    # -----------------------------------------------------

    command_run = [
        "dbt",
        "run"
    ]

    if not run_command(
        "dbt run",
        command_run,
        cwd=DBT_DIR,
        dry_run=dry_run
    ):
        return False

    # -----------------------------------------------------
    # dbt test
    # -----------------------------------------------------

    command_test = [
        "dbt",
        "test"
    ]

    return run_command(
        "dbt test",
        command_test,
        cwd=DBT_DIR,
        dry_run=dry_run
    )


# =========================================================
# PROCESS MINING
# =========================================================

def run_mining(dry_run=False):

    if not check_directory(MINING_DIR, "Mining"):
        return True

    # -----------------------------------------------------
    # Process Discovery
    # -----------------------------------------------------

    if check_file(DISCOVER_SCRIPT, "Process Discovery"):

        command = [
            sys.executable,
            str(DISCOVER_SCRIPT)
        ]

        if not run_command(
            "Process Discovery",
            command,
            cwd=ROOT_DIR,
            dry_run=dry_run
        ):
            return False

    else:
        warning(
            f"Process Discovery skipped: "
            f"file not found -> {DISCOVER_SCRIPT}"
        )

    # -----------------------------------------------------
    # Conformance Checking
    # -----------------------------------------------------

    if check_file(CONFORMANCE_SCRIPT, "Conformance Checking"):

        command = [
            sys.executable,
            str(CONFORMANCE_SCRIPT)
        ]

        if not run_command(
            "Conformance Checking",
            command,
            cwd=ROOT_DIR,
            dry_run=dry_run
        ):
            return False

    else:
        warning(
            f"Conformance Checking skipped: "
            f"file not found -> {CONFORMANCE_SCRIPT}"
        )

    return True


# =========================================================
# ARGUMENTS
# =========================================================

def parse_arguments():

    parser = argparse.ArgumentParser(
        description="CareFlow end-to-end pipeline runner."
    )

    parser.add_argument(
        "--skip-generate",
        action="store_true",
        help="Skip event generation."
    )

    parser.add_argument(
        "--skip-load",
        action="store_true",
        help="Skip BigQuery loading."
    )

    parser.add_argument(
        "--skip-dbt",
        action="store_true",
        help="Skip dbt run and dbt test."
    )

    parser.add_argument(
        "--skip-mine",
        action="store_true",
        help="Skip process mining."
    )

    parser.add_argument(
        "--only",
        choices=[
            "generate",
            "load",
            "dbt",
            "mine"
        ],
        help="Run only one pipeline stage."
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Display commands without executing them."
    )

    return parser.parse_args()


# =========================================================
# MAIN PIPELINE
# =========================================================

def main():

    args = parse_arguments()

    log("=" * 70)
    log("CAREFLOW: CLINICAL PATHWAY PROCESS MINING")
    log("=" * 70)

    log(f"PROJECT ROOT: {ROOT_DIR}")

    if args.dry_run:
        log("MODE: DRY-RUN")

    pipeline_start = time.perf_counter()

    # =====================================================
    # ONLY MODE
    # =====================================================

    if args.only:

        log(f"ONLY MODE: {args.only}")

        if args.only == "generate":
            success = generate_events(args.dry_run)

        elif args.only == "load":
            success = load_to_bigquery(args.dry_run)

        elif args.only == "dbt":
            success = run_dbt(args.dry_run)

        elif args.only == "mine":
            success = run_mining(args.dry_run)

        else:
            success = False

        elapsed = time.perf_counter() - pipeline_start

        log("=" * 70)

        if success:
            log("PIPELINE COMPLETED SUCCESSFULLY")
        else:
            error("PIPELINE FAILED")

        log(f"TOTAL TIME: {elapsed:.2f} seconds")

        return 0 if success else 1

    # =====================================================
    # FULL PIPELINE
    # =====================================================

    steps = []

    if not args.skip_generate:
        steps.append(
            ("Generate Events", generate_events)
        )

    if not args.skip_load:
        steps.append(
            ("Load to BigQuery", load_to_bigquery)
        )

    if not args.skip_dbt:
        steps.append(
            ("dbt", run_dbt)
        )

    if not args.skip_mine:
        steps.append(
            ("Mining", run_mining)
        )

    # =====================================================
    # EXECUTE PIPELINE
    # =====================================================

    for name, function in steps:

        log("")
        log(f"PIPELINE STEP: {name}")

        success = function(args.dry_run)

        if not success:

            error("=" * 70)
            error(f"PIPELINE STOPPED AT: {name}")
            error("No later steps were executed.")
            error("=" * 70)

            elapsed = time.perf_counter() - pipeline_start

            error(f"TOTAL TIME: {elapsed:.2f} seconds")

            return 1

    # =====================================================
    # PIPELINE COMPLETE
    # =====================================================

    elapsed = time.perf_counter() - pipeline_start

    log("")
    log("=" * 70)
    log("PIPELINE COMPLETED SUCCESSFULLY")
    log(f"TOTAL TIME: {elapsed:.2f} seconds")
    log("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())