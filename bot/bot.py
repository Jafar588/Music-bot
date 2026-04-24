import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# إعداد السجلات (Logs)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# سحب التوكن من Variables في ريلوي
TOKEN = os.getenv("BOT_TOKEN")

# إعدادات البحث لـ SoundCloud و Audiomack
# ملاحظة: yt-dlp يدعم المحركين بشكل ممتاز
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة الترحيب"""
    await update.message.reply_text(
        "🚀 **بوت تحميل الموسيقى جاهز!**\n\n"
        "أرسل اسم الأغنية وسأبحث عنها في:\n"
        "☁️ SoundCloud\n"
        "🎵 Audiomack",
        parse_mode="Markdown"
    )

async def search_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """البحث في ساوند كلاود وأوديو ماك"""
    query = update.message.text
    status_msg = await update.message.reply_text(f"🔍 جاري البحث عن '{query}'...")

    # المحركات المستهدفة فقط
    # scsearch: SoundCloud
    # amsearch: Audiomack (مدعوم عبر yt-dlp)
    engines = ['scsearch1', 'amsearch1']
    results = []

    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            for engine in engines:
                source_name = "SoundCloud" if "sc" in engine else "Audiomack"
                logger.info(f"Searching {source_name}...")

                try:
                    # البحث عن نتيجة واحدة من كل محرك
                    info = ydl.extract_info(f"{engine}:{query}", download=False)
                    if info and 'entries' in info and len(info['entries']) > 0:
                        entry = info['entries'][0]
                        results.append({
                            'title': entry.get('title'),
                            'url': entry.get('webpage_url') or entry.get('url'),
                            'source': source_name
                        })
                except Exception as e:
                    logger.error(f"Error in {source_name}: {e}")
                    continue

        if results:
            response = "✅ **نتائج البحث:**\n\n"
            for res in results:
                response += f"🎵 **{res['title']}**\n🔗 [اضغط هنا للاستماع/التحميل]({res['url']})\n📌 المصدر: {res['source']}\n\n"
            
            await status_msg.edit_text(response, parse_mode="Markdown", disable_web_page_preview=False)
        else:
            await status_msg.edit_text("❌ للأسف لم أجد الأغنية في SoundCloud أو Audiomack.")

    except Exception as e:
        logger.error(f"General Error: {e}")
        await status_msg.edit_text("⚠️ حدث خطأ فني، حاول كتابة اسم الأغنية بشكل أوضح.")

def main():
    if not TOKEN:
        logger.error("خطأ: لم يتم ضبط BOT_TOKEN في Variables!")
        return

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_music))

    logger.info("Bot is running without YouTube headaches...")
    application.run_polling(drop_pending_updates=True) # يتجاهل الرسائل القديمة عند التشغيل لتجنب الـ Conflict

if __name__ == '__main__':
    main()
