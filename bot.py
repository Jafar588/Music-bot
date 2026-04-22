import os
import asyncio
import yt_dlp
import logging
from shazamio import Shazam
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

# 1. إعدادات المراقبة الفائقة
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")
shazam = Shazam()

# إعدادات المحركات العالمية (تجاوز الحظر)
YDL_COMMON_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
}

# 2. محرك البحث الذكي (متعدد المصادر)
async def perform_search(update: Update, context, query, status_msg):
    loop = asyncio.get_event_loop()
    # ترتيب المصادر حسب الاستقرار: ساوند كلاود -> باند كامب -> أوديومك -> يوتيوب (كحل أخير)
    sources = [
        ('scsearch5', 'SoundCloud'),
        ('bcsearch5', 'Bandcamp'),
        ('amsearch5', 'Audiomack'),
        ('ytsearch5', 'YouTube')
    ]
    
    final_entries = []
    active_source = ""

    for prefix, name in sources:
        try:
            with yt_dlp.YoutubeDL({**YDL_COMMON_OPTS, 'default_search': prefix}) as ydl:
                await status_msg.edit_text(f"<b>🔍 جاري البحث في {name}...</b>", parse_mode='HTML')
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(query, download=False))
                if info.get('entries'):
                    final_entries = info['entries'][:5]
                    active_source = name
                    break # توقف عند أول مصدر يجد نتائج
        except: continue

    if not final_entries:
        await status_msg.edit_text("❌ لم أجد نتائج في جميع المصادر العالمية.")
        return

    keyboard = []
    results_text = f"<b>🎯 نتائج من {active_source} لـ:</b>\n<code>{query}</code>\n\n<i>القائمة مستمرة؛ يمكنك تجربة الكل:</i>"
    
    for i, entry in enumerate(final_entries):
        title = entry.get('title')[:40]
        # تشفير البيانات: dl_معرف_اسم المصدر
        keyboard.append([InlineKeyboardButton(f"🎵 {title}", callback_data=f"dl_{entry['id']}_{active_source[:2].lower()}")])

    await status_msg.edit_text(results_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

# 3. ميزة التعرف (Shazam) مع التحويل التلقائي للبحث
async def identify_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    audio_file = update.message.voice or update.message.audio or update.message.video
    if not audio_file: return
    status = await update.message.reply_text("<b>🎧 جاري تحليل الترددات...</b>", parse_mode='HTML')
    try:
        file = await context.bot.get_file(audio_file.file_id)
        path = f"shazam_{audio_file.file_id}.mp3"
        await file.download_to_drive(path)
        out = await shazam.recognize_song(path)
        if os.path.exists(path): os.remove(path)
        if out.get('track'):
            q = f"{out['track']['title']} {out['track']['subtitle']}"
            await status.edit_text(f"<b>✅ تم التعرف: {q}</b>")
            await perform_search(update, context, q, status)
        else: await status.edit_text("❌ فشل التعرف.")
    except: await status.edit_text("⚠️ خطأ في المحرك.")

# 4. معالج البحث النصي (مع فلترة المجموعات)
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if msg.chat.type in [constants.ChatType.GROUP, constants.ChatType.SUPERGROUP]:
        if not msg.text.startswith("بحث"): return
        q = msg.text.replace("بحث", "").strip()
    else: q = msg.text
    if not q: return
    status = await msg.reply_text("<b>🚀 جاري تشغيل المحركات...</b>", parse_mode='HTML')
    await perform_search(update, context, q, status)

# 5. دالة الجلب "المستمرة" (Persistent Menu)
async def download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, entry_id, src_code = query.data.split('_')
    await query.answer(f"⏳ جاري سحب الملف من {src_code.upper()}...")
    
    # تحديد الرابط بناءً على المصدر
    prefix_map = {'sc': 'https://soundcloud.com/', 'bc': 'https://bandcamp.com/track/', 'am': 'https://audiomack.com/song/', 'yt': 'https://youtube.com/watch?v='}
    url = f"{prefix_map.get(src_code, '')}{entry_id}"
    
    progress = await query.message.reply_text("<b>⏳ يتم الآن استخراج الرابط المباشر...</b>", parse_mode='HTML')
    loop = asyncio.get_event_loop()
    try:
        with yt_dlp.YoutubeDL(YDL_COMMON_OPTS) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            await query.message.reply_audio(
                audio=info['url'],
                title=info['title'],
                duration=int(info.get('duration', 0)),
                performer=info.get('uploader', 'المقاومة'),
                caption=f"✅ المصدر: {src_code.upper()}",
                parse_mode='HTML'
            )
            await progress.delete()
    except Exception:
        await progress.edit_text("❌ هذا الخيار مقيد، جرب خياراً آخر من القائمة.")

def main():
    req = HTTPXRequest(http_version="2.0", connect_timeout=45)
    app = ApplicationBuilder().token(TOKEN).request(req).build()
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("<b>أهلاً بك في نظام المقاومة الشامل 🌐</b>", parse_mode='HTML')))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO | filters.VIDEO, identify_music))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(download_callback))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
