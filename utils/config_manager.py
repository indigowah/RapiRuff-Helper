"""
Configuration manager for handling guild and user specific settings.
"""

import json
from typing import Any, Dict, Optional
from utils.database import GuildSettings, UserSettings

class ConfigManager:
    """
    Manages configuration for guilds and users, with caching.
    """
    def __init__(self):
        self.guild_cache: Dict[int, Dict[str, Any]] = {}
        self.user_cache: Dict[int, Dict[str, Any]] = {}

    async def get_guild_config(self, guild_id: int) -> Dict[str, Any]:
        """
        Get configuration for a guild.
        """
        if guild_id in self.guild_cache:
            return self.guild_cache[guild_id]

        try:
            settings, created = GuildSettings.get_or_create(guild_id=guild_id)
            config = {
                "emoji_tracking_enabled": settings.emoji_tracking_enabled,
                "spam_detection_enabled": settings.spam_detection_enabled,
                "call_tracking_enabled": settings.call_tracking_enabled,
                "settings": json.loads(settings.settings_json) if settings.settings_json else {}
            }
            self.guild_cache[guild_id] = config
            return config
        except Exception as e:
            # Fallback to defaults if DB fails
            return {
                "emoji_tracking_enabled": False,
                "spam_detection_enabled": False,
                "call_tracking_enabled": False,
                "settings": {}
            }

    async def update_guild_config(self, guild_id: int, key: str, value: Any) -> bool:
        """
        Update a specific configuration key for a guild.
        """
        try:
            settings, _ = GuildSettings.get_or_create(guild_id=guild_id)
            
            if key == "emoji_tracking_enabled":
                settings.emoji_tracking_enabled = value
            elif key == "spam_detection_enabled":
                settings.spam_detection_enabled = value
            elif key == "call_tracking_enabled":
                settings.call_tracking_enabled = value
            else:
                # Update JSON settings
                current_settings = json.loads(settings.settings_json) if settings.settings_json else {}
                current_settings[key] = value
                settings.settings_json = json.dumps(current_settings)
            
            settings.save()
            
            # Invalidate cache
            if guild_id in self.guild_cache:
                del self.guild_cache[guild_id]
                
            return True
        except Exception:
            return False

    async def is_feature_enabled(self, guild_id: int, feature: str) -> bool:
        """
        Check if a specific feature is enabled for a guild.
        """
        config = await self.get_guild_config(guild_id)
        return config.get(f"{feature}_enabled", False)

    async def get_user_config(self, user_id: int) -> Dict[str, Any]:
        """
        Get configuration for a user.
        """
        if user_id in self.user_cache:
            return self.user_cache[user_id]

        try:
            settings, created = UserSettings.get_or_create(user_id=user_id)
            config = {
                "opt_out": settings.opt_out,
                "settings": json.loads(settings.settings_json) if settings.settings_json else {}
            }
            self.user_cache[user_id] = config
            return config
        except Exception:
            return {"opt_out": False, "settings": {}}

    async def set_user_opt_out(self, user_id: int, opt_out: bool) -> bool:
        """
        Set user opt-out status.
        """
        try:
            settings, _ = UserSettings.get_or_create(user_id=user_id)
            settings.opt_out = opt_out
            settings.save()
            
            # Invalidate cache
            if user_id in self.user_cache:
                del self.user_cache[user_id]
                
            return True
        except Exception:
            return False
