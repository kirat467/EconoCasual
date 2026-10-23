"""Model API: serves the Member-2 results (ITE, uplift curve, optimizer) over HTTP.

It is a Flask Blueprint, so it can run on its own or be plugged into Kirat's
existing Flask app (backend/app.py) with two lines:

    from model_api import model_api
    app.register_blueprint(model_api)

Run on its own (from the repository root):
    python backend/model_api.py          # http://localhost:8000

Endpoints follow docs/api_contract.md. For now they serve the files that the
export scripts produce (docs/sample_ite.json, docs/sample_uplift_curve.json,
docs/sample_optimize.json, docs/sample_drift.json), so the frontend can be built against real model
output. Re-run the export scripts to refresh them.
"""
import json
from pathlib import Path

from flask import Blueprint, Flask, jsonify, request

DOCS = Path(__file__).resolve().parent.parent / "docs"
SEGMENTS = {"persuadable", "sleeping_dog", "sure_thing", "lost_cause"}
SUPPORTED_BUDGET = 5000  # the budget the stored optimizer result was computed for

model_api = Blueprint("model_api", __name__)


def _load(name):
    path = DOCS / name
    if not path.exists():
        return None
    with path.open() as f:
        return json.load(f)


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
    data = _load("sample_optimize.json")
    if data is None:
        return _missing("sample_optimize.json", "run python backend/optimizer.py --export")

    body = request.get_json(silent=True) or {}
    budget = body.get("budget", request.args.get("budget", SUPPORTED_BUDGET, type=float))
    try:
        budget = float(budget)
    except (TypeError, ValueError):
        return jsonify({"error": "budget must be a number"}), 400
    if budget != SUPPORTED_BUDGET:
        return jsonify({
            "error": f"only budget={SUPPORTED_BUDGET} is available for now",
            "hint": "other budgets can be computed with: python backend/optimizer.py --budget <amount> --export",
        }), 400
    return jsonify(data)


@model_api.route("/api/drift")
def drift():
    # Stored result of backend/drift.py (a simulated-drift example). A live
    # check would compare incoming customer data with the training data.
    data = _load("sample_drift.json")
    if data is None:
        return _missing("sample_drift.json", "run python backend/drift.py --export")
    return jsonify(data)


@model_api.route("/api/health")
def health():
    files = ["sample_ite.json", "sample_uplift_curve.json", "sample_optimize.json", "sample_drift.json"]
    return jsonify({"status": "ok", "files": {f: (DOCS / f).exists() for f in files}})


def create_app():
    app = Flask(__name__)
    app.register_blueprint(model_api)
    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=8000, debug=False)
