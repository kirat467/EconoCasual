import sys
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent

sys.path.insert(0, str(BACKEND_DIR))

from generate_purchase_insights import generate_purchase_insights


REPORT_FILE = PROJECT_DIR / "reports" / "customer_purchase_insights.md"


class TestGeneratePurchaseInsights(unittest.TestCase):

    def test_report_is_generated(self):
        result = generate_purchase_insights()
        self.assertIsInstance(result, str)

    def test_report_file_exists(self):
        generate_purchase_insights()
        self.assertTrue(REPORT_FILE.exists())

    def test_report_contains_dataset_overview(self):
        result = generate_purchase_insights()
        self.assertIn("Dataset Overview", result)

    def test_report_contains_purchase_history(self):
        result = generate_purchase_insights()
        self.assertIn("Purchase History Analysis", result)

    def test_report_contains_engagement_and_discount(self):
        result = generate_purchase_insights()
        self.assertIn("Engagement Analysis", result)
        self.assertIn("Discount Analysis", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)