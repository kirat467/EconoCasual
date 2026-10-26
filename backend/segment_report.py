from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
SUMMARY_FILE = BASE_DIR / "reports" / "customer_segments_summary.csv"
OUTPUT_FILE = BASE_DIR / "reports" / "customer_segmentation_report.md"


def generate_report():
    if not SUMMARY_FILE.exists():
        raise FileNotFoundError(
            "Segment summary not found. Run backend/customer_segments.py first."
        )

    summary = pd.read_csv(SUMMARY_FILE)

    required_columns = [
        "engagement_segment",
        "purchase_history_segment",
        "total_customers",
        "total_purchases",
        "average_engagement",
        "average_previous_purchases",
        "purchase_rate_percent",
    ]

    missing = [column for column in required_columns if column not in summary.columns]

    if missing:
        raise ValueError(f"Missing columns in summary: {missing}")

    total_customers = int(summary["total_customers"].sum())
    total_purchases = int(summary["total_purchases"].sum())

    overall_rate = (
        total_purchases / total_customers * 100
        if total_customers > 0
        else 0
    )

    # Create Markdown table without requiring tabulate
    table_lines = [
        "| " + " | ".join(summary.columns) + " |",
        "| " + " | ".join(["---"] * len(summary.columns)) + " |",
    ]

    for _, row in summary.iterrows():
        values = []
        for column in summary.columns:
            value = row[column]
            if pd.isna(value):
                values.append("")
            elif isinstance(value, float):
                values.append(f"{value:.2f}")
            else:
                values.append(str(value))
        table_lines.append("| " + " | ".join(values) + " |")

    ranked = summary.sort_values(
        by=["purchase_rate_percent", "total_customers"],
        ascending=[False, False],
    )

    lines = [
        "# Customer Segmentation Analysis Report",
        "",
        "## 1. Overview",
        "",
        "This report summarizes customer purchasing behavior across engagement "
        "and previous-purchase-history segments.",
        "",
        f"- Total customers analyzed: {total_customers}",
        f"- Total purchases: {total_purchases}",
        f"- Overall purchase rate: {overall_rate:.2f}%",
        "",
        "## 2. Segment Summary",
        "",
        *table_lines,
        "",
        "## 3. Key Findings",
        "",
    ]

    if not ranked.empty:
        highest = ranked.iloc[0]
        lines.extend([
            "- Highest purchase-rate segment combination: "
            f"{highest['engagement_segment']} + "
            f"{highest['purchase_history_segment']}.",
            f"- Purchase rate for this combination: "
            f"{highest['purchase_rate_percent']:.2f}%.",
            f"- Customers in this combination: "
            f"{int(highest['total_customers'])}.",
        ])
    else:
        lines.append("- No segment data was available for analysis.")

    lines.extend([
        "",
        "## 4. Interpretation",
        "",
        "Compare purchase rates across segments to understand how engagement "
        "and purchase history relate to purchasing behavior. These comparisons "
        "show associations, not proof of cause and effect.",
        "",
        "## 5. Limitations",
        "",
        "- Results describe the available dataset only.",
        "- Segment comparisons do not prove causation.",
        "- Small segments may have less reliable purchase-rate estimates.",
        "",
        "## 6. Suggested Next Steps",
        "",
        "- Compare findings with the baseline purchase-prediction model.",
        "- Review segment sizes before making business decisions.",
        "- Validate the results on additional customer data.",
        "",
    ])

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")

    print("Customer segmentation report generated successfully!")
    print(f"Total customers analyzed: {total_customers}")
    print(f"Total purchases: {total_purchases}")
    print(f"Overall purchase rate: {overall_rate:.2f}%")
    print(f"Report saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_report()