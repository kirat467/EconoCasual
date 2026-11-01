from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "reports" / "customer_segments.csv"
OUTPUT_DIR = BASE_DIR / "reports" / "charts"

REQUIRED_COLUMNS = [
    "engagement_segment",
    "purchase_history_segment",
    "purchase",
]


def load_segment_data(file_path=DATA_FILE):
    """Load customer segmentation data from a CSV file."""
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Customer segments file not found: {file_path}. "
            "Run backend/customer_segments.py first."
        )

    return pd.read_csv(file_path)


def validate_segment_data(df):
    """Validate the columns and purchase values needed for visualization."""
    missing = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    if df.empty:
        raise ValueError("Customer segments dataset is empty.")

    if df[REQUIRED_COLUMNS].isnull().any().any():
        raise ValueError("Required columns contain missing values.")

    purchase_values = pd.to_numeric(df["purchase"], errors="coerce")

    if purchase_values.isna().any():
        raise ValueError("Purchase column contains non-numeric values.")

    if not purchase_values.isin([0, 1]).all():
        raise ValueError("Purchase column must contain only 0 and 1.")

    return True


def create_visualizations(file_path=DATA_FILE, output_dir=OUTPUT_DIR):
    """Create and save three customer segmentation charts."""
    df = load_segment_data(file_path)
    validate_segment_data(df)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df["purchase"] = pd.to_numeric(df["purchase"])

    chart_paths = []

    # Graph 1: Number of customers in each engagement segment.
    engagement_counts = df["engagement_segment"].value_counts()

    plt.figure(figsize=(8, 5))
    engagement_counts.plot(kind="bar")
    plt.title("Customers by Engagement Segment")
    plt.xlabel("Engagement Segment")
    plt.ylabel("Number of Customers")
    plt.xticks(rotation=0)
    plt.tight_layout()

    chart_path = output_dir / "engagement_segments.png"
    plt.savefig(chart_path)
    plt.close()
    chart_paths.append(chart_path)

    # Graph 2: Purchase rate by engagement segment.
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

    chart_path = output_dir / "purchase_rate_by_engagement.png"
    plt.savefig(chart_path)
    plt.close()
    chart_paths.append(chart_path)

    # Graph 3: Purchase rate by previous purchase history.
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

    chart_path = output_dir / "purchase_rate_by_history.png"
    plt.savefig(chart_path)
    plt.close()
    chart_paths.append(chart_path)

    print("Customer segment visualizations created successfully!")
    print(f"Charts saved in: {output_dir}")

    for path in chart_paths:
        print(f"- {path.name}")

    return chart_paths


if __name__ == "__main__":
    try:
        create_visualizations()
    except (FileNotFoundError, ValueError) as error:
        print(f"Visualization error: {error}")