from pathlib import Path

import numpy as np
import pandas as pd


# Project ke reports folder ka path.
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "reports" / "correlation_matrix.csv"


def load_correlation_matrix(file_path=DATA_FILE):
    """Load the correlation matrix from a CSV file."""
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Correlation matrix not found: {file_path}"
        )

    return pd.read_csv(file_path, index_col=0)


def validate_correlation_matrix(df, tolerance=0.01):
    """Validate the structure and values of a correlation matrix."""

    errors = []

    # Matrix must not be empty.
    if df.empty:
        errors.append({"type": "empty_matrix"})

        return {
            "is_valid": False,
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "errors": errors,
        }

    # Rows and columns must be equal.
    if df.shape[0] != df.shape[1]:
        errors.append({"type": "matrix_not_square"})

    # Row and column labels must match.
    if not df.index.equals(df.columns):
        errors.append({"type": "row_column_labels_mismatch"})

    # All values must be numeric.
    numeric_df = df.apply(pd.to_numeric, errors="coerce")

    if numeric_df.isna().any().any():
        errors.append({"type": "missing_or_non_numeric_values"})

    else:
        values = numeric_df.to_numpy(dtype=float)

        # Values must be finite.
        if not np.isfinite(values).all():
            errors.append({"type": "non_finite_values"})

        else:
            # Correlation values must lie between -1 and +1.
            if ((values < -1 - tolerance) |
                    (values > 1 + tolerance)).any():
                errors.append({"type": "values_out_of_range"})

            # A correlation matrix must be symmetric.
            if not np.allclose(
                values,
                values.T,
                atol=tolerance,
                rtol=0
            ):
                errors.append({"type": "matrix_not_symmetric"})

            # Diagonal values should be approximately 1.
            if not np.allclose(
                np.diag(values),
                1,
                atol=tolerance,
                rtol=0
            ):
                errors.append({"type": "invalid_diagonal_values"})

    return {
        "is_valid": len(errors) == 0,
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "missing_values": int(df.isnull().sum().sum()),
        "errors": errors,
    }


def run_validation(file_path=DATA_FILE):
    """Load, validate and display the correlation matrix."""

    df = load_correlation_matrix(file_path)
    result = validate_correlation_matrix(df)

    print("\n===== CORRELATION MATRIX VALIDATION =====")
    print(f"Rows: {result['rows']}")
    print(f"Columns: {result['columns']}")
    print(f"Missing Values: {result['missing_values']}")
    print(f"Validation Status: {'PASSED' if result['is_valid'] else 'FAILED'}")

    if result["errors"]:
        print("\nValidation Errors:")
        for error in result["errors"]:
            print(error)

    print("\nCorrelation Matrix:")
    print(df.round(2))

    print("\nValidation completed!")
    print("=========================================")

    return result


if __name__ == "__main__":
    try:
        run_validation()
    except FileNotFoundError as error:
        print(f"ERROR: {error}")
