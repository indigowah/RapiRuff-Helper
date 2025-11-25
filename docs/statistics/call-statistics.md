# Call Statistics Plan

## Overview
This feature tracks voice channel activity for each user, including time spent in calls, active days, and times of day. The goal is to provide detailed insights into user engagement in voice channels while respecting privacy.

## Requirements

### Metrics to Track
1. **Total Call Time**: Total duration spent in voice channels.
2. **Session History**: Individual call sessions (start time, end time, duration).
3. **Active Times**: Heatmap of activity by hour of day.
4. **Active Days**: Heatmap of activity by day of week.
5. **Longest Call**: Duration of the longest single session.
6. **Average Call Duration**: Average time per session.

### Data Storage

#### Database Schema
Use the `call_sessions` table defined in the design document, but enhanced:

| Table | Columns |
|-------|---------|
| `call_sessions` | `session_id` (PK), `user_id` (FK), `channel_id`, `join_ts` (TIMESTAMP), `leave_ts` (TIMESTAMP), `duration` (INTEGER, seconds) |

**Note**: `duration` is calculated on completion. `leave_ts` is NULL while the call is active.

#### Aggregated Stats (Optional/Cache)
For quick access to totals without summing all sessions every time:

| Table | Columns |
|-------|---------|
| `user_voice_stats` | `user_id` (PK), `total_time_seconds`, `total_sessions`, `longest_session_seconds`, `last_active_ts` |

## Implementation Details

### Voice State Listener
Create a listener for `on_voice_state_update`:

```python
@commands.Cog.listener()
async def on_voice_state_update(self, member, before, after):
    # Skip bots
    if member.bot:
        return

    # User joined a channel
    if before.channel is None and after.channel is not None:
        await self.start_voice_session(member, after.channel)
    
    # User left a channel
    elif before.channel is not None and after.channel is None:
        await self.end_voice_session(member, before.channel)
    
    # User switched channels (End previous, start new)
    elif before.channel != after.channel:
        await self.end_voice_session(member, before.channel)
        await self.start_voice_session(member, after.channel)
```

### Session Management

#### Start Session
1. Insert a new record into `call_sessions` with `user_id`, `channel_id`, and `join_ts`.
2. `leave_ts` and `duration` are NULL.

#### End Session
1. Find the open session for the user (where `leave_ts` is NULL).
2. Update `leave_ts` to current time.
3. Calculate `duration` = `leave_ts` - `join_ts`.
4. Update `duration` field.
5. Update aggregated `user_voice_stats`.

### Handling Bot Restarts
- **On Startup**: Check for users currently in voice channels.
  - If they have an open session in DB, keep it (or close and restart to account for downtime).
  - If they don't have a session, start one.
- **On Shutdown**: Close all open sessions with the shutdown timestamp.

## Commands

### View Call Stats
```python
@commands.command(name="callstats")
async def call_stats(self, ctx, user: Optional[discord.Member] = None):
    """
    Display voice call statistics for a user.
    
    Usage: /callstats [@user]
    """
    target = user or ctx.author
    
    # Fetch stats from DB
    stats = await self.get_user_voice_stats(target.id)
    
    # Create embed
    embed = discord.Embed(title=f"📞 Call Statistics for {target.display_name}")
    embed.add_field(name="Total Time", value=format_duration(stats.total_time))
    embed.add_field(name="Total Sessions", value=str(stats.total_sessions))
    embed.add_field(name="Average Duration", value=format_duration(stats.avg_duration))
    embed.add_field(name="Longest Call", value=format_duration(stats.longest_session))
    
    await ctx.send(embed=embed)
```

### Leaderboard
```python
@commands.command(name="calltop")
async def call_leaderboard(self, ctx):
    """
    Display leaderboard for most time spent in calls.
    """
    # Query top users by total_time
    # Display in paginated embed
```

## Privacy Considerations
- Users can opt-out of tracking.
- Data deletion command (`/callstats delete`) to wipe history.

## Testing Strategy
1. **Unit Tests**:
   - Test session start/end logic.
   - Test duration calculations.
2. **Integration Tests**:
   - Simulate voice state updates.
   - Verify DB records are created and updated.
   - Test bot restart handling.

## Dependencies
- `peewee` or `sqlalchemy` (for database interactions)
- `python-dateutil` (for time calculations)

---
*Plan created on 2025-11-25*
