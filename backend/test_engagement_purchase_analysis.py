import sys
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from engagement_purchase_analysis import analyze_engagement_purchase


class TestEngagementPurchaseAnalysis(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.base_dir = Path(self.temp_dir.name)
        self.data_file = self.base_dir / "customers.csv"
        self.report_dir = self.base_dir / "reports"
        self.chart_dir = self.report_dir / "charts"
        self.output_file = self.report_dir / "engagement_purchase_analysis.csv"
        self.chart_file = self.chart_dir / "engagement_purchase_rate.png"

        self.sample_data = pd.DataFrame({
            "customer_id": [1, 2, 3, 4, 5],
            "engagement": [1, 1, 2, 2, 3],
            "purchase": [1, 0, 1, 1, 0],
        })

        self.sample_data.to_csv(self.data_file, index=False)

        patches = [
            patch(
                "engagement_purchase_analysis.DATA_FILE",
                self.data_file
            ),
            patch(
                "engagement_purchase_analysis.REPORT_DIR",
                self.report_dir
            ),
            patch(
                "engagement_purchase_analysis.CHART_DIR",
                self.chart_dir
            ),
            patch(
                "engagement_purchase_analysis.OUTPUT_FILE",
                self.output_file
            ),
            patch(
                "engagement_purchase_analysis.CHART_FILE",
                self.chart_file
            ),
        ]

        for active_patch in patches:
            active_patch.start()
            self.addCleanup(active_patch.stop)

    def test_analysis_returns_dataframe(self):
        result = analyze_engagement_purchase()

        self.assertIsInstance(result, pd.DataFrame)

    def test_result_contains_required_columns(self):
        result = analyze_engagement_purchase()

        expected_columns = [
            "engagement",
            "customer_count",
            "total_purchases",
            "non_purchases",
            "purchase_rate_percent",
        ]

        for column in expected_columns:
            with self.subTest(column=column):
                self.assertIn(column, result.columns)

    def test_result_is_not_empty(self):
        result = analyze_engagement_purchase()

        self.assertFalse(result.empty)

    def test_engagement_groups_are_correct(self):
        result = analyze_engagement_purchase()

        self.assertEqual(
            result["engagement"].tolist(),
            [1, 2, 3]
        )

    def test_customer_counts_are_correct(self):
        result = analyze_engagement_purchase()

        self.assertEqual(
            result["customer_count"].tolist(),
            [2, 2, 1]
        )

    def test_total_purchases_are_correct(self):
        result = analyze_engagement_purchase()

        self.assertEqual(
            result["total_purchases"].tolist(),
            [1, 2, 0]
        )

    def test_non_purchases_are_correct(self):
        result = analyze_engagement_purchase()

        self.assertEqual(
            result["non_purchases"].tolist(),
            [1, 0, 1]
        )

    def test_purchase_rates_are_correct(self):
        result = analyze_engagement_purchase()

        self.assertEqual(
            result["purchase_rate_percent"].tolist(),
            [50.0, 100.0, 0.0]
        )

    def test_purchase_rates_are_valid(self):
        result = analyze_engagement_purchase()

        self.assertTrue(
            result["purchase_rate_percent"].between(0, 100).all()
        )

    def test_purchases_do_not_exceed_customer_count(self):
        result = analyze_engagement_purchase()

        self.assertTrue(
            (
                result["total_purchases"]
                <= result["customer_count"]
            ).all()
        )

    def test_output_csv_is_generated(self):
        analyze_engagement_purchase()

        self.assertTrue(self.output_file.exists())

    def test_chart_is_generated(self):
        analyze_engagement_purchase()

        self.assertTrue(self.chart_file.exists())

    def test_missing_dataset_raises_error(self):
        self.data_file.unlink()

        with self.assertRaises(FileNotFoundError):
            analyze_engagement_purchase()

    def test_missing_required_column_raises_error(self):
        invalid_data = self.sample_data.drop(columns=["engagement"])
        invalid_data.to_csv(self.data_file, index=False)

        with self.assertRaises(ValueError):
            analyze_engagement_purchase()

    def test_empty_dataset_raises_error(self):
        empty_data = pd.DataFrame(
            columns=["customer_id", "engagement", "purchase"]
        )
        empty_data.to_csv(self.data_file, index=False)

        with self.assertRaises(ValueError):
            analyze_engagement_purchase()

    def test_missing_values_raise_error(self):
        invalid_data = self.sample_data.copy()
        invalid_data.loc[0, "engagement"] = None
        invalid_data.to_csv(self.data_file, index=False)

        with self.assertRaises(ValueError):
            analyze_engagement_purchase()

    def test_invalid_purchase_value_raises_error(self):
        invalid_data = self.sample_data.copy()
        invalid_data.loc[0, "purchase"] = 2
        invalid_data.to_csv(self.data_file, index=False)

        with self.assertRaises(ValueError):
            analyze_engagement_purchase()

    def test_invalid_engagement_value_raises_error(self):
        invalid_data = self.sample_data.copy()

        # Convert column to text before inserting invalid value
        invalid_data["engagement"] = (
            invalid_data["engagement"].astype(str)
        )
        invalid_data.loc[0, "engagement"] = "invalid"

        invalid_data.to_csv(self.data_file, index=False)

        with self.assertRaises(ValueError):
            analyze_engagement_purchase()

    def test_analysis_is_repeatable(self):
        first_result = analyze_engagement_purchase()
        second_result = analyze_engagement_purchase()

        pd.testing.assert_frame_equal(first_result, second_result)


if __name__ == "__main__":
    unittest.main(verbosity=2)