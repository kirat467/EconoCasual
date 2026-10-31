import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

import purchase_correlation_analysis as analysis


class TestPurchaseCorrelationAnalysis(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.temp_path = Path(self.temp_dir.name)

        self.data_file = self.temp_path / "customers.csv"

        self.test_data = pd.DataFrame({
            "previous_purchases": [1, 2, 3, 4, 5],
            "engagement": [10, 20, 30, 40, 50],
            "discount": [5, 10, 15, 20, 25],
            "purchase": [0, 0, 1, 1, 1],
        })

        self.test_data.to_csv(self.data_file, index=False)

        self.report_dir = self.temp_path / "reports"
        self.chart_dir = self.report_dir / "charts"

        self.output_file = (
            self.report_dir / "purchase_correlation_analysis.csv"
        )
        self.chart_file = (
            self.chart_dir / "purchase_correlation_heatmap.png"
        )

        patchers = [
            patch.object(analysis, "DATA_FILE", self.data_file),
            patch.object(analysis, "REPORT_DIR", self.report_dir),
            patch.object(analysis, "CHART_DIR", self.chart_dir),
            patch.object(analysis, "OUTPUT_FILE", self.output_file),
            patch.object(analysis, "CHART_FILE", self.chart_file),
        ]

        for patcher in patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_analysis_returns_dataframe(self):
        result = analysis.analyze_purchase_correlations()
        self.assertIsInstance(result, pd.DataFrame)

    def test_result_contains_required_columns(self):
        result = analysis.analyze_purchase_correlations()

        expected = [
            "previous_purchases",
            "engagement",
            "discount",
            "purchase",
        ]

        self.assertEqual(result.columns.tolist(), expected)
        self.assertEqual(result.index.tolist(), expected)

    def test_correlation_matrix_is_square(self):
        result = analysis.analyze_purchase_correlations()

        self.assertEqual(result.shape, (4, 4))

    def test_correlation_values_are_valid(self):
        result = analysis.analyze_purchase_correlations()

        values = result.to_numpy()

        self.assertTrue(((values >= -1) & (values <= 1)).all())

    def test_diagonal_values_are_one(self):
        result = analysis.analyze_purchase_correlations()

        for column in result.columns:
            with self.subTest(column=column):
                self.assertAlmostEqual(result.loc[column, column], 1.0)

    def test_correlation_matrix_is_symmetric(self):
        result = analysis.analyze_purchase_correlations()

        pd.testing.assert_frame_equal(
            result,
            result.T,
            check_exact=False,
            atol=1e-10,
        )

    def test_result_is_not_empty(self):
        result = analysis.analyze_purchase_correlations()
        self.assertFalse(result.empty)

    def test_correlation_values_are_rounded(self):
        result = analysis.analyze_purchase_correlations()

        rounded = result.round(3)

        pd.testing.assert_frame_equal(result, rounded)

    def test_csv_report_is_created(self):
        analysis.analyze_purchase_correlations()

        self.assertTrue(self.output_file.exists())
        self.assertGreater(self.output_file.stat().st_size, 0)

    def test_saved_csv_matches_result(self):
        result = analysis.analyze_purchase_correlations()

        saved_result = pd.read_csv(self.output_file, index_col=0)

        pd.testing.assert_frame_equal(
            saved_result,
            result,
            check_dtype=False,
        )

    def test_heatmap_is_created(self):
        analysis.analyze_purchase_correlations()

        self.assertTrue(self.chart_file.exists())
        self.assertGreater(self.chart_file.stat().st_size, 0)

    def test_missing_dataset_raises_error(self):
        with patch.object(
            analysis,
            "DATA_FILE",
            self.temp_path / "missing.csv",
        ):
            with self.assertRaises(FileNotFoundError):
                analysis.analyze_purchase_correlations()

    def test_missing_columns_raise_error(self):
        invalid_data = pd.DataFrame({
            "previous_purchases": [1],
            "purchase": [1],
        })

        invalid_data.to_csv(self.data_file, index=False)

        with self.assertRaisesRegex(ValueError, "Missing required columns"):
            analysis.analyze_purchase_correlations()

    def test_empty_dataset_raises_error(self):
        empty_data = pd.DataFrame(columns=[
            "previous_purchases",
            "engagement",
            "discount",
            "purchase",
        ])

        empty_data.to_csv(self.data_file, index=False)

        with self.assertRaisesRegex(ValueError, "empty"):
            analysis.analyze_purchase_correlations()

    def test_invalid_numeric_values_raise_error(self):
        invalid_data = self.test_data.copy()
        invalid_data["engagement"] = "invalid"
        invalid_data.to_csv(self.data_file, index=False)

        with self.assertRaises(ValueError):
            analysis.analyze_purchase_correlations()

    def test_missing_numeric_values_raise_error(self):
        invalid_data = self.test_data.copy()
        invalid_data.loc[0, "discount"] = None
        invalid_data.to_csv(self.data_file, index=False)

        with self.assertRaisesRegex(ValueError, "missing values"):
            analysis.analyze_purchase_correlations()

    def test_analysis_is_repeatable(self):
        first_result = analysis.analyze_purchase_correlations()
        second_result = analysis.analyze_purchase_correlations()

        pd.testing.assert_frame_equal(first_result, second_result)


if __name__ == "__main__":
    unittest.main(verbosity=2)