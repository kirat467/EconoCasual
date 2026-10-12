"""Richer synthetic data for EconoCausal (Week 2, Member 2).

Why this exists
  The team's data/customers.csv has two covariates, a binary discount and one
  uniform effect, so there is nothing for a heterogeneous-effect (CATE) model to
  find. This generator keeps the same column names where possible and adds:
    - a discount LEVEL (0 / 10 / 20 dollars)
    - extra covariates (price_sensitivity, age)
    - confounded assignment (same story as the team data)
    - heterogeneous effects, including NEGATIVE ones ("Sleeping Dogs")
    - the TRUE individual effect, so we can check the model against ground truth

Output: data/customers_causal.csv  (does NOT overwrite the team's customers.csv)
Run from the repo root:  python backend/generate_causal_data.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


def generate(n=5000, seed=42):
    rng = np.random.default_rng(seed)

    previous_purchases = rng.integers(0, 10, n)
    engagement = rng.integers(1, 11, n)
    price_sensitivity = rng.beta(2, 3, n)          # 0..1
    age = rng.integers(18, 70, n)

    # Baseline purchase propensity with NO discount
    base_logit = (
        -1.5
        + 0.22 * previous_purchases
        + 0.12 * engagement
        - 0.01 * (age - 40)
    )

    # Confounded assignment: discounts go to low-history, high-engagement
    # customers (same direction as the team's customers.csv)
    assign_logit = 0.3 - 0.20 * previous_purchases + 0.10 * engagement
    treated = rng.binomial(1, sigmoid(assign_logit))
    p_big = sigmoid(0.4 - 0.15 * previous_purchases)   # bigger coupons to low-history
    big = rng.binomial(1, p_big)
    discount = treated * np.where(big == 1, 20, 10)

    # TRUE effect per dollar on the logit scale. Heterogeneous:
    #   - price-sensitive customers respond strongly (Persuadables)
    #   - low price sensitivity -> negative effect (Sleeping Dogs)
    #   - highly engaged customers would buy anyway (smaller effect)
    effect_per_dollar = 0.15 * (price_sensitivity - 0.25) * (1.3 - engagement / 10)

    logit = base_logit + effect_per_dollar * discount
    purchase = rng.binomial(1, sigmoid(logit))

    # Ground-truth individual effect of a $10 discount (probability scale)
    true_ite_10 = sigmoid(base_logit + effect_per_dollar * 10) - sigmoid(base_logit)

    return pd.DataFrame({
        "customer_id": np.arange(1, n + 1),
        "previous_purchases": previous_purchases,
        "engagement": engagement,
        "price_sensitivity": price_sensitivity.round(4),
        "age": age,
        "discount": discount,                 # dollars: 0, 10 or 20
        "purchase": purchase,
        "true_ite_10": true_ite_10.round(5),  # validation only; not a model input
    })


if __name__ == "__main__":
    df = generate()
    out = ROOT / "data" / "customers_causal.csv"
    out.parent.mkdir(exist_ok=True)
    df.to_csv(out, index=False)

    print(f"Saved {len(df)} rows to {out.relative_to(ROOT)}")
    print("\nDiscount level counts:\n", df.discount.value_counts().sort_index().to_string())
    print("\nPurchase rate by discount level:\n",
          df.groupby("discount").purchase.mean().round(3).to_string())
    naive = (df[df.discount > 0].purchase.mean() - df[df.discount == 0].purchase.mean())
    print(f"\nNaive (any discount vs none): {naive:+.3f}")
    print(f"True mean effect of a $10 discount: {df.true_ite_10.mean():+.3f}")
    print("\nTrue-effect segments for a $10 discount:")
    seg = pd.cut(df.true_ite_10, [-1, -0.01, 0.01, 1],
                 labels=["Sleeping Dog (<-0.01)", "Near zero", "Persuadable (>0.01)"])
    print((seg.value_counts(normalize=True).sort_index() * 100).round(1).astype(str).add("%").to_string())
