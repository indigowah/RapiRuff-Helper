"""
Base Cog class that all cogs should inherit from.

Provides common functionality and utilities for all cogs.
"""

from discord.ext import commands
from utils import logger


class BaseCog(commands.Cog):
    """
    Base class for all cogs to inherit from.
    
    Provides common initialization and utilities.
    """
    
    def __init__(self, bot: commands.Bot):
        """
        Initialize the base cog.
        
        Args:
            bot: The Discord bot instance
        """
        self.bot = bot
        self.logger = logger
        self.logger.info(f"Loaded cog: {self.__class__.__name__}")
    
    async def cog_load(self):
        """Called when the cog is loaded."""
        self.logger.debug(f"{self.__class__.__name__} cog loaded")
    
    async def cog_unload(self):
        """Called when the cog is unloaded."""
        self.logger.debug(f"{self.__class__.__name__} cog unloaded")
    
    async def cog_command_error(self, ctx: commands.Context, error: Exception):
        """
        Error handler for commands in this cog.
        
        Args:
            ctx: The command context
            error: The error that occurred
        """
        self.logger.error(f"Error in {ctx.command}: {error}", exc_info=error)
        await ctx.send(f"An error occurred: {str(error)}")
