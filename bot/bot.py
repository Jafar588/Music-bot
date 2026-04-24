import sys
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- (هذا هو الحل السحري) ---
# هذا السطر يخبر بايثون أن يرجع خطوة للخارج (للمجلد الرئيسي) لكي يرى ملف config وبقية المجلدات
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# الآن سيتمكن من قراءة الملفات الخارجية بدون أي خطأ
from config import TOKEN
from core.search import search_and_list
from core.downloader import button_callback

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚡ **مرحباً بك في بوت الموسيقى المطور!**\n\n"
        "💡 **في المجموعات:** ابدأ طلبك بكلمة 'بحث' (مثال: بحث انتي السند).\n"
        "📱 **في الخاص:** أرسل الاسم مباشرة."
    )

def main():
    if not TOKEN: 
        logger.error("Error: No BOT_TOKEN found in environment variables!")
        return

    application = Application.builder().token(TOKEN).build()
    
    # إضافة أمر البداية
    application.add_handler(CommandHandler("start", start))

    # فلتر المجموعات والخاص
    group_filter = filters.ChatType.GROUPS & filters.Regex(r'^بحث\s+')
    private_filter = filters.ChatType.PRIVATE
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & (private_filter | group_filter), search_and_list))
    
    # معالج الأزرار
    application.add_handler(CallbackQueryHandler(button_callback))
    
    logger.info("Bot is running...")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
