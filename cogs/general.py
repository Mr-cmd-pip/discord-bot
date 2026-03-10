"""
cogs/general.py — General utility commands
Commands: !help, !ping, !info, !userinfo
"""

import discord
from discord.ext import commands
from datetime import timezone


class General(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx):
        """!help — Show all commands."""
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
            name="🎵 Music",
            value=(
                "`!join`  — Join your voice channel\n"
                "`!play <url or search>`  — Play or queue a track\n"
                "`!pause`  — Pause playback\n"
                "`!resume`  — Resume playback\n"
                "`!skip`  — Skip the current track\n"
                "`!queue`  — Show the track queue\n"
                "`!nowplaying` / `!np`  — Show the current track\n"
                "`!volume <0-100>`  — Adjust volume\n"
                "`!stop`  — Stop and clear the queue\n"
                "`!leave`  — Disconnect from voice\n"
                "`!247`  — Toggle 24/7 mode (stay in VC forever)"
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

    @commands.command(name="ping")
    async def ping(self, ctx):
        """!ping — Check bot latency."""
        ms = round(self.bot.latency * 1000)
        await ctx.send(f"🏓 Pong! `{ms}ms`")

    @commands.command(name="info")
    async def server_info(self, ctx):
        """!info — Display server statistics."""
        guild        = ctx.guild
        online_count = sum(
            1 for m in guild.members
            if m.status != discord.Status.offline and not m.bot
        )
        created_at = guild.created_at.astimezone(timezone.utc).strftime("%B %d, %Y")

        embed = discord.Embed(title=f"📊 {guild.name}", color=discord.Color.green())
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="👑 Owner",         value=guild.owner.mention,      inline=True)
        embed.add_field(name="👥 Total Members", value=str(guild.member_count),  inline=True)
        embed.add_field(name="🟢 Online",        value=str(online_count),        inline=True)
        embed.add_field(name="📅 Created",       value=created_at,               inline=True)
        embed.add_field(name="💬 Channels",      value=str(len(guild.channels)), inline=True)
        embed.add_field(name="🏷️ Roles",         value=str(len(guild.roles)-1),  inline=True)
        embed.set_footer(text=f"Server ID: {guild.id}")
        await ctx.send(embed=embed)

    @commands.command(name="userinfo")
    async def user_info(self, ctx, member: discord.Member = None):
        """!userinfo [@user] — Show profile info for a user."""
        member     = member or ctx.author
        created_at = member.created_at.astimezone(timezone.utc).strftime("%B %d, %Y")
        joined_at  = (
            member.joined_at.astimezone(timezone.utc).strftime("%B %d, %Y")
            if member.joined_at else "Unknown"
        )
        roles         = [r.mention for r in reversed(member.roles) if r.name != "@everyone"]
        roles_display = ", ".join(roles) if roles else "None"

        embed = discord.Embed(
            title=f"👤 {member}",
            color=member.color if member.color != discord.Color.default() else discord.Color.blurple()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="🆔 User ID",               value=str(member.id),  inline=True)
        embed.add_field(name="🤖 Bot?",                  value=str(member.bot), inline=True)
        embed.add_field(name="📅 Account Created",        value=created_at,      inline=False)
        embed.add_field(name="📥 Joined Server",          value=joined_at,       inline=False)
        embed.add_field(name=f"🏷️ Roles ({len(roles)})", value=roles_display,   inline=False)
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(General(bot))