
import sys
import unittest
from pathlib import Path

import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent

sys.path.insert(0, str(BACKEND_DIR))

from discount_purchase_analysis import analyze_discount_purchases


OUTPUT_FILE = PROJECT_DIR / "reports" / "discount_purchase_analysis.csv"
CHART_FILE = PROJECT_DIR / "reports" / "charts" / "discount_purchase_rate.png"


class TestDiscountPurchaseAnalysis(unittest.TestCase):

    def test_analysis_returns_dataframe(self):
        result = analyze_discount_purchases()
        self.assertIsInstance(result, pd.DataFrame)

    def test_purchase_rates_are_valid(self):
        result = analyze_discount_purchases()
        self.assertTrue(
            result["purchase_rate_percent"].between(0, 100).all()
        )

    def test_output_csv_exists(self):
        analyze_discount_purchases()
        self.assertTrue(OUTPUT_FILE.exists())

    def test_chart_exists(self):
        analyze_discount_purchases()
        self.assertTrue(CHART_FILE.exists())

    def test_required_columns_exist(self):
        result = analyze_discount_purchases()

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

    def test_result_is_not_empty(self):
        result = analyze_discount_purchases()
        self.assertFalse(result.empty)

    def test_customer_counts_are_non_negative(self):
        result = analyze_discount_purchases()

        for column in ["customer_count", "total_purchases", "non_purchases"]:
            with self.subTest(column=column):
                self.assertTrue((result[column] >= 0).all())

    def test_purchases_do_not_exceed_customer_count(self):
        result = analyze_discount_purchases()

        self.assertTrue(
            (result["total_purchases"] <= result["customer_count"]).all()
        )

    def test_purchase_rate_matches_counts(self):
        result = analyze_discount_purchases()
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

    def test_analysis_is_repeatable(self):
        first_result = analyze_discount_purchases()
        second_result = analyze_discount_purchases()

        pd.testing.assert_frame_equal(first_result, second_result)


if __name__ == "__main__":
    unittest.main(verbosity=2)

