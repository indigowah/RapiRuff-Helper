# Discord Bot Design Document

## Overview
This document outlines the design of a Discord bot written in Python that provides a suite of utility commands and tracking features for a community. The bot focuses on privacy by **not storing raw message content**, instead tracking statistics and user interactions using a relational database and lightweight JSON/TOML files.

## Features
- **Currency Conversion**: Convert amounts between Chinese Yuan (CNY), South African Rand (ZAR), and US Dollars (USD).
- **Game Rotation**: Manage a personal game rotation list (e.g., Minecraft, Fortnite) with commands to view, add, remove, and set the current game.
- **Due Tracker**: Simple task‑or‑due tracking system that users can add, list, and complete items.
- **VCS Join Notification**: Play a ringtone or send a notification when a user joins a voice channel.
- **Financial Tracker**: Track personal balances in multiple currencies without persisting raw transaction messages.
- **Call Time Statistics**: Record voice channel join/leave timestamps to compute total time spent in calls per user.

## Architecture
- **Bot Framework**: `discord.py` (or its maintained fork `nextcord`).
- **Database**: SQLite for local development, PostgreSQL for production. Stores only numeric/statistical data.
- **File‑Based Stats**: Emoji usage and custom string counters stored in a JSON file (`emoji_stats.json`). This avoids persisting full message text.
- **Embeds & Channel Names**: All user‑visible data is presented via rich embeds or by updating channel names, ensuring information is always visible at a glance.

## Commands
### Currency Conversion
```
/convert <amount> <from_currency> <to_currency>
```
Supported currencies: `CNY`, `ZAR`, `USD`. Uses a simple API or hard‑coded rates refreshed daily.

### Game Rotation
- `/games list` – Show current rotation.
- `/games add <game>` – Add a game to the rotation.
- `/games remove <game>` – Remove a game.
- `/games set <game>` – Set the active game (displayed in an embed).

### Due Tracker
- `/due add <description>` – Add a due item.
- `/due list` – List pending items.
- `/due complete <id>` – Mark an item as completed.

### VCS Join Notification
- Event listener for `on_voice_state_update`.
- When a user joins a voice channel, the bot plays a configurable ringtone file or sends an embed notification.

### Financial Tracker
- `/finance add <amount> <currency>` – Add to personal balance.
- `/finance balance` – Show current balances across currencies.
- `/finance transfer <@user> <amount> <currency>` – Transfer funds between users (balances only).

## AFK Command
- `/afk set <reason>` – Mark user as AFK with an optional reason. Updates a status embed in a designated channel.
- When an AFK user is mentioned, the bot replies to the mentioner with the AFK reason and timestamp.

## Ollama Integration
- Run a lightweight local Ollama model (<180 MB) to answer natural‑language queries.
- `/ask <question>` – Forward the question to the Ollama model, optionally injecting relevant server context (e.g., user status, financial data) and return the response.
- Implemented via a subprocess call to `ollama run <model>`; model files stored locally.

### Financial Tracker Enhancements
- Track monthly income, recurring subscriptions, and expected expenses.
- `/finance income <amount>` – Record monthly income.
- `/finance subscription add <name> <cost>` – Add a recurring subscription.
- `/finance expense add <description> <amount>` – Record an expected expense.
- `/finance report` – Display an embed summarizing income, subscriptions, expenses, and net balance.

### Call Time Statistics
- Bot records timestamps on voice channel join/leave.
- `/stats calltime` – Show total time spent in voice calls for the invoking user or the server.

## Data Storage
### Database Schema (simplified)
| Table | Columns |
|-------|---------|
| `users` | `user_id` (PK), `discord_name`, `created_at` |
| `finances` | `user_id` (FK), `currency`, `balance` |
| `call_sessions` | `session_id` (PK), `user_id` (FK), `join_ts`, `leave_ts` |
| `due_items` | `item_id` (PK), `user_id` (FK), `description`, `created_at`, `completed` |
| `game_prefs` | `user_id` (FK), `game_name`, `position` |

### JSON/TOML Stats File
- Path: `data/emoji_stats.json`
- Structure:
```json
{
  "user_id": {
    "emoji": {
      "😀": 12,
      ":3": 5
    },
    "custom_strings": {
      "thanks": 8
    }
  }
}
```
The bot increments counters when messages contain tracked emojis or strings, **without storing the message text**.

## Embeds & Channel Updates
- **Embeds**: All command responses use rich embeds with fields, timestamps, and appropriate colors.
- **Channel Names**: The bot can rename a designated channel (e.g., `#game-rotation`) to reflect the current active game or number of pending due items.

## Security & Privacy
- No raw message content is persisted.
- All stored data is limited to IDs, timestamps, and numeric counters.
- Permissions: Bot requires `Send Messages`, `Embed Links`, `Connect`, `Speak`, and `Manage Channels` (for renaming).

## Deployment
1. **Environment Variables**: `DISCORD_TOKEN`, `DATABASE_URL`, `RINGTONE_PATH`.
2. **Dockerfile** (example):
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
```
3. **Running**: `docker compose up -d` or `python bot.py` locally.

## Future Enhancements
- Integration with external finance APIs for live exchange rates.
- Web dashboard for visualizing statistics.
- Support for additional games and customizable rotation logic.
- Automated reminders for due items via scheduled messages.

---
*Design document created on 2025‑11‑25.*
