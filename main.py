import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped
from youtubesearchpython import VideosSearch
import yt_dlp
from flask import Flask
from threading import Thread

# Flask keep alive
app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "Music Bot Running 24/7"

def run():
    app_flask.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

# Config
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
STRING_SESSION = os.environ.get("STRING_SESSION")

# Clients
app = Client(
    "MusicBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

assistant = Client(
    "Assistant",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=STRING_SESSION
)

call_py = PyTgCalls(assistant)

if not os.path.exists("downloads"):
    os.makedirs("downloads")

# Download audio
def download_audio(query):
    search = VideosSearch(query, limit=1)
    result = search.result()["result"][0]

    title = result["title"]
    url = result["link"]

    ydl_opts = {
        "format": "bestaudio",
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "quiet": True,
        "noplaylist": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)

    return file_path, title

# Start command
@app.on_message(filters.command("start"))
async def start(_, message):
    text = """
🎵 أهلاً بك في بوت الميوزك العربي

الأوامر:

/تشغيل اسم الاغنية
/ايقاف
/استئناف
/انهاء
/مساعدة
"""

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🎶 قناة البوت", url="https://t.me/")
            ]
        ]
    )

    await message.reply_text(text, reply_markup=buttons)

# Help
@app.on_message(filters.command("مساعدة"))
async def help_cmd(_, message):
    await message.reply_text(
        "🎧 أرسل:\n\n/تشغيل اسم الاغنية"
    )

# Play
@app.on_message(filters.command("تشغيل"))
async def play(_, message):
    if len(message.command) < 2:
        return await message.reply_text("❌ اكتب اسم الأغنية بعد الأمر")

    query = " ".join(message.command[1:])

    msg = await message.reply_text("🔎 جاري البحث وتحميل الأغنية...")

    try:
        file_path, title = download_audio(query)

        await call_py.join_group_call(
            message.chat.id,
            AudioPiped(file_path)
        )

        await msg.edit(
            f"▶️ تم تشغيل:\n\n{title}"
        )

    except Exception as e:
        await msg.edit(f"❌ خطأ:\n{e}")

# Stop
@app.on_message(filters.command("ايقاف"))
async def stop(_, message):
    try:
        await call_py.pause_stream(message.chat.id)
        await message.reply_text("⏸ تم إيقاف التشغيل")
    except:
        await message.reply_text("❌ لا يوجد تشغيل")

# Resume
@app.on_message(filters.command("استئناف"))
async def resume(_, message):
    try:
        await call_py.resume_stream(message.chat.id)
        await message.reply_text("▶️ تم الاستئناف")
    except:
        await message.reply_text("❌ لا يوجد تشغيل متوقف")

# End
@app.on_message(filters.command("انهاء"))
async def end(_, message):
    try:
        await call_py.leave_group_call(message.chat.id)
        await message.reply_text("⏹ تم إنهاء المكالمة")
    except:
        await message.reply_text("❌ لا توجد مكالمة")

# Run
keep_alive()

assistant.start()
call_py.start()
app.run()
