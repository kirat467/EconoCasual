import tempfile
import unittest
from pathlib import Path

import pandas as pd

from backend.generate_summary import (
    load_customer_data,
    validate_customer_data,
    build_customer_summary,
    generate_summary,
)


class TestGenerateSummary(unittest.TestCase):

    def setUp(self):
        self.df = pd.DataFrame({
            "customer_id": [1, 2, 3, 4],
            "purchase": [1, 1, 0, 1],
            "previous_purchases": [2, 4, 1, 3],
            "engagement": [8, 7, 5, 9],
        })

        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        self.input_file = self.temp_path / "customers.csv"
        self.output_file = self.temp_path / "customer_summary.txt"

        self.df.to_csv(self.input_file, index=False)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_customer_data(self):
        result = load_customer_data(self.input_file)
        self.assertEqual(len(result), 4)

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            load_customer_data(self.temp_path / "missing.csv")

    def test_valid_customer_data(self):
        self.assertEqual(validate_customer_data(self.df), [])

    def test_missing_column(self):
        df = self.df.drop(columns=["engagement"])
        errors = validate_customer_data(df)
        self.assertTrue(any("Missing columns" in error for error in errors))

    def test_empty_dataset(self):
        df = self.df.iloc[0:0]
        errors = validate_customer_data(df)
        self.assertTrue(any("empty" in error.lower() for error in errors))

    def test_missing_values(self):
        df = self.df.copy()
        df.loc[0, "engagement"] = None
        errors = validate_customer_data(df)
        self.assertTrue(any("missing values" in error.lower() for error in errors))

    def test_invalid_purchase_value(self):
        df = self.df.copy()
        df["purchase"] = df["purchase"].astype(object)
        df.loc[0, "purchase"] = 5
        errors = validate_customer_data(df)
        self.assertTrue(any("0 or 1" in error for error in errors))

    def test_negative_previous_purchases(self):
        df = self.df.copy()
        df.loc[0, "previous_purchases"] = -2
        errors = validate_customer_data(df)
        self.assertTrue(any("negative" in error.lower() for error in errors))

    def test_invalid_engagement(self):
        df = self.df.copy()
        df.loc[0, "engagement"] = 11
        errors = validate_customer_data(df)
        self.assertTrue(any("between 1 and 10" in error for error in errors))

    def test_build_customer_summary(self):
        summary = build_customer_summary(self.df)
        self.assertIn("Total Customers: 4", summary)
        self.assertIn("Total Purchases: 3", summary)
        self.assertIn("Total Non-Purchases: 1", summary)
        self.assertIn("Overall Purchase Rate: 75.00%", summary)

    def test_build_summary_rejects_invalid_data(self):
        df = self.df.copy()
        df.loc[0, "purchase"] = 8

        with self.assertRaises(ValueError):
            build_customer_summary(df)

    def test_generate_summary(self):
        summary = generate_summary(
            self.input_file,
            self.output_file
        )

        self.assertTrue(self.output_file.exists())
        self.assertEqual(
            self.output_file.read_text(encoding="utf-8"),
            summary
        )


if __name__ == "__main__":
    unittest.main()