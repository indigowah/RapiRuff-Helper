"""
Example cog demonstrating the structure.

This is a template cog that shows how to create new cogs for the bot.
"""

from discord.ext import commands
from discord import app_commands
import discord
from cogs.base_cog import BaseCog


class ExampleCog(BaseCog):
    """Example cog showing basic structure."""
    
    def __init__(self, bot: commands.Bot):
        """Initialize the example cog."""
        super().__init__(bot)
    
    @app_commands.command(name="ping", description="Check if the bot is responsive")
    async def ping(self, interaction: discord.Interaction):
        """
        Simple ping command.
        
        Args:
            interaction: The interaction that triggered this command
        """
        latency = self.bot.latency * 1000  # Convert to milliseconds
        
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Bot latency: {latency:.2f}ms",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed)
        self.logger.info(f"Ping command used by {interaction.user}")
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Event listener: Called when the bot is ready."""
        self.logger.info(f"Example cog ready! Logged in as {self.bot.user}")


async def setup(bot: commands.Bot):
    """
    Setup function to add this cog to the bot.
    
    Args:
        bot: The Discord bot instance
    """
    await bot.add_cog(ExampleCog(bot))
