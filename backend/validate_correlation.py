import pandas as pd
import os

# Validate Correlation Matrix
file_path = "data/correlation_matrix.csv"

print("\n===== CORRELATION MATRIX VALIDATION =====")

if os.path.exists(file_path):
    df = pd.read_csv(file_path, index_col=0)

    print("File exists: Yes")
    print("Rows:", df.shape[0])
    print("Columns:", df.shape[1])
    print("Missing Values:", df.isnull().sum().sum())
    print("\nCorrelation Matrix:")
    print(df.round(2))

    print("\nValidation completed!")

else:
    print("Correlation matrix file not found.")

print("=========================================")