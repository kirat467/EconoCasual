import sys
import unittest
from pathlib import Path
from unittest.mock import patch

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent

sys.path.insert(0, str(BACKEND_DIR))

from generate_purchase_insights import generate_purchase_insights

REPORT_FILE = PROJECT_DIR / "reports" / "customer_purchase_insights.md"

class TestGeneratePurchaseInsights(unittest.TestCase):


 def test_report_is_generated(self):
    result = generate_purchase_insights()
    self.assertIsInstance(result, str)
    self.assertGreater(len(result), 0)

 def test_report_file_exists(self):
    generate_purchase_insights()
    self.assertTrue(REPORT_FILE.exists())

 def test_report_file_matches_generated_content(self):
    result = generate_purchase_insights()
    saved_content = REPORT_FILE.read_text(encoding="utf-8")
    self.assertEqual(saved_content, result)

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

 def test_report_contains_all_expected_sections(self):
    result = generate_purchase_insights()

    expected_sections = [
        "Dataset Overview",
        "Purchase History Analysis",
        "Engagement Analysis",
        "Discount Analysis",
    ]

    for section in expected_sections:
        with self.subTest(section=section):
            self.assertIn(section, result)

 def test_report_has_markdown_heading(self):
    result = generate_purchase_insights()
    self.assertIn("#", result)

 def test_report_file_is_not_empty(self):
    generate_purchase_insights()

    self.assertGreater(REPORT_FILE.stat().st_size, 0)

 def test_report_generation_is_repeatable(self):
    first_result = generate_purchase_insights()
    second_result = generate_purchase_insights()

    self.assertEqual(first_result, second_result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
