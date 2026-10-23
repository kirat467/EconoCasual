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

    def test_customers_response_is_json(self):
        response = self.client.get("/customers")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)

    def test_customer_values_are_integers(self):
        response = self.client.get("/customers")
        customer = response.get_json()["customers"][0]

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
        self.assertEqual(response.get_json()["returned_customers"], 10)

    def test_customers_offset(self):
        response = self.client.get("/customers?limit=10&offset=20")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["offset"], 20)
        self.assertEqual(response.get_json()["returned_customers"], 10)

    def test_customers_invalid_limit(self):
        response = self.client.get("/customers?limit=abc")
        self.assertEqual(response.status_code, 400)

    def test_customers_limit_out_of_range(self):
        response = self.client.get("/customers?limit=101")
        self.assertEqual(response.status_code, 400)

    def test_customers_negative_offset(self):
        response = self.client.get("/customers?offset=-1")
        self.assertEqual(response.status_code, 400)

    def test_customers_invalid_offset(self):
        response = self.client.get("/customers?offset=abc")
        self.assertEqual(response.status_code, 400)

    def test_customers_zero_limit(self):
        response = self.client.get("/customers?limit=0")
        self.assertEqual(response.status_code, 400)

    def test_customers_offset_beyond_dataset(self):
        response = self.client.get("/customers?limit=10&offset=2000")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["customers"], [])

    def test_purchase_summary(self):
        response = self.client.get("/purchase-summary")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(data["total_customers"], 1000)
        self.assertEqual(data["total_purchases"], 573)
        self.assertEqual(data["non_purchases"], 427)
        self.assertEqual(data["purchase_rate_percent"], 57.3)

    def test_purchase_counts_match_total_customers(self):
        data = self.client.get("/purchase-summary").get_json()

        self.assertEqual(
            data["total_purchases"] + data["non_purchases"],
            data["total_customers"]
        )

    def test_purchase_summary_response_structure(self):
        data = self.client.get("/purchase-summary").get_json()

        for key in [
            "total_customers",
            "total_purchases",
            "non_purchases",
            "purchase_rate_percent"
        ]:
            self.assertIn(key, data)

    def test_purchase_summary_values_are_numeric(self):
        data = self.client.get("/purchase-summary").get_json()

        self.assertIsInstance(data["total_customers"], int)
        self.assertIsInstance(data["total_purchases"], int)
        self.assertIsInstance(data["non_purchases"], int)
        self.assertIsInstance(
            data["purchase_rate_percent"], (int, float)
        )

    def test_purchase_summary_returns_json(self):
        response = self.client.get("/purchase-summary")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)

    def test_purchase_rate_is_valid(self):
        data = self.client.get("/purchase-summary").get_json()

        self.assertGreaterEqual(data["purchase_rate_percent"], 0)
        self.assertLessEqual(data["purchase_rate_percent"], 100)

    def test_discount_analysis(self):
        response = self.client.get("/discount-analysis")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIn("discount_groups", data)
        self.assertIn("0", data["discount_groups"])
        self.assertIn("1", data["discount_groups"])

    def test_discount_analysis_counts_and_rates(self):
        response = self.client.get("/discount-analysis")
        self.assertEqual(response.status_code, 200)

        groups = response.get_json()["discount_groups"]

        for group in groups.values():
            self.assertEqual(
                group["total_purchases"] + group["non_purchases"],
                group["total_customers"]
            )
            self.assertGreaterEqual(group["purchase_rate_percent"], 0)
            self.assertLessEqual(group["purchase_rate_percent"], 100)

    def test_previous_purchases_analysis(self):
        response = self.client.get("/previous-purchases-analysis")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIn("previous_purchase_groups", data)
        self.assertGreater(len(data["previous_purchase_groups"]), 0)

    def test_previous_purchase_analysis_counts(self):
        response = self.client.get("/previous-purchases-analysis")
        self.assertEqual(response.status_code, 200)

        groups = response.get_json()["previous_purchase_groups"]

        for group in groups.values():
            self.assertEqual(
                group["total_purchases"] + group["non_purchases"],
                group["total_customers"]
            )
            self.assertGreaterEqual(group["purchase_rate_percent"], 0)
            self.assertLessEqual(group["purchase_rate_percent"], 100)

    def test_engagement_analysis(self):
        response = self.client.get("/engagement-analysis")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIn("engagement_groups", data)
        self.assertGreater(len(data["engagement_groups"]), 0)

    def test_engagement_analysis_counts_and_rates(self):
        response = self.client.get("/engagement-analysis")
        self.assertEqual(response.status_code, 200)

        groups = response.get_json()["engagement_groups"]

        for group in groups.values():
            self.assertEqual(
                group["total_purchases"] + group["non_purchases"],
                group["total_customers"]
            )
            self.assertGreaterEqual(group["purchase_rate_percent"], 0)
            self.assertLessEqual(group["purchase_rate_percent"], 100)

    def test_validate_data(self):
        response = self.client.get("/validate-data")

        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(data["total_rows"], 1000)
        self.assertIn("missing_values_by_column", data)
        self.assertIn("duplicate_customer_ids", data)
        self.assertIn("invalid_purchase_rows", data)
        self.assertIn("is_valid", data)

    def test_validate_data_missing_values_counts(self):
        response = self.client.get("/validate-data")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        for count in data["missing_values_by_column"].values():
            self.assertGreaterEqual(count, 0)

    def test_customer_statistics(self):
        response = self.client.get("/customer-statistics")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)

        data = response.get_json()
        self.assertEqual(data["total_customers"], 1000)

        for column in [
            "previous_purchases",
            "engagement",
            "discount"
        ]:
            self.assertIn(column, data["statistics"])

            stats = data["statistics"][column]
            self.assertIn("average", stats)
            self.assertIn("minimum", stats)
            self.assertIn("maximum", stats)
            self.assertIn("count", stats)

    def test_customer_statistics_values_are_valid(self):
        response = self.client.get("/customer-statistics")
        self.assertEqual(response.status_code, 200)

        statistics = response.get_json()["statistics"]

        for stats in statistics.values():
            self.assertGreaterEqual(stats["count"], 1)
            self.assertLessEqual(stats["minimum"], stats["maximum"])
            self.assertGreaterEqual(
                stats["average"], stats["minimum"]
            )
            self.assertLessEqual(
                stats["average"], stats["maximum"]
            )

    def test_customer_statistics_average_is_numeric(self):
        response = self.client.get("/customer-statistics")
        self.assertEqual(response.status_code, 200)

        statistics = response.get_json()["statistics"]

        for stats in statistics.values():
            self.assertIsInstance(stats["average"], (int, float))

    def test_invalid_url(self):
        response = self.client.get("/invalid-url")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main(verbosity=2)