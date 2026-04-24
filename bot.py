import os
import asyncio
import yt_dlp
import logging
import ujson
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

# 1. إعدادات النخبة والمراقبة
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")

# إعدادات البحث الصاروخي (جلب 50 نتيجة - العناوين فقط للسرعة)
SEARCH_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'scsearch50', 
    'nocheckcertificate': True,
    'extract_flat': 'in_playlist', # السر الحقيقي للسرعة: يجلب القائمة بدون تحليل الروابط
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
}

# 2. نظام الصفحات (5 نتائج لكل صفحة)
def get_pagination_keyboard(results, page=1):
    per_page = 5
    total_pages = (len(results) + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    current_results = results[start:end]

    keyboard = []
    for i, entry in enumerate(current_results):
        title = entry.get('title', 'Audio')[:35]
        # d_ للتحميل
        keyboard.append([InlineKeyboardButton(f"🎵 {title}", callback_data=f"d_{start + i}")])

    # سطر التحكم (السابق | الصفحة | التالي)
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"p_{page-1}"))
    
    nav.append(InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="none"))
    
    if end < len(results):
        nav.append(InlineKeyboardButton("➡️", callback_data=f"p_{page+1}"))
    
    keyboard.append(nav)
    return InlineKeyboardMarkup(keyboard)

# 3. معالج البحث
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg.text or msg.text.startswith('/'): return
    
    # فلترة المجموعات
    if msg.chat.type != constants.ChatType.PRIVATE:
        if not msg.text.startswith("بحث"): return
        query = msg.text.replace("بحث", "").strip()
    else:
        query = msg.text

    status = await msg.reply_text("<b>⚡ جاري المسح السريع للمصادر...</b>", parse_mode='HTML')

    try:
        with yt_dlp.YoutubeDL(SEARCH_OPTS) as ydl:
            # البحث السريع (Metadata Only)
            info = await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.extract_info(query, download=False))
            results = info.get('entries', [])
            
            if not results:
                await status.edit_text("❌ لم أجد نتائج.")
                return

            # تخزين البيانات الأساسية فقط لتقليل استهلاك الرام
            context.user_data["r"] = [{"t": e.get("title"), "u": e.get("url") or e.get("webpage_url"), "d": e.get("duration")} for e in results]
            
            await status.edit_text(
                f"<b>🎯 عثرت على {len(results)} نسخة:</b>\n<i>اختر من القائمة (5 لكل صفحة)</i>",
                reply_markup=get_pagination_keyboard(results, 1),
                parse_mode='HTML'
            )
    except:
        await status.edit_text("⚠️ السيرفر مشغول حالياً.")

# 4. معالج الأزرار (التنقل والتحميل)
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    results = context.user_data.get("r", [])

    if data.startswith("p_"): # التنقل بين الصفحات
        page = int(data.split("_")[1])
        await query.edit_message_reply_markup(reply_markup=get_pagination_keyboard(results, page))
        await query.answer()

    elif data.startswith("d_"): # التحميل المباشر
        idx = int(data.split("_")[1])
        entry = results[idx]
        await query.answer(f"🚀 جاري جلب المقطع...")
        
        # رسالة جاري التحميل تظهر تحت القائمة لكي لا تختفي القائمة
        prog = await query.message.reply_text("<b>⏳ جاري المعالجة النهائية...</b>", parse_mode='HTML')
        try:
            with yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'quiet': True}) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.extract_info(entry['u'], download=False))
                await query.message.reply_audio(
                    audio=info['url'], 
                    title=entry['t'], 
                    duration=int(entry['d'] or 0),
                    performer="المقاومة"
                )
                await prog.delete()
        except:
            await prog.edit_text("❌ عذراً، هذا الرابط تعذر سحبه.")

def main():
    # إعدادات HTTP/2 لسرعة الرد
    req = HTTPXRequest(http_version="2.0", connect_timeout=45, read_timeout=45)
    app = ApplicationBuilder().token(TOKEN).request(req).build()

    app.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("<b>أهلاً بك! أرسل اسم الأغنية للبحث.</b>", parse_mode='HTML')))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    print("🚀 البوت يعمل الآن بسرعة البرق...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
