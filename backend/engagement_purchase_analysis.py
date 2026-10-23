from pathlib import Path

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "customers.csv"
REPORT_DIR = BASE_DIR / "reports"
CHART_DIR = REPORT_DIR / "charts"

OUTPUT_FILE = REPORT_DIR / "engagement_purchase_analysis.csv"
CHART_FILE = CHART_DIR / "engagement_purchase_rate.png"


def analyze_engagement_purchase():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

    df = pd.read_csv(DATA_FILE)

    required_columns = ["customer_id", "engagement", "purchase"]
    missing = [column for column in required_columns if column not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if df.empty:
        raise ValueError("Customer dataset is empty.")

    df["engagement"] = pd.to_numeric(df["engagement"], errors="raise")
    df["purchase"] = pd.to_numeric(df["purchase"], errors="raise")

    if df["engagement"].isna().any() or df["purchase"].isna().any():
        raise ValueError("Engagement and purchase cannot contain missing values.")

    if not df["purchase"].isin([0, 1]).all():
        raise ValueError("Purchase values must be 0 or 1.")

    summary = (
        df.groupby("engagement")
        .agg(
            customer_count=("customer_id", "count"),
            total_purchases=("purchase", "sum"),
            average_purchase=("purchase", "mean"),
        )
        .reset_index()
    )

    summary["non_purchases"] = (
        summary["customer_count"] - summary["total_purchases"]
    )

    summary["purchase_rate_percent"] = (
        summary["average_purchase"] * 100
    ).round(2)

    summary = summary.drop(columns=["average_purchase"])

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    CHART_DIR.mkdir(parents=True, exist_ok=True)

    summary.to_csv(OUTPUT_FILE, index=False)

    plt.figure(figsize=(9, 5))
    plt.bar(
        summary["engagement"].astype(str),
        summary["purchase_rate_percent"],
    )
    plt.title("Purchase Rate by Customer Engagement")
    plt.xlabel("Engagement Level")
    plt.ylabel("Purchase Rate (%)")
    plt.ylim(0, 100)
    plt.tight_layout()
    plt.savefig(CHART_FILE)
    plt.close()

    print("Engagement analysis completed successfully!")
    print(f"Customers analyzed: {len(df)}")
    print(f"Report saved: {OUTPUT_FILE}")
    print(f"Chart saved: {CHART_FILE}")

    return summary


if __name__ == "__main__":
    result = analyze_engagement_purchase()
    print(result.to_string(index=False))