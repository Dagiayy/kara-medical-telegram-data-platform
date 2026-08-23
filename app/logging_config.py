"""Structured logging setup shared by every entrypoint in the platform.

Gives every pipeline stage a consistent, greppable log format and (when
`log_json=True`) machine-parseable JSON lines suitable for shipping to a log
aggregator, without adding an extra dependency.
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        extra = getattr(record, "extra_fields", None)
        if extra:
            payload.update(extra)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(name: str, level: str = "INFO", json_output: bool = False) -> logging.Logger:
    """Configure and return a named logger with a single stream handler.

    Safe to call multiple times (e.g. once per module) -- handlers are not
    duplicated on repeated calls for the same logger name.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level.upper())

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        if json_output:
            handler.setFormatter(JsonFormatter())
        else:
            handler.setFormatter(
                logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
            )
        logger.addHandler(handler)
        logger.propagate = False

    return logger
