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


def test_optimize_rejects_unsupported_or_invalid_budget():
    assert client.post("/api/optimize", json={"budget": 9999}).status_code == 400
    assert client.post("/api/optimize", json={"budget": "lots"}).status_code == 400


def test_drift_flags_shifted_features_only():
    body = client.get("/api/drift").get_json()
    assert body["drift_detected"] is True
    flagged = {f["name"] for f in body["features"] if f["drift"]}
    assert flagged == {"previous_purchases", "engagement"}


def test_cors_header_present():
    assert client.get("/api/uplift-curve").headers["Access-Control-Allow-Origin"] == "*"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS  {t.__name__}")
    print(f"\n{len(tests)} tests passed")
