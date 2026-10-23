import unittest
from urllib.error import URLError
from urllib.request import urlopen
import json


BASE_URL = "http://127.0.0.1:5000"


class TestAPIResponses(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            with urlopen(f"{BASE_URL}/health", timeout=3) as response:
                if response.status != 200:
                    raise RuntimeError("Backend health check failed.")
        except (URLError, TimeoutError) as error:
            raise RuntimeError(
                "Backend is not running. Start backend/app.py first."
            ) from error

    def check_json_endpoint(self, endpoint):
        with urlopen(f"{BASE_URL}{endpoint}", timeout=5) as response:
            self.assertEqual(response.status, 200)
            content_type = response.headers.get("Content-Type", "")
            self.assertIn("application/json", content_type)

            data = json.loads(response.read().decode("utf-8"))
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

    def test_discount_analysis_endpoint(self):
        data = self.check_json_endpoint("/discount-analysis")
        self.assertTrue(data)

    def test_engagement_analysis_endpoint(self):
        data = self.check_json_endpoint("/engagement-analysis")
        self.assertTrue(data)

    def test_previous_purchases_endpoint(self):
        data = self.check_json_endpoint("/previous-purchases-analysis")
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

