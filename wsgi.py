"""
CivicFix WSGI Entrypoint for Cloud & Production Deployment
==========================================================
Used by Gunicorn, Waitress, uWSGI, and PaaS hosts (Render, Railway, Heroku, Docker).
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR / "backend"))
sys.path.append(str(BASE_DIR / "machine_learning" / "src"))

from app import app
from database import init_db

# Initialize database schema on startup
init_db()

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
