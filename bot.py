import os
import asyncio
import yt_dlp
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")

# إعدادات ساوند كلاود
YDL_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'default_search': 'scsearch5', # البحث في ساوند كلاود حصراً (5 نتائج)
    'nocheckcertificate': True,
}

# 1. رسالة الترحيب
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "<b>مرحباً بك في بوت المقاومة (نسخة ساوند كلاود) 🛡️</b>\n\n"
        "▫️ في الخاص: أرسل الاسم مباشرة.\n"
        "▫️ في المجموعات: يجب أن تبدأ رسالتك بكلمة <b>بحث</b> لكي أجيبك.",
        parse_mode='HTML'
    )

# 2. منطق البحث الذكي
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    query = update.message.text
    if query.startswith('/'): return

    chat_type = update.message.chat.type
    
    # فلترة المجموعات: لا يستجيب إلا إذا بدأت الرسالة بكلمة "بحث"
    if chat_type in [constants.ChatType.GROUP, constants.ChatType.SUPERGROUP]:
        if not query.startswith("بحث"):
            return # صمت تام في المجموعة إذا لم يطلب البحث
        search_query = query.replace("بحث", "").strip()
    else:
        search_query = query

    if not search_query: return

    status_msg = await update.message.reply_text("<b>🔍 جاري التنقيب في ساوند كلاود...</b>", parse_mode='HTML')

    loop = asyncio.get_event_loop()
    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(search_query, download=False))
            
            if 'entries' not in info or len(info['entries']) == 0:
                await status_msg.edit_text("❌ لم أجد هذه القصيدة في ساوند كلاود.")
                return

            keyboard = []
            results_text = "<b>🎧 نتائج البحث من ساوند كلاود:</b>\n\n"
            
            for i, entry in enumerate(info['entries'][:5]):
                title = entry.get('title')[:45]
                duration = entry.get('duration')
                entry_id = entry.get('id')
                
                mins, secs = divmod(duration, 60) if duration else (0, 0)
                results_text += f"{i+1}. {title} [<code>{mins}:{secs:02d}</code>]\n\n"
                
                # تخزين البيانات في الزر (المعرف الفريد)
                keyboard.append([InlineKeyboardButton(f"🎵 الخيار رقم {i+1}", callback_data=f"sc_{entry_id}")])

            await status_msg.edit_text(results_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
            
    except Exception as e:
        logging.error(f"Error: {e}")
        await status_msg.edit_text("⚠️ السيرفر مشغول، حاول مرة أخرى.")

# 3. معالجة اختيار الأغنية وإرسالها مع شريط التقديم
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("جاري جلب الملف الصوتي... ⏳")
    
    sc_id = query.data.replace("sc_", "")
    # رابط ساوند كلاود المباشر باستخدام المعرف
    track_url = f"https://api.soundcloud.com/tracks/{sc_id}" 

    await query.edit_message_text("<b>🚀 يتم الآن تجهيز الملف الصوتي...</b>", parse_mode='HTML')

    loop = asyncio.get_event_loop()
    try:
        with yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'quiet': True}) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(f"https://soundcloud.com/{sc_id}", download=False))
            
            audio_url = info.get('url')
            title = info.get('title')
            duration = info.get('duration')
            uploader = info.get('uploader', 'SoundCloud')

            if audio_url:
                # إرسال كـ Audio لضمان ظهور شريط التقديم والترجيع
                await query.message.reply_audio(
                    audio=audio_url,
                    title=title,
                    performer=uploader,
                    duration=duration, # هنا السر لظهور شريط التقديم
                    caption=f"✅ <b>{title}</b>",
                    parse_mode='HTML'
                )
                await query.message.delete()
            else:
                await query.edit_message_text("❌ فشل جلب الرابط المباشر.")
    except Exception as e:
        logging.error(f"Callback Error: {e}")
        await query.edit_message_text("⚠️ حدث خطأ أثناء التحميل.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("✅ البوت يعمل الآن بنظام ساوند كلاود الاحترافي...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
