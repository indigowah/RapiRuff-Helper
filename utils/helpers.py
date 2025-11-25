"""
Helper utilities for common bot operations.

Provides utility functions for embeds, user management, etc.
"""

from typing import Optional
import discord
from datetime import datetime


def create_embed(
    title: str,
    description: Optional[str] = None,
    color: discord.Color = discord.Color.blue(),
    fields: Optional[list[tuple[str, str, bool]]] = None,
    footer: Optional[str] = None,
    thumbnail: Optional[str] = None,
    image: Optional[str] = None,
    timestamp: bool = True
) -> discord.Embed:
    """
    Create a standardized Discord embed.
    
    Args:
        title: Embed title
        description: Embed description
        color: Embed color
        fields: List of tuples (name, value, inline) for embed fields
        footer: Footer text
        thumbnail: Thumbnail URL
        image: Image URL
        timestamp: Whether to add current timestamp
    
    Returns:
        discord.Embed: Configured embed object
    """
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
    
    if footer:
        embed.set_footer(text=footer)
    
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    
    if image:
        embed.set_image(url=image)
    
    if timestamp:
        embed.timestamp = datetime.utcnow()
    
    return embed


def create_error_embed(message: str) -> discord.Embed:
    """
    Create a standardized error embed.
    
    Args:
        message: Error message to display
    
    Returns:
        discord.Embed: Error embed
    """
    return create_embed(
        title="❌ Error",
        description=message,
        color=discord.Color.red()
    )


def create_success_embed(message: str) -> discord.Embed:
    """
    Create a standardized success embed.
    
    Args:
        message: Success message to display
    
    Returns:
        discord.Embed: Success embed
    """
    return create_embed(
        title="✅ Success",
        description=message,
        color=discord.Color.green()
    )


def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds to a human-readable string.
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        str: Formatted duration string (e.g., "2h 15m 30s")
    """
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")
    
    return " ".join(parts)
