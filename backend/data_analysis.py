import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

pd.set_option("display.max_rows", None)

project_folder = Path(__file__).resolve().parent.parent
file_path = project_folder / "data" / "customers.csv"

df = pd.read_csv(file_path)
print("Column names:",df.columns.tolist())

print("ECONOCASUAL - DATA ANALYSIS")
print("===========================")

print("\nCUSTOMER DATA")
print(df.head())

print("\nDATASET SHAPE")
print(df.shape)

print("\nCOLUMN NAMES")
print(df.columns.tolist())
print("ACTUAL CLUMN NAMES:",df.columns.tolist())

print("\nMISSING VALUES")
print(df.isnull().sum())

print("\nDUPLICATE ROWS")
print(df.duplicated().sum())

print("\nPURCHASE RATE BY DISCOUNT")
purchase_rates = df.groupby("discount")["purchase"].mean()
print(purchase_rates)

print("\nOVERALL PURCHASE RATE")

overall_purchase_rate = df["purchase"].mean()

print(f"Overall Purchase Rate: {overall_purchase_rate:.2%}")

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

print("\n========== ANALYSIS SUMMARY ==========")
print(f"Total customers: {len(df)}")
print(f"Overall purchase rate: {df['purchase'].mean():.2%}")
print("======================================")

# Customer Engagement Analysis

print("\n--- Customer Engagement Analysis ---")

if "engagement" in df.columns:
    print("\nAverage Engagement Rate:")
    print(df["engagement"].mean())

    print("\nEngagement Statistics:")
    print(df["engagement"].describe())

    if "purchase" in df.columns:
        print("\nPurchase Rate by Engagement:")

        engagement_purchase = df.groupby("engagement")["purchase"].mean()

        print(engagement_purchase)
else:
    print("Engagement column not found.")
    print("Available columns:")
    print(df.columns.tolist())

    # Purchase Rate by Engagement Chart

import matplotlib.pyplot as plt

if "engagement" in df.columns and "purchase" in df.columns:

    engagement_purchase = df.groupby("engagement")["purchase"].mean()

    plt.figure(figsize=(8, 5))
    engagement_purchase.plot(kind="bar")

    plt.title("Purchase Rate by Engagement")
    plt.xlabel("Engagement")
    plt.ylabel("Purchase Rate")
    plt.xticks(rotation=0)

    plt.tight_layout()
    plt.show()

print("\n========== CUSTOMER PURCHASE COMPARISON ==========")

purchase_history = df.groupby("previous_purchases")["purchase"].mean()

print("\nPurchase rate by previous purchases:")
print((purchase_history * 100).round(2).astype(str) + "%")

highest_group = purchase_history.idxmax()
highest_rate = purchase_history.max()

print(f"\nHighest purchase rate: customers with {highest_group} previous purchases")
print(f"Purchase rate: {highest_rate:.2%}")

print("===================================================")

print("\n========== DATA QUALITY CHECK ==========")

print("\nDataset Shape:")
print(df.shape)

print("\nMissing Values:")
print(df.isnull().sum())

print("\nDuplicate Rows:")
print(df.duplicated().sum())

print("\nDataset Information:")
df.info()

print("========================================")

print("\n========== PURCHASE DISTRIBUTION ==========")

print("\nPurchase Counts:")
print(df["purchase"].value_counts())

print("\nPurchase Percentages:")
print((df["purchase"].value_counts(normalize=True) * 100).round(2))

print("\n============================================")

print("\n========== DESCRIPTIVE STATISTICS ==========")

print("\nCustomer Data Summary:")
print(df.describe())

print("\n=============================================")

print("\n========== CORRELATION ANALYSIS ==========")

correlation = df[
    ["previous_purchases", "engagement", "discount", "purchase"]
].corr()

print("\nCorrelation Between Variables:")
print(correlation.round(2))

print("\nCorrelation with Purchase:")
print(correlation["purchase"].drop("purchase").round(2))

print("==========================================")

    