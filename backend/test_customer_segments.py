"""Tests for the customer segmentation module."""

import unittest
from pathlib import Path

import pandas as pd

from backend.customer_segments import (
    create_customer_segments,
    SEGMENTS_FILE,
    SUMMARY_FILE,
)


class TestCustomerSegments(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Generate segmentation reports once before running tests
        create_customer_segments()

    def test_detailed_report_exists(self):
        """Detailed customer segmentation report should exist."""
        self.assertTrue(SEGMENTS_FILE.exists())

    def test_summary_report_exists(self):
        """Customer segmentation summary should exist."""
        self.assertTrue(SUMMARY_FILE.exists())

    def test_detailed_report_has_1000_customers(self):
        """Detailed report should contain all 1000 customers."""
        df = pd.read_csv(SEGMENTS_FILE)
        self.assertEqual(len(df), 1000)

    def test_required_segment_columns(self):
        """Detailed report should contain both segment columns."""
        df = pd.read_csv(SEGMENTS_FILE)

        self.assertIn("engagement_segment", df.columns)
        self.assertIn("purchase_history_segment", df.columns)

    def test_all_nine_segment_combinations(self):
        """Summary should contain nine engagement-history combinations."""
        summary = pd.read_csv(SUMMARY_FILE)
        self.assertEqual(len(summary), 9)

    def test_summary_customer_count(self):
        """Segment customer counts should add up to 1000."""
        summary = pd.read_csv(SUMMARY_FILE)

        self.assertEqual(
            summary["total_customers"].sum(),
            1000,
        )

    def test_summary_purchase_count(self):
        """Segment purchase counts should add up to 586."""
        summary = pd.read_csv(SUMMARY_FILE)

        self.assertEqual(
            summary["total_purchases"].sum(),
            586,
        )

    def test_purchase_rates_are_valid(self):
        """Purchase rates should remain between 0 and 100 percent."""
        summary = pd.read_csv(SUMMARY_FILE)

        self.assertTrue(
            summary["purchase_rate_percent"].between(0, 100).all()
        )


if __name__ == "__main__":
    unittest.main()
