# -*- coding: utf-8 -*-
"""
Created
@author:
@links:
@description:
Implements a consistent standard for logging.
"""

# ┌─────────┐
# │ Imports │
# └─────────┘

import logging
import logging.handlers
import os

# ┌───────────────────┐
# │ Program functions │
# └───────────────────┘


def setup_logging(
    log_level: int = logging.DEBUG,
    log_file: str = "logs/app.log",
    error_log_file: str = "logs/error.log",
    max_bytes: int = 10**6,
    backup_count: int = 5,
    console_level: int = logging.INFO,
) -> None:
    """
    Sets up the logging configuration for the application, ensuring that handlers
    are correctly configured without duplicating them.

    Args:
        log_level (int): The logging level for file logging.
        log_file (str): The path to the log file.
        error_log_file (str): The path to the error log file.
        max_bytes (int): The maximum size of the log file before it is rotated.
        backup_count (int): The number of backup files to keep.
        console_level (int): The logging level for console output.
    """

    # Remove all handlers associated with the root logger object to avoid duplicates
    if not logging.getLogger().hasHandlers():
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # Ensure the logs directory exists
        if not os.path.exists(os.path.dirname(log_file)):
            os.makedirs(os.path.dirname(log_file))

        # Log format for console and file handlers
        log_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s [in %(pathname)s:%(lineno)d]"
        )

        # Root logger setup
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        # Console handler for real-time output
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        console_handler.setFormatter(log_format)
        root_logger.addHandler(console_handler)

        # File handler for general logs (all log levels)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(log_format)
        root_logger.addHandler(file_handler)

        # Separate file handler for errors only
        error_file_handler = logging.handlers.RotatingFileHandler(
            error_log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(log_format)
        root_logger.addHandler(error_file_handler)

        logging.info("Logging setup is initialized.")


def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger with the specified name, ensuring that logging is set up.
    """
    return logging.getLogger(name)


def close_loggers() -> None:
    """
    Closes all handlers associated with the root logger to ensure a clean shutdown.
    """
    for handler in logging.getLogger().handlers:
        handler.close()
        logging.getLogger().removeHandler(handler)
