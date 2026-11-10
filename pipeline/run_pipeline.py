
import argparse
import subprocess
import sys
import time
from pathlib import Path


# =========================================================
# CAREFLOW PIPELINE CONFIGURATION
# =========================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

SCRIPTS = {
    "generate": ROOT_DIR / "scripts" / "generate_event_log.py",
    "validate": ROOT_DIR / "scripts" / "validate_event_log.py",
    "analyze": ROOT_DIR / "data_generator" / "analyze_process_performance.py",
    "visualize": ROOT_DIR / "data_generator" / "create_process_visualizations.py",
    "report": ROOT_DIR / "data_generator" / "generate_bottleneck_report.py",
    "load": ROOT_DIR / "data_generator" / "load_to_bq.py",
    "export": ROOT_DIR / "pipeline" / "export_results.py",
}

DBT_DIR = ROOT_DIR / "dbt_project"
MINING_DIR = ROOT_DIR / "mining"
TEST_DIR = ROOT_DIR / "tests"

VALIDATION_REPORT = ROOT_DIR / "documentation" / "validation_report.txt"


# =========================================================
# LOGGING
# =========================================================

def log(message):
    print(f"[PIPELINE] {message}", flush=True)


def warning(message):
    print(f"[WARNING] {message}", flush=True)


def error(message):
    print(f"[ERROR] {message}", flush=True)


# =========================================================
# COMMAND EXECUTION
# =========================================================

def run_command(name, command, cwd=None, dry_run=False):

    log("=" * 65)
    log(f"STARTING: {name}")
    log(f"COMMAND: {' '.join(str(item) for item in command)}")

    if cwd:
        log(f"WORKDIR: {cwd}")

    if dry_run:
        log("DRY-RUN: command not executed")
        return True

    start = time.perf_counter()

    try:
        result = subprocess.run(
            command,
            cwd=cwd or ROOT_DIR,
            check=False
        )

        elapsed = time.perf_counter() - start

        if result.returncode == 0:
            log(f"SUCCESS: {name}")
            log(f"TIME: {elapsed:.2f} seconds")
            return True

        error(f"FAILED: {name}")
        error(f"RETURN CODE: {result.returncode}")
        error(f"TIME: {elapsed:.2f} seconds")
        return False

    except Exception as exc:
        error(f"FAILED: {name}: {exc}")
        return False


# =========================================================
# PYTHON SCRIPT EXECUTION
# =========================================================

def run_script(stage, name, dry_run=False):

    script = SCRIPTS[stage]

    if not script.is_file():
        error(f"Required script not found: {script}")
        return False

    return run_command(
        name,
        [sys.executable, str(script)],
        cwd=ROOT_DIR,
        dry_run=dry_run
    )


# =========================================================
# EVENT LOG VALIDATION
# =========================================================

def validate_events(dry_run=False):

    success = run_script(
        "validate",
        "Event Log Validation",
        dry_run
    )

    if not success or dry_run:
        return success

    if not VALIDATION_REPORT.is_file():
        error("Validation report was not generated.")
        return False

    report = VALIDATION_REPORT.read_text(
        encoding="utf-8"
    )

    if "OVERALL VALIDATION STATUS: PASS" not in report:
        error("Event log validation did not pass.")
        return False

    log("All event log validation checks passed.")
    return True


# =========================================================
# PROCESS ANALYSIS
# =========================================================

def analyze_process(dry_run=False):

    return run_script(
        "analyze",
        "Process Performance Analysis",
        dry_run
    )


# =========================================================
# VISUALIZATION
# =========================================================

def create_visualizations(dry_run=False):

    return run_script(
        "visualize",
        "Process Visualization Generation",
        dry_run
    )


# =========================================================
# BOTTLENECK REPORT
# =========================================================

def generate_report(dry_run=False):

    return run_script(
        "report",
        "Bottleneck Report Generation",
        dry_run
    )


# =========================================================
# AUTOMATED TESTING
# =========================================================

def run_tests(dry_run=False):

    if not TEST_DIR.is_dir():
        error("Tests directory not found.")
        return False

    return run_command(
        "Automated Tests",
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            str(TEST_DIR),
            "-p",
            "test_*.py",
            "-v"
        ],
        cwd=ROOT_DIR,
        dry_run=dry_run
    )


# =========================================================
# BIGQUERY EXPORT
# =========================================================

def export_results(dry_run=False):

    warning(
        "This export replaces the existing careflow_summary "
        "BigQuery table using WRITE_TRUNCATE."
    )

    return run_script(
        "export",
        "BigQuery Results Export",
        dry_run
    )


# =========================================================
# OPTIONAL DBT
# =========================================================

def run_dbt(dry_run=False):

    if not DBT_DIR.is_dir():
        error("dbt_project directory is not available.")
        return False

    if not dry_run and not (DBT_DIR / "dbt_project.yml").is_file():
        error("dbt_project.yml not found.")
        return False

    if not run_command(
        "dbt run",
        ["dbt", "run"],
        cwd=DBT_DIR,
        dry_run=dry_run
    ):
        return False

    return run_command(
        "dbt test",
        ["dbt", "test"],
        cwd=DBT_DIR,
        dry_run=dry_run
    )


# =========================================================
# OPTIONAL PROCESS MINING
# =========================================================

def run_mining(dry_run=False):

    if not MINING_DIR.is_dir():
        error("Separate mining directory is not available.")
        return False

    scripts = [
        MINING_DIR / "discover.py",
        MINING_DIR / "conformance.py"
    ]

    for script in scripts:

        if not script.is_file():
            error(f"Required mining script not found: {script}")
            return False

        if not run_command(
            script.stem,
            [sys.executable, str(script)],
            cwd=ROOT_DIR,
            dry_run=dry_run
        ):
            return False

    return True


# =========================================================
# ARGUMENTS
# =========================================================

def parse_arguments():

    parser = argparse.ArgumentParser(
        description="CareFlow integrated pipeline runner."
    )

    parser.add_argument(
        "--only",
        choices=[
            "generate",
            "validate",
            "analyze",
            "visualize",
            "report",
            "load",
            "dbt",
            "mine",
            "export",
            "test"
        ],
        help="Run only one pipeline stage."
    )

    parser.add_argument(
        "--include-generate",
        action="store_true",
        help="Include event generation."
    )

    parser.add_argument(
        "--include-load",
        action="store_true",
        help="Include BigQuery event loading. May replace raw_ehr_events."
    )

    parser.add_argument(
        "--include-export",
        action="store_true",
        help="Include BigQuery results export. May replace careflow_summary."
    )

    parser.add_argument(
        "--include-dbt",
        action="store_true",
        help="Include dbt run and test."
    )

    parser.add_argument(
        "--include-mine",
        action="store_true",
        help="Include the separate process-mining module."
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

    log("=" * 65)
    log("CAREFLOW: CLINICAL PATHWAY PROCESS MINING")
    log("=" * 65)
    log(f"PROJECT ROOT: {ROOT_DIR}")

    if args.dry_run:
        log("MODE: DRY-RUN")

    # Only one selected stage
    if args.only:

        log(f"ONLY MODE: {args.only}")

        single_stage = {
            "generate": lambda: run_script(
                "generate", "Generate Events", args.dry_run
            ),
            "validate": lambda: validate_events(args.dry_run),
            "analyze": lambda: analyze_process(args.dry_run),
            "visualize": lambda: create_visualizations(args.dry_run),
            "report": lambda: generate_report(args.dry_run),
            "load": lambda: run_script(
                "load", "Load Events to BigQuery", args.dry_run
            ),
            "dbt": lambda: run_dbt(args.dry_run),
            "mine": lambda: run_mining(args.dry_run),
            "export": lambda: export_results(args.dry_run),
            "test": lambda: run_tests(args.dry_run),
        }

        start = time.perf_counter()
        success = single_stage[args.only]()
        elapsed = time.perf_counter() - start

        log("=" * 65)
        log(
            "STAGE COMPLETED SUCCESSFULLY"
            if success else "STAGE FAILED"
        )
        log(f"TOTAL TIME: {elapsed:.2f} seconds")

        return 0 if success else 1

    # Default pipeline uses existing local data.
    steps = [
        ("Event Log Validation", validate_events),
        ("Process Performance Analysis", analyze_process),
        ("Process Visualizations", create_visualizations),
        ("Bottleneck Report", generate_report),
    ]

    # Optional stages are included only when explicitly requested.
    if args.include_generate:
        steps.insert(
            0,
            ("Generate Events", lambda dry: run_script(
                "generate", "Generate Events", dry
            ))
        )

    if args.include_load:
        steps.append(
            ("BigQuery Event Loading", lambda dry: run_script(
                "load", "Load Events to BigQuery", dry
            ))
        )

    if args.include_dbt:
        steps.append(("dbt", run_dbt))

    if args.include_mine:
        steps.append(("Process Mining", run_mining))

    if args.include_export:
        steps.append(("BigQuery Results Export", export_results))

    steps.append(("Automated Tests", run_tests))

    # Execute pipeline
    pipeline_start = time.perf_counter()
    completed = []

    for name, function in steps:

        log("")
        log(f"PIPELINE STEP: {name}")

        success = function(args.dry_run)

        if not success:

            error("=" * 65)
            error(f"PIPELINE STOPPED AT: {name}")
            error("Later stages were not executed.")
            error("=" * 65)

            log(f"COMPLETED STAGES: {len(completed)}")
            log(f"TOTAL TIME: {time.perf_counter() - pipeline_start:.2f} seconds")

            return 1

        completed.append(name)

    elapsed = time.perf_counter() - pipeline_start

    log("")
    log("=" * 65)
    log("CAREFLOW PIPELINE COMPLETED SUCCESSFULLY")
    log("=" * 65)

    for stage in completed:
        log(f"COMPLETED: {stage}")

    log(f"TOTAL STAGES: {len(completed)}")
    log(f"TOTAL TIME: {elapsed:.2f} seconds")

    return 0


if __name__ == "__main__":
    sys.exit(main())
