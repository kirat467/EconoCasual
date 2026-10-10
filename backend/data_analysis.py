import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

project_folder = Path(__file__).resolve().parent.parent
file_path = project_folder / "data" / "customers.csv"

df = pd.read_csv(file_path)

print("ECONOCASUAL - DATA ANALYSIS")
print("===========================")

print("\nCUSTOMER DATA")
print(df.head())

print("\nDATASET SHAPE")
print(df.shape)

print("\nCOLUMN NAMES")
print(df.columns.tolist())

print("\nMISSING VALUES")
print(df.isnull().sum())

print("\nDUPLICATE ROWS")
print(df.duplicated().sum())

print("\nPURCHASE RATE BY DISCOUNT")
purchase_rates = df.groupby("discount")["purchase"].mean()
print(purchase_rates)

print("\nPURCHASE RATE BY PREVIOUS PURCHASES")
previous_purchase_rates = df.groupby("previous_purchases")["purchase"].mean()
print(previous_purchase_rates)

# Chart 1: Purchase rate by discount
purchase_rates.plot(kind="bar")

plt.title("Purchase Rate with and without Discounts")
plt.xlabel("Discount (0 = No, 1 = Yes)")
plt.ylabel("Purchase Rate")
plt.xticks(rotation=0)

plt.tight_layout()
plt.show()

# First chart
purchase_rates.plot(kind="bar")

plt.title("Purchase Rate with and without Discounts")
plt.xlabel("Discount (0 = No, 1 = Yes)")
plt.ylabel("Purchase Rate")

plt.tight_layout()
plt.show()

print("FIRST CHART CLOSED")

# Second chart
print("PREPARING SECOND CHART")

print("OPENING SECOND CHART")

plt.figure(figsize=(8, 5))
previous_purchase_rates.plot(kind="bar")

plt.title("Purchase Rate by Previous Purchases")
plt.xlabel("Previous Purchases")
plt.ylabel("Purchase Rate")

plt.tight_layout()
plt.show()

print("SECOND CHART CLOSED")
