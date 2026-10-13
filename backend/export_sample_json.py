"""
export_sample_json.py - writes sample API payloads for Member 3 (frontend).

Outputs (in ./sample_json/):
    ite_sample.json     per-customer Individual Treatment Effect + segment
    uplift_curve.json   cumulative uplift / Qini curve + model-vs-random AUUC
    summary.json        headline numbers + balance diagnostics (from propensity.py)

NOTE: ITE here comes from a T-learner (gradient boosting) as a stand-in.
Swap `estimate_ite()` for the Week-2 EconML Double ML output when wired in;
the JSON shape (the contract) stays identical.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split

import propensity as pr

# NumPy 2 renamed trapz -> trapezoid; support both.
_trapz = getattr(np, "trapezoid", None) or np.trapz

OUT = Path(__file__).parent / "sample_json"


def estimate_ite(df: pd.DataFrame, train_idx, score_idx) -> np.ndarray:
    """T-learner: ITE = P(buy | X, treated) - P(buy | X, control)."""
    X = df[pr.COVARIATES].to_numpy(float)
    t = (df[pr.TREATMENT] > 0).to_numpy()
    y = df[pr.OUTCOME].to_numpy(int)
    tr = np.asarray(train_idx)
    m1 = GradientBoostingClassifier(n_estimators=100, max_depth=2, learning_rate=0.05, subsample=0.8, random_state=0).fit(X[tr][t[tr]], y[tr][t[tr]])
    m0 = GradientBoostingClassifier(n_estimators=100, max_depth=2, learning_rate=0.05, subsample=0.8, random_state=0).fit(X[tr][~t[tr]], y[tr][~t[tr]])
    Xs = X[score_idx]
    return m1.predict_proba(Xs)[:, 1] - m0.predict_proba(Xs)[:, 1]


def segment(ite: np.ndarray, base: np.ndarray) -> list[str]:
    """Marketing segments. 'persuadable' = discount meaningfully raises buy prob."""
    out = []
    for i, b in zip(ite, base):
        if i >= 0.10:
            out.append("persuadable")
        elif i <= -0.02:
            out.append("sleeping_dog")      # discount hurts / no benefit
        elif b >= 0.6:
            out.append("sure_thing")        # buys anyway
        else:
            out.append("lost_cause")
    return out


def uplift_curve(ite_pred, y, t, n_points: int = 50) -> dict:
    """Qini-style curve on held-out data, ranked by predicted ITE."""
    order = np.argsort(-ite_pred)
    y, t = y[order], t[order]
    n = len(y)
    fracs = np.linspace(0, 1, n_points + 1)
    qini = [0.0]
    for f in fracs[1:]:
        k = int(round(f * n))
        yk, tk = y[:k], t[:k]
        n1, n0 = max(tk.sum(), 1), max((1 - tk).sum(), 1)
        qini.append(float(yk[tk == 1].sum() - yk[tk == 0].sum() * n1 / n0))
    qini = np.array(qini)
    random_line = fracs * qini[-1]
    return {
        "fraction_targeted": fracs.round(4).tolist(),
        "qini_model": qini.round(3).tolist(),
        "qini_random": random_line.round(3).tolist(),
        "auuc_model": float(_trapz(qini, fracs)),
        "auuc_random": float(_trapz(random_line, fracs)),
    }


def main(n_customers: int = 5000, n_sample: int = 200):
    OUT.mkdir(exist_ok=True)
    df = pr.make_synthetic(n=n_customers)
    idx = np.arange(len(df))
    train, test = train_test_split(idx, test_size=0.3, random_state=0)

    ite = estimate_ite(df, train, test)
    test_df = df.iloc[test].reset_index(drop=True)
    t = (test_df[pr.TREATMENT] > 0).to_numpy().astype(int)
    y = test_df[pr.OUTCOME].to_numpy(int)

    base = np.clip(0.5 + 0.2 * test_df["engagement"].to_numpy(), 0, 1)  # display-only proxy
    segs = segment(ite, base)

    sample = test_df.assign(ite=ite, segment=segs).sort_values("ite", ascending=False).head(n_sample)
    ite_payload = {
        "meta": {"n_customers_scored": int(len(test_df)), "n_returned": int(len(sample)),
                 "treatment": "discount>0", "outcome": "purchase",
                 "ite_definition": "P(buy|discount) - P(buy|no discount)"},
        "customers": [
            {"customer_id": int(r.customer_id),
             "previous_purchases": float(r.previous_purchases),
             "engagement": round(float(r.engagement), 4),
             "ite": round(float(r.ite), 4),
             "segment": r.segment}
            for r in sample.itertuples()
        ],
    }

    summary = pr.run(df, n_boot=100)
    summary["avg_predicted_ite"] = float(np.mean(ite))
    summary["segment_counts"] = pd.Series(segs).value_counts().to_dict()

    (OUT / "ite_sample.json").write_text(json.dumps(ite_payload, indent=2))
    (OUT / "uplift_curve.json").write_text(json.dumps(uplift_curve(ite, y, t), indent=2))
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    print("wrote", [p.name for p in OUT.iterdir()])


if __name__ == "__main__":
    main()
