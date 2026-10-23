
import sys
import unittest
from pathlib import Path

import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent

sys.path.insert(0, str(BACKEND_DIR))

from data_quality_report import generate_data_quality_report


CSV_FILE = PROJECT_DIR / "reports" / "data_quality_report.csv"
SUMMARY_FILE = PROJECT_DIR / "reports" / "data_quality_summary.md"


class TestDataQualityReport(unittest.TestCase):

    def test_report_returns_dataframe(self):
        result = generate_data_quality_report()
        self.assertIsInstance(result, pd.DataFrame)

    def test_required_checks_exist(self):
        result = generate_data_quality_report()

        expected_checks = [
            "Missing values",
            "Duplicate customer IDs",
            "Invalid purchase values (expected 0 or 1)",
            "Invalid discount values (expected 0 or 1)",
        ]

        for check in expected_checks:
            self.assertIn(check, result["check"].tolist())

    def test_status_values_are_valid(self):
        result = generate_data_quality_report()
        self.assertTrue(
            result["status"].isin(["PASS", "CHECK", "INFO"]).all()
        )

    def test_csv_report_exists(self):
        generate_data_quality_report()
        self.assertTrue(CSV_FILE.exists())

    def test_markdown_summary_exists(self):
        generate_data_quality_report()
        self.assertTrue(SUMMARY_FILE.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)

