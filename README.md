# EconoCasual 🛍️

A customer purchase prediction and causal analysis project focused on understanding purchasing behaviour, customer engagement, discounts, and customer targeting.

## About the Project

EconoCasual uses data analysis and machine learning to study customer purchasing behaviour and estimate how customers may respond to discounts.

The project combines data analysis, machine learning, backend APIs, and an interactive frontend dashboard to provide customer insights and support data-driven discount decisions.

## Project Objectives

* Analyze customer purchasing behaviour.
* Understand relationships between customer engagement, discounts, and purchases.
* Develop machine learning models for purchase analysis.
* Identify customer segments based on estimated discount response.
* Optimize discount allocation within a given budget.
* Monitor changes in customer data distributions.
* Display customer insights through an interactive dashboard.

## Dataset

The project uses a synthetic dataset containing 1,000 fictional customer records.

### Dataset Features

| Column               | Description                  |
| -------------------- | ---------------------------- |
| `customer_id`        | Unique customer identifier   |
| `previous_purchases` | Number of previous purchases |
| `engagement`         | Customer engagement value    |
| `discount`           | Discount indicator           |
| `purchase`           | Purchase outcome             |

The dataset is intended for development, analysis, and testing. It does not contain real customer records.

## Team Members and Responsibilities

| Team Member | Primary Responsibility                   |
| ----------- | ---------------------------------------- |
| Kirat       | Data Analysis and Project Coordination   |
| Sharath     | Machine Learning and Purchase Prediction |
| Kailash     | Frontend and User Interface              |

## Project Status

The project has completed local integration and functional testing of its main components.

Completed work includes:

* Customer data analysis and validation.
* Backend REST API development.
* Machine learning API integration.
* Individual Treatment Effect (ITE) analysis.
* Uplift curve analysis.
* Customer segmentation.
* Budget optimization.
* Data drift detection.
* Frontend dashboard integration.
* Charts, filters, customer table, search, and pagination testing.
* CSV upload, preview, and export testing.

Public deployment and production configuration remain separate tasks.

## Future Improvements

* Deploy the backend and frontend publicly.
* Configure production API URLs.
* Improve model performance and evaluate it on additional datasets.
* Monitor model performance and data drift over time.
* Improve dashboard functionality and user experience.

---

# EconoCasual Backend

## Overview

The EconoCasual backend provides REST APIs for customer records, statistical analysis, dataset validation, and machine learning functionality.

## Requirements

* Python
* Flask
* Flask-CORS
* Project dataset: `data/customers.csv`

## Run the Combined Backend

Open PowerShell in the project root directory and run:

```powershell
.\.venv\Scripts\python.exe backend/server.py
```

The combined backend runs locally at:

```text
http://127.0.0.1:8000
```

This server integrates the data API and machine learning API.

## Frontend Setup

Open a separate terminal and run:

```powershell
.\.venv\Scripts\python.exe -m http.server 5500 --directory frontend
```

Open the dashboard at:

```text
http://127.0.0.1:5500
```

The frontend backend address is configured in `frontend/config.js`.

For public deployment, replace the local backend URL with the deployed backend URL.

## Data API Endpoints

All endpoints below use GET.

| Endpoint                       | Purpose                                |
| ------------------------------ | -------------------------------------- |
| `/`                            | Backend welcome message                |
| `/health`                      | Backend health check                   |
| `/customers`                   | Retrieve customer records              |
| `/api/customers`               | Customer data for frontend integration |
| `/purchase-summary`            | Overall purchase statistics            |
| `/discount-analysis`           | Purchase analysis by discount          |
| `/engagement-analysis`         | Purchase analysis by engagement        |
| `/previous-purchases-analysis` | Analysis by previous purchases         |
| `/validate-data`               | Dataset validation                     |
| `/customer-statistics`         | Numerical customer statistics          |

## Machine Learning API Endpoints

| Endpoint            | Method     | Purpose                              |
| ------------------- | ---------- | ------------------------------------ |
| `/api/health`       | GET        | Model API health check               |
| `/api/ite`          | GET        | Individual Treatment Effect analysis |
| `/api/uplift-curve` | GET        | Uplift curve analysis                |
| `/api/optimize`     | GET / POST | Budget optimization                  |
| `/api/drift`        | GET / POST | Customer data drift detection        |

## Customer API

The `/customers` endpoint supports pagination and filtering.

### Pagination Example

```text
/customers?page=1&per_page=10
```

### Filtering Examples

```text
/customers?discount=1
/customers?engagement=1
/customers?purchase=1
```

Filters can also be combined:

```text
/customers?discount=1&purchase=1
```

## Data Validation

The `/validate-data` endpoint checks the dataset and reports missing values and dataset dimensions.

The `/customer-statistics` endpoint provides numerical statistics for customer data.

## Testing

Run the data API tests from the project root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend -p "test_app.py" -v
```

Other backend test files can be executed individually.

**Testing note:** The optimizer test could not be executed in the current Python 3.14 environment because its `econml` dependency could not be installed due to compatibility limitations.

## Important Notes

* The dataset contains synthetic customer records.
* Model predictions and optimization results are estimates, not guaranteed real-world outcomes.
* Observational relationships should not automatically be interpreted as causal effects.
* The Flask development server is intended for local testing, not production deployment.
* Production deployment requires an appropriate WSGI server and deployed API configuration.

---

Developed collaboratively by the EconoCasual team.
