"""
Structured logging for ADMC Agent.
Writes JSON-formatted log lines to file and human-readable lines to stdout.
"""
from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path
from typing import Optional


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def get_logger(
    name: str = "admc",
    log_file: Optional[str] = None,
    level: str = "INFO",
) -> logging.Logger:
    """Return a configured logger that writes JSON to file and plain text to stdout."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Console handler — human-readable
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(numeric_level)
    ch.setFormatter(
        logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s — %(message)s",
                          datefmt="%Y-%m-%d %H:%M:%S")
    )
    logger.addHandler(ch)

    # File handler — JSON structured
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setLevel(numeric_level)
        fh.setFormatter(_JsonFormatter())
        logger.addHandler(fh)

    logger.propagate = False
    return logger
