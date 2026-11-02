"""One server for the whole backend: Kirat's data API + Sharath's model API.

It imports the existing Flask app (backend/app.py) and plugs the model API into it,
without editing either file. It also adds GET /api/customers, the endpoint the
frontend (frontend/docs/API.md) expects: every customer as one JSON array.

Run from the repository root:
    python backend/server.py                      # http://localhost:8000
    gunicorn --chdir backend --bind 0.0.0.0:8000 server:app

Then, in frontend/config.js, set:  window.ECONO_CONFIG = { apiBase: "http://localhost:8000" };
"""
import sys
from pathlib import Path

from flask import jsonify

sys.path.insert(0, str(Path(__file__).resolve().parent))
from app import REQUIRED_COLUMNS, app, load_data  # noqa: E402  (Kirat's app and data loader)
from model_api import model_api  # noqa: E402

app.register_blueprint(model_api)


@app.route("/api/customers", methods=["GET"])
def api_customers():
    """All customers as a plain JSON array (the shape the dashboard reads)."""
    try:
        df = load_data()[REQUIRED_COLUMNS]
        return jsonify(df.to_dict(orient="records")), 200
    except Exception:
        app.logger.exception("Error retrieving customers for the dashboard")
        return jsonify({"error": "Unable to retrieve customers"}), 500


@app.after_request
def allow_dashboard(response):
    """Let the browser dashboard (another origin) read /api/* responses."""
    from flask import request
    if request.path.startswith("/api/"):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
