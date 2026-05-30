import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os

TOKEN = os.getenv("DISCORD_TOKEN", "PUT_YOUR_TOKEN_HERE")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

queues = {}

ytdl_opts = {
    "format": "bestaudio/best",
    "quiet": True,
    "default_search": "ytsearch",
    "nocheckcertificate": True,
}

ffmpeg_opts = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}

ytdl = yt_dlp.YoutubeDL(ytdl_opts)


def search(query):
    info = ytdl.extract_info(query, download=False)
    if "entries" in info:
        info = info["entries"][0]
    return {
        "url": info["url"],
        "title": info.get("title", "Unknown")
    }


async def play_next(ctx):
    guild_id = ctx.guild.id

    if guild_id not in queues or len(queues[guild_id]) == 0:
        return

    song = queues[guild_id].pop(0)

    vc = ctx.voice_client

    source = discord.FFmpegPCMAudio(song["url"], **ffmpeg_opts)

    vc.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))

    await ctx.send(f"🎶 Now playing: **{song['title']}**")


@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send("✅ Joined voice channel")
    else:
        await ctx.send("❌ You must be in a voice channel")


@bot.command()
async def play(ctx, *, query):
    if not ctx.voice_client:
        await ctx.invoke(join)

    song = search(query)

    guild_id = ctx.guild.id
    queues.setdefault(guild_id, []).append(song)

    await ctx.send(f"➕ Added: **{song['title']}**")

    if not ctx.voice_client.is_playing():
        await play_next(ctx)


@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭ Skipped")


@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("⛔ Stopped")


@bot.command()
async def queue(ctx):
    guild_id = ctx.guild.id
    q = queues.get(guild_id, [])

    if not q:
        await ctx.send("📭 Queue is empty")
        return

    msg = "\n".join([f"{i+1}. {s['title']}" for i, s in enumerate(q)])
    await ctx.send(f"🎧 Queue:\n{msg}")


bot.run(TOKEN)
