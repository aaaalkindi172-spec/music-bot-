import os
from flask import Flask
from threading import Thread
import telebot

# إعداد خادم ويب وهمي لمنع توقف منصة Render
app = Flask('')

@app.route('/')
def home():
    return "البوت يعمل بنجاح 24/7!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

# جلب توكن البوت من متغيرات البيئة في Render للحماية
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# أمر البدء /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بك في بوت الموسيقى! 🎵\nأرسل رابط الأغنية أو المقطع الصوتي لتشغيله.")

# استقبال الرسائل النصية
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "تم استلام طلبك، يتم الآن معالجة المقطع الصوتي... ⏳")

# تشغيل الخادم ثم تشغيل البوت
if __name__ == "__main__":
    keep_alive()
    print("البوت بدأ العمل الآن...")
    bot.infinity_polling()
