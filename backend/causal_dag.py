"""Week 1 (Member 2): causal graph for EconoCausal using DoWhy.

Causal story for data/customers.csv
  - Confounders (affect BOTH who gets a discount and who buys):
        previous_purchases, engagement
  - Treatment: discount (0/1)
  - Outcome:   purchase (0/1)

Discounts were not handed out at random. They depend on previous_purchases
and engagement, which also drive purchasing. That is confounding, so the
simple "discounted vs not discounted" comparison is biased.

Run from the repo root:  python backend/causal_dag.py
"""
from pathlib import Path

import pandas as pd
from dowhy import CausalModel

ROOT = Path(__file__).resolve().parent.parent
df = pd.read_csv(ROOT / "data" / "customers.csv")

CONFOUNDERS = ["previous_purchases", "engagement"]

model = CausalModel(
    data=df,
    treatment="discount",
    outcome="purchase",
    common_causes=CONFOUNDERS,
)

# Save a picture of the DAG for the report and viva (needs graphviz; optional)
try:
    model.view_model(layout="dot", file_name=str(ROOT / "backend" / "causal_dag"))
    print("DAG image saved to backend/causal_dag.png")
except Exception as exc:  # graphviz missing is fine
    print("Could not draw the DAG image:", exc)

# Step 1: identify what we must adjust for
estimand = model.identify_effect(proceed_when_unidentifiable=True)
print(estimand)

# Step 2: compare the naive difference with an adjusted estimate
naive = (
    df[df.discount == 1].purchase.mean() - df[df.discount == 0].purchase.mean()
)
print(f"\nNaive discounted-vs-not difference: {naive:+.3f}")

estimate = model.estimate_effect(
    estimand, method_name="backdoor.linear_regression"
)
print(f"Adjusted effect (linear regression, controls for confounders): "
      f"{estimate.value:+.3f}")
print("\nIf the two numbers differ, confounding is biasing the naive result.")
