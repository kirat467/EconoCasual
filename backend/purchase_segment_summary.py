
from pathlib import Path

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "customers.csv"
REPORT_DIR = BASE_DIR / "reports"
CHART_DIR = REPORT_DIR / "charts"

OUTPUT_FILE = REPORT_DIR / "purchase_segment_summary.csv"
CHART_FILE = CHART_DIR / "purchase_segment_purchase_rate.png"


def generate_purchase_segment_summary():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

    df = pd.read_csv(DATA_FILE)

    required_columns = ["customer_id", "previous_purchases", "purchase"]
    missing = [column for column in required_columns if column not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if df.empty:
        raise ValueError("Customer dataset is empty.")

    df["previous_purchases"] = pd.to_numeric(
        df["previous_purchases"], errors="raise"
    )
    df["purchase"] = pd.to_numeric(df["purchase"], errors="raise")

    if df[["previous_purchases", "purchase"]].isna().any().any():
        raise ValueError("Required columns contain missing values.")

    if not df["purchase"].isin([0, 1]).all():
        raise ValueError("Purchase values must be 0 or 1.")

    df["purchase_segment"] = pd.cut(
        df["previous_purchases"],
        bins=[-float("inf"), 2, 5, float("inf")],
        labels=["Low", "Medium", "High"],
    )

    summary = (
        df.groupby("purchase_segment", observed=False)
        .agg(
            customer_count=("customer_id", "count"),
            total_purchases=("purchase", "sum"),
            average_previous_purchases=("previous_purchases", "mean"),
        )
        .reset_index()
    )

    summary["non_purchases"] = (
        summary["customer_count"] - summary["total_purchases"]
    )

    summary["purchase_rate_percent"] = (
        summary["total_purchases"]
        / summary["customer_count"].replace(0, float("nan"))
        * 100
    ).round(2)

    summary["average_previous_purchases"] = (
        summary["average_previous_purchases"].round(2)
    )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    CHART_DIR.mkdir(parents=True, exist_ok=True)

    summary.to_csv(OUTPUT_FILE, index=False)

    chart_data = summary.dropna(subset=["purchase_rate_percent"])

    plt.figure(figsize=(8, 5))
    plt.bar(
        chart_data["purchase_segment"].astype(str),
        chart_data["purchase_rate_percent"],
    )
    plt.title("Purchase Rate by Customer Purchase Segment")
    plt.xlabel("Purchase History Segment")
    plt.ylabel("Purchase Rate (%)")
    plt.ylim(0, 100)
    plt.tight_layout()
    plt.savefig(CHART_FILE)
    plt.close()

    print("Purchase segment summary generated successfully!")
    print(f"Report: {OUTPUT_FILE}")
    print(f"Chart: {CHART_FILE}")
    print(summary.to_string(index=False))

    return summary


if __name__ == "__main__":
    generate_purchase_segment_summary()

