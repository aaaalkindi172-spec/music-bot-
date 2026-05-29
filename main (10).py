import os
import asyncio
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls import StreamType
from pytgcalls.types.input_stream import AudioPiped
from yt_dlp import YoutubeDL

# 1. إعداد خادم ويب وهمي لمنصة Render لمنع توقف البوت
app = Flask('')

@app.route('/')
def home():
    return "البوت يعمل بنجاح!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# 2. إعداد بيانات التليجرام (يتم سحبها من متغيرات البيئة)
API_ID = int(os.environ.get("API_ID", 12345))
API_HASH = os.environ.get("API_HASH", "your_api_hash")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token")

# حساب المساعد (الحساب الحسابي مطلوب لتشغيل الصوت في المكالمات)
SESSION_STRING = os.environ.get("SESSION_STRING", "your_session_string")

bot = Client("music_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_client = Client("user_assistant", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
call_py = PyTgCalls(user_client)

# 3. أمر البحث والتشغيل من اليوتيوب
@bot.on_message(filters.command("play") & filters.group)
async def play_audio(client, message):
    query = "".join(message.command[1:])
    if not query:
        await message.reply("يرجى كتابة اسم الأغنية أو الرابط بعد الأمر! مثال: /play القرآن الكريم")
        return

    m = await message.reply("🔎 جاري البحث في يوتيوب والتحميل...")
    
    # إعدادات البحث والتحميل من اليوتيوب
    ydl_opts = {
        "format": "bestaudio/best",
        "default_search": "ytsearch",
        "noplaylist": True,
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(query, download=False)
            if 'entries' in info_dict:
                video = info_dict['entries'][0]
            else:
                video = info_dict
            
            audio_url = video['url']
            title = video['title']
            
        chat_id = message.chat.id
        
        # تشغيل الصوت داخل المكالمة الصوتية للمجموعة
        await call_py.join_group_call(
            chat_id,
            AudioPiped(audio_url),
            stream_type=StreamType.local_stream,
        )
        await m.edit(format(f"🎶 تم بدء التشغيل بنجاح:\n📌 **{title}**"))
        
    except Exception as e:
        await m.edit(f"❌ حدث خطأ أثناء التشغيل: {str(e)}")

# 4. ميزة حماية بسيطة (مثال: منع الروابط)
@bot.on_message(filters.text & filters.group)
async def protection(client, message):
    if "t.me/" in message.text or "http" in message.text:
        # التحقق مما إذا كان المرسل مشرفاً أم لا
        member = await message.chat.get_member(message.from_user.id)
        if member.status not in ["administrator", "creator"]:
            try:
                await message.delete()
                await message.reply_text(f"⚠️ عزيزي {message.from_user.mention}، إرسال الروابط ممنوع هنا!")
            except:
                pass

# تشغيل كل الخدمات معاً
if __name__ == "__main__":
    Thread(target=run_web).start() # تشغيل خادم الويب
    call_py.start()                # تشغيل متحكم المكالمات
    bot.run()                      # تشغيل البوت الأساسي
