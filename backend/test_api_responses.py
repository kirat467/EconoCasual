
import unittest

from app import app


class TestAPIResponses(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()

    def check_json_endpoint(self, endpoint):
        response = self.client.get(endpoint)

        self.assertEqual(
            response.status_code,
            200,
            msg=f"{endpoint} returned status {response.status_code}",
        )
        self.assertTrue(
            response.is_json,
            msg=f"{endpoint} did not return JSON",
        )

        data = response.get_json()
        self.assertIsNotNone(data)

        return data

    def test_health_endpoint(self):
        data = self.check_json_endpoint("/health")
        self.assertEqual(data["status"], "healthy")

    def test_customers_endpoint(self):
        data = self.check_json_endpoint("/customers")

        self.assertIn("total_customers", data)
        self.assertIn("columns", data)
        self.assertIn("page", data)
        self.assertIn("per_page", data)
        self.assertIn("customers", data)

        self.assertIsInstance(data["total_customers"], int)
        self.assertIsInstance(data["columns"], list)
        self.assertIsInstance(data["customers"], list)

        self.assertEqual(data["page"], 1)
        self.assertEqual(data["per_page"], 20)
        self.assertLessEqual(len(data["customers"]), 20)

        if data["customers"]:
            customer = data["customers"][0]

            for column in [
                "customer_id",
                "previous_purchases",
                "engagement",
                "discount",
                "purchase",
            ]:
                self.assertIn(column, customer)

    def test_customers_pagination(self):
        data = self.check_json_endpoint("/customers?page=2&per_page=10")

        self.assertEqual(data["page"], 2)
        self.assertEqual(data["per_page"], 10)
        self.assertLessEqual(len(data["customers"]), 10)

    def test_customers_per_page_limit(self):
        data = self.check_json_endpoint("/customers?per_page=500")

        self.assertEqual(data["per_page"], 100)
        self.assertLessEqual(len(data["customers"]), 100)

    def test_purchase_summary_endpoint(self):
        data = self.check_json_endpoint("/purchase-summary")

        expected_keys = [
            "total_customers",
            "total_purchases",
            "non_purchases",
            "purchase_rate_percent",
        ]

        for key in expected_keys:
            self.assertIn(key, data)

        self.assertIsInstance(data["total_customers"], int)
        self.assertIsInstance(data["total_purchases"], int)
        self.assertIsInstance(data["non_purchases"], int)
        self.assertIsInstance(data["purchase_rate_percent"], (int, float))

        self.assertEqual(
            data["total_customers"],
            data["total_purchases"] + data["non_purchases"],
        )

    def test_discount_analysis_endpoint(self):
        data = self.check_json_endpoint("/discount-analysis")
        self.assertIn("analysis", data)
        self.assertIsInstance(data["analysis"], dict)

    def test_engagement_analysis_endpoint(self):
        data = self.check_json_endpoint("/engagement-analysis")
        self.assertIn("analysis", data)
        self.assertIsInstance(data["analysis"], dict)

    def test_previous_purchases_endpoint(self):
        data = self.check_json_endpoint("/previous-purchases-analysis")
        self.assertIn("analysis", data)
        self.assertIsInstance(data["analysis"], dict)

    def test_validate_data_endpoint(self):
        data = self.check_json_endpoint("/validate-data")

        self.assertIn("total_rows", data)
        self.assertIn("total_columns", data)
        self.assertIn("columns", data)
        self.assertIn("missing_values_by_column", data)
        self.assertIn("has_missing_values", data)

        self.assertIsInstance(data["total_rows"], int)
        self.assertIsInstance(data["total_columns"], int)
        self.assertIsInstance(data["columns"], list)
        self.assertIsInstance(data["missing_values_by_column"], dict)
        self.assertIsInstance(data["has_missing_values"], bool)

    def test_customer_statistics_endpoint(self):
        data = self.check_json_endpoint("/customer-statistics")

        self.assertIn("total_customers", data)
        self.assertIn("columns", data)
        self.assertIn("numeric_statistics", data)

        self.assertIsInstance(data["total_customers"], int)
        self.assertIsInstance(data["columns"], list)
        self.assertIsInstance(data["numeric_statistics"], dict)


if __name__ == "__main__":
    unittest.main(verbosity=2)

