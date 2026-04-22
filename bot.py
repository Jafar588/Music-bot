import os
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import yt_dlp

# الحصول على التوكن من إعدادات Railway
TOKEN = os.getenv("BOT_TOKEN")

# إعدادات البحث والتحميل لساوند كلاود
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'scsearch', # البحث في ساوند كلاود
}

async def search_and_download(song_name):
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
        
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            # البحث في ساوند كلاود عن أول نتيجة
            info = ydl.extract_info(f"scsearch1:{song_name}", download=True)
            if 'entries' in info and len(info['entries']) > 0:
                video_info = info['entries'][0]
                filename = ydl.prepare_filename(video_info)
                
                # تصحيح الامتداد إلى mp3
                base, ext = os.path.splitext(filename)
                mp3_filename = base + ".mp3"
                
                # التأكد من وجود الملف (ساوند كلاود قد يغير الاسم قليلاً)
                if os.path.exists(mp3_filename):
                    return mp3_filename
                return filename
        except Exception as e:
            print(f"Error SC: {e}")
            return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text or update.message.text.startswith('/'):
        return
    
    song_name = update.message.text
    status_msg = await update.message.reply_text(f"🎵 جاري البحث في SoundCloud عن: {song_name}...")

    try:
        file_path = await search_and_download(song_name)

        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as audio:
                await update.message.reply_audio(
                    audio=audio, 
                    title=song_name,
                    caption=f"✅ تم الجلب من SoundCloud"
                )
            await status_msg.delete()
            os.remove(file_path)
        else:
            await status_msg.edit_text("❌ لم أجد هذه الأغنية في SoundCloud، جرب كتابة الاسم بشكل أوضح.")
    except Exception as e:
        print(f"General Error: {e}")
        await status_msg.edit_text("⚠️ حدث خطأ فني.")

def main():
    if not TOKEN:
        print("Error: No BOT_TOKEN found!")
        return

    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("البوت يعمل الآن بالبحث في ساوند كلاود...")
    application.run_polling()

if __name__ == '__main__':
    main()
