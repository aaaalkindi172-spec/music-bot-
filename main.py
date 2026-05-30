import os
import telebot
import yt_dlp
from flask import Flask
from threading import Thread

# ===== Flask Keep Alive =====
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7"

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

# ===== Telegram Bot =====
TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Start command
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🎵 أهلاً بك!\nأرسل رابط يوتيوب وسأقوم بتحميله لك كصوت.")

# Handle links
@bot.message_handler(func=lambda m: True)
def download_audio(message):
    url = message.text

    status = bot.reply_to(message, "⏳ جاري التحميل...")

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'song.%(ext)s',
            'quiet': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        with open(filename, 'rb') as audio:
            bot.send_audio(message.chat.id, audio)

        os.remove(filename)

        bot.delete_message(message.chat.id, status.message_id)

    except Exception:
        bot.edit_message_text("❌ حدث خطأ أثناء التحميل", message.chat.id, status.message_id)


if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
