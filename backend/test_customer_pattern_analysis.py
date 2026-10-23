
import unittest
from pathlib import Path

import pandas as pd

from customer_pattern_analysis import analyze_customer_patterns


BASE_DIR = Path(__file__).resolve().parent.parent
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
            self.assertIn(column, result.columns)


if __name__ == "__main__":
    unittest.main(verbosity=2)

