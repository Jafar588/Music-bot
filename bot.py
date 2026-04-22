import os
import asyncio
import logging
import yt_dlp
from shazamio import Shazam

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, MessageHandler,
    CommandHandler, CallbackQueryHandler,
    filters, ContextTypes
)

# ===== إعدادات =====
TOKEN = os.getenv("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)

shazam = Shazam()
os.makedirs("downloads", exist_ok=True)

CACHE = {}

YDL_SEARCH = {
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch5'
}

YDL_DOWNLOAD = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(id)s.%(ext)s',
    'quiet': True,
    'no_warnings': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '128',
    }],
}

# ===== start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 اكتب اسم الأغنية أو أرسل مقطع صوتي")

# ===== البحث =====
 async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    msg = await update.message.reply_text("🔍 جاري البحث...")

    loop = asyncio.get_event_loop()

    try:
        ydl_opts = {
        'http_headers': {
    'User-Agent': 'Mozilla/5.0'
}
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch5',
            'extract_flat': True,   # 🔥 هذا أهم سطر
            'source_address': '0.0.0.0',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(
                None, lambda: ydl.extract_info(query, download=False)
            )

        entries = info.get("entries", [])

        if not entries:
            await msg.edit_text("❌ ماكو نتائج")
            return

        context.user_data["results"] = entries[:5]

        keyboard = []
        for i, entry in enumerate(entries[:5]):
            title = entry.get("title", "No Title")[:40]
            keyboard.append([
                InlineKeyboardButton(f"🎵 {title}", callback_data=f"dl_{i}")
            ])

        await msg.edit_text("🎯 اختر:", reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        await msg.edit_text(f"❌ خطأ:\n{str(e)[:100]}")
# ===== التحميل =====
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    index = int(query.data.split("_")[1])
    entry = context.user_data.get("results", [])[index]

    url = f"https://www.youtube.com/watch?v={entry['id']}"
    video_id = entry.get("id")

    msg = await query.message.reply_text("⏳ جاري التحميل...")

    # ===== كاش =====
    if video_id in CACHE and os.path.exists(CACHE[video_id]):
        with open(CACHE[video_id], "rb") as f:
            await query.message.reply_audio(audio=f)
        await msg.delete()
        return

    loop = asyncio.get_event_loop()

    try:
        with yt_dlp.YoutubeDL(YDL_DOWNLOAD) as ydl:
            await loop.run_in_executor(None, lambda: ydl.download([url]))

        file_path = f"downloads/{video_id}.mp3"

        CACHE[video_id] = file_path

        with open(file_path, "rb") as f:
            await query.message.reply_audio(
                audio=f,
                title=entry.get("title"),
                performer=entry.get("uploader"),
                duration=int(entry.get("duration") or 0)
            )

        await msg.delete()

    except Exception as e:
        logging.error(e)
        await msg.edit_text("❌ فشل التحميل")

# ===== Shazam =====
async def recognize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    audio = msg.voice or msg.audio

    if not audio:
        return

    status = await msg.reply_text("🎧 جاري التعرف...")

    try:
        file = await context.bot.get_file(audio.file_id)
        path = "temp.ogg"
        await file.download_to_drive(path)

        result = await shazam.recognize_song(path)

        os.remove(path)

        if result.get("track"):
            title = result["track"]["title"]
            artist = result["track"]["subtitle"]

            await status.edit_text(f"✅ {title} - {artist}")
            update.message.text = f"{title} {artist}"
            await search(update, context)
        else:
            await status.edit_text("❌ لم يتم التعرف")

    except Exception as e:
        logging.error(e)
        await status.edit_text("❌ خطأ Shazam")

# ===== تشغيل =====
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, recognize))
    app.add_handler(CallbackQueryHandler(download))

    app.run_polling()

if __name__ == "__main__":
    main()