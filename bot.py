import os
import asyncio
import yt_dlp
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes

# إعداد السجلات - ضروري جداً لمراقبة السيرفر في Railway
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")

# إعدادات ساوند كلاود (نسخة محصنة)
SC_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'default_search': 'scsearch5',
    'nocheckcertificate': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("<b>بوت المقاومة جاهز 🛡️</b>\n\nابحث عن أي قصيدة بالاسم.\n(في المجموعات اكتب كلمة <b>بحث</b> قبل الاسم).", parse_mode='HTML')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    query = update.message.text
    if query.startswith('/'): return

    chat_type = update.message.chat.type
    # نظام الفلترة في المجموعات
    if chat_type in [constants.ChatType.GROUP, constants.ChatType.SUPERGROUP]:
        if not query.startswith("بحث"): return
        search_query = query.replace("بحث", "").strip()
    else:
        search_query = query

    if not search_query: return

    status_msg = await update.message.reply_text("<b>🔍 جاري التنقيب...</b>", parse_mode='HTML')

    loop = asyncio.get_event_loop()
    try:
        with yt_dlp.YoutubeDL(SC_OPTS) as ydl:
            # محاولة البحث
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(search_query, download=False))
            
            if not info or 'entries' not in info or len(info['entries']) == 0:
                await status_msg.edit_text("❌ لم أجد نتائج في ساوند كلاود.")
                return

            keyboard = []
            results_text = "<b>🎧 اختر النتيجة المطلوبة:</b>\n\n"
            
            for i, entry in enumerate(info['entries'][:5]):
                title = entry.get('title')[:40]
                duration = entry.get('duration')
                sc_url = entry.get('webpage_url')
                
                mins, secs = divmod(duration, 60) if duration else (0, 0)
                results_text += f"{i+1}. {title} [<code>{mins}:{secs:02d}</code>]\n\n"
                # نرسل رابط الصفحة كـ callback_data
                keyboard.append([InlineKeyboardButton(f"🎵 خيار {i+1}", callback_data=f"dl_{sc_url}")])

            await status_msg.edit_text(results_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
            
    except Exception as e:
        logging.error(f"Real Error: {e}")
        await status_msg.edit_text(f"⚠️ خطأ فني: {str(e)[:50]}...")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("جاري التحضير... ⏳")
    
    url = query.data.replace("dl_", "")
    await query.edit_message_text("<b>🚀 جاري جلب الملف مع شريط التحكم...</b>", parse_mode='HTML')

    loop = asyncio.get_event_loop()
    try:
        with yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'quiet': True}) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            
            # إرسال الملف الصوتي مع المدة لظهور شريط التقديم والترجيع
            await query.message.reply_audio(
                audio=info.get('url'),
                title=info.get('title'),
                performer=info.get('uploader'),
                duration=info.get('duration'), # هذا هو سر شريط التقديم
                caption=f"✅ {info.get('title')}",
                parse_mode='HTML'
            )
            await query.message.delete()
    except Exception as e:
        await query.edit_message_text(f"❌ فشل الجلب: {str(e)[:50]}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
