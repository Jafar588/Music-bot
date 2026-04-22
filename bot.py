import os
import asyncio
import logging
import yt_dlp

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, MessageHandler,
    CommandHandler, CallbackQueryHandler,
    filters, ContextTypes
)

# ===== إعدادات =====
TOKEN = os.getenv("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)

os.makedirs("downloads", exist_ok=True)

CACHE = {}

# ===== إعدادات YouTube =====
YDL_YT_SEARCH = {
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch5',
    'extract_flat': True,
    'source_address': '0.0.0.0',
    'http_headers': {
        'User-Agent': 'Mozilla/5.0'
    }
}

# ===== إعدادات SoundCloud =====
YDL_SC_SEARCH = {
    'quiet': True,
    'no_warnings': True,
    'default_search': 'scsearch5',
}

# ===== تحميل =====
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
    await update.message.reply_text("🎵 اكتب اسم الأغنية")

# ===== البحث =====
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    msg = await update.message.reply_text("🔍 جاري البحث...")

    loop = asyncio.get_event_loop()

    try:
        # ===== محاولة YouTube =====
        with yt_dlp.YoutubeDL(YDL_YT_SEARCH) as ydl:
            info = await loop.run_in_executor(
                None, lambda: ydl.extract_info(query, download=False)
            )

        entries = info.get("entries", [])

        if entries:
            context.user_data["results"] = entries[:5]
            context.user_data["source"] = "yt"
        else:
            raise Exception("YT empty")

    except:
        # ===== fallback إلى SoundCloud =====
        try:
            with yt_dlp.YoutubeDL(YDL_SC_SEARCH) as ydl:
                info = await loop.run_in_executor(
                    None, lambda: ydl.extract_info(query, download=False)
                )

            entries = info.get("entries", [])

            if not entries:
                await msg.edit_text("❌ ماكو نتائج")
                return

            context.user_data["results"] = entries[:5]
            context.user_data["source"] = "sc"

        except Exception as e:
            logging.error(e)
            await msg.edit_text("❌ فشل البحث بكل المصادر")
            return

    # ===== عرض النتائج =====
    keyboard = []
    for i, entry in enumerate(context.user_data["results"]):
        title = entry.get("title", "No Title")[:40]
        keyboard.append([
            InlineKeyboardButton(f"🎵 {title}", callback_data=f"dl_{i}")
        ])

    await msg.edit_text("🎯 اختر:", reply_markup=InlineKeyboardMarkup(keyboard))

# ===== التحميل =====
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    index = int(query.data.split("_")[1])
    entry = context.user_data.get("results", [])[index]
    source = context.user_data.get("source", "yt")

    # ===== تحديد الرابط =====
    if source == "yt":
        url = f"https://www.youtube.com/watch?v={entry['id']}"
    else:
        url = entry.get("url")

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

# ===== تشغيل =====
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
    app.add_handler(CallbackQueryHandler(download))

    app.run_polling()

if __name__ == "__main__":
    main()