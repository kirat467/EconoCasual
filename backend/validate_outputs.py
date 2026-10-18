import pandas as pd
import os

# Validate Customer Insights File
file_path = "data/customer_insights.csv"

print("\n===== CUSTOMER INSIGHTS VALIDATION =====")

if os.path.exists(file_path):
    df = pd.read_csv(file_path)

    print("File exists: Yes")
    print("Total Rows:", len(df))
    print("Total Columns:", len(df.columns))
    print("Missing Values:", df.isnull().sum().sum())
    print("Duplicate Customer IDs:", df["customer_id"].duplicated().sum())

    if df.isnull().sum().sum() == 0:
        print("Missing value check: PASSED")
    else:
        print("Missing value check: REVIEW NEEDED")

    print("\nValidation completed!")

else:
    print("Customer insights file not found.")

print("========================================")