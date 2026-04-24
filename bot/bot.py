import sys
import os
import asyncio
import logging

# السطر السحري لضمان عمل الاستيراد بين المجلدات
sys.path.append(os.getcwd())

# إعدادات السيرفر وتوكن البوت
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")
process_limiter = asyncio.Semaphore(5)

from telegram import Update, constants
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

# استيراد أدواتك من المجلدات الأخرى
from core.search import search
from core.downloader import extract
from core.utils import pagination, is_url
from core.anti_spam import is_spam
from database.db import add_fav

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("<b>نظام المقاومة الإمبراطوري جاهز للعمل! ⚡</b>", parse_mode='HTML')

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text: return
    user_id = update.effective_user.id
    text = msg.text.strip()

    # فحص السبام
    if is_spam(user_id):
        return

    # فحص إذا كان النص رابطاً
    if is_url(text):
        status = await msg.reply_text("<b>🔗 تم رصد رابط.. جاري المعالجة...</b>", parse_mode='HTML')
        async with process_limiter:
            info = await extract(text)
            if info:
                await msg.reply_audio(
                    audio=info['url'], title=info.get('title', 'صوت مستخرج'),
                    duration=int(info.get('duration', 0)), performer="المقاومة"
                )
                await status.delete()
            else:
                await status.edit_text("❌ تعذر سحب الصوت من الرابط.")
        return

    # منطق المجموعات (يجب أن يبدأ بكلمة بحث)
    if msg.chat.type != constants.ChatType.PRIVATE:
        if not text.startswith("بحث"): return
        query = text.replace("بحث", "").strip()
    else:
        query = text

    if not query: return

    status = await msg.reply_text("<b>🚀 جاري التنقيب في الأرشيف...</b>", parse_mode='HTML')
    
    async with process_limiter:
        results = await search(query)
        if not results:
            await status.edit_text("❌ لم أجد نتائج في الأرشيف العالمي.")
            return

        context.user_data["r"] = results
        await status.edit_text(
            f"<b>🎯 عثرت على {len(results)} نسخة:</b>",
            reply_markup=pagination(results, 1),
            parse_mode='HTML'
        )

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    results = context.user_data.get("r", [])

    if not results:
        await query.answer("⚠️ انتهت الجلسة، ابحث مجدداً.", show_alert=True)
        return

    if data.startswith("p_"):
        page = int(data.split("_")[1])
        await query.edit_message_reply_markup(reply_markup=pagination(results, page))
        await query.answer()

    elif data.startswith("d_"):
        idx = int(data.split("_")[1])
        entry = results[idx]
        await query.answer("⚡ جاري السحب...")
        prog = await query.message.reply_text("<b>⏳ يتم الآن استخراج الرابط المباشر...</b>", parse_mode='HTML')
        
        async with process_limiter:
            info = await extract(entry['u'])
            if info:
                await query.message.reply_audio(
                    audio=info['url'], title=entry['t'], 
                    duration=int(entry['d'] or 0), performer="المقاومة"
                )
                await prog.delete()
            else:
                await prog.edit_text("❌ عذراً، هذا الرابط مقيد حالياً.")

def main():
    if not TOKEN:
        logging.error("❌ التوكن غير موجود! تأكد من إضافته في Railway Variables.")
        return

    req = HTTPXRequest(http_version="2.0", connect_timeout=45, read_timeout=45)
    app = ApplicationBuilder().token(TOKEN).request(req).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
