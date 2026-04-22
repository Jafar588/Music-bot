import os
import asyncio
import yt_dlp
import logging
from shazamio import Shazam
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

# 1. إعدادات النخبة والمراقبة
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")
shazam = Shazam()

# إعدادات المحرك الهجين (تجاوز الحظر)
YDL_COMMON_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
}

# 2. ميزة التعرف على الموسيقى (Shazam)
async def identify_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    audio_file = update.message.voice or update.message.audio or update.message.video
    if not audio_file: return

    status = await update.message.reply_text("<b>🎧 جاري التعرف على المقطع...</b>", parse_mode='HTML')
    
    try:
        file = await context.bot.get_file(audio_file.file_id)
        file_path = f"temp_{audio_file.file_id}.mp3"
        await file.download_to_drive(file_path)
        
        out = await shazam.recognize_song(file_path)
        if os.path.exists(file_path): os.remove(file_path)

        if not out.get('track'):
            await status.edit_text("❌ لم أستطع التعرف على الصوت.")
            return

        full_query = f"{out['track']['title']} {out['track']['subtitle']}"
        await status.edit_text(f"<b>✅ تم التعرف: {full_query}</b>\n🔍 جاري البحث عن الخيارات...")
        await perform_search(update, context, full_query, status)
    except:
        await status.edit_text("⚠️ حدث خطأ في نظام التعرف.")

# 3. محرك البحث الهجين (SC/YT)
async def perform_search(update: Update, context, query, status_msg):
    loop = asyncio.get_event_loop()
    try:
        # البحث في ساوند كلاود أولاً
        with yt_dlp.YoutubeDL({**YDL_COMMON_OPTS, 'default_search': 'scsearch5'}) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(query, download=False))
            
            if not info['entries']: # البديل: يوتيوب
                with yt_dlp.YoutubeDL({**YDL_COMMON_OPTS, 'default_search': 'ytsearch5'}) as ydl_yt:
                    info = await loop.run_in_executor(None, lambda: ydl_yt.extract_info(query, download=False))

            if not info['entries']:
                await status_msg.edit_text("❌ لم أجد خيارات لهذه الأغنية.")
                return

            keyboard = []
            for entry in info['entries'][:5]:
                source = "sc" if "soundcloud" in entry.get('webpage_url', '').lower() else "yt"
                title = entry['title'][:40]
                keyboard.append([InlineKeyboardButton(f"🎵 {title}", callback_data=f"dl_{entry['id']}_{source}")])

            await status_msg.edit_text(
                f"<b>🎯 عثرت على 5 خيارات لـ:</b>\n<code>{query}</code>\n\n<i>يمكنك تجربة أكثر من خيار من القائمة أدناه:</i>",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
    except:
        await status_msg.edit_text("⚠️ السيرفر مشغول حالياً.")

# 4. معالج البحث النصي
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if msg.chat.type in [constants.ChatType.GROUP, constants.ChatType.SUPERGROUP]:
        if not msg.text.startswith("بحث"): return
        search_query = msg.text.replace("بحث", "").strip()
    else:
        search_query = msg.text

    status = await msg.reply_text("<b>🔍 جاري البحث...</b>", parse_mode='HTML')
    await perform_search(update, context, search_query, status)

# 5. دالة الجلب "المستمرة" (حل مشكلتك)
async def download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, entry_id, source = query.data.split('_')
    
    # السر هنا: إظهار رسالة علوية (Toast) دون تغيير القائمة
    await query.answer(f"🚀 جاري جلب المطلب من {source.upper()}...", show_alert=False)
    
    url = f"https://www.youtube.com/watch?v={entry_id}" if source == "yt" else f"https://api.soundcloud.com/tracks/{entry_id}"
    
    # إرسال رسالة مؤقتة لبيان التقدم لكي لا تختفي القائمة
    progress_msg = await query.message.reply_text("<b>⏳ يتم الآن استخراج الملف...</b>", parse_mode='HTML')

    loop = asyncio.get_event_loop()
    try:
        with yt_dlp.YoutubeDL(YDL_COMMON_OPTS) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            
            await query.message.reply_audio(
                audio=info['url'],
                title=info['title'],
                duration=int(info.get('duration', 0)),
                performer=info.get('uploader', 'المقاومة'),
                caption=f"✅ <b>{info['title']}</b>",
                parse_mode='HTML'
            )
            # نحذف فقط رسالة التقدم "⏳" ونبقي قائمة الخيارات كما هي
            await progress_msg.delete()
            
    except Exception:
        await progress_msg.edit_text("❌ عذراً، هذا الخيار معطل حالياً. جرب خياراً آخر من القائمة.")

def main():
    req = HTTPXRequest(http_version="2.0", connect_timeout=45)
    app = ApplicationBuilder().token(TOKEN).request(req).build()

    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("<b>أرسل اسماً أو بصمة صوتية!</b>", parse_mode='HTML')))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO | filters.VIDEO, identify_music))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(download_callback))
    
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
