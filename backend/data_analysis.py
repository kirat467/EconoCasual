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

# Heatmap of purchase rates
import matplotlib.pyplot as plt
import numpy as np

heatmap_data = df.pivot_table(
    index="engagement",
    columns="previous_purchases",
    values="purchase",
    aggfunc="mean"
)

plt.figure(figsize=(10, 6))

plt.imshow(heatmap_data, aspect="auto", cmap="YlGnBu", origin="lower")

plt.colorbar(label="Purchase Rate")
plt.title("Purchase Rate Heatmap")
plt.xlabel("Previous Purchases")
plt.ylabel("Customer Engagement")

plt.xticks(
    range(len(heatmap_data.columns)),
    heatmap_data.columns
)

plt.yticks(
    range(len(heatmap_data.index)),
    heatmap_data.index
)

plt.tight_layout()
plt.show()

# ==========================================
# CUSTOMER SEGMENTATION - UNIQUE FEATURE
# ==========================================

print("\n========== CUSTOMER SEGMENTATION ==========")

# Calculate median values
purchase_median = df["previous_purchases"].median()
engagement_median = df["engagement"].median()

# Classify customers into different segments
def classify_customer(row):
    if (row["previous_purchases"] >= purchase_median
            and row["engagement"] >= engagement_median):
        return "High-Value Customers"
    elif row["previous_purchases"] >= purchase_median:
        return "Loyal Customers"
    elif row["engagement"] >= engagement_median:
        return "Highly Engaged Customers"
    else:
        return "Customers Needing Attention"

df["customer_segment"] = df.apply(classify_customer, axis=1)

# Calculate customer count and purchase rate
segment_summary = df.groupby("customer_segment").agg(
    customer_count=("customer_id", "count"),
    purchase_rate=("purchase", "mean")
)

segment_summary["purchase_rate"] *= 100

print("\nCustomer Segment Summary:")
print(segment_summary.round(2))

# Visualize purchase rate by customer segment
plt.figure(figsize=(10, 6))

plt.bar(
    segment_summary.index,
    segment_summary["purchase_rate"]
)

plt.title("Purchase Rate by Customer Segment")
plt.xlabel("Customer Segment")
plt.ylabel("Purchase Rate (%)")
plt.xticks(rotation=20, ha="right")
plt.tight_layout()
plt.show()

print("\nCustomer segmentation completed successfully!")
print("============================================")

# ==========================================
# CUSTOMER PURCHASE RISK ANALYSIS
# ==========================================

print("\n========== CUSTOMER PURCHASE RISK ANALYSIS ==========")

def identify_risk(row):
    if row["engagement"] < engagement_median and row["previous_purchases"] < purchase_median:
        return "High Attention Needed"
    elif row["engagement"] < engagement_median or row["previous_purchases"] < purchase_median:
        return "Moderate Attention Needed"
    else:
        return "Low Attention Needed"

df["customer_risk"] = df.apply(identify_risk, axis=1)

risk_summary = df.groupby("customer_risk").agg(
    customer_count=("customer_id", "count"),
    actual_purchase_rate=("purchase", "mean")
)

risk_summary["actual_purchase_rate"] *= 100

print("\nCustomer Risk Summary:")
print(risk_summary.round(2))

plt.figure(figsize=(8, 5))
plt.bar(
    risk_summary.index,
    risk_summary["customer_count"]
)

plt.title("Customer Distribution by Attention Level")
plt.xlabel("Customer Attention Level")
plt.ylabel("Number of Customers")
plt.xticks(rotation=15, ha="right")
plt.tight_layout()
plt.show()

print("\nCustomer risk analysis completed successfully!")
print("======================================================")

# ==========================================
# ENGAGEMENT-BASED PURCHASE INSIGHTS
# ==========================================

print("\n========== ENGAGEMENT-BASED INSIGHTS ==========")

engagement_summary = df.groupby("engagement").agg(
    total_customers=("customer_id", "count"),
    purchases=("purchase", "sum"),
    purchase_rate=("purchase", "mean")
)

engagement_summary["purchase_rate"] *= 100

print("\nEngagement Analysis:")
print(engagement_summary.round(2))

# Find engagement level with the highest purchase rate
best_engagement = engagement_summary["purchase_rate"].idxmax()
best_rate = engagement_summary["purchase_rate"].max()

print(f"\nEngagement level with highest observed purchase rate: {best_engagement}")
print(f"Observed purchase rate at this level: {best_rate:.2f}%")

# Plot purchase rate by engagement
plt.figure(figsize=(9, 5))
plt.plot(
    engagement_summary.index,
    engagement_summary["purchase_rate"],
    marker="o"
)

plt.title("Customer Engagement vs Purchase Rate")
plt.xlabel("Engagement Level")
plt.ylabel("Purchase Rate (%)")
plt.xticks(engagement_summary.index)
plt.grid(True)
plt.tight_layout()
plt.show()

print("\nEngagement-based insights completed!")
print("==============================================")

