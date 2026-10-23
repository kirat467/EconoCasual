from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, request


app = Flask(__name__)

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_DIR / "data" / "customers.csv"

REQUIRED_COLUMNS = [
    "customer_id",
    "previous_purchases",
    "engagement",
    "discount",
    "purchase",
]


def load_data():
    """Load customer data and verify that required columns exist."""
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Customer dataset not found: {DATA_FILE}"
        )

    df = pd.read_csv(DATA_FILE)

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    return df


def calculate_purchase_statistics(group):
    """Calculate purchase statistics for a customer group."""
    total_customers = int(len(group))
    total_purchases = int(group["purchase"].sum())
    non_purchases = total_customers - total_purchases

    purchase_rate = (
        round(total_purchases / total_customers * 100, 2)
        if total_customers
        else 0.0
    )

    return {
        "total_customers": total_customers,
        "total_purchases": total_purchases,
        "non_purchases": non_purchases,
        "purchase_rate_percent": purchase_rate,
    }


def analyse_column(df, column):
    """Group customer data and calculate purchase statistics."""
    result = {}

    for value, group in df.groupby(column, dropna=False):
        key = str(value) if pd.notna(value) else "Unknown"
        result[key] = calculate_purchase_statistics(group)

    return result


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Welcome to EconoCasual Backend API",
        "status": "running",
    }), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
    }), 200


@app.route("/customers", methods=["GET"])
def customers():
    try:
        df = load_data()

        # Invalid, zero, or negative page values default to page 1.
        try:
            page = int(request.args.get("page", 1))
        except (TypeError, ValueError):
            page = 1

        if page < 1:
            page = 1

        try:
            per_page = int(request.args.get("per_page", 20))
        except (TypeError, ValueError):
            per_page = 20

        if per_page < 1:
            per_page = 20

        # Prevent excessively large responses.
        per_page = min(per_page, 100)

        # Optional filtering.
        for column in ["discount", "engagement", "purchase"]:
            value = request.args.get(column)

            if value is not None:
                try:
                    numeric_value = float(value)
                    df = df[df[column] == numeric_value]
                except ValueError:
                    return jsonify({
                        "error": f"Invalid filter value for {column}"
                    }), 400

        total_customers = int(len(df))
        start = (page - 1) * per_page
        end = start + per_page

        page_df = df.iloc[start:end].copy()
        page_df = page_df.astype(object).where(
            pd.notna(page_df), None
        )

        return jsonify({
            "total_customers": total_customers,
            "columns": list(df.columns),
            "page": page,
            "per_page": per_page,
            "customers": page_df.to_dict(orient="records"),
        }), 200

    except FileNotFoundError as error:
        app.logger.error("%s", error)
        return jsonify({"error": "Customer dataset not found"}), 500

    except (ValueError, pd.errors.ParserError):
        app.logger.exception("Unable to load customer data")
        return jsonify({"error": "Invalid customer dataset"}), 500

    except Exception:
        app.logger.exception("Error retrieving customers")
        return jsonify({"error": "Unable to retrieve customers"}), 500


@app.route("/purchase-summary", methods=["GET"])
def purchase_summary():
    try:
        df = load_data()
        summary = calculate_purchase_statistics(df)
        return jsonify(summary), 200

    except Exception:
        app.logger.exception("Error generating purchase summary")
        return jsonify({
            "error": "Unable to generate purchase summary"
        }), 500


@app.route("/discount-analysis", methods=["GET"])
def discount_analysis():
    try:
        df = load_data()
        return jsonify({
            "analysis": analyse_column(df, "discount")
        }), 200

    except Exception:
        app.logger.exception("Error generating discount analysis")
        return jsonify({
            "error": "Unable to generate discount analysis"
        }), 500


@app.route("/engagement-analysis", methods=["GET"])
def engagement_analysis():
    try:
        df = load_data()
        return jsonify({
            "analysis": analyse_column(df, "engagement")
        }), 200

    except Exception:
        app.logger.exception("Error generating engagement analysis")
        return jsonify({
            "error": "Unable to generate engagement analysis"
        }), 500


@app.route("/previous-purchases-analysis", methods=["GET"])
def previous_purchases_analysis():
    try:
        df = load_data()
        return jsonify({
            "analysis": analyse_column(df, "previous_purchases")
        }), 200

    except Exception:
        app.logger.exception(
            "Error generating previous purchases analysis"
        )
        return jsonify({
            "error": "Unable to generate previous purchases analysis"
        }), 500


@app.route("/validate-data", methods=["GET"])
def validate_data():
    try:
        df = load_data()

        missing_values = {
            column: int(count)
            for column, count in df.isnull().sum().items()
        }

        return jsonify({
            "total_rows": int(len(df)),
            "total_columns": int(len(df.columns)),
            "columns": list(df.columns),
            "missing_values_by_column": missing_values,
            "has_missing_values": bool(df.isnull().values.any()),
        }), 200

    except FileNotFoundError as error:
        app.logger.error("%s", error)
        return jsonify({"error": "Customer dataset not found"}), 500

    except Exception:
        app.logger.exception("Error validating customer data")
        return jsonify({
            "error": "Unable to validate customer data"
        }), 500


@app.route("/customer-statistics", methods=["GET"])
def customer_statistics():
    try:
        df = load_data()

        return jsonify({
            "total_customers": int(len(df)),
            "columns": list(df.columns),
            "numeric_statistics": (
                df.select_dtypes(include="number")
                .describe()
                .round(2)
                .to_dict()
            ),
        }), 200

    except Exception:
        app.logger.exception("Error generating customer statistics")
        return jsonify({
            "error": "Unable to generate customer statistics"
        }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found"
    }), 404


if __name__ == "__main__":
    app.run(debug=True)