# Discord Utility Bot

A multi-server Discord bot written in Python with discord.py. It plays music from YouTube, sends welcome and farewell messages, offers basic moderation tools, and can stay in a voice channel around the clock. Each server gets its own independent music queue and settings.

## Features

**Music**
- Play a track from a YouTube link or a search phrase, with automatic joining of your voice channel
- Per-server queue with pause, resume, skip, stop, volume and now-playing commands
- **24/7 mode:** the bot stays in the voice channel and rejoins if it gets disconnected
- **Auto-leave:** without 24/7 mode, the bot leaves an empty voice channel after a 30-second grace period, and stays if someone comes back
- A keep-alive task runs every 20 seconds to prevent idle voice disconnects
- Embed messages show the track details and queue position

**Welcome messages**
- Greets new members and posts a farewell when someone leaves
- The channel and message text are set through environment variables

**Moderation**
- Bulk-delete up to 100 messages
- Make the bot post a message as itself
- Both are limited to members with Administrator or Manage Messages permission

**General**
- Help menu, latency check, server info and user info

## Commands

The command prefix is `!`.

| Category | Command | What it does |
|---|---|---|
| General | `!help` | Show all commands |
| General | `!ping` | Check bot latency |
| General | `!info` | Show server statistics |
| General | `!userinfo [@user]` | Show a user's profile info |
| Music | `!join` | Join your voice channel |
| Music | `!play <url or search>` | Play a track or add it to the queue |
| Music | `!pause` / `!resume` | Pause or resume playback |
| Music | `!skip` | Skip the current track |
| Music | `!queue` | Show the track queue |
| Music | `!nowplaying` or `!np` | Show the current track |
| Music | `!volume <0-100>` or `!vol` | Adjust the volume (default 50%) |
| Music | `!stop` | Stop playback and clear the queue |
| Music | `!leave` | Disconnect from voice |
| Music | `!247`, `!24/7` or `!stay` | Toggle 24/7 mode |
| Moderation | `!clear <number>` | Delete 1 to 100 messages |
| Moderation | `!say <text>` | Make the bot say something |

## Tech stack

| Area | Tools |
|---|---|
| Language | Python 3.11 |
| Bot framework | discord.py with voice support (cogs architecture) |
| Audio | yt-dlp, FFmpeg, PyNaCl |
| Config | python-dotenv |
| Deployment | Docker, Railway |

## Project structure

```
discord-bot/
├── bot.py             # entry point: intents, cog loading, error handling, voice keep-alive
├── cogs/
│   ├── general.py     # help, ping, info, userinfo
│   ├── music.py       # player, queue, 24/7 mode, auto-leave
│   ├── moderation.py  # clear, say
│   └── welcome.py     # join and leave messages
├── Dockerfile         # Python 3.11 image with FFmpeg
├── railway.json       # Railway start command
├── requirements.txt
└── .gitignore
```

## Getting started

### Requirements

- Python 3.11 (the version the Dockerfile uses)
- [FFmpeg](https://ffmpeg.org/download.html) installed and available on your PATH
- A Discord bot application and token from the [Discord Developer Portal](https://discord.com/developers/applications)
- Node.js or Deno is recommended, because yt-dlp works best with a JavaScript runtime available

### 1. Create the bot and enable intents

In the Developer Portal, open your application, go to **Bot**, and turn on these Privileged Gateway Intents:

- Server Members Intent
- Message Content Intent
- Presence Intent

### 2. Install

```bash
git clone https://github.com/Mr-cmd-pip/discord-bot.git
cd discord-bot
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Install FFmpeg for your system:

```bash
sudo apt install ffmpeg         # Ubuntu or Debian
brew install ffmpeg             # macOS
```

On Windows, download FFmpeg from the link above and add it to your PATH.

### 3. Configure

Create a `.env` file in the project root:

```env
DISCORD_TOKEN=your_bot_token_here
WELCOME_CHANNEL_ID=123456789012345678
WELCOME_MESSAGE=Welcome {username} to {server}!
```

| Variable | Required | Description |
|---|---|---|
| `DISCORD_TOKEN` | Yes | Your bot token |
| `WELCOME_CHANNEL_ID` | No | Channel ID for welcome and farewell messages. Leave it out to turn them off |
| `WELCOME_MESSAGE` | No | Welcome text. `{username}` mentions the new member and `{server}` is the server name |

Never commit your `.env` file. It is already listed in `.gitignore`.

### 4. Run

```bash
python bot.py
```

When it connects, the console shows the bot's name and how many servers it is in.

### Invite the bot to a server

In the Developer Portal, go to **OAuth2**, then **URL Generator**. Select the `bot` scope and these permissions: View Channels, Send Messages, Embed Links, Read Message History, Manage Messages, Connect and Speak. Open the generated link to add the bot to a server where you have Manage Server permission.

## Deployment

### Docker

The included Dockerfile installs FFmpeg and the Python dependencies.

```bash
docker build -t discord-bot .
docker run -d --env-file .env discord-bot
```

### Railway

`railway.json` sets the start command to `python bot.py`. Add your environment variables in the Railway dashboard, and make sure FFmpeg is available in the build, as it is in the Dockerfile.

## Things to know

- The queue and the 24/7 setting are stored in memory, so they reset when the bot restarts
- Links to YouTube playlists play a single track rather than the whole playlist
- The bot needs the Manage Messages permission in a channel for `!clear` to work
