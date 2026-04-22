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

YDL_OPTS_SEARCH = {
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch10'
}

YDL_OPTS_DOWNLOAD = {
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

os.makedirs("downloads", exist_ok=True)

# ===== /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 اكتب اسم أي أغنية وأنا أجيبها لك!")

# ===== البحث =====
async def search_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    msg = await update.message.reply_text("🔍 جاري البحث...")

    loop = asyncio.get_event_loop()

    try:
        with yt_dlp.YoutubeDL(YDL_OPTS_SEARCH) as ydl:
            info = await loop.run_in_executor(
                None, lambda: ydl.extract_info(query, download=False)
            )

        results = info.get("entries", [])[:5]

        if not results:
            await msg.edit_text("❌ ماكو نتائج.")
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
        await msg.edit_text("❌ صار خطأ أثناء البحث.")

# ===== التحميل =====
async def download_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    index = int(query.data.split("_")[1])
    entry = context.user_data.get("results", [])[index]

    url = entry.get("webpage_url")

    msg = await query.message.reply_text("⏳ جاري التحميل...")

    loop = asyncio.get_event_loop()

    try:
        with yt_dlp.YoutubeDL(YDL_OPTS_DOWNLOAD) as ydl:
            await loop.run_in_executor(None, lambda: ydl.download([url]))

        file_name = f"downloads/{entry['id']}.mp3"

        with open(file_name, "rb") as f:
            await query.message.reply_audio(
                audio=f,
                title=entry.get("title"),
                performer=entry.get("uploader"),
                duration=int(entry.get("duration") or 0)
            )

        os.remove(file_name)
        await msg.delete()

    except Exception as e:
        logging.error(e)
        await msg.edit_text("❌ فشل التحميل، جرب غير أغنية.")

# ===== التشغيل =====
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_music))
    app.add_handler(CallbackQueryHandler(download_music))

    app.run_polling()

if __name__ == "__main__":
    main()