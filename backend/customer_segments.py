from pathlib import Path

import pandas as pd


# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "customers.csv"
REPORT_DIR = BASE_DIR / "reports"

SEGMENTS_FILE = REPORT_DIR / "customer_segments.csv"
SUMMARY_FILE = REPORT_DIR / "customer_segments_summary.csv"


def create_customer_segments():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_FILE}"
        )

    df = pd.read_csv(DATA_FILE)

    required_columns = [
        "customer_id",
        "previous_purchases",
        "engagement",
        "discount",
        "purchase",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    if df.empty:
        raise ValueError("The customer dataset is empty.")

    # Convert analysis columns to numeric values
    numeric_columns = [
        "previous_purchases",
        "engagement",
        "discount",
        "purchase",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="raise"
        )

    # Divide customers into engagement groups
    df["engagement_segment"] = pd.qcut(
        df["engagement"].rank(method="first"),
        q=3,
        labels=["Low Engagement", "Medium Engagement", "High Engagement"],
    )

    # Divide customers by previous purchase history
    df["purchase_history_segment"] = pd.qcut(
        df["previous_purchases"].rank(method="first"),
        q=3,
        labels=["Low Purchase History", "Medium Purchase History", "High Purchase History"],
    )

    # Calculate statistics for each customer segment
    summary = (
        df.groupby(
            ["engagement_segment", "purchase_history_segment"],
            observed=False,
        )
        .agg(
            total_customers=("customer_id", "count"),
            total_purchases=("purchase", "sum"),
            average_engagement=("engagement", "mean"),
            average_previous_purchases=("previous_purchases", "mean"),
        )
        .reset_index()
    )

    summary["purchase_rate_percent"] = (
        summary["total_purchases"]
        / summary["total_customers"].replace(0, pd.NA)
        * 100
    ).fillna(0).round(2)

    # Create output folder if it does not exist
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    # Save detailed customer segments and summary
    df.to_csv(SEGMENTS_FILE, index=False)
    summary.to_csv(SUMMARY_FILE, index=False)

    print("Customer segmentation completed successfully!")
    print(f"Total customers analyzed: {len(df)}")
    print(f"Detailed results saved to: {SEGMENTS_FILE}")
    print(f"Segment summary saved to: {SUMMARY_FILE}")
    print("\nSegment Summary:")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    create_customer_segments()