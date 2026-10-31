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
        """Default generation should create 1000 customers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "customers.csv"

            df = generate_dataset(output_file=output)

            self.assertEqual(len(df), 1000)
            self.assertTrue(output.exists())

    def test_generate_dataset_custom_rows(self):
        """Custom generation should use the requested row count."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "customers.csv"

            df = generate_dataset(
                n=100,
                output_file=output,
            )

            self.assertEqual(len(df), 100)
            self.assertTrue(output.exists())

    def test_dataset_has_required_columns(self):
        """Generated dataset should contain all required columns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "customers.csv"

            df = generate_dataset(output_file=output)

            expected_columns = [
                "customer_id",
                "previous_purchases",
                "engagement",
                "discount",
                "purchase",
            ]

            self.assertEqual(list(df.columns), expected_columns)

    def test_dataset_is_reproducible(self):
        """Same random state should produce identical data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output1 = Path(temp_dir) / "customers1.csv"
            output2 = Path(temp_dir) / "customers2.csv"

            df1 = generate_dataset(
                n=50,
                random_state=42,
                output_file=output1,
            )

            df2 = generate_dataset(
                n=50,
                random_state=42,
                output_file=output2,
            )

            pd.testing.assert_frame_equal(df1, df2)

    def test_invalid_customer_count(self):
        """Zero customers should raise ValueError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "customers.csv"

            with self.assertRaises(ValueError):
                generate_dataset(
                    n=0,
                    output_file=output,
                )

    def test_invalid_random_state(self):
        """Non-integer random state should raise ValueError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "customers.csv"

            with self.assertRaises(ValueError):
                generate_dataset(
                    random_state=1.5,
                    output_file=output,
                )

    def test_valid_dataset(self):
        """Generated dataset should pass validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "customers.csv"

            df = generate_dataset(
                n=50,
                output_file=output,
            )

            self.assertEqual(validate_dataset(df), [])

    def test_missing_column(self):
        """Missing required column should be detected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "customers.csv"

            df = generate_dataset(
                n=20,
                output_file=output,
            )

            df = df.drop(columns=["purchase"])

            errors = validate_dataset(df)

            self.assertTrue(
                any("Missing columns" in error for error in errors)
            )

    def test_empty_dataset(self):
        """Empty dataset should fail validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "customers.csv"

            df = generate_dataset(
                n=20,
                output_file=output,
            )

            df = df.iloc[0:0]

            errors = validate_dataset(df)

            self.assertIn("Dataset is empty.", errors)

    def test_duplicate_customer_ids(self):
        """Duplicate customer IDs should be detected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "customers.csv"

            df = generate_dataset(
                n=20,
                output_file=output,
            )

            df.loc[1, "customer_id"] = df.loc[0, "customer_id"]

            errors = validate_dataset(df)

            self.assertIn("Duplicate customer IDs found.", errors)

    def test_invalid_purchase_value(self):
        """Purchase values other than 0 or 1 should be rejected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "customers.csv"

            df = generate_dataset(
                n=20,
                output_file=output,
            )

            df["purchase"] = df["purchase"].astype(object)
            df.loc[0, "purchase"] = 3

            errors = validate_dataset(df)

            self.assertIn(
                "Column 'purchase' must contain only 0 or 1.",
                errors,
            )

    def test_missing_values(self):
        """Missing values should be detected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "customers.csv"

            df = generate_dataset(
                n=20,
                output_file=output,
            )

            df.loc[0, "engagement"] = float("nan")

            errors = validate_dataset(df)

            self.assertIn("Dataset contains missing values.", errors)

    def test_run_analysis(self):
        """Analysis should create a dataset at the requested path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "customers.csv"

            df = run_analysis(
                n=25,
                output_file=output,
            )

            self.assertEqual(len(df), 25)
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()