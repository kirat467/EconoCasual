import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent

sys.path.insert(0, str(BACKEND_DIR))

from customer_pattern_analysis import analyze_customer_patterns


OUTPUT_FILE = BASE_DIR / "reports" / "customer_pattern_analysis.csv"
CHART_FILE = BASE_DIR / "reports" / "charts" / "customer_purchase_patterns.png"


class TestCustomerPatternAnalysis(unittest.TestCase):

    def test_analysis_returns_dataframe(self):
        result = analyze_customer_patterns()
        self.assertIsInstance(result, pd.DataFrame)

    def test_purchase_rates_are_valid(self):
        result = analyze_customer_patterns()
        self.assertTrue(
            result["purchase_rate_percent"].between(0, 100).all()
        )

    def test_output_csv_exists(self):
        analyze_customer_patterns()
        self.assertTrue(OUTPUT_FILE.exists())

    def test_chart_exists(self):
        analyze_customer_patterns()
        self.assertTrue(CHART_FILE.exists())

    def test_required_columns_exist(self):
        result = analyze_customer_patterns()

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

    def test_result_is_not_empty(self):
        result = analyze_customer_patterns()
        self.assertFalse(result.empty)

    def test_customer_counts_are_non_negative(self):
        result = analyze_customer_patterns()

        for column in ["customer_count", "purchasers", "non_purchasers"]:
            with self.subTest(column=column):
                self.assertTrue((result[column] >= 0).all())

    def test_purchasers_do_not_exceed_customer_count(self):
        result = analyze_customer_patterns()

        self.assertTrue(
            (result["purchasers"] <= result["customer_count"]).all()
        )

    def test_purchase_rate_matches_counts(self):
        result = analyze_customer_patterns()

        valid_rows = result["customer_count"] > 0
        expected_rates = (
            result.loc[valid_rows, "purchasers"]
            / result.loc[valid_rows, "customer_count"]
            * 100
        )

        actual_rates = result.loc[valid_rows, "purchase_rate_percent"]

        self.assertTrue(
            (expected_rates.round(2) == actual_rates.round(2)).all()
        )

    def test_analysis_is_repeatable(self):
        first_result = analyze_customer_patterns()
        second_result = analyze_customer_patterns()

        pd.testing.assert_frame_equal(first_result, second_result)


if __name__ == "__main__":
    unittest.main(verbosity=2)