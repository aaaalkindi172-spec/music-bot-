import os
import telebot
import yt_dlp
from flask import Flask
from threading import Thread
from collections import deque

# ================= WEB SERVER =================
app = Flask(__name__)

@app.route('/')
def home():
    return "PRO ULTRA Music Bot Running"

Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))).start()

# ================= BOT =================
bot = telebot.TeleBot(os.environ.get("BOT_TOKEN"))

queues = {}

def get_queue(chat_id):
    if chat_id not in queues:
        queues[chat_id] = deque()
    return queues[chat_id]

# ================= YOUTUBE SEARCH =================
def search_youtube(query):
    ydl_opts = {
        'format': 'bestaudio',
        'quiet': True,
        'default_search': 'ytsearch1'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        return info['entries'][0]['webpage_url']

# ================= DOWNLOAD =================
def download_audio(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'song.%(ext)s',
        'quiet': True,
        'nocheckcertificate': True,
        'geo_bypass': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    for f in os.listdir():
        if f.startswith("song"):
            return f

# ================= INLINE BUTTONS =================
def controls():
    markup = telebot.types.InlineKeyboardMarkup()

    markup.row(
        telebot.types.InlineKeyboardButton("⏭ Skip", callback_data="skip"),
        telebot.types.InlineKeyboardButton("⏹ Stop", callback_data="stop")
    )

    markup.row(
        telebot.types.InlineKeyboardButton("🔁 Replay", callback_data="replay")
    )

    return markup

# ================= PLAY SYSTEM =================
def play(chat_id):
    q = get_queue(chat_id)

    if not q:
        return

    url = q[0]

    file = download_audio(url)

    with open(file, 'rb') as audio:
        bot.send_audio(
            chat_id,
            audio,
            caption="🎧 Now Playing",
            reply_markup=controls()
        )

    os.remove(file)

# ================= START =================
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "🎵 PRO ULTRA BOT\n\n"
        "✔ أرسل اسم أو رابط\n"
        "✔ يدعم Queue\n"
        "✔ أزرار تحكم"
    )

# ================= MAIN =================
@bot.message_handler(func=lambda m: True)
def handle(message):

    text = message.text.strip()
    chat_id = message.chat.id

    msg = bot.reply_to(message, "⏳ Processing...")

    try:

        if text.startswith("http"):
            url = text
        else:
            url = search_youtube(text)

        q = get_queue(chat_id)
        q.append(url)

        bot.edit_message_text("➕ Added to queue", chat_id, msg.message_id)

        if len(q) == 1:
            play(chat_id)

    except:
        bot.edit_message_text("❌ Error", chat_id, msg.message_id)

# ================= CALLBACKS =================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):

    chat_id = call.message.chat.id
    q = get_queue(chat_id)

    if call.data == "skip":
        if q:
            q.popleft()
            play(chat_id)

        bot.answer_callback_query(call.id, "⏭ Skipped")

    elif call.data == "stop":
        queues[chat_id] = deque()
        bot.answer_callback_query(call.id, "⏹ Stopped")

    elif call.data == "replay":
        if q:
            play(chat_id)

        bot.answer_callback_query(call.id, "🔁 Replaying")

# ================= RUN =================
bot.infinity_polling()
