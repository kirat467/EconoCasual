# EconoCasual
A project focused on combining affordability, convenience, and a user-friendly experience to deliver practical solutions for everyday needs.
EconoCasual 🛍️

About the Project

EconoCasual is a customer purchase prediction project that uses data analysis and machine learning to study customer purchasing behaviour and predict the likelihood of a purchase.

Objectives

- Analyze customer purchasing behaviour.
- Understand the relationship between customer engagement and purchases.
- Study the impact of discounts on purchase rates.
- Develop a machine learning model to predict customer purchases.
- Build a user-friendly frontend to display predictions.


Dataset

The project currently uses a synthetic dataset containing 1,000 fictional customer records.

Dataset features:

- "customer_id"
- "previous_purchases"
- "engagement"
- "discount"
- "purchase"

The dataset is intended for project development and testing.

Team Members and Responsibilities

Team Member| Primary Responsibility
Kirat| Data Analysis and Project Coordination
Sharath| Machine Learning and Purchase Prediction
Kailash| Frontend and User Interface

Note: Team members will rotate responsibilities weekly so everyone can gain experience in all three areas.


Project Status

Currently in development. Data analysis, machine learning, and frontend development will be completed and integrated progressively.

Future Improvements

- Improve data quality and analysis.
- Train and evaluate purchase prediction models.
- Integrate the model with the frontend.
- Create a dashboard for displaying predictions.

---

Developed collaboratively by the EconoCasual team.

# EconoCasual Backend

## Overview

The EconoCasual backend provides APIs for customer data, purchasing behavior, data analysis, and dataset validation.

## Requirements

* Python
* Flask
* Project customer dataset: `data/customers.csv`

## Run the Backend

From the project root directory, run:

```powershell
.\.venv\Scripts\python.exe backend\app.py
```

The local development server will display its address in the terminal.

## API Endpoints

| Method | Endpoint                       | Purpose                                   |
| ------ | ------------------------------ | ----------------------------------------- |
| GET    | `/`                            | Check project status                      |
| GET    | `/health`                      | Check backend health                      |
| GET    | `/customers`                   | Retrieve customer records                 |
| GET    | `/purchase-summary`            | Get overall purchase statistics           |
| GET    | `/discount-analysis`           | Analyze purchases by discount             |
| GET    | `/previous-purchases-analysis` | Analyze previous purchase behavior        |
| GET    | `/engagement-analysis`         | Analyze purchasing behavior by engagement |
| GET    | `/validate-data`               | Check dataset quality                     |
| GET    | `/customer-statistics`         | Get numerical column statistics           |

## Customer Pagination

The `/customers` endpoint supports `limit` and `offset`.

Example:

`/customers?limit=10&offset=20`

* `limit`: Number of records to return; allowed range is 1–100.
* `offset`: Number of records to skip; must be zero or greater.

## Data Columns

The dataset contains:

* `customer_id`
* `previous_purchases`
* `engagement`
* `discount`
* `purchase`

## Testing

From the project root, run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend -p "test_app.py" -v
```

## Notes

* The customer dataset must exist at `data/customers.csv`.
* Analysis endpoints depend on the dataset's column names and values.
* This project is under development; endpoint behavior may change as features are added.

