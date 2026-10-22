import csv
from pathlib import Path
from flask import Flask, jsonify, request

app = Flask(__name__)

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "customers.csv"


def load_customers():
    with open(DATA_FILE, "r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def convert_customer_values(data):
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

    return data


def create_purchase_groups(data, group_column):
    groups = {}

    for row in data:
        group_value = int(row[group_column])
        purchase = int(row["purchase"])

        if group_value not in groups:
            groups[group_value] = {
                "total_customers": 0,
                "total_purchases": 0,
                "non_purchases": 0
            }

        groups[group_value]["total_customers"] += 1

        if purchase == 1:
            groups[group_value]["total_purchases"] += 1
        else:
            groups[group_value]["non_purchases"] += 1

    results = {}

    for group_value, values in sorted(groups.items()):
        total = values["total_customers"]
        purchases = values["total_purchases"]

        results[str(group_value)] = {
            "total_customers": total,
            "total_purchases": purchases,
            "non_purchases": values["non_purchases"],
            "purchase_rate_percent": round(
                (purchases / total) * 100, 2
            )
        }

    return results


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

    data = convert_customer_values(load_customers())
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

    data = load_customers()
    total = len(data)

    if total == 0:
        return jsonify({
            "error": "Dataset is empty"
        }), 400

    purchases = sum(int(row["purchase"]) for row in data)

    return jsonify({
        "total_customers": total,
        "total_purchases": purchases,
        "non_purchases": total - purchases,
        "purchase_rate_percent": round(
            (purchases / total) * 100, 2
        )
    })


@app.route("/discount-analysis")
def discount_analysis():
    if not DATA_FILE.exists():
        return jsonify({
            "error": "Customer dataset not found"
        }), 404

    data = load_customers()

    if not data:
        return jsonify({
            "error": "Dataset is empty"
        }), 400

    return jsonify({
        "analysis": "Discount-wise customer purchase behavior",
        "discount_groups": create_purchase_groups(data, "discount")
    })


@app.route("/previous-purchases-analysis")
def previous_purchases_analysis():
    if not DATA_FILE.exists():
        return jsonify({
            "error": "Customer dataset not found"
        }), 404

    data = load_customers()

    if not data:
        return jsonify({
            "error": "Dataset is empty"
        }), 400

    return jsonify({
        "analysis": "Previous purchases and current purchase behavior",
        "previous_purchase_groups": create_purchase_groups(
            data, "previous_purchases"
        )
    })


@app.route("/engagement-analysis")
def engagement_analysis():
    if not DATA_FILE.exists():
        return jsonify({
            "error": "Customer dataset not found"
        }), 404

    data = load_customers()

    if not data:
        return jsonify({
            "error": "Dataset is empty"
        }), 400

    return jsonify({
        "analysis": "Engagement-wise customer purchase behavior",
        "engagement_groups": create_purchase_groups(
            data, "engagement"
        )
    })


if __name__ == "__main__":
    app.run(debug=True)