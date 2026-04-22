import os, asyncio, yt_dlp
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# جلب التوكن من ريلوي
TOKEN = os.getenv("BOT_TOKEN")

async def search_and_download(song_name):
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
        
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
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
                # الحصول على مسار الملف الصحيح
                filename = ydl.prepare_filename(video)
                path_no_ext = os.path.splitext(filename)[0]
                return path_no_ext + ".mp3"
            return None
    except Exception as e:
        print(f"Error occurred: {e}")
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text or update.message.text.startswith('/'):
        return
    
    text = update.message.text
    status_msg = await update.message.reply_text(f"⏳ جاري جلب: {text}...")
    
    file_path = await search_and_download(text)
    
    if file_path and os.path.exists(file_path):
        with open(file_path, 'rb') as audio:
            await update.message.reply_audio(audio=audio, title=text)
        await status_msg.delete()
        os.remove(file_path)
    else:
        await status_msg.edit_text("❌ عذراً، تعذر التحميل. قد يكون السيرفر محظوراً من يوتيوب حالياً.")

def main():
    if not TOKEN:
        return
    # بناء البوت
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("البوت انطلق بنجاح...")
    application.run_polling()

if __name__ == '__main__':
    main()
