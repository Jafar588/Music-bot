import sys
import os
import logging
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# حل مشكلة المسارات
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TOKEN, FORCE_SUB_CHANNEL
from core.search import search_and_list
from core.downloader import button_callback

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- (حيلة الكود 8: خادم ويب وهمي لخداع Render و Hugging Face) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Alive and Running Perfect!"

def run_web_server():
    # Render يعطينا بورت (Port) تلقائي، السيرفر سيستمع له هنا
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
# -------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.message.chat.type
    user_id = update.message.fromuser.id if update.message.from_user else update.message.chat.id

    if chat_type == 'private' and FORCE_SUB_CHANNEL:
        try:
            member = await context.bot.get_chat_member(chat_id=FORCE_SUB_CHANNEL, user_id=user_id)
            if member.status in ['left', 'kicked']:
                keyboard = [[InlineKeyboardButton("📢 اضغط هنا للانضمام للمجموعة", url=f"https://t.me/{FORCE_SUB_CHANNEL.replace('@', '')}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    "❌ **عذراً عزيزي، يجب عليك الانضمام لمجموعتنا أولاً لتتمكن من استخدام البوت في الخاص.**\n\n"
                    "انضم من الزر بالأسفل، ثم أرسل /start",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
                return 
        except Exception as e:
            logger.error(f"Force Sub Error: {e}")

    await update.message.reply_text(
        "⚡ **مرحباً بك في بوت الموسيقى المطور!**\n\n"
        "💡 **في المجموعات:** ابدأ طلبك بكلمة 'بحث' (مثال: بحث انتي السند).\n"
        "📱 **في الخاص:** أرسل الاسم مباشرة."
    )

def main():
    if not TOKEN: 
        logger.error("Error: No BOT_TOKEN found in environment variables!")
        return

    # تشغيل خادم الويب الوهمي في مسار خلفي (Thread) لكي لا يوقف البوت
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()

    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))

    group_filter = filters.ChatType.GROUPS & filters.Regex(r'^بحث\s+')
    private_filter = filters.ChatType.PRIVATE
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & (private_filter | group_filter), search_and_list))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    logger.info("Bot and Web Server are running...")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
