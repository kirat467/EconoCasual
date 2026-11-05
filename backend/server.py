"""Combined backend server for EconoCasual.

Runs Kirat's data API and Sharath's model API
on a single Flask application.

Run from the repository root:

    .\.venv\Scripts\python.exe backend/server.py
"""

import sys
from pathlib import Path

# Add backend directory to Python path
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

# Import the existing Flask app
from app import app  # noqa: E402

# Import Sharath's model API blueprint
from model_api import model_api  # noqa: E402

# Register model API routes
app.register_blueprint(model_api)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=False
    )
