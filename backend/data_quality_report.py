from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "customers.csv"

REPORT_DIR = BASE_DIR / "reports"
OUTPUT_FILE = REPORT_DIR / "data_quality_report.csv"
SUMMARY_FILE = REPORT_DIR / "data_quality_summary.md"


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


def generate_data_quality_report():
    """Generate customer dataset quality checks and save reports."""

    # Check whether the dataset exists.
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

    # Read dataset and handle completely empty CSV files.
    try:
        df = pd.read_csv(DATA_FILE)
    except pd.errors.EmptyDataError:
        raise ValueError("Customer dataset is empty.")

    # Reject empty datasets.
    if df.empty:
        raise ValueError("Customer dataset is empty.")

    # Validate required columns.
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    checks = []

    # Total customer records.
    checks.append({
        "check": "Total customer records",
        "issue_count": int(len(df)),
        "status": "INFO",
    })

    # Missing values across the complete dataset.
    missing_count = int(df.isna().sum().sum())

    checks.append({
        "check": "Missing values",
        "issue_count": missing_count,
        "status": "PASS" if missing_count == 0 else "CHECK",
    })

    # Duplicate customer IDs.
    duplicate_ids = int(
        df["customer_id"].duplicated().sum()
    )

    checks.append({
        "check": "Duplicate customer IDs",
        "issue_count": duplicate_ids,
        "status": "PASS" if duplicate_ids == 0 else "CHECK",
    })

    # Validate numeric columns.
    converted_columns = {}

    for column in NUMERIC_COLUMNS:
        converted = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        converted_columns[column] = converted

        invalid_count = int(converted.isna().sum())

        checks.append({
            "check": f"Invalid numeric values: {column}",
            "issue_count": invalid_count,
            "status": "PASS" if invalid_count == 0 else "CHECK",
        })

    # Purchase values must be either 0 or 1.
    purchase_values = converted_columns["purchase"]

    invalid_purchase_count = int(
        (~purchase_values.isin([0, 1])).sum()
    )

    checks.append({
        "check": "Invalid purchase values (expected 0 or 1)",
        "issue_count": invalid_purchase_count,
        "status": (
            "PASS"
            if invalid_purchase_count == 0
            else "CHECK"
        ),
    })

    # Discount values must be either 0 or 1.
    discount_values = converted_columns["discount"]

    invalid_discount_count = int(
        (~discount_values.isin([0, 1])).sum()
    )

    checks.append({
        "check": "Invalid discount values (expected 0 or 1)",
        "issue_count": invalid_discount_count,
        "status": (
            "PASS"
            if invalid_discount_count == 0
            else "CHECK"
        ),
    })

    # Create the final report.
    report = pd.DataFrame(
        checks,
        columns=["check", "issue_count", "status"]
    )

    # Create report directory if it does not exist.
    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # Save CSV report.
    report.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # Generate Markdown summary.
    summary_lines = [
        "# Customer Data Quality Report",
        "",
        f"- Total records: {len(df)}",
        f"- Total columns: {len(df.columns)}",
        f"- Duplicate customer IDs: {duplicate_ids}",
        f"- Missing cells: {missing_count}",
        "",
        "## Validation Checks",
        "",
        "| Check | Issue Count | Status |",
        "|---|---:|---|",
    ]

    for _, row in report.iterrows():
        summary_lines.append(
            f"| {row['check']} | "
            f"{row['issue_count']} | "
            f"{row['status']} |"
        )

    SUMMARY_FILE.write_text(
        "\n".join(summary_lines) + "\n",
        encoding="utf-8"
    )

    print("Data quality report generated successfully!")
    print(f"Records checked: {len(df)}")
    print(f"CSV report: {OUTPUT_FILE}")
    print(f"Summary report: {SUMMARY_FILE}")
    print(report.to_string(index=False))

    return report


if __name__ == "__main__":
    generate_data_quality_report()