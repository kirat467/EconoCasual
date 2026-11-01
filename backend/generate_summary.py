from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "reports" / "customer_insights.csv"
OUTPUT_FILE = BASE_DIR / "reports" / "customer_summary.txt"

REQUIRED_COLUMNS = [
    "customer_id",
    "purchase",
    "previous_purchases",
    "engagement",
]


def load_customer_data(file_path=DATA_FILE):
    """Load customer insights from a CSV file."""
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Customer insights file not found: {file_path}"
        )

    return pd.read_csv(file_path)


def validate_customer_data(df):
    """Validate the columns and values required for the summary."""
    errors = []

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        errors.append(f"Missing columns: {missing_columns}")
        return errors

    if df.empty:
        errors.append("Customer dataset is empty.")
        return errors

    if df[REQUIRED_COLUMNS].isnull().any().any():
        errors.append("Required columns contain missing values.")

    for column in ["purchase", "previous_purchases", "engagement"]:
        converted = pd.to_numeric(df[column], errors="coerce")

        if converted.isna().any():
            errors.append(f"Column '{column}' contains non-numeric values.")
            continue

        if not converted.map(lambda value: float("-inf") < float(value) < float("inf")).all():
            errors.append(f"Column '{column}' contains non-finite values.")

    purchase = pd.to_numeric(df["purchase"], errors="coerce")

    if purchase.notna().all() and not purchase.isin([0, 1]).all():
        errors.append("Purchase values must be 0 or 1.")

    previous = pd.to_numeric(df["previous_purchases"], errors="coerce")
    if previous.notna().all() and (previous < 0).any():
        errors.append("Previous purchases cannot be negative.")

    engagement = pd.to_numeric(df["engagement"], errors="coerce")
    if engagement.notna().all() and not engagement.between(1, 10).all():
        errors.append("Engagement values must be between 1 and 10.")

    return errors


def build_customer_summary(df):
    """Build a text summary of observed customer behavior."""
    errors = validate_customer_data(df)

    if errors:
        raise ValueError("; ".join(errors))

    total_customers = len(df)
    total_purchases = int(pd.to_numeric(df["purchase"]).sum())
    total_non_purchases = total_customers - total_purchases
    purchase_rate = (
        pd.to_numeric(df["purchase"]).mean() * 100
    )

    average_previous_purchases = (
        pd.to_numeric(df["previous_purchases"]).mean()
    )
    average_engagement = (
        pd.to_numeric(df["engagement"]).mean()
    )

    return f"""ECONOCASUAL - CUSTOMER INSIGHTS SUMMARY

Total Customers: {total_customers}
Total Purchases: {total_purchases}
Total Non-Purchases: {total_non_purchases}
Overall Purchase Rate: {purchase_rate:.2f}%

Average Previous Purchases: {average_previous_purchases:.2f}
Average Customer Engagement: {average_engagement:.2f}

This summary describes observed customer behavior.
It does not establish causal relationships.
"""


def generate_summary(file_path=DATA_FILE, output_file=OUTPUT_FILE):
    """Load, validate, generate, and save the customer summary."""
    df = load_customer_data(file_path)
    summary = build_customer_summary(df)

    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(summary, encoding="utf-8")

    print("\n===== ECONOCASUAL CUSTOMER SUMMARY =====")
    print(summary)
    print(f"Summary saved to: {output_file}")
    print("========================================")

    return summary


if __name__ == "__main__":
    try:
        generate_summary()
    except (FileNotFoundError, ValueError) as error:
        print(f"Summary generation failed: {error}")
