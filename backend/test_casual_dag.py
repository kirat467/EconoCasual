"""Tests for the causal DAG and adjusted-effect analysis."""

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from backend.causal_dag import (
    load_customer_data,
    calculate_naive_difference,
    identify_causal_effect,
    calculate_adjusted_effect,
)


def create_test_data():
    """Create deterministic sample data with variation in all variables."""
    rows = []

    for i in range(100):
        previous_purchases = (i * 3) % 6
        engagement = ((i * 7) % 100) / 100
        discount = (i // 2) % 2

        purchase = int(
            ((i * 13) % 17 < 9)
            or (engagement > 0.7 and previous_purchases >= 2)
        )

        rows.append({
            "previous_purchases": previous_purchases,
            "engagement": engagement,
            "discount": discount,
            "purchase": purchase,
        })

    return pd.DataFrame(rows)


class TestCausalDag(unittest.TestCase):

    def setUp(self):
        self.df = create_test_data()

    def test_load_customer_data(self):
        """Actual customer dataset should load successfully."""
        df = load_customer_data()

        self.assertEqual(len(df), 1000)
        self.assertTrue({
            "previous_purchases",
            "engagement",
            "discount",
            "purchase",
        }.issubset(df.columns))

    def test_load_data_with_missing_columns(self):
        """Loading should reject a CSV with missing required columns."""
        invalid_df = self.df.drop(columns=["discount"])

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "invalid.csv"
            invalid_df.to_csv(file_path, index=False)

            with self.assertRaises(ValueError):
                load_customer_data(file_path)

    def test_load_data_with_missing_values(self):
        """Loading should reject missing values."""
        invalid_df = self.df.copy()
        invalid_df.loc[0, "engagement"] = np.nan

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "missing.csv"
            invalid_df.to_csv(file_path, index=False)

            with self.assertRaises(ValueError):
                load_customer_data(file_path)

    def test_load_data_with_invalid_binary_values(self):
        """Discount and purchase should contain only 0 and 1."""
        invalid_df = self.df.copy()
        invalid_df.loc[0, "discount"] = 2

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "invalid_binary.csv"
            invalid_df.to_csv(file_path, index=False)

            with self.assertRaises(ValueError):
                load_customer_data(file_path)

    def test_naive_difference(self):
        """Naive difference should equal the difference between group means."""
        result = calculate_naive_difference(self.df)

        discounted_mean = self.df.loc[
            self.df["discount"] == 1, "purchase"
        ].mean()

        non_discounted_mean = self.df.loc[
            self.df["discount"] == 0, "purchase"
        ].mean()

        self.assertAlmostEqual(
            result,
            discounted_mean - non_discounted_mean,
        )

    def test_naive_difference_without_discount_group(self):
        """Naive difference should reject data with only one discount group."""
        invalid_df = self.df.copy()
        invalid_df["discount"] = 1

        with self.assertRaises(ValueError):
            calculate_naive_difference(invalid_df)

    def test_identify_causal_effect(self):
        """DoWhy should identify a causal estimand."""
        model, estimand = identify_causal_effect(self.df)

        self.assertIsNotNone(model)
        self.assertIsNotNone(estimand)

    def test_calculate_adjusted_effect(self):
        """Adjusted effect should be a finite number."""
        effect, regression = calculate_adjusted_effect(self.df)

        self.assertTrue(np.isfinite(effect))
        self.assertIsNotNone(regression)
        self.assertIn("discount", regression.params.index)


if __name__ == "__main__":
    unittest.main()