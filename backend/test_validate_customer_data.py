import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from backend import validate_customer_data as validation


class TestValidateCustomerData(unittest.TestCase):

    def setUp(self):
        # Required columns ke according valid sample dataset banao.
        self.valid_data = {}

        for column in validation.REQUIRED_COLUMNS:

            if column == "purchase":
                self.valid_data[column] = [1, 0]

            elif column == "discount":
                self.valid_data[column] = [0, 1]

            elif column == "engagement":
                self.valid_data[column] = [5, 8]

            elif column == "previous_purchases":
                self.valid_data[column] = [2, 4]

            elif "id" in column.lower():
                self.valid_data[column] = [1, 2]

            else:
                self.valid_data[column] = [1, 2]

        self.df = pd.DataFrame(self.valid_data)

    def test_valid_customer_data(self):
        # Valid dataset successfully validate hona chahiye.
        result = validation.validate_customer_data(self.df.copy())

        self.assertTrue(result["is_valid"])
        self.assertEqual(result["total_rows"], 2)
        self.assertEqual(result["errors"], [])

    def test_missing_required_column(self):
        # Required column missing hone par validation fail honi chahiye.
        column = validation.REQUIRED_COLUMNS[0]

        df = self.df.drop(columns=[column])

        result = validation.validate_customer_data(df)

        self.assertFalse(result["is_valid"])
        self.assertEqual(
            result["errors"][0]["type"],
            "missing_columns"
        )

        self.assertIn(
            column,
            result["errors"][0]["columns"]
        )

    def test_multiple_missing_columns(self):
        # Multiple missing columns detect hone chahiye.
        columns = validation.REQUIRED_COLUMNS[:2]

        df = self.df.drop(columns=columns)

        result = validation.validate_customer_data(df)

        self.assertFalse(result["is_valid"])
        self.assertEqual(
            result["errors"][0]["type"],
            "missing_columns"
        )

        for column in columns:
            self.assertIn(
                column,
                result["errors"][0]["columns"]
            )

    def test_missing_values(self):
        # Dataset mein missing values detect honi chahiye.
        column = next(
            col for col in validation.REQUIRED_COLUMNS
            if col != "purchase"
        )

        df = self.df.copy()
        df.loc[0, column] = None

        result = validation.validate_customer_data(df)

        self.assertFalse(result["is_valid"])

        error_types = [
            error["type"]
            for error in result["errors"]
        ]

        self.assertIn("missing_values", error_types)

    def test_non_numeric_values(self):
        # Numeric column mein invalid text detect hona chahiye.
        column = next(
            col for col in validation.NUMERIC_COLUMNS
            if col != "purchase"
        )

        df = self.df.copy()

        df[column] = df[column].astype(object)
        df.loc[0, column] = "invalid"

        result = validation.validate_customer_data(df)

        self.assertFalse(result["is_valid"])

        matching_errors = [
            error for error in result["errors"]
            if error["type"] == "non_numeric_values"
        ]

        self.assertTrue(matching_errors)

        self.assertEqual(
            matching_errors[0]["column"],
            column
        )

        self.assertEqual(
            matching_errors[0]["count"],
            1
        )

    def test_non_finite_values(self):
        # Infinity jaisi non-finite numeric value detect honi chahiye.
        column = next(
            col for col in validation.NUMERIC_COLUMNS
            if col != "purchase"
        )

        df = self.df.copy()

        # Integer column ko float mein convert karo.
        df[column] = df[column].astype(float)

        # Float column mein infinity assign karo.
        df.loc[0, column] = float("inf")

        result = validation.validate_customer_data(df)

        self.assertFalse(result["is_valid"])

        error_types = [
            error["type"]
            for error in result["errors"]
        ]

        self.assertIn("non_finite_values", error_types)

    def test_invalid_purchase_values(self):
        # Purchase column mein sirf 0 aur 1 valid hain.
        df = self.df.copy()

        df.loc[0, "purchase"] = 2

        result = validation.validate_customer_data(df)

        self.assertFalse(result["is_valid"])

        matching_errors = [
            error for error in result["errors"]
            if error["type"] == "invalid_purchase_values"
        ]

        self.assertTrue(matching_errors)

        self.assertEqual(
            matching_errors[0]["count"],
            1
        )

    def test_invalid_purchase_text(self):
        # Purchase column mein invalid text detect hona chahiye.
        df = self.df.copy()

        df["purchase"] = df["purchase"].astype(object)
        df.loc[0, "purchase"] = "unknown"

        result = validation.validate_customer_data(df)

        self.assertFalse(result["is_valid"])

        error_types = [
            error["type"]
            for error in result["errors"]
        ]

        self.assertIn(
            "invalid_purchase_values",
            error_types
        )

    def test_validate_dataset_file_success(self):
        # Temporary CSV file se dataset load hona chahiye.
        with tempfile.TemporaryDirectory() as temp_dir:

            file_path = Path(temp_dir) / "customers.csv"

            self.df.to_csv(file_path, index=False)

            with patch.object(
                validation,
                "DATA_FILE",
                file_path
            ):
                result = validation.validate_dataset_file()

        self.assertTrue(result["is_valid"])
        self.assertEqual(result["total_rows"], 2)

    def test_validate_dataset_file_missing(self):
        # Missing dataset file par FileNotFoundError aana chahiye.
        missing_path = Path("missing_customer_dataset.csv")

        with patch.object(
            validation,
            "DATA_FILE",
            missing_path
        ):
            with self.assertRaises(FileNotFoundError):
                validation.validate_dataset_file()


if __name__ == "__main__":
    unittest.main()