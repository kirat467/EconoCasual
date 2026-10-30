import unittest
import pandas as pd

from backend.baseline_model import (
    load_customer_data,
    train_baseline_model,
    calculate_naive_difference,
)


class TestBaselineModel(unittest.TestCase):

    def setUp(self):
        # Create sample customer data for testing
        self.df = pd.DataFrame({
            "previous_purchases": [1, 2, 3, 4, 5, 6, 7, 8],
            "engagement": [0, 1, 0, 1, 0, 1, 0, 1],
            "discount": [0, 1, 0, 1, 0, 1, 0, 1],
            "purchase": [0, 1, 0, 1, 0, 1, 0, 1],
        })

    def test_load_customer_data(self):
        # Check that the original customer dataset loads correctly
        df = load_customer_data()

        self.assertEqual(len(df), 1000)

        self.assertTrue(
            {
                "previous_purchases",
                "engagement",
                "discount",
                "purchase",
            }.issubset(df.columns)
        )

    def test_train_baseline_model(self):
        # Check model training and AUC calculation
        model, test, auc = train_baseline_model(self.df)

        self.assertIsNotNone(model)
        self.assertGreater(len(test), 0)
        self.assertGreaterEqual(auc, 0)
        self.assertLessEqual(auc, 1)

    def test_model_prediction(self):
        # Check that the trained model produces predictions
        model, test, auc = train_baseline_model(self.df)

        predictions = model.predict(
            test[
                [
                    "previous_purchases",
                    "engagement",
                    "discount",
                ]
            ]
        )

        self.assertEqual(len(predictions), len(test))

    def test_naive_difference(self):
        # Check observed purchase-rate difference
        result = calculate_naive_difference(self.df)

        self.assertAlmostEqual(result, 1.0)

    def test_missing_columns(self):
        # Check that missing required columns raise an error
        invalid_df = self.df.drop(columns=["discount"])

        with self.assertRaises(ValueError):
            train_baseline_model(invalid_df)

    def test_missing_values(self):
        # Check that missing values raise an error
        invalid_df = self.df.copy()
        invalid_df.loc[0, "purchase"] = None

        with self.assertRaises(ValueError):
            train_baseline_model(invalid_df)

    def test_invalid_purchase_values(self):
        # Check that purchase values other than 0 and 1 are rejected
        invalid_df = self.df.copy()
        invalid_df["purchase"] = [0, 1, 0, 1, 0, 1, 0, 2]

        with self.assertRaises(ValueError):
            train_baseline_model(invalid_df)

    def test_missing_discount_group(self):
        # Check that both discount groups are required
        invalid_df = self.df.copy()
        invalid_df["discount"] = 1

        with self.assertRaises(ValueError):
            calculate_naive_difference(invalid_df)


if __name__ == "__main__":
    unittest.main()

