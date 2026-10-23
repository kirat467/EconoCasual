from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "customers.csv"
REPORT_DIR = BASE_DIR / "reports"
OUTPUT_FILE = REPORT_DIR / "customer_purchase_insights.md"


def generate_purchase_insights():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

    df = pd.read_csv(DATA_FILE)

    required_columns = [
        "customer_id",
        "previous_purchases",
        "engagement",
        "discount",
        "purchase",
    ]

    missing = [column for column in required_columns if column not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if df.empty:
        raise ValueError("Customer dataset is empty.")

    for column in ["previous_purchases", "engagement", "discount", "purchase"]:
        df[column] = pd.to_numeric(df[column], errors="raise")

    if df[required_columns].isna().any().any():
        raise ValueError("Dataset contains missing values in required columns.")

    if not df["purchase"].isin([0, 1]).all():
        raise ValueError("Purchase values must be 0 or 1.")

    total_customers = len(df)
    total_purchases = int(df["purchase"].sum())
    non_purchases = total_customers - total_purchases
    purchase_rate = total_purchases / total_customers * 100

    history_summary = (
        df.groupby("previous_purchases")["purchase"]
        .agg(["count", "sum", "mean"])
        .reset_index()
    )
    history_summary["purchase_rate_percent"] = (
        history_summary["mean"] * 100
    ).round(2)

    engagement_summary = (
        df.groupby("engagement")["purchase"]
        .agg(["count", "sum", "mean"])
        .reset_index()
    )
    engagement_summary["purchase_rate_percent"] = (
        engagement_summary["mean"] * 100
    ).round(2)

    discount_summary = (
        df.groupby("discount")["purchase"]
        .agg(["count", "sum", "mean"])
        .reset_index()
    )
    discount_summary["discount_group"] = discount_summary["discount"].map({
        0: "No Discount",
        1: "Discount",
    })
    discount_summary["purchase_rate_percent"] = (
        discount_summary["mean"] * 100
    ).round(2)

    history_lines = [
        "| Previous purchases | Customers | Purchases | Purchase rate (%) |",
        "|---:|---:|---:|---:|",
    ]
    for _, row in history_summary.iterrows():
        history_lines.append(
            f"| {row['previous_purchases']} | {int(row['count'])} | "
            f"{int(row['sum'])} | {row['purchase_rate_percent']:.2f} |"
        )

    engagement_lines = [
        "| Engagement | Customers | Purchases | Purchase rate (%) |",
        "|---:|---:|---:|---:|",
    ]
    for _, row in engagement_summary.iterrows():
        engagement_lines.append(
            f"| {row['engagement']} | {int(row['count'])} | "
            f"{int(row['sum'])} | {row['purchase_rate_percent']:.2f} |"
        )

    discount_lines = [
        "| Group | Customers | Purchases | Purchase rate (%) |",
        "|---|---:|---:|---:|",
    ]
    for _, row in discount_summary.iterrows():
        discount_lines.append(
            f"| {row['discount_group']} | {int(row['count'])} | "
            f"{int(row['sum'])} | {row['purchase_rate_percent']:.2f} |"
        )

    report = f"""# Customer Purchase Insights Report

## 1. Dataset Overview

- **Total customers analyzed:** {total_customers}
- **Customers who purchased:** {total_purchases}
- **Customers who did not purchase:** {non_purchases}
- **Overall purchase rate:** {purchase_rate:.2f}%

## 2. Purchase History Analysis

{chr(10).join(history_lines)}

## 3. Engagement Analysis

{chr(10).join(engagement_lines)}

## 4. Discount Analysis

{chr(10).join(discount_lines)}

## 5. Key Notes

- The overall purchase rate is **{purchase_rate:.2f}%**.
- Purchase rates vary across previous-purchase and engagement groups.
- Discount-group rates show the observed association between discount status and purchases.
- These are descriptive findings from the available dataset; they do not establish that discounts or engagement caused a purchase.

## 6. Future Work

- Compare these findings with the purchase-prediction model.
- Evaluate model performance using suitable metrics.
- Integrate the analysis outputs during the planned final integration phase.
"""

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(report, encoding="utf-8")

    print("Customer purchase insights report generated successfully!")
    print(f"Customers analyzed: {total_customers}")
    print(f"Overall purchase rate: {purchase_rate:.2f}%")
    print(f"Report saved: {OUTPUT_FILE}")

    return report


if __name__ == "__main__":
    generate_purchase_insights()