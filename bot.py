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

TOKEN = os.getenv("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)

os.makedirs("downloads", exist_ok=True)

# ===== إعدادات البحث (SoundCloud فقط) =====
YDL_SEARCH = {
    'quiet': True,
    'no_warnings': True,
    'default_search': 'scsearch5',
}

# ===== إعدادات التحميل =====
YDL_DOWNLOAD = {
    'format': 'bestaudio',
    'outtmpl': 'downloads/%(id)s.%(ext)s',
    'quiet': True,
    'no_warnings': True,
    'retries': 10,
    'fragment_retries': 10,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0',
    }
}

# ===== start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎧 اكتب اسم الأغنية")

# ===== البحث =====
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    msg = await update.message.reply_text("🔍 جاري البحث في SoundCloud...")

    loop = asyncio.get_event_loop()

    try:
        with yt_dlp.YoutubeDL(YDL_SEARCH) as ydl:
            info = await loop.run_in_executor(
                None, lambda: ydl.extract_info(query, download=False)
            )

        results = info.get("entries", [])[:5]

        if not results:
            await msg.edit_text("❌ ماكو نتائج")
            return

        context.user_data["results"] = results

        keyboard = []
        for i, entry in enumerate(results):
            title = entry.get("title", "No Title")[:40]
            keyboard.append([
                InlineKeyboardButton(f"🎵 {title}", callback_data=f"dl_{i}")
            ])

        await msg.edit_text(
            "🎯 اختر الأغنية:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logging.error(e)
        await msg.edit_text("❌ فشل البحث")

# ===== التحميل =====
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    index = int(query.data.split("_")[1])
    entry = context.user_data.get("results", [])[index]

    url = entry.get("webpage_url")

    msg = await query.message.reply_text("⏳ جاري التحميل...")

    loop = asyncio.get_event_loop()

    try:
        with yt_dlp.YoutubeDL(YDL_DOWNLOAD) as ydl:
            info = await loop.run_in_executor(
                None, lambda: ydl.extract_info(url, download=True)
            )

        file_path = ydl.prepare_filename(info)

        with open(file_path, "rb") as f:
            await query.message.reply_audio(
                audio=f,
                title=info.get("title"),
                performer=info.get("uploader"),
                duration=int(info.get("duration") or 0)
            )

        os.remove(file_path)
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