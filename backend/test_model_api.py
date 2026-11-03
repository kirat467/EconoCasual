"""Tests for the model API. Run from the repository root:
    python backend/test_model_api.py      (plain run)
    pytest backend/test_model_api.py      (if pytest is installed)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from model_api import create_app  # noqa: E402

client = create_app().test_client()


def test_health_reports_all_files():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert all(r.get_json()["files"].values())


def test_ite_returns_all_customers_with_expected_fields():
    r = client.get("/api/ite")
    body = r.get_json()
    assert r.status_code == 200
    assert body["n_customers"] == len(body["customers"]) == 1500
    assert {"customer_id", "baseline_prob", "ite", "ci_lower", "ci_upper", "segment"} <= set(body["customers"][0])


def test_ite_segment_filter_and_limit():
    body = client.get("/api/ite?segment=persuadable&limit=5").get_json()
    assert body["n_returned"] == 5
    assert all(c["segment"] == "persuadable" for c in body["customers"])


def test_ite_rejects_bad_input():
    assert client.get("/api/ite?segment=banana").status_code == 400
    assert client.get("/api/ite?limit=-1").status_code == 400
    assert client.get("/api/ite?discount=20").status_code == 400


def test_uplift_curve_has_model_and_random_lines():
    body = client.get("/api/uplift-curve").get_json()
    assert len(body["model"]["x"]) == len(body["model"]["qini"]) == 21
    assert body["random"]["qini"][0] == 0


def test_optimize_respects_budget_and_never_picks_negative_effects():
    r = client.post("/api/optimize", json={"budget": 5000})
    body = r.get_json()
    assert r.status_code == 200
    assert body["total_cost"] <= body["budget"]
    assert all(row["cautious_uplift"] > 0 for row in body["allocation"])


def test_optimize_works_for_other_budgets():
    small = client.post("/api/optimize", json={"budget": 2000}).get_json()
    large = client.post("/api/optimize", json={"budget": 8000}).get_json()
    assert small["total_cost"] <= 2000 and large["total_cost"] <= 8000
    assert large["cautious_incremental_purchases"] > small["cautious_incremental_purchases"]
    assert isinstance(large["summary"], str) and "$8,000" in large["summary"]


def test_summary_does_not_present_point_estimate_savings_as_cautious():
    summary = client.post("/api/optimize", json={"budget": 2000}).get_json()["summary"]
    assert "cautious estimate" in summary
    if "blanket" in summary:
        assert "which run high" in summary


def test_optimize_rejects_invalid_budget():
    for bad in (0, -50, "lots", 10**9):
        assert client.post("/api/optimize", json={"budget": bad}).status_code == 400


def test_drift_flags_shifted_features_only():
    body = client.get("/api/drift").get_json()
    assert body["drift_detected"] is True
    flagged = {f["name"] for f in body["features"] if f["drift"]}
    assert flagged == {"previous_purchases", "engagement"}


def _live_rows(shift=0.0, n=300, seed=7):
    import numpy as np
    rng = np.random.default_rng(seed)
    return [{"previous_purchases": float(max(0, rng.normal(3, 2))),
             "engagement": float(rng.normal(5 + shift, 2)),
             "price_sensitivity": float(rng.uniform(0, 1)),
             "age": float(rng.normal(40, 10))} for _ in range(n)]


def test_live_drift_flags_a_shifted_feature():
    bad = client.post("/api/drift", json={"customers": _live_rows(6.0)}).get_json()
    assert bad["drift_detected"] is True
    assert "engagement" in {f["name"] for f in bad["features"] if f["drift"]}
    assert bad["n_new"] == 300


def test_live_drift_rejects_bad_input():
    assert client.post("/api/drift", json={"customers": []}).status_code == 400
    assert client.post("/api/drift", json={}).status_code == 400
    too_few = _live_rows(n=10)
    assert client.post("/api/drift", json={"customers": too_few}).status_code == 400
    missing = [{"engagement": 5}] * 100
    assert client.post("/api/drift", json={"customers": missing}).status_code == 400


def _check_rows():
    import json
    from model_api import DOCS
    return json.loads((DOCS / "predict_model.json").read_text())["check_rows"]


def test_predict_matches_the_trained_model_for_known_customers():
    for case in _check_rows():
        got = client.post("/api/predict", json=case["features"]).get_json()
        exp = case["expected"]
        assert abs(got["baseline_prob"] - exp["baseline_prob"]) < 1e-4
        for coupon in ("10", "20"):
            for field in ("effect", "ci_lower", "ci_upper"):
                assert abs(got["coupons"][coupon][field] - exp[coupon][field]) < 1e-4


def test_predict_accepts_a_list_and_returns_the_expected_fields():
    rows = [c["features"] for c in _check_rows()]
    body = client.post("/api/predict", json={"customers": rows}).get_json()
    assert body["n"] == len(rows)
    first = body["customers"][0]
    assert {"baseline_prob", "coupons", "segment", "suggested_coupon", "outside_training_range", "features"} <= set(first)
    assert first["segment"] in {"persuadable", "sleeping_dog", "sure_thing", "lost_cause"}
    assert first["suggested_coupon"] in (0, 10, 20)


def test_predict_never_suggests_a_coupon_that_is_not_clearly_positive():
    rows = [c["features"] for c in _check_rows()]
    for res in client.post("/api/predict", json={"customers": rows}).get_json()["customers"]:
        if res["suggested_coupon"]:
            assert res["coupons"][str(res["suggested_coupon"])]["ci_lower"] > 0


def test_predict_flags_values_outside_the_training_range():
    row = dict(_check_rows()[0]["features"], age=150)
    res = client.post("/api/predict", json=row).get_json()
    assert res["outside_training_range"] == ["age"]


def test_predict_rejects_bad_input():
    good = _check_rows()[0]["features"]
    assert client.post("/api/predict", json={}).status_code == 400
    assert client.post("/api/predict", json={"customers": []}).status_code == 400
    assert client.post("/api/predict", json=dict(good, age="old")).status_code == 400
    assert client.post("/api/predict", json={k: v for k, v in good.items() if k != "age"}).status_code == 400
    assert client.post("/api/predict", json={"customers": [good] * 1001}).status_code == 400


def test_cors_header_present():
    assert client.get("/api/uplift-curve").headers["Access-Control-Allow-Origin"] == "*"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS  {t.__name__}")
    print(f"\n{len(tests)} tests passed")
