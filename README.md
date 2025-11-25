# RapiRuff Helper Discord Bot

A feature-rich Discord bot built with `discord.py`, `peewee`, and `rich` logging. This bot provides various utility commands and tracking features for Discord communities.

## Features

- **Currency Conversion**: Convert between CNY, ZAR, and USD
- **Game Rotation**: Manage personal game rotation lists
- **Due Tracker**: Simple task/due tracking system
- **Voice Channel Notifications**: Get notified when users join voice channels
- **Financial Tracker**: Track personal balances in multiple currencies
- **Call Time Statistics**: Track time spent in voice channels
- **AFK System**: Set AFK status with reasons
- **Ollama Integration**: Optional AI-powered question answering

## Project Structure

```
RapiRuff Helper/
├── bot.py                 # Main bot entry point
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env.example          # Example environment variables
├── .gitignore            # Git ignore rules
│
├── cogs/                 # Bot command modules (cogs)
│   ├── base_cog.py       # Base class for all cogs
│   └── example_cog.py    # Example cog with ping command
│
├── utils/                # Shared utilities
│   ├── __init__.py       # Package exports
│   ├── logging.py        # Rich logging setup
│   ├── database.py       # Peewee ORM models
│   └── helpers.py        # Helper functions (embeds, formatters)
│
├── data/                 # Data storage (auto-created)
│   ├── bot.db            # SQLite database
│   └── emoji_stats.json  # Emoji usage statistics
│
├── logs/                 # Log files (auto-created)
│   └── bot.log           # Application logs
│
└── docs/                 # Documentation
    └── design.md         # Design document
```

## Setup

### Prerequisites

- Python 3.10 or higher
- Discord Bot Token ([Create one here](https://discord.com/developers/applications))

### Installation

1. **Clone the repository** (or navigate to the project directory):
   ```bash
   cd "/Users/ethan.reddiar/Projects/RapiRuff Helper"
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your Discord bot token:
   ```env
   DISCORD_TOKEN=your_discord_bot_token_here
   ```

5. **Run the bot**:
   ```bash
   python bot.py
   ```

## Configuration

All configuration is managed through environment variables in the `.env` file:

- `DISCORD_TOKEN`: Your Discord bot token (required)
- `DATABASE_URL`: Database connection string (default: `sqlite:///data/bot.db`)
- `LOG_LEVEL`: Logging level (default: `INFO`)
- `LOG_FILE`: Log file path (default: `logs/bot.log`)
- `RINGTONE_PATH`: Path to voice notification audio file (optional)
- `OLLAMA_MODEL`: Ollama model name (default: `tinyllama`)
- `OLLAMA_ENABLED`: Enable Ollama integration (default: `false`)

## Creating New Cogs

To add new features to the bot, create a new cog in the `cogs/` directory:

```python
from discord.ext import commands
from discord import app_commands
import discord
from cogs.base_cog import BaseCog


class MyCog(BaseCog):
    """Description of your cog."""
    
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
    
    @app_commands.command(name="mycommand", description="Command description")
    async def my_command(self, interaction: discord.Interaction):
        """Your command logic here."""
        await interaction.response.send_message("Hello!")


async def setup(bot: commands.Bot):
    await bot.add_cog(MyCog(bot))
```

The bot will automatically load all cogs in the `cogs/` directory on startup.

## Database Models

The bot uses Peewee ORM with the following models:

- **User**: Discord user information
- **Finance**: User financial balances by currency
- **CallSession**: Voice channel join/leave timestamps
- **DueItem**: Task/due tracking
- **GamePreference**: User game rotation preferences

All models are defined in `utils/database.py`.

## Logging

The bot uses `rich` for beautiful console logging with the following features:

- Color-coded log levels
- Detailed tracebacks with local variables
- Both console and file logging
- Structured log formatting

## Development

### Adding Database Models

1. Add your model class to `utils/database.py`
2. Add the model to the `MODELS` list
3. Restart the bot (tables are created automatically)

### Testing

Run the bot with `LOG_LEVEL=DEBUG` for detailed logging:

```bash
LOG_LEVEL=DEBUG python bot.py
```

## Contributing

This is a private project, but contributions are welcome. Please:

1. Create feature branches
2. Write clear commit messages
3. Test your changes thoroughly
4. Update documentation as needed

## Privacy

This bot prioritizes user privacy:

- No raw message content is stored
- Only statistical data and IDs are persisted
- All tracking is based on events, not message scanning

## License

Private project - All rights reserved.

---

*For detailed feature specifications, see [docs/design.md](docs/design.md)*
