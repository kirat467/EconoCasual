import subprocess
import sys
import unittest
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
PYTHON_EXE = BASE_DIR / ".venv" / "Scripts" / "python.exe"
SCRIPT_FILE = BASE_DIR / "backend" / "compare_segments_report.py"
INPUT_FILE = BASE_DIR / "reports" / "segment_comparison.csv"
REPORT_FILE = BASE_DIR / "reports" / "segment_comparison_report.md"


class TestCompareSegmentsReport(unittest.TestCase):

    def test_script_exists(self):
        self.assertTrue(SCRIPT_FILE.exists())

    def test_comparison_file_exists(self):
        self.assertTrue(INPUT_FILE.exists())

    def test_report_generation(self):
        result = subprocess.run(
            [str(PYTHON_EXE), str(SCRIPT_FILE)],
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

    def test_report_sections(self):
        self.assertTrue(REPORT_FILE.exists())
        content = REPORT_FILE.read_text(encoding="utf-8")

        self.assertIn("# Customer Segment Comparison Report", content)
        self.assertIn("## 1. Overview", content)
        self.assertIn("## 2. Segment Comparison", content)
        self.assertIn("## 3. Key Findings", content)
        self.assertIn("## 5. Limitations", content)

    def test_report_statistics(self):
        self.assertTrue(REPORT_FILE.exists())
        content = REPORT_FILE.read_text(encoding="utf-8")

        self.assertIn("Total purchases:", content)
        self.assertIn("Overall purchase rate:", content)
        self.assertIn("Highest purchase-rate combination:", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)