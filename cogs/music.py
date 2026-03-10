"""
cogs/music.py — Full music player + 24/7 mode
Commands: !join, !leave, !play, !pause, !resume, !skip,
          !queue, !nowplaying, !volume, !stop, !247
"""

import discord
from discord.ext import commands
import asyncio
import yt_dlp
from collections import deque


# ─────────────────────────────────────────────
# yt-dlp & FFmpeg options
# ─────────────────────────────────────────────
YDL_OPTIONS = {
    "format":         "bestaudio/best",
    "noplaylist":     True,
    "quiet":          True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options":        "-vn",
}


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
async def resolve_track(query: str):
    """Fetch track metadata from YouTube via yt-dlp (non-blocking)."""
    loop = asyncio.get_event_loop()

    def _extract():
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(query, download=False)
            if "entries" in info:
                info = info["entries"][0]
            return {
                "title":       info.get("title", "Unknown"),
                "url":         info["url"],
                "webpage_url": info.get("webpage_url", query),
                "duration":    info.get("duration", 0),
            }

    try:
        return await loop.run_in_executor(None, _extract)
    except Exception as e:
        print(f"yt-dlp error: {e}")
        return None


# ─────────────────────────────────────────────
# Cog
# ─────────────────────────────────────────────
class Music(commands.Cog):

    def __init__(self, bot):
        self.bot                   = bot
        self.music_queues: dict    = {}   # guild_id -> deque
        self.now_playing:  dict    = {}   # guild_id -> track dict
        self.twentyfourseven: set  = set()  # guild_ids with 24/7 on

    # ── Queue helper ───────────────────────────────────────────
    def get_queue(self, guild_id: int) -> deque:
        if guild_id not in self.music_queues:
            self.music_queues[guild_id] = deque()
        return self.music_queues[guild_id]

    # ── Advance queue after track ends ─────────────────────────
    async def advance_queue(self, ctx):
        guild_id = ctx.guild.id
        queue    = self.get_queue(guild_id)

        if not queue:
            self.now_playing.pop(guild_id, None)
            return

        track = queue.popleft()
        self.now_playing[guild_id] = track

        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"[{track['title']}]({track['webpage_url']})",
            color=discord.Color.green()
        )
        if track.get("duration"):
            mins, secs = divmod(track["duration"], 60)
            embed.add_field(name="⏱️ Duration", value=f"{mins}:{secs:02d}")
        await ctx.send(embed=embed)

        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(track["url"], **FFMPEG_OPTIONS), volume=0.5
        )

        def after_play(error):
            if error:
                print(f"Player error: {error}")
            asyncio.run_coroutine_threadsafe(self.advance_queue(ctx), self.bot.loop)

        if ctx.voice_client and ctx.voice_client.is_connected():
            ctx.voice_client.play(source, after=after_play)

    # ── Auto-rejoin on force disconnect ────────────────────────
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Rejoin voice if force-kicked. Always rejoin in 24/7 mode."""
        if member != self.bot.user:
            return
        if before.channel and not after.channel:
            guild_id = before.channel.guild.id
            await asyncio.sleep(2)
            try:
                await before.channel.connect()
                await before.channel.guild.change_voice_state(
                    channel=before.channel, self_mute=False, self_deaf=True
                )
                mode = "[24/7] " if guild_id in self.twentyfourseven else ""
                print(f"🔄 {mode}Rejoined {before.channel.name}")
            except Exception as e:
                print(f"❌ Failed to rejoin: {e}")

    # ══════════════════════════════════════════
    # Commands
    # ══════════════════════════════════════════

    @commands.command(name="join")
    async def join(self, ctx):
        """!join — Join your voice channel."""
        if not ctx.author.voice:
            return await ctx.send("❌ You must be in a voice channel first!", delete_after=8)
        channel = ctx.author.voice.channel
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        await ctx.guild.change_voice_state(channel=channel, self_mute=False, self_deaf=True)
        await ctx.send(f"✅ Joined **{channel.name}**")

    @commands.command(name="leave")
    async def leave(self, ctx):
        """!leave — Disconnect from voice and clear the queue."""
        if not ctx.voice_client:
            return await ctx.send("❌ I'm not in a voice channel.", delete_after=8)
        guild_id = ctx.guild.id
        self.twentyfourseven.discard(guild_id)   # disable 24/7 on manual leave
        self.get_queue(guild_id).clear()
        self.now_playing.pop(guild_id, None)
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Disconnected from voice channel.")

    @commands.command(name="247", aliases=["24/7", "stay"])
    async def twentyfourseven_cmd(self, ctx):
        """!247 — Toggle 24/7 mode. Bot stays in VC forever until disabled."""
        if not ctx.author.voice:
            return await ctx.send("❌ You must be in a voice channel first!", delete_after=8)

        guild_id = ctx.guild.id

        if guild_id in self.twentyfourseven:
            self.twentyfourseven.discard(guild_id)
            await ctx.send(embed=discord.Embed(
                title="💤 24/7 Mode Disabled",
                description="I'll now leave when the channel is empty.\nRun `!247` again to re-enable.",
                color=discord.Color.red()
            ))
        else:
            if not ctx.voice_client:
                await ctx.author.voice.channel.connect()
                await ctx.guild.change_voice_state(
                    channel=ctx.author.voice.channel, self_mute=False, self_deaf=True
                )
            self.twentyfourseven.add(guild_id)
            await ctx.send(embed=discord.Embed(
                title="🔁 24/7 Mode Enabled",
                description="I'll stay in the voice channel no matter what.\nRun `!247` again to disable.",
                color=discord.Color.green()
            ))

    @commands.command(name="play")
    async def play(self, ctx, *, query: str = None):
        """!play <url or search> — Play or queue a track."""
        if not query:
            return await ctx.send("⚠️ Usage: `!play <url or search terms>`", delete_after=8)

        if not ctx.voice_client:
            if not ctx.author.voice:
                return await ctx.send("❌ Join a voice channel first!", delete_after=8)
            await ctx.author.voice.channel.connect()
            await ctx.guild.change_voice_state(
                channel=ctx.author.voice.channel, self_mute=False, self_deaf=True
            )

        loading_msg = await ctx.send("🔍 Searching...")
        track = await resolve_track(query)

        if not track:
            return await loading_msg.edit(content="❌ Could not find that track. Try a different search.")

        await loading_msg.delete()

        guild_id = ctx.guild.id
        queue    = self.get_queue(guild_id)

        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            queue.append(track)
            embed = discord.Embed(
                title="➕ Added to Queue",
                description=f"[{track['title']}]({track['webpage_url']})",
                color=discord.Color.blue()
            )
            embed.add_field(name="📋 Position in Queue", value=str(len(queue)))
            await ctx.send(embed=embed)
        else:
            self.now_playing[guild_id] = track
            source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(track["url"], **FFMPEG_OPTIONS), volume=0.5
            )

            def after_play(error):
                if error:
                    print(f"Player error: {error}")
                asyncio.run_coroutine_threadsafe(self.advance_queue(ctx), self.bot.loop)

            ctx.voice_client.play(source, after=after_play)

            embed = discord.Embed(
                title="🎵 Now Playing",
                description=f"[{track['title']}]({track['webpage_url']})",
                color=discord.Color.green()
            )
            if track.get("duration"):
                mins, secs = divmod(track["duration"], 60)
                embed.add_field(name="⏱️ Duration", value=f"{mins}:{secs:02d}")
            await ctx.send(embed=embed)

    @commands.command(name="pause")
    async def pause(self, ctx):
        """!pause — Pause the current track."""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Paused.")
        else:
            await ctx.send("❌ Nothing is playing right now.", delete_after=8)

    @commands.command(name="resume")
    async def resume(self, ctx):
        """!resume — Resume a paused track."""
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Resumed.")
        else:
            await ctx.send("❌ Nothing is paused right now.", delete_after=8)

    @commands.command(name="skip")
    async def skip(self, ctx):
        """!skip — Skip the current track."""
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            return await ctx.send("❌ Nothing is playing right now.", delete_after=8)
        ctx.voice_client.stop()
        await ctx.send("⏭️ Skipped.")

    @commands.command(name="queue")
    async def show_queue(self, ctx):
        """!queue — Show the music queue."""
        guild_id = ctx.guild.id
        queue    = self.get_queue(guild_id)
        current  = self.now_playing.get(guild_id)

        embed = discord.Embed(title="🎶 Music Queue", color=discord.Color.purple())
        embed.add_field(
            name="🎵 Now Playing",
            value=f"[{current['title']}]({current['webpage_url']})" if current else "Nothing",
            inline=False
        )
        if queue:
            lines = "\n".join(
                f"`{i+1}.` [{t['title']}]({t['webpage_url']})"
                for i, t in enumerate(queue)
            )
            embed.add_field(name=f"📋 Up Next ({len(queue)} tracks)", value=lines, inline=False)
        else:
            embed.add_field(name="📋 Up Next", value="Queue is empty", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="nowplaying", aliases=["np"])
    async def now_playing_cmd(self, ctx):
        """!nowplaying / !np — Show the current track."""
        track = self.now_playing.get(ctx.guild.id)
        if not track:
            return await ctx.send("❌ Nothing is playing right now.", delete_after=8)
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"[{track['title']}]({track['webpage_url']})",
            color=discord.Color.green()
        )
        if track.get("duration"):
            mins, secs = divmod(track["duration"], 60)
            embed.add_field(name="⏱️ Duration", value=f"{mins}:{secs:02d}")
        await ctx.send(embed=embed)

    @commands.command(name="volume", aliases=["vol"])
    async def volume(self, ctx, level: int = None):
        """!volume <0-100> — Adjust playback volume."""
        if level is None:
            return await ctx.send("⚠️ Usage: `!volume <0-100>`", delete_after=8)
        if not (0 <= level <= 100):
            return await ctx.send("⚠️ Volume must be between 0 and 100.", delete_after=8)
        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = level / 100
            await ctx.send(f"🔊 Volume set to **{level}%**")
        else:
            await ctx.send("❌ Nothing is playing right now.", delete_after=8)

    @commands.command(name="stop")
    async def stop(self, ctx):
        """!stop — Stop playback and clear the queue."""
        guild_id = ctx.guild.id
        self.get_queue(guild_id).clear()
        self.now_playing.pop(guild_id, None)
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        await ctx.send("⏹️ Stopped playback and cleared the queue.")


async def setup(bot):
    await bot.add_cog(Music(bot))