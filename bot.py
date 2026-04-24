import os
import asyncio
import yt_dlp
import logging
import ujson # لمعالجة البيانات بسرعة وبدون استهلاك رام
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

# 1. إعداد السجلات (Logs) - مفتاح الحل لأي كراش
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")

YDL_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'scsearch100',
    'nocheckcertificate': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
}

# --- دالة لمعالجة أي خطأ غير متوقع ومنع الكراش ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"حدث خطأ غير متوقع: {context.error}")
    if isinstance(update, Update) and update.message:
        await update.message.reply_text("⚠️ حدث تضارب في السيرفر، تم إعادة تشغيل المحرك تلقائياً.")

# --- نظام الصفحات الذكي (تقليل حجم البيانات) ---
def get_pagination_keyboard(results, page=1):
    results_per_page = 10
    start = (page - 1) * results_per_page
    end = start + results_per_page
    current_results = results[start:end]
    total_pages = (len(results) + 9) // 10

    keyboard = []
    for i, entry in enumerate(current_results):
        # تقليل الـ callback_data لأقصى حد لتجنب كراش الـ 64 بت
        keyboard.append([InlineKeyboardButton(f"🎵 {entry.get('title', 'Audio')[:35]}", callback_data=f"d_{start + i}")])

    nav = []
    if page > 1: nav.append(InlineKeyboardButton("⬅️", callback_data=f"p_{page-1}"))
    nav.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="none"))
    if end < len(results): nav.append(InlineKeyboardButton("➡️", callback_data=f"p_{page+1}"))
    
    keyboard.append(nav)
    return InlineKeyboardMarkup(keyboard)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg.text or msg.text.startswith('/'): return
    
    # فلترة المجموعات
    query = msg.text.replace("بحث", "").strip() if msg.chat.type != constants.ChatType.PRIVATE and msg.text.startswith("بحث") else msg.text
    if msg.chat.type != constants.ChatType.PRIVATE and not msg.text.startswith("بحث"): return

    status = await msg.reply_text("<b>🔍 جاري سحب 100 نتيجة...</b>", parse_mode='HTML')

    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            # استخدام run_in_executor لمنع تجميد السيرفر أثناء البحث الثقيل
            info = await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.extract_info(query, download=False))
            results = info.get('entries', [])
            
            if not results:
                await status.edit_text("❌ لم أجد نتائج.")
                return

            # تخزين النتائج بشكل "نظيف" (فقط البيانات الضرورية لتوفير الرام)
            context.user_data["r"] = [{"t": e.get("title"), "u": e.get("webpage_url"), "d": e.get("duration")} for e in results]
            
            await status.edit_text("<b>🎯 اختر النسخة المطلوبة:</b>", reply_markup=get_pagination_keyboard(results, 1), parse_mode='HTML')
    except Exception as e:
        logger.error(f"Search Error: {e}")
        await status.edit_text("⚠️ السيرفر مشغول، حاول مرة أخرى.")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    results = context.user_data.get("r", [])

    if data.startswith("p_"): # التنقل بين الصفحات
        page = int(data.split("_")[1])
        await query.edit_message_reply_markup(reply_markup=get_pagination_keyboard(results, page))
        await query.answer()

    elif data.startswith("d_"): # التحميل
        idx = int(data.split("_")[1])
        entry = results[idx]
        await query.answer(f"⏳ جاري جلب: {entry['t'][:20]}")
        
        prog = await query.message.reply_text("<b>🚀 جاري التحميل...</b>", parse_mode='HTML')
        try:
            with yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'quiet': True}) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.extract_info(entry['u'], download=False))
                await query.message.reply_audio(
                    audio=info['url'], title=entry['t'], 
                    duration=int(entry['d'] or 0), performer="المقاومة"
                )
                await prog.delete()
        except:
            await prog.edit_text("❌ هذا الرابط تعذر سحبه.")

def main():
    # رفع إعدادات الصبر (Timeout) لضمان عدم حدوث كراش شبكة
    req = HTTPXRequest(http_version="2.0", connect_timeout=60, read_timeout=60)
    app = ApplicationBuilder().token(TOKEN).request(req).build()

    app.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("<b>جاهز لخدمتك!</b>", parse_mode='HTML')))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    # إضافة صائد الأخطاء لضمان بقاء البوت حياً
    app.add_error_handler(error_handler)
    
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
