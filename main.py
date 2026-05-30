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
    return "PRO MAX Music Bot is running"

Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))).start()

# ================= BOT =================
bot = telebot.TeleBot(os.environ.get("BOT_TOKEN"))

# Queue لكل مجموعة
queues = {}

def get_queue(chat_id):
    if chat_id not in queues:
        queues[chat_id] = deque()
    return queues[chat_id]

# ================= YT SEARCH =================
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
        'geo_bypass': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    for f in os.listdir():
        if f.startswith("song"):
            return f

# ================= PLAY FUNCTION =================
def play_next(chat_id):
    q = get_queue(chat_id)

    if not q:
        return

    url = q.popleft()
    file = download_audio(url)

    with open(file, 'rb') as audio:
        bot.send_audio(chat_id, audio, caption="🎧 Now Playing")

    os.remove(file)

# ================= COMMANDS =================
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "🎵 PRO MAX MUSIC BOT\n\n"
        "📌 أرسل:\n"
        "- رابط يوتيوب\n"
        "- أو اسم أغنية\n\n"
        "⚡ يدعم Queue و التحكم"
    )

# ================= MAIN HANDLER =================
@bot.message_handler(func=lambda m: True)
def handle(message):

    text = message.text.strip()
    chat_id = message.chat.id

    msg = bot.reply_to(message, "⏳ جاري المعالجة...")

    try:

        # إذا بحث أو رابط
        if text.startswith("http"):
            url = text
        else:
            url = search_youtube(text)

        q = get_queue(chat_id)
        q.append(url)

        bot.edit_message_text("➕ تمت الإضافة إلى قائمة التشغيل", chat_id, msg.message_id)

        # إذا أول عنصر → تشغيل مباشر
        if len(q) == 1:
            play_next(chat_id)

    except Exception:
        bot.edit_message_text("❌ خطأ في المعالجة", chat_id, msg.message_id)

# ================= SKIP =================
@bot.message_handler(commands=['skip'])
def skip(message):
    chat_id = message.chat.id
    q = get_queue(chat_id)

    if q:
        play_next(chat_id)
    else:
        bot.reply_to(message, "❌ لا يوجد شيء للتخطي")

# ================= CLEAR =================
@bot.message_handler(commands=['stop'])
def stop(message):
    chat_id = message.chat.id
    queues[chat_id] = deque()
    bot.reply_to(message, "⏹ تم إيقاف القائمة")

# ================= RUN =================
bot.infinity_polling()
