import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent

sys.path.insert(0, str(BACKEND_DIR))

from data_quality_report import generate_data_quality_report

CSV_FILE = PROJECT_DIR / "reports" / "data_quality_report.csv"
SUMMARY_FILE = PROJECT_DIR / "reports" / "data_quality_summary.md"
DATA_FILE = PROJECT_DIR / "data" / "customers.csv"

class TestDataQualityReport(unittest.TestCase):


 def test_report_returns_dataframe(self):
    result = generate_data_quality_report()
    self.assertIsInstance(result, pd.DataFrame)

 def test_report_has_expected_columns(self):
    result = generate_data_quality_report()

    self.assertEqual(
        result.columns.tolist(),
        ["check", "issue_count", "status"]
    )

 def test_required_checks_exist(self):
    result = generate_data_quality_report()

    expected_checks = [
        "Total customer records",
        "Missing values",
        "Duplicate customer IDs",
        "Invalid numeric values: previous_purchases",
        "Invalid numeric values: engagement",
        "Invalid numeric values: discount",
        "Invalid numeric values: purchase",
        "Invalid purchase values (expected 0 or 1)",
        "Invalid discount values (expected 0 or 1)",
    ]

    actual_checks = result["check"].tolist()

    for check in expected_checks:
        with self.subTest(check=check):
            self.assertIn(check, actual_checks)

 def test_status_values_are_valid(self):
    result = generate_data_quality_report()

    self.assertTrue(
        result["status"].isin(["PASS", "CHECK", "INFO"]).all()
    )

 def test_issue_counts_are_non_negative_integers(self):
    result = generate_data_quality_report()

    self.assertTrue((result["issue_count"] >= 0).all())

    for value in result["issue_count"]:
        self.assertIsInstance(value, (int,))

 def test_total_customer_records_matches_dataset(self):
    result = generate_data_quality_report()
    dataset = pd.read_csv(DATA_FILE)

    total_row = result.loc[
        result["check"] == "Total customer records"
    ].iloc[0]

    self.assertEqual(int(total_row["issue_count"]), len(dataset))
    self.assertEqual(total_row["status"], "INFO")

 def test_csv_report_exists(self):
    generate_data_quality_report()
    self.assertTrue(CSV_FILE.exists())

 def test_markdown_summary_exists(self):
    generate_data_quality_report()
    self.assertTrue(SUMMARY_FILE.exists())

 def test_csv_report_matches_generated_report(self):
    result = generate_data_quality_report()
    saved_report = pd.read_csv(CSV_FILE)

    pd.testing.assert_frame_equal(
        saved_report,
        result,
        check_dtype=False
    )

 def test_markdown_summary_contains_report_heading(self):
    generate_data_quality_report()

    summary = SUMMARY_FILE.read_text(encoding="utf-8")

    self.assertIn("# Customer Data Quality Report", summary)
    self.assertIn("## Validation Checks", summary)
    self.assertIn("| Check | Issue Count | Status |", summary)

 def test_missing_dataset_raises_file_not_found(self):
    missing_file = PROJECT_DIR / "missing_customers_test.csv"

    with patch("data_quality_report.DATA_FILE", missing_file):
        with self.assertRaises(FileNotFoundError):
            generate_data_quality_report()

 def test_empty_dataset_is_rejected(self):
    with patch(
        "data_quality_report.DATA_FILE",
        DATA_FILE
    ), patch(
        "data_quality_report.pd.read_csv",
        return_value=pd.DataFrame()
    ):
        with self.assertRaisesRegex(
            ValueError,
            "Customer dataset is empty"
        ):
            generate_data_quality_report()

 def test_missing_required_columns_are_rejected(self):
    incomplete_data = pd.DataFrame({
        "customer_id": [1],
        "purchase": [1]
    })

    with patch(
        "data_quality_report.DATA_FILE",
        DATA_FILE
    ), patch(
        "data_quality_report.pd.read_csv",
        return_value=incomplete_data
    ):
        with self.assertRaisesRegex(
            ValueError,
            "Missing required columns"
        ):
            generate_data_quality_report()


if __name__ == "__main__":
    unittest.main(verbosity=2)
