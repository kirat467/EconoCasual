import unittest
from app import app


class TestEconoCasualAPI(unittest.TestCase):

    def test_invalid_api_route(self):
        

     def test_invalid_api_route(self):
        response = self.client.get("/invalid-route")
        self.assertEqual(response.status_code, 404)

    def test_invalid_method(self):
        response = self.client.post("/health")
        self.assertEqual(response.status_code, 405)


    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_home(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.get_json()["project"],
            "EconoCasual"
        )

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.get_json()["status"],
            "healthy"
        )

    def test_customers(self):
        response = self.client.get("/customers")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(data["total_customers"], 1000)
        self.assertLessEqual(len(data["customers"]), 20)

        self.assertIn("customer_id", data["columns"])
        self.assertIn("purchase", data["columns"])

    def test_purchase_summary(self):
        response = self.client.get("/purchase-summary")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(data["total_customers"], 1000)

        self.assertEqual(
            data["total_purchases"] + data["non_purchases"],
            data["total_customers"]
        )

        self.assertEqual(
            data["purchase_rate_percent"],
            57.3
        )

    def test_purchase_summary_response_structure(self):
        response = self.client.get("/purchase-summary")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertIn("total_customers", data)
        self.assertIn("total_purchases", data)
        self.assertIn("non_purchases", data)
        self.assertIn("purchase_rate_percent", data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
    
