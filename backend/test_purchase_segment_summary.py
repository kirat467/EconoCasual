import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

import purchase_segment_summary as analysis


class TestPurchaseSegmentSummary(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.temp_path = Path(self.temp_dir.name)
        self.data_file = self.temp_path / "customers.csv"

        self.test_data = pd.DataFrame({
            "customer_id": [1, 2, 3, 4, 5, 6],
            "previous_purchases": [0, 2, 3, 5, 6, 8],
            "purchase": [0, 1, 0, 1, 1, 1],
        })

        self.test_data.to_csv(self.data_file, index=False)

        self.report_dir = self.temp_path / "reports"
        self.chart_dir = self.report_dir / "charts"

        self.output_file = (
            self.report_dir / "purchase_segment_summary.csv"
        )

        self.chart_file = (
            self.chart_dir / "purchase_segment_purchase_rate.png"
        )

        patchers = [
            patch.object(analysis, "DATA_FILE", self.data_file),
            patch.object(analysis, "REPORT_DIR", self.report_dir),
            patch.object(analysis, "CHART_DIR", self.chart_dir),
            patch.object(analysis, "OUTPUT_FILE", self.output_file),
            patch.object(analysis, "CHART_FILE", self.chart_file),
        ]

        for patcher in patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_summary_returns_dataframe(self):
        result = analysis.generate_purchase_segment_summary()

        self.assertIsInstance(result, pd.DataFrame)

    def test_all_segments_are_present(self):
        result = analysis.generate_purchase_segment_summary()

        self.assertEqual(
            set(result["purchase_segment"].astype(str)),
            {"Low", "Medium", "High"},
        )

    def test_expected_segment_counts(self):
        result = analysis.generate_purchase_segment_summary()

        counts = result.set_index("purchase_segment")["customer_count"]

        self.assertEqual(counts["Low"], 2)
        self.assertEqual(counts["Medium"], 2)
        self.assertEqual(counts["High"], 2)

    def test_total_purchases_are_correct(self):
        result = analysis.generate_purchase_segment_summary()

        purchases = result.set_index("purchase_segment")["total_purchases"]

        self.assertEqual(purchases["Low"], 1)
        self.assertEqual(purchases["Medium"], 1)
        self.assertEqual(purchases["High"], 2)

    def test_purchase_rates_are_correct(self):
        result = analysis.generate_purchase_segment_summary()

        rates = result.set_index("purchase_segment")[
            "purchase_rate_percent"
        ]

        self.assertEqual(rates["Low"], 50.0)
        self.assertEqual(rates["Medium"], 50.0)
        self.assertEqual(rates["High"], 100.0)

    def test_non_purchases_are_correct(self):
        result = analysis.generate_purchase_segment_summary()

        non_purchases = result.set_index("purchase_segment")[
            "non_purchases"
        ]

        self.assertEqual(non_purchases["Low"], 1)
        self.assertEqual(non_purchases["Medium"], 1)
        self.assertEqual(non_purchases["High"], 0)

    def test_required_columns_exist(self):
        result = analysis.generate_purchase_segment_summary()

        expected = [
            "purchase_segment",
            "customer_count",
            "total_purchases",
            "average_previous_purchases",
            "non_purchases",
            "purchase_rate_percent",
        ]

        self.assertEqual(result.columns.tolist(), expected)

    def test_purchase_rates_are_within_valid_range(self):
        result = analysis.generate_purchase_segment_summary()

        valid_rates = result["purchase_rate_percent"].dropna()

        self.assertTrue(valid_rates.between(0, 100).all())

    def test_customer_counts_are_non_negative(self):
        result = analysis.generate_purchase_segment_summary()

        self.assertTrue((result["customer_count"] >= 0).all())

    def test_purchases_do_not_exceed_customer_counts(self):
        result = analysis.generate_purchase_segment_summary()

        self.assertTrue(
            (
                result["total_purchases"]
                <= result["customer_count"]
            ).all()
        )

    def test_csv_report_is_created(self):
        analysis.generate_purchase_segment_summary()

        self.assertTrue(self.output_file.exists())
        self.assertGreater(self.output_file.stat().st_size, 0)

    def test_saved_csv_matches_result(self):
        result = analysis.generate_purchase_segment_summary()

        saved_result = pd.read_csv(self.output_file)

        expected_result = result.copy()
        expected_result["purchase_segment"] = (
            expected_result["purchase_segment"].astype(str)
        )

        pd.testing.assert_frame_equal(
            saved_result,
            expected_result,
            check_dtype=False,
        )

    def test_chart_is_created(self):
        analysis.generate_purchase_segment_summary()

        self.assertTrue(self.chart_file.exists())
        self.assertGreater(self.chart_file.stat().st_size, 0)

    def test_missing_dataset_raises_error(self):
        with patch.object(
            analysis,
            "DATA_FILE",
            self.temp_path / "missing.csv",
        ):
            with self.assertRaises(FileNotFoundError):
                analysis.generate_purchase_segment_summary()

    def test_missing_columns_raise_error(self):
        invalid_data = pd.DataFrame({
            "customer_id": [1],
            "purchase": [1],
        })

        invalid_data.to_csv(self.data_file, index=False)

        with self.assertRaisesRegex(
            ValueError,
            "Missing required columns",
        ):
            analysis.generate_purchase_segment_summary()

    def test_empty_dataset_raises_error(self):
        empty_data = pd.DataFrame(columns=[
            "customer_id",
            "previous_purchases",
            "purchase",
        ])

        empty_data.to_csv(self.data_file, index=False)

        with self.assertRaisesRegex(ValueError, "empty"):
            analysis.generate_purchase_segment_summary()

    def test_invalid_numeric_values_raise_error(self):
        invalid_data = self.test_data.copy()

        invalid_data["previous_purchases"] = (
            invalid_data["previous_purchases"].astype(object)
        )

        invalid_data.loc[0, "previous_purchases"] = "invalid"
        invalid_data.to_csv(self.data_file, index=False)

        with self.assertRaises(ValueError):
            analysis.generate_purchase_segment_summary()

    def test_missing_numeric_values_raise_error(self):
        invalid_data = self.test_data.copy()

        invalid_data.loc[0, "purchase"] = None
        invalid_data.to_csv(self.data_file, index=False)

        with self.assertRaisesRegex(ValueError, "missing values"):
            analysis.generate_purchase_segment_summary()

    def test_invalid_purchase_values_raise_error(self):
        invalid_data = self.test_data.copy()

        invalid_data.loc[0, "purchase"] = 2
        invalid_data.to_csv(self.data_file, index=False)

        with self.assertRaisesRegex(ValueError, "0 or 1"):
            analysis.generate_purchase_segment_summary()

    def test_summary_is_repeatable(self):
        first_result = analysis.generate_purchase_segment_summary()
        second_result = analysis.generate_purchase_segment_summary()

        pd.testing.assert_frame_equal(first_result, second_result)


if __name__ == "__main__":
    unittest.main(verbosity=2)

