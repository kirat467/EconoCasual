import tempfile
import unittest
from pathlib import Path

import pandas as pd

from backend.visualize_segments import (
    load_segment_data,
    validate_segment_data,
    create_visualizations,
)


class TestVisualizeSegments(unittest.TestCase):

    def setUp(self):
        self.df = pd.DataFrame({
            "engagement_segment": [
                "Low", "Medium", "High", "High"
            ],
            "purchase_history_segment": [
                "New", "Regular", "Regular", "Frequent"
            ],
            "purchase": [0, 1, 1, 0],
        })

        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        self.csv_path = self.temp_path / "customer_segments.csv"
        self.df.to_csv(self.csv_path, index=False)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_segment_data(self):
        df = load_segment_data(self.csv_path)

        self.assertEqual(len(df), 4)
        self.assertIn("purchase", df.columns)

    def test_missing_file(self):
        missing_path = self.temp_path / "missing.csv"

        with self.assertRaises(FileNotFoundError):
            load_segment_data(missing_path)

    def test_valid_segment_data(self):
        self.assertTrue(validate_segment_data(self.df))

    def test_missing_required_column(self):
        df = self.df.drop(columns=["engagement_segment"])

        with self.assertRaises(ValueError):
            validate_segment_data(df)

    def test_multiple_missing_columns(self):
        df = self.df[["purchase"]]

        with self.assertRaises(ValueError):
            validate_segment_data(df)

    def test_empty_dataset(self):
        df = self.df.iloc[0:0]

        with self.assertRaises(ValueError):
            validate_segment_data(df)

    def test_missing_values(self):
        df = self.df.copy()
        df.loc[0, "purchase"] = float("nan")

        with self.assertRaises(ValueError):
            validate_segment_data(df)

    def test_non_numeric_purchase(self):
        df = self.df.copy()
        df["purchase"] = df["purchase"].astype(object)
        df.loc[0, "purchase"] = "invalid"

        with self.assertRaises(ValueError):
            validate_segment_data(df)

    def test_invalid_purchase_value(self):
        df = self.df.copy()
        df.loc[0, "purchase"] = 2

        with self.assertRaises(ValueError):
            validate_segment_data(df)

    def test_create_visualizations(self):
        output_dir = self.temp_path / "charts"

        chart_paths = create_visualizations(
            file_path=self.csv_path,
            output_dir=output_dir,
        )

        self.assertEqual(len(chart_paths), 3)

        for chart_path in chart_paths:
            self.assertTrue(chart_path.exists())
            self.assertGreater(chart_path.stat().st_size, 0)

    def test_visualization_output_filenames(self):
        output_dir = self.temp_path / "charts"

        chart_paths = create_visualizations(
            file_path=self.csv_path,
            output_dir=output_dir,
        )

        filenames = {path.name for path in chart_paths}

        expected = {
            "engagement_segments.png",
            "purchase_rate_by_engagement.png",
            "purchase_rate_by_history.png",
        }

        self.assertEqual(filenames, expected)


if __name__ == "__main__":
    unittest.main()