import os
import asyncio
import yt_dlp
from telegram import Update, constants
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# إعدادات الاستخراج اللحظي (بدون تحميل إذا أمكن)
YDL_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'scsearch',
    'nocheckcertificate': True,
    # حذف أي عمليات فحص إضافية لتقليل زمن الاستجابة (Latency)
    'extract_flat': False, 
    'skip_download': False, 
}

async def get_audio_data(query):
    loop = asyncio.get_event_loop()
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        try:
            # البحث عن النتيجة الأولى واستخراج بياناتها فقط
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(f"scsearch1:{query}", download=True))
            if 'entries' in info:
                video = info['entries'][0]
                return ydl.prepare_filename(video), video.get('title')
            return None, "لم أجد نتائج"
        except Exception as e:
            return None, str(e)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text or update.message.text.startswith('/'): return

    # إشعار المستخدم فوراً (بأقل من 1 ثانية)
    status_msg = await update.message.reply_text("🚀") 
    
    file_path, title = await get_audio_data(update.message.text)

    if file_path and os.path.exists(file_path):
        try:
            # إرسال الملف (هنا السرعة تعتمد على سرعة رفع السيرفر لتليجرام)
            with open(file_path, 'rb') as audio:
                await update.message.reply_audio(audio=audio, title=title)
            await status_msg.delete()
            os.remove(file_path)
        except Exception as e:
            await status_msg.edit_text(f"⚠️ {str(e)}")
    else:
        await status_msg.edit_text("❌ لم يتم الجلب.")

def main():
    # استخدام تقنية الـ Base Request لتقليل زمن الاتصال
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__': main()
