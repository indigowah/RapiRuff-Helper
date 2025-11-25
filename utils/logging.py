"""
Logging configuration using Rich for beautiful console output.

Provides a centralized logger that can be imported throughout the application.
"""

import logging
import sys
from pathlib import Path
from rich.logging import RichHandler
from rich.console import Console
from rich.traceback import install as install_rich_traceback

from config import config


def setup_logging() -> logging.Logger:
    """
    Set up logging with Rich formatting.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Install rich traceback handler for better error messages
    install_rich_traceback(show_locals=True)
    
    # Create console for Rich output
    console = Console()
    
    # Create logger
    logger = logging.getLogger("discord_bot")
    logger.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Rich console handler
    console_handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        markup=True
    )
    console_handler.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
    console_formatter = logging.Formatter(
        "%(message)s",
        datefmt="[%X]"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (standard format for file logging)
    if config.LOG_FILE:
        log_path = Path(config.LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # File gets all logs
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


# Global logger instance
logger = setup_logging()
