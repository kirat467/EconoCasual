"""Tests for discount purchase analysis."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from backend import discount_purchase_analysis as analysis_module


class TestDiscountPurchaseAnalysis(unittest.TestCase):

    def setUp(self):
        """Create isolated temporary files for every test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.temp_path = Path(self.temp_dir.name)

        self.data_file = self.temp_path / "customers.csv"
        self.report_dir = self.temp_path / "reports"
        self.chart_dir = self.report_dir / "charts"
        self.output_file = (
            self.report_dir / "discount_purchase_analysis.csv"
        )
        self.chart_file = (
            self.chart_dir / "discount_purchase_rate.png"
        )

        self.sample_data = pd.DataFrame({
            "customer_id": [1, 2, 3, 4, 5, 6],
            "discount": [0, 0, 0, 1, 1, 1],
            "purchase": [1, 0, 1, 1, 1, 0],
        })

        self.sample_data.to_csv(self.data_file, index=False)

        self.patches = [
            patch.object(analysis_module, "DATA_FILE", self.data_file),
            patch.object(analysis_module, "REPORT_DIR", self.report_dir),
            patch.object(analysis_module, "CHART_DIR", self.chart_dir),
            patch.object(analysis_module, "OUTPUT_FILE", self.output_file),
            patch.object(analysis_module, "CHART_FILE", self.chart_file),
        ]

        for patcher in self.patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_analysis_returns_dataframe(self):
        """Analysis should return a Pandas DataFrame."""
        result = analysis_module.analyze_discount_purchases()

        self.assertIsInstance(result, pd.DataFrame)

    def test_result_contains_required_columns(self):
        """Result should contain all expected columns."""
        result = analysis_module.analyze_discount_purchases()

        expected_columns = [
            "discount",
            "customer_count",
            "total_purchases",
            "non_purchases",
            "purchase_rate_percent",
            "discount_group",
        ]

        for column in expected_columns:
            with self.subTest(column=column):
                self.assertIn(column, result.columns)

    def test_result_contains_two_discount_groups(self):
        """Both discount groups should appear in the result."""
        result = analysis_module.analyze_discount_purchases()

        self.assertEqual(set(result["discount"]), {0, 1})

        self.assertEqual(
            set(result["discount_group"]),
            {"No Discount", "Discount"},
        )

    def test_customer_counts_are_correct(self):
        """Customer counts should match the sample dataset."""
        result = analysis_module.analyze_discount_purchases()

        self.assertEqual(result["customer_count"].sum(), 6)

    def test_purchase_counts_are_correct(self):
        """Total purchases should match the sample dataset."""
        result = analysis_module.analyze_discount_purchases()

        self.assertEqual(result["total_purchases"].sum(), 4)

    def test_purchase_rates_are_correct(self):
        """Purchase rates should be calculated correctly."""
        result = analysis_module.analyze_discount_purchases()

        expected_rates = {
            0: 66.67,
            1: 66.67,
        }

        for _, row in result.iterrows():
            expected = expected_rates[row["discount"]]

            self.assertAlmostEqual(
                row["purchase_rate_percent"],
                expected,
                places=2,
            )

    def test_non_purchases_are_correct(self):
        """Non-purchases should equal customers minus purchases."""
        result = analysis_module.analyze_discount_purchases()

        expected = (
            result["customer_count"] - result["total_purchases"]
        )

        pd.testing.assert_series_equal(
            result["non_purchases"],
            expected,
            check_names=False,
        )

    def test_output_csv_is_generated(self):
        """Analysis should generate its CSV report."""
        analysis_module.analyze_discount_purchases()

        self.assertTrue(self.output_file.exists())

        saved_data = pd.read_csv(self.output_file)

        self.assertFalse(saved_data.empty)

    def test_chart_is_generated(self):
        """Analysis should generate its comparison chart."""
        analysis_module.analyze_discount_purchases()

        self.assertTrue(self.chart_file.exists())
        self.assertGreater(self.chart_file.stat().st_size, 0)

    def test_missing_dataset_is_rejected(self):
        """A missing dataset should raise FileNotFoundError."""
        self.data_file.unlink()

        with self.assertRaises(FileNotFoundError):
            analysis_module.analyze_discount_purchases()

    def test_missing_required_column_is_rejected(self):
        """Missing required columns should raise ValueError."""
        invalid_data = self.sample_data.drop(columns=["discount"])
        invalid_data.to_csv(self.data_file, index=False)

        with self.assertRaises(ValueError):
            analysis_module.analyze_discount_purchases()

    def test_empty_dataset_is_rejected(self):
        """An empty dataset should raise ValueError."""
        empty_data = self.sample_data.iloc[0:0]
        empty_data.to_csv(self.data_file, index=False)

        with self.assertRaises(ValueError):
            analysis_module.analyze_discount_purchases()

    def test_missing_values_are_rejected(self):
        """Missing discount or purchase values should be rejected."""
        invalid_data = self.sample_data.copy()
        invalid_data.loc[0, "discount"] = float("nan")
        invalid_data.to_csv(self.data_file, index=False)

        with self.assertRaises(ValueError):
            analysis_module.analyze_discount_purchases()

    def test_invalid_purchase_values_are_rejected(self):
        """Purchase values must be binary."""
        invalid_data = self.sample_data.copy()
        invalid_data["purchase"] = invalid_data["purchase"].astype(object)
        invalid_data.loc[0, "purchase"] = 2
        invalid_data.to_csv(self.data_file, index=False)

        with self.assertRaises(ValueError):
            analysis_module.analyze_discount_purchases()

    def test_invalid_discount_values_are_rejected(self):
        """Discount values must be binary."""
        invalid_data = self.sample_data.copy()
        invalid_data["discount"] = invalid_data["discount"].astype(object)
        invalid_data.loc[0, "discount"] = 2
        invalid_data.to_csv(self.data_file, index=False)

        with self.assertRaises(ValueError):
            analysis_module.analyze_discount_purchases()


if __name__ == "__main__":
    unittest.main(verbosity=2)