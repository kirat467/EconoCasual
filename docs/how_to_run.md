# EconoCasual – How to Run the Project

This guide explains how to set up and run the EconoCasual backend and frontend locally.

All commands are run from the repository root unless specified otherwise.

## 1. Project Requirements

* Python 3.11 recommended.
* pip (Python package manager).
* VS Code or another code editor.
* Git.

## 2. Backend Setup

Open PowerShell in the project root directory.

### Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### Install dependencies

```powershell
pip install -r backend/requirements.txt
```

The full requirements include machine learning and data analysis packages. Some packages may require a compatible Python version.

## 3. Dataset

The main customer dataset is:

```text
data/customers.csv
```

It contains 1,000 synthetic customer records.

Dataset features:

| Column             | Description                  |
| ------------------ | ---------------------------- |
| customer_id        | Unique customer identifier   |
| previous_purchases | Number of previous purchases |
| engagement         | Customer engagement value    |
| discount           | Discount indicator           |
| purchase           | Purchase outcome             |

The project also uses sample JSON files stored in the `docs/` directory for model API responses.

## 4. Run the Combined Backend

The combined backend includes:

* Kirat's customer data APIs.
* Sharath's machine learning APIs.
* Customer data endpoint for frontend integration.
* CORS support for frontend-backend communication.

From the project root, run:

```powershell
.\.venv\Scripts\python.exe backend/server.py
```

The backend will run at:

```text
http://127.0.0.1:8000
```

Keep this terminal open while using the dashboard.

**Important:** Use the Python command above for local Windows development. Gunicorn is intended for Linux-based production environments and does not run natively on Windows.

## 5. Verify Backend APIs

Open a separate PowerShell terminal.

### Data API health check

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected response:

```text
healthy
```

### Model API health check

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

Expected status:

```text
ok
```

### Customer records

```powershell
$customers = Invoke-RestMethod http://127.0.0.1:8000/api/customers
$customers.Count
```

Expected result:

```text
1000
```

## 6. Run the Frontend Dashboard

Open another PowerShell terminal.

Run:

```powershell
.\.venv\Scripts\python.exe -m http.server 5500 --directory frontend
```

Open the dashboard in your browser:

```text
http://127.0.0.1:5500
```

The frontend backend URL is configured in:

```text
frontend/config.js
```

For local testing, the API address is:

```javascript
window.ECONO_CONFIG = { apiBase: "http://127.0.0.1:8000" };
```

The backend must be running before opening the dashboard.

## 7. Backend API Endpoints

### Data API

| Endpoint                       | Purpose                         |
| ------------------------------ | ------------------------------- |
| `/`                            | Backend welcome message         |
| `/health`                      | Data API health check           |
| `/customers`                   | Retrieve customer records       |
| `/api/customers`               | Customer data for frontend      |
| `/purchase-summary`            | Overall purchase statistics     |
| `/discount-analysis`           | Purchase analysis by discount   |
| `/engagement-analysis`         | Purchase analysis by engagement |
| `/previous-purchases-analysis` | Analysis by previous purchases  |
| `/validate-data`               | Dataset validation              |
| `/customer-statistics`         | Numerical customer statistics   |

### Machine Learning API

| Endpoint            | Method     | Purpose                              |
| ------------------- | ---------- | ------------------------------------ |
| `/api/health`       | GET        | Model API health check               |
| `/api/ite`          | GET        | Individual Treatment Effect analysis |
| `/api/uplift-curve` | GET        | Uplift curve analysis                |
| `/api/optimize`     | GET / POST | Budget optimization                  |
| `/api/drift`        | GET / POST | Customer data drift detection        |

## 8. Run Individual Backend Scripts

All commands below are run from the project root.

### Week 1 scripts

```powershell
python backend/causal_dag.py
python backend/baseline_model.py
```

### Generate causal dataset

```powershell
python backend/generate_causal_data.py
```

This creates:

```text
data/customers_causal.csv
```

### Week 2 scripts

```powershell
python backend/casual_model.py
python backend/propensity.py
python backend/refutation.py
python backend/export_sample_json.py
```

These scripts perform causal analysis, propensity matching, refutation testing, and sample JSON generation.

### Week 3 optimizer

```powershell
python backend/optimizer.py --export
```

This generates optimization output files in the `docs/` directory.

**Note:** Some individual scripts require additional dependencies and generated datasets. They are not required every time the dashboard is started.

## 9. Testing

Run the data API tests from the project root:

```powershell
python -m unittest discover -s backend -p "test_app.py" -v
```

Other test files can be executed individually.

The optimizer test requires the `econml` dependency. Its execution may be restricted by the installed Python version and package compatibility.

## 10. Project Directory Structure

```text
EconoCasual/
│
├── backend/
│   ├── app.py
│   ├── server.py
│   ├── model_api.py
│   ├── data_analysis.py
│   ├── optimizer.py
│   ├── optimizer_core.py
│   ├── drift.py
│   ├── requirements.txt
│   └── requirements-api.txt
│
├── data/
│   └── customers.csv
│
├── docs/
│   ├── api_contract.md
│   ├── sample_ite.json
│   ├── sample_uplift_curve.json
│   ├── sample_drift.json
│   ├── optimizer_effects.json
│   └── drift_reference.json
│
├── frontend/
│   ├── index.html
│   ├── script.js
│   ├── style.css
│   └── config.js
│
└── README.md
```

## 11. Troubleshooting

**Backend does not start:**

* Confirm that the virtual environment is activated.
* Install the required dependencies.
* Check that port 8000 is available.
* Run commands from the project root.

**Frontend cannot connect to the backend:**

* Confirm that the backend is running.
* Check the API URL in `frontend/config.js`.
* Verify that the browser can access `http://127.0.0.1:8000/health`.

**Customer dataset not found:**

* Confirm that `data/customers.csv` exists.
* Run commands from the repository root.

**Missing model JSON files:**

* Check the required sample JSON files in `docs/`.
* Run the relevant export scripts if those files need to be regenerated.

**Gunicorn error on Windows:**

* Do not run Gunicorn directly on Windows.
* Use `python backend/server.py` for local development.

## 12. Important Notes

* The dataset contains synthetic customer records.
* Model predictions and optimization results are estimates, not guaranteed real-world outcomes.
* Observational relationships should not automatically be interpreted as causal effects.
* The Flask development server is intended for local testing, not production deployment.
* Public deployment is not required for local project demonstration.

---

Developed collaboratively by the EconoCasual team.
