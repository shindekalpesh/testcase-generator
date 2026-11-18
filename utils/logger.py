"""
Structured logging.

SSOT section: §20

Usage in any module:

    import logging
    from utils.logger import log_action

    logger = logging.getLogger(__name__)
    log_action(logger, logging.INFO, "BoundaryGenerationCompleted", TestCaseCount=6)

Produces one line:

    2026-11-18 16:42:03 | INFO | generators.boundary_generator | Action=BoundaryGenerationCompleted | TestCaseCount=6
"""

import logging

from config import config

# Marker so setup_logging() never attaches a second handler (which would
# write every line twice) if it is called more than once.
_HANDLER_MARKER = "_testcase_generator_handler"


def setup_logging(log_file=config.LOG_FILE, level=logging.INFO):
    """Attach the file handler once. Call this at program start (main.py)."""
    root = logging.getLogger()

    if any(getattr(h, _HANDLER_MARKER, False) for h in root.handlers):
        return

    log_file.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(
        logging.Formatter(config.LOG_FORMAT, datefmt=config.LOG_DATE_FORMAT)
    )
    setattr(handler, _HANDLER_MARKER, True)

    root.addHandler(handler)
    root.setLevel(level)


def format_action(action, **fields):
    """Build 'Action=<action> | Key=Value | ...' in the order fields are given."""
    parts = [f"Action={action}"]
    parts.extend(f"{key}={value}" for key, value in fields.items())
    return " | ".join(parts)


def log_action(logger, level, action, **fields):
    """Log one structured message at the given level."""
    logger.log(level, format_action(action, **fields))
