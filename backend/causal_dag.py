"""Causal DAG and adjusted discount-effect analysis for EconoCasual."""

from pathlib import Path

import pandas as pd
import statsmodels.api as sm
from dowhy import CausalModel


ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "customers.csv"

CONFOUNDERS = ["previous_purchases", "engagement"]
TREATMENT = "discount"
OUTCOME = "purchase"

REQUIRED_COLUMNS = CONFOUNDERS + [TREATMENT, OUTCOME]


def load_customer_data(file_path=DATA_FILE):
    """Load and validate customer data."""

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Dataset not found: {file_path}")

    df = pd.read_csv(file_path)

    missing = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    for column in REQUIRED_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    if df[REQUIRED_COLUMNS].isnull().any().any():
        raise ValueError("Required columns contain missing or invalid values.")

    for column in [TREATMENT, OUTCOME]:
        if not set(df[column].unique()).issubset({0, 1}):
            raise ValueError(f"{column} must contain only 0 and 1.")

    if df[TREATMENT].nunique() != 2:
        raise ValueError("Discount must contain both 0 and 1.")

    if df[OUTCOME].nunique() != 2:
        raise ValueError("Purchase must contain both 0 and 1.")

    return df


def calculate_naive_difference(df):
    """Calculate the unadjusted purchase-rate difference."""

    discounted = df.loc[df[TREATMENT] == 1, OUTCOME]
    not_discounted = df.loc[df[TREATMENT] == 0, OUTCOME]

    if discounted.empty or not_discounted.empty:
        raise ValueError("Both discount groups must contain customers.")

    return discounted.mean() - not_discounted.mean()


def identify_causal_effect(df):
    """Create the DoWhy model and identify the causal estimand."""

    model = CausalModel(
        data=df,
        treatment=TREATMENT,
        outcome=OUTCOME,
        common_causes=CONFOUNDERS,
    )

    estimand = model.identify_effect(
        proceed_when_unidentifiable=True
    )

    return model, estimand


def calculate_adjusted_effect(df):
    """Estimate the adjusted discount effect using OLS."""

    features = [TREATMENT] + CONFOUNDERS

    X = sm.add_constant(df[features], has_constant="add")
    y = df[OUTCOME]

    regression = sm.OLS(y, X).fit()

    adjusted_effect = regression.params[TREATMENT]

    return float(adjusted_effect), regression


def run_analysis():
    """Run the complete causal analysis."""

    df = load_customer_data()

    model, estimand = identify_causal_effect(df)

    print("Identified causal estimand:")
    print(estimand)

    # Generate the causal DAG image.
    try:
        model.view_model(
            layout="dot",
            file_name=str(ROOT / "backend" / "causal_dag"),
        )
        print("\nDAG image saved to backend/causal_dag.png")

    except Exception as exc:
        print("\nCould not draw DAG image:", exc)

    naive = calculate_naive_difference(df)

    adjusted, regression = calculate_adjusted_effect(df)

    print(f"\nNaive discounted-vs-not difference: {naive:+.3f}")

    print(
        "Adjusted effect (OLS controlling for confounders): "
        f"{adjusted:+.3f}"
    )

    print(
        "\nTakeaway: the naive comparison does not adjust for "
        "previous purchases and engagement. The adjusted estimate "
        "controls for these observed confounders."
    )

    return {
        "naive_difference": naive,
        "adjusted_effect": adjusted,
        "estimand": estimand,
        "regression": regression,
    }


if __name__ == "__main__":
    run_analysis()