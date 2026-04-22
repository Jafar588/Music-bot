import os, asyncio, yt_dlp
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

@asyncio.create_task
async def download_task(update, song_name, status_msg):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'default_search': 'ytsearch',
        'quiet': True,
        'nocheckcertificate': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{song_name}", download=True)
            if 'entries' in info:
                video = info['entries'][0]
                file_path = ydl.prepare_filename(video).rsplit('.', 1)[0] + ".mp3"
                await update.message.reply_audio(audio=open(file_path, 'rb'), title=song_name)
                await status_msg.delete()
                os.remove(file_path)
            else:
                await status_msg.edit_text("❌ لم يظهر شيء في البحث.")
    except Exception as e:
        # هنا السحر: البوت راح يگولك بالضبط شنو العطل
        await status_msg.edit_text(f"⚠️ خطأ برمجـي:\n`{str(e)[:100]}`", parse_mode='Markdown')

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text:
        status_msg = await update.message.reply_text("⏳ جاري المعالجة...")
        await download_task(update, update.message.text, status_msg)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.run_polling()

if __name__ == '__main__':
    main()
