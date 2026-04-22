import os
import asyncio
import yt_dlp
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")

# إعدادات البحث المتقدمة
YDL_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'scsearch1',
    'nocheckcertificate': True,
}

# 1. رسالة الترحيب الاحترافية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome_text = (
        f"<b>أهلاً بك يا {user_name} في بوت المقاومة 🎵</b>\n\n"
        "أنا بوت متطور لجلب القصائد والأناشيد بأعلى جودة.\n"
        "فقط أرسل اسم ما تبحث عنه وسأقوم بالواجب."
    )
    
    # أزرار تحت الرسالة
    keyboard = [
        [InlineKeyboardButton("⭐ قناة المطور", url="https://t.me/your_channel")],
        [InlineKeyboardButton("📖 طريقة الاستخدام", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='HTML')

# 2. معالجة البحث والتحميل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    if update.message.text.startswith('/'): return

    query = update.message.text
    chat_type = update.message.chat.type

    # تصفية الرسائل في المجموعات (لا يبحث إلا بكلمة "بحث")
    if chat_type in [constants.ChatType.GROUP, constants.ChatType.SUPERGROUP]:
        if not query.startswith("بحث "): return
        search_query = query.replace("بحث ", "").strip()
    else:
        search_query = query

    # رسالة جاري المعالجة الأنيقة
    status_msg = await update.message.reply_text("<b>🔍 جاري البحث في القاعدة...</b>", parse_mode='HTML')

    loop = asyncio.get_event_loop()
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        try:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(search_query, download=False))
            if 'entries' in info: info = info['entries'][0]
            
            url = info.get('url')
            title = info.get('title')
            duration = info.get('duration') # بالثواني
            uploader = info.get('uploader')
            
            # تحويل المدة لدقائق
            mins, secs = divmod(duration, 60) if duration else (0, 0)

            if url:
                caption = (
                    f"<b>✅ تم العثور على الطلب:</b>\n\n"
                    f"<b>📝 العنوان:</b> {title}\n"
                    f"<b>👤 الناشر:</b> {uploader}\n"
                    f"<b>⏳ المدة:</b> {mins}:{secs:02d}\n"
                )
                
                await update.message.reply_audio(
                    audio=url, 
                    title=title, 
                    caption=caption, 
                    parse_mode='HTML'
                )
                await status_msg.delete()
            else:
                await status_msg.edit_text("❌ لم أجد نتائج مطابقة.")
        except Exception as e:
            logging.error(f"Error: {e}")
            await status_msg.edit_text("⚠️ عذراً، واجهت مشكلة في الاتصال بالسيرفر.")

def main():
    app = Application.builder().token(TOKEN).build()
    
    # إضافة الأوامر والمعالجات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 البوت يعمل الآن بأناقة...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
