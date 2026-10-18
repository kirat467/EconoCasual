import pandas as pd
import os

# Generate Customer Insights Summary
file_path = "data/customer_insights.csv"

print("\n===== CUSTOMER INSIGHTS SUMMARY =====")

if os.path.exists(file_path):
    df = pd.read_csv(file_path)

    total_customers = len(df)
    total_purchases = df["purchase"].sum()
    purchase_rate = df["purchase"].mean() * 100

    summary = f"""
ECONOCASUAL - CUSTOMER INSIGHTS SUMMARY

Total Customers: {total_customers}
Total Purchases: {total_purchases}
Total Non-Purchases: {total_customers - total_purchases}
Overall Purchase Rate: {purchase_rate:.2f}%

Average Previous Purchases: {df['previous_purchases'].mean():.2f}
Average Customer Engagement: {df['engagement'].mean():.2f}

This summary describes observed customer behavior.
It does not establish causal relationships.
"""

    os.makedirs("reports", exist_ok=True)

    with open("reports/customer_summary.txt", "w", encoding="utf-8") as file:
        file.write(summary)

    print(summary)
    print("Summary saved to reports/customer_summary.txt")

else:
    print("Customer insights file not found.")

print("=====================================")