"""
cogs/welcome.py — Automatic welcome/farewell messages
Fires on member join and member leave events.
Configure via .env:
    WELCOME_CHANNEL_ID=123456789
    WELCOME_MESSAGE=👋 Welcome {username} to {server}!
"""

import discord
from discord.ext import commands
import os


WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID", 0))
WELCOME_MESSAGE    = os.getenv("WELCOME_MESSAGE", "👋 Welcome {username} to {server}!")


class Welcome(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Send a welcome message when a new member joins."""
        if not WELCOME_CHANNEL_ID:
            return
        channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
        if channel is None:
            return
        message = WELCOME_MESSAGE.format(username=member.mention, server=member.guild.name)
        await channel.send(message)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Send a farewell message when a member leaves."""
        if not WELCOME_CHANNEL_ID:
            return
        channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
        if channel is None:
            return
        await channel.send(
            embed=discord.Embed(
                description=f"👋 **{member.display_name}** has left the server.",
                color=discord.Color.red(),
            )
        )


async def setup(bot):
    await bot.add_cog(Welcome(bot))