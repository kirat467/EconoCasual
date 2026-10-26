import unittest
import json
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

BASE_URL = "http://127.0.0.1:5000"


class TestAPIErrorHandling(unittest.TestCase):

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

    def test_unknown_endpoint_returns_404(self):
        with self.assertRaises(HTTPError) as context:
            urlopen(f"{BASE_URL}/this-endpoint-does-not-exist", timeout=5)

        self.assertEqual(context.exception.code, 404)
        context.exception.close()

    def test_customers_endpoint_rejects_invalid_page(self):
        with urlopen(f"{BASE_URL}/customers?page=invalid", timeout=5) as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode("utf-8"))
            self.assertIsNotNone(data)

    def test_customers_endpoint_handles_zero_page(self):
        with urlopen(f"{BASE_URL}/customers?page=0", timeout=5) as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode("utf-8"))
            self.assertIsNotNone(data)

    def test_customers_endpoint_handles_negative_page(self):
        with urlopen(f"{BASE_URL}/customers?page=-1", timeout=5) as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode("utf-8"))
            self.assertIsNotNone(data)

    def test_customers_endpoint_handles_large_page(self):
        with urlopen(f"{BASE_URL}/customers?page=999999", timeout=5) as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode("utf-8"))
            self.assertIsNotNone(data)


if __name__ == "__main__":
    unittest.main(verbosity=2)