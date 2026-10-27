
import unittest
import subprocess
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_PYTHON = BASE_DIR / ".venv" / "Scripts" / "python.exe"
REPORT_SCRIPT = BASE_DIR / "backend" / "segment_report.py"
SUMMARY_FILE = BASE_DIR / "reports" / "customer_segments_summary.csv"
REPORT_FILE = BASE_DIR / "reports" / "customer_segmentation_report.md"


class TestSegmentReport(unittest.TestCase):

    def test_report_script_exists(self):
        self.assertTrue(REPORT_SCRIPT.exists())

    def test_summary_file_exists(self):
        self.assertTrue(SUMMARY_FILE.exists())

    def test_report_generation(self):
        result = subprocess.run(
            [str(PROJECT_PYTHON), str(REPORT_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=BASE_DIR,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=f"Report generation failed:\n{result.stderr}",
        )
        self.assertTrue(REPORT_FILE.exists())

    def test_report_has_required_sections(self):
        result = subprocess.run(
            [str(PROJECT_PYTHON), str(REPORT_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=BASE_DIR,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=f"Report generation failed:\n{result.stderr}",
        )

        content = REPORT_FILE.read_text(encoding="utf-8")

        expected_sections = [
            "# Customer Segmentation Analysis Report",
            "## 1. Overview",
            "## 2. Segment Summary",
            "## 3. Key Findings",
            "## 5. Limitations",
        ]

        for section in expected_sections:
            with self.subTest(section=section):
                self.assertIn(section, content)

    def test_report_has_purchase_statistics(self):
        content = REPORT_FILE.read_text(encoding="utf-8")

        expected_labels = [
            "Total customers analyzed:",
            "Total purchases:",
            "Overall purchase rate:",
        ]

        for label in expected_labels:
            with self.subTest(label=label):
                self.assertIn(label, content)

    def test_report_is_not_empty(self):
        self.assertTrue(REPORT_FILE.exists())
        content = REPORT_FILE.read_text(encoding="utf-8")
        self.assertTrue(content.strip())

    def test_report_uses_markdown_format(self):
        self.assertTrue(REPORT_FILE.exists())
        content = REPORT_FILE.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("# "))

    def test_summary_file_is_not_empty(self):
        self.assertTrue(SUMMARY_FILE.exists())
        self.assertGreater(SUMMARY_FILE.stat().st_size, 0)

    def test_report_generation_is_repeatable(self):
        first_run = subprocess.run(
            [str(PROJECT_PYTHON), str(REPORT_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=BASE_DIR,
        )

        self.assertEqual(
            first_run.returncode,
            0,
            msg=f"First report generation failed:\n{first_run.stderr}",
        )

        first_content = REPORT_FILE.read_text(encoding="utf-8")

        second_run = subprocess.run(
            [str(PROJECT_PYTHON), str(REPORT_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=BASE_DIR,
        )

        self.assertEqual(
            second_run.returncode,
            0,
            msg=f"Second report generation failed:\n{second_run.stderr}",
        )

        second_content = REPORT_FILE.read_text(encoding="utf-8")
        self.assertEqual(first_content, second_content)


if __name__ == "__main__":
    unittest.main(verbosity=2)

