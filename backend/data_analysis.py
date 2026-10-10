import pandas as pd
import numpy as np

# Create sample customer data
np.random.seed(42)

data = {
    "customer_id": range(1, 11),
    "previous_purchases": [2, 5, 1, 7, 3, 6, 2, 8, 4, 5],
    "discount": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
    "purchase": [1, 1, 1, 1, 0, 1, 1, 1, 1, 0]
}

# Create a DataFrame
df = pd.DataFrame(data)

# Display customer data
print("CUSTOMER DATA")
print(df)

# Compare purchase rates
print("\nPURCHASE RATE BY DISCOUNT")
print(df.groupby("discount")["purchase"].mean())

import matplotlib.pyplot as plt

# Calculate purchase rates
purchase_rates = df.groupby("discount")["purchase"].mean()

# Create a bar chart
purchase_rates.plot(kind="bar")

# Add chart labels
plt.title("Purchase Rate With and Without Discounts")
plt.xlabel("Discount (0 = No, 1 = Yes)")
plt.ylabel("Purchase Rate")
plt.xticks(rotation=0)

# Display the chart
plt.tight_layout()
plt.show()

    