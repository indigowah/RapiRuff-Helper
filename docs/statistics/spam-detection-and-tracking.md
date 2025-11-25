# Spam Detection and Tracking Plan

## Overview
This feature detects and tracks "spam-like" message patterns for each user, including repeated characters, keyboard mashing, and repetitive messages. The goal is to provide statistical insights while maintaining privacy by not storing raw message content.

## Requirements

### Spam Pattern Types

1. **Character Repetition Spam**
   - Messages with excessive repeated characters: `aaaaaaa`, `lololololol`, `hahahaha`
   - Threshold: 4+ consecutive identical characters

2. **Keyboard Mashing**
   - Random character sequences that don't form words: `aebgoiab`, `asdfghjkl`, `qwertyuiop`
   - Detection criteria:
     - Low vowel-to-consonant ratio
     - Consecutive keyboard keys
     - No dictionary words found
     - Minimum length: 5 characters

3. **CAPS LOCK Spam**
   - Messages with excessive uppercase letters
   - Threshold: 70%+ of message is uppercase AND message length > 10 characters

4. **Repeated Messages**
   - Same message sent multiple times in short period
   - Store message hash (not content) to detect duplicates
   - Threshold: 3+ identical messages within 60 seconds

5. **Excessive Length**
   - Unusually long messages (potential copy-paste spam)
   - Threshold: 500+ characters of repeated patterns

## Data Storage

### JSON File Structure
Extend `emoji_stats.json` or create `spam_stats.json`:

```json
{
  "user_id": {
    "spam_stats": {
      "char_repetition": {
        "count": 15,
        "last_triggered": "2025-11-25T14:30:16+08:00",
        "examples": {
          "a": 5,
          "h": 8,
          "l": 2
        }
      },
      "keyboard_mashing": {
        "count": 23,
        "last_triggered": "2025-11-25T13:20:10+08:00",
        "avg_length": 8
      },
      "caps_spam": {
        "count": 7,
        "last_triggered": "2025-11-24T18:45:00+08:00"
      },
      "repeated_messages": {
        "count": 3,
        "last_triggered": "2025-11-23T09:15:30+08:00"
      },
      "total_spam_score": 48,
      "messages_analyzed": 1250,
      "spam_percentage": 3.84
    }
  }
}
```

### Database Schema (Optional)
For advanced querying:

| Table | Columns |
|-------|---------|
| `spam_stats` | `user_id` (FK), `spam_type`, `count`, `last_triggered`, `metadata` (JSON) |
| `message_hashes` | `hash_id` (PK), `user_id` (FK), `msg_hash`, `timestamp`, `expires_at` |

**Note**: Message hashes are temporary (expire after 5 minutes) and used only for duplicate detection.

## Implementation Details

### Spam Detection Functions

#### 1. Character Repetition Detection
```python
def detect_char_repetition(message_content: str) -> tuple[bool, dict]:
    """
    Detect excessive character repetition.
    
    Returns:
        (is_spam, metadata) where metadata contains repeated char and count
    """
    pattern = r'(.)\1{3,}'  # 4+ consecutive identical characters
    matches = re.findall(pattern, message_content, re.IGNORECASE)
    
    if matches:
        return True, {
            "repeated_chars": list(set(matches)),
            "total_repetitions": len(matches)
        }
    return False, {}
```

#### 2. Keyboard Mashing Detection
```python
def detect_keyboard_mashing(text: str) -> bool:
    """
    Detect keyboard mashing patterns.
    """
    # Remove spaces and convert to lowercase
    text = text.replace(" ", "").lower()
    
    if len(text) < 5:
        return False
    
    # Check vowel ratio (should be low for mashing)
    vowels = sum(1 for c in text if c in 'aeiou')
    vowel_ratio = vowels / len(text)
    
    if vowel_ratio > 0.3:  # Too many vowels, probably real text
        return False
    
    # Check for keyboard row patterns
    keyboard_rows = [
        'qwertyuiop',
        'asdfghjkl',
        'zxcvbnm'
    ]
    
    for row in keyboard_rows:
        # Check if text contains 4+ consecutive keyboard keys
        for i in range(len(text) - 3):
            substring = text[i:i+4]
            if substring in row or substring[::-1] in row:
                return True
    
    # Check for low word-like patterns using entropy
    # High entropy = random = likely mashing
    char_counts = {}
    for char in text:
        char_counts[char] = char_counts.get(char, 0) + 1
    
    # Calculate entropy
    import math
    entropy = 0
    for count in char_counts.values():
        p = count / len(text)
        entropy -= p * math.log2(p)
    
    # High entropy (> 3.5) suggests random mashing
    return entropy > 3.5
```

#### 3. CAPS LOCK Detection
```python
def detect_caps_spam(text: str) -> bool:
    """Detect excessive uppercase usage."""
    if len(text) <= 10:
        return False
    
    # Remove spaces and count capitals
    text_no_space = text.replace(" ", "")
    capitals = sum(1 for c in text_no_space if c.isupper())
    letters = sum(1 for c in text_no_space if c.isalpha())
    
    if letters == 0:
        return False
    
    caps_ratio = capitals / letters
    return caps_ratio >= 0.7
```

