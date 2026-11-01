from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "customers.csv"

REQUIRED_COLUMNS = [
    "customer_id",
    "previous_purchases",
    "engagement",
    "discount",
    "purchase",
]


def generate_dataset(n=1000, random_state=42, output_file=DATA_FILE):
    """Generate and save reproducible customer sample data."""

    if not isinstance(n, int) or isinstance(n, bool) or n <= 0:
        raise ValueError("Number of customers must be a positive integer.")

    if not isinstance(random_state, int) or isinstance(random_state, bool):
        raise ValueError("Random state must be an integer.")

    rng = np.random.default_rng(random_state)

    previous_purchases = rng.integers(0, 10, n)
    engagement = rng.integers(1, 11, n)

    discount_probability = 1 / (
        1 + np.exp(
            -(0.5 - 0.15 * previous_purchases
              + 0.10 * engagement)
        )
    )

    discount = rng.binomial(1, discount_probability)

    purchase_probability = 1 / (
        1 + np.exp(
            -(-2
              + 0.25 * previous_purchases
              + 0.15 * engagement
              + 0.8 * discount)
        )
    )

    purchase = rng.binomial(1, purchase_probability)

    df = pd.DataFrame({
        "customer_id": range(1, n + 1),
        "previous_purchases": previous_purchases,
        "engagement": engagement,
        "discount": discount,
        "purchase": purchase,
    })

    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)

    return df


def validate_dataset(df):
    """Validate generated customer data."""

    errors = []

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        errors.append(f"Missing columns: {missing_columns}")
        return errors

    if df.empty:
        errors.append("Dataset is empty.")
        return errors

    if df[REQUIRED_COLUMNS].isnull().any().any():
        errors.append("Dataset contains missing values.")

    if df["customer_id"].duplicated().any():
        errors.append("Duplicate customer IDs found.")

    for column in ["previous_purchases", "engagement",
                   "discount", "purchase"]:
        converted = pd.to_numeric(df[column], errors="coerce")

        if converted.isna().any():
            errors.append(f"Column '{column}' contains invalid values.")
            continue

        if not np.isfinite(converted.to_numpy(dtype=float)).all():
            errors.append(f"Column '{column}' contains non-finite values.")

    if not errors:
        if not df["previous_purchases"].between(0, 9).all():
            errors.append("Previous purchases must be between 0 and 9.")

        if not df["engagement"].between(1, 10).all():
            errors.append("Engagement must be between 1 and 10.")

        for column in ["discount", "purchase"]:
            if not df[column].isin([0, 1]).all():
                errors.append(f"Column '{column}' must contain only 0 or 1.")

    return errors


def run_analysis(n=1000, random_state=42, output_file=DATA_FILE):
    """Generate, validate, and display dataset information."""

    df = generate_dataset(
        n=n,
        random_state=random_state,
        output_file=output_file,
    )

    errors = validate_dataset(df)

    if errors:
        raise ValueError("; ".join(errors))

    print("\n===== ECONOCASUAL DATASET GENERATION =====")
    print("Dataset created successfully!")
    print(f"Total customers: {len(df)}")
    print(f"Total columns: {len(df.columns)}")
    print(f"Total purchases: {int(df['purchase'].sum())}")
    print(f"Overall purchase rate: {df['purchase'].mean():.2%}")

    print("\nFirst five customers:")
    print(df.head().to_string(index=False))

    print("\nPurchase rate by discount:")
    print(df.groupby("discount")["purchase"].mean())

    print("\nMissing values:")
    print(df.isnull().sum())

    print("\nDuplicate rows:")
    print(df.duplicated().sum())

    print(f"\nDataset saved to: {output_file}")
    print("==========================================")

    return df


if __name__ == "__main__":
    run_analysis()