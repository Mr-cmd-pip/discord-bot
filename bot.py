"""
Discord Utility Bot
===================
A feature-complete Discord bot with general commands, moderation tools,
and an automatic welcome system.

Requirements:
    pip install discord.py python-dotenv

Setup:
    1. Create a .env file in the same directory with:
       DISCORD_TOKEN=your_bot_token_here
       WELCOME_CHANNEL_ID=channel_id_for_welcome_messages (optional)
       WELCOME_MESSAGE=👋 Welcome {username} to {server}! (optional)
    2. Enable the following Privileged Gateway Intents in the Discord Developer Portal:
       - SERVER MEMBERS INTENT
       - MESSAGE CONTENT INTENT
    3. Run with: python bot.py
"""

import discord
from discord.ext import commands
import os
from datetime import timezone
from dotenv import load_dotenv

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID", 0))  # 0 = disabled
WELCOME_MESSAGE = os.getenv(
    "WELCOME_MESSAGE",
    "👋 Welcome {username} to {server}!"
)

# ─────────────────────────────────────────────
# Intents & Bot Setup
# ─────────────────────────────────────────────
intents = discord.Intents.default()
intents.members = True          # Required for on_member_join & member count
intents.message_content = True  # Required to read message content (privileged)
intents.presences = True        # Required for online member count

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ─────────────────────────────────────────────
# Helper: Permission Check
# ─────────────────────────────────────────────
def is_moderator(ctx: commands.Context) -> bool:
    """Returns True if the invoking member has Administrator or Manage Messages permission."""
    perms = ctx.author.guild_permissions
    return perms.administrator or perms.manage_messages


# ═════════════════════════════════════════════
# EVENTS
# ═════════════════════════════════════════════

@bot.event
async def on_ready():
    """Fired when the bot successfully connects to Discord."""
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"   Connected to {len(bot.guilds)} guild(s)")
    await bot.change_presence(activity=discord.Game(name="!help for commands"))


@bot.event
async def on_member_join(member: discord.Member):
    """
    Welcome System
    ──────────────
    Fires when a new member joins the server.
    Sends a configurable welcome message to WELCOME_CHANNEL_ID.
    If no channel is configured the event is silently ignored.
    """
    if not WELCOME_CHANNEL_ID:
        return  # Welcome system disabled

    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    if channel is None:
        print(f"⚠️  Welcome channel {WELCOME_CHANNEL_ID} not found in {member.guild.name}")
        return

    message = WELCOME_MESSAGE.format(
        username=member.mention,
        server=member.guild.name
    )
    await channel.send(message)


# ═════════════════════════════════════════════
# GENERAL COMMANDS
# ═════════════════════════════════════════════

@bot.command(name="ping")
async def ping(ctx: commands.Context):
    """
    !ping
    ─────
    Measures the bot's WebSocket latency and responds with the result.
    """
    latency_ms = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! `{latency_ms}ms`")


@bot.command(name="help")
async def help_command(ctx: commands.Context):
    """
    !help
    ─────
    Displays all available commands grouped by category using a Discord Embed.
    """
    embed = discord.Embed(
        title="📖 Bot Commands",
        description="Here's everything I can do:",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="🔷 General",
        value=(
            "`!ping`  — Check bot latency\n"
            "`!help`  — Show this help menu\n"
            "`!info`  — Server statistics\n"
            "`!userinfo [@user]`  — User profile info"
        ),
        inline=False
    )

    embed.add_field(
        name="🛡️ Moderation *(Admin / Manage Messages)*",
        value=(
            "`!clear <number>`  — Bulk-delete messages (max 100)\n"
            "`!say <text>`  — Make the bot say something"
        ),
        inline=False
    )

    embed.add_field(
        name="👋 Automatic Welcome",
        value="Sends a welcome message whenever a new member joins.",
        inline=False
    )

    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)


@bot.command(name="info")
async def server_info(ctx: commands.Context):
    """
    !info
    ─────
    Displays detailed statistics about the current server using an Embed.
    """
    guild = ctx.guild

    # Count online members (requires presences intent)
    online_count = sum(
        1 for m in guild.members
        if m.status != discord.Status.offline and not m.bot
    )

    # Format creation date
    created_at = guild.created_at.astimezone(timezone.utc).strftime("%B %d, %Y")

    embed = discord.Embed(
        title=f"📊 {guild.name}",
        color=discord.Color.green()
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    embed.add_field(name="👑 Owner",         value=guild.owner.mention,         inline=True)
    embed.add_field(name="👥 Total Members", value=str(guild.member_count),      inline=True)
    embed.add_field(name="🟢 Online",        value=str(online_count),            inline=True)
    embed.add_field(name="📅 Created",       value=created_at,                   inline=True)
    embed.add_field(name="💬 Channels",      value=str(len(guild.channels)),     inline=True)
    embed.add_field(name="🏷️ Roles",         value=str(len(guild.roles) - 1),    inline=True)  # -1 to exclude @everyone

    embed.set_footer(text=f"Server ID: {guild.id}")
    await ctx.send(embed=embed)


@bot.command(name="userinfo")
async def user_info(ctx: commands.Context, member: discord.Member = None):
    """
    !userinfo [@user]
    ─────────────────
    Displays profile information for the mentioned user.
    Defaults to the command author if no user is mentioned.

    Parameter
    ---------
    member : discord.Member, optional
        The member to look up. Defaults to ctx.author.
    """
    member = member or ctx.author  # Default to command invoker

    # Format dates
    created_at = member.created_at.astimezone(timezone.utc).strftime("%B %d, %Y")
    joined_at = (
        member.joined_at.astimezone(timezone.utc).strftime("%B %d, %Y")
        if member.joined_at else "Unknown"
    )

    # Build roles list (exclude @everyone)
    roles = [r.mention for r in reversed(member.roles) if r.name != "@everyone"]
    roles_display = ", ".join(roles) if roles else "None"

    embed = discord.Embed(
        title=f"👤 {member}",
        color=member.color if member.color != discord.Color.default() else discord.Color.blurple()
    )
    embed.set_thumbnail(url=member.display_avatar.url)

    embed.add_field(name="🆔 User ID",          value=str(member.id),    inline=True)
    embed.add_field(name="🤖 Bot?",             value=str(member.bot),   inline=True)
    embed.add_field(name="📅 Account Created",  value=created_at,        inline=False)
    embed.add_field(name="📥 Joined Server",    value=joined_at,         inline=False)
    embed.add_field(name=f"🏷️ Roles ({len(roles)})", value=roles_display, inline=False)

    embed.set_footer(text=f"Requested by {ctx.author}")
    await ctx.send(embed=embed)


# ═════════════════════════════════════════════
# MODERATION COMMANDS
# ═════════════════════════════════════════════

@bot.command(name="clear")
async def clear_messages(ctx: commands.Context, amount: int = None):
    """
    !clear <number>
    ───────────────
    Bulk-deletes a specified number of messages from the current channel.
    Capped at 100 messages per invocation to prevent abuse.

    Permission required: Administrator OR Manage Messages
    """
    # ── Permission check ──
    if not is_moderator(ctx):
        await ctx.send(
            "❌ You need **Administrator** or **Manage Messages** permission to use this command.",
            delete_after=8
        )
        return

    # ── Argument validation ──
    if amount is None:
        await ctx.send("⚠️ Please specify how many messages to delete. e.g. `!clear 10`", delete_after=8)
        return

    if not (1 <= amount <= 100):
        await ctx.send("⚠️ Please provide a number between **1** and **100**.", delete_after=8)
        return

    # ── Deletion (include the command message itself: amount + 1) ──
    deleted = await ctx.channel.purge(limit=amount + 1)

    confirmation = await ctx.send(
        f"✅ Deleted **{len(deleted) - 1}** message(s)."
    )
    # Auto-remove confirmation after 5 seconds
    await confirmation.delete(delay=5)


@bot.command(name="say")
async def say(ctx: commands.Context, *, text: str = None):
    """
    !say <text>
    ───────────
    Makes the bot echo the provided text, then deletes the original command message.

    Permission required: Administrator OR Manage Messages
    """
    # ── Permission check ──
    if not is_moderator(ctx):
        await ctx.send(
            "❌ You need **Administrator** or **Manage Messages** permission to use this command.",
            delete_after=8
        )
        return

    # ── Argument check ──
    if not text:
        await ctx.send("⚠️ Please provide some text. e.g. `!say Hello world!`", delete_after=8)
        return

    # ── Delete invoker's message, then speak ──
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass  # Can't delete — carry on anyway

    await ctx.send(text)
    
# ═════════════════════════════════════════════
# MUSIC COMMANDS
# ═════════════════════════════════════════════

@bot.command(name="join")
async def join(ctx: commands.Context):
    """!join — Bot joins your current voice channel."""
    if not ctx.author.voice:
        await ctx.send("❌ You must be in a voice channel first!", delete_after=8)
        return
    channel = ctx.author.voice.channel
    if ctx.voice_client:
        await ctx.voice_client.move_to(channel)
    else:
        await channel.connect()
    await ctx.send(f"✅ Joined **{channel.name}**")


@bot.command(name="leave")
async def leave(ctx: commands.Context):
    """!leave — Disconnect from voice and clear the queue."""
    if not ctx.voice_client:
        await ctx.send("❌ I'm not in a voice channel.", delete_after=8)
        return
    guild_id = ctx.guild.id
    get_queue(guild_id).clear()
    now_playing.pop(guild_id, None)
    await ctx.voice_client.disconnect()
    await ctx.send("👋 Disconnected from voice channel.")


@bot.command(name="play")
async def play(ctx: commands.Context, *, query: str = None):
    """
    !play <YouTube URL or search terms>
    ────────────────────────────────────
    Plays immediately if idle, otherwise adds to the queue.
    Accepts full YouTube URLs or plain search text.
    """
    if not query:
        await ctx.send("⚠️ Usage: `!play <url or search terms>`", delete_after=8)
        return

    # Auto-join if needed
    if not ctx.voice_client:
        if not ctx.author.voice:
            await ctx.send("❌ Join a voice channel first!", delete_after=8)
            return
        await ctx.author.voice.channel.connect()

    loading_msg = await ctx.send("🔍 Searching...")
    track       = await resolve_track(query)

    if not track:
        await loading_msg.edit(content="❌ Could not find that track. Try a different search.")
        return

    await loading_msg.delete()

    guild_id = ctx.guild.id
    queue    = get_queue(guild_id)

    if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
        # ── Add to queue ──
        queue.append(track)
        embed = discord.Embed(
            title="➕ Added to Queue",
            description=f"[{track['title']}]({track['webpage_url']})",
            color=discord.Color.blue()
        )
        embed.add_field(name="📋 Position in Queue", value=str(len(queue)))
        await ctx.send(embed=embed)
    else:
        # ── Play immediately ──
        now_playing[guild_id] = track
        source = discord.FFmpegPCMAudio(track["url"], **FFMPEG_OPTIONS)
        source = discord.PCMVolumeTransformer(source, volume=0.5)

        def after_play(error):
            if error:
                print(f"Player error: {error}")
            asyncio.run_coroutine_threadsafe(advance_queue(ctx), bot.loop)

        ctx.voice_client.play(source, after=after_play)

        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"[{track['title']}]({track['webpage_url']})",
            color=discord.Color.green()
        )
        duration = track.get("duration", 0)
        if duration:
            mins, secs = divmod(duration, 60)
            embed.add_field(name="⏱️ Duration", value=f"{mins}:{secs:02d}")
        await ctx.send(embed=embed)


@bot.command(name="pause")
async def pause(ctx: commands.Context):
    """!pause — Pause the current track."""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Paused.")
    else:
        await ctx.send("❌ Nothing is playing right now.", delete_after=8)


@bot.command(name="resume")
async def resume(ctx: commands.Context):
    """!resume — Resume a paused track."""
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Resumed.")
    else:
        await ctx.send("❌ Nothing is paused right now.", delete_after=8)


@bot.command(name="skip")
async def skip(ctx: commands.Context):
    """!skip — Skip the current track."""
    if not ctx.voice_client or not ctx.voice_client.is_playing():
        await ctx.send("❌ Nothing is playing right now.", delete_after=8)
        return
    ctx.voice_client.stop()   # triggers after_play → advance_queue
    await ctx.send("⏭️ Skipped.")


@bot.command(name="queue")
async def show_queue(ctx: commands.Context):
    """!queue — Show the music queue."""
    guild_id = ctx.guild.id
    queue    = get_queue(guild_id)
    current  = now_playing.get(guild_id)

    embed = discord.Embed(title="🎶 Music Queue", color=discord.Color.purple())

    embed.add_field(
        name="🎵 Now Playing",
        value=(
            f"[{current['title']}]({current['webpage_url']})"
            if current else "Nothing"
        ),
        inline=False
    )

    if queue:
        queue_list = "\n".join(
            f"`{i+1}.` [{t['title']}]({t['webpage_url']})"
            for i, t in enumerate(queue)
        )
        embed.add_field(name=f"📋 Up Next ({len(queue)} tracks)", value=queue_list, inline=False)
    else:
        embed.add_field(name="📋 Up Next", value="Queue is empty", inline=False)

    await ctx.send(embed=embed)


@bot.command(name="nowplaying", aliases=["np"])
async def now_playing_cmd(ctx: commands.Context):
    """!nowplaying (or !np) — Show the current track."""
    track = now_playing.get(ctx.guild.id)
    if not track:
        await ctx.send("❌ Nothing is playing right now.", delete_after=8)
        return
    embed = discord.Embed(
        title="🎵 Now Playing",
        description=f"[{track['title']}]({track['webpage_url']})",
        color=discord.Color.green()
    )
    duration = track.get("duration", 0)
    if duration:
        mins, secs = divmod(duration, 60)
        embed.add_field(name="⏱️ Duration", value=f"{mins}:{secs:02d}")
    await ctx.send(embed=embed)


@bot.command(name="volume", aliases=["vol"])
async def volume(ctx: commands.Context, level: int = None):
    """!volume <0-100> — Adjust playback volume."""
    if level is None:
        await ctx.send("⚠️ Usage: `!volume <0-100>`", delete_after=8)
        return
    if not (0 <= level <= 100):
        await ctx.send("⚠️ Volume must be between **0** and **100**.", delete_after=8)
        return
    if ctx.voice_client and ctx.voice_client.source:
        ctx.voice_client.source.volume = level / 100
        await ctx.send(f"🔊 Volume set to **{level}%**")
    else:
        await ctx.send("❌ Nothing is playing right now.", delete_after=8)


@bot.command(name="stop")
async def stop(ctx: commands.Context):
    """!stop — Stop playback and clear the queue."""
    guild_id = ctx.guild.id
    get_queue(guild_id).clear()
    now_playing.pop(guild_id, None)
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
    await ctx.send("⏹️ Stopped playback and cleared the queue.")
    

# ═════════════════════════════════════════════
# ERROR HANDLING
# ═════════════════════════════════════════════

@bot.event
async def on_command_error(ctx: commands.Context, error):
    """
    Global error handler — catches common errors and responds with
    a friendly message instead of letting the bot silently fail.
    """
    if isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Member not found. Please mention a valid user.", delete_after=8)

    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ Invalid argument: `{error}`", delete_after=8)

    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument: `{error.param.name}`", delete_after=8)

    elif isinstance(error, commands.CommandNotFound):
        pass  # Silently ignore unknown commands

    elif isinstance(error, discord.Forbidden):
        await ctx.send("❌ I don't have permission to do that.", delete_after=8)

    else:
        # Re-raise unexpected errors so they show up in console logs
        print(f"Unhandled error in command '{ctx.command}': {error}")
        raise error


# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    if not TOKEN:
        raise ValueError(
            "❌ DISCORD_TOKEN not found. "
            "Create a .env file with DISCORD_TOKEN=your_token_here"
        )
    bot.run(TOKEN)