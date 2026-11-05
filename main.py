"""Run the CareFlow patient-level data cleaning and analysis pipeline."""

import argparse
from pathlib import Path

from clinical_analysis import analyze_dataset
from data_cleaning import DEFAULT_INPUT, DEFAULT_OUTPUT, clean_dataset


PROJECT_ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "data" / "processed")
    parser.add_argument("--findings", type=Path, default=PROJECT_ROOT / "docs" / "findings.md")
    args = parser.parse_args()

    if not args.input.is_file():
        raise FileNotFoundError(f"Input dataset not found: {args.input}")

    cleaned_path = args.output_dir / DEFAULT_OUTPUT.name
    _, cleaning_report = clean_dataset(args.input, cleaned_path)
    analysis_summary = analyze_dataset(
        cleaned_path,
        output_dir=args.output_dir,
        findings_path=args.findings,
        cleaning_report=cleaning_report,
    )

    print(f"Cleaned dataset: {cleaned_path}")
    print(f"Analysis outputs: {args.output_dir}")
    print(f"Findings report: {args.findings}")
    print("Cleaning report:", cleaning_report)
    print("Analysis summary:", analysis_summary)


if __name__ == "__main__":
    main()
