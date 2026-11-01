from pathlib import Path

import pandas as pd


# Project directories.
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "customer_insights.csv"


def validate_customer_insights(file_path=DATA_FILE):
    """
    Validate the customer insights CSV file.

    Returns:
        Dictionary containing validation results.
    """

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Customer insights file not found: {file_path}"
        )

    df = pd.read_csv(file_path)

    errors = []

    # Check whether customer_id column exists.
    if "customer_id" not in df.columns:
        errors.append({
            "type": "missing_customer_id_column"
        })

        duplicate_ids = None

    else:
        duplicate_ids = int(
            df["customer_id"].duplicated().sum()
        )

        if duplicate_ids > 0:
            errors.append({
                "type": "duplicate_customer_ids",
                "count": duplicate_ids,
            })

    # Check missing values.
    missing_values = int(df.isnull().sum().sum())

    if missing_values > 0:
        errors.append({
            "type": "missing_values",
            "count": missing_values,
        })

    return {
        "file_exists": True,
        "total_rows": int(len(df)),
        "total_columns": int(len(df.columns)),
        "missing_values": missing_values,
        "duplicate_customer_ids": duplicate_ids,
        "is_valid": len(errors) == 0,
        "errors": errors,
    }


def run_validation(file_path=DATA_FILE):
    """Run validation and display a readable report."""

    result = validate_customer_insights(file_path)

    print("\n===== CUSTOMER INSIGHTS VALIDATION =====")

    print("File exists:", result["file_exists"])
    print("Total Rows:", result["total_rows"])
    print("Total Columns:", result["total_columns"])
    print("Missing Values:", result["missing_values"])
    print(
        "Duplicate Customer IDs:",
        result["duplicate_customer_ids"]
    )

    if result["is_valid"]:
        print("Validation Status: PASSED")
    else:
        print("Validation Status: FAILED")

        print("\nValidation Errors:")

        for error in result["errors"]:
            print(error)

    print("\nValidation completed!")
    print("========================================")

    return result


if __name__ == "__main__":
    try:
        run_validation()

    except FileNotFoundError as error:
        print(f"DATASET ERROR: {error}")

    except Exception as error:
        print(f"UNEXPECTED ERROR: {error}")