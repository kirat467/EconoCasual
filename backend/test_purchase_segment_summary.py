
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


if __name__ == "__main__":
    unittest.main(verbosity=2)

