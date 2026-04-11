"""Production-grade logging configuration for the application.

Features:
- File-based logging with automatic rotation
- Console output for development
- Separate log files for different components
- Structured logging with timestamps
- Debug, info, warning, and error levels
"""

from __future__ import annotations

import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime


# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Log file paths
APP_LOG_FILE = LOGS_DIR / "app.log"
ROUTER_LOG_FILE = LOGS_DIR / "router.log"
DATABASE_LOG_FILE = LOGS_DIR / "database.log"
PARSER_LOG_FILE = LOGS_DIR / "parser.log"
DETECTION_LOG_FILE = LOGS_DIR / "detection.log"

# Logging configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Maximum file size: 10MB
MAX_LOG_SIZE = 10 * 1024 * 1024

# Number of backup log files to keep
BACKUP_COUNT = 5


def setup_logging() -> None:
    """Configure logging for the entire application.
    
    Sets up:
    - Root logger with file and console handlers
    - Per-module loggers with specific handlers
    - Rotating file handlers to prevent disk bloat
    - Formatted output with timestamps
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # ============================================
    # 1. ROOT LOGGER - General Application Logs
    # ============================================
    app_file_handler = logging.handlers.RotatingFileHandler(
        APP_LOG_FILE,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
    )
    app_file_handler.setLevel(logging.DEBUG)
    app_file_handler.setFormatter(formatter)
    root_logger.addHandler(app_file_handler)

    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # ============================================
    # 2. API ROUTER LOGGER - Router-specific logs
    # ============================================
    router_logger = logging.getLogger("app.api")
    router_logger.setLevel(logging.DEBUG)
    
    router_file_handler = logging.handlers.RotatingFileHandler(
        ROUTER_LOG_FILE,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
    )
    router_file_handler.setLevel(logging.DEBUG)
    router_file_handler.setFormatter(formatter)
    router_logger.addHandler(router_file_handler)

    # ============================================
    # 3. DATABASE LOGGER - Database operation logs
    # ============================================
    db_logger = logging.getLogger("app.db")
    db_logger.setLevel(logging.DEBUG)
    
    db_file_handler = logging.handlers.RotatingFileHandler(
        DATABASE_LOG_FILE,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
    )
    db_file_handler.setLevel(logging.DEBUG)
    db_file_handler.setFormatter(formatter)
    db_logger.addHandler(db_file_handler)

    # ============================================
    # 4. PARSER LOGGER - File parsing logs
    # ============================================
    parser_logger = logging.getLogger("app.storage")
    parser_logger.setLevel(logging.DEBUG)
    
    parser_file_handler = logging.handlers.RotatingFileHandler(
        PARSER_LOG_FILE,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
    )
    parser_file_handler.setLevel(logging.DEBUG)
    parser_file_handler.setFormatter(formatter)
    parser_logger.addHandler(parser_file_handler)

    # ============================================
    # 5. DETECTION LOGGER - Plagiarism detection logs
    # ============================================
    detection_logger = logging.getLogger("app.services.detection")
    detection_logger.setLevel(logging.DEBUG)
    
    detection_file_handler = logging.handlers.RotatingFileHandler(
        DETECTION_LOG_FILE,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
    )
    detection_file_handler.setLevel(logging.DEBUG)
    detection_file_handler.setFormatter(formatter)
    detection_logger.addHandler(detection_file_handler)

    # ============================================
    # 6. SILENCE NOISY THIRD-PARTY LOGGERS
    # ============================================
    # Third-party libraries can be chatty; reduce their verbosity
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("Logging initialized successfully")
    logger.info(f"App logs: {APP_LOG_FILE.absolute()}")
    logger.info(f"Router logs: {ROUTER_LOG_FILE.absolute()}")
    logger.info(f"Database logs: {DATABASE_LOG_FILE.absolute()}")
    logger.info(f"Parser logs: {PARSER_LOG_FILE.absolute()}")
    logger.info(f"Detection logs: {DETECTION_LOG_FILE.absolute()}")
    logger.info("=" * 80)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.
    
    Args:
        name: Module name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


__all__ = [
    "setup_logging",
    "get_logger",
    "LOGS_DIR",
    "APP_LOG_FILE",
    "ROUTER_LOG_FILE",
    "DATABASE_LOG_FILE",
    "PARSER_LOG_FILE",
    "DETECTION_LOG_FILE",
]
