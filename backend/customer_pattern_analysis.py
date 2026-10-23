
from pathlib import Path

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "customers.csv"
REPORT_DIR = BASE_DIR / "reports"
CHART_DIR = REPORT_DIR / "charts"

OUTPUT_FILE = REPORT_DIR / "customer_pattern_analysis.csv"
CHART_FILE = CHART_DIR / "customer_purchase_patterns.png"


def analyze_customer_patterns():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

    df = pd.read_csv(DATA_FILE)

    required_columns = [
        "customer_id",
        "previous_purchases",
        "engagement",
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

    df["previous_purchases"] = pd.to_numeric(
        df["previous_purchases"], errors="raise"
    )
    df["purchase"] = pd.to_numeric(
        df["purchase"], errors="raise"
    )

    if not df["purchase"].isin([0, 1]).all():
        raise ValueError("Purchase values must be 0 or 1.")

    df["purchase_group"] = df["purchase"].map({
        0: "No Purchase",
        1: "Purchase",
    })

    summary = (
        df.groupby("previous_purchases")
        .agg(
            customer_count=("customer_id", "count"),
            purchasers=("purchase", "sum"),
            average_engagement=("engagement", "mean"),
        )
        .reset_index()
    )

    summary["non_purchasers"] = (
        summary["customer_count"] - summary["purchasers"]
    )

    summary["purchase_rate_percent"] = (
        summary["purchasers"]
        / summary["customer_count"]
        * 100
    ).round(2)

    summary["average_engagement"] = (
        summary["average_engagement"].round(2)
    )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    CHART_DIR.mkdir(parents=True, exist_ok=True)

    summary.to_csv(OUTPUT_FILE, index=False)

    plt.figure(figsize=(9, 5))
    plt.bar(
        summary["previous_purchases"].astype(str),
        summary["purchase_rate_percent"],
    )
    plt.title("Customer Purchase Rate by Purchase History")
    plt.xlabel("Previous Purchases")
    plt.ylabel("Purchase Rate (%)")
    plt.ylim(0, 100)
    plt.tight_layout()
    plt.savefig(CHART_FILE)
    plt.close()

    print("Customer pattern analysis completed successfully!")
    print(f"Total customers analyzed: {len(df)}")
    print(f"Report saved to: {OUTPUT_FILE}")
    print(f"Chart saved to: {CHART_FILE}")

    return summary


if __name__ == "__main__":
    analyze_customer_patterns()


