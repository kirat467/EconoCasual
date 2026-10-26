from pathlib import Path
import math
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_DIR / "data" / "customers.csv"

REQUIRED_COLUMNS = [
    "customer_id",
    "previous_purchases",
    "engagement",
    "discount",
    "purchase",
]

NUMERIC_COLUMNS = [
    "customer_id",
    "previous_purchases",
    "engagement",
    "discount",
    "purchase",
]


def validate_customer_data(df):
    errors = []

    # Check required columns
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        errors.append({
            "type": "missing_columns",
            "columns": missing_columns,
        })

        return {
            "is_valid": False,
            "total_rows": int(len(df)),
            "errors": errors,
        }

    # Check missing values
    missing_values = {
        column: int(count)
        for column, count in df[REQUIRED_COLUMNS].isnull().sum().items()
        if count > 0
    }

    if missing_values:
        errors.append({
            "type": "missing_values",
            "details": missing_values,
        })

    # Check numeric columns
    for column in NUMERIC_COLUMNS:
        converted = pd.to_numeric(df[column], errors="coerce")

        invalid_mask = converted.isna() & df[column].notna()

        if invalid_mask.any():
            errors.append({
                "type": "non_numeric_values",
                "column": column,
                "count": int(invalid_mask.sum()),
            })
            continue

        non_finite_mask = converted.notna() & ~converted.map(
            lambda value: math.isfinite(float(value))
        )

        if non_finite_mask.any():
            errors.append({
                "type": "non_finite_values",
                "column": column,
                "count": int(non_finite_mask.sum()),
            })

    # Check purchase values (must be 0 or 1)
    purchase_values = pd.to_numeric(
        df["purchase"],
        errors="coerce",
    )

    invalid_purchase = (
        purchase_values.isna()
        | ~purchase_values.isin([0, 1])
    )

    if invalid_purchase.any():
        errors.append({
            "type": "invalid_purchase_values",
            "count": int(invalid_purchase.sum()),
        })

    return {
        "is_valid": len(errors) == 0,
        "total_rows": int(len(df)),
        "errors": errors,
    }


def validate_dataset_file():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Customer dataset not found: {DATA_FILE}"
        )

    df = pd.read_csv(DATA_FILE)
    return validate_customer_data(df)


if __name__ == "__main__":
    try:
        result = validate_dataset_file()
        print("Customer Data Validation Result:")
        print(result)

        if result["is_valid"]:
            print("SUCCESS: Customer dataset is valid.")
        else:
            print("WARNING: Customer dataset contains validation errors.")

    except Exception as error:
        print(f"ERROR: {error}")