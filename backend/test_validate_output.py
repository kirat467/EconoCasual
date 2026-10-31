import tempfile
import unittest
from pathlib import Path

import pandas as pd

from backend import validate_outputs


class TestValidateOutputs(unittest.TestCase):

    def setUp(self):
        # Valid customer insights sample dataset.
        self.df = pd.DataFrame({
            "customer_id": [1, 2, 3],
            "previous_purchases": [2, 4, 5],
            "engagement": [5, 8, 7],
            "discount": [0, 1, 0],
            "purchase": [1, 0, 1],
            "customer_segment": ["Loyal", "New", "Loyal"],
            "loyalty_level": ["High", "Low", "High"],
        })

        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "customer_insights.csv"

        self.df.to_csv(self.file_path, index=False)

    def tearDown(self):
        # Temporary test files clean up karo.
        self.temp_dir.cleanup()

    def test_valid_customer_insights(self):
        result = validate_outputs.validate_customer_insights(self.file_path)

        self.assertTrue(result["is_valid"])
        self.assertEqual(result["total_rows"], 3)
        self.assertEqual(result["total_columns"], 7)
        self.assertEqual(result["missing_values"], 0)
        self.assertEqual(result["duplicate_customer_ids"], 0)
        self.assertEqual(result["errors"], [])

    def test_missing_file(self):
        missing_path = Path(self.temp_dir.name) / "missing.csv"

        with self.assertRaises(FileNotFoundError):
            validate_outputs.validate_customer_insights(missing_path)

    def test_missing_customer_id_column(self):
        df = self.df.drop(columns=["customer_id"])
        df.to_csv(self.file_path, index=False)

        result = validate_outputs.validate_customer_insights(self.file_path)

        self.assertFalse(result["is_valid"])
        self.assertIsNone(result["duplicate_customer_ids"])

        error_types = [error["type"] for error in result["errors"]]
        self.assertIn("missing_customer_id_column", error_types)

    def test_duplicate_customer_ids(self):
        df = self.df.copy()
        df.loc[2, "customer_id"] = 1
        df.to_csv(self.file_path, index=False)

        result = validate_outputs.validate_customer_insights(self.file_path)

        self.assertFalse(result["is_valid"])
        self.assertEqual(result["duplicate_customer_ids"], 1)

        error_types = [error["type"] for error in result["errors"]]
        self.assertIn("duplicate_customer_ids", error_types)

    def test_missing_values(self):
        df = self.df.copy()
        df.loc[0, "engagement"] = None
        df.to_csv(self.file_path, index=False)

        result = validate_outputs.validate_customer_insights(self.file_path)

        self.assertFalse(result["is_valid"])
        self.assertEqual(result["missing_values"], 1)

        error_types = [error["type"] for error in result["errors"]]
        self.assertIn("missing_values", error_types)

    def test_empty_dataset(self):
        df = self.df.iloc[0:0]
        df.to_csv(self.file_path, index=False)

        result = validate_outputs.validate_customer_insights(self.file_path)

        self.assertTrue(result["is_valid"])
        self.assertEqual(result["total_rows"], 0)

    def test_run_validation(self):
        result = validate_outputs.run_validation(self.file_path)

        self.assertTrue(result["is_valid"])


if __name__ == "__main__":
    unittest.main()