
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

        expected_sections = [
            "Discount Analysis",
            "Engagement Analysis",
            "Previous Purchase History",
        ]

        for section in expected_sections:
            with self.subTest(section=section):
                self.assertIn(section, result)

    def test_report_file_exists(self):
        generate_backend_summary()
        self.assertTrue(REPORT_FILE.exists())

    def test_report_file_contains_generated_content(self):
        result = generate_backend_summary()
        self.assertEqual(
            REPORT_FILE.read_text(encoding="utf-8"),
            result,
        )

    def test_report_is_not_empty(self):
        result = generate_backend_summary()
        self.assertTrue(result.strip())

    def test_report_is_markdown(self):
        result = generate_backend_summary()
        self.assertTrue(result.startswith("# "))

    def test_report_contains_customer_count_label(self):
        result = generate_backend_summary()
        self.assertIn("Total customers:", result)

    def test_report_generation_is_repeatable(self):
        first_result = generate_backend_summary()
        second_result = generate_backend_summary()
        self.assertEqual(first_result, second_result)

    def test_report_contains_markdown_table_structure(self):
        result = generate_backend_summary()
        self.assertIn("|", result)

    def test_purchase_rate_is_within_valid_range(self):
        result = generate_backend_summary()

        rate_line = next(
            (
                line for line in result.splitlines()
                if "Overall purchase rate:" in line
            ),
            None,
        )

        self.assertIsNotNone(rate_line)

        import re

        match = re.search(r"(\d+(?:\.\d+)?)%", rate_line)
        self.assertIsNotNone(match)

        rate = float(match.group(1))
        self.assertGreaterEqual(rate, 0)
        self.assertLessEqual(rate, 100)


if __name__ == "__main__":
    unittest.main(verbosity=2)
