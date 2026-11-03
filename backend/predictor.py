"""Score NEW customers with the saved causal model (no EconML needed).

Loads docs/predict_model.json, written by backend/export_predict_model.py.
For each customer it returns the baseline purchase probability and the effect of a $10
and a $20 coupon, each with a 95% interval, plus a segment and a suggested coupon.
"""
import json
from functools import lru_cache
from itertools import combinations_with_replacement
from pathlib import Path

import lightgbm as lgb
import numpy as np

MODEL_FILE = Path(__file__).resolve().parent.parent / "docs" / "predict_model.json"


@lru_cache(maxsize=1)
def load():
    if not MODEL_FILE.exists():
        return None
    spec = json.loads(MODEL_FILE.read_text())
    spec["_theta"] = {d: np.array(v) for d, v in spec["theta"].items()}
    spec["_cov"] = {d: np.array(v) for d, v in spec["covariance"].items()}
    spec["_booster"] = lgb.Booster(model_str=spec["baseline_lightgbm"])
    return spec


def features_matrix(X):
    """[1, x1..xn, then every product x_i*x_j (i <= j)]: the same order as sklearn's
    PolynomialFeatures(2, include_bias=False) with a constant column in front."""
    n, p = X.shape
    cols = [np.ones(n)] + [X[:, i] for i in range(p)]
    cols += [X[:, i] * X[:, j] for i, j in combinations_with_replacement(range(p), 2)]
    return np.column_stack(cols)


def segment(lo, hi, baseline):
    if lo > 0:
        return "persuadable"
    if hi < 0:
        return "sleeping_dog"
    return "sure_thing" if baseline >= 0.5 else "lost_cause"


def predict(rows):
    """rows: list of dicts with the model's features. Returns a list of result dicts."""
    spec = load()
    feats = spec["features"]
    X = np.array([[float(r[f]) for f in feats] for r in rows])
    M = features_matrix(X)
    p0 = spec["_booster"].predict(X)                      # probability of buying with no discount
    z = spec["z"]

    per_coupon = {}
    for d in spec["discounts"]:
        key = str(d)
        mean = M @ spec["_theta"][key]
        se = np.sqrt(np.einsum("ij,jk,ik->i", M, spec["_cov"][key], M))
        # a probability effect must lie in [-p0, 1 - p0]
        per_coupon[key] = tuple(np.clip(v, -p0, 1 - p0) for v in (mean, mean - z * se, mean + z * se))

    results = []
    for i, row in enumerate(rows):
        coupons = {k: {"effect": round(float(v[0][i]), 4), "ci_lower": round(float(v[1][i]), 4),
                       "ci_upper": round(float(v[2][i]), 4)} for k, v in per_coupon.items()}
        # suggested coupon: the one with the best CAUTIOUS (lower-bound) effect, if it is above zero
        best = max(coupons, key=lambda k: coupons[k]["ci_lower"])
        suggested = int(best) if coupons[best]["ci_lower"] > 0 else 0
        outside = [f for f in feats if not spec["training_ranges"][f][0] <= float(row[f]) <= spec["training_ranges"][f][1]]
        results.append({
            "baseline_prob": round(float(p0[i]), 4),
            "coupons": coupons,
            "segment": segment(coupons["10"]["ci_lower"], coupons["10"]["ci_upper"], float(p0[i])),
            "suggested_coupon": suggested,
            "outside_training_range": outside,
        })
    return results
