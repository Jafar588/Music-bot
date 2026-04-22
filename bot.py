import os
import asyncio
import yt_dlp
import logging
from telegram import Update, constants
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# إعدادات بسيطة جداً وسريعة
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")

# إعدادات التحميل المباشر (بدون تحويل)
YDL_OPTS = {
    'format': 'bestaudio/best', # حمل أفضل صوت موجود فوراً
    'noplaylist': True,
    'outtmpl': 'downloads/%(id)s.%(ext)s', # الحفظ بالامتداد الأصلي لتجنب المعالجة
    'quiet': True,
    'no_warnings': True,
    'default_search': 'scsearch',
    'nocheckcertificate': True,
}

async def fast_download(query):
    if not os.path.exists('downloads'): os.makedirs('downloads')
    
    loop = asyncio.get_event_loop()
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        try:
            # بحث سريع جداً عن نتيجة واحدة
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(f"scsearch1:{query}", download=True))
            if 'entries' in info:
                video = info['entries'][0]
                file_path = ydl.prepare_filename(video)
                return file_path, video.get('title', 'Audio')
            return None, "لم أجد نتائج."
        except Exception as e:
            return None, str(e)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text or update.message.text.startswith('/'): return

    query = update.message.text
    # إرسال رسالة توضح أن العمل بدأ
    status_msg = await update.message.reply_text("⚡️ **جاري الجلب السريع...**", parse_mode=constants.ParseMode.MARKDOWN)
    
    # إشعار التليجرام بأن البوت "يرفع ملفاً" لتقليل توتر المستخدم
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.UPLOAD_VOICE)

    file_path, title = await fast_download(query)

    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, 'rb') as audio:
                await update.message.reply_audio(
                    audio=audio, 
                    title=title, 
                    caption="✅ تم التحميل بالسرعة القصوى."
                )
            await status_msg.delete()
            os.remove(file_path)
        except Exception as e:
            await status_msg.edit_text(f"⚠️ خطأ في الإرسال: {str(e)[:50]}")
    else:
        await status_msg.edit_text(f"❌ فشل: {title}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("البوت السريع انطلق...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__': main()
