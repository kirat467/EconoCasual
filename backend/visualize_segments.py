from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "reports" / "customer_segments.csv"
OUTPUT_DIR = BASE_DIR / "reports" / "charts"


def create_visualizations():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            "customer_segments.csv not found. "
            "Run backend/customer_segments.py first."
        )

    df = pd.read_csv(DATA_FILE)

    required_columns = [
        "engagement_segment",
        "purchase_history_segment",
        "purchase",
    ]

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Graph 1: Number of customers in each engagement segment
    engagement_counts = df["engagement_segment"].value_counts()

    plt.figure(figsize=(8, 5))
    engagement_counts.plot(kind="bar")
    plt.title("Customers by Engagement Segment")
    plt.xlabel("Engagement Segment")
    plt.ylabel("Number of Customers")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "engagement_segments.png")
    plt.close()

    # Graph 2: Purchase rate by engagement segment
    purchase_rates = (
        df.groupby("engagement_segment", observed=False)["purchase"]
        .mean()
        .mul(100)
    )

    plt.figure(figsize=(8, 5))
    purchase_rates.plot(kind="bar")
    plt.title("Purchase Rate by Engagement Segment")
    plt.xlabel("Engagement Segment")
    plt.ylabel("Purchase Rate (%)")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "purchase_rate_by_engagement.png")
    plt.close()

    # Graph 3: Purchase rate by previous purchase history
    history_rates = (
        df.groupby("purchase_history_segment", observed=False)["purchase"]
        .mean()
        .mul(100)
    )

    plt.figure(figsize=(8, 5))
    history_rates.plot(kind="bar")
    plt.title("Purchase Rate by Purchase History")
    plt.xlabel("Purchase History Segment")
    plt.ylabel("Purchase Rate (%)")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "purchase_rate_by_history.png")
    plt.close()

    print("Customer segment visualizations created successfully!")
    print(f"Charts saved in: {OUTPUT_DIR}")


if __name__ == "__main__":
    create_visualizations()