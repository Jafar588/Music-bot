import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# إعداد السجلات (Logs) بشكل نظيف
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# سحب التوكن من إعدادات Railway (Variables)
TOKEN = os.getenv("BOT_TOKEN")

# إعدادات البحث والتحميل
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0', # لتجنب بعض مشاكل الشبكة في السيرفرات
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر البداية"""
    await update.message.reply_text("أهلاً بك! أرسل لي اسم الأغنية وسأبحث لك عنها في SoundCloud و YouTube.")

async def search_and_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل والبحث"""
    query = update.message.text
    status_msg = await update.message.reply_text(f"🔎 جاري البحث عن: {query}...")

    # المحركات التي تستخدمها (نفس التي كانت في السجلات لديك)
    engines = ['ytsearch1', 'scsearch1'] 
    results = []

    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            for engine in engines:
                # تحديث الـ Logs بشكل احترافي
                logger.info(f"Searching on engine: {engine} for query: {query}")
                
                # البحث الفعلي
                info = ydl.extract_info(f"{engine}:{query}", download=False)
                if 'entries' in info and len(info['entries']) > 0:
                    video = info['entries'][0]
                    results.append({
                        'title': video.get('title'),
                        'url': video.get('webpage_url'),
                        'source': "YouTube" if "yt" in engine else "SoundCloud"
                    })

        if results:
            response_text = "✨ **نتائج البحث:**\n\n"
            for res in results:
                response_text += f"🎵 [{res['title']}]({res['url']}) \n📌 المصدر: {res['source']}\n\n"
            
            await status_msg.edit_text(response_text, parse_mode="Markdown", disable_web_page_preview=False)
        else:
            await status_msg.edit_text("❌ لم يتم العثور على نتائج.")

    except Exception as e:
        logger.error(f"Error occurred: {e}")
        await status_msg.edit_text("⚠️ حدث خطأ أثناء البحث، حاول مرة أخرى لاحقاً.")

def main():
    """تشغيل البوت"""
    if not TOKEN:
        logger.error("لم يتم العثور على BOT_TOKEN في متغيرات البيئة!")
        return

    application = Application.builder().token(TOKEN).build()

    # الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_and_download))

    # بدء التشغيل
    logger.info("Bot started successfully...")
    application.run_polling()

if __name__ == '__main__':
    main()
