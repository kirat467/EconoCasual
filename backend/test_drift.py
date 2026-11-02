"""Tests for the drift detector. Run from the repository root:
    python backend/test_drift.py      (plain run)
    pytest backend/test_drift.py      (if pytest is installed)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from drift import detect_drift, psi  # noqa: E402


def _frame(seed, shift=0.0, n=2000):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({"a": rng.normal(0 + shift, 1, n), "b": rng.normal(5, 2, n)})


def test_same_population_is_not_flagged():
    result = detect_drift(_frame(1), _frame(2), features=["a", "b"])
    assert result["drift_detected"] is False


def test_shifted_feature_is_flagged_and_other_is_not():
    result = detect_drift(_frame(1), _frame(2, shift=1.0), features=["a", "b"])
    flagged = {f["name"] for f in result["features"] if f["drift"]}
    assert flagged == {"a"}


def test_psi_is_zero_for_identical_samples_and_grows_with_shift():
    x = np.random.default_rng(0).normal(size=3000)
    assert psi(x, x) < 1e-6
    assert psi(x, x + 0.5) < psi(x, x + 1.5)


def test_payload_has_the_fields_the_api_promises():
    result = detect_drift(_frame(1), _frame(2), features=["a"])
    assert {"drift_detected", "checked_at", "features", "n_reference", "n_new"} <= set(result)
    assert {"name", "ks_statistic", "p_value", "psi", "drift"} <= set(result["features"][0])


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS  {t.__name__}")
    print(f"\n{len(tests)} tests passed")
