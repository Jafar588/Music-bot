import os
import logging
import asyncio
import re
from telegram import Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# إعداد السجلات (Logs)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# سحب التوكن من Railway
TOKEN = os.getenv("BOT_TOKEN")

# إعدادات التحميل الشاملة
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'default_search': 'auto',
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚡ **مرحباً بك في بوت الموسيقى الشامل!**\n\n"
        "أرسل اسم الأغنية وسأبحث لك في:\n"
        "🎵 SoundCloud, Audiomack, Spotify,\n"
        "Deezer, Apple Music, Tidal\n\n"
        "💡 **في المجموعات:** ابدأ طلبك بكلمة 'بحث' (مثال: بحث انتي السند).\n"
        "📱 **في الخاص:** أرسل الاسم مباشرة."
    )

async def search_and_send_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = update.message.text
    chat_type = update.message.chat.type

    # تنظيف النص إذا بدأ بكلمة "بحث" في المجموعات
    if chat_type in ['group', 'supergroup'] and raw_text.startswith("بحث "):
        query = raw_text.replace("بحث ", "", 1).strip()
    else:
        query = raw_text.strip()

    if not query:
        return

    status_msg = await update.message.reply_text(f"🔍 جاري البحث والتحميل: {query}...")

    # ترتيب المحركات
    engines = ['scsearch1', 'amsearch1', 'dzsearch1', 'spsearch1']
    
    try:
        if not os.path.exists('downloads'):
            os.makedirs('downloads')

        file_path = None
        metadata = {}

        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            for engine in engines:
                try:
                    info = ydl.extract_info(f"{engine}:{query}", download=True)
                    if info and 'entries' in info and len(info['entries']) > 0:
                        entry = info['entries'][0]
                        file_path = ydl.prepare_filename(entry)
                        
                        metadata = {
                            'title': entry.get('title', 'Unknown'),
                            'uploader': entry.get('uploader', 'Unknown'),
                            'url': entry.get('webpage_url'),
                            'thumbnail': entry.get('thumbnail'),
                            'source': "SoundCloud" if "sc" in engine else ("Audiomack" if "am" in engine else "Global Engine")
                        }
                        break
                except Exception as e:
                    logger.error(f"Engine {engine} failed: {e}")
                    continue

        if file_path and os.path.exists(file_path):
            caption = (
                f"✅ **تم العثور على الأغنية!**\n\n"
                f"🎵 **الأسم:** {metadata['title']}\n"
                f"👤 **الفنان:** {metadata['uploader']}\n"
                f"🌐 **المصدر:** {metadata['source']}\n"
                f"🔗 [رابط الأغنية]({metadata['url']})"
            )

            if metadata['thumbnail']:
                try:
                    await update.message.reply_photo(photo=metadata['thumbnail'], caption=caption, parse_mode="Markdown")
                except:
                    await update.message.reply_text(caption, parse_mode="Markdown")
            else:
                await update.message.reply_text(caption, parse_mode="Markdown")

            await update.message.reply_audio(
                audio=open(file_path, 'rb'),
                title=metadata['title'],
                performer=metadata['uploader']
            )

            os.remove(file_path)
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ لم أتمكن من العثور على الأغنية.")

    except Exception as e:
        logger.error(f"Error: {e}")
        if status_msg:
            await status_msg.edit_text("⚠️ حدث خطأ فني أثناء المعالجة.")

def main():
    if not TOKEN: 
        print("Error: No BOT_TOKEN found!")
        return

    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))

    # الفلتر الجديد:
    # يعمل في الخاص على أي نص
    # يعمل في المجموعات فقط إذا بدأت الرسالة بكلمة "بحث "
    group_filter = filters.ChatType.GROUPS & filters.Regex(r'^بحث\s+')
    private_filter = filters.ChatType.PRIVATE
    
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & (private_filter | group_filter), 
        search_and_send_all
    ))
    
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
