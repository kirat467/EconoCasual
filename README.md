# EconoCasual 🛍️

A customer purchase prediction project focused on understanding purchasing behaviour, affordability, convenience, and customer engagement.

## About the Project

EconoCasual uses data analysis and machine learning to study customer purchasing behaviour and predict the likelihood of a purchase. The project aims to understand how previous purchases, customer engagement, and discounts relate to purchasing decisions.

## Project Objectives

* Analyze customer purchasing behaviour.
* Understand the relationship between customer engagement and purchases.
* Study the impact of discounts on purchase rates.
* Develop and evaluate a machine learning model for purchase prediction.
* Build a user-friendly frontend to display customer insights and predictions.
* Provide backend APIs for customer data, statistical analysis, and dataset validation.

## Dataset

The project currently uses a synthetic dataset containing 1,000 fictional customer records.

### Dataset Features

| Column               | Description                      |
| -------------------- | -------------------------------- |
| `customer_id`        | Unique identifier for a customer |
| `previous_purchases` | Number of previous purchases     |
| `engagement`         | Customer engagement value        |
| `discount`           | Discount indicator or value      |
| `purchase`           | Purchase outcome                 |

The dataset is intended for development, analysis, and testing. It does not contain real customer records.

## Team Members and Responsibilities

| Team Member | Primary Responsibility                   |
| ----------- | ---------------------------------------- |
| Kirat       | Data Analysis and Project Coordination   |
| Sharath     | Machine Learning and Purchase Prediction |
| Kailash     | Frontend and User Interface              |

**Note:** Team members retain their assigned responsibilities throughout the project. Integration of the different components is planned for Week 4.

## Project Status

The project is currently under development. Data analysis, machine learning, and frontend development are being developed progressively before integration.

## Future Improvements

* Improve data quality and analysis.
* Train and evaluate purchase prediction models.
* Evaluate model performance using appropriate metrics.
* Integrate the machine learning model with the backend.
* Connect the frontend to backend APIs.
* Develop a dashboard to display customer insights and predictions.

---

# EconoCasual Backend

## Overview

The EconoCasual backend provides REST API endpoints for retrieving customer records, analyzing purchasing behaviour, calculating statistics, and validating the dataset.

## Requirements

* Python
* Flask
* Project dataset: `data/customers.csv`

## Run the Backend

Open a terminal in the project root directory and run:

```powershell
.\.venv\Scripts\python.exe backend\app.py
```

Use the local server address displayed in the terminal to access the API.

## API Endpoints

All endpoints below use the HTTP `GET` method.

| Endpoint                       | Purpose                                    |
| ------------------------------ | ------------------------------------------ |
| `/`                            | Check project status                       |
| `/health`                      | Check backend health                       |
| `/customers`                   | Retrieve customer records                  |
| `/purchase-summary`            | Get overall purchase statistics            |
| `/discount-analysis`           | Analyze purchasing behaviour by discount   |
| `/engagement-analysis`         | Analyze purchasing behaviour by engagement |
| `/previous-purchases-analysis` | Analyze previous purchase behaviour        |
| `/validate-data`               | Check dataset quality                      |
| `/customer-statistics`         | Get numerical column statistics            |

## Customer API

The `/customers` endpoint supports pagination and filtering.

### Pagination

Example:

```text
/customers?page=1&per_page=10
```

* `page`: Page number.
* `per_page`: Number of records requested per page.

### Filtering

Examples:

```text
/customers?discount=1
/customers?engagement=1
/customers?purchase=1
```

* `discount`: Filter customers by discount value.
* `engagement`: Filter customers by engagement value.
* `purchase`: Filter by purchase outcome.

Filters can also be combined when supported by the endpoint:

```text
/customers?discount=1&purchase=1
```

Invalid filter values are expected to return an HTTP `400 Bad Request` response.

## Data Validation

The `/validate-data` endpoint checks the dataset and returns validation information, including the total number of rows and missing values by column.

The `/customer-statistics` endpoint provides numerical statistics for customer data.

## Data Columns

The dataset contains these columns:

* `customer_id`
* `previous_purchases`
* `engagement`
* `discount`
* `purchase`

## Testing

Run the backend API tests from the project root directory:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend -p "test_app.py" -v
```

To run all backend test files:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend -p "test_*.py" -v
```

## Notes

* The dataset must be available at `data/customers.csv`.
* Analysis and validation endpoints depend on the dataset's expected columns and values.
* The dataset contains synthetic records for project development and testing.
* The project is under development, and API functionality may change as new features are added.

---

Developed collaboratively by the EconoCasual team.
