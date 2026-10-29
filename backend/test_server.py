"""Tests for the combined server. Run from the repository root:
    python backend/test_server.py      (plain run)
    pytest backend/test_server.py      (if pytest is installed)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from server import app  # noqa: E402

client = app.test_client()


def test_api_customers_returns_a_plain_array_in_the_shape_the_frontend_expects():
    r = client.get("/api/customers")
    rows = r.get_json()
    assert r.status_code == 200
    assert isinstance(rows, list) and len(rows) == 1000
    assert set(rows[0]) == {"customer_id", "previous_purchases", "engagement", "discount", "purchase"}
    assert all(row["discount"] in (0, 1) and row["purchase"] in (0, 1) for row in rows)
    assert all(0 <= row["engagement"] <= 10 and row["previous_purchases"] >= 0 for row in rows)


def test_api_customers_allows_the_browser_to_read_it():
    assert client.get("/api/customers").headers["Access-Control-Allow-Origin"] == "*"


def test_team_routes_still_work():
    assert client.get("/health").get_json() == {"status": "healthy"}
    assert client.get("/purchase-summary").status_code == 200
    assert client.get("/customers?page=1&per_page=5").get_json()["per_page"] == 5


def test_model_routes_are_plugged_in():
    assert client.get("/api/uplift-curve").status_code == 200
    assert client.get("/api/ite?limit=3").get_json()["n_returned"] == 3
    assert client.post("/api/optimize", json={"budget": 3000}).status_code == 200
    assert client.get("/api/health").get_json()["status"] == "ok"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS  {t.__name__}")
    print(f"\n{len(tests)} tests passed")