#### 4. Repeated Message Detection
```python
import hashlib
from datetime import datetime, timedelta

# In-memory cache with expiration
message_cache = {}  # {user_id: [(hash, timestamp), ...]}

def detect_repeated_message(user_id: int, content: str) -> bool:
    """Detect repeated messages using hashing."""
    # Create hash of message content
    msg_hash = hashlib.md5(content.encode()).hexdigest()
    
    current_time = datetime.now()
    cleanup_time = current_time - timedelta(seconds=60)
    
    # Clean up old entries
    if user_id in message_cache:
        message_cache[user_id] = [
            (h, t) for h, t in message_cache[user_id] 
            if t > cleanup_time
        ]
    else:
        message_cache[user_id] = []
    
    # Count identical messages in last 60 seconds
    identical_count = sum(
        1 for h, _ in message_cache[user_id] 
        if h == msg_hash
    )
    
    # Add current message to cache
    message_cache[user_id].append((msg_hash, current_time))
    
    # Spam if 3+ identical messages
    return identical_count >= 2  # 2 previous + current = 3 total
```

### Message Event Listener
```python
@commands.Cog.listener()
async def on_message(self, message):
    if message.author.bot:
        return
    
    # Check if spam detection is enabled
    if not await self.is_spam_detection_enabled(message.guild.id):
        return
    
    # Run spam detection
    await self.process_spam_detection(message)
```

## Configuration

### Config Fields
Add to `config.py`:

```python
# Spam Detection Configuration
SPAM_DETECTION_ENABLED: bool = os.getenv("SPAM_DETECTION_ENABLED", "false").lower() == "true"
SPAM_STATS_FILE: Path = DATA_DIR / "spam_stats.json"

# Spam Thresholds (customizable)
SPAM_CHAR_REPETITION_THRESHOLD: int = int(os.getenv("SPAM_CHAR_REPETITION_THRESHOLD", "4"))
SPAM_CAPS_RATIO_THRESHOLD: float = float(os.getenv("SPAM_CAPS_RATIO_THRESHOLD", "0.7"))
SPAM_REPEATED_MSG_COUNT: int = int(os.getenv("SPAM_REPEATED_MSG_COUNT", "3"))
SPAM_REPEATED_MSG_WINDOW: int = int(os.getenv("SPAM_REPEATED_MSG_WINDOW", "60"))  # seconds
```

## Commands

### Toggle Spam Detection
```python
@tracking_group.command(name="spam")
@commands.has_permissions(administrator=True)
async def toggle_spam_detection(self, ctx, enabled: bool):
    """
    Enable or disable spam detection for this server.
    
    Usage: /tracking spam <true/false>
    """
    # Update guild settings
    await self.update_guild_setting(ctx.guild.id, "spam_detection_enabled", enabled)
    
    # Send confirmation
    status = "enabled" if enabled else "disabled"
    await ctx.send(embed=self.create_success_embed(
        title="Spam Detection Updated",
        description=f"Spam detection has been **{status}** for this server."
    ))
```

### View Spam Stats
```python
@commands.command(name="spamstats")
async def spam_stats(self, ctx, user: Optional[discord.Member] = None):
    """
    Display spam statistics for a user.
    
    Usage: /spamstats [@user]
    """
    target = user or ctx.author
    stats = await self.load_spam_stats(target.id)
    
    # Create embed with statistics
    embed = discord.Embed(
        title=f"📊 Spam Statistics for {target.display_name}",
        color=discord.Color.blue()
    )
    
    if stats:
        spam_data = stats.get("spam_stats", {})
        embed.add_field(
            name="Character Repetition",
            value=f"{spam_data.get('char_repetition', {}).get('count', 0)} times",
            inline=True
        )
        embed.add_field(
            name="Keyboard Mashing",
            value=f"{spam_data.get('keyboard_mashing', {}).get('count', 0)} times",
            inline=True
        )
        embed.add_field(
            name="CAPS SPAM",
            value=f"{spam_data.get('caps_spam', {}).get('count', 0)} times",
            inline=True
        )
        embed.add_field(
            name="Repeated Messages",
            value=f"{spam_data.get('repeated_messages', {}).get('count', 0)} times",
            inline=True
        )
        embed.add_field(
            name="Total Spam Score",
            value=f"{spam_data.get('total_spam_score', 0)}",
            inline=True
        )
        embed.add_field(
            name="Spam Percentage",
            value=f"{spam_data.get('spam_percentage', 0):.2f}%",
            inline=True
        )
    else:
        embed.description = "No spam statistics available for this user."
    
    await ctx.send(embed=embed)
```

## Privacy Considerations

- **No Message Storage**: Only spam pattern counters are stored
- **Hash-Only for Duplicates**: Message hashes expire after 5 minutes
- **Transparency**: Users can view their own spam statistics
- **No Punishment System**: This is for statistics only, not moderation

## Testing Strategy

1. **Unit Tests**:
   - Test each spam detection function with edge cases
   - Verify thresholds work correctly
   - Test JSON serialization/deserialization

2. **Integration Tests**:
   - Send messages with various spam patterns
   - Verify counters increment correctly
   - Test message hash expiration

3. **Manual Testing**:
   - Test with real-world spam examples
   - Verify no false positives on normal messages
   - Check stats command output

## Performance Considerations

- Use async I/O for JSON file operations
- Implement caching for frequently accessed stats
- Clean up expired message hashes periodically
- Consider batching stats updates (every 10 spam detections instead of every single one)

## Future Enhancements

- Configurable thresholds per server
- Spam trend analysis over time
- Integration with moderation tools (optional)
- Machine learning for improved spam detection

---
*Plan created on 2025-11-25*
