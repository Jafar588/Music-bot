import os
import asyncio
import yt_dlp
from telegram import Update, constants
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
    # 1. التأكد من وجود نص
    if not update.message.text or update.message.text.startswith('/'): return
    
    text = update.message.text
    chat_type = update.message.chat.type # معرفة هل الرسالة في مجموعة أم خاص

    # 2. الحل الذكي:
    # إذا كانت في مجموعة، لا يبحث إلا إذا بدأت الرسالة بكلمة "بحث "
    # أما في الخاص (private)، فيبحث عن كل شيء مباشرة
    if chat_type in [constants.ChatType.GROUP, constants.ChatType.SUPERGROUP]:
        if not text.startswith("بحث "):
            return # تجاهل الرسالة تماماً إذا لم تبدأ بكلمة بحث
        query = text.replace("بحث ", "").strip() # حذف كلمة "بحث" وأخذ اسم الأغنية
    else:
        query = text # في الخاص، ابحث عن النص مباشرة

    # 3. إظهار "جاري الكتابة" أو الصاروخ
    status_msg = await update.message.reply_text("🚀")
    
    loop = asyncio.get_event_loop()
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        try:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(query, download=False))
            if 'entries' in info: info = info['entries'][0]
            
            url = info.get('url')
            title = info.get('title', 'Audio')
            
            if url:
                await update.message.reply_audio(audio=url, title=title)
                await status_msg.delete()
            else:
                await status_msg.edit_text("❌ لم أجد نتائج.")
        except Exception:
            await status_msg.edit_text("⚠️ عذراً، لم أستطع العثور على طلبك.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
