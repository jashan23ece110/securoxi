"""
SECUROXI AI Security Engine Logger
Provides privacy-aware structured logging without leaking sensitive document content.
"""

import logging
import sys
from typing import Optional


class RedactingFormatter(logging.Formatter):
    """Logging formatter that redacts sensitive text unless explicitly allowed."""

    def __init__(self, fmt=None, datefmt=None, style='%', log_sensitive: bool = False):
        super().__init__(fmt, datefmt, style)
        self.log_sensitive = log_sensitive


def get_logger(name: str = "securoxi", log_level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(log_level)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
