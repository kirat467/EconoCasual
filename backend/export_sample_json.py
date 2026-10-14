"""Export real model output as sample JSON for the frontend (Week 2, Member 2).

Member 3 can build the dashboard against these files before the API exists.
  docs/sample_ite.json          -> shape of  GET /api/ite
  docs/sample_uplift_curve.json -> shape of  GET /api/uplift-curve

Run from the repo root:  python backend/export_sample_json.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from econml.dml import LinearDML
from lightgbm import LGBMClassifier, LGBMRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PolynomialFeatures

ROOT = Path(__file__).resolve().parent.parent
FEATURES = ["previous_purchases", "engagement", "price_sensitivity", "age"]
DISCOUNT = 10
N_SAMPLE_CUSTOMERS = None   # None = export every held-out customer (the Mid Review needs "thousands")

# NumPy 2 renamed trapz -> trapezoid; support both
_trapezoid = getattr(np, "trapezoid", None) or np.trapz


def lgbm():
    return LGBMRegressor(n_estimators=200, learning_rate=0.05, num_leaves=8,
                         min_child_samples=30, random_state=0, verbose=-1)


def segment(ite, lo, hi, baseline):
    if lo > 0:
        return "persuadable"
    if hi < 0:
        return "sleeping_dog"
    return "sure_thing" if baseline >= 0.5 else "lost_cause"


def qini_curve(score, treated, outcome, points=21):
    """Qini curve: cumulative extra purchases caused, targeting best-ranked first."""
    order = np.argsort(-score)
    t, y = treated[order], outcome[order]
    cum_t, cum_c = np.cumsum(t), np.cumsum(1 - t)
    y_t, y_c = np.cumsum(y * t), np.cumsum(y * (1 - t))
    q = y_t - y_c * np.divide(cum_t, np.maximum(cum_c, 1))
    idx = np.linspace(0, len(score), points).astype(int)
    x = idx / len(score)
    qv = np.concatenate([[0.0], q[idx[1:] - 1]])
    return x, qv


def main():
    df = pd.read_csv(ROOT / "data" / "customers_causal.csv")
    train, test = train_test_split(df, test_size=0.3, random_state=0)

    model = LinearDML(model_y=lgbm(), model_t=lgbm(), cv=5, random_state=0,
                      featurizer=PolynomialFeatures(2, include_bias=False))
    model.fit(train.purchase.values, train.discount.values, X=train[FEATURES].values)

    # baseline purchase probability with NO discount (used to split the 'no effect' groups)
    base = LGBMClassifier(n_estimators=150, learning_rate=0.05, verbose=-1, random_state=0)
    ctrl = train[train.discount == 0]
    base.fit(ctrl[FEATURES], ctrl.purchase)

    X = test[FEATURES].values
    ite = model.effect(X, T0=0, T1=DISCOUNT)
    lo, hi = model.effect_interval(X, T0=0, T1=DISCOUNT, alpha=0.05)
    p0 = base.predict_proba(test[FEATURES])[:, 1]

    customers = [
        {"customer_id": int(cid), "baseline_prob": round(float(b), 4),
         "ite": round(float(i), 4), "ci_lower": round(float(l), 4),
         "ci_upper": round(float(h), 4), "segment": segment(i, l, h, b)}
        for cid, b, i, l, h in zip(test.customer_id.values, p0, ite, lo, hi)
    ]
    counts = pd.Series([c["segment"] for c in customers]).value_counts().to_dict()
    sample = {
        "discount": DISCOUNT,
        "model": "LinearDML (EconML), LightGBM nuisance models",
        "n_customers": len(customers),
        "segment_counts": counts,
        "customers": customers[:N_SAMPLE_CUSTOMERS],
    }
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "sample_ite.json").write_text(json.dumps(sample, indent=2))

    # Qini curve on held-out customers who got $0 or $10 (observed outcomes only)
    sub = test[test.discount.isin([0, DISCOUNT])]
    s = model.effect(sub[FEATURES].values, T0=0, T1=DISCOUNT)
    treated = (sub.discount.values == DISCOUNT).astype(float)
    x, q = qini_curve(s, treated, sub.purchase.values.astype(float))
    random_line = x * q[-1]
    uplift = {
        "discount": DISCOUNT,
        "x_label": "fraction of customers targeted (best-ranked first)",
        "y_label": "cumulative extra purchases caused",
        "model": {"x": [round(v, 3) for v in x], "qini": [round(float(v), 2) for v in q]},
        "random": {"x": [round(v, 3) for v in x], "qini": [round(float(v), 2) for v in random_line]},
        "qini_coefficient": round(float(_trapezoid(q - random_line, x)), 3),
    }
    (ROOT / "docs" / "sample_uplift_curve.json").write_text(json.dumps(uplift, indent=2))

    print(f"Wrote docs/sample_ite.json ({len(sample['customers'])} customers) "
          "and docs/sample_uplift_curve.json")
    print("Segments over all scored customers:", counts)
    print("Qini curve (model):", uplift["model"]["qini"][::4], "...")
    print("Qini curve (random):", uplift["random"]["qini"][::4], "...")
    print("Qini coefficient:", uplift["qini_coefficient"])


if __name__ == "__main__":
    main()
