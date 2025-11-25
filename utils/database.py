"""
Database models and utilities using Peewee ORM.

Defines all database models and provides database initialization functions.
"""

from datetime import datetime
from peewee import (
    Model,
    SqliteDatabase,
    PostgresqlDatabase,
    BigIntegerField,
    CharField,
    DateTimeField,
    DecimalField,
    IntegerField,
    BooleanField,
    ForeignKeyField,
)
from config import config


# Initialize database based on configuration
def get_database():
    """Get the appropriate database instance based on configuration."""
    db_config = config.get_database_config()
    
    if db_config["type"] == "sqlite":
        return SqliteDatabase(db_config["database"])
    elif db_config["type"] == "postgresql":
        return PostgresqlDatabase(
            db_config["database"],
            user=db_config["user"],
            password=db_config["password"],
            host=db_config["host"],
            port=db_config["port"]
        )
    else:
        raise ValueError(f"Unsupported database type: {db_config['type']}")


# Database proxy
database = get_database()


class BaseModel(Model):
    """Base model class that all models inherit from."""
    
    class Meta:
        database = database


class User(BaseModel):
    """User model for tracking Discord users."""
    
    user_id = BigIntegerField(primary_key=True, help_text="Discord user ID")
    discord_name = CharField(max_length=255, help_text="Discord username")
    created_at = DateTimeField(default=datetime.utcnow, help_text="When user was first seen")
    
    class Meta:
        table_name = "users"


class Finance(BaseModel):
    """Financial balance tracking for users."""
    
    user = ForeignKeyField(User, backref="finances", on_delete="CASCADE")
    currency = CharField(max_length=3, help_text="Currency code (CNY, ZAR, USD)")
    balance = DecimalField(max_digits=15, decimal_places=2, default=0)
    
    class Meta:
        table_name = "finances"
        indexes = (
            (("user", "currency"), True),  # Unique constraint on user + currency
        )


class CallSession(BaseModel):
    """Voice channel call session tracking."""
    
    session_id = IntegerField(primary_key=True)
    user = ForeignKeyField(User, backref="call_sessions", on_delete="CASCADE")
    join_ts = DateTimeField(help_text="Timestamp when user joined voice channel")
    leave_ts = DateTimeField(null=True, help_text="Timestamp when user left voice channel")
    
    class Meta:
        table_name = "call_sessions"


class DueItem(BaseModel):
    """Due/task tracking for users."""
    
    item_id = IntegerField(primary_key=True)
    user = ForeignKeyField(User, backref="due_items", on_delete="CASCADE")
    description = CharField(max_length=500, help_text="Task description")
    created_at = DateTimeField(default=datetime.utcnow, help_text="When task was created")
    completed = BooleanField(default=False, help_text="Whether task is completed")
    
    class Meta:
        table_name = "due_items"


class GamePreference(BaseModel):
    """User game rotation preferences."""
    
    user = ForeignKeyField(User, backref="game_preferences", on_delete="CASCADE")
    game_name = CharField(max_length=255, help_text="Name of the game")
    position = IntegerField(help_text="Position in rotation list")
    
    class Meta:
        table_name = "game_prefs"
        indexes = (
            (("user", "game_name"), True),  # Unique constraint on user + game
        )


# List of all models for easy reference
MODELS = [User, Finance, CallSession, DueItem, GamePreference]


def initialize_database():
    """Initialize the database and create tables if they don't exist."""
    database.connect()
    database.create_tables(MODELS, safe=True)
    return database


def close_database():
    """Close the database connection."""
    if not database.is_closed():
        database.close()
