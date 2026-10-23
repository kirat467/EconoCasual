from pathlib import Path

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "customers.csv"
REPORT_DIR = BASE_DIR / "reports"
CHART_DIR = REPORT_DIR / "charts"

OUTPUT_FILE = REPORT_DIR / "discount_purchase_analysis.csv"
CHART_FILE = CHART_DIR / "discount_purchase_rate.png"


def analyze_discount_purchases():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

    df = pd.read_csv(DATA_FILE)

    required_columns = ["customer_id", "discount", "purchase"]
    missing = [column for column in required_columns if column not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if df.empty:
        raise ValueError("Customer dataset is empty.")

    df["discount"] = pd.to_numeric(df["discount"], errors="raise")
    df["purchase"] = pd.to_numeric(df["purchase"], errors="raise")

    if df["discount"].isna().any() or df["purchase"].isna().any():
        raise ValueError("Discount and purchase cannot contain missing values.")

    if not df["purchase"].isin([0, 1]).all():
        raise ValueError("Purchase values must be 0 or 1.")

    if not df["discount"].isin([0, 1]).all():
        raise ValueError("Discount values must be 0 or 1.")

    summary = (
        df.groupby("discount")
        .agg(
            customer_count=("customer_id", "count"),
            total_purchases=("purchase", "sum"),
            purchase_rate=("purchase", "mean"),
        )
        .reset_index()
    )

    summary["non_purchases"] = (
        summary["customer_count"] - summary["total_purchases"]
    )

    summary["purchase_rate_percent"] = (
        summary["purchase_rate"] * 100
    ).round(2)

    summary = summary.drop(columns=["purchase_rate"])
    summary["discount_group"] = summary["discount"].map({
        0: "No Discount",
        1: "Discount",
    })

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    CHART_DIR.mkdir(parents=True, exist_ok=True)

    summary.to_csv(OUTPUT_FILE, index=False)

    plt.figure(figsize=(8, 5))
    plt.bar(
        summary["discount_group"],
        summary["purchase_rate_percent"],
    )
    plt.title("Purchase Rate: Discount vs No Discount")
    plt.xlabel("Customer Group")
    plt.ylabel("Purchase Rate (%)")
    plt.ylim(0, 100)
    plt.tight_layout()
    plt.savefig(CHART_FILE)
    plt.close()

    print("Discount purchase analysis completed successfully!")
    print(f"Customers analyzed: {len(df)}")
    print(f"Report saved: {OUTPUT_FILE}")
    print(f"Chart saved: {CHART_FILE}")
    print(summary.to_string(index=False))

    return summary


if __name__ == "__main__":
    analyze_discount_purchases()