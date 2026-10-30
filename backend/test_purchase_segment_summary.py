
import sys
import unittest
from pathlib import Path

import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent

sys.path.insert(0, str(BACKEND_DIR))

from purchase_segment_summary import generate_purchase_segment_summary


CSV_FILE = PROJECT_DIR / "reports" / "purchase_segment_summary.csv"
CHART_FILE = PROJECT_DIR / "reports" / "charts" / "purchase_segment_purchase_rate.png"


class TestPurchaseSegmentSummary(unittest.TestCase):

    def test_summary_returns_dataframe(self):
        result = generate_purchase_segment_summary()
        self.assertIsInstance(result, pd.DataFrame)

    def test_all_segments_are_present(self):
        result = generate_purchase_segment_summary()

        self.assertEqual(
            set(result["purchase_segment"].astype(str)),
            {"Low", "Medium", "High"},
        )

    def test_purchase_rates_are_valid(self):
        result = generate_purchase_segment_summary()
        valid_rates = result["purchase_rate_percent"].dropna()

        self.assertTrue(valid_rates.between(0, 100).all())

    def test_csv_report_exists(self):
        generate_purchase_segment_summary()
        self.assertTrue(CSV_FILE.exists())

    def test_chart_exists(self):
        generate_purchase_segment_summary()
        self.assertTrue(CHART_FILE.exists())

    def test_result_is_not_empty(self):
        result = generate_purchase_segment_summary()
        self.assertFalse(result.empty)

    def test_required_columns_exist(self):
        result = generate_purchase_segment_summary()

        expected_columns = [
            "purchase_segment",
            "customer_count",
            "total_purchases",
            "purchase_rate_percent",
        ]

        for column in expected_columns:
            with self.subTest(column=column):
                self.assertIn(column, result.columns)

    def test_customer_counts_are_non_negative(self):
        result = generate_purchase_segment_summary()

        self.assertTrue((result["customer_count"] >= 0).all())

    def test_purchases_do_not_exceed_customer_counts(self):
        result = generate_purchase_segment_summary()

        self.assertTrue(
            (result["total_purchases"] <= result["customer_count"]).all()
        )

    def test_purchase_rates_match_counts(self):
        result = generate_purchase_segment_summary()
        valid_rows = result["customer_count"] > 0

        expected_rates = (
            result.loc[valid_rows, "total_purchases"]
            / result.loc[valid_rows, "customer_count"]
            * 100
        )

        actual_rates = result.loc[valid_rows, "purchase_rate_percent"]

        self.assertTrue(
            (expected_rates.round(2) == actual_rates.round(2)).all()
        )

    def test_summary_is_repeatable(self):
        first_result = generate_purchase_segment_summary()
        second_result = generate_purchase_segment_summary()

        pd.testing.assert_frame_equal(first_result, second_result)


if __name__ == "__main__":
    unittest.main(verbosity=2)

