from pathlib import Path

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "customers.csv"
REPORT_DIR = BASE_DIR / "reports"
CHART_DIR = REPORT_DIR / "charts"

OUTPUT_FILE = REPORT_DIR / "purchase_trend_analysis.csv"
CHART_FILE = CHART_DIR / "purchase_trend_by_history.png"


def analyze_purchase_trends():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

    df = pd.read_csv(DATA_FILE)

    required_columns = [
        "customer_id",
        "previous_purchases",
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
        raise ValueError("Customer dataset is empty.")

    df["previous_purchases"] = pd.to_numeric(
        df["previous_purchases"], errors="raise"
    )

    df["purchase"] = pd.to_numeric(
        df["purchase"], errors="raise"
    )

    if df[required_columns].isna().any().any():
        raise ValueError("Required columns contain missing values.")

    if not df["previous_purchases"].ge(0).all():
        raise ValueError(
            "Previous purchases must be non-negative."
        )

    if not df["previous_purchases"].mod(1).eq(0).all():
        raise ValueError(
            "Previous purchases must be whole numbers."
        )

    if not df["purchase"].isin([0, 1]).all():
        raise ValueError("Purchase values must be 0 or 1.")

    summary = (
        df.groupby("previous_purchases")
        .agg(
            customer_count=("customer_id", "count"),
            total_purchases=("purchase", "sum"),
            purchase_rate=("purchase", "mean"),
        )
        .reset_index()
    )

    summary["purchase_rate_percent"] = (
        summary["purchase_rate"] * 100
    ).round(2)

    summary = summary.drop(columns=["purchase_rate"])

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    CHART_DIR.mkdir(parents=True, exist_ok=True)

    summary.to_csv(OUTPUT_FILE, index=False)

    plt.figure(figsize=(9, 5))
    plt.plot(
        summary["previous_purchases"],
        summary["purchase_rate_percent"],
        marker="o",
    )
    plt.title("Purchase Rate by Previous Purchase Count")
    plt.xlabel("Number of Previous Purchases")
    plt.ylabel("Purchase Rate (%)")
    plt.ylim(0, 100)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(CHART_FILE)
    plt.close()

    print("Purchase trend analysis completed successfully!")
    print(f"CSV file: {OUTPUT_FILE}")
    print(f"Chart file: {CHART_FILE}")

    return summary


if __name__ == "__main__":
    analyze_purchase_trends()