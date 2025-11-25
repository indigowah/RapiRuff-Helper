# Configuration Management Plan

## Overview
This feature provides a centralized and flexible configuration system for all statistics features. It allows server administrators to enable/disable features, set thresholds, and manage permissions via commands and persistent storage.

## Requirements

### Configuration Levels
1. **Global Config**: Environment variables and `config.py` for bot-wide defaults.
2. **Guild Config**: Per-server settings stored in the database.
3. **User Config**: Per-user preferences (e.g., opt-out) stored in the database.

### Settings to Manage

#### Global/System
- `OWNER_ID`: Bot owner ID.
- `DEFAULT_PREFIX`: Command prefix.

#### Per-Guild
- `emoji_tracking_enabled` (bool)
- `spam_detection_enabled` (bool)
- `call_tracking_enabled` (bool)
- `spam_thresholds` (JSON): Custom thresholds for spam detection.
- `ignored_channels` (List[int]): Channels to exclude from tracking.
- `ignored_roles` (List[int]): Roles to exclude from tracking.

#### Per-User
- `tracking_opt_out` (bool): User chooses not to be tracked.

## Data Storage

### Database Schema

#### Guild Settings Table
| Table | Columns |
|-------|---------|
| `guild_settings` | `guild_id` (PK), `emoji_tracking` (bool), `spam_detection` (bool), `call_tracking` (bool), `settings_json` (Text/JSON) |

#### User Settings Table
| Table | Columns |
|-------|---------|
| `user_settings` | `user_id` (PK), `opt_out` (bool), `settings_json` (Text/JSON) |

## Implementation Details

### Config Manager Class
Create a `ConfigManager` class in `utils/config_manager.py`:

```python
class ConfigManager:
    def __init__(self, db):
        self.db = db
        self.cache = {}  # Cache for guild settings
    
    async def get_guild_config(self, guild_id: int) -> dict:
        # Check cache first
        if guild_id in self.cache:
            return self.cache[guild_id]
        
        # Fetch from DB or create default
        config = await self.fetch_or_create_guild_config(guild_id)
        self.cache[guild_id] = config
        return config
    
    async def update_guild_config(self, guild_id: int, key: str, value: Any):
        # Update DB
        # Update cache
        pass
        
    async def is_feature_enabled(self, guild_id: int, feature: str) -> bool:
        config = await self.get_guild_config(guild_id)
        return config.get(f"{feature}_enabled", False)
```

### Commands

#### Admin Configuration
```python
@commands.group(name="config")
@commands.has_permissions(administrator=True)
async def config_group(self, ctx):
    """Manage bot configuration."""
    pass

@config_group.command(name="enable")
async def config_enable(self, ctx, feature: str):
    """
    Enable a feature (emoji, spam, call).
    
    Usage: /config enable <feature>
    """
    valid_features = ["emoji", "spam", "call"]
    if feature not in valid_features:
        await ctx.send("Invalid feature.")
        return
        
    await self.config_manager.update_guild_config(ctx.guild.id, f"{feature}_tracking", True)
    await ctx.send(f"Enabled {feature} tracking.")

@config_group.command(name="disable")
async def config_disable(self, ctx, feature: str):
    """Disable a feature."""
    # ... implementation ...
```

#### User Privacy
```python
@commands.command(name="optout")
async def opt_out(self, ctx):
    """Opt out of all tracking statistics."""
    await self.config_manager.set_user_opt_out(ctx.author.id, True)
    await ctx.send("You have opted out of statistics tracking.")

@commands.command(name="optin")
async def opt_in(self, ctx):
    """Opt in to statistics tracking."""
    await self.config_manager.set_user_opt_out(ctx.author.id, False)
    await ctx.send("You have opted in to statistics tracking.")
```

## Testing Strategy
1. **Unit Tests**:
   - Test caching logic.
   - Test default value fallback.
2. **Integration Tests**:
   - Verify DB updates persist.
   - Verify commands update config correctly.

---
*Plan created on 2025-11-25*
