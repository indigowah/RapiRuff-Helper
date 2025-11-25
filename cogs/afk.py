"""
AFK status cog.

Provides AFK status commands and automatic notifications when AFK users are mentioned.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands

from cogs.base_cog import BaseCog
from utils.helpers import create_embed, create_error_embed, create_success_embed
from utils import User, AFKStatus


class AFK(BaseCog):
    """AFK status management cog."""
    
    def __init__(self, bot: commands.Bot):
        """Initialize the AFK cog."""
        super().__init__(bot)
    
    def _get_or_create_user(self, user_id: int, username: str) -> User:
        """
        Get or create a user in the database.
        
        Args:
            user_id: Discord user ID
            username: Discord username
        
        Returns:
            User: User model instance
        """
        user, created = User.get_or_create(
            user_id=user_id,
            defaults={"discord_name": username}
        )
        if not created and user.discord_name != username:
            user.discord_name = username
            user.save()
        return user
    
    def _parse_time_delta(self, time_str: str) -> Optional[timedelta]:
        """
        Parse a time delta string like '2h', '30m', '1d'.
        
        Args:
            time_str: Time string to parse
        
        Returns:
            Optional[timedelta]: Parsed time delta or None if invalid
        """
        time_str = time_str.strip().lower()
        
        try:
            if time_str.endswith('h'):
                hours = int(time_str[:-1])
                return timedelta(hours=hours)
            elif time_str.endswith('m'):
                minutes = int(time_str[:-1])
                return timedelta(minutes=minutes)
            elif time_str.endswith('d'):
                days = int(time_str[:-1])
                return timedelta(days=days)
        except (ValueError, IndexError):
            return None
        
        return None
    
    @app_commands.command(
        name="afk",
        description="Set your AFK status with optional reason and expected return time"
    )
    @app_commands.describe(
        reason="Reason for being AFK (optional)",
        expected_back="Expected return time (e.g., '2h', '30m', '1d') (optional)",
        timezone_offset="Your timezone offset from UTC (e.g., '+8' or '-5') (optional)"
    )
    async def afk(
        self,
        interaction: discord.Interaction,
        reason: Optional[str] = None,
        expected_back: Optional[str] = None,
        timezone_offset: Optional[str] = None
    ):
        """
        Set AFK status command.
        
        Args:
            interaction: Discord interaction
            reason: Reason for being AFK
            expected_back: Expected return time as a duration string
            timezone_offset: User's timezone offset from UTC
        """
        await interaction.response.defer()
        
        # Get or create user
        user = self._get_or_create_user(
            interaction.user.id,
            str(interaction.user)
        )
        
        # Parse expected back time
        expected_back_dt = None
        if expected_back:
            delta = self._parse_time_delta(expected_back)
            if delta:
                expected_back_dt = datetime.utcnow() + delta
            else:
                await interaction.followup.send(
                    embed=create_error_embed(
                        "Invalid time format! Use '2h', '30m', or '1d' format."
                    )
                )
                return
        
        # Parse timezone offset
        tz_offset_hours = 0
        if timezone_offset:
            try:
                tz_offset_hours = int(timezone_offset)
                if tz_offset_hours < -12 or tz_offset_hours > 14:
                    await interaction.followup.send(
                        embed=create_error_embed(
                            "Invalid timezone offset! Must be between -12 and +14."
                        )
                    )
                    return
            except ValueError:
                await interaction.followup.send(
                    embed=create_error_embed(
                        "Invalid timezone offset! Use format like '+8' or '-5'."
                    )
                )
                return
        
        # Create or update AFK status
        afk_status, created = AFKStatus.get_or_create(
            user=user,
            defaults={
                "reason": reason,
                "expected_back": expected_back_dt,
                "set_at": datetime.utcnow()
            }
        )
        
        if not created:
            afk_status.reason = reason
            afk_status.expected_back = expected_back_dt
            afk_status.set_at = datetime.utcnow()
            afk_status.save()
        
        # Build embed fields
        fields = []
        
        # Reason field
        if reason:
            fields.append(("💬 Reason", reason, False))
        else:
            fields.append(("💬 Reason", "*No reason provided*", False))
        
        # Expected back field
        if expected_back_dt:
            # Convert to user's timezone for display
            user_tz = timezone(timedelta(hours=tz_offset_hours))
            local_time = expected_back_dt.replace(tzinfo=timezone.utc).astimezone(user_tz)
            
            time_str = local_time.strftime("%Y-%m-%d %I:%M %p")
            tz_str = f"UTC{timezone_offset}" if timezone_offset else "UTC"
            
            fields.append((
                "⏰ Expected Back",
                f"{time_str} ({tz_str})",
                False
            ))
        else:
            fields.append(("⏰ Expected Back", "*Not specified*", False))
        
        # Create success embed
        embed = create_embed(
            title="💤 AFK Status Set",
            description=f"**{interaction.user.display_name}** is now AFK!",
            color=discord.Color.orange(),
            fields=fields,
            footer="You'll be automatically removed from AFK when you send a message"
        )
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        await interaction.followup.send(embed=embed)
        
        self.logger.info(
            f"User {interaction.user} set AFK status. Reason: {reason}, "
            f"Expected back: {expected_back_dt}"
        )
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Listen for messages to:
        1. Remove AFK status when an AFK user sends a message
        2. Notify when AFK users are mentioned
        
        Args:
            message: Discord message
        """
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Check if author is AFK and remove status
        try:
            user = User.get(User.user_id == message.author.id)
            afk_status = AFKStatus.get(AFKStatus.user == user)
            
            # Calculate how long they were AFK
            afk_duration = datetime.utcnow() - afk_status.set_at
            hours = int(afk_duration.total_seconds() // 3600)
            minutes = int((afk_duration.total_seconds() % 3600) // 60)
            
            duration_str = ""
            if hours > 0:
                duration_str = f"{hours}h {minutes}m"
            else:
                duration_str = f"{minutes}m"
            
            # Remove AFK status
            afk_status.delete_instance()
            
            embed = create_embed(
                title="👋 Welcome Back!",
                description=f"**{message.author.display_name}**, your AFK status has been removed.",
                color=discord.Color.green(),
                fields=[
                    ("⏱️ AFK Duration", duration_str, True)
                ]
            )
            
            await message.channel.send(embed=embed, delete_after=10)
            
            self.logger.info(f"Removed AFK status for user {message.author}")
            
        except User.DoesNotExist:
            pass
        except AFKStatus.DoesNotExist:
            pass
        
        # Check if any AFK users are mentioned
        for mentioned_user in message.mentions:
            try:
                user = User.get(User.user_id == mentioned_user.id)
                afk_status = AFKStatus.get(AFKStatus.user == user)
                
                # Build notification embed
                fields = []
                
                # Reason
                if afk_status.reason:
                    fields.append(("💬 Reason", afk_status.reason, False))
                
                # Expected back
                if afk_status.expected_back:
                    now = datetime.utcnow()
                    if afk_status.expected_back > now:
                        time_until = afk_status.expected_back - now
                        hours = int(time_until.total_seconds() // 3600)
                        minutes = int((time_until.total_seconds() % 3600) // 60)
                        
                        if hours > 0:
                            time_str = f"in ~{hours}h {minutes}m"
                        else:
                            time_str = f"in ~{minutes}m"
                        
                        fields.append(("⏰ Expected Back", time_str, False))
                    else:
                        fields.append(("⏰ Expected Back", "Should be back soon", False))
                
                # How long they've been AFK
                afk_duration = now - afk_status.set_at
                hours = int(afk_duration.total_seconds() // 3600)
                minutes = int((afk_duration.total_seconds() % 3600) // 60)
                
                if hours > 0:
                    duration_str = f"{hours}h {minutes}m ago"
                else:
                    duration_str = f"{minutes}m ago"
                
                fields.append(("⏱️ AFK Since", duration_str, False))
                
                embed = create_embed(
                    title="💤 User is AFK",
                    description=f"**{mentioned_user.display_name}** is currently AFK.",
                    color=discord.Color.orange(),
                    fields=fields
                )
                
                embed.set_thumbnail(url=mentioned_user.display_avatar.url)
                
                await message.channel.send(embed=embed, delete_after=30)
                
                self.logger.info(
                    f"Notified about AFK user {mentioned_user} in response to "
                    f"mention by {message.author}"
                )
                
            except User.DoesNotExist:
                continue
            except AFKStatus.DoesNotExist:
                continue


async def setup(bot: commands.Bot):
    """
    Setup function to add this cog to the bot.
    
    Args:
        bot: The Discord bot instance
    """
    await bot.add_cog(AFK(bot))
