import unittest
from app import app


class TestEconoCasualAPI(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_home(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["project"], "EconoCasual")

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "healthy")

    def test_customers(self):
        response = self.client.get("/customers")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(data["total_customers"], 1000)
        self.assertLessEqual(len(data["customers"]), 20)
        self.assertIn("customer_id", data["columns"])
        self.assertIn("purchase", data["columns"])

        for customer in data["customers"]:
            self.assertIn("customer_id", customer)
            self.assertIn("purchase", customer)

    def test_customers_response_is_json(self):
        response = self.client.get("/customers")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)

    def test_customer_values_are_integers(self):
        response = self.client.get("/customers")
        data = response.get_json()
        customer = data["customers"][0]

        for column in [
            "customer_id",
            "previous_purchases",
            "engagement",
            "discount",
            "purchase"
        ]:
            self.assertIsInstance(customer[column], int)

    def test_customers_custom_limit(self):
        response = self.client.get("/customers?limit=10")

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(data["limit"], 10)
        self.assertEqual(data["returned_customers"], 10)
        self.assertEqual(len(data["customers"]), 10)

    def test_customers_offset(self):
        response = self.client.get("/customers?limit=10&offset=20")

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(data["limit"], 10)
        self.assertEqual(data["offset"], 20)
        self.assertEqual(data["returned_customers"], 10)

    def test_customers_invalid_limit(self):
        response = self.client.get("/customers?limit=abc")

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_customers_limit_out_of_range(self):
        response = self.client.get("/customers?limit=101")

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_customers_negative_offset(self):
        response = self.client.get("/customers?offset=-1")

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_customers_invalid_offset(self):
        response = self.client.get("/customers?offset=abc")

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_customers_zero_limit(self):
        response = self.client.get("/customers?limit=0")

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_customers_offset_beyond_dataset(self):
        response = self.client.get("/customers?limit=10&offset=2000")

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(data["returned_customers"], 0)
        self.assertEqual(data["customers"], [])

    def test_purchase_summary(self):
        response = self.client.get("/purchase-summary")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(data["total_customers"], 1000)
        self.assertEqual(data["total_purchases"], 573)
        self.assertEqual(data["non_purchases"], 427)
        self.assertEqual(data["purchase_rate_percent"], 57.3)

    def test_purchase_summary_response_structure(self):
        response = self.client.get("/purchase-summary")
        data = response.get_json()

        self.assertIn("total_customers", data)
        self.assertIn("total_purchases", data)
        self.assertIn("non_purchases", data)
        self.assertIn("purchase_rate_percent", data)

    def test_purchase_summary_values_are_numeric(self):
        response = self.client.get("/purchase-summary")
        data = response.get_json()

        self.assertIsInstance(data["total_customers"], int)
        self.assertIsInstance(data["total_purchases"], int)
        self.assertIsInstance(data["non_purchases"], int)
        self.assertIsInstance(data["purchase_rate_percent"], (int, float))

    def test_purchase_summary_returns_json(self):
        response = self.client.get("/purchase-summary")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)

    def test_purchase_rate_is_valid(self):
        response = self.client.get("/purchase-summary")
        data = response.get_json()

        self.assertGreaterEqual(data["purchase_rate_percent"], 0)
        self.assertLessEqual(data["purchase_rate_percent"], 100)

    def test_invalid_url(self):
        response = self.client.get("/invalid-url")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main(verbosity=2)