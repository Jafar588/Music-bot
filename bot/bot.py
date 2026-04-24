import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# سحب التوكن من Railway Variables
TOKEN = os.getenv("BOT_TOKEN")

# إعدادات التحميل (تعديل ليدعم تحميل الملف الفعلي)
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'outtmpl': 'downloads/%(title)s.%(ext)s', # مسار حفظ الملف مؤقتاً
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✨ أرسل لي اسم الأغنية وسأرسلها لك كملف صوتي مباشرة!")

async def search_and_send_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    status_msg = await update.message.reply_text(f"⏳ جاري معالجة وتحميل: {query}...")

    # المحركات: SoundCloud و Audiomack
    engines = ['scsearch1', 'amsearch1']
    
    try:
        # التأكد من وجود مجلد التحميلات
        if not os.path.exists('downloads'):
            os.makedirs('downloads')

        file_path = None
        title = ""

        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            for engine in engines:
                try:
                    # البحث والتحميل الفعلي
                    info = ydl.extract_info(f"{engine}:{query}", download=True)
                    if 'entries' in info and len(info['entries']) > 0:
                        entry = info['entries'][0]
                        file_path = ydl.prepare_filename(entry)
                        title = entry.get('title', 'Unknown')
                        break # توقف عند أول نتيجة ناجحة
                except Exception as e:
                    logger.error(f"Error with engine {engine}: {e}")
                    continue

        if file_path and os.path.exists(file_path):
            # إرسال الملف الصوتي للتليجرام
            await status_msg.edit_text("⚡ جاري الرفع إلى تيليجرام...")
            
            with open(file_path, 'rb') as audio:
                await update.message.reply_audio(
                    audio=audio,
                    title=title,
                    caption=f"🎵: {title}\n✅ تم التحميل بنجاح"
                )
            
            # حذف الملف من السيرفر لتوفير المساحة
            os.remove(file_path)
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ لم يتم العثور على ملف صالح للتحميل.")

    except Exception as e:
        logger.error(f"General Error: {e}")
        await status_msg.edit_text("⚠️ حدث خطأ أثناء التحميل، حاول لاحقاً.")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

def main():
    if not TOKEN:
        return
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_and_send_audio))
    
    # drop_pending_updates تتجاهل الرسائل القديمة لتجنب التعليق
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
