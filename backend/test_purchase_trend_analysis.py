import subprocess
import unittest
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
PYTHON_EXE = BASE_DIR / ".venv" / "Scripts" / "python.exe"
SCRIPT_FILE = BASE_DIR / "backend" / "purchase_trend_analysis.py"
INPUT_FILE = BASE_DIR / "data" / "customers.csv"
OUTPUT_FILE = BASE_DIR / "reports" / "purchase_trend_analysis.csv"
CHART_FILE = BASE_DIR / "reports" / "charts" / "purchase_trend_by_history.png"

class TestPurchaseTrendAnalysis(unittest.TestCase):


  def test_analysis_script_exists(self):
    self.assertTrue(SCRIPT_FILE.exists())

  def test_customer_dataset_exists(self):
    self.assertTrue(INPUT_FILE.exists())

  def test_analysis_runs_successfully(self):
    result = subprocess.run(
        [str(PYTHON_EXE), str(SCRIPT_FILE)],
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
    )

    self.assertEqual(
        result.returncode,
        0,
        msg=f"Analysis failed:\n{result.stderr}",
    )

def test_output_csv_exists(self):
    self.assertTrue(OUTPUT_FILE.exists())

def test_output_columns(self):
    self.assertTrue(OUTPUT_FILE.exists())

    result = pd.read_csv(OUTPUT_FILE)

    expected_columns = [
        "previous_purchases",
        "customer_count",
        "total_purchases",
        "purchase_rate_percent",
    ]

    for column in expected_columns:
        self.assertIn(column, result.columns)

def test_purchase_rates_are_valid(self):
    self.assertTrue(OUTPUT_FILE.exists())

    result = pd.read_csv(OUTPUT_FILE)

    self.assertTrue(
        result["purchase_rate_percent"].between(0, 100).all()
    )

def test_chart_exists(self):
    self.assertTrue(CHART_FILE.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
