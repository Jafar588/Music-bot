import os
import asyncio
import yt_dlp
import logging
from shazamio import Shazam
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")
shazam = Shazam()

# إعدادات المحركات
YDL_COMMON_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
}

# 1. دالة البداية (Start Command) - الاحترافية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome_text = (
        f"<b>أهلاً بك يا {user_name} في نظام المقاومة المتطور 🛡️</b>\n\n"
        "أنا هنا لمساعدتك في الحصول على أدق النسخ الصوتية والقصائد.\n\n"
        "✨ <b>كيف يمكنك استخدامي؟</b>\n"
        "▫️ <b>البحث النصي:</b> أرسل اسم الأغنية أو الرادود مباشرة.\n"
        "▫️ <b>التعرف الصوتي:</b> أرسل بصمة صوتية (شازام) وسأعرفها لك.\n"
        "▫️ <b>في المجموعات:</b> يجب أن تبدأ رسالتك بكلمة <b>'بحث'</b>.\n\n"
        "<i>اكتب اسم ما تبحث عنه الآن...</i>"
    )
    
    # إضافة أزرار تحت رسالة الترحيب
    keyboard = [
        [InlineKeyboardButton("⭐ قناة التحديثات", url="https://t.me/your_channel")],
        [InlineKeyboardButton("🛠️ الدعم الفني", url="https://t.me/your_username")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='HTML')

# 2. البحث الهجين (الذي يعمل في الخلفية)
async def perform_search(update: Update, context, query, status_msg):
    loop = asyncio.get_event_loop()
    sources = [('scsearch5', 'SoundCloud'), ('amsearch5', 'Audiomack'), ('ytsearch5', 'YouTube')]
    
    final_entries = []
    active_source = ""

    for prefix, name in sources:
        try:
            with yt_dlp.YoutubeDL({**YDL_COMMON_OPTS, 'default_search': prefix}) as ydl:
                await status_msg.edit_text(f"<b>🔍 جاري التنقيب في {name}...</b>", parse_mode='HTML')
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(query, download=False))
                if info.get('entries'):
                    final_entries = info['entries'][:5]
                    active_source = name
                    break
        except: continue

    if not final_entries:
        await status_msg.edit_text("❌ لم أجد نتائج في جميع المصادر العالمية.")
        return

    keyboard = []
    results_text = f"<b>🎯 عثرت على هذه النسخ من {active_source}:</b>"
    
    for i, entry in enumerate(final_entries):
        title = entry.get('title')[:40]
        keyboard.append([InlineKeyboardButton(f"🎵 {title}", callback_data=f"dl_{entry['id']}_{active_source[:2].lower()}")])

    await status_msg.edit_text(results_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

# 3. معالج النصوص والمجموعات
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg.text or msg.text.startswith('/'): return
    
    if msg.chat.type in [constants.ChatType.GROUP, constants.ChatType.SUPERGROUP]:
        if not msg.text.startswith("بحث"): return
        query = msg.text.replace("بحث", "").strip()
    else:
        query = msg.text

    if not query: return
    status = await msg.reply_text("<b>🚀 جاري تشغيل المحركات...</b>", parse_mode='HTML')
    await perform_search(update, context, query, status)

# 4. معالج الصوت (شازام)
async def identify_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    audio_file = update.message.voice or update.message.audio or update.message.video
    status = await update.message.reply_text("<b>🎧 جاري التعرف على اللحن...</b>", parse_mode='HTML')
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
            await status.edit_text("❌ فشل التعرف على المقطع.")
    except:
        await status.edit_text("⚠️ خطأ في محرك التعرف.")

# 5. معالج التحميل
async def download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, entry_id, src = query.data.split('_')
    await query.answer(f"⏳ جاري سحب الملف من {src.upper()}...")
    
    prefix_map = {'sc': 'https://soundcloud.com/', 'am': 'https://audiomack.com/song/', 'yt': 'https://youtube.com/watch?v='}
    url = f"{prefix_map.get(src, '')}{entry_id}"
    
    progress = await query.message.reply_text("<b>⏳ جاري السحب المباشر...</b>", parse_mode='HTML')
    try:
        with yt_dlp.YoutubeDL(YDL_COMMON_OPTS) as ydl:
            info = await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            await query.message.reply_audio(
                audio=info['url'],
                title=info['title'],
                duration=int(info.get('duration', 0)),
                performer=info.get('uploader', 'المقاومة'),
                caption=f"✅ {info['title']}",
                parse_mode='HTML'
            )
            await progress.delete()
    except:
        await progress.edit_text("❌ هذا الخيار مقيد، جرب خياراً آخر.")

def main():
    req = HTTPXRequest(http_version="2.0", connect_timeout=45)
    app = ApplicationBuilder().token(TOKEN).request(req).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO | filters.VIDEO, identify_music))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(download_callback))
    
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
