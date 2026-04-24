import os
import asyncio
import yt_dlp
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")

# إعدادات البحث (توازن بين السرعة والدقة)
SEARCH_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'scsearch50', # جلب 50 نتيجة
    'nocheckcertificate': True,
    'extract_flat': True, # جلب البيانات الأساسية بسرعة
}

# دالة توليد القائمة (5 نتائج لكل صفحة)
def get_pagination_keyboard(results, page=1):
    per_page = 5
    total_results = len(results)
    total_pages = (total_results + per_page - 1) // per_page
    
    start = (page - 1) * per_page
    end = start + per_page
    current_results = results[start:end]

    keyboard = []
    for i, entry in enumerate(current_results):
        # التأكد من وجود عنوان، وإلا نضع اسم البحث
        title = entry.get('title') or "نسخة صوتية"
        display_title = f"🎵 {title[:35]}..."
        # تخزين الفهرس الحقيقي للنتيجة
        keyboard.append([InlineKeyboardButton(display_title, callback_data=f"d_{start + i}")])

    # صف الأزرار (سابق | صفحة | تالي)
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"p_{page-1}"))
    
    nav.append(InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="none"))
    
    if page < total_pages:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"p_{page+1}"))
    
    keyboard.append(nav)
    return InlineKeyboardMarkup(keyboard)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg.text or msg.text.startswith('/'): return
    
    # منطق المجموعات
    if msg.chat.type != constants.ChatType.PRIVATE:
        if not msg.text.startswith("بحث"): return
        query = msg.text.replace("بحث", "").strip()
    else:
        query = msg.text

    status = await msg.reply_text("<b>⚡ جاري جلب الأرشيف (50 نسخة)...</b>", parse_mode='HTML')

    try:
        with yt_dlp.YoutubeDL(SEARCH_OPTS) as ydl:
            info = await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.extract_info(query, download=False))
            results = info.get('entries', [])
            
            if not results:
                await status.edit_text("❌ لم أجد نتائج في الأرشيف.")
                return

            # تخزين البيانات الضرورية فقط لضمان السرعة وعدم الضياع
            formatted_results = []
            for e in results:
                formatted_results.append({
                    "t": e.get("title") or "نسخة غير مسمى",
                    "u": e.get("url") or e.get("webpage_url"),
                    "d": e.get("duration")
                })
            
            context.user_data["r"] = formatted_results
            context.user_data["q"] = query

            await status.edit_text(
                f"<b>🎯 عثرت على {len(results)} نسخة لـ:</b>\n<code>{query}</code>",
                reply_markup=get_pagination_keyboard(formatted_results, 1),
                parse_mode='HTML'
            )
    except Exception as e:
        logging.error(f"Search Error: {e}")
        await status.edit_text("⚠️ السيرفر مشغول، حاول مرة أخرى.")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    results = context.user_data.get("r", [])

    if not results:
        await query.answer("⚠️ الجلسة انتهت، ابحث مجدداً.", show_alert=True)
        return

    if data.startswith("p_"):
        page = int(data.split("_")[1])
        await query.edit_message_reply_markup(reply_markup=get_pagination_keyboard(results, page))
        await query.answer()

    elif data.startswith("d_"):
        idx = int(data.split("_")[1])
        entry = results[idx]
        await query.answer(f"🚀 جاري جلب: {entry['t'][:20]}")
        
        prog = await query.message.reply_text("<b>⏳ جاري المعالجة...</b>", parse_mode='HTML')
        
        try:
            # التحميل بطلب "عميق" للرابط المختار فقط
            with yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'quiet': True, 'nocheckcertificate': True}) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.extract_info(entry['u'], download=False))
                await query.message.reply_audio(
                    audio=info['url'], 
                    title=entry['t'], 
                    duration=int(entry['d'] or 0),
                    performer="بوت المقاومة"
                )
                await prog.delete()
        except Exception as e:
            logging.error(f"Download Error: {e}")
            await prog.edit_text("❌ عذراً، هذا الرابط مقيد حالياً. جرب نسخة أخرى.")

def main():
    req = HTTPXRequest(http_version="2.0", connect_timeout=50, read_timeout=50)
    app = ApplicationBuilder().token(TOKEN).request(req).build()

    app.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("<b>أهلاً بك! أرسل اسم ما تبحث عنه.</b>", parse_mode='HTML')))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
