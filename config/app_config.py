"""
Central application configuration.

All environment-specific values are read from environment variables so the same
codebase runs unchanged locally (SQLite) and on Render (PostgreSQL). A local
`.env` file is loaded automatically for development convenience.
"""

import os
import time

# Set timezone to Asia/Kolkata (IST) to ensure correct time on deployments like Render
os.environ['TZ'] = 'Asia/Kolkata'
if hasattr(time, 'tzset'):
    time.tzset()

from dotenv import load_dotenv

# Load variables from a local `.env` file when present (no-op in production
# where Render injects real environment variables).
load_dotenv()

# Absolute path to the project root.
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))  # Adjusted for being inside config/ directory


# ---------------------------------------------------------------------------
# Environment detection
# ---------------------------------------------------------------------------
# Render automatically sets the `RENDER` environment variable on its platform,
# so we can auto-detect production without any manual configuration.
ENVIRONMENT = os.environ.get(
    "ENVIRONMENT",
    "production" if os.environ.get("RENDER") else "development",
).lower()

# IS_PRODUCTION and IS_DEVELOPMENT
IS_PRODUCTION = ENVIRONMENT == "production"
IS_DEVELOPMENT = not IS_PRODUCTION


# ---------------------------------------------------------------------------
# Database configuration
# ---------------------------------------------------------------------------
# Priority:
#   1. DATABASE_URL  -> managed database (e.g. Render PostgreSQL)
#   2. local SQLite  -> ./database/taskflow.db (developer machines)
#
# The database path is never hard-coded for production; it is derived entirely
# from DATABASE_URL, so switching to PostgreSQL later requires zero code changes.
def _normalize_database_url(url: str) -> str:
    """SQLAlchemy requires the ``postgresql://`` scheme, but Render/Heroku hand
    out URLs beginning with ``postgres://``. Normalise them transparently."""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    DATABASE_URI = _normalize_database_url(DATABASE_URL)
else:
    DB_DIR = os.path.join(BASE_DIR, "database")
    os.makedirs(DB_DIR, exist_ok=True)
    DATABASE_URI = f"sqlite:///{os.path.join(DB_DIR, 'taskflow.db')}"

# Convenience flag used by the engine factory to apply SQLite-only settings.
IS_SQLITE = DATABASE_URI.startswith("sqlite")


# ---------------------------------------------------------------------------
# Security / session management
# ---------------------------------------------------------------------------
# STORAGE_SECRET signs NiceGUI's session cookies (equivalent to Flask's
# SECRET_KEY). It MUST be overridden with a strong random value in production.
# Both STORAGE_SECRET and SECRET_KEY are accepted for flexibility.
STORAGE_SECRET = (
    os.environ.get("STORAGE_SECRET")
    or os.environ.get("SECRET_KEY")
    or "taskflow-dev-secret-change-me"
)


# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------
# Render provides the port to bind to via the PORT environment variable.
PORT = int(os.environ.get("PORT", 8080))
HOST = os.environ.get("HOST", "0.0.0.0")


# ---------------------------------------------------------------------------
# Default administrator (used only to seed an empty database)
# ---------------------------------------------------------------------------
# DEFAULT_ADMIN_ID = os.environ.get("DEFAULT_ADMIN_ID", "admin")
DEFAULT_ADMIN_PASSWORD = os.environ.get("DEFAULT_ADMIN_PASSWORD", "Admin@123")
DEFAULT_ADMIN_ID = os.environ.get("DEFAULT_ADMIN_ID", "admin")


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO" if IS_PRODUCTION else "DEBUG").upper()


# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------
# Daily reminder schedule (24-hour clock).
REMINDER_HOUR = 18  # 6:00 PM
REMINDER_MINUTE = 0

# Task status values.
STATUS_PENDING = "Pending"
STATUS_WIP = "Work In Progress"
STATUS_COMPLETED = "Completed"
STATUS_BLOCKED = "Blocked"
STATUS_ON_HOLD = "On Hold"

STATUS_CHOICES = [
    STATUS_PENDING,
    STATUS_WIP,
    STATUS_COMPLETED,
    STATUS_BLOCKED,
    STATUS_ON_HOLD,
]
