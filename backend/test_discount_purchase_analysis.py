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
            self.assertIn(column, result.columns)


if __name__ == "__main__":
    unittest.main(verbosity=2)