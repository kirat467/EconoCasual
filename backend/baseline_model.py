"""Week 1 (Member 2): baseline purchase-prediction model.

This is the "ordinary ML" baseline. It predicts WHO WILL BUY, which is not the
same as WHO BUYS BECAUSE OF A DISCOUNT. Later weeks add Double ML (EconML) to
estimate the causal effect, and this baseline is what we compare against.

Run from the repo root:  python backend/baseline_model.py
"""
from pathlib import Path

import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent.parent
df = pd.read_csv(ROOT / "data" / "customers.csv")

FEATURES = ["previous_purchases", "engagement", "discount"]

train, test = train_test_split(df, test_size=0.25, random_state=0)

model = GradientBoostingClassifier(random_state=0)
model.fit(train[FEATURES], train["purchase"])

auc = roc_auc_score(test["purchase"], model.predict_proba(test[FEATURES])[:, 1])
print(f"Baseline purchase-prediction AUC: {auc:.3f}")

# Crude 'uplift' from the baseline: predict with discount=1 minus discount=0
with_discount = test.assign(discount=1)
without_discount = test.assign(discount=0)
uplift = (
    model.predict_proba(with_discount[FEATURES])[:, 1]
    - model.predict_proba(without_discount[FEATURES])[:, 1]
)
print(f"Baseline average estimated uplift from a discount: {uplift.mean():+.3f}")

naive = (
    df[df.discount == 1].purchase.mean() - df[df.discount == 0].purchase.mean()
)
print(f"Naive discounted-vs-not purchase-rate difference: {naive:+.3f}")

print(
    "\nTakeaway: a good predictor can still be a poor guide for targeting "
    "discounts. Double ML (Week 2) estimates the causal effect properly."
)
