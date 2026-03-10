"""
Discord Utility Bot  (with Voice / Music Support)
==================================================
Entry point — loads all cogs and starts the bot.

Requirements:
    pip install "discord.py[voice]" python-dotenv yt-dlp PyNaCl

Setup:
    1. Create a .env file with:
       DISCORD_TOKEN=your_bot_token_here
       WELCOME_CHANNEL_ID=channel_id   (optional)
       WELCOME_MESSAGE=👋 Welcome {username} to {server}!  (optional)
    2. Enable in Discord Developer Portal:
       - Server Members Intent
       - Message Content Intent
       - Presence Intent
    3. Install FFmpeg:
       Ubuntu:  sudo apt install ffmpeg
       macOS:   brew install ffmpeg
       Windows: https://ffmpeg.org/download.html
    4. Run: python bot.py
"""

import discord
from discord.ext import commands, tasks
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ─────────────────────────────────────────────
# Intents & Bot
# ─────────────────────────────────────────────
intents                 = discord.Intents.default()
intents.members         = True
intents.message_content = True
intents.presences       = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

COGS = [
    "cogs.general",
    "cogs.welcome",
    "cogs.music",
    "cogs.moderation",
]

# ─────────────────────────────────────────────
# Voice Keep-Alive (prevents idle disconnects)
# ─────────────────────────────────────────────
@tasks.loop(seconds=20)
async def voice_keep_alive():
    """Sends a silent ping every 20s to all active voice connections."""
    for vc in bot.voice_clients:
        if vc.is_connected():
            await vc.guild.change_voice_state(channel=vc.channel, self_mute=False, self_deaf=True)

@voice_keep_alive.before_loop
async def before_voice_keep_alive():
    await bot.wait_until_ready()

# ─────────────────────────────────────────────
# Events
# ─────────────────────────────────────────────
@bot.event
async def on_ready():
    voice_keep_alive.start()
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"   Connected to {len(bot.guilds)} guild(s)")
    await bot.change_presence(activity=discord.Game(name="!help for commands"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Member not found.", delete_after=8)
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ Invalid argument: `{error}`", delete_after=8)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing argument: `{error.param.name}`", delete_after=8)
    elif isinstance(error, commands.CommandNotFound):
        pass
    elif isinstance(error, discord.Forbidden):
        await ctx.send("❌ I don't have permission to do that.", delete_after=8)
    else:
        print(f"Unhandled error in '{ctx.command}': {error}")
        raise error

# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────
async def main():
    async with bot:
        for cog in COGS:
            try:
                await bot.load_extension(cog)
                print(f"  ✅ Loaded {cog}")
            except Exception as e:
                print(f"  ❌ Failed to load {cog}: {e}")
        await bot.start(TOKEN)

if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("❌ DISCORD_TOKEN not found. Add it to your .env file.")
    asyncio.run(main())