import os
import asyncio
import logging
import sqlite3
import static_ffmpeg
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    InlineQueryHandler,
    filters,
    ContextTypes
)

# تفعيل الأداة الصوتية
static_ffmpeg.add_paths()

# إعداد السجلات (Logs)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")

# --- نظام قاعدة البيانات (Database) ---
def init_db():
    conn = sqlite3.connect('music_bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS favorites 
                 (user_id INTEGER, song_title TEXT, song_url TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- إعدادات المحرك (Engine Settings) ---
YDL_OPTS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '128'}],
    'quiet': True,
    'no_warnings': True,
    'geo_bypass': True,
}

# --- الدوال البرمجية (Functions) ---

async def get_search_results(query):
    """جلب أفضل 5 نتائج للبحث"""
    with yt_dlp.YoutubeDL({'default_search': 'scsearch5', 'quiet': True}) as ydl:
        try:
            info = await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.extract_info(f"scsearch5:{query}", download=False))
            results = []
            if 'entries' in info:
                for entry in info['entries'][:5]:
                    results.append({
                        'title': entry.get('title'),
                        'url': entry.get('url'),
                        'id': entry.get('id'),
                        'duration': entry.get('duration')
                    })
            return results
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

async def download_task(url, title):
    """تحميل الملف المطلوب"""
    custom_opts = YDL_OPTS.copy()
    file_id = "".join(x for x in title if x.isalnum())[:10]
    custom_opts['outtmpl'] = f'downloads/{file_id}.%(ext)s'
    
    with yt_dlp.YoutubeDL(custom_opts) as ydl:
        info = await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.extract_info(url, download=True))
        return ydl.prepare_filename(info).rsplit('.', 1)[0] + ".mp3"

# --- معالجة الرسائل والأزرار (Handlers) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    await update.message.reply_text(
        f"أهلاً بك يا {user} في بوتك الاحترافي! 🎶\n\n"
        "• أرسل اسم أي أغنية للبحث.\n"
        "• استخدم @ يوزر البوت للبحث في أي محادثة.\n"
        "• اضغط /fav لعرض مفضلتك."
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    if query.startswith('/'): return

    status = await update.message.reply_text("🔍 **جاري البحث عن خيارات...**", parse_mode=constants.ParseMode.MARKDOWN)
    results = await get_search_results(query)

    if not results:
        await status.edit_text("❌ لم أجد نتائج، جرب كلمات أخرى.")
        return

    keyboard = []
    for res in results:
        # زر لتحميل الأغنية وزر لإضافتها للمفضلة
        keyboard.append([InlineKeyboardButton(f"🎵 {res['title'][:35]}...", callback_data=f"dl|{res['url']}|{res['title'][:20]}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await status.edit_text("إليك أفضل النتائج، اختر ما تريد تحميله:", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('|')
    if data[0] == "dl":
        url, title = data[1], data[2]
        await query.edit_message_text(f"⏳ جاري تجهيز: {title}...")
        
        try:
            file_path = await download_task(url, title)
            await query.message.reply_chat_action(constants.ChatAction.UPLOAD_VOICE)
            with open(file_path, 'rb') as audio:
                await query.message.reply_audio(audio=audio, title=title, caption="تم التحميل بواسطة بوتك الخاص ✅")
            os.remove(file_path)
            await query.message.delete()
        except Exception as e:
            await query.edit_message_text(f"⚠️ حدث خطأ: {str(e)[:50]}")

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نظام البحث السريع من خارج البوت"""
    query = update.inline_query.query
    if not query: return
    
    results = await get_search_results(query)
    articles = []
    
    from telegram import InlineQueryResultAudio
    for i, res in enumerate(results):
        # هنا البوت يعرض النتائج في الـ Inline
        articles.append(
            InlineQueryResultAudio(
                id=str(i),
                audio_url=res['url'], # ملاحظة: الـ Inline يحتاج روابط مباشرة، هذا يحتاج سيرفر قوي
                title=res['title']
            )
        )
    await update.inline_query.answer(articles)

# --- تشغيل البوت ---

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(InlineQueryHandler(inline_query))
    
    print("🚀 البوت الأسطوري انطلق الآن...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
