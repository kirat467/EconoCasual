from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "reports" / "customer_segments.csv"
OUTPUT_DIR = BASE_DIR / "reports"
CHART_DIR = OUTPUT_DIR / "charts"
COMPARISON_FILE = OUTPUT_DIR / "segment_comparison.csv"

REQUIRED_COLUMNS = [
    "engagement_segment",
    "purchase_history_segment",
    "purchase",
    "customer_id",
]


def load_segment_data(file_path=DATA_FILE):
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Customer segments file not found: {file_path}"
        )

    return pd.read_csv(file_path)


def validate_segment_data(df):
    missing = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    if df.empty:
        raise ValueError("Customer segment dataset is empty.")

    if df["customer_id"].isnull().any():
        raise ValueError("Customer IDs contain missing values.")

    if df["customer_id"].duplicated().any():
        raise ValueError("Duplicate customer IDs found.")

    purchase = pd.to_numeric(df["purchase"], errors="coerce")

    if purchase.isnull().any():
        raise ValueError("Purchase contains non-numeric values.")

    if not purchase.isin([0, 1]).all():
        raise ValueError("Purchase values must be 0 or 1.")

    if df["engagement_segment"].isnull().any():
        raise ValueError("Engagement segment contains missing values.")

    if df["purchase_history_segment"].isnull().any():
        raise ValueError(
            "Purchase history segment contains missing values."
        )

    return True


def create_segment_comparison(df):
    validate_segment_data(df)

    df = df.copy()
    df["purchase"] = pd.to_numeric(df["purchase"])

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

    return comparison


def save_comparison_charts(df, output_dir=CHART_DIR):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    chart_paths = []

    engagement = (
        df.groupby("engagement_segment", observed=False)["purchase"]
        .mean()
        .mul(100)
    )

    engagement_path = output_dir / "segment_comparison_engagement.png"

    plt.figure(figsize=(8, 5))
    engagement.plot(kind="bar")
    plt.title("Purchase Rate Comparison by Engagement")
    plt.xlabel("Engagement Segment")
    plt.ylabel("Purchase Rate (%)")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(engagement_path)
    plt.close()

    chart_paths.append(engagement_path)

    history = (
        df.groupby(
            "purchase_history_segment",
            observed=False,
        )["purchase"]
        .mean()
        .mul(100)
    )

    history_path = output_dir / "segment_comparison_history.png"

    plt.figure(figsize=(8, 5))
    history.plot(kind="bar")
    plt.title("Purchase Rate Comparison by Purchase History")
    plt.xlabel("Purchase History Segment")
    plt.ylabel("Purchase Rate (%)")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(history_path)
    plt.close()

    chart_paths.append(history_path)

    return chart_paths


def compare_segments(
    file_path=DATA_FILE,
    output_file=COMPARISON_FILE,
    chart_dir=CHART_DIR,
):
    df = load_segment_data(file_path)
    validate_segment_data(df)

    comparison = create_segment_comparison(df)

    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    comparison.to_csv(output_file, index=False)

    chart_paths = save_comparison_charts(df, chart_dir)

    print("Segment comparison completed successfully!")
    print(f"Customers analyzed: {len(df)}")
    print(f"Comparison saved to: {output_file}")
    print(f"Charts saved in: {chart_dir}")
    print("\nSegment comparison results:")
    print(comparison.to_string(index=False))

    return {
        "customers_analyzed": len(df),
        "comparison": comparison,
        "comparison_file": output_file,
        "chart_paths": chart_paths,
    }


if __name__ == "__main__":
    compare_segments()
