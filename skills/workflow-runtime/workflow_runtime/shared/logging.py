from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, cast


class StructuredLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extra_data: Any = getattr(record, "extra_data", None)
        if isinstance(extra_data, dict):
            log_entry.update(cast(dict[str, Any], extra_data))
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


class JSONLogger:
    def __init__(self, name: str) -> None:
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(StructuredLogFormatter())
            self.logger.addHandler(handler)

    def info(self, message: str, extra: dict[str, Any] | None = None) -> None:
        extra_dict = {"extra_data": extra} if extra else {}
        self.logger.info(message, extra=extra_dict)

    def error(self, message: str, extra: dict[str, Any] | None = None) -> None:
        extra_dict = {"extra_data": extra} if extra else {}
        self.logger.error(message, extra=extra_dict)

    def warning(self, message: str, extra: dict[str, Any] | None = None) -> None:
        extra_dict = {"extra_data": extra} if extra else {}
        self.logger.warning(message, extra=extra_dict)


class LoggerFactory:
    @staticmethod
    def get_logger(name: str) -> JSONLogger:
        return JSONLogger(name)