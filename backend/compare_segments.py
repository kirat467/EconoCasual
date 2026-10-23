from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "reports" / "customer_segments.csv"
OUTPUT_DIR = BASE_DIR / "reports"
CHART_DIR = OUTPUT_DIR / "charts"

COMPARISON_FILE = OUTPUT_DIR / "segment_comparison.csv"


def compare_segments():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            "Customer segments file not found. "
            "Run backend/customer_segments.py first."
        )

    df = pd.read_csv(DATA_FILE)

    required_columns = [
        "engagement_segment",
        "purchase_history_segment",
        "purchase",
        "customer_id",
    ]

    missing = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    if df.empty:
        raise ValueError("Customer segment dataset is empty.")

    df["purchase"] = pd.to_numeric(df["purchase"], errors="raise")

    comparison = (
        df.groupby(
            ["engagement_segment", "purchase_history_segment"],
            observed=False,
        )
        .agg(
            customer_count=("customer_id", "count"),
            total_purchases=("purchase", "sum"),
            purchase_rate=("purchase", "mean"),
        )
        .reset_index()
    )

    comparison["purchase_rate_percent"] = (
        comparison["purchase_rate"] * 100
    ).round(2)

    comparison.drop(columns=["purchase_rate"], inplace=True)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CHART_DIR.mkdir(parents=True, exist_ok=True)

    comparison.to_csv(COMPARISON_FILE, index=False)

    # Plot purchase rates for engagement groups
    engagement_comparison = (
        df.groupby("engagement_segment", observed=False)["purchase"]
        .mean()
        .mul(100)
    )

    plt.figure(figsize=(8, 5))
    engagement_comparison.plot(kind="bar")
    plt.title("Purchase Rate Comparison by Engagement")
    plt.xlabel("Engagement Segment")
    plt.ylabel("Purchase Rate (%)")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(CHART_DIR / "segment_comparison_engagement.png")
    plt.close()

    # Plot purchase rates for purchase-history groups
    history_comparison = (
        df.groupby("purchase_history_segment", observed=False)["purchase"]
        .mean()
        .mul(100)
    )

    plt.figure(figsize=(8, 5))
    history_comparison.plot(kind="bar")
    plt.title("Purchase Rate Comparison by Purchase History")
    plt.xlabel("Purchase History Segment")
    plt.ylabel("Purchase Rate (%)")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(CHART_DIR / "segment_comparison_history.png")
    plt.close()

    print("Segment comparison completed successfully!")
    print(f"Customers analyzed: {len(df)}")
    print(f"Comparison saved to: {COMPARISON_FILE}")
    print(f"Charts saved in: {CHART_DIR}")
    print("\nSegment comparison results:")
    print(comparison.to_string(index=False))


if __name__ == "__main__":
    compare_segments()