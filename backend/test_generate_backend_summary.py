import sys
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent

sys.path.insert(0, str(BACKEND_DIR))

from generate_backend_summary import generate_backend_summary


REPORT_FILE = PROJECT_DIR / "reports" / "backend_summary.md"


class TestGenerateBackendSummary(unittest.TestCase):

    def test_report_returns_text(self):
        result = generate_backend_summary()
        self.assertIsInstance(result, str)

    def test_report_contains_project_title(self):
        result = generate_backend_summary()
        self.assertIn("# EconoCasual Backend Summary Report", result)

    def test_report_contains_purchase_statistics(self):
        result = generate_backend_summary()
        self.assertIn("Total customers:", result)
        self.assertIn("Overall purchase rate:", result)

    def test_report_contains_analysis_sections(self):
        result = generate_backend_summary()
        self.assertIn("Discount Analysis", result)
        self.assertIn("Engagement Analysis", result)
        self.assertIn("Previous Purchase History", result)

    def test_report_file_exists(self):
        generate_backend_summary()
        self.assertTrue(REPORT_FILE.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)