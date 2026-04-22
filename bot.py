import os
import asyncio
import yt_dlp
import logging
from shazamio import Shazam
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

# 1. إعدادات المراقبة (Logs) - لمتابعة حالة السيرفر في Railway
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")
shazam = Shazam()

# إعدادات المحرك العالمي
YDL_COMMON_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'retries': 5,
}

# 2. محرك البحث الهجين (البحث في المصادر العالمية)
async def perform_search(update: Update, context, query, status_msg):
    loop = asyncio.get_event_loop()
    # ترتيب المصادر لضمان أعلى استقرار
    sources = [('scsearch5', 'SoundCloud'), ('bcsearch5', 'Bandcamp'), ('amsearch5', 'Audiomack'), ('ytsearch5', 'YouTube')]
    
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
                    break
        except: continue

    if not final_entries:
        await status_msg.edit_text("❌ لم أجد نتائج، جرب كلمات بحث أوضح.")
        return

    keyboard = []
    results_text = f"<b>🎯 نتائج من {active_source} لـ:</b>\n<code>{query}</code>"
    
    for i, entry in enumerate(final_entries):
        title = entry.get('title')[:40]
        # تشفير البيانات لضمان عدم حدوث كراش في الأزرار
        keyboard.append([InlineKeyboardButton(f"🎵 {title}", callback_data=f"dl_{entry['id']}_{active_source[:2].lower()}")])

    await status_msg.edit_text(results_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

# 3. ميزة التعرف على الموسيقى (Shazam)
async def identify_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    audio_file = msg.voice or msg.audio or msg.video
    if not audio_file: return

    status = await msg.reply_text("<b>🎧 جاري تحليل الصوت...</b>", parse_mode='HTML')
    try:
        file = await context.bot.get_file(audio_file.file_id)
        path = f"temp_{audio_file.file_id}.mp3"
        await file.download_to_drive(path)
        
        out = await shazam.recognize_song(path)
        if os.path.exists(path): os.remove(path)

        if out.get('track'):
            q = f"{out['track']['title']} {out['track']['subtitle']}"
            await status.edit_text(f"<b>✅ تم التعرف: {q}</b>")
            await perform_search(update, context, q, status)
        else:
            await status.edit_text("❌ لم أستطع التعرف على هذا المقطع.")
    except Exception as e:
        logging.error(f"Shazam Error: {e}")
        await status.edit_text("⚠️ فشل نظام التعرف، جرب البحث النصي.")

# 4. معالج البحث النصي
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg.text or msg.text.startswith('/'): return
    
    # فلترة المجموعات
    if msg.chat.type in [constants.ChatType.GROUP, constants.ChatType.SUPERGROUP]:
        if not msg.text.startswith("بحث"): return
        query = msg.text.replace("بحث", "").strip()
    else:
        query = msg.text

    if not query: return
    status = await msg.reply_text("<b>🚀 جاري تشغيل المحركات...</b>", parse_mode='HTML')
    await perform_search(update, context, query, status)

# 5. معالج التحميل المستمر (بدون حذف القائمة)
async def download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, entry_id, src = query.data.split('_')
    await query.answer(f"⏳ جاري الجلب من {src.upper()}...")
    
    prefix_map = {'sc': 'https://soundcloud.com/', 'bc': 'https://bandcamp.com/track/', 'am': 'https://audiomack.com/song/', 'yt': 'https://youtube.com/watch?v='}
    url = f"{prefix_map.get(src, '')}{entry_id}"
    
    progress = await query.message.reply_text("<b>⏳ جاري سحب الرابط المباشر...</b>", parse_mode='HTML')
    
    loop = asyncio.get_event_loop()
    try:
        with yt_dlp.YoutubeDL(YDL_COMMON_OPTS) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            await query.message.reply_audio(
                audio=info['url'],
                title=info['title'],
                duration=int(info.get('duration', 0)),
                performer=info.get('uploader', 'المقاومة'),
                caption=f"✅ المصدر: {src.upper()}",
                parse_mode='HTML'
            )
            await progress.delete()
    except:
        await progress.edit_text("❌ هذا الملف مقيد حالياً، جرب خياراً آخر من القائمة.")

# 6. تشغيل النظام
def main():
    if not TOKEN: return
    req = HTTPXRequest(http_version="2.0", connect_timeout=45, read_timeout=45)
    app = ApplicationBuilder().token(TOKEN).request(req).build()

    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("<b>بوت المقاومة الإمبراطوري جاهز!</b>", parse_mode='HTML')))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO | filters.VIDEO, identify_music))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(download_callback))
    
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
