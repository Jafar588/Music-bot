import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TOKEN")

async def auto_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if not text:
        return

    msg = await update.message.reply_text("⏳ جاري التحميل...")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'song.%(ext)s',
        'quiet': True,
        'noplaylist': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{text}", download=True)
            entry = info['entries'][0]
            filename = ydl.prepare_filename(entry)

        await update.message.reply_audio(
            audio=open(filename, 'rb'),
            title=entry.get("title"),
            performer=entry.get("uploader")
        )

        os.remove(filename)
        await msg.delete()

    except:
        await msg.edit_text("❌ فشل التحميل")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), auto_music))

print("Bot running...")
app.run_polling()
