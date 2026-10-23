from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "customers.csv"
REPORT_DIR = BASE_DIR / "reports"
OUTPUT_FILE = REPORT_DIR / "backend_summary.md"


def dataframe_to_markdown(df):
    """Convert a DataFrame into a Markdown table without extra packages."""
    headers = [str(column) for column in df.columns]
    rows = df.fillna("").astype(str).values.tolist()

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for row in rows:
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def generate_backend_summary():
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

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(f"Missing columns: {missing_columns}")

    if df.empty:
        raise ValueError("Customer dataset is empty.")

    numeric_columns = [
        "previous_purchases",
        "engagement",
        "discount",
        "purchase",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="raise")

    if df[required_columns].isna().any().any():
        raise ValueError("Required columns contain missing values.")

    if not df["purchase"].isin([0, 1]).all():
        raise ValueError("Purchase values must be 0 or 1.")

    total_customers = len(df)
    total_purchases = int(df["purchase"].sum())
    non_purchases = total_customers - total_purchases
    purchase_rate = total_purchases / total_customers * 100

    discount_summary = (
        df.groupby("discount", observed=True)
        .agg(
            customers=("customer_id", "count"),
            purchases=("purchase", "sum"),
            purchase_rate=("purchase", "mean"),
        )
        .reset_index()
    )
    discount_summary["purchase_rate"] = (
        discount_summary["purchase_rate"] * 100
    ).round(2)

    engagement_summary = (
        df.groupby("engagement", observed=True)
        .agg(
            customers=("customer_id", "count"),
            purchases=("purchase", "sum"),
            purchase_rate=("purchase", "mean"),
        )
        .reset_index()
    )
    engagement_summary["purchase_rate"] = (
        engagement_summary["purchase_rate"] * 100
    ).round(2)

    history_summary = (
        df.groupby("previous_purchases", observed=True)
        .agg(
            customers=("customer_id", "count"),
            purchases=("purchase", "sum"),
            purchase_rate=("purchase", "mean"),
        )
        .reset_index()
    )
    history_summary["purchase_rate"] = (
        history_summary["purchase_rate"] * 100
    ).round(2)

    discount_table = dataframe_to_markdown(discount_summary)
    engagement_table = dataframe_to_markdown(engagement_summary)
    history_table = dataframe_to_markdown(history_summary)

    report = f"""# EconoCasual Backend Summary Report

## 1. Project Overview

This report summarizes customer purchasing behaviour using the
EconoCasual customer dataset.

## 2. Overall Purchase Statistics

- **Total customers:** {total_customers}
- **Customers who purchased:** {total_purchases}
- **Customers who did not purchase:** {non_purchases}
- **Overall purchase rate:** {purchase_rate:.2f}%

## 3. Discount Analysis

{discount_table}

## 4. Engagement Analysis

{engagement_table}

## 5. Previous Purchase History

{history_table}

## 6. Key Findings

- The overall purchase rate is {purchase_rate:.2f}%.
- {total_purchases} customers made a purchase.
- {non_purchases} customers did not make a purchase.
- Discount, engagement, and previous purchase history were analyzed
  to summarize customer purchasing behaviour.

## 7. Limitations

These results describe the available dataset and do not prove that
discounts, engagement, or previous purchases cause customers to buy.
Further analysis and model validation are needed before making predictions.

## 8. Conclusion

This report brings together the main descriptive statistics for
EconoCasual customer purchasing behaviour.
"""

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(report, encoding="utf-8")

    print("Backend summary report generated successfully!")
    print(f"Report saved to: {OUTPUT_FILE}")
    print(f"Total customers: {total_customers}")
    print(f"Total purchases: {total_purchases}")
    print(f"Non-purchases: {non_purchases}")
    print(f"Purchase rate: {purchase_rate:.2f}%")

    return report


if __name__ == "__main__":
    generate_backend_summary()