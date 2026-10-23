
from flask import Flask, jsonify, request
from pathlib import Path
import pandas as pd

app = Flask(__name__)

DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "customers.csv"
)


@app.route("/")
def home():
    return jsonify({
        "message": "EconoCasual API is running successfully"
    }), 200


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy"
    }), 200


@app.route("/customers", methods=["GET"])
def customers():
    if not DATA_FILE.exists():
        return jsonify({
            "error": "Customer dataset not found"
        }), 404

    try:
        limit = int(request.args.get("limit", 20))
        offset = int(request.args.get("offset", 0))

    except ValueError:
        return jsonify({
            "error": "Limit and offset must be integers"
        }), 400

    if limit < 1 or offset < 0:
        return jsonify({
            "error": "Limit must be positive and offset cannot be negative"
        }), 400

    try:
        df = pd.read_csv(DATA_FILE)

        customers_data = df.iloc[offset:offset + limit]

        return jsonify({
            "total_customers": len(df),
            "limit": limit,
            "offset": offset,
            "columns": df.columns.tolist(),
            "customers": customers_data.to_dict(orient="records")
        }), 200

    except Exception as e:
        app.logger.exception("Error reading customer dataset")

        return jsonify({
            "error": "Unable to read customer dataset"
        }), 500


@app.route("/purchase-summary", methods=["GET"])
def purchase_summary():
    if not DATA_FILE.exists():
        return jsonify({
            "error": "Customer dataset not found"
        }), 404

    try:
        df = pd.read_csv(DATA_FILE)

        if "purchase" not in df.columns:
            return jsonify({
                "error": "Purchase column not found in dataset"
            }), 400

        total_customers = len(df)
        total_purchases = int(df["purchase"].sum())
        non_purchases = total_customers - total_purchases

        purchase_rate = (
            round((total_purchases / total_customers) * 100, 2)
            if total_customers > 0
            else 0
        )

        return jsonify({
            "total_customers": total_customers,
            "total_purchases": total_purchases,
            "non_purchases": non_purchases,
            "purchase_rate_percent": purchase_rate
        }), 200

    except Exception:
        app.logger.exception("Error generating purchase summary")

        return jsonify({
            "error": "Unable to generate purchase summary"
        }), 500


if __name__ == "__main__":
    app.run(debug=True)

