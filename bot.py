import os
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import yt_dlp

# الحصول على التوكن من إعدادات Railway
TOKEN = os.getenv("BOT_TOKEN")

# إعدادات البحث والتحميل المطورة لتجنب الحظر
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    # هذا السطر مهم جداً لإيهام يوتيوب أن الطلب من متصفح حقيقي
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
}

async def search_and_download(song_name):
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
        
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            # البحث عن اسم الأغنية
            info = ydl.extract_info(f"ytsearch1:{song_name}", download=True)
            if 'entries' in info and len(info['entries']) > 0:
                video_info = info['entries'][0]
                filename = ydl.prepare_filename(video_info)
                # التأكد من امتداد الملف بعد التحويل لـ mp3
                base, ext = os.path.splitext(filename)
                mp3_filename = base + ".mp3"
                return mp3_filename
        except Exception as e:
            print(f"خطأ أثناء البحث أو التحميل: {e}")
            return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # نأخذ النص فقط إذا لم يكن أمراً برمجياً
    if not update.message or not update.message.text or update.message.text.startswith('/'):
        return
    
    song_name = update.message.text
    status_msg = await update.message.reply_text(f"🔎 جاري البحث عن: {song_name}...")

    try:
        file_path = await search_and_download(song_name)

        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as audio:
                await update.message.reply_audio(
                    audio=audio, 
                    title=song_name,
                    caption=f"تم التحميل بواسطة بوتك الخاص 🎵"
                )
            await status_msg.delete()
            os.remove(file_path) # حذف الملف لتوفير مساحة السيرفر
        else:
            await status_msg.edit_text("❌ لم أتمكن من العثور على الأغنية أو ربما هناك حظر من يوتيوب حالياً.")
    except Exception as e:
        print(f"خطأ في معالجة الرسالة: {e}")
        await status_msg.edit_text("⚠️ حدث خطأ فني أثناء المعالجة.")

def main():
    if not TOKEN:
        print("خطأ: لم يتم العثور على BOT_TOKEN!")
        return

    application = Application.builder().token(TOKEN).build()
    
    # الرد على الرسائل النصية فقط
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("البوت بدأ العمل بنجاح...")
    application.run_polling()

if __name__ == '__main__':
    main()