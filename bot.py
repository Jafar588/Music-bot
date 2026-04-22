import os
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import yt_dlp

# الحصول على التوكن من إعدادات Railway
TOKEN = os.getenv("BOT_TOKEN")

# إعدادات البحث والتحميل
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': 'downloads/%(title)s.%(ext)s', # حفظ في مجلد مؤقت
    'quiet': True
}

async def search_and_download(song_name):
    # إنشاء مجلد للتحميل إذا لم يكن موجوداً
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
        
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch1:{song_name}", download=True)
            if 'entries' in info:
                video_info = info['entries'][0]
                filename = ydl.prepare_filename(video_info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
                return filename
        except Exception as e:
            print(f"Error: {e}")
            return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text: return
    
    song_name = update.message.text
    status_msg = await update.message.reply_text(f"🔎 جاري البحث عن: {song_name}...")

    file_path = await search_and_download(song_name)

    if file_path and os.path.exists(file_path):
        with open(file_path, 'rb') as audio:
            await update.message.reply_audio(audio=audio, title=song_name)
        await status_msg.delete()
        os.remove(file_path) # تنظيف المساحة فوراً
    else:
        await status_msg.edit_text("❌ لم أتمكن من العثور على الأغنية.")

def main():
    if not TOKEN:
        print("خطأ: لم يتم العثور على BOT_TOKEN!")
        return

    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("البوت بدأ العمل...")
    application.run_polling()

if __name__ == '__main__':
    main()
