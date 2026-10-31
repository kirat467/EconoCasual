"""Tests for the customer segment comparison report."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from backend import compare_segments_report as report_module


class TestCompareSegmentsReport(unittest.TestCase):

    def setUp(self):
        """Create isolated temporary input and output files."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.temp_path = Path(self.temp_dir.name)

        self.input_file = self.temp_path / "segment_comparison.csv"
        self.output_file = (
            self.temp_path / "segment_comparison_report.md"
        )

        self.valid_data = pd.DataFrame({
            "engagement_segment": ["High", "Low"],
            "purchase_history_segment": ["Frequent", "Rare"],
            "customer_count": [100, 50],
            "total_purchases": [80, 10],
            "purchase_rate_percent": [80.0, 20.0],
        })

        self.valid_data.to_csv(self.input_file, index=False)

        self.input_patch = patch.object(
            report_module,
            "INPUT_FILE",
            self.input_file,
        )
        self.output_patch = patch.object(
            report_module,
            "OUTPUT_FILE",
            self.output_file,
        )

        self.input_patch.start()
        self.output_patch.start()

        self.addCleanup(self.input_patch.stop)
        self.addCleanup(self.output_patch.stop)

    def test_valid_report_is_generated(self):
        """A valid dataset should generate a Markdown report."""
        report_module.generate_comparison_report()

        self.assertTrue(self.output_file.exists())

        content = self.output_file.read_text(encoding="utf-8")

        self.assertIn("# Customer Segment Comparison Report", content)
        self.assertIn("## 1. Overview", content)
        self.assertIn("## 2. Segment Comparison", content)
        self.assertIn("## 3. Key Findings", content)
        self.assertIn("## 4. Interpretation", content)
        self.assertIn("## 5. Limitations", content)
        self.assertIn("## 6. Recommended Next Steps", content)

    def test_report_contains_segment_names(self):
        """The report should include actual segment names."""
        report_module.generate_comparison_report()

        content = self.output_file.read_text(encoding="utf-8")

        self.assertIn("High", content)
        self.assertIn("Low", content)
        self.assertIn("Frequent", content)
        self.assertIn("Rare", content)

    def test_missing_input_file_is_rejected(self):
        """A missing input CSV should raise FileNotFoundError."""
        self.input_file.unlink()

        with self.assertRaises(FileNotFoundError):
            report_module.generate_comparison_report()

    def test_missing_required_column_is_rejected(self):
        """A dataset missing a required column should raise ValueError."""
        invalid_data = self.valid_data.drop(
            columns=["engagement_segment"]
        )
        invalid_data.to_csv(self.input_file, index=False)

        with self.assertRaises(ValueError):
            report_module.generate_comparison_report()

    def test_empty_dataset_is_rejected(self):
        """An empty dataset should raise ValueError."""
        empty_data = self.valid_data.iloc[0:0]
        empty_data.to_csv(self.input_file, index=False)

        with self.assertRaises(ValueError):
            report_module.generate_comparison_report()

    def test_invalid_numeric_values_are_rejected(self):
        """Non-numeric values should raise ValueError."""
        numeric_columns = [
            "customer_count",
            "total_purchases",
            "purchase_rate_percent",
        ]

        for column in numeric_columns:
            with self.subTest(column=column):
                invalid_data = self.valid_data.copy()
                invalid_data[column] = invalid_data[column].astype(object)
                invalid_data.loc[0, column] = "invalid"
                invalid_data.to_csv(self.input_file, index=False)

                with self.assertRaises(ValueError):
                    report_module.generate_comparison_report()

    def test_negative_customer_count_is_rejected(self):
        """Customer counts cannot be negative."""
        invalid_data = self.valid_data.copy()
        invalid_data.loc[0, "customer_count"] = -10
        invalid_data.to_csv(self.input_file, index=False)

        with self.assertRaises(ValueError):
            report_module.generate_comparison_report()

    def test_negative_purchase_count_is_rejected(self):
        """Purchase counts cannot be negative."""
        invalid_data = self.valid_data.copy()
        invalid_data.loc[0, "total_purchases"] = -5
        invalid_data.to_csv(self.input_file, index=False)

        with self.assertRaises(ValueError):
            report_module.generate_comparison_report()

    def test_purchases_cannot_exceed_customers(self):
        """Purchases cannot exceed the customer count."""
        invalid_data = self.valid_data.copy()
        invalid_data.loc[0, "total_purchases"] = 120
        invalid_data.to_csv(self.input_file, index=False)

        with self.assertRaises(ValueError):
            report_module.generate_comparison_report()

    def test_purchase_rate_below_zero_is_rejected(self):
        """Purchase rates cannot be below zero."""
        invalid_data = self.valid_data.copy()
        invalid_data.loc[0, "purchase_rate_percent"] = -1
        invalid_data.to_csv(self.input_file, index=False)

        with self.assertRaises(ValueError):
            report_module.generate_comparison_report()

    def test_purchase_rate_above_100_is_rejected(self):
        """Purchase rates cannot exceed 100 percent."""
        invalid_data = self.valid_data.copy()
        invalid_data.loc[0, "purchase_rate_percent"] = 101
        invalid_data.to_csv(self.input_file, index=False)

        with self.assertRaises(ValueError):
            report_module.generate_comparison_report()


if __name__ == "__main__":
    unittest.main()