import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import data_analysis


class TestDataAnalysis(unittest.TestCase):

    def setUp(self):
        self.df = pd.DataFrame({
            "customer_id": [1, 2, 3, 4, 5, 6],
            "previous_purchases": [1, 3, 5, 7, 8, 2],
            "engagement": [2, 4, 6, 8, 9, 3],
            "discount": [0, 1, 0, 1, 0, 1],
            "purchase": [0, 1, 1, 1, 1, 0],
        })

    def test_load_real_customer_data(self):
        df = data_analysis.load_customer_data()
        self.assertEqual(len(df), 1000)

    def test_validate_customer_data(self):
        self.assertTrue(data_analysis.validate_customer_data(self.df.copy()))

    def test_duplicate_customer_ids_rejected(self):
        df = self.df.copy()
        df.loc[1, "customer_id"] = df.loc[0, "customer_id"]
        with self.assertRaises(ValueError):
            data_analysis.validate_customer_data(df)

    def test_invalid_purchase_value_rejected(self):
        df = self.df.copy()
        df.loc[0, "purchase"] = 2
        with self.assertRaises(ValueError):
            data_analysis.validate_customer_data(df)

    def test_invalid_discount_value_rejected(self):
        df = self.df.copy()
        df.loc[0, "discount"] = 3
        with self.assertRaises(ValueError):
            data_analysis.validate_customer_data(df)

    def test_invalid_engagement_rejected(self):
        df = self.df.copy()
        df.loc[0, "engagement"] = 11
        with self.assertRaises(ValueError):
            data_analysis.validate_customer_data(df)

    def test_customer_segments_created(self):
        result = data_analysis.create_customer_segments(self.df)
        self.assertIn("customer_segment", result.columns)
        self.assertEqual(len(result), len(self.df))

    def test_risk_classification_created(self):
        result = data_analysis.create_risk_classification(self.df)
        self.assertIn("customer_risk", result.columns)

    def test_loyalty_classification_created(self):
        result = data_analysis.create_loyalty_classification(self.df)
        self.assertIn("loyalty_level", result.columns)

    def test_summaries_cover_all_customers(self):
        df = data_analysis.create_customer_segments(self.df)
        df = data_analysis.create_risk_classification(df)
        df = data_analysis.create_loyalty_classification(df)
        summaries = data_analysis.create_summaries(df)
        total = summaries["segment_summary"]["customer_count"].sum()
        self.assertEqual(total, len(self.df))

    def test_correlation_matrix_shape(self):
        result = data_analysis.create_correlation_matrix(self.df)
        self.assertEqual(result.shape, (4, 4))

    def test_run_analysis_creates_reports(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            results = data_analysis.run_analysis(output_dir=output_dir)

            self.assertEqual(results["total_customers"], 1000)
            self.assertEqual(results["total_purchases"], 573)
            self.assertEqual(results["total_non_purchases"], 427)

            expected_files = [
                "customer_insights.csv",
                "correlation_matrix.csv",
                "segment_summary.csv",
                "customer_segment_purchase_rate.png",
                "engagement_purchase_rate.png",
                "discount_purchase_rate.png",
            ]

            for filename in expected_files:
                self.assertTrue((output_dir / filename).exists(), filename)


if __name__ == "__main__":
    unittest.main()
