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
        # Har test ke liye separate temporary directory banao
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.temp_path = Path(self.temp_dir.name)

        # Temporary test dataset banao
        self.data_file = self.temp_path / "customers.csv"

        self.test_data = pd.DataFrame({
            "customer_id": [1, 2, 3, 4, 5],
            "previous_purchases": [0, 1, 1, 2, 2],
            "engagement": [20, 40, 60, 70, 90],
            "purchase": [0, 1, 0, 1, 1],
        })

        self.test_data.to_csv(self.data_file, index=False)

        # Temporary report aur chart paths
        self.report_dir = self.temp_path / "reports"
        self.chart_dir = self.report_dir / "charts"

        self.output_file = self.report_dir / "analysis.csv"
        self.chart_file = self.chart_dir / "analysis.png"

        # Original paths ko temporary test paths se replace karo
        self.patches = [
            patch.object(analysis, "DATA_FILE", self.data_file),
            patch.object(analysis, "REPORT_DIR", self.report_dir),
            patch.object(analysis, "CHART_DIR", self.chart_dir),
            patch.object(analysis, "OUTPUT_FILE", self.output_file),
            patch.object(analysis, "CHART_FILE", self.chart_file),
        ]

        for patcher in self.patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_analysis_returns_dataframe(self):
        result = analysis.analyze_customer_patterns()
        self.assertIsInstance(result, pd.DataFrame)

    def test_result_is_not_empty(self):
        result = analysis.analyze_customer_patterns()
        self.assertFalse(result.empty)

    def test_required_columns_exist(self):
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

    def test_customer_counts_are_correct(self):
        result = analysis.analyze_customer_patterns()
        self.assertEqual(result["customer_count"].sum(), 5)

    def test_purchase_counts_are_correct(self):
        result = analysis.analyze_customer_patterns()
        self.assertEqual(result["purchasers"].sum(), 3)

    def test_non_purchaser_counts_are_correct(self):
        result = analysis.analyze_customer_patterns()
        self.assertEqual(result["non_purchasers"].sum(), 2)

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

    def test_output_csv_is_created(self):
        analysis.analyze_customer_patterns()
        self.assertTrue(self.output_file.exists())

    def test_chart_is_created(self):
        analysis.analyze_customer_patterns()
        self.assertTrue(self.chart_file.exists())

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
        self.test_data.iloc[0:0].to_csv(
            self.data_file,
            index=False,
        )

        with self.assertRaisesRegex(ValueError, "empty"):
            analysis.analyze_customer_patterns()

    def test_invalid_purchase_values_raise_error(self):
        self.test_data["purchase"] = [0, 1, 2, 0, 1]
        self.test_data.to_csv(self.data_file, index=False)

        with self.assertRaisesRegex(ValueError, "0 or 1"):
            analysis.analyze_customer_patterns()

    def test_analysis_is_repeatable(self):
        first_result = analysis.analyze_customer_patterns()
        second_result = analysis.analyze_customer_patterns()

        pd.testing.assert_frame_equal(first_result, second_result)


if __name__ == "__main__":
    unittest.main(verbosity=2)