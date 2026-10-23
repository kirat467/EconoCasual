# EconoCasual Backend API Documentation

## 1. Project Overview

EconoCasual is a customer purchasing behaviour analysis project. Its backend provides customer data, purchase statistics, and analytical results through REST API endpoints.

**Base URL:** `http://127.0.0.1:5000`

## 2. Available API Endpoints

All endpoints listed below use the GET method.

### 2.1 Home

* **Endpoint:** `/`
* **Purpose:** Displays the backend's home response.

### 2.2 Health Check

* **Endpoint:** `/health`
* **Purpose:** Checks whether the backend is running.

### 2.3 Customer Data

* **Endpoint:** `/customers`
* **Purpose:** Returns customer records. Filtering and pagination are supported by the backend.

### 2.4 Purchase Summary

* **Endpoint:** `/purchase-summary`
* **Purpose:** Returns overall customer purchase statistics.

Dataset summary:

* Total customers: 1,000
* Total purchases: 573
* Non-purchases: 427
* Purchase rate: 57.3%

### 2.5 Discount Analysis

* **Endpoint:** `/discount-analysis`
* **Purpose:** Summarizes customer purchases by discount category.

### 2.6 Engagement Analysis

* **Endpoint:** `/engagement-analysis`
* **Purpose:** Summarizes customer purchases by engagement level.

### 2.7 Previous Purchase Analysis

* **Endpoint:** `/previous-purchases-analysis`
* **Purpose:** Analyzes purchasing behaviour by previous purchase history.

### 2.8 Data Validation

* **Endpoint:** `/validate-data`
* **Purpose:** Reports dataset validation information, including missing values.

Dataset validation results:

* Total rows: 1,000
* Missing values in the reported columns: 0

### 2.9 Customer Statistics

* **Endpoint:** `/customer-statistics`
* **Purpose:** Returns additional customer dataset statistics.

## 3. How to Run the Backend

Open the project terminal and run:

```powershell
.\.venv\Scripts\python.exe backend/app.py
```

Keep the terminal running while testing the API.

## 4. How to Test an Endpoint

Open a second terminal and run:

```powershell
.\.venv\Scripts\python.exe -c "import requests; r=requests.get('http://127.0.0.1:5000/health', timeout=5); print(r.status_code); print(r.text)"
```

A status code of `200` indicates a successful HTTP response.

## 5. Automated Testing

Run the complete backend test suite using:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend -p "test_*.py" -v
```

The latest reported test run contained **86 tests**. Confirm the terminal ends with `OK` before reporting the entire suite as passing.

## 6. Notes

* The local base URL is intended for development and testing.
* API response fields may vary by endpoint.
* Confirm the implementation in `backend/app.py` before documenting additional query parameters.
* Descriptive analysis identifies patterns in the dataset but does not prove causation.
* Final integration of team branches is planned for Week 4.
