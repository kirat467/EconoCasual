import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from data_quality_report import generate_data_quality_report


class TestDataQualityReport(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

        self.data_file = self.test_dir / "customers.csv"
        self.report_dir = self.test_dir / "reports"

        self.output_file = (
            self.report_dir / "data_quality_report.csv"
        )
        self.summary_file = (
            self.report_dir / "data_quality_summary.md"
        )

        self.sample_data = pd.DataFrame({
            "customer_id": [1, 2, 3, 4],
            "previous_purchases": [2, 5, 3, 1],
            "engagement": [0.8, 0.6, 0.9, 0.4],
            "discount": [0, 1, 0, 1],
            "purchase": [1, 0, 1, 0],
        })

        self.sample_data.to_csv(
            self.data_file,
            index=False
        )

        self.patcher = patch.multiple(
            "data_quality_report",
            DATA_FILE=self.data_file,
            REPORT_DIR=self.report_dir,
            OUTPUT_FILE=self.output_file,
            SUMMARY_FILE=self.summary_file,
        )
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.temp_dir.cleanup()

    def get_check(self, report, check_name):
        matching_rows = report.loc[
            report["check"] == check_name
        ]

        self.assertEqual(len(matching_rows), 1)

        return matching_rows.iloc[0]

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

        for check in expected_checks:
            with self.subTest(check=check):
                self.assertIn(check, result["check"].tolist())

    def test_status_values_are_valid(self):
        result = generate_data_quality_report()

        self.assertTrue(
            result["status"].isin(
                ["PASS", "CHECK", "INFO"]
            ).all()
        )

    def test_issue_counts_are_non_negative_integers(self):
        result = generate_data_quality_report()

        self.assertTrue(
            (result["issue_count"] >= 0).all()
        )

        for value in result["issue_count"]:
            self.assertIsInstance(value, (int,))

    def test_total_customer_records_matches_dataset(self):
        result = generate_data_quality_report()

        total_row = self.get_check(
            result,
            "Total customer records"
        )

        self.assertEqual(
            total_row["issue_count"],
            len(self.sample_data)
        )
        self.assertEqual(total_row["status"], "INFO")

    def test_missing_values_are_detected(self):
        data = self.sample_data.copy()
        data.loc[0, "engagement"] = None
        data.to_csv(self.data_file, index=False)

        result = generate_data_quality_report()

        row = self.get_check(result, "Missing values")

        self.assertEqual(row["issue_count"], 1)
        self.assertEqual(row["status"], "CHECK")

    def test_duplicate_customer_ids_are_detected(self):
        data = self.sample_data.copy()
        data.loc[3, "customer_id"] = 1
        data.to_csv(self.data_file, index=False)

        result = generate_data_quality_report()

        row = self.get_check(
            result,
            "Duplicate customer IDs"
        )

        self.assertEqual(row["issue_count"], 1)
        self.assertEqual(row["status"], "CHECK")

    def test_invalid_numeric_values_are_detected(self):
        data = self.sample_data.copy()
        data["engagement"] = data["engagement"].astype(object)
        data.loc[0, "engagement"] = "invalid"
        data.to_csv(self.data_file, index=False)

        result = generate_data_quality_report()

        row = self.get_check(
            result,
            "Invalid numeric values: engagement"
        )

        self.assertEqual(row["issue_count"], 1)
        self.assertEqual(row["status"], "CHECK")

    def test_invalid_purchase_values_are_detected(self):
        data = self.sample_data.copy()
        data.loc[0, "purchase"] = 2
        data.to_csv(self.data_file, index=False)

        result = generate_data_quality_report()

        row = self.get_check(
            result,
            "Invalid purchase values (expected 0 or 1)"
        )

        self.assertEqual(row["issue_count"], 1)
        self.assertEqual(row["status"], "CHECK")

    def test_invalid_discount_values_are_detected(self):
        data = self.sample_data.copy()
        data.loc[0, "discount"] = 3
        data.to_csv(self.data_file, index=False)

        result = generate_data_quality_report()

        row = self.get_check(
            result,
            "Invalid discount values (expected 0 or 1)"
        )

        self.assertEqual(row["issue_count"], 1)
        self.assertEqual(row["status"], "CHECK")

    def test_valid_dataset_has_no_quality_issues(self):
        result = generate_data_quality_report()

        issue_rows = result[
            result["check"] != "Total customer records"
        ]

        self.assertTrue(
            (issue_rows["issue_count"] == 0).all()
        )
        self.assertTrue(
            (issue_rows["status"] == "PASS").all()
        )

    def test_csv_report_is_created(self):
        generate_data_quality_report()

        self.assertTrue(self.output_file.exists())

    def test_markdown_summary_is_created(self):
        generate_data_quality_report()

        self.assertTrue(self.summary_file.exists())

    def test_csv_matches_returned_report(self):
        result = generate_data_quality_report()

        saved_report = pd.read_csv(self.output_file)

        pd.testing.assert_frame_equal(
            saved_report,
            result,
            check_dtype=False
        )

    def test_markdown_summary_contains_expected_sections(self):
        generate_data_quality_report()

        summary = self.summary_file.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "# Customer Data Quality Report",
            summary
        )
        self.assertIn("## Validation Checks", summary)
        self.assertIn(
            "| Check | Issue Count | Status |",
            summary
        )

    def test_missing_dataset_raises_file_not_found(self):
        missing_file = self.test_dir / "missing.csv"

        with patch(
            "data_quality_report.DATA_FILE",
            missing_file
        ):
            with self.assertRaises(FileNotFoundError):
                generate_data_quality_report()

    def test_empty_dataset_is_rejected(self):
        pd.DataFrame().to_csv(
            self.data_file,
            index=False
        )

        with self.assertRaisesRegex(
            ValueError,
            "Customer dataset is empty"
        ):
            generate_data_quality_report()

    def test_missing_required_columns_are_rejected(self):
        incomplete_data = pd.DataFrame({
            "customer_id": [1],
            "purchase": [1],
        })

        incomplete_data.to_csv(
            self.data_file,
            index=False
        )

        with self.assertRaisesRegex(
            ValueError,
            "Missing required columns"
        ):
            generate_data_quality_report()


if __name__ == "__main__":
    unittest.main(verbosity=2)