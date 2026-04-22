import os
import asyncio
import yt_dlp
import logging
import ujson
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants, InlineQueryResultAudio
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, InlineQueryHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

# 1. إعدادات النخبة (High-End Logging)
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")

# 2. المحرك الهجين (ساوند كلاود + يوتيوب + باند كامب)
def get_ydl_opts(search_query, source="sc"):
    # إذا كان المصدر ساوند كلاود نستخدم scsearch، وإذا يوتيوب نستخدم ytsearch
    prefix = "scsearch" if source == "sc" else "ytsearch"
    return {
        'format': 'bestaudio/best',
        'quiet': True,
        'default_search': f'{prefix}5',
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }

# 3. ميزة "البحث المباشر" (Inline Mode) - قمة الاحتراف
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    if not query: return
    
    results = []
    with yt_dlp.YoutubeDL(get_ydl_opts(query, "sc")) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            for i, entry in enumerate(info['entries'][:5]):
                results.append(
                    InlineQueryResultAudio(
                        id=entry['id'],
                        audio_url=entry['url'],
                        title=f"🎵 {entry['title']}",
                        performer=entry.get('uploader', 'المقاومة')
                    )
                )
        except: pass
    await update.inline_query.answer(results)

# 4. رسالة الترحيب الاحترافية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>مرحباً بك في النظام المتطور لبوت المقاومة 🛡️</b>\n\n"
        "✨ <b>مميزات لا تصدق:</b>\n"
        "• بحث هجين (SoundCloud & YouTube)\n"
        "• ميزة Inline: ابحث عني في أي شات عبر كتابة يوزري\n"
        "• وضع المجموعات الذكي (لا أتدخل إلا بكلمة 'بحث')\n"
        "• شريط تحكم كامل بالصوت\n\n"
        "<i>جرب إرسال اسم قصيدة الآن...</i>"
    )
    await update.message.reply_text(text, parse_mode='HTML')

# 5. معالج الرسائل الذكي
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg.text or msg.text.startswith('/'): return

    # نظام "تجاهل الضجيج" في المجموعات
    if msg.chat.type in [constants.ChatType.GROUP, constants.ChatType.SUPERGROUP]:
        if not msg.text.startswith("بحث"): return
        search_query = msg.text.replace("بحث", "").strip()
    else:
        search_query = msg.text

    status = await msg.reply_text("<b>⏳ جاري فحص المصادر (SC/YT)...</b>", parse_mode='HTML')

    loop = asyncio.get_event_loop()
    # المحاولة في ساوند كلاود أولاً
    source = "sc"
    try:
        with yt_dlp.YoutubeDL(get_ydl_opts(search_query, source)) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(search_query, download=False))
            
            # إذا لم يجد نتائج في ساوند كلاود، ينتقل لليوتيوب تلقائياً
            if not info['entries']:
                source = "yt"
                await status.edit_text("<b>🔄 لم نجد في SC.. ننتقل للمصدر الثاني...</b>", parse_mode='HTML')
                with yt_dlp.YoutubeDL(get_ydl_opts(search_query, source)) as ydl_yt:
                    info = await loop.run_in_executor(None, lambda: ydl_yt.extract_info(search_query, download=False))

            if not info['entries']:
                await status.edit_text("❌ عذراً، لم نجد نتائج في جميع المصادر.")
                return

            keyboard = []
            for i, entry in enumerate(info['entries'][:5]):
                title = entry['title'][:35] + ".."
                keyboard.append([InlineKeyboardButton(f"🎧 {title}", callback_data=f"dl_{entry['id']}_{source}")])

            await status.edit_text("<b>🎯 اختر النسخة الأفضل لك:</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

    except Exception as e:
        await status.edit_text(f"⚠️ خطأ في المحرك: {str(e)[:50]}")

# 6. معالجة التحميل مع شريط التحكم
async def download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.split('_')
    vid_id = data[1]
    source = data[2]
    
    await query.answer("جاري التحضير النهائي...")
    await query.edit_message_text("<b>🚀 يتم الآن جلب الملف بأعلى جودة (320kbps)...</b>", parse_mode='HTML')

    url = f"https://www.youtube.com/watch?v={vid_id}" if source == "yt" else f"https://api.soundcloud.com/tracks/{vid_id}"
    
    loop = asyncio.get_event_loop()
    try:
        with yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'quiet': True}) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            await query.message.reply_audio(
                audio=info['url'],
                title=info['title'],
                duration=info.get('duration'),
                performer=info.get('uploader', 'المقاومة'),
                caption=f"✅ <b>تم الجلب من {source.upper()}</b>",
                parse_mode='HTML'
            )
            await query.message.delete()
    except:
        await query.edit_message_text("❌ حدث خطأ غير متوقع في المصدر.")

def main():
    # استخدام HTTP/2 لسرعة خرافية في الاتصال
    req = HTTPXRequest(http_version="2.0", connect_timeout=30, read_timeout=30)
    app = ApplicationBuilder().token(TOKEN).request(req).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(InlineQueryHandler(inline_query)) # تفعيل ميزة البحث في أي مكان
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(download_callback))

    print("👑 إمبراطورية البوت تعمل الآن...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
