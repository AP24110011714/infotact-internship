import unittest
import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "outputs"

class TestCareFlowOutputs(unittest.TestCase):

    def test_careflow_summary_exists(self):
        file = OUTPUT_DIR / "careflow_summary.csv"
        self.assertTrue(file.exists())
        self.assertGreater(file.stat().st_size, 0)

    def test_kpi_summary_exists(self):
        file = OUTPUT_DIR / "kpi_summary.csv"
        self.assertTrue(file.exists())
        self.assertGreater(file.stat().st_size, 0)

    def test_loopbacks_exists(self):
        file = OUTPUT_DIR / "loopbacks.csv"
        self.assertTrue(file.exists())
        self.assertGreater(file.stat().st_size, 0)

    def test_transition_times_exists(self):
        file = OUTPUT_DIR / "transition_times.csv"
        self.assertTrue(file.exists())
        self.assertGreater(file.stat().st_size, 0)

    def test_csv_files_are_readable(self):
        files = list(OUTPUT_DIR.glob("*.csv"))

        self.assertGreater(len(files), 0)

        for file in files:
            with open(file, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                self.assertIsNotNone(header, f"{file.name} is empty")

if __name__ == "__main__":
    unittest.main()