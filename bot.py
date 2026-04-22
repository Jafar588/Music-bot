import os
import asyncio
import yt_dlp
import logging
from shazamio import Shazam
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

# 1. إعدادات المراقبة والتحليل
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")
shazam = Shazam()

# 2. إعدادات كسر الحظر (The Bypass Engine)
YDL_COMMON_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    # حيلة احترافية: محاكاة متصفح حقيقي متكامل
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'add_header': [
        'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language: en-US,en;q=0.9',
        'Sec-Ch-Ua-Platform: "Windows"',
    ],
    'referer': 'https://www.google.com/',
    'retries': 10, # زيادة عدد المحاولات في حال فشل السيرفر
}

# 3. محرك البحث الهجين المستقر
async def perform_search(update: Update, context, query, status_msg):
    loop = asyncio.get_event_loop()
    # المصادر مرتبة من الأكثر استقراراً للأقل
    sources = [
        ('scsearch5', 'SoundCloud'),
        ('amsearch5', 'Audiomack'),
        ('bcsearch5', 'Bandcamp'),
        ('ytsearch5', 'YouTube')
    ]
    
    final_entries = []
    active_source = ""

    for prefix, name in sources:
        try:
            with yt_dlp.YoutubeDL({**YDL_COMMON_OPTS, 'default_search': prefix}) as ydl:
                await status_msg.edit_text(f"<b>🔍 جاري الفحص في {name}...</b>", parse_mode='HTML')
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(query, download=False))
                if info.get('entries'):
                    final_entries = info['entries'][:5]
                    active_source = name
                    break
        except Exception as e:
            logging.error(f"Error in {name}: {e}")
            continue

    if not final_entries:
        await status_msg.edit_text("❌ جميع المصادر العالمية فرضت قيوداً مؤقتة. يرجى المحاولة لاحقاً.")
        return

    keyboard = []
    results_text = f"<b>🎯 نتائج من {active_source}:</b>\n<code>{query}</code>"
    
    for i, entry in enumerate(final_entries):
        title = entry.get('title')[:40]
        # تشفير دقيق للبيانات (المعرف - المصدر المختصر)
        keyboard.append([InlineKeyboardButton(f"🎵 {title}", callback_data=f"dl_{entry['id']}_{active_source[:2].lower()}")])

    await status_msg.edit_text(results_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

# 4. دالة الجلب "المتجاوزة للقيود"
async def download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, entry_id, src_code = query.data.split('_')
    
    await query.answer(f"⏳ جاري تجاوز القيود لـ {src_code.upper()}...")
    
    prefix_map = {'sc': 'https://soundcloud.com/', 'bc': 'https://bandcamp.com/track/', 'am': 'https://audiomack.com/song/', 'yt': 'https://youtube.com/watch?v='}
    url = f"{prefix_map.get(src_code, '')}{entry_id}"
    
    progress = await query.message.reply_text("<b>🚀 جاري سحب الرابط المباشر...</b>", parse_mode='HTML')
    
    loop = asyncio.get_event_loop()
    try:
        # استخدام إعدادات سحب مكثفة
        with yt_dlp.YoutubeDL({**YDL_COMMON_OPTS, 'extract_flat': False}) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            
            await query.message.reply_audio(
                audio=info['url'],
                title=info['title'],
                duration=int(info.get('duration', 0)),
                performer=info.get('uploader', 'المقاومة'),
                caption=f"✅ المصدر: {src_code.upper()}",
                parse_mode='HTML'
            )
            await progress.delete()
    except Exception as e:
        logging.error(f"Download error: {e}")
        await progress.edit_text("❌ هذا الملف محمي بتشفير عالي. جرب خياراً آخر.")

# --- بقية الدوال (handle_text, start, identify_music) تبقى كما هي ---
# (تأكد من إضافتها من الكود السابق ليعمل البوت بالكامل)

def main():
    req = HTTPXRequest(http_version="2.0", connect_timeout=50, read_timeout=50)
    app = ApplicationBuilder().token(TOKEN).request(req).build()
    
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("<b>نظام المقاومة الشامل 🌐</b>", parse_mode='HTML')))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO | filters.VIDEO, identify_music))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(download_callback))
    
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
