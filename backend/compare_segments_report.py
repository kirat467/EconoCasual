from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "reports" / "segment_comparison.csv"
OUTPUT_FILE = BASE_DIR / "reports" / "segment_comparison_report.md"


def generate_comparison_report():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            "segment_comparison.csv not found. "
            "Run backend/compare_segments.py first."
        )

    df = pd.read_csv(INPUT_FILE)

    required_columns = [
        "engagement_segment",
        "purchase_history_segment",
        "customer_count",
        "total_purchases",
        "purchase_rate_percent",
    ]

    missing = [column for column in required_columns if column not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    total_customers = int(df["customer_count"].sum())
    total_purchases = int(df["total_purchases"].sum())

    overall_purchase_rate = (
        total_purchases / total_customers * 100
        if total_customers > 0
        else 0
    )

    highest_rate = df.loc[df["purchase_rate_percent"].idxmax()]
    lowest_rate = df.loc[df["purchase_rate_percent"].idxmin()]

    # Build Markdown table without requiring extra packages
    table_lines = [
        "| " + " | ".join(df.columns) + " |",
        "| " + " | ".join(["---"] * len(df.columns)) + " |",
    ]

    for _, row in df.iterrows():
        values = []
        for value in row:
            if pd.isna(value):
                values.append("")
            elif isinstance(value, float):
                values.append(f"{value:.2f}")
            else:
                values.append(str(value))

        table_lines.append("| " + " | ".join(values) + " |")

    report = [
        "# Customer Segment Comparison Report",
        "",
        "## 1. Overview",
        "",
        f"- Total customers represented in comparison: {total_customers}",
        f"- Total purchases: {total_purchases}",
        f"- Overall purchase rate: {overall_purchase_rate:.2f}%",
        "",
        "## 2. Segment Comparison",
        "",
        *table_lines,
        "",
        "## 3. Key Findings",
        "",
        f"- Highest purchase-rate combination: "
        f"{highest_rate['engagement_segment']} + "
        f"{highest_rate['purchase_history_segment']} "
        f"({highest_rate['purchase_rate_percent']:.2f}%).",
        f"- Lowest purchase-rate combination: "
        f"{lowest_rate['engagement_segment']} + "
        f"{lowest_rate['purchase_history_segment']} "
        f"({lowest_rate['purchase_rate_percent']:.2f}%).",
        "",
        "## 4. Interpretation",
        "",
        "These results describe associations between customer segments and "
        "purchasing behavior. They do not establish that engagement or previous "
        "purchases cause a customer to buy.",
        "",
        "## 5. Limitations",
        "",
        "- Segment purchase rates depend on the available dataset.",
        "- Small customer groups can produce unstable rates.",
        "- Findings should be validated before business decisions are made.",
        "",
        "## 6. Recommended Next Steps",
        "",
        "- Compare these findings with the purchase-prediction model.",
        "- Review segment sizes alongside purchase rates.",
        "- Re-evaluate the results when new customer data becomes available.",
        "",
    ]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text("\n".join(report), encoding="utf-8")

    print("Segment comparison report generated successfully!")
    print(f"Report saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_comparison_report()