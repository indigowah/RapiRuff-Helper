"""
Statistics Cog for tracking user activity and managing configuration.
"""

import discord
from discord.ext import commands
import json
import re
import asyncio
from datetime import datetime, timedelta
import emoji
from typing import Optional, Dict, List, Any
from pathlib import Path

from config import config
from utils.database import User, CallSession, SpamStats, GuildSettings
from utils.config_manager import ConfigManager
from utils.visualization import VisualizationService
from utils import logger

class Statistics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_manager = ConfigManager()
        self.viz_service = VisualizationService()
        self.spam_cache: Dict[int, List[Tuple[str, datetime]]] = {}  # Cache for repeated messages
        
        # Load emoji stats
        self.emoji_stats = self._load_emoji_stats()
        
    def _load_emoji_stats(self) -> Dict[str, Any]:
        """Load emoji statistics from JSON file."""
        if config.EMOJI_STATS_FILE.exists():
            try:
                with open(config.EMOJI_STATS_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load emoji stats: {e}")
                return {}
        return {}

    def _save_emoji_stats(self):
        """Save emoji statistics to JSON file."""
        try:
            with open(config.EMOJI_STATS_FILE, 'w') as f:
                json.dump(self.emoji_stats, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save emoji stats: {e}")

    # --- Emoji Tracking ---

    EMOTICON_PATTERNS = [
        (r':-?\)', ':)'), (r':-?D', ':D'), (r'=\)', '=)'), (r'=D', '=D'),
        (r':3', ':3'), (r'\^_\^', '^_^'), (r'\^-\^', '^-^'), (r'\^\^', '^^'),
        (r':>', ':>'), (r'c:', 'c:'),
        (r':-?\(', ':('), (r':\'?\(', ':('), (r'=\(', '=('), (r'\):', '):'),
        (r';-?\)', ';)'), (r';-?D', ';D'),
        (r':O', ':O'), (r':o', ':o'), (r'o_O', 'o_O'), (r'O_o', 'O_o'),
        (r'<3', '<3'),
        (r':-?\|', ':|'), (r'=\|', '=|'),
        (r':-?/', ':/'), (r':-?\\', ':\\'), (r'-_-', '-_-'),
        (r'>:-?\(', '>:('), (r'>:-?\)', '>:)'),
        (r'[Xx]D', 'XD'), (r'uwu', 'uwu'), (r'owo', 'owo'), (r'>w<', '>w<'),
    ]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Check if tracking is enabled for this guild
        if message.guild:
            if not await self.config_manager.is_feature_enabled(message.guild.id, "emoji_tracking"):
                return
        
        # Check user opt-out
        user_config = await self.config_manager.get_user_config(message.author.id)
        if user_config["opt_out"]:
            return

        await self._process_emoji_tracking(message)
        await self._process_spam_detection(message)

    async def _process_emoji_tracking(self, message):
        """Process and count emojis in a message."""
        content = message.content
        user_id = str(message.author.id)
        
        if user_id not in self.emoji_stats:
            self.emoji_stats[user_id] = {
                "unicode_emojis": {},
                "text_emoticons": {},
                "custom_emojis": {},
                "total_emojis": 0,
                "last_updated": str(datetime.utcnow())
            }
            
        stats = self.emoji_stats[user_id]
        found_any = False

        # 1. Unicode Emojis
        emoji_list = emoji.emoji_list(content)
        for item in emoji_list:
            char = item['emoji']
            stats["unicode_emojis"][char] = stats["unicode_emojis"].get(char, 0) + 1
            stats["total_emojis"] += 1
            found_any = True

        # 2. Text Emoticons
        for pattern, normalized in self.EMOTICON_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                stats["text_emoticons"][normalized] = stats["text_emoticons"].get(normalized, 0) + len(matches)
                stats["total_emojis"] += len(matches)
                found_any = True

        # 3. Custom Emojis
        custom_emojis = re.findall(r'<a?:(\w+):(\d+)>', content)
        for name, _ in custom_emojis:
            stats["custom_emojis"][name] = stats["custom_emojis"].get(name, 0) + 1
            stats["total_emojis"] += 1
            found_any = True

        if found_any:
            stats["last_updated"] = str(datetime.utcnow())
            self._save_emoji_stats()

    @commands.command(name="emojistats")
    async def emoji_stats_cmd(self, ctx, user: Optional[discord.Member] = None):
        """Display emoji usage statistics."""
        target = user or ctx.author
        user_id = str(target.id)
        
        if user_id not in self.emoji_stats:
            await ctx.send(f"No emoji statistics found for {target.display_name}.")
            return

        stats = self.emoji_stats[user_id]
        
        embed = discord.Embed(title=f"😀 Emoji Statistics for {target.display_name}", color=discord.Color.blue())
        embed.add_field(name="Total Emojis Used", value=str(stats["total_emojis"]), inline=False)
        
        # Top Unicode
        top_unicode = sorted(stats["unicode_emojis"].items(), key=lambda x: x[1], reverse=True)[:5]
        if top_unicode:
            embed.add_field(name="Top Unicode", value="\n".join([f"{k}: {v}" for k, v in top_unicode]), inline=True)
            
        # Top Emoticons
        top_emoticons = sorted(stats["text_emoticons"].items(), key=lambda x: x[1], reverse=True)[:5]
        if top_emoticons:
            embed.add_field(name="Top Emoticons", value="\n".join([f"{k}: {v}" for k, v in top_emoticons]), inline=True)
            
        # Top Custom
        top_custom = sorted(stats["custom_emojis"].items(), key=lambda x: x[1], reverse=True)[:5]
        if top_custom:
            embed.add_field(name="Top Custom", value="\n".join([f"{k}: {v}" for k, v in top_custom]), inline=True)

        await ctx.send(embed=embed)

    async def _process_spam_detection(self, message):
        """Process spam detection for a message."""
        if not message.guild:
            return
            
        if not await self.config_manager.is_feature_enabled(message.guild.id, "spam_detection"):
            return

        content = message.content
        user_id = message.author.id
        is_spam = False
        spam_type = ""

        # 1. Character Repetition
        if self._detect_char_repetition(content):
            is_spam = True
            spam_type = "char_repetition"

        # 2. CAPS LOCK Spam
        elif self._detect_caps_spam(content):
            is_spam = True
            spam_type = "caps_spam"

        # 3. Repeated Messages
        elif self._detect_repeated_message(user_id, content):
            is_spam = True
            spam_type = "repeated_messages"

        if is_spam:
            await self._record_spam(user_id, spam_type)

    def _detect_char_repetition(self, content: str) -> bool:
        """Detect excessive character repetition."""
        threshold = config.SPAM_CHAR_REPETITION_THRESHOLD
        pattern = r'(.)\1{' + str(threshold - 1) + r',}'
        return bool(re.search(pattern, content, re.IGNORECASE))

    def _detect_caps_spam(self, content: str) -> bool:
        """Detect excessive uppercase usage."""
        if len(content) <= 10:
            return False
        
        text_no_space = content.replace(" ", "")
        if not text_no_space:
            return False
            
        capitals = sum(1 for c in text_no_space if c.isupper())
        letters = sum(1 for c in text_no_space if c.isalpha())
        
        if letters == 0:
            return False
        
        return (capitals / letters) >= config.SPAM_CAPS_RATIO_THRESHOLD

    def _detect_repeated_message(self, user_id: int, content: str) -> bool:
        """Detect repeated messages."""
        import hashlib
        msg_hash = hashlib.md5(content.encode()).hexdigest()
        now = datetime.utcnow()
        
        if user_id not in self.spam_cache:
            self.spam_cache[user_id] = []
            
        # Clean up old cache
        window = timedelta(seconds=config.SPAM_REPEATED_MSG_WINDOW)
        self.spam_cache[user_id] = [
            (h, t) for h, t in self.spam_cache[user_id] 
            if now - t < window
        ]
        
        # Check count
        count = sum(1 for h, _ in self.spam_cache[user_id] if h == msg_hash)
        self.spam_cache[user_id].append((msg_hash, now))
        
        return count >= config.SPAM_REPEATED_MSG_COUNT

    async def _record_spam(self, user_id: int, spam_type: str):
        """Record spam detection in database."""
        try:
            user, _ = User.get_or_create(user_id=user_id, defaults={'discord_name': 'Unknown'})
            
            # Update or create stats
            stats, created = SpamStats.get_or_create(
                user=user, 
                spam_type=spam_type,
                defaults={'count': 0}
            )
            stats.count += 1
            stats.last_triggered = datetime.utcnow()
            stats.save()
        except Exception as e:
            logger.error(f"Failed to record spam stats: {e}")

    @commands.command(name="spamstats")
    async def spam_stats_cmd(self, ctx, user: Optional[discord.Member] = None):
        """Display spam statistics."""
        target = user or ctx.author
        
        stats = SpamStats.select().where(SpamStats.user == target.id)
        
        if not stats.exists():
            await ctx.send(f"No spam statistics found for {target.display_name}.")
            return
            
        embed = discord.Embed(title=f"🚫 Spam Statistics for {target.display_name}", color=discord.Color.red())
        
        total_spam = 0
        for stat in stats:
            embed.add_field(
                name=stat.spam_type.replace("_", " ").title(),
                value=f"{stat.count} times\nLast: {stat.last_triggered.strftime('%Y-%m-%d %H:%M')}",
                inline=True
            )
            total_spam += stat.count
            
        embed.set_footer(text=f"Total Spam Detections: {total_spam}")
        await ctx.send(embed=embed)

    # --- Call Statistics ---

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        # Check if tracking is enabled
        if member.guild:
             if not await self.config_manager.is_feature_enabled(member.guild.id, "call_tracking"):
                return
        
        # User joined a channel
        if before.channel is None and after.channel is not None:
            await self._start_voice_session(member, after.channel)
        
        # User left a channel
        elif before.channel is not None and after.channel is None:
            await self._end_voice_session(member, before.channel)
        
        # User switched channels
        elif before.channel != after.channel:
            await self._end_voice_session(member, before.channel)
            await self._start_voice_session(member, after.channel)

    async def _start_voice_session(self, member, channel):
        """Start a new voice session."""
        try:
            user, _ = User.get_or_create(user_id=member.id, defaults={'discord_name': member.name})
            
            CallSession.create(
                user=user,
                channel_id=channel.id,
                join_ts=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Failed to start voice session: {e}")

    async def _end_voice_session(self, member, channel):
        """End an active voice session."""
        try:
            # Find open session
            session = (CallSession
                      .select()
                      .where(
                          (CallSession.user == member.id) & 
                          (CallSession.leave_ts.is_null())
                      )
                      .order_by(CallSession.join_ts.desc())
                      .first())
            
            if session:
                now = datetime.utcnow()
                session.leave_ts = now
                session.duration = int((now - session.join_ts).total_seconds())
                session.save()
        except Exception as e:
            logger.error(f"Failed to end voice session: {e}")

    @commands.command(name="callstats")
    async def call_stats_cmd(self, ctx, user: Optional[discord.Member] = None):
        """Display call statistics."""
        target = user or ctx.author
        
        sessions = CallSession.select().where(CallSession.user == target.id)
        
        if not sessions.exists():
            await ctx.send(f"No call statistics found for {target.display_name}.")
            return
            
        total_duration = 0
        total_sessions = 0
        longest_session = 0
        
        for session in sessions:
            if session.duration:
                total_duration += session.duration
                total_sessions += 1
                if session.duration > longest_session:
                    longest_session = session.duration
        
        # Format durations
        def format_duration(seconds):
            hours, remainder = divmod(seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours}h {minutes}m {seconds}s"
            
        embed = discord.Embed(title=f"📞 Call Statistics for {target.display_name}", color=discord.Color.green())
        embed.add_field(name="Total Time", value=format_duration(total_duration), inline=True)
        embed.add_field(name="Total Sessions", value=str(total_sessions), inline=True)
        embed.add_field(name="Longest Call", value=format_duration(longest_session), inline=True)
        
        if total_sessions > 0:
            avg_duration = total_duration // total_sessions
            embed.add_field(name="Average Duration", value=format_duration(avg_duration), inline=True)
            
        await ctx.send(embed=embed)

    # --- Visualization Commands ---

    @commands.command(name="graph")
    async def show_graph(self, ctx, graph_type: str = "activity"):
        """
        Display a statistical graph.
        Types: activity, emoji, spam
        """
        user_id = ctx.author.id
        
        if graph_type == "activity":
            # Generate dummy activity data for now (7 days x 24 hours)
            # In a real implementation, this would query the DB
            data = [[0] * 24 for _ in range(7)]
            
            # Populate with some call data
            sessions = CallSession.select().where(CallSession.user == user_id)
            for session in sessions:
                day = session.join_ts.weekday()
                hour = session.join_ts.hour
                data[day][hour] += 1
            
            image_buffer = await asyncio.to_thread(self.viz_service.generate_activity_heatmap, data)
            filename = "activity_heatmap.png"
            title = "Activity Heatmap"
            
        elif graph_type == "emoji":
            if str(user_id) not in self.emoji_stats:
                await ctx.send("No emoji stats found.")
                return
                
            stats = self.emoji_stats[str(user_id)]
            # Combine all emoji types
            all_emojis = {**stats["unicode_emojis"], **stats["text_emoticons"], **stats["custom_emojis"]}
            
            if not all_emojis:
                await ctx.send("No emoji usage recorded.")
                return
                
            image_buffer = await asyncio.to_thread(self.viz_service.generate_emoji_pie_chart, all_emojis)
            filename = "emoji_pie.png"
            title = "Emoji Usage"
            
        elif graph_type == "spam":
            stats = SpamStats.select().where(SpamStats.user == user_id)
            if not stats.exists():
                await ctx.send("No spam stats found.")
                return
                
            spam_data = {s.spam_type: s.count for s in stats}
            image_buffer = await asyncio.to_thread(self.viz_service.generate_spam_stats_chart, spam_data)
            filename = "spam_chart.png"
            title = "Spam Statistics"
            
        else:
            await ctx.send("Invalid graph type. Options: activity, emoji, spam")
            return
            
        file = discord.File(image_buffer, filename=filename)
        embed = discord.Embed(title=title, color=discord.Color.blue())
        embed.set_image(url=f"attachment://{filename}")
        
        await ctx.send(embed=embed, file=file)

    # --- Configuration Commands ---

    @commands.group(name="config")
    @commands.has_permissions(administrator=True)
    async def config_group(self, ctx):
        """Manage bot configuration."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @config_group.command(name="enable")
    async def config_enable(self, ctx, feature: str):
        """
        Enable a feature (emoji, spam, call).
        Usage: /config enable <feature>
        """
        valid_features = ["emoji", "spam", "call"]
        if feature not in valid_features:
            await ctx.send(f"Invalid feature. Valid options: {', '.join(valid_features)}")
            return
            
        success = await self.config_manager.update_guild_config(
            ctx.guild.id, f"{feature}_tracking_enabled", True
        )
        
        if success:
            await ctx.send(f"✅ Enabled {feature} tracking.")
        else:
            await ctx.send("❌ Failed to update configuration.")

    @config_group.command(name="disable")
    async def config_disable(self, ctx, feature: str):
        """
        Disable a feature (emoji, spam, call).
        Usage: /config disable <feature>
        """
        valid_features = ["emoji", "spam", "call"]
        if feature not in valid_features:
            await ctx.send(f"Invalid feature. Valid options: {', '.join(valid_features)}")
            return
            
        success = await self.config_manager.update_guild_config(
            ctx.guild.id, f"{feature}_tracking_enabled", False
        )
        
        if success:
            await ctx.send(f"✅ Disabled {feature} tracking.")
        else:
            await ctx.send("❌ Failed to update configuration.")

    @commands.command(name="optout")
    async def opt_out(self, ctx):
        """Opt out of all tracking statistics."""
        success = await self.config_manager.set_user_opt_out(ctx.author.id, True)
        if success:
            await ctx.send("✅ You have opted out of statistics tracking.")
        else:
            await ctx.send("❌ Failed to update preferences.")

    @commands.command(name="optin")
    async def opt_in(self, ctx):
        """Opt in to statistics tracking."""
        success = await self.config_manager.set_user_opt_out(ctx.author.id, False)
        if success:
            await ctx.send("✅ You have opted in to statistics tracking.")
        else:
            await ctx.send("❌ Failed to update preferences.")

async def setup(bot):
    await bot.add_cog(Statistics(bot))
