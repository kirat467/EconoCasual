import tempfile
import unittest
from pathlib import Path

import pandas as pd

from backend.validate_correlation import (
    load_correlation_matrix,
    validate_correlation_matrix,
    run_validation,
)


class TestCorrelationValidation(unittest.TestCase):

    def setUp(self):
        # Create a valid sample correlation matrix.
        self.valid_matrix = pd.DataFrame(
            [
                [1.0, 0.5, -0.2],
                [0.5, 1.0, 0.3],
                [-0.2, 0.3, 1.0],
            ],
            index=["A", "B", "C"],
            columns=["A", "B", "C"],
        )

    def test_valid_matrix(self):
        result = validate_correlation_matrix(self.valid_matrix)

        self.assertTrue(result["is_valid"])
        self.assertEqual(result["rows"], 3)
        self.assertEqual(result["columns"], 3)
        self.assertEqual(result["errors"], [])

    def test_empty_matrix(self):
        df = pd.DataFrame()

        result = validate_correlation_matrix(df)

        self.assertFalse(result["is_valid"])
        self.assertIn(
            "empty_matrix",
            [error["type"] for error in result["errors"]]
        )

    def test_matrix_not_square(self):
        df = pd.DataFrame(
            [[1.0, 0.5]],
            columns=["A", "B"]
        )

        result = validate_correlation_matrix(df)

        self.assertFalse(result["is_valid"])
        self.assertIn(
            "matrix_not_square",
            [error["type"] for error in result["errors"]]
        )

    def test_mismatched_labels(self):
        df = self.valid_matrix.copy()
        df.columns = ["X", "Y", "Z"]

        result = validate_correlation_matrix(df)

        self.assertIn(
            "row_column_labels_mismatch",
            [error["type"] for error in result["errors"]]
        )

    def test_missing_values(self):
        df = self.valid_matrix.copy()
        df.iloc[0, 1] = float("nan")

        result = validate_correlation_matrix(df)

        self.assertFalse(result["is_valid"])
        self.assertIn(
            "missing_or_non_numeric_values",
            [error["type"] for error in result["errors"]]
        )

    def test_non_numeric_values(self):
        # Convert column to object dtype before inserting text.
        df = self.valid_matrix.copy()
        df["B"] = df["B"].astype(object)
        df.iloc[0, 1] = "invalid"

        result = validate_correlation_matrix(df)

        self.assertFalse(result["is_valid"])
        self.assertIn(
            "missing_or_non_numeric_values",
            [error["type"] for error in result["errors"]]
        )

    def test_values_out_of_range(self):
        df = self.valid_matrix.copy()
        df.iloc[0, 1] = 1.5

        result = validate_correlation_matrix(df)

        self.assertIn(
            "values_out_of_range",
            [error["type"] for error in result["errors"]]
        )

    def test_matrix_not_symmetric(self):
        df = self.valid_matrix.copy()
        df.iloc[0, 1] = 0.8

        result = validate_correlation_matrix(df)

        self.assertIn(
            "matrix_not_symmetric",
            [error["type"] for error in result["errors"]]
        )

    def test_invalid_diagonal(self):
        df = self.valid_matrix.copy()
        df.iloc[0, 0] = 0.5

        result = validate_correlation_matrix(df)

        self.assertIn(
            "invalid_diagonal_values",
            [error["type"] for error in result["errors"]]
        )

    def test_load_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            load_correlation_matrix("missing_correlation.csv")

    def test_load_correlation_matrix(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "correlation.csv"

            self.valid_matrix.to_csv(file_path)

            result = load_correlation_matrix(file_path)

            self.assertEqual(result.shape, (3, 3))

    def test_run_validation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "correlation.csv"

            self.valid_matrix.to_csv(file_path)

            result = run_validation(file_path)

            self.assertTrue(result["is_valid"])


if __name__ == "__main__":
    unittest.main()
