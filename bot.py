import os
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import yt_dlp

# التوكن من إعدادات ريلوي
TOKEN = os.getenv("BOT_TOKEN")

# إعدادات مخصصة لساوند كلاود لتجنب أي حظر
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'quiet': True,
    'default_search': 'scsearch', # البحث في ساوند كلاود فقط
    'nocheckcertificate': True,
}

async def search_and_download(song_name):
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
        
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            # نستخدم scsearch للبحث في ساوند كلاود
            info = ydl.extract_info(f"scsearch1:{song_name}", download=True)
            if 'entries' in info and len(info['entries']) > 0:
                video_info = info['entries'][0]
                filename = ydl.prepare_filename(video_info)
                # تحويل الامتداد برمجياً للتأكد
                base, ext = os.path.splitext(filename)
                return base + ".mp3"
            return None
        except Exception as e:
            print(f"SC Error: {e}")
            return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text or update.message.text.startswith('/'):
        return
    
    song_name = update.message.text
    status_msg = await update.message.reply_text(f"🎵 جاري الجلب من SoundCloud: {song_name}...")

    file_path = await search_and_download(song_name)

    if file_path and os.path.exists(file_path):
        with open(file_path, 'rb') as audio:
            await update.message.reply_audio(audio=audio, title=song_name)
        await status_msg.delete()
        os.remove(file_path)
    else:
        await status_msg.edit_text("❌ لم أجد النتائج المطلوبة في SoundCloud، جرب كتابة الاسم بدقة أكثر.")

def main():
    if not TOKEN: return
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("البوت يعمل الآن عبر SoundCloud...")
    app.run_polling()

if __name__ == '__main__':
    main()
