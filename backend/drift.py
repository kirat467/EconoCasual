"""Data drift detector (Week 4, Member 2).

Question it answers: has the customer data we see NOW stopped looking like the
data the model was trained on? If it has, the ITE estimates may no longer be
trustworthy and the frontend should show a warning.

Method: for every feature, compare the reference (training) values with the new
values using
  - the two-sample Kolmogorov-Smirnov test (ks_statistic, p_value), and
  - the Population Stability Index, PSI (common in industry: < 0.1 stable,
    0.1 to 0.25 moderate shift, > 0.25 large shift).
A feature is flagged as drifted when p < alpha AND PSI >= 0.1. Requiring both
avoids false alarms: with thousands of rows the KS test alone flags tiny,
harmless differences, and PSI alone ignores sample size.

Run from the repository root:
    python backend/drift.py            # demo on data/customers_causal.csv
    python backend/drift.py --export   # also writes docs/sample_drift.json
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

ROOT = Path(__file__).resolve().parent.parent
FEATURES = ["previous_purchases", "engagement", "price_sensitivity", "age"]
PSI_THRESHOLD = 0.1
ALPHA = 0.01


def psi(reference, new, bins=10):
    """Population Stability Index between two samples (bins from the reference)."""
    reference, new = np.asarray(reference, float), np.asarray(new, float)
    edges = np.unique(np.quantile(reference, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:  # almost constant feature
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    eps = 1e-4  # avoids log(0) for empty bins
    ref_share = np.histogram(reference, edges)[0] / len(reference) + eps
    new_share = np.histogram(new, edges)[0] / len(new) + eps
    return float(np.sum((new_share - ref_share) * np.log(new_share / ref_share)))


def detect_drift(reference, new, features=FEATURES, alpha=ALPHA, psi_threshold=PSI_THRESHOLD):
    """Compare two DataFrames feature by feature. Returns the /api/drift payload."""
    rows = []
    for name in features:
        ks = ks_2samp(reference[name], new[name])
        value = psi(reference[name], new[name])
        rows.append({
            "name": name,
            "ks_statistic": round(float(ks.statistic), 4),
            "p_value": round(float(ks.pvalue), 4),
            "psi": round(value, 4),
            "drift": bool(ks.pvalue < alpha and value >= psi_threshold),
        })
    return {
        "drift_detected": any(r["drift"] for r in rows),
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "n_reference": int(len(reference)),
        "n_new": int(len(new)),
        "rule": f"drift if KS p-value < {alpha} and PSI >= {psi_threshold}",
        "features": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", action="store_true", help="write docs/sample_drift.json")
    args = parser.parse_args()

    df = pd.read_csv(ROOT / "data" / "customers_causal.csv")
    rng = np.random.default_rng(42)
    idx = rng.permutation(len(df))
    reference, same = df.iloc[idx[:2500]], df.iloc[idx[2500:]]

    print("Case 1: new data from the SAME population (should show no drift)")
    ok = detect_drift(reference, same)
    print(pd.DataFrame(ok["features"]).to_string(index=False))
    print("drift_detected:", ok["drift_detected"], "\n")

    # Simulate a change: customers become more engaged and spend less per visit
    shifted = same.copy()
    shifted["engagement"] = shifted["engagement"] + shifted["engagement"].std() * 0.8
    shifted["previous_purchases"] = (shifted["previous_purchases"] * 0.6).round()
    print("Case 2: engagement +0.8 SD and previous_purchases x0.6 (should show drift)")
    bad = detect_drift(reference, shifted)
    print(pd.DataFrame(bad["features"]).to_string(index=False))
    print("drift_detected:", bad["drift_detected"])

    if args.export:
        out = ROOT / "docs" / "sample_drift.json"
        out.write_text(json.dumps(bad, indent=2))
        # the reference data the live check (POST /api/drift) compares new data against
        ref = {name: [round(float(v), 4) for v in reference[name]] for name in FEATURES}
        (ROOT / "docs" / "drift_reference.json").write_text(json.dumps(ref))
        print(f"\nWrote {out.relative_to(ROOT)} (the simulated-drift case) and "
              f"docs/drift_reference.json (reference data for live checks)")


if __name__ == "__main__":
    main()
