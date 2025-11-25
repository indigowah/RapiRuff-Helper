# Emoji and Emoticon Tracking Plan

## Overview
This feature tracks emoji usage for each user across the Discord server, including both Unicode emojis (😀, 🎉) and text-based emoticons (:), :3, :D, etc.). The tracking is per-user and privacy-focused, storing only counters without raw message content.

## Requirements

### Emoji Types to Track
1. **Unicode Emojis**: Standard Unicode emoji characters (😀, 🎉, ❤️, etc.)
2. **Text Emoticons**: Common ASCII/text-based emoticons
   - Happy: `:)`, `:D`, `:-)`, `=)`, `=D`, `:3`, `^_^`, `^-^`, `^^`, `:>`, `c:`
   - Sad: `:(`, `:'(`, `:-(`, `=(`, `):`
   - Winking: `;)`, `;D`, `;-)`
   - Surprised: `:O`, `:o`, `o_O`, `O_o`, `o.O`
   - Love: `<3`, `<3`
   - Neutral: `:|`, `:-|`, `=|`
   - Other: `:/`, `:\\`, `-_-`, `>:(`, `>:)`, `XD`, `xD`, `uwu`, `owo`, `>w<`
3. **Custom Discord Emojis**: Server-specific custom emojis (`:custom_emoji:`)

### Data Storage

#### JSON File Structure
Extend the existing `emoji_stats.json` file:

```json
{
  "user_id": {
    "unicode_emojis": {
      "😀": 12,
      "🎉": 5,
      "❤️": 8
    },
    "text_emoticons": {
      ":)": 45,
      ":3": 23,
      "<3": 18,
      "uwu": 7
    },
    "custom_emojis": {
      "custom_emoji_name": 10,
      "another_custom": 3
    },
    "total_emojis": 131,
    "last_updated": "2025-11-25T14:30:16+08:00"
  }
}
```

#### Database Schema Extension
Add a table for aggregated emoji statistics (optional, for faster queries):

| Table | Columns |
|-------|---------|
| `emoji_stats` | `user_id` (FK), `emoji_type` (unicode/text/custom), `emoji_value`, `count`, `last_used` |

**Note**: JSON file is primary storage; database table is optional for performance optimization.

## Implementation Details

### Message Event Listener
Create a new event listener in a dedicated cog:

```python
@commands.Cog.listener()
async def on_message(self, message):
    # Skip bot messages
    if message.author.bot:
        return
    
    # Check if emoji tracking is enabled (per-guild or global config)
    if not await self.is_emoji_tracking_enabled(message.guild.id):
        return
    
    # Extract and count emojis
    await self.process_emoji_tracking(message)
```

### Emoji Detection Logic

1. **Unicode Emoji Detection**:
   - Use the `emoji` library or regex pattern to detect all Unicode emojis
   - Count each unique emoji occurrence per message

2. **Text Emoticon Detection**:
   - Use regex patterns with word boundaries to avoid false positives
   - Priority matching: longer patterns first (`:-)` before `:)`)
   - Case-insensitive matching for patterns like `XD`, `uwu`, `owo`

3. **Custom Discord Emoji Detection**:
   - Parse Discord's emoji format: `<:emoji_name:emoji_id>` or `<a:emoji_name:emoji_id>` (animated)
   - Extract emoji name and count usage

### Emoticon Regex Patterns

