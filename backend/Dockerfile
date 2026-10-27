# Packages the EconoCausal model API.
# Build from the repository root:   docker build -f backend/Dockerfile -t econocausal-api .
# Run:                              docker run -p 8000:8000 econocausal-api
# Then open http://localhost:8000/api/health
FROM python:3.11-slim

WORKDIR /app
COPY backend/requirements-api.txt backend/requirements-api.txt
RUN pip install --no-cache-dir -r backend/requirements-api.txt

# only what the API needs: the code and the saved model results
COPY backend/model_api.py backend/optimizer_core.py backend/drift.py backend/
COPY docs/sample_ite.json docs/sample_uplift_curve.json docs/sample_drift.json \
     docs/drift_reference.json docs/optimizer_effects.json docs/

EXPOSE 8000
CMD ["gunicorn", "--chdir", "backend", "--bind", "0.0.0.0:8000", "--workers", "2", "model_api:create_app()"]
