
import sys
import unittest
from pathlib import Path

import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent

sys.path.insert(0, str(BACKEND_DIR))

from purchase_correlation_analysis import analyze_purchase_correlations


CSV_FILE = PROJECT_DIR / "reports" / "purchase_correlation_analysis.csv"
CHART_FILE = PROJECT_DIR / "reports" / "charts" / "purchase_correlation_heatmap.png"


class TestPurchaseCorrelationAnalysis(unittest.TestCase):

    def test_analysis_returns_dataframe(self):
        result = analyze_purchase_correlations()
        self.assertIsInstance(result, pd.DataFrame)

    def test_correlation_values_are_valid(self):
        result = analyze_purchase_correlations()
        values = result.to_numpy()
        self.assertTrue(
            ((values >= -1) & (values <= 1)).all()
        )

    def test_required_columns_exist(self):
        result = analyze_purchase_correlations()

        expected_columns = [
            "previous_purchases",
            "engagement",
            "discount",
            "purchase",
        ]

        for column in expected_columns:
            self.assertIn(column, result.columns)
            self.assertIn(column, result.index)

    def test_csv_report_exists(self):
        analyze_purchase_correlations()
        self.assertTrue(CSV_FILE.exists())

    def test_heatmap_exists(self):
        analyze_purchase_correlations()
        self.assertTrue(CHART_FILE.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)

