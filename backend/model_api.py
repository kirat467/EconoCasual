"""Model API: serves the Member-2 results (ITE, uplift curve, optimizer) over HTTP.

It is a Flask Blueprint, so it can run on its own or be plugged into Kirat's
existing Flask app (backend/app.py) with two lines:

    from model_api import model_api
    app.register_blueprint(model_api)

Run on its own (from the repository root):
    python backend/model_api.py          # http://localhost:8000

Endpoints follow docs/api_contract.md. For now they serve the files that the
export scripts produce (docs/sample_ite.json, docs/sample_uplift_curve.json,
docs/optimizer_effects.json, docs/sample_drift.json), so the frontend can be built against real model
output. Re-run the export scripts to refresh them.
"""
import json
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from flask import Blueprint, Flask, jsonify, request

sys.path.insert(0, str(Path(__file__).resolve().parent))
from drift import FEATURES, detect_drift  # noqa: E402
from optimizer_core import DISCOUNTS, build_response  # noqa: E402

DOCS = Path(__file__).resolve().parent.parent / "docs"
SEGMENTS = {"persuadable", "sleeping_dog", "sure_thing", "lost_cause"}

MIN_DRIFT_ROWS = 50   # fewer rows than this makes the statistical tests unreliable

model_api = Blueprint("model_api", __name__)


def _load(name):
    path = DOCS / name
    if not path.exists():
        return None
    with path.open() as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _effects():
    return _load("optimizer_effects.json")


def _missing(name, hint):
    return jsonify({"error": f"{name} not found", "hint": hint}), 503


@model_api.after_request
def _cors(response):
    # lets the browser frontend (served from another origin) read the response
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@model_api.route("/api/ite")
def ite():
    data = _load("sample_ite.json")
    if data is None:
        return _missing("sample_ite.json", "run python backend/export_sample_json.py")

    discount = request.args.get("discount", "10")
    if discount != "10":
        return jsonify({"error": "only discount=10 is supported for now"}), 400

    segment = request.args.get("segment")
    customers = data["customers"]
    if segment:
        if segment not in SEGMENTS:
            return jsonify({"error": f"segment must be one of {sorted(SEGMENTS)}"}), 400
        customers = [c for c in customers if c["segment"] == segment]

    limit = request.args.get("limit", type=int)
    if limit is not None:
        if limit < 0:
            return jsonify({"error": "limit must be 0 or more"}), 400
        customers = customers[:limit]

    return jsonify({**data, "customers": customers, "n_returned": len(customers)})


@model_api.route("/api/uplift-curve")
def uplift_curve():
    data = _load("sample_uplift_curve.json")
    if data is None:
        return _missing("sample_uplift_curve.json", "run python backend/export_sample_json.py")
    return jsonify(data)


@model_api.route("/api/optimize", methods=["GET", "POST"])
def optimize():
    """Solve the coupon allocation for ANY budget (uses the saved effects, no refit)."""
    cache = _effects()
    if cache is None:
        return _missing("optimizer_effects.json", "run python backend/optimizer.py --export")

    body = request.get_json(silent=True) or {}
    budget = body.get("budget", request.args.get("budget", 5000))
    try:
        budget = float(budget)
    except (TypeError, ValueError):
        return jsonify({"error": "budget must be a number"}), 400
    n = len(cache["customer_id"])
    if not (budget > 0) or budget > n * max(DISCOUNTS):   # also rejects NaN
        return jsonify({"error": f"budget must be more than 0 and at most {n * max(DISCOUNTS):,}"}), 400

    result = build_response(
        budget, np.array(cache["customer_id"]),
        {d: np.array(cache[f"tau_{d}"]) for d in DISCOUNTS},
        {d: np.array(cache[f"lo_{d}"]) for d in DISCOUNTS},
    )
    return jsonify(result)


@lru_cache(maxsize=1)
def _drift_reference():
    ref = _load("drift_reference.json")
    return None if ref is None else pd.DataFrame(ref)


@model_api.route("/api/drift", methods=["GET", "POST"])
def drift():
    """GET: stored example (a simulated shift). POST: live check of YOUR customers.

    POST body: {"customers": [{"previous_purchases": 3, "engagement": 7,
                               "price_sensitivity": 0.4, "age": 35}, ...]}
    The rows are compared with the data the model was trained on.
    """
    if request.method == "GET":
        data = _load("sample_drift.json")
        if data is None:
            return _missing("sample_drift.json", "run python backend/drift.py --export")
        return jsonify(data)

    reference = _drift_reference()
    if reference is None:
        return _missing("drift_reference.json", "run python backend/drift.py --export")

    body = request.get_json(silent=True) or {}
    rows = body.get("customers")
    if not isinstance(rows, list) or len(rows) < MIN_DRIFT_ROWS:
        return jsonify({"error": f"send a 'customers' list with at least {MIN_DRIFT_ROWS} rows"}), 400
    try:
        new = pd.DataFrame(rows)[FEATURES].astype(float)
    except (KeyError, ValueError, TypeError):
        return jsonify({"error": f"every customer needs numeric values for {FEATURES}"}), 400
    if new.isna().any().any() or not np.isfinite(new.to_numpy()).all():
        return jsonify({"error": "values must be finite numbers (no missing values)"}), 400
    return jsonify(detect_drift(reference, new))


@model_api.route("/api/health")
def health():
    files = ["sample_ite.json", "sample_uplift_curve.json", "optimizer_effects.json", "sample_drift.json", "drift_reference.json"]
    return jsonify({"status": "ok", "files": {f: (DOCS / f).exists() for f in files}})


def create_app():
    app = Flask(__name__)
    app.register_blueprint(model_api)
    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=8000, debug=False)
