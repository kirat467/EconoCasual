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

print("\n========== FINAL ANALYSIS INSIGHTS ==========")

purchase_rate = df["purchase"].mean() * 100
print(f"Overall Purchase Rate: {purchase_rate:.2f}%")

previous_corr = df["previous_purchases"].corr(df["purchase"])
engagement_corr = df["engagement"].corr(df["purchase"])
discount_corr = df["discount"].corr(df["purchase"])

print(f"Previous Purchases Correlation: {previous_corr:.2f}")
print(f"Engagement Correlation: {engagement_corr:.2f}")
print(f"Discount Correlation: {discount_corr:.2f}")

print("=============================================")

print("\n========== CUSTOMER PURCHASE COMPARISON ==========")

buyers = df[df["purchase"] == 1]
non_buyers = df[df["purchase"] == 0]

print("\nAverage Previous Purchases:")
print(f"Buyers: {buyers['previous_purchases'].mean():.2f}")
print(f"Non-buyers: {non_buyers['previous_purchases'].mean():.2f}")

print("\nAverage Engagement:")
print(f"Buyers: {buyers['engagement'].mean():.2f}")
print(f"Non-buyers: {non_buyers['engagement'].mean():.2f}")

print("\nAverage Discount:")
print(f"Buyers: {buyers['discount'].mean():.2f}")
print(f"Non-buyers: {non_buyers['discount'].mean():.2f}")

print("===================================================")

print("\n========== PURCHASE RATE BY ENGAGEMENT ==========")

engagement_purchase = df.groupby("engagement")["purchase"].mean() * 100

print("\nEngagement Level | Purchase Rate (%)")
print(engagement_purchase.round(2))

print("=================================================")

print("\n========== PURCHASE RATE BY DISCOUNT ==========")

discount_rates = df.groupby("discount")["purchase"].mean() * 100

print("\nDiscount | Purchase Rate (%)")
print(discount_rates.round(2))

print("===============================================")

# Find the customer group with the highest purchase rate

purchase_by_engagement = df.groupby("engagement")["purchase"].mean()

print("Purchase Rate by Engagement:")
print(purchase_by_engagement)

print("\nEngagement Level with Highest Purchase Rate:")
print(purchase_by_engagement.idxmax())

# Analyze purchase rate by previous purchases
purchase_by_previous = df.groupby("previous_purchases")["purchase"].mean()

print("Purchase Rate by Previous Purchases:")
print(purchase_by_previous)

# Plot purchase rate by previous purchases
import matplotlib.pyplot as plt

purchase_by_previous.plot(kind="bar", figsize=(8, 5))

plt.title("Purchase Rate by Previous Purchases")
plt.xlabel("Previous Purchases")
plt.ylabel("Purchase Rate")
plt.tight_layout()
plt.show()

# Plot purchase rate by engagement
purchase_by_engagement.plot(kind="bar", figsize=(8, 5))

plt.title("Purchase Rate by Customer Engagement")
plt.xlabel("Engagement Level")
plt.ylabel("Purchase Rate")
plt.tight_layout()
plt.show()

# Analyze engagement and previous purchases together
combined_analysis = df.groupby(
    ["engagement", "previous_purchases"]
)["purchase"].mean()

print("Purchase Rate by Engagement and Previous Purchases:")
print(combined_analysis)

    