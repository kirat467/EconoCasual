import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from backend import purchase_trend_analysis as analysis


class TestPurchaseTrendAnalysis(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)

        self.data_dir = self.base_dir / "data"
        self.report_dir = self.base_dir / "reports"
        self.chart_dir = self.report_dir / "charts"

        self.data_dir.mkdir(parents=True)

        self.data_file = self.data_dir / "customers.csv"
        self.output_file = self.report_dir / "purchase_trend_analysis.csv"
        self.chart_file = self.chart_dir / "purchase_trend_by_history.png"

        self.data = pd.DataFrame({
            "customer_id": [1, 2, 3, 4, 5, 6],
            "previous_purchases": [0, 0, 1, 1, 2, 2],
            "purchase": [0, 1, 1, 0, 1, 1],
        })

        self.data.to_csv(self.data_file, index=False)

        self.patcher = patch.multiple(
            analysis,
            DATA_FILE=self.data_file,
            REPORT_DIR=self.report_dir,
            CHART_DIR=self.chart_dir,
            OUTPUT_FILE=self.output_file,
            CHART_FILE=self.chart_file,
        )
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.temp_dir.cleanup()

    def write_data(self, dataframe):
        dataframe.to_csv(self.data_file, index=False)

    def test_analysis_returns_dataframe(self):
        result = analysis.analyze_purchase_trends()

        self.assertIsInstance(result, pd.DataFrame)

    def test_analysis_groups_previous_purchase_counts(self):
        result = analysis.analyze_purchase_trends()

        self.assertEqual(
            result["previous_purchases"].tolist(),
            [0, 1, 2],
        )

    def test_customer_counts_are_correct(self):
        result = analysis.analyze_purchase_trends()

        self.assertEqual(
            result["customer_count"].tolist(),
            [2, 2, 2],
        )

    def test_total_purchases_are_correct(self):
        result = analysis.analyze_purchase_trends()

        self.assertEqual(
            result["total_purchases"].tolist(),
            [1, 1, 2],
        )

    def test_purchase_rates_are_correct(self):
        result = analysis.analyze_purchase_trends()

        self.assertEqual(
            result["purchase_rate_percent"].tolist(),
            [50.0, 50.0, 100.0],
        )

    def test_output_has_expected_columns(self):
        result = analysis.analyze_purchase_trends()

        expected_columns = [
            "previous_purchases",
            "customer_count",
            "total_purchases",
            "purchase_rate_percent",
        ]

        self.assertEqual(result.columns.tolist(), expected_columns)

    def test_internal_purchase_rate_is_not_in_output(self):
        result = analysis.analyze_purchase_trends()

        self.assertNotIn("purchase_rate", result.columns)

    def test_output_csv_is_created(self):
        analysis.analyze_purchase_trends()

        self.assertTrue(self.output_file.exists())

    def test_chart_is_created(self):
        analysis.analyze_purchase_trends()

        self.assertTrue(self.chart_file.exists())

    def test_saved_csv_matches_returned_summary(self):
        result = analysis.analyze_purchase_trends()
        saved_result = pd.read_csv(self.output_file)

        pd.testing.assert_frame_equal(
            saved_result,
            result,
            check_dtype=False,
        )

    def test_purchase_rates_remain_between_zero_and_one_hundred(self):
        result = analysis.analyze_purchase_trends()

        self.assertTrue(
            result["purchase_rate_percent"].between(0, 100).all()
        )

    def test_total_purchases_do_not_exceed_customer_count(self):
        result = analysis.analyze_purchase_trends()

        self.assertTrue(
            (
                result["total_purchases"]
                <= result["customer_count"]
            ).all()
        )

    def test_customer_counts_are_positive(self):
        result = analysis.analyze_purchase_trends()

        self.assertTrue((result["customer_count"] > 0).all())

    def test_missing_dataset_raises_file_not_found_error(self):
        self.data_file.unlink()

        with self.assertRaises(FileNotFoundError):
            analysis.analyze_purchase_trends()

    def test_missing_required_column_raises_value_error(self):
        invalid_data = self.data.drop(columns=["purchase"])
        self.write_data(invalid_data)

        with self.assertRaises(ValueError):
            analysis.analyze_purchase_trends()

    def test_empty_dataset_raises_value_error(self):
        empty_data = pd.DataFrame(columns=[
            "customer_id",
            "previous_purchases",
            "purchase",
        ])
        self.write_data(empty_data)

        with self.assertRaises(ValueError):
            analysis.analyze_purchase_trends()

    def test_invalid_purchase_value_raises_value_error(self):
        invalid_data = self.data.copy()
        invalid_data["purchase"] = invalid_data["purchase"].astype(object)
        invalid_data.loc[0, "purchase"] = 2
        self.write_data(invalid_data)

        with self.assertRaises(ValueError):
            analysis.analyze_purchase_trends()

    def test_non_numeric_purchase_value_raises_error(self):
        invalid_data = self.data.copy()
        invalid_data["purchase"] = invalid_data["purchase"].astype(object)
        invalid_data.loc[0, "purchase"] = "invalid"
        self.write_data(invalid_data)

        with self.assertRaises((ValueError, TypeError)):
            analysis.analyze_purchase_trends()

    def test_non_numeric_previous_purchases_raises_error(self):
        invalid_data = self.data.copy()
        invalid_data["previous_purchases"] = (
            invalid_data["previous_purchases"].astype(object)
        )
        invalid_data.loc[0, "previous_purchases"] = "invalid"
        self.write_data(invalid_data)

        with self.assertRaises((ValueError, TypeError)):
            analysis.analyze_purchase_trends()

    def test_missing_previous_purchases_are_rejected(self):
        invalid_data = self.data.copy()
        invalid_data.loc[0, "previous_purchases"] = float("nan")
        self.write_data(invalid_data)

        with self.assertRaises(ValueError):
            analysis.analyze_purchase_trends()


if __name__ == "__main__":
    unittest.main(verbosity=2)