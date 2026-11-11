import sys
import unittest
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, call
from contextlib import redirect_stderr
from io import StringIO

from pipeline import run_pipeline as runner


class TestPipelineArguments(unittest.TestCase):

    def test_valid_arguments(self):
        with patch.object(
            sys,
            "argv",
            ["run_pipeline.py", "--only", "analyze", "--dry-run"]
        ):
            args = runner.parse_arguments()

        self.assertEqual(args.only, "analyze")
        self.assertTrue(args.dry_run)

    def test_invalid_stage_is_rejected(self):
        with patch.object(
            sys,
            "argv",
            ["run_pipeline.py", "--only", "invalid"]
        ):
            with redirect_stderr(StringIO()):
                with self.assertRaises(SystemExit) as result:
                    runner.parse_arguments()

        self.assertEqual(result.exception.code, 2)


class TestPipelineExecution(unittest.TestCase):

    def test_dry_run_does_not_execute_command(self):
        with patch.object(runner.subprocess, "run") as mock_run:
            result = runner.run_command(
                "Test Command",
                ["python", "example.py"],
                dry_run=True
            )

        self.assertTrue(result)
        mock_run.assert_not_called()

    def test_missing_script_is_handled(self):
        missing_script = Path("missing_script.py")

        with patch.dict(
            runner.SCRIPTS,
            {"missing": missing_script}
        ):
            result = runner.run_script(
                "missing",
                "Missing Script"
            )

        self.assertFalse(result)

    def test_default_pipeline_executes_correct_stages(self):

        args = SimpleNamespace(
            only=None,
            dry_run=False,
            include_generate=False,
            include_load=False,
            include_export=False,
            include_dbt=False,
            include_mine=False
        )

        executed = []

        def record(stage):
            def execute(dry_run=False):
                executed.append(stage)
                return True
            return execute

        with patch.object(runner, "parse_arguments", return_value=args):
            with patch.object(
                runner, "validate_events", side_effect=record("validate")
            ):
                with patch.object(
                    runner, "analyze_process", side_effect=record("analyze")
                ):
                    with patch.object(
                        runner, "create_visualizations",
                        side_effect=record("visualize")
                    ):
                        with patch.object(
                            runner, "generate_report",
                            side_effect=record("report")
                        ):
                            with patch.object(
                                runner, "run_tests",
                                side_effect=record("test")
                            ):
                                result = runner.main()

        self.assertEqual(result, 0)

        self.assertEqual(
            executed,
            ["validate", "analyze", "visualize", "report", "test"]
        )

    def test_pipeline_stops_after_failure(self):

        args = SimpleNamespace(
            only=None,
            dry_run=False,
            include_generate=False,
            include_load=False,
            include_export=False,
            include_dbt=False,
            include_mine=False
        )

        with patch.object(runner, "parse_arguments", return_value=args):
            with patch.object(
                runner, "validate_events", return_value=False
            ):
                with patch.object(runner, "analyze_process") as mock_analyze:
                    result = runner.main()

        self.assertEqual(result, 1)
        mock_analyze.assert_not_called()

    def test_only_mode_runs_selected_stage(self):

        args = SimpleNamespace(
            only="analyze",
            dry_run=True
        )

        with patch.object(runner, "parse_arguments", return_value=args):
            with patch.object(
                runner, "analyze_process", return_value=True
            ) as mock_analyze:
                result = runner.main()

        self.assertEqual(result, 0)
        mock_analyze.assert_called_once_with(True)


class TestPipelineValidation(unittest.TestCase):

    def test_validation_passes_with_valid_report(self):

        with tempfile.TemporaryDirectory() as temp_dir:

            report = Path(temp_dir) / "validation_report.txt"

            report.write_text(
                "OVERALL VALIDATION STATUS: PASS",
                encoding="utf-8"
            )

            with patch.object(
                runner, "run_script", return_value=True
            ):
                with patch.object(
                    runner, "VALIDATION_REPORT", report
                ):
                    result = runner.validate_events()

        self.assertTrue(result)

    def test_validation_fails_with_failed_report(self):

        with tempfile.TemporaryDirectory() as temp_dir:

            report = Path(temp_dir) / "validation_report.txt"

            report.write_text(
                "OVERALL VALIDATION STATUS: FAIL",
                encoding="utf-8"
            )

            with patch.object(
                runner, "run_script", return_value=True
            ):
                with patch.object(
                    runner, "VALIDATION_REPORT", report
                ):
                    result = runner.validate_events()

        self.assertFalse(result)


class TestOptionalComponents(unittest.TestCase):

    def test_missing_dbt_directory_is_handled(self):

        with patch.object(
            runner, "DBT_DIR", Path("missing_dbt_directory")
        ):
            result = runner.run_dbt()

        self.assertFalse(result)

    def test_missing_mining_directory_is_handled(self):

        with patch.object(
            runner, "MINING_DIR", Path("missing_mining_directory")
        ):
            result = runner.run_mining()

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
