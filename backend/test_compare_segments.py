import tempfile
import unittest
from pathlib import Path

import pandas as pd

from backend.compare_segments import (
    load_segment_data,
    validate_segment_data,
    create_segment_comparison,
    save_comparison_charts,
    compare_segments,
)


class TestCompareSegments(unittest.TestCase):

    def setUp(self):
        self.df = pd.DataFrame({
            "customer_id": [1, 2, 3, 4],
            "engagement_segment": [
                "High", "High", "Low", "Low"
            ],
            "purchase_history_segment": [
                "Frequent", "Rare", "Frequent", "Rare"
            ],
            "purchase": [1, 0, 1, 0],
        })

    def test_load_segment_data(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "segments.csv"
            self.df.to_csv(file_path, index=False)

            result = load_segment_data(file_path)

            self.assertEqual(len(result), 4)

    def test_load_missing_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "missing.csv"

            with self.assertRaises(FileNotFoundError):
                load_segment_data(file_path)

    def test_validate_segment_data(self):
        self.assertTrue(validate_segment_data(self.df))

    def test_missing_required_column(self):
        df = self.df.drop(columns=["purchase"])

        with self.assertRaises(ValueError):
            validate_segment_data(df)

    def test_empty_dataset(self):
        with self.assertRaises(ValueError):
            validate_segment_data(self.df.iloc[0:0])

    def test_missing_customer_id(self):
        df = self.df.copy()
        df.loc[0, "customer_id"] = None

        with self.assertRaises(ValueError):
            validate_segment_data(df)

    def test_duplicate_customer_id(self):
        df = self.df.copy()
        df.loc[1, "customer_id"] = 1

        with self.assertRaises(ValueError):
            validate_segment_data(df)

    def test_invalid_purchase_values(self):
        df = self.df.copy()
        df["purchase"] = [1, 0, 2, 0]

        with self.assertRaises(ValueError):
            validate_segment_data(df)

    def test_non_numeric_purchase(self):
        df = self.df.copy()
        df["purchase"] = [1, 0, "invalid", 0]

        with self.assertRaises(ValueError):
            validate_segment_data(df)

    def test_segment_comparison(self):
        result = create_segment_comparison(self.df)

        self.assertEqual(len(result), 4)
        self.assertIn("customer_count", result.columns)
        self.assertIn("total_purchases", result.columns)
        self.assertIn("purchase_rate_percent", result.columns)

    def test_comparison_purchase_rates(self):
        result = create_segment_comparison(self.df)

        self.assertEqual(
            sorted(result["purchase_rate_percent"].tolist()),
            [0.0, 0.0, 100.0, 100.0],
        )

    def test_save_comparison_charts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = save_comparison_charts(
                self.df,
                output_dir=temp_dir,
            )

            self.assertEqual(len(paths), 2)

            for path in paths:
                self.assertTrue(Path(path).exists())

    def test_compare_segments_end_to_end(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)

            input_file = temp_dir / "segments.csv"
            output_file = temp_dir / "comparison.csv"
            chart_dir = temp_dir / "charts"

            self.df.to_csv(input_file, index=False)

            result = compare_segments(
                file_path=input_file,
                output_file=output_file,
                chart_dir=chart_dir,
            )

            self.assertEqual(result["customers_analyzed"], 4)
            self.assertTrue(output_file.exists())
            self.assertEqual(len(result["chart_paths"]), 2)


if __name__ == "__main__":
    unittest.main()