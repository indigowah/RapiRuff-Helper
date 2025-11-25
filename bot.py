"""
Main bot entry point.

Initializes the Discord bot, loads cogs, and handles startup/shutdown.
"""

import asyncio
import sys
from pathlib import Path
import discord
from discord.ext import commands

from config import config
from utils import logger, initialize_database, close_database


class DiscordBot(commands.Bot):
    """Custom Discord Bot class with extended functionality."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the bot."""
        super().__init__(*args, **kwargs)
        self.logger = logger
    
    async def setup_hook(self):
        """
        Async initialization hook.
        
        Called when the bot is starting up. Load all cogs here.
        """
        self.logger.info("Running setup hook...")
        
        # Load all cogs from the cogs directory
        await self.load_cogs()
        
        # Sync slash commands with Discord
        self.logger.info("Syncing command tree...")
        await self.tree.sync()
        self.logger.info("Command tree synced")
    
    async def load_cogs(self):
        """Load all cogs from the cogs directory."""
        cogs_dir = Path("cogs")
        
        for cog_file in cogs_dir.glob("*.py"):
            # Skip base_cog and __init__
            if cog_file.stem in ["base_cog", "__init__"]:
                continue
            
            cog_name = f"cogs.{cog_file.stem}"
            
            try:
                await self.load_extension(cog_name)
                self.logger.info(f"✓ Loaded cog: {cog_name}")
            except Exception as e:
                self.logger.error(f"✗ Failed to load cog {cog_name}: {e}", exc_info=e)
    
    async def on_ready(self):
        """Called when the bot is ready and connected to Discord."""
        self.logger.info("=" * 50)
        self.logger.info(f"Bot is ready!")
        self.logger.info(f"Logged in as: {self.user.name} (ID: {self.user.id})")
        self.logger.info(f"Connected to {len(self.guilds)} guild(s)")
        self.logger.info("=" * 50)
    
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """
        Global error handler for commands.
        
        Args:
            ctx: The command context
            error: The error that occurred
        """
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors
        
        self.logger.error(f"Command error in {ctx.command}: {error}", exc_info=error)
        
        # Send user-friendly error message
        await ctx.send(f"An error occurred while executing the command: {str(error)}")


async def main():
    """Main entry point for the bot."""
    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    # Initialize database
    logger.info("Initializing database...")
    try:
        initialize_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=e)
        sys.exit(1)
    
    # Create bot instance with intents
    intents = discord.Intents.default()
    intents.message_content = True  # Required for message content
    intents.members = True  # Required for member events
    intents.voice_states = True  # Required for voice channel tracking
    
    bot = DiscordBot(
        command_prefix="!",  # Fallback prefix for traditional commands
        intents=intents,
        help_command=None  # We'll create a custom help command later
    )
    
    try:
        # Start the bot
        logger.info("Starting bot...")
        await bot.start(config.DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=e)
    finally:
        # Cleanup
        logger.info("Cleaning up...")
        await bot.close()
        close_database()
        logger.info("Bot shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot terminated by user")
