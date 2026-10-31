import tempfile
import unittest
from pathlib import Path

import pandas as pd

from backend.prepare_datset import (
    generate_dataset,
    validate_dataset,
    run_analysis,
)


class TestPrepareDataset(unittest.TestCase):

    def test_generate_dataset_default_rows(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "customers.csv"
            df = generate_dataset(output_file=output)

            self.assertEqual(len(df), 1000)
            self.assertTrue(output.exists())

    def test_generate_dataset_custom_rows(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "customers.csv"
            df = generate_dataset(n=100, output_file=output)

            self.assertEqual(len(df), 100)

    def test_dataset_has_required_columns(self):
        df = generate_dataset()

        self.assertEqual(
            list(df.columns),
            [
                "customer_id",
                "previous_purchases",
                "engagement",
                "discount",
                "purchase",
            ],
        )

    def test_dataset_is_reproducible(self):
        df1 = generate_dataset(n=50, random_state=42)
        df2 = generate_dataset(n=50, random_state=42)

        pd.testing.assert_frame_equal(df1, df2)

    def test_invalid_customer_count(self):
        with self.assertRaises(ValueError):
            generate_dataset(n=0)

    def test_invalid_random_state(self):
        with self.assertRaises(ValueError):
            generate_dataset(random_state=1.5)

    def test_valid_dataset(self):
        df = generate_dataset(n=50)

        self.assertEqual(validate_dataset(df), [])

    def test_missing_column(self):
        df = generate_dataset(n=20).drop(columns=["purchase"])

        errors = validate_dataset(df)

        self.assertTrue(any("Missing columns" in error for error in errors))

    def test_empty_dataset(self):
        df = generate_dataset(n=20).iloc[0:0]

        errors = validate_dataset(df)

        self.assertIn("Dataset is empty.", errors)

    def test_duplicate_customer_ids(self):
        df = generate_dataset(n=20)
        df.loc[1, "customer_id"] = df.loc[0, "customer_id"]

        errors = validate_dataset(df)

        self.assertIn("Duplicate customer IDs found.", errors)

    def test_invalid_purchase_value(self):
        df = generate_dataset(n=20)
        df["purchase"] = df["purchase"].astype(object)
        df.loc[0, "purchase"] = 3

        errors = validate_dataset(df)

        self.assertIn(
            "Column 'purchase' must contain only 0 or 1.",
            errors,
        )

    def test_missing_values(self):
        df = generate_dataset(n=20)
        df.loc[0, "engagement"] = float("nan")

        errors = validate_dataset(df)

        self.assertIn("Dataset contains missing values.", errors)

    def test_run_analysis(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "customers.csv"

            df = run_analysis(n=25, output_file=output)

            self.assertEqual(len(df), 25)
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()