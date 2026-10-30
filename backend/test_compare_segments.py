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
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)

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

        self.input_file = self.output_dir / "customers.csv"
        self.df.to_csv(self.input_file, index=False)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_segment_data(self):
        result = load_segment_data(self.input_file)
        self.assertEqual(len(result), 4)

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            load_segment_data(self.output_dir / "missing.csv")

    def test_valid_segment_data(self):
        self.assertTrue(validate_segment_data(self.df))

    def test_missing_column(self):
        df = self.df.drop(columns=["purchase"])
        with self.assertRaises(ValueError):
            validate_segment_data(df)

    def test_empty_dataset(self):
        df = self.df.iloc[0:0]
        with self.assertRaises(ValueError):
            validate_segment_data(df)

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

    def test_invalid_purchase_value(self):
        df = self.df.copy()
        df["purchase"] = [1, 0, 2, 0]
        with self.assertRaises(ValueError):
            validate_segment_data(df)

    def test_comparison_results(self):
        result = create_segment_comparison(self.df)

        self.assertEqual(len(result), 4)
        self.assertIn("customer_count", result.columns)
        self.assertIn("total_purchases", result.columns)
        self.assertIn("purchase_rate_percent", result.columns)

    def test_chart_generation(self):
        paths = save_comparison_charts(
            self.df,
            self.output_dir / "charts"
        )

        self.assertEqual(len(paths), 2)

        for path in paths:
            self.assertTrue(path.exists())

    def test_complete_comparison(self):
        output_file = self.output_dir / "comparison.csv"
        chart_dir = self.output_dir / "charts"

        result = compare_segments(
            file_path=self.input_file,
            output_file=output_file,
            chart_dir=chart_dir,
        )

        self.assertEqual(result["customers_analyzed"], 4)
        self.assertTrue(output_file.exists())
        self.assertEqual(len(result["chart_paths"]), 2)


if __name__ == "__main__":
    unittest.main()