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