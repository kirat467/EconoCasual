import tempfile
import unittest
from pathlib import Path

import pandas as pd

from backend import data_analysis


class TestDataAnalysis(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.df = data_analysis.load_customer_data()

    def test_load_customer_data(self):
        self.assertEqual(len(self.df), 1000)

    def test_required_columns(self):
        required = [
            "customer_id",
            "previous_purchases",
            "engagement",
            "discount",
            "purchase",
        ]

        for column in required:
            self.assertIn(column, self.df.columns)

    def test_no_missing_values(self):
        self.assertEqual(
            int(self.df.isnull().sum().sum()),
            0,
        )

    def test_purchase_values_are_binary(self):
        self.assertTrue(self.df["purchase"].isin([0, 1]).all())

    def test_discount_values_are_binary(self):
        self.assertTrue(self.df["discount"].isin([0, 1]).all())

    def test_create_customer_segments(self):
        result = data_analysis.create_customer_segments(self.df.copy())
        self.assertEqual(len(result), 1000)

    def test_create_risk_classification(self):
        result = data_analysis.create_risk_classification(self.df.copy())
        self.assertEqual(len(result), 1000)

    def test_create_loyalty_classification(self):
        result = data_analysis.create_loyalty_classification(self.df.copy())
        self.assertEqual(len(result), 1000)

    def test_create_summaries(self):
        df = data_analysis.create_customer_segments(self.df.copy())
        df = data_analysis.create_risk_classification(df)
        df = data_analysis.create_loyalty_classification(df)

        summaries = data_analysis.create_summaries(df)

        self.assertIn("segment_summary", summaries)

    def test_correlation_matrix_shape(self):
        result = data_analysis.create_correlation_matrix(self.df)
        self.assertEqual(result.shape, (4, 4))

    def test_run_analysis_creates_reports(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            results = data_analysis.run_analysis(
                file_path=data_analysis.DATA_FILE,
                output_dir=output_dir,
            )

            self.assertEqual(results["total_customers"], 1000)
            self.assertEqual(results["total_purchases"], 586)
            self.assertEqual(results["total_non_purchases"], 414)

            expected_files = [
                "customer_insights.csv",
                "correlation_matrix.csv",
                "segment_summary.csv",
                "customer_segment_purchase_rate.png",
                "engagement_purchase_rate.png",
                "discount_purchase_rate.png",
            ]

            for filename in expected_files:
                self.assertTrue(
                    (output_dir / filename).exists(),
                    filename,
                )


if __name__ == "__main__":
    unittest.main()
