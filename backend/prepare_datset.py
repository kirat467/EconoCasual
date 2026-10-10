import pandas as pd
import numpy as np

# Generate reproducible sample data
np.random.seed(42)

n = 1000

# Customer characteristics
previous_purchases = np.random.randint(0, 10, n)
engagement = np.random.randint(1, 11, n)

# Simulate discount assignment
discount_probability = 1 / (
    1 + np.exp(
        -(0.5 - 0.15 * previous_purchases
          + 0.10 * engagement)
    )
)

discount = np.random.binomial(
    1, discount_probability
)

# Simulate purchase outcomes
purchase_probability = 1 / (
    1 + np.exp(
        -(-2
          + 0.25 * previous_purchases
          + 0.15 * engagement
          + 0.8 * discount)
    )
)

purchase = np.random.binomial(
    1, purchase_probability
)

# Create the dataset
df = pd.DataFrame({
    "customer_id": range(1, n + 1),
    "previous_purchases": previous_purchases,
    "engagement": engagement,
    "discount": discount,
    "purchase": purchase
})

# Save the dataset
df.to_csv("data/customers.csv", index=False)

print("Dataset created successfully!")
print("\nFirst five customers:")
print(df.head())

print("\nDataset information:")
print(df.info())

print("\nPurchase rate by discount:")
print(df.groupby("discount")["purchase"].mean())

