import os
import asyncio
import yt_dlp
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

# 1. إعدادات السجلات والمراقبة
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")

# 2. إعدادات المحرك "الفولاذي" لتجاوز الحظر
YDL_COMMON_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'referer': 'https://www.google.com/',
    'http_chunk_size': 1048576, # تحسين سرعة النقل
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "<b>مرحباً بك في نظام المقاومة الإمبراطوري 👑</b>\n\n"
        "✨ <b>مميزات النظام:</b>\n"
        "• بحث هجين (SoundCloud + YouTube)\n"
        "• شريط تحكم كامل (تقديم/ترجيع)\n"
        "• وضع المجموعات الذكي (رد فقط على 'بحث')\n"
        "• حماية من الحظر والضغط العالي\n"
    )
    await update.message.reply_text(welcome, parse_mode='HTML')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg.text or msg.text.startswith('/'): return

    # نظام الفلترة الذكي للمجموعات
    if msg.chat.type in [constants.ChatType.GROUP, constants.ChatType.SUPERGROUP]:
        if not msg.text.startswith("بحث"): return
        search_query = msg.text.replace("بحث", "").strip()
    else:
        search_query = msg.text

    if not search_query: return

    status = await msg.reply_text("<b>🔍 جاري التنقيب والمطابقة في السيرفرات...</b>", parse_mode='HTML')

    loop = asyncio.get_event_loop()
    try:
        # البحث في المصدر الأول (ساوند كلاود)
        with yt_dlp.YoutubeDL({**YDL_COMMON_OPTS, 'default_search': 'scsearch5'}) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(search_query, download=False))
            
            # إذا فشل ساوند كلاود، ننتقل تلقائياً للمصدر الثاني (يوتيوب)
            if not info['entries']:
                await status.edit_text("<b>🔄 المصدر الأول مشغول.. ننتقل للمحرك البديل...</b>", parse_mode='HTML')
                with yt_dlp.YoutubeDL({**YDL_COMMON_OPTS, 'default_search': 'ytsearch5'}) as ydl_yt:
                    info = await loop.run_in_executor(None, lambda: ydl_yt.extract_info(search_query, download=False))

            if not info['entries']:
                await status.edit_text("❌ لم أجد نتائج في جميع المصادر المتاحة.")
                return

            keyboard = []
            for entry in info['entries'][:5]:
                # تحديد المصدر بدقة لحل مشكلة السحب لاحقاً
                source = "sc" if "soundcloud" in entry.get('webpage_url', '').lower() else "yt"
                title = entry['title'][:45]
                # إرسال المعرف مع المصدر في Callback
                keyboard.append([InlineKeyboardButton(f"🎵 {title}", callback_data=f"dl_{entry['id']}_{source}")])

            await status.edit_text("<b>🎯 اختر النسخة الأفضل (تحكم كامل متاح):</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    except Exception as e:
        logging.error(f"Search Error: {e}")
        await status.edit_text("⚠️ السيرفر مشغول حالياً، يرجى المحاولة بعد قليل.")

# 3. دالة السحب "المنقحة" (حل المشكلة التي ظهرت لك)
async def download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, entry_id, source = query.data.split('_')
    
    await query.answer("جاري المعالجة الاحترافية... ⏳")
    await query.edit_message_text("<b>🚀 يتم الآن فك التشفير وجلب الرابط المباشر...</b>", parse_mode='HTML')

    # بناء الرابط المباشر للمقاطع التي كانت تفشل
    url = f"https://www.youtube.com/watch?v={entry_id}" if source == "yt" else f"https://api.soundcloud.com/tracks/{entry_id}"
    
    loop = asyncio.get_event_loop()
    try:
        # الحل هنا: استخدام خيارات سحب أكثر مرونة لضمان عدم حدوث خطأ متوقع
        with yt_dlp.YoutubeDL({**YDL_COMMON_OPTS, 'noplaylist': True}) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            
            # إرسال الملف الصوتي مع تفعيل شريط التقديم (Duration)
            await query.message.reply_audio(
                audio=info['url'],
                title=info['title'],
                performer=info.get('uploader', 'المقاومة'),
                duration=int(info.get('duration', 0)), # ضمان ظهور شريط التحكم
                caption=f"✅ <b>{info['title']}</b>\n🌐 المصدر: {source.upper()}",
                parse_mode='HTML'
            )
            await query.message.delete()
    except Exception as e:
        logging.error(f"Download Error: {e}")
        await query.edit_message_text("❌ عذراً، هذا الرابط مقيد من المصدر، جرب خياراً آخر.")

def main():
    # تفعيل السرعة القصوى عبر HTTP/2
    req = HTTPXRequest(http_version="2.0", connect_timeout=45, read_timeout=45)
    app = ApplicationBuilder().token(TOKEN).request(req).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(download_callback))

    print("🛡️ نظام المقاومة يعمل الآن بأعلى استقرار...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
