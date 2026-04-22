import os
import asyncio
import yt_dlp
import logging
from shazamio import Shazam
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

# 1. إعدادات المراقبة
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")
shazam = Shazam()

YDL_COMMON_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
}

# 2. ميزة التعرف على الصوت (Shazam Logic)
async def identify_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # نأخذ الملف سواء كان بصمة صوتية أو ملف صوتي
    message = update.message
    audio_file = message.voice or message.audio or message.video
    
    if not audio_file: return

    status = await message.reply_text("<b>🎧 جاري الاستماع للمقطع والتعرف عليه...</b>", parse_mode='HTML')
    
    try:
        # تحميل المقطع مؤقتاً لتحليله
        file = await context.bot.get_file(audio_file.file_id)
        file_path = f"temp_{audio_file.file_id}.mp3"
        await file.download_to_drive(file_path)

        # استخدام محرك شازام
        out = await shazam.recognize_song(file_path)
        
        # حذف الملف المؤقت فوراً لحماية الخصوصية وتوفير المساحة
        if os.path.exists(file_path): os.remove(file_path)

        if not out.get('track'):
            await status.edit_text("❌ عذراً، لم أستطع التعرف على هذا المقطع.")
            return

        track_title = out['track']['title']
        track_subtitle = out['track']['subtitle']
        full_query = f"{track_title} {track_subtitle}"

        await status.edit_text(f"<b>✅ تم التعرف: {full_query}</b>\n🔍 جاري جلب النسخة الكاملة...")
        
        # تحويل النتيجة لنظام البحث الهجين الذي بنيناه سابقاً
        await perform_search(update, context, full_query, status)

    except Exception as e:
        logging.error(f"Shazam Error: {e}")
        await status.edit_text("⚠️ فشل نظام التعرف على الصوت حالياً.")

# 3. نظام البحث الهجين (الذي نستخدمه في البحث النصي والتعرف الصوتي)
async def perform_search(update: Update, context, query, status_msg):
    loop = asyncio.get_event_loop()
    try:
        # البحث في ساوند كلاود أولاً كالعادة
        with yt_dlp.YoutubeDL({**YDL_COMMON_OPTS, 'default_search': 'scsearch5'}) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(query, download=False))
            
            if not info['entries']:
                with yt_dlp.YoutubeDL({**YDL_COMMON_OPTS, 'default_search': 'ytsearch5'}) as ydl_yt:
                    info = await loop.run_in_executor(None, lambda: ydl_yt.extract_info(query, download=False))

            if not info['entries']:
                await status_msg.edit_text("❌ عرفت الأغنية لكن لم أجدها في المصادر المتاحة.")
                return

            keyboard = []
            for entry in info['entries'][:5]:
                source = "sc" if "soundcloud" in entry.get('webpage_url', '').lower() else "yt"
                keyboard.append([InlineKeyboardButton(f"🎵 {entry['title'][:40]}", callback_data=f"dl_{entry['id']}_{source}")])

            await status_msg.edit_text(f"<b>🎯 تم التعرف على المقطع بنجاح!</b>\nاختر النسخة التي تريد تحميلها:", 
                                     reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    except:
        await status_msg.edit_text("⚠️ حدث خطأ أثناء جلب الخيارات.")

# 4. معالج الرسائل النصية (البحث العادي)
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if msg.chat.type in [constants.ChatType.GROUP, constants.ChatType.SUPERGROUP]:
        if not msg.text.startswith("بحث"): return
        search_query = msg.text.replace("بحث", "").strip()
    else:
        search_query = msg.text

    status = await msg.reply_text("<b>🔍 جاري البحث...</b>", parse_mode='HTML')
    await perform_search(update, context, search_query, status)

# 5. دالة التحميل النهائية (التي طلبتها مع شريط التحكم)
async def download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, entry_id, source = query.data.split('_')
    await query.answer("جاري السحب المباشر...")
    
    url = f"https://www.youtube.com/watch?v={entry_id}" if source == "yt" else f"https://api.soundcloud.com/tracks/{entry_id}"
    
    try:
        with yt_dlp.YoutubeDL(YDL_COMMON_OPTS) as ydl:
            info = await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            await query.message.reply_audio(
                audio=info['url'],
                title=info['title'],
                duration=int(info.get('duration', 0)), # لتفعيل شريط التقديم
                performer=info.get('uploader', 'المقاومة'),
                caption=f"✅ تم الجلب من {source.upper()}",
                parse_mode='HTML'
            )
            await query.message.delete()
    except:
        await query.edit_message_text("❌ فشل الجلب، جرب خياراً آخر.")

def main():
    req = HTTPXRequest(http_version="2.0", connect_timeout=45)
    app = ApplicationBuilder().token(TOKEN).request(req).build()

    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("<b>أرسل نصاً للبحث أو بصمة صوتية للتعرف عليها!</b>", parse_mode='HTML')))
    
    # معالج الصوت والبصمات (شازام)
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO | filters.VIDEO, identify_music))
    
    # معالج النصوص (البحث الهجين)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    app.add_handler(CallbackQueryHandler(download_callback))
    
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
