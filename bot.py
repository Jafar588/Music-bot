import os
import asyncio
import yt_dlp
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

YDL_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'scsearch1',
    'nocheckcertificate': True,
}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text or update.message.text.startswith('/'): return
    
    query = update.message.text
    status_msg = await update.message.reply_text("🚀")
    
    loop = asyncio.get_event_loop()
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        try:
            # استخراج الرابط المباشر دون تحميل الملف للسيرفر
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(query, download=False))
            if 'entries' in info: info = info['entries'][0]
            
            url = info.get('url')
            title = info.get('title', 'Audio')
            
            if url:
                # إرسال الصوت عبر الرابط (تليجرام يتولى التحميل)
                await update.message.reply_audio(audio=url, title=title)
                await status_msg.delete()
            else:
                await status_msg.edit_text("❌ لم أجد نتائج.")
        except Exception:
            await status_msg.edit_text("⚠️ حدث خطأ في الجلب.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
