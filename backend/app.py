import csv
from pathlib import Path
from flask import Flask, jsonify, request

app = Flask(__name__)

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "customers.csv"


@app.route("/")
def home():
    return jsonify({
        "project": "EconoCasual",
        "status": "running"
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy"
    })


@app.route("/customers")
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

    if limit < 1 or limit > 100:
        return jsonify({
            "error": "Limit must be between 1 and 100"
        }), 400

    if offset < 0:
        return jsonify({
            "error": "Offset cannot be negative"
        }), 400

    with open(DATA_FILE, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        data = list(reader)

    numeric_columns = [
        "customer_id",
        "previous_purchases",
        "engagement",
        "discount",
        "purchase"
    ]

    for customer in data:
        for column in numeric_columns:
            if column in customer and customer[column] != "":
                customer[column] = int(customer[column])

    total = len(data)
    selected_customers = data[offset:offset + limit]

    return jsonify({
        "total_customers": total,
        "limit": limit,
        "offset": offset,
        "returned_customers": len(selected_customers),
        "columns": list(data[0].keys()) if data else [],
        "customers": selected_customers
    })


@app.route("/purchase-summary")
def purchase_summary():
    if not DATA_FILE.exists():
        return jsonify({
            "error": "Customer dataset not found"
        }), 404

    with open(DATA_FILE, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        data = list(reader)

    total = len(data)

    if total == 0:
        return jsonify({
            "error": "Dataset is empty"
        }), 400

    purchases = sum(int(row["purchase"]) for row in data)
    purchase_rate = round((purchases / total) * 100, 2)

    return jsonify({
        "total_customers": total,
        "total_purchases": purchases,
        "non_purchases": total - purchases,
        "purchase_rate_percent": purchase_rate
    })


if __name__ == "__main__":
    app.run(debug=True)