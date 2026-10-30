"""Customer data analysis and reporting for EconoCasual."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "customers.csv"
REPORT_DIR = BASE_DIR / "reports"

REQUIRED_COLUMNS = [
    "customer_id",
    "previous_purchases",
    "engagement",
    "discount",
    "purchase",
]

NUMERIC_COLUMNS = [
    "previous_purchases",
    "engagement",
    "discount",
    "purchase",
]


def load_customer_data(file_path=DATA_FILE):
    """Load customer data and check required columns."""

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Dataset not found: {file_path}")

    df = pd.read_csv(file_path)

    if df.empty:
        raise ValueError("Customer dataset is empty.")

    missing = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="raise")

    return df


def validate_customer_data(df):
    """Validate customer records and allowed values."""

    missing = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if df.empty:
        raise ValueError("Customer dataset is empty.")

    if df[REQUIRED_COLUMNS].isnull().any().any():
        raise ValueError("Required columns cannot contain missing values.")

    if df["customer_id"].duplicated().any():
        raise ValueError("Duplicate customer IDs found.")

    if not df["purchase"].isin([0, 1]).all():
        raise ValueError("Purchase values must be 0 or 1.")

    if not df["discount"].isin([0, 1]).all():
        raise ValueError("Discount values must be 0 or 1.")

    if not df["engagement"].between(1, 10).all():
        raise ValueError("Engagement values must be between 1 and 10.")

    if (df["previous_purchases"] < 0).any():
        raise ValueError("Previous purchases cannot be negative.")

    return True


def create_customer_segments(df):
    """Group customers using purchase history and engagement."""

    result = df.copy()

    purchase_median = result["previous_purchases"].median()
    engagement_median = result["engagement"].median()

    def classify(row):
        if (
            row["previous_purchases"] >= purchase_median
            and row["engagement"] >= engagement_median
        ):
            return "High-Value Customers"

        if row["previous_purchases"] >= purchase_median:
            return "Loyal Customers"

        if row["engagement"] >= engagement_median:
            return "Highly Engaged Customers"

        return "Customers Needing Attention"

    result["customer_segment"] = result.apply(classify, axis=1)

    return result


def create_risk_classification(df):
    """Classify customers by attention level."""

    result = df.copy()

    purchase_median = result["previous_purchases"].median()
    engagement_median = result["engagement"].median()

    def identify_risk(row):
        low_engagement = row["engagement"] < engagement_median
        low_history = row["previous_purchases"] < purchase_median

        if low_engagement and low_history:
            return "High Attention Needed"

        if low_engagement or low_history:
            return "Moderate Attention Needed"

        return "Low Attention Needed"

    result["customer_risk"] = result.apply(
        identify_risk, axis=1
    )

    return result


def create_loyalty_classification(df):
    """Classify customers by previous purchases."""

    result = df.copy()

    def classify(row):
        if row["previous_purchases"] >= 7:
            return "Highly Loyal"

        if row["previous_purchases"] >= 4:
            return "Moderately Loyal"

        return "New or Occasional"

    result["loyalty_level"] = result.apply(
        classify, axis=1
    )

    return result


def create_summaries(df):
    """Generate customer behavior summaries."""

    segment_summary = (
        df.groupby("customer_segment")
        .agg(
            customer_count=("customer_id", "count"),
            total_purchases=("purchase", "sum"),
            purchase_rate=("purchase", "mean"),
        )
        .reset_index()
    )
    segment_summary["purchase_rate"] *= 100

    risk_summary = (
        df.groupby("customer_risk")
        .agg(
            customer_count=("customer_id", "count"),
            purchase_rate=("purchase", "mean"),
        )
        .reset_index()
    )
    risk_summary["purchase_rate"] *= 100

    loyalty_summary = (
        df.groupby("loyalty_level")
        .agg(
            customer_count=("customer_id", "count"),
            purchase_rate=("purchase", "mean"),
        )
        .reset_index()
    )
    loyalty_summary["purchase_rate"] *= 100

    engagement_summary = (
        df.groupby("engagement")
        .agg(
            total_customers=("customer_id", "count"),
            purchases=("purchase", "sum"),
            purchase_rate=("purchase", "mean"),
        )
        .reset_index()
    )
    engagement_summary["purchase_rate"] *= 100

    discount_summary = (
        df.groupby("discount")["purchase"]
        .mean()
        .mul(100)
        .reset_index(name="purchase_rate")
    )

    return {
        "segment_summary": segment_summary,
        "risk_summary": risk_summary,
        "loyalty_summary": loyalty_summary,
        "engagement_summary": engagement_summary,
        "discount_summary": discount_summary,
    }


def create_correlation_matrix(df):
    """Calculate correlations between customer behavior variables."""

    columns = [
        "previous_purchases",
        "engagement",
        "discount",
        "purchase",
    ]

    return df[columns].corr()


def save_charts(summaries, output_dir):
    """Save charts without opening interactive windows."""

    output_dir.mkdir(parents=True, exist_ok=True)

    charts = [
        (
            "customer_segment_purchase_rate.png",
            summaries["segment_summary"],
            "customer_segment",
            "Purchase Rate by Customer Segment",
            "Customer Segment",
        ),
        (
            "engagement_purchase_rate.png",
            summaries["engagement_summary"],
            "engagement",
            "Purchase Rate by Engagement",
            "Engagement",
        ),
        (
            "discount_purchase_rate.png",
            summaries["discount_summary"],
            "discount",
            "Purchase Rate by Discount",
            "Discount",
        ),
    ]

    for filename, data, x_col, title, xlabel in charts:
        plt.figure(figsize=(8, 5))
        plt.bar(
            data[x_col].astype(str),
            data["purchase_rate"],
        )

        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel("Purchase Rate (%)")
        plt.xticks(rotation=20, ha="right")
        plt.tight_layout()
        plt.savefig(output_dir / filename)
        plt.close()


def run_analysis(file_path=DATA_FILE, output_dir=REPORT_DIR):
    """Run the complete customer analysis and export reports."""

    output_dir = Path(output_dir)

    df = load_customer_data(file_path)
    validate_customer_data(df)

    df = create_customer_segments(df)
    df = create_risk_classification(df)
    df = create_loyalty_classification(df)

    summaries = create_summaries(df)
    correlation = create_correlation_matrix(df)

    output_dir.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_dir / "customer_insights.csv", index=False)
    correlation.to_csv(output_dir / "correlation_matrix.csv")

    for name, summary in summaries.items():
        summary.to_csv(output_dir / f"{name}.csv", index=False)

    save_charts(summaries, output_dir)

    results = {
        "total_customers": len(df),
        "total_purchases": int(df["purchase"].sum()),
        "total_non_purchases": int((df["purchase"] == 0).sum()),
        "purchase_rate": float(df["purchase"].mean() * 100),
        "missing_values": int(df.isnull().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "buyers": int((df["purchase"] == 1).sum()),
        "non_buyers": int((df["purchase"] == 0).sum()),
        "segment_summary": summaries["segment_summary"],
        "risk_summary": summaries["risk_summary"],
        "loyalty_summary": summaries["loyalty_summary"],
        "correlation_matrix": correlation,
    }

    print("\n========== ECONOCASUAL DATA ANALYSIS ==========")
    print(f"Total customers: {results['total_customers']}")
    print(f"Total purchases: {results['total_purchases']}")
    print(f"Non-purchases: {results['total_non_purchases']}")
    print(f"Overall purchase rate: {results['purchase_rate']:.2f}%")
    print(f"Missing values: {results['missing_values']}")
    print(f"Duplicate rows: {results['duplicate_rows']}")

    print("\nCustomer Segment Summary:")
    print(summaries["segment_summary"].round(2).to_string(index=False))

    print("\nCustomer Risk Summary:")
    print(summaries["risk_summary"].round(2).to_string(index=False))

    print("\nCustomer Loyalty Summary:")
    print(summaries["loyalty_summary"].round(2).to_string(index=False))

    print("\nCorrelation Matrix:")
    print(correlation.round(2))

    print(f"\nReports saved to: {output_dir}")
    print("Original customers.csv remains unchanged.")
    print("===============================================")

    return results


if __name__ == "__main__":
    run_analysis()