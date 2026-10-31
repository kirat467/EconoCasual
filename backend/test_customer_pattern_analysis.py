import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

import customer_pattern_analysis as analysis


class TestCustomerPatternAnalysis(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.temp_path = Path(self.temp_dir.name)

        self.data_file = self.temp_path / "customers.csv"

        self.test_data = pd.DataFrame({
            "customer_id": [1, 2, 3, 4, 5],
            "previous_purchases": [0, 1, 1, 2, 2],
            "engagement": [20, 40, 60, 70, 90],
            "purchase": [0, 1, 0, 1, 1],
        })

        self.test_data.to_csv(self.data_file, index=False)

        self.report_dir = self.temp_path / "reports"
        self.chart_dir = self.report_dir / "charts"

        self.output_file = self.report_dir / "analysis.csv"
        self.chart_file = self.chart_dir / "analysis.png"

        patches = [
            patch.object(analysis, "DATA_FILE", self.data_file),
            patch.object(analysis, "REPORT_DIR", self.report_dir),
            patch.object(analysis, "CHART_DIR", self.chart_dir),
            patch.object(analysis, "OUTPUT_FILE", self.output_file),
            patch.object(analysis, "CHART_FILE", self.chart_file),
        ]

        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_analysis_returns_dataframe(self):
        result = analysis.analyze_customer_patterns()
        self.assertIsInstance(result, pd.DataFrame)

    def test_result_is_not_empty(self):
        result = analysis.analyze_customer_patterns()
        self.assertFalse(result.empty)

    def test_result_contains_required_columns(self):
        result = analysis.analyze_customer_patterns()

        expected_columns = [
            "previous_purchases",
            "customer_count",
            "purchasers",
            "average_engagement",
            "non_purchasers",
            "purchase_rate_percent",
        ]

        for column in expected_columns:
            with self.subTest(column=column):
                self.assertIn(column, result.columns)

    def test_previous_purchase_groups_are_correct(self):
        result = analysis.analyze_customer_patterns()

        self.assertEqual(
            result["previous_purchases"].tolist(),
            [0, 1, 2],
        )

    def test_customer_counts_are_correct(self):
        result = analysis.analyze_customer_patterns()

        self.assertEqual(
            result["customer_count"].tolist(),
            [1, 2, 2],
        )

    def test_purchaser_counts_are_correct(self):
        result = analysis.analyze_customer_patterns()

        self.assertEqual(
            result["purchasers"].tolist(),
            [0, 1, 2],
        )

    def test_non_purchaser_counts_are_correct(self):
        result = analysis.analyze_customer_patterns()

        self.assertEqual(
            result["non_purchasers"].tolist(),
            [1, 1, 0],
        )

    def test_average_engagement_is_correct(self):
        result = analysis.analyze_customer_patterns()

        self.assertEqual(
            result["average_engagement"].tolist(),
            [20.0, 50.0, 80.0],
        )

    def test_purchase_rates_are_correct(self):
        result = analysis.analyze_customer_patterns()

        self.assertEqual(
            result["purchase_rate_percent"].tolist(),
            [0.0, 50.0, 100.0],
        )

    def test_purchase_rates_are_valid(self):
        result = analysis.analyze_customer_patterns()

        self.assertTrue(
            result["purchase_rate_percent"].between(0, 100).all()
        )

    def test_purchase_rate_matches_counts(self):
        result = analysis.analyze_customer_patterns()

        expected_rates = (
            result["purchasers"]
            / result["customer_count"]
            * 100
        ).round(2)

        pd.testing.assert_series_equal(
            result["purchase_rate_percent"],
            expected_rates,
            check_names=False,
        )

    def test_total_customer_count_is_correct(self):
        result = analysis.analyze_customer_patterns()

        self.assertEqual(result["customer_count"].sum(), 5)

    def test_total_purchaser_count_is_correct(self):
        result = analysis.analyze_customer_patterns()

        self.assertEqual(result["purchasers"].sum(), 3)

    def test_output_csv_is_created(self):
        analysis.analyze_customer_patterns()

        self.assertTrue(self.output_file.exists())

    def test_saved_csv_matches_analysis(self):
        result = analysis.analyze_customer_patterns()
        saved_result = pd.read_csv(self.output_file)

        pd.testing.assert_frame_equal(
            saved_result,
            result,
            check_dtype=False,
        )

    def test_chart_is_created(self):
        analysis.analyze_customer_patterns()

        self.assertTrue(self.chart_file.exists())
        self.assertGreater(self.chart_file.stat().st_size, 0)

    def test_missing_dataset_raises_error(self):
        with patch.object(
            analysis,
            "DATA_FILE",
            self.temp_path / "missing.csv",
        ):
            with self.assertRaises(FileNotFoundError):
                analysis.analyze_customer_patterns()

    def test_missing_columns_raise_error(self):
        invalid_data = pd.DataFrame({
            "customer_id": [1],
            "purchase": [1],
        })

        invalid_data.to_csv(self.data_file, index=False)

        with self.assertRaisesRegex(ValueError, "Missing columns"):
            analysis.analyze_customer_patterns()

    def test_empty_dataset_raises_error(self):
        empty_data = pd.DataFrame(
            columns=[
                "customer_id",
                "previous_purchases",
                "engagement",
                "purchase",
            ]
        )

        empty_data.to_csv(self.data_file, index=False)

        with self.assertRaisesRegex(ValueError, "empty"):
            analysis.analyze_customer_patterns()

    def test_invalid_purchase_values_raise_error(self):
        invalid_data = self.test_data.copy()
        invalid_data["purchase"] = [0, 1, 2, 0, 1]
        invalid_data.to_csv(self.data_file, index=False)

        with self.assertRaisesRegex(ValueError, "0 or 1"):
            analysis.analyze_customer_patterns()

    def test_missing_purchase_value_raises_error(self):
        invalid_data = self.test_data.copy()
        invalid_data.loc[0, "purchase"] = None
        invalid_data.to_csv(self.data_file, index=False)

        with self.assertRaisesRegex(ValueError, "0 or 1"):
            analysis.analyze_customer_patterns()

    def test_invalid_previous_purchases_value_raises_error(self):
        invalid_data = self.test_data.copy()
        invalid_data["previous_purchases"] = (
            invalid_data["previous_purchases"].astype(str)
        )
        invalid_data.loc[0, "previous_purchases"] = "invalid"
        invalid_data.to_csv(self.data_file, index=False)

        with self.assertRaises(ValueError):
            analysis.analyze_customer_patterns()

    def test_analysis_is_repeatable(self):
        first_result = analysis.analyze_customer_patterns()
        second_result = analysis.analyze_customer_patterns()

        pd.testing.assert_frame_equal(first_result, second_result)


if __name__ == "__main__":
    unittest.main(verbosity=2)