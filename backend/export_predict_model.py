"""Save the trained causal model as plain numbers, so the API can score NEW customers.

Why this works: the model's final stage is linear in the features. With the degree-2
polynomial features phi(x) (14 of them) and a constant, the effect of coupon d is

    effect_d(x) = [1, phi(x)] . theta_d          and its 95% interval comes from
    stderr_d(x) = sqrt([1, phi(x)] V_d [1, phi(x)]^T)

so we only need theta_d (15 numbers) and V_d (15 x 15) for each coupon. No EconML is
needed at prediction time. The baseline purchase probability (no discount) comes from a
small LightGBM model, saved as text.

Run from the repository root:  python backend/export_predict_model.py
Writes docs/predict_model.json
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PolynomialFeatures

sys.path.insert(0, str(Path(__file__).resolve().parent))
from optimizer import DISCOUNTS, FEATURES, fit_model  # noqa: E402

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
Z = 1.959964          # 95% two-sided normal quantile


def main():
    df = pd.read_csv(ROOT / "data" / "customers_causal.csv")
    train, test = train_test_split(df, test_size=0.3, random_state=0)   # same split as the optimizer
    model = fit_model(train)

    final = model.model_final_
    params, cov = np.asarray(final._param), np.asarray(final._param_var)
    k = len(params) // len(DISCOUNTS)                                     # 15 = constant + 14 features
    theta = {str(d): params[i * k:(i + 1) * k].tolist() for i, d in enumerate(DISCOUNTS)}
    covariance = {str(d): cov[i * k:(i + 1) * k, i * k:(i + 1) * k].tolist() for i, d in enumerate(DISCOUNTS)}

    # baseline purchase probability with NO discount (also splits the "no effect" groups)
    ctrl = train[train.discount == 0]
    base = LGBMClassifier(n_estimators=150, learning_rate=0.05, verbose=-1, random_state=0)
    base.fit(ctrl[FEATURES], ctrl.purchase)

    # a few real customers with the model's own answers, so the API can be tested without EconML
    X = test[FEATURES].values
    p0 = base.predict_proba(test[FEATURES])[:, 1]
    check = []
    for i in range(5):
        row = {f: float(test[f].iloc[i]) for f in FEATURES}
        out = {"baseline_prob": float(np.round(p0[i], 6))}
        for d in DISCOUNTS:
            mean = float(model.effect(X[i:i + 1], T0=0, T1=d)[0])
            lo, hi = (float(v[0]) for v in model.effect_interval(X[i:i + 1], T0=0, T1=d, alpha=0.05))
            # same feasibility clip the optimizer uses: a probability effect lies in [-p0, 1-p0]
            out[str(d)] = {"effect": round(float(np.clip(mean, -p0[i], 1 - p0[i])), 6),
                           "ci_lower": round(float(np.clip(lo, -p0[i], 1 - p0[i])), 6),
                           "ci_upper": round(float(np.clip(hi, -p0[i], 1 - p0[i])), 6)}
        check.append({"features": row, "expected": out})

    out = {
        "model": "LinearDML (EconML), multi-valued treatment $0/$10/$20, degree-2 polynomial final stage",
        "features": FEATURES,
        "discounts": DISCOUNTS,
        "z": Z,
        "theta": theta,
        "covariance": covariance,
        "baseline_lightgbm": base.booster_.model_to_string(),
        "training_ranges": {f: [float(train[f].min()), float(train[f].max())] for f in FEATURES},
        "n_training": int(len(train)),
        "check_rows": check,
    }
    (ROOT / "docs" / "predict_model.json").write_text(json.dumps(out))
    size = (ROOT / "docs" / "predict_model.json").stat().st_size / 1024
    print(f"Wrote docs/predict_model.json ({size:.0f} KB); training ranges:", out["training_ranges"])

    # sanity: our formula against EconML on 200 held-out customers
    phi = PolynomialFeatures(2, include_bias=False).fit_transform(X[:200])
    M = np.hstack([np.ones((len(phi), 1)), phi])
    for d in DISCOUNTS:
        mine = M @ np.array(theta[str(d)])
        theirs = model.effect(X[:200], T0=0, T1=d)
        print(f"${d}: max |formula - EconML| = {np.abs(mine - theirs).max():.2e}")


if __name__ == "__main__":
    main()
