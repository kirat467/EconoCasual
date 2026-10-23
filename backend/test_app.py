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

    def test_customers(self):
        response = self.client.get("/customers")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["total_customers"], 1000)

    def test_customer_pagination(self):
        response = self.client.get("/customers?limit=10&offset=20")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["returned_customers"], 10)

    def test_invalid_limit(self):
        response = self.client.get("/customers?limit=abc")
        self.assertEqual(response.status_code, 400)

    def test_limit_above_maximum(self):
        response = self.client.get("/customers?limit=101")
        self.assertEqual(response.status_code, 400)

    def test_negative_offset(self):
        response = self.client.get("/customers?offset=-1")
        self.assertEqual(response.status_code, 400)

    def test_filter_purchases(self):
        response = self.client.get("/customers?purchase=1")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertGreater(data["total_customers"], 0)

        for customer in data["customers"]:
            self.assertEqual(customer["purchase"], 1)

    def test_filter_non_purchases(self):
        response = self.client.get("/customers?purchase=0")
        self.assertEqual(response.status_code, 200)

        for customer in response.get_json()["customers"]:
            self.assertEqual(customer["purchase"], 0)

    def test_filter_discount(self):
        response = self.client.get("/customers?discount=1")
        self.assertEqual(response.status_code, 200)

        for customer in response.get_json()["customers"]:
            self.assertEqual(customer["discount"], 1)

    def test_combined_filters(self):
        response = self.client.get("/customers?purchase=1&discount=1")
        self.assertEqual(response.status_code, 200)

        for customer in response.get_json()["customers"]:
            self.assertEqual(customer["purchase"], 1)
            self.assertEqual(customer["discount"], 1)

    def test_invalid_purchase_filter(self):
        response = self.client.get("/customers?purchase=2")
        self.assertEqual(response.status_code, 400)

    def test_invalid_discount_filter(self):
        response = self.client.get("/customers?discount=abc")
        self.assertEqual(response.status_code, 400)

    def test_purchase_summary(self):
        response = self.client.get("/purchase-summary")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(data["total_customers"], 1000)
        self.assertEqual(data["total_purchases"], 573)
        self.assertEqual(data["non_purchases"], 427)
        self.assertEqual(data["purchase_rate_percent"], 57.3)

    def test_discount_analysis(self):
        response = self.client.get("/discount-analysis")
        self.assertEqual(response.status_code, 200)
        self.assertIn("discount_groups", response.get_json())

    def test_previous_purchases_analysis(self):
        response = self.client.get("/previous-purchases-analysis")
        self.assertEqual(response.status_code, 200)
        self.assertIn("previous_purchase_groups", response.get_json())

    def test_engagement_analysis(self):
        response = self.client.get("/engagement-analysis")
        self.assertEqual(response.status_code, 200)
        self.assertIn("engagement_groups", response.get_json())

    def test_validate_data(self):
        response = self.client.get("/validate-data")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(data["total_rows"], 1000)
        self.assertIn("is_valid", data)

    def test_customer_statistics(self):
        response = self.client.get("/customer-statistics")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(data["total_customers"], 1000)

        for column in [
            "previous_purchases",
            "engagement",
            "discount"
        ]:
            self.assertIn(column, data["statistics"])
            self.assertIn("average", data["statistics"][column])
            self.assertIn("minimum", data["statistics"][column])
            self.assertIn("maximum", data["statistics"][column])

    def test_invalid_url(self):
        response = self.client.get("/invalid-url")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main(verbosity=2)