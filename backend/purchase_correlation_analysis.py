
from pathlib import Path

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "customers.csv"
REPORT_DIR = BASE_DIR / "reports"
CHART_DIR = REPORT_DIR / "charts"

OUTPUT_FILE = REPORT_DIR / "purchase_correlation_analysis.csv"
CHART_FILE = CHART_DIR / "purchase_correlation_heatmap.png"


def analyze_purchase_correlations():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

    df = pd.read_csv(DATA_FILE)

    columns = [
        "previous_purchases",
        "engagement",
        "discount",
        "purchase",
    ]

    missing = [column for column in columns if column not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if df.empty:
        raise ValueError("Customer dataset is empty.")

    numeric_df = df[columns].apply(pd.to_numeric, errors="raise")

    if numeric_df.isna().any().any():
        raise ValueError("Required columns contain missing values.")

    correlation_matrix = numeric_df.corr().round(3)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    CHART_DIR.mkdir(parents=True, exist_ok=True)

    correlation_matrix.to_csv(OUTPUT_FILE)

    figure, axis = plt.subplots(figsize=(8, 6))

    image = axis.imshow(
        correlation_matrix.values,
        vmin=-1,
        vmax=1,
        cmap="coolwarm",
    )

    axis.set_xticks(range(len(columns)))
    axis.set_xticklabels(columns, rotation=45, ha="right")
    axis.set_yticks(range(len(columns)))
    axis.set_yticklabels(columns)

    for row in range(len(columns)):
        for column in range(len(columns)):
            axis.text(
                column,
                row,
                f"{correlation_matrix.iloc[row, column]:.2f}",
                ha="center",
                va="center",
            )

    axis.set_title("Customer Purchase Correlation Heatmap")
    figure.colorbar(image, ax=axis, label="Correlation")
    figure.tight_layout()
    figure.savefig(CHART_FILE)
    plt.close(figure)

    print("Purchase correlation analysis completed!")
    print(f"Correlation CSV: {OUTPUT_FILE}")
    print(f"Heatmap: {CHART_FILE}")
    print(correlation_matrix.to_string())

    return correlation_matrix


if __name__ == "__main__":
    analyze_purchase_correlations()

