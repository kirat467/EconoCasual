
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
        self.assertTrue(data)

    def test_customers_endpoint(self):
        data = self.check_json_endpoint("/customers")
        self.assertTrue(data)

    def test_purchase_summary_endpoint(self):
        data = self.check_json_endpoint("/purchase-summary")

        self.assertIn("total_customers", data)
        self.assertIn("total_purchases", data)
        self.assertIn("non_purchases", data)
        self.assertIn("purchase_rate_percent", data)

    def test_discount_analysis_endpoint(self):
        data = self.check_json_endpoint("/discount-analysis")
        self.assertTrue(data)

    def test_engagement_analysis_endpoint(self):
        data = self.check_json_endpoint("/engagement-analysis")
        self.assertTrue(data)

    def test_previous_purchases_endpoint(self):
        data = self.check_json_endpoint(
            "/previous-purchases-analysis"
        )
        self.assertTrue(data)

    def test_validate_data_endpoint(self):
        data = self.check_json_endpoint("/validate-data")

        self.assertIn("total_rows", data)
        self.assertIn("missing_values_by_column", data)

    def test_customer_statistics_endpoint(self):
        data = self.check_json_endpoint("/customer-statistics")
        self.assertTrue(data)


if __name__ == "__main__":
    unittest.main(verbosity=2)

