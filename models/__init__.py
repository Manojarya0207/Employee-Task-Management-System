"""
Database engine and session factory.

The engine is built from ``DATABASE_URI`` (see ``config.py``) so it works with
both SQLite locally and PostgreSQL in production without any code changes.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import DATABASE_URI, IS_SQLITE

# ``pool_pre_ping`` transparently recycles stale connections — important for
# managed PostgreSQL instances that drop idle connections.
engine_kwargs = {"pool_pre_ping": True}

if IS_SQLITE:
    # Required for SQLite when accessed from multiple threads (web server).
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URI, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Yield a database session and guarantee it is closed afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
