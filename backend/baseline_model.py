"""Baseline purchase-prediction model.

Predicts which customers are likely to purchase.
This is a predictive model, not a causal treatment-effect model.
"""

from pathlib import Path

import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split


ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "customers.csv"

FEATURES = ["previous_purchases", "engagement", "discount"]
TARGET = "purchase"
REQUIRED_COLUMNS = FEATURES + [TARGET]


def load_customer_data(file_path=DATA_FILE):
    """Load and validate customer data."""

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Dataset not found: {file_path}")

    df = pd.read_csv(file_path)

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if df[REQUIRED_COLUMNS].isnull().any().any():
        raise ValueError("Required columns contain missing values.")

    for column in REQUIRED_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    if df[REQUIRED_COLUMNS].isnull().any().any():
        raise ValueError("Required columns must contain numeric values.")

    if not set(df[TARGET].unique()).issubset({0, 1}):
        raise ValueError("Purchase column must contain only 0 and 1.")

    if df[TARGET].nunique() != 2:
        raise ValueError("Purchase column must contain both classes: 0 and 1.")

    if (df[FEATURES] < 0).any().any():
        raise ValueError("Feature values cannot be negative.")

    return df


def train_baseline_model(df):
    """Train the baseline classifier and calculate its AUC."""

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if df[REQUIRED_COLUMNS].isnull().any().any():
        raise ValueError("Required columns contain missing values.")

    if df[TARGET].nunique() != 2:
        raise ValueError("Purchase target must contain both classes.")

    train, test = train_test_split(
        df,
        test_size=0.25,
        random_state=0,
        stratify=df[TARGET],
    )

    model = GradientBoostingClassifier(random_state=0)

    model.fit(train[FEATURES], train[TARGET])

    predictions = model.predict_proba(test[FEATURES])[:, 1]

    auc = roc_auc_score(test[TARGET], predictions)

    return model, test, auc


def calculate_naive_difference(df):
    """Calculate the observed purchase-rate difference."""

    discounted = df.loc[df["discount"] == 1, TARGET]
    not_discounted = df.loc[df["discount"] == 0, TARGET]

    if discounted.empty or not_discounted.empty:
        raise ValueError("Both discount groups must contain customers.")

    return discounted.mean() - not_discounted.mean()


def run_analysis():
    """Run the complete baseline analysis."""

    df = load_customer_data()

    model, test, auc = train_baseline_model(df)

    with_discount = test.assign(discount=1)
    without_discount = test.assign(discount=0)

    uplift = (
        model.predict_proba(with_discount[FEATURES])[:, 1]
        - model.predict_proba(without_discount[FEATURES])[:, 1]
    )

    naive = calculate_naive_difference(df)

    print(f"Baseline purchase-prediction AUC: {auc:.3f}")
    print(
        "Baseline average estimated uplift from a discount: "
        f"{uplift.mean():+.3f}"
    )
    print(f"Naive discounted-vs-not purchase-rate difference: {naive:+.3f}")

    print(
        "\nTakeaway: a good predictor can still be a poor guide for "
        "targeting discounts. Predictive association is not causal effect."
    )


if __name__ == "__main__":
    run_analysis()