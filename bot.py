import os
import asyncio
import yt_dlp
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

# إعداد السجلات للمراقبة في Railway Logs
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")

# إعدادات المحرك (تم تحديثها لتجاوز الحظر)
YDL_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch1', # تم التغيير لليوتيوب لأنه الأسرع حالياً
    'nocheckcertificate': True,
    'source_address': '0.0.0.0',
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "<b>أهلاً بك في نسخة البوت المطورة 🚀</b>\n\n"
        "أرسل اسم القصيدة أو رابط يوتيوب مباشرة.\n"
        "<i>مثال: طبعي بحراني</i>"
    )
    await update.message.reply_text(welcome_text, parse_mode='HTML')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    query = update.message.text
    if query.startswith('/'): return

    # نظام "الذكاء" في المجموعات
    chat_type = update.message.chat.type
    if chat_type in [constants.ChatType.GROUP, constants.ChatType.SUPERGROUP]:
        if not query.startswith("بحث "): return
        search_query = query.replace("بحث ", "").strip()
    else:
        search_query = query

    status_msg = await update.message.reply_text("<b>🔍 جاري المعالجة...</b>", parse_mode='HTML')

    loop = asyncio.get_event_loop()
    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            # محاولة جلب المعلومات
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(search_query, download=False))
            
            if 'entries' in info:
                info = info['entries'][0]
            
            url = info.get('url')
            title = info.get('title')
            duration = info.get('duration')
            
            if url:
                mins, secs = divmod(duration, 60) if duration else (0, 0)
                caption = f"<b>✅ تم الجلب بنجاح</b>\n\n<b>📝:</b> {title}\n<b>⏳:</b> {mins}:{secs:02d}"
                
                await update.message.reply_audio(
                    audio=url, 
                    title=title, 
                    caption=caption, 
                    parse_mode='HTML'
                )
                await status_msg.delete()
            else:
                await status_msg.edit_text("❌ لم أجد ملفاً صالحاً.")
                
    except Exception as e:
        logging.error(f"خطأ تقني: {e}")
        # إذا فشل البحث، يخبرك البوت بالسبب في السجلات
        await status_msg.edit_text("⚠️ السيرفر مشغول حالياً، يرجى المحاولة بعد لحظات.")

def main():
    if not TOKEN: return
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