```python
EMOTICON_PATTERNS = [
    # Happy variations
    (r':-?\)', ':)'),
    (r':-?D', ':D'),
    (r'=\)', '=)'),
    (r'=D', '=D'),
    (r':3', ':3'),
    (r'\^_\^', '^_^'),
    (r'\^-\^', '^-^'),
    (r'\^\^', '^^'),
    (r':>', ':>'),
    (r'c:', 'c:'),
    
    # Sad variations
    (r':-?\(', ':('),
    (r':\'?\(', ':('),
    (r'=\(', '=('),
    (r'\):', '):'),
    
    # Winking
    (r';-?\)', ';)'),
    (r';-?D', ';D'),
    
    # Surprised
    (r':O', ':O'),
    (r':o', ':o'),
    (r'o_O', 'o_O'),
    (r'O_o', 'O_o'),
    (r'o\.O', 'o.O'),
    
    # Love
    (r'<3', '<3'),
    
    # Neutral
    (r':-?\|', ':|'),
    (r'=\|', '=|'),
    
    # Other
    (r':-?/', ':/'),
    (r':-?\\', ':\\'),
    (r'-_-', '-_-'),
    (r'>:-?\(', '>:('),
    (r'>:-?\)', '>:)'),
    (r'[Xx]D', 'XD'),
    (r'uwu', 'uwu'),
    (r'owo', 'owo'),
    (r'>w<', '>w<'),
]
```

## Configuration

### Config Fields
Add to `config.py`:

```python
# Emoji Tracking Configuration
EMOJI_TRACKING_ENABLED: bool = os.getenv("EMOJI_TRACKING_ENABLED", "false").lower() == "true"
EMOJI_STATS_FILE: Path = DATA_DIR / "emoji_stats.json"
```

### Per-Guild Configuration
Store guild-specific settings in database:

| Table | Columns |
|-------|---------|
| `guild_settings` | `guild_id` (PK), `emoji_tracking_enabled` (BOOLEAN, default=FALSE), `spam_detection_enabled` (BOOLEAN, default=FALSE) |

## Commands

### Toggle Emoji Tracking
```python
@commands.group(name="tracking")
@commands.has_permissions(administrator=True)
async def tracking_group(self, ctx):
    """Manage server tracking settings."""
    pass

@tracking_group.command(name="emoji")
async def toggle_emoji_tracking(self, ctx, enabled: bool):
    """
    Enable or disable emoji tracking for this server.
    
    Usage: /tracking emoji <true/false>
    """
    # Update guild settings in database
    # Update config if global
    # Send confirmation embed
```

### View Emoji Stats (Individual)
```python
@commands.command(name="emojistats")
async def emoji_stats(self, ctx, user: Optional[discord.Member] = None):
    """
    Display emoji usage statistics for a user.
    
    Usage: /emojistats [@user]
    If no user is mentioned, shows stats for the command invoker.
    """
    # Load stats from JSON
    # Create rich embed with top emojis
    # Show breakdown by category (unicode, text, custom)
```

### Leaderboard
```python
@commands.command(name="emojileaderboard")
async def emoji_leaderboard(self, ctx, emoji: Optional[str] = None):
    """
    Display emoji leaderboard for the server.
    
    Usage: /emojileaderboard [emoji]
    If emoji is provided, shows top users for that emoji.
    Otherwise, shows users with most total emoji usage.
    """
    # Aggregate stats across all users
    # Create paginated embed with rankings
```

## Privacy Considerations

- **No Message Storage**: Only emoji counters are stored, never the message content
- **Opt-Out**: Server administrators can disable tracking
- **User Control**: Users can request their emoji data be deleted (GDPR compliance)

## Testing Strategy

1. **Unit Tests**:
   - Test emoji detection regex patterns
   - Test JSON read/write operations
   - Test counter increment logic

2. **Integration Tests**:
   - Send test messages with various emoji types
   - Verify counters update correctly
   - Test configuration toggle functionality

3. **Manual Testing**:
   - Send messages with mixed emojis and emoticons
   - Verify stats command displays correct data
   - Test with custom server emojis

## Dependencies

```
emoji>=2.0.0          # Unicode emoji detection and parsing
```

## Future Enhancements

- Track emoji usage over time (daily/weekly/monthly trends)
- Identify user's "signature" emojis (most frequently used)
- Emoji usage heatmap by time of day
- Cross-server emoji statistics (if bot is in multiple servers)

---
*Plan created on 2025-11-25*
