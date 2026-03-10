"""
cogs/moderation.py — Moderation commands
Commands: !clear, !say
Requires: Administrator or Manage Messages permission
"""

import discord
from discord.ext import commands


def is_moderator(ctx: commands.Context) -> bool:
    perms = ctx.author.guild_permissions
    return perms.administrator or perms.manage_messages


class Moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="clear")
    async def clear_messages(self, ctx, amount: int = None):
        """!clear <number> — Bulk-delete messages (max 100). Requires Manage Messages."""
        if not is_moderator(ctx):
            return await ctx.send("❌ You need **Administrator** or **Manage Messages** permission.", delete_after=8)
        if amount is None:
            return await ctx.send("⚠️ Usage: `!clear <number>`", delete_after=8)
        if not (1 <= amount <= 100):
            return await ctx.send("⚠️ Number must be between **1** and **100**.", delete_after=8)
        deleted      = await ctx.channel.purge(limit=amount + 1)
        confirmation = await ctx.send(f"✅ Deleted **{len(deleted) - 1}** message(s).")
        await confirmation.delete(delay=5)

    @commands.command(name="say")
    async def say(self, ctx, *, text: str = None):
        """!say <text> — Make the bot repeat text. Requires Manage Messages."""
        if not is_moderator(ctx):
            return await ctx.send("❌ You need **Administrator** or **Manage Messages** permission.", delete_after=8)
        if not text:
            return await ctx.send("⚠️ Usage: `!say <text>`", delete_after=8)
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        await ctx.send(text)


async def setup(bot):
    await bot.add_cog(Moderation(bot))