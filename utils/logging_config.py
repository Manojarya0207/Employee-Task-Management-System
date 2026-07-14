"""
Application logging configuration.

Logs are written to both the console (captured by Render's log stream) and a
rotating file under ``logs/`` so history is retained without growing unbounded.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

from config import LOG_DIR, LOG_LEVEL

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def configure_logging() -> logging.Logger:
    """Configure root logging once and return the application logger."""
    os.makedirs(LOG_DIR, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(LOG_LEVEL)

    # Avoid attaching duplicate handlers if called more than once (e.g. under
    # the auto-reloader).
    if not root.handlers:
        formatter = logging.Formatter(_LOG_FORMAT)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root.addHandler(console_handler)

        file_handler = RotatingFileHandler(
            os.path.join(LOG_DIR, "taskflow.log"),
            maxBytes=1_000_000,  # 1 MB per file
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    return logging.getLogger("taskflow")
