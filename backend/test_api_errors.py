import unittest
from pathlib import Path
from unittest.mock import patch

from app import app

class TestAPIErrorHandling(unittest.TestCase):


 @classmethod
 def setUpClass(cls):
    app.config["TESTING"] = True
    cls.client = app.test_client()

 def test_unknown_endpoint_returns_404(self):
    response = self.client.get("/this-endpoint-does-not-exist")

    self.assertEqual(response.status_code, 404)

 def test_unknown_endpoint_returns_json(self):
    response = self.client.get("/this-endpoint-does-not-exist")

    self.assertTrue(response.is_json)
    self.assertEqual(
        response.get_json()["error"],
        "Endpoint not found",
    )

 def test_customers_endpoint_handles_invalid_page(self):
    response = self.client.get("/customers?page=invalid")

    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.is_json)

 def test_customers_endpoint_handles_zero_page(self):
    response = self.client.get("/customers?page=0")

    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.get_json()["page"], 1)

 def test_customers_endpoint_handles_negative_page(self):
    response = self.client.get("/customers?page=-1")

    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.get_json()["page"], 1)

 def test_customers_endpoint_handles_large_page(self):
    response = self.client.get("/customers?page=999999")

    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.get_json()["customers"], [])

 def test_customers_endpoint_rejects_invalid_filters(self):
    for column in ["discount", "engagement", "purchase"]:
        with self.subTest(column=column):
            response = self.client.get(
                f"/customers?{column}=invalid"
            )

            self.assertEqual(response.status_code, 400)
            self.assertTrue(response.is_json)
            self.assertIn("error", response.get_json())

 def test_customers_endpoint_rejects_non_finite_filters(self):
    for value in ["NaN", "inf", "-inf"]:
        for column in ["discount", "engagement", "purchase"]:
            with self.subTest(column=column, value=value):
                response = self.client.get(
                    f"/customers?{column}={value}"
                )

                self.assertEqual(response.status_code, 400)
                self.assertTrue(response.is_json)

 def test_customers_endpoint_handles_missing_dataset(self):
    with patch(
        "app.DATA_FILE",
        Path("missing_customers_test.csv"),
    ):
        response = self.client.get("/customers")

    self.assertEqual(response.status_code, 500)
    self.assertTrue(response.is_json)
    self.assertEqual(
        response.get_json()["error"],
        "Customer dataset not found",
    )


if __name__ == "__main__":
    unittest.main(verbosity=2)
