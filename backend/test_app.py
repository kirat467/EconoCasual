

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from app import app


class TestEconoCasualAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()

    def test_home(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_home_returns_json(self):
        response = self.client.get("/")
        self.assertTrue(response.is_json)

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)

    def test_health_status(self):
        response = self.client.get("/health")
        self.assertEqual(response.get_json()["status"], "healthy")

    def test_customers(self):
        response = self.client.get("/customers")
        self.assertEqual(response.status_code, 200)

    def test_customers_returns_json(self):
        response = self.client.get("/customers")
        self.assertTrue(response.is_json)

    def test_customers_pagination(self):
        response = self.client.get("/customers?page=1&per_page=5")
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(response.get_json()["customers"]), 5)

    def test_customers_invalid_page(self):
        response = self.client.get("/customers?page=invalid")
        self.assertEqual(response.status_code, 200)

    def test_customers_zero_page(self):
        response = self.client.get("/customers?page=0")
        self.assertEqual(response.status_code, 200)

    def test_customers_negative_page(self):
        response = self.client.get("/customers?page=-1")
        self.assertEqual(response.status_code, 200)

    def test_customers_large_page(self):
        response = self.client.get("/customers?page=999999")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["customers"], [])

    def test_customers_filter_by_discount(self):
        response = self.client.get("/customers?discount=1")
        self.assertEqual(response.status_code, 200)
        for customer in response.get_json()["customers"]:
            self.assertEqual(float(customer["discount"]), 1.0)

    def test_customers_filter_by_engagement(self):
        response = self.client.get("/customers?engagement=1")
        self.assertEqual(response.status_code, 200)
        for customer in response.get_json()["customers"]:
            self.assertEqual(float(customer["engagement"]), 1.0)

    def test_customers_filter_by_purchase(self):
        response = self.client.get("/customers?purchase=1")
        self.assertEqual(response.status_code, 200)
        for customer in response.get_json()["customers"]:
            self.assertEqual(float(customer["purchase"]), 1.0)

    def test_customers_invalid_discount_filter(self):
        response = self.client.get("/customers?discount=invalid")
        self.assertEqual(response.status_code, 400)

    def test_customers_invalid_engagement_filter(self):
        response = self.client.get("/customers?engagement=invalid")
        self.assertEqual(response.status_code, 400)

    def test_customers_invalid_purchase_filter(self):
        response = self.client.get("/customers?purchase=invalid")
        self.assertEqual(response.status_code, 400)

    def test_customers_nan_discount_filter(self):
        response = self.client.get("/customers?discount=NaN")
        self.assertEqual(response.status_code, 400)

    def test_customers_nan_engagement_filter(self):
        response = self.client.get("/customers?engagement=NaN")
        self.assertEqual(response.status_code, 400)

    def test_customers_nan_purchase_filter(self):
        response = self.client.get("/customers?purchase=NaN")
        self.assertEqual(response.status_code, 400)

    def test_customers_infinite_discount_filter(self):
        response = self.client.get("/customers?discount=inf")
        self.assertEqual(response.status_code, 400)

    def test_customers_negative_infinite_engagement_filter(self):
        response = self.client.get("/customers?engagement=-inf")
        self.assertEqual(response.status_code, 400)

    def test_customers_infinite_purchase_filter(self):
        response = self.client.get("/customers?purchase=inf")
        self.assertEqual(response.status_code, 400)

    def test_purchase_summary(self):
        response = self.client.get("/purchase-summary")
        self.assertEqual(response.status_code, 200)

    def test_purchase_summary_fields(self):
        response = self.client.get("/purchase-summary")
        data = response.get_json()
        self.assertIn("total_customers", data)
        self.assertIn("total_purchases", data)
        self.assertIn("non_purchases", data)
        self.assertIn("purchase_rate_percent", data)

    def test_discount_analysis(self):
        response = self.client.get("/discount-analysis")
        self.assertEqual(response.status_code, 200)

    def test_engagement_analysis(self):
        response = self.client.get("/engagement-analysis")
        self.assertEqual(response.status_code, 200)

    def test_previous_purchases_analysis(self):
        response = self.client.get("/previous-purchases-analysis")
        self.assertEqual(response.status_code, 200)

    def test_validate_data(self):
        response = self.client.get("/validate-data")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("total_rows", data)
        self.assertIn("missing_values_by_column", data)

    def test_customer_statistics(self):
        response = self.client.get("/customer-statistics")
        self.assertEqual(response.status_code, 200)

    def test_unknown_endpoint(self):
        response = self.client.get("/invalid-url")
        self.assertEqual(response.status_code, 404)

    def test_unknown_endpoint_returns_json(self):
        response = self.client.get("/invalid-url")
        self.assertTrue(response.is_json)

    def test_customers_missing_dataset(self):
        with patch("app.DATA_FILE", Path("missing_customers_test.csv")):
            response = self.client.get("/customers")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.get_json()["error"],
            "Customer dataset not found"
        )

    def test_purchase_summary_missing_dataset(self):
        with patch("app.DATA_FILE", Path("missing_customers_test.csv")):
            response = self.client.get("/purchase-summary")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.get_json()["error"],
            "Unable to generate purchase summary"
        )

    def test_validate_data_missing_dataset(self):
        with patch("app.DATA_FILE", Path("missing_customers_test.csv")):
            response = self.client.get("/validate-data")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.get_json()["error"],
            "Customer dataset not found"
        )

    def test_customers_dataset_missing_required_column(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "customers.csv"
            pd.DataFrame({
                "customer_id": [1],
                "purchase": [1],
            }).to_csv(file_path, index=False)

            with patch("app.DATA_FILE", file_path):
                response = self.client.get("/customers")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.get_json()["error"],
            "Invalid customer dataset"
        )

    def test_customers_malformed_csv(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "customers.csv"
            file_path.write_text(
                'customer_id,previous_purchases\n1,"unfinished',
                encoding="utf-8"
            )

            with patch("app.DATA_FILE", file_path):
                response = self.client.get("/customers")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.get_json()["error"],
            "Invalid customer dataset"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