# ==========================================
# EXPORT CUSTOMER INSIGHTS
# ==========================================

import os

print("\n========== EXPORTING CUSTOMER INSIGHTS ==========")

# Create the data folder if it doesn't exist
os.makedirs("data", exist_ok=True)

# Select useful customer information
insights = df.copy()

# Save results in a separate file
output_file = os.path.join("data", "customer_insights.csv")
insights.to_csv(output_file, index=False)

print("\nCustomer insights exported successfully!")
print(f"Total customer records: {len(insights)}")
print(f"Saved file: {output_file}")
print("Original customers.csv remains unchanged.")
print("=================================================")


# ==========================================
# CUSTOMER LOYALTY CLASSIFICATION
# ==========================================

print("\n========== CUSTOMER LOYALTY ANALYSIS ==========")

def classify_loyalty(row):
    if row["previous_purchases"] >= 7:
        return "Highly Loyal"
    elif row["previous_purchases"] >= 4:
        return "Moderately Loyal"
    else:
        return "New or Occasional"

df["loyalty_level"] = df.apply(classify_loyalty, axis=1)

loyalty_summary = df.groupby("loyalty_level").agg(
    customer_count=("customer_id", "count"),
    purchase_rate=("purchase", "mean")
)

loyalty_summary["purchase_rate"] *= 100

print("\nLoyalty Summary:")
print(loyalty_summary.round(2))

plt.figure(figsize=(8, 5))
plt.bar(
    loyalty_summary.index,
    loyalty_summary["customer_count"]
)

plt.title("Customer Loyalty Distribution")
plt.xlabel("Loyalty Level")
plt.ylabel("Number of Customers")
plt.tight_layout()
plt.show()

print("\nCustomer loyalty analysis completed!")
print("==============================================")

# ==========================================
# AUTOMATED CUSTOMER BEHAVIOR INSIGHTS
# ==========================================

print("\n========== CUSTOMER BEHAVIOR INSIGHTS ==========")

# Overall purchase rate
overall_rate = df["purchase"].mean() * 100

# Average customer behavior
avg_previous_purchases = df["previous_purchases"].mean()
avg_engagement = df["engagement"].mean()

# Compare buyers and non-buyers
buyers = df[df["purchase"] == 1]
non_buyers = df[df["purchase"] == 0]

print(f"\nOverall Purchase Rate: {overall_rate:.2f}%")
print(f"Average Previous Purchases: {avg_previous_purchases:.2f}")
print(f"Average Customer Engagement: {avg_engagement:.2f}")

print("\n--- Buyer vs Non-Buyer Comparison ---")
print(
    f"Buyers' Average Previous Purchases: "
    f"{buyers['previous_purchases'].mean():.2f}"
)
print(
    f"Non-Buyers' Average Previous Purchases: "
    f"{non_buyers['previous_purchases'].mean():.2f}"
)

print(
    f"Buyers' Average Engagement: "
    f"{buyers['engagement'].mean():.2f}"
)
print(
    f"Non-Buyers' Average Engagement: "
    f"{non_buyers['engagement'].mean():.2f}"
)

print("\n--- Business Recommendation ---")

if buyers["previous_purchases"].mean() > non_buyers["previous_purchases"].mean():
    print("Previous purchase history is associated with purchasing behavior.")
else:
    print("Previous purchase history shows no higher average among buyers.")

if buyers["engagement"].mean() > non_buyers["engagement"].mean():
    print("Higher engagement is associated with purchasing behavior.")
else:
    print("Higher engagement is not associated with a higher buyer average.")

print("\nInsight generation completed!")
print("=================================================")

# ==========================================
# CUSTOMER DATA VALIDATION
# ==========================================

print("\n========== CUSTOMER DATA VALIDATION ==========")

# Check for missing values
missing_values = df.isnull().sum()
print("\nMissing Values:")
print(missing_values)

# Check for duplicate customer IDs
duplicate_ids = df["customer_id"].duplicated().sum()
print(f"\nDuplicate Customer IDs: {duplicate_ids}")

# Validate purchase values
invalid_purchases = (~df["purchase"].isin([0, 1])).sum()
print(f"Invalid Purchase Values: {invalid_purchases}")

# Validate discount values
invalid_discounts = (~df["discount"].isin([0, 1])).sum()
print(f"Invalid Discount Values: {invalid_discounts}")

# Validate engagement range
invalid_engagement = (
    (~df["engagement"].between(1, 10))
).sum()
print(f"Invalid Engagement Values: {invalid_engagement}")

# Validate previous purchases
invalid_previous = (df["previous_purchases"] < 0).sum()
print(f"Invalid Previous Purchase Values: {invalid_previous}")

print("\nData validation completed!")
print("==============================================")

# Data Quality Check
print("\n===== DATA QUALITY CHECK =====")

print("\nMissing Values:")
print(df.isnull().sum())

print("\nDuplicate Customer IDs:")
print(df["customer_id"].duplicated().sum())

print("\nDataset Shape:")
print(df.shape)

print("==============================")
    