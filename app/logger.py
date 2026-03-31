"""
Simple logging setup — no structlog dependency required.
Falls back gracefully if structlog is not installed.
"""
from __future__ import annotations
import logging
import sys
from typing import Any

# Try structlog; if missing, use stdlib fallback
try:
    import structlog

    def configure_logging(log_level: str = "INFO", json_logs: bool = False) -> None:
        structlog.configure(
            processors=[
                structlog.stdlib.add_log_level,
                structlog.stdlib.add_logger_name,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.dev.ConsoleRenderer(colors=False),
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        logging.basicConfig(
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
            stream=sys.stdout,
            level=getattr(logging, log_level.upper(), logging.INFO),
        )

    def get_logger(name: str = __name__):
        return structlog.get_logger(name)

except ImportError:
    # structlog not available — plain stdlib
    def configure_logging(log_level: str = "INFO", json_logs: bool = False) -> None:
        logging.basicConfig(
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
            stream=sys.stdout,
            level=getattr(logging, log_level.upper(), logging.INFO),
        )

    def get_logger(name: str = __name__) -> logging.Logger:
        return logging.getLogger(name)
