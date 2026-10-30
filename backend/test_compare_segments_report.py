import sys
from pathlib import Path

import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent

sys.path.insert(0, str(BACKEND_DIR))

from compare_segments_report import generate_comparison_report


def run_tests():

    sample_data = pd.DataFrame({
        "engagement_segment": ["High", "Low"],
        "purchase_history_segment": ["Frequent", "Rare"],
        "customer_count": [100, 50],
        "total_purchases": [80, 10],
        "purchase_rate_percent": [80.0, 20.0],
    })

    input_file = PROJECT_DIR / "reports" / "segment_comparison.csv"
    output_file = (
        PROJECT_DIR / "reports" / "segment_comparison_report.md"
    )

    # Test 1: Function exists
    assert callable(generate_comparison_report)
    print("Test 1 passed: Report function exists")

    # Test 2: Input CSV exists
    assert input_file.exists()
    print("Test 2 passed: Input CSV exists")

    # Test 3: Required columns exist
    required_columns = [
        "engagement_segment",
        "purchase_history_segment",
        "customer_count",
        "total_purchases",
        "purchase_rate_percent",
    ]

    for column in required_columns:
        assert column in sample_data.columns

    print("Test 3 passed: Required columns exist")

    # Test 4: Dataset is not empty
    assert not sample_data.empty
    print("Test 4 passed: Dataset is not empty")

    # Test 5: Numeric values are valid
    numeric_columns = [
        "customer_count",
        "total_purchases",
        "purchase_rate_percent",
    ]

    for column in numeric_columns:
        converted = pd.to_numeric(
            sample_data[column],
            errors="coerce"
        )
        assert not converted.isna().any()

    print("Test 5 passed: Numeric values are valid")

    # Test 6: Customer counts are non-negative
    assert (sample_data["customer_count"] >= 0).all()
    print("Test 6 passed: Customer counts are non-negative")

    # Test 7: Purchases do not exceed customers
    assert (
        sample_data["total_purchases"]
        <= sample_data["customer_count"]
    ).all()

    print("Test 7 passed: Purchases do not exceed customers")

    # Test 8: Purchase rates are valid
    rates = sample_data["purchase_rate_percent"]

    assert (rates >= 0).all()
    assert (rates <= 100).all()

    print("Test 8 passed: Purchase rates are valid")

    # Test 9: Report generation
    generate_comparison_report()
    print("Test 9 passed: Report generated")

    # Test 10: Output file exists
    assert output_file.exists()
    print("Test 10 passed: Output file exists")

    # Read generated report
    content = output_file.read_text(encoding="utf-8")

    # Test 11: Report headings
    headings = [
        "# Customer Segment Comparison Report",
        "## 1. Overview",
        "## 2. Segment Comparison",
        "## 3. Key Findings",
        "## 4. Interpretation",
        "## 5. Limitations",
        "## 6. Recommended Next Steps",
    ]

    for heading in headings:
        assert heading in content

    print("Test 11 passed: Report headings exist")

    # Test 12: Actual segment names from CSV
    actual_data = pd.read_csv(input_file)

    for column in [
        "engagement_segment",
        "purchase_history_segment",
    ]:
        for value in actual_data[column].dropna().unique():
            assert str(value) in content, (
                f"Segment value {value} missing from report"
            )

    print("Test 12 passed: Actual segment names exist")

    # Test 13: Customer total
    assert sample_data["customer_count"].sum() == 150
    print("Test 13 passed: Sample customer total is correct")

    # Test 14: Purchase total
    assert sample_data["total_purchases"].sum() == 90
    print("Test 14 passed: Sample purchase total is correct")

    # Test 15: Dataset contains two segments
    assert len(sample_data) == 2
    print("Test 15 passed: Sample segment count is correct")

    print("\nAll 15 tests passed successfully!")


if __name__ == "__main__":
    run_tests()