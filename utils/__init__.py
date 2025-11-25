"""
Utilities package for the Discord bot.

This package contains shared utilities like logging and database management.
"""

from .logging import logger
from .database import (
    database,
    initialize_database,
    close_database,
    User,
    Finance,
    CallSession,
    DueItem,
    GamePreference,
    AFKStatus,
)

__all__ = [
    "logger",
    "database",
    "initialize_database",
    "close_database",
    "User",
    "Finance",
    "CallSession",
    "DueItem",
    "GamePreference",
    "AFKStatus",
]
