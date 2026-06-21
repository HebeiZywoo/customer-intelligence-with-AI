"""Lightweight logging setup shared by the pipeline scripts."""

from __future__ import annotations

import logging
import os

_LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_DATE_FORMAT = "%H:%M:%S"


def configure_logging(level: int | None = None) -> logging.Logger:
    """Configure root logging once and return the project logger.

    The level can be overridden with the ``LOG_LEVEL`` environment variable
    (e.g. ``LOG_LEVEL=DEBUG``); it defaults to ``INFO``.
    """

    if level is None:
        level = getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO)
    logging.basicConfig(level=level, format=_LOG_FORMAT, datefmt=_DATE_FORMAT)
    return logging.getLogger("customer_ai")
