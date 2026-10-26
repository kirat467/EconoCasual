import unittest
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_PYTHON = BASE_DIR / ".venv" / "Scripts" / "python.exe"
REPORT_SCRIPT = BASE_DIR / "backend" / "segment_report.py"
REPORT_FILE = BASE_DIR / "reports" / "customer_segmentation_report.md"


class TestSegmentReport(unittest.TestCase):

    def test_report_script_exists(self):
        self.assertTrue(REPORT_SCRIPT.exists())

    def test_summary_file_exists(self):
        summary_file = BASE_DIR / "reports" / "customer_segments_summary.csv"
        self.assertTrue(summary_file.exists())

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
        self.assertTrue(REPORT_FILE.exists())

        content = REPORT_FILE.read_text(encoding="utf-8")

        self.assertIn("# Customer Segmentation Analysis Report", content)
        self.assertIn("## 1. Overview", content)
        self.assertIn("## 2. Segment Summary", content)
        self.assertIn("## 3. Key Findings", content)
        self.assertIn("## 5. Limitations", content)

    def test_report_has_purchase_statistics(self):
        self.assertTrue(REPORT_FILE.exists())

        content = REPORT_FILE.read_text(encoding="utf-8")

        self.assertIn("Total customers analyzed:", content)
        self.assertIn("Total purchases:", content)
        self.assertIn("Overall purchase rate:", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)