import os, asyncio, yt_dlp
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import static_ffmpeg

static_ffmpeg.add_paths()
TOKEN = os.getenv("BOT_TOKEN")

async def search_and_download(song_name):
    if not os.path.exists('downloads'): os.makedirs('downloads')
        
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128', # تقليل الجودة لتسريع المعالجة
        }],
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'default_search': 'scsearch',
        'quiet': True,
        'no_warnings': True, # إيقاف التحذيرات لتوفير الجهد
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # البحث عن نتيجة واحدة فقط بسرعة
            info = ydl.extract_info(f"scsearch1:{song_name}", download=True)
            if 'entries' in info and len(info['entries']) > 0:
                video = info['entries'][0]
                filename = ydl.prepare_filename(video)
                return os.path.splitext(filename)[0] + ".mp3", None
            return None, "لم أجد نتائج."
    except Exception as e:
        return None, str(e)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text or update.message.text.startswith('/'): return
    
    status_msg = await update.message.reply_text("🔎 جاري المعالجة السريعة...")
    file_path, error = await search_and_download(update.message.text)
    
    if file_path and os.path.exists(file_path):
        await update.message.reply_audio(audio=open(file_path, 'rb'), title=update.message.text)
        await status_msg.delete()
        os.remove(file_path)
    else:
        await status_msg.edit_text(f"❌ خطأ: {error}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__': main()
