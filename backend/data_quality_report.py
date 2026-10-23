
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "customers.csv"
REPORT_DIR = BASE_DIR / "reports"

OUTPUT_FILE = REPORT_DIR / "data_quality_report.csv"
SUMMARY_FILE = REPORT_DIR / "data_quality_summary.md"


def generate_data_quality_report():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

    df = pd.read_csv(DATA_FILE)

    if df.empty:
        raise ValueError("Customer dataset is empty.")

    required_columns = [
        "customer_id",
        "previous_purchases",
        "engagement",
        "discount",
        "purchase",
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    checks = []

    checks.append({
        "check": "Total customer records",
        "issue_count": len(df),
        "status": "INFO",
    })

    checks.append({
        "check": "Missing values",
        "issue_count": int(df.isna().sum().sum()),
        "status": "PASS" if not df.isna().any().any() else "CHECK",
    })

    duplicate_ids = int(df["customer_id"].duplicated().sum())

    checks.append({
        "check": "Duplicate customer IDs",
        "issue_count": duplicate_ids,
        "status": "PASS" if duplicate_ids == 0 else "CHECK",
    })

    for column in [
        "previous_purchases",
        "engagement",
        "discount",
        "purchase",
    ]:
        converted = pd.to_numeric(df[column], errors="coerce")
        invalid_count = int(converted.isna().sum())

        checks.append({
            "check": f"Invalid numeric values: {column}",
            "issue_count": invalid_count,
            "status": "PASS" if invalid_count == 0 else "CHECK",
        })

    purchase_values = pd.to_numeric(df["purchase"], errors="coerce")
    invalid_purchase_count = int(
        (~purchase_values.isin([0, 1])).sum()
    )

    checks.append({
        "check": "Invalid purchase values (expected 0 or 1)",
        "issue_count": invalid_purchase_count,
        "status": "PASS" if invalid_purchase_count == 0 else "CHECK",
    })

    discount_values = pd.to_numeric(df["discount"], errors="coerce")
    invalid_discount_count = int(
        (~discount_values.isin([0, 1])).sum()
    )

    checks.append({
        "check": "Invalid discount values (expected 0 or 1)",
        "issue_count": invalid_discount_count,
        "status": "PASS" if invalid_discount_count == 0 else "CHECK",
    })

    report = pd.DataFrame(checks)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report.to_csv(OUTPUT_FILE, index=False)

    summary_lines = [
        "# Customer Data Quality Report",
        "",
        f"- Total records: {len(df)}",
        f"- Total columns: {len(df.columns)}",
        f"- Duplicate customer IDs: {duplicate_ids}",
        f"- Missing cells: {int(df.isna().sum().sum())}",
        "",
        "## Validation Checks",
        "",
        "| Check | Issue Count | Status |",
        "|---|---:|---|",
    ]

    for _, row in report.iterrows():
        summary_lines.append(
            f"| {row['check']} | {row['issue_count']} | {row['status']} |"
        )

    SUMMARY_FILE.write_text(
        "\n".join(summary_lines) + "\n",
        encoding="utf-8",
    )

    print("Data quality report generated successfully!")
    print(f"Records checked: {len(df)}")
    print(f"CSV report: {OUTPUT_FILE}")
    print(f"Summary report: {SUMMARY_FILE}")
    print(report.to_string(index=False))

    return report


if __name__ == "__main__":
    generate_data_quality_report()

