"""
Configuration management for the Discord bot.

Loads environment variables and provides centralized access to all configuration settings.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Central configuration class for the bot."""
    
    # Discord Configuration
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///data/bot.db")
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/bot.log")
    
    # Voice Configuration
    RINGTONE_PATH: Optional[str] = os.getenv("RINGTONE_PATH")
    
    # Ollama Configuration
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "tinyllama")
    OLLAMA_ENABLED: bool = os.getenv("OLLAMA_ENABLED", "false").lower() == "true"
    
    # Directory Paths
    BASE_DIR: Path = Path(__file__).parent
    DATA_DIR: Path = BASE_DIR / "data"
    LOGS_DIR: Path = BASE_DIR / "logs"
    COGS_DIR: Path = BASE_DIR / "cogs"
    
    # Database file path (for SQLite)
    DB_FILE: Path = DATA_DIR / "bot.db"
    
    # JSON Stats file
    EMOJI_STATS_FILE: Path = DATA_DIR / "emoji_stats.json"
    
    @classmethod
    def validate(cls) -> None:
        """Validate that required configuration values are set."""
        if not cls.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN environment variable is required")
        
        # Create necessary directories
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.LOGS_DIR.mkdir(exist_ok=True)
        cls.COGS_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def get_database_config(cls) -> dict:
        """
        Parse DATABASE_URL and return database configuration.
        
        Returns:
            dict: Database configuration for Peewee
        """
        url = cls.DATABASE_URL
        
        if url.startswith("sqlite:///"):
            db_path = url.replace("sqlite:///", "")
            return {
                "type": "sqlite",
                "database": db_path
            }
        elif url.startswith("postgres://") or url.startswith("postgresql://"):
            # Parse PostgreSQL URL format: postgresql://user:pass@host:port/dbname
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return {
                "type": "postgresql",
                "database": parsed.path[1:],  # Remove leading slash
                "user": parsed.username,
                "password": parsed.password,
                "host": parsed.hostname,
                "port": parsed.port or 5432
            }
        else:
            raise ValueError(f"Unsupported DATABASE_URL format: {url}")


# Create config instance
config = Config()
