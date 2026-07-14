"""
utils/db_migration.py

Safe, startup-time migration utility.

Adds the four new registration-approval columns to the 'employees' table if they
do not already exist.  Works for both SQLite (development) and PostgreSQL
(production) without requiring Alembic.

Call ``run_migrations()`` once from ``main.py`` right after ``init_db()``.
"""

import logging
from sqlalchemy import inspect, text
from models import engine, SessionLocal
from models.employee import Employee  # noqa: F401 — ensure model is imported

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# New columns to add  (column_name → SQL definition string)
# ---------------------------------------------------------------------------
_NEW_COLUMNS = {
    "registration_status": "VARCHAR(20) NOT NULL DEFAULT 'approved'",
    "approved_at":         "DATETIME",
    "rejected_at":         "DATETIME",
    "rejection_reason":    "TEXT",
}


def _existing_columns(connection) -> set[str]:
    """Return the set of column names currently in the employees table."""
    inspector = inspect(connection)
    cols = inspector.get_columns("employees")
    return {c["name"] for c in cols}


def run_migrations():
    """
    Idempotent migration runner.

    1. Adds any missing columns to the employees table.
    2. Backfills ``registration_status = 'approved'`` for every row that still
       has NULL in that column (i.e., employees created before this migration).
    """
    logger.info("Running database migrations...")

    with engine.connect() as conn:
        existing = _existing_columns(conn)

        for col_name, col_def in _NEW_COLUMNS.items():
            if col_name not in existing:
                logger.info("Adding column '%s' to employees table...", col_name)
                try:
                    conn.execute(
                        text(f"ALTER TABLE employees ADD COLUMN {col_name} {col_def}")
                    )
                    conn.commit()
                    logger.info("Column '%s' added successfully.", col_name)
                except Exception as exc:
                    # Column may already exist in a race condition; log and continue.
                    logger.warning("Could not add column '%s': %s", col_name, exc)
                    conn.rollback()
            else:
                logger.debug("Column '%s' already exists — skipping.", col_name)

    # ------------------------------------------------------------------
    # Backfill: any existing employee row that has NULL registration_status
    # (SQLite ignores DEFAULT on ALTER TABLE for existing rows) gets 'approved'.
    # ------------------------------------------------------------------
    db = SessionLocal()
    try:
        result = db.execute(
            text(
                "UPDATE employees SET registration_status = 'approved' "
                "WHERE registration_status IS NULL"
            )
        )
        if result.rowcount:
            db.commit()
            logger.info(
                "Backfilled registration_status='approved' for %d existing employee(s).",
                result.rowcount,
            )
        else:
            logger.debug("No backfill needed for registration_status.")
    except Exception as exc:
        logger.error("Backfill error: %s", exc)
        db.rollback()
    finally:
        db.close()

    logger.info("Database migrations complete.")
