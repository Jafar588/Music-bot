import os
import asyncio
import yt_dlp
import logging
from shazamio import Shazam
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

# 1. إعدادات النخبة
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")
shazam = Shazam()

# إعدادات البحث العميق (جلب 100 نتيجة)
YDL_SEARCH_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'scsearch100', # القوة الضاربة: 100 نتيجة
    'nocheckcertificate': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
}

# 2. نظام الصفحات الذكي (10 نتائج لكل صفحة)
def get_pagination_keyboard(results, page=1, results_per_page=10):
    start_index = (page - 1) * results_per_page
    end_index = start_index + results_per_page
    current_results = results[start_index:end_index]
    total_pages = (len(results) + results_per_page - 1) // results_per_page

    keyboard = []
    # أزرار النتائج
    for i, entry in enumerate(current_results):
        title = entry.get('title', 'No Title')[:40]
        actual_index = start_index + i
        keyboard.append([InlineKeyboardButton(f"🎵 {title}", callback_data=f"dl_{actual_index}")])

    # أزرار التنقل (السابق | الصفحة | التالي)
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"page_{page-1}"))
    
    nav_row.append(InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="none"))
    
    if end_index < len(results):
        nav_row.append(InlineKeyboardButton("التالي ➡️", callback_data=f"page_{page+1}"))
    
    keyboard.append(nav_row)
    return InlineKeyboardMarkup(keyboard)

# 3. محرك البحث (ساوند كلاود بـ 100 نتيجة)
async def perform_search(update: Update, context, query, status_msg):
    loop = asyncio.get_event_loop()
    try:
        with yt_dlp.YoutubeDL(YDL_SEARCH_OPTS) as ydl:
            await status_msg.edit_text(f"<b>🔍 جاري جلب 100 نتيجة لـ:</b>\n<code>{query}</code>", parse_mode='HTML')
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(query, download=False))
            results = info.get('entries', [])
            
            if not results:
                await status_msg.edit_text("❌ لم أجد نتائج في الأرشيف.")
                return

            # حفظ 100 نتيجة في ذاكرة الجلسة
            context.user_data["search_results"] = results
            context.user_data["current_query"] = query
            
            reply_markup = get_pagination_keyboard(results, page=1)
            await status_msg.edit_text(
                f"<b>🎯 عثرت على {len(results)} نسخة صوتية:</b>\n<i>اختر النسخة المطلوبة للتحميل</i>",
                reply_markup=reply_markup, parse_mode='HTML'
            )
    except Exception as e:
        logging.error(f"Search Error: {e}")
        await status_msg.edit_text("⚠️ السيرفر مشغول حالياً بكثرة الطلبات.")

# 4. معالجة النصوص (المجموعات والخاص)
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg.text or msg.text.startswith('/'): return
    
    if msg.chat.type in [constants.ChatType.GROUP, constants.ChatType.SUPERGROUP]:
        if not msg.text.startswith("بحث"): return
        query = msg.text.replace("بحث", "").strip()
    else:
        query = msg.text

    if not query: return
    status = await msg.reply_text("<b>🚀 جاري تشغيل المحرك العملاق...</b>", parse_mode='HTML')
    await perform_search(update, context, query, status)

# 5. معالج الأزرار (تحميل وتنقل)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    results = context.user_data.get("search_results", [])

    if data.startswith("page_"):
        new_page = int(data.split("_")[1])
        reply_markup = get_pagination_keyboard(results, page=new_page)
        await query.edit_message_text(
            f"<b>🎯 نتائج البحث لـ ({context.user_data.get('current_query')}):</b>\n<i>الصفحة الحالية: {new_page}</i>",
            reply_markup=reply_markup, parse_mode='HTML'
        )
        await query.answer()

    elif data.startswith("dl_"):
        index = int(data.split("_")[1])
        if index >= len(results): return
        entry = results[index]
        await query.answer(f"⏳ جاري جلب: {entry['title'][:20]}...")
        
        progress = await query.message.reply_text("<b>🚀 جاري سحب الملف...</b>", parse_mode='HTML')
        try:
            with yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'quiet': True}) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.extract_info(entry['webpage_url'], download=False))
                await query.message.reply_audio(
                    audio=info['url'],
                    title=info['title'],
                    duration=int(info.get('duration', 0)),
                    performer=info.get('uploader', 'المقاومة'),
                    caption=f"✅ <b>{info['title']}</b>",
                    parse_mode='HTML'
                )
                await progress.delete()
        except:
            await progress.edit_text("❌ هذا الخيار مقيد من المصدر.")

def main():
    # رفع مدة الانتظار لأن جلب 100 نتيجة يحتاج وقتاً أطول قليلاً
    req = HTTPXRequest(http_version="2.0", connect_timeout=60, read_timeout=60)
    app = ApplicationBuilder().token(TOKEN).request(req).build()

    app.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("<b>نظام المقاومة جاهز لـ 100 نتيجة! 🛡️</b>", parse_mode='HTML')))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
