import os
import asyncio
import traceback
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import yt_dlp

TOKEN = os.getenv("BOT_TOKEN")

# إعدادات قوية جداً لمحاولة كسر الحظر
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'quiet': False, # جعلناه False لنرى التفاصيل في السجلات
    'no_warnings': False,
    'default_search': 'ytsearch', 
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': True,
    'source_address': '0.0.0.0',
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

async def search_and_download(song_name):
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
        
    # نحاول البحث أولاً في يوتيوب بطريقة "ytsearch"
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            # هنا نطلب المعلومات فقط أولاً للتأكد من البحث
            search_result = ydl.extract_info(f"ytsearch1:{song_name}", download=True)
            if 'entries' in search_result and len(search_result['entries']) > 0:
                video_info = search_result['entries'][0]
                filename = ydl.prepare_filename(video_info)
                base, ext = os.path.splitext(filename)
                mp3_filename = base + ".mp3"
                return mp3_filename, None
            else:
                return None, "لم تظهر أي نتائج في البحث."
        except Exception as e:
            # إرجاع الخطأ الحقيقي لتحليله
            error_msg = str(e).split('\n')[0] # نأخذ أول سطر من الخطأ فقط
            return None, error_msg

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text or update.message.text.startswith('/'):
        return
    
    song_name = update.message.text
    status_msg = await update.message.reply_text(f"⏳ جاري محاولة جلب: {song_name}...")

    try:
        file_path, error = await search_and_download(song_name)

        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as audio:
                await update.message.reply_audio(audio=audio, title=song_name)
            await status_msg.delete()
            os.remove(file_path)
        else:
            # هنا البوت سيخبرك بالسبب الحقيقي للفشل
            await status_msg.edit_text(f"❌ فشل الطلب.\nالسبب: {error}")
            
    except Exception as e:
        await status_msg.edit_text(f"⚠️ خطأ فني: {str(e)[:50]}")

def main():
    if not TOKEN: return
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("البوت يعمل الآن بنظام التشخيص...")
    app.run_polling()

if __name__ == '__main__':
    main()
