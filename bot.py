import os
import asyncio
import yt_dlp
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")

# إعدادات البحث (طلب 5 نتائج)
YDL_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch5', # جلب 5 نتائج من يوتيوب
    'nocheckcertificate': True,
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("<b>أهلاً بك في بوت المقاومة المتطور 🚀</b>\nأرسل اسم ما تبحث عنه وسأعطيك خيارات متعددة.", parse_mode='HTML')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    query = update.message.text
    if query.startswith('/'): return

    # نظام البحث في المجموعات
    chat_type = update.message.chat.type
    if chat_type in [constants.ChatType.GROUP, constants.ChatType.SUPERGROUP]:
        if not query.startswith("بحث "): return
        search_query = query.replace("بحث ", "").strip()
    else:
        search_query = query

    status_msg = await update.message.reply_text("<b>🔍 جاري البحث عن أفضل الخيارات...</b>", parse_mode='HTML')

    loop = asyncio.get_event_loop()
    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            # جلب نتائج البحث
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(search_query, download=False))
            
            if 'entries' not in info or len(info['entries']) == 0:
                await status_msg.edit_text("❌ لم أجد نتائج لهذه التسمية.")
                return

            keyboard = []
            results_text = "<b>📌 اختر النتيجة المطلوبة:</b>\n\n"
            
            # عرض أول 5 نتائج فقط
            for i, entry in enumerate(info['entries'][:5]):
                title = entry.get('title')
                duration = entry.get('duration')
                video_id = entry.get('id') # نستخدم المعرف الفريد للفيديو
                
                mins, secs = divmod(duration, 60) if duration else (0, 0)
                
                # إضافة النص للقائمة
                results_text += f"{i+1}. {title} (⏳ {mins}:{secs:02d})\n\n"
                
                # إنشاء زر لكل نتيجة (نخزن الـ ID في الـ callback_data)
                keyboard.append([InlineKeyboardButton(f"الخيار رقم {i+1}", callback_data=f"dl_{video_id}")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await status_msg.edit_text(results_text, reply_markup=reply_markup, parse_mode='HTML')
            
    except Exception as e:
        logging.error(f"Error: {e}")
        await status_msg.edit_text("⚠️ السيرفر مشغول حالياً، حاول مرة أخرى.")

# معالجة ضغط الأزرار
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("جاري التحضير... ⏳")
    
    # الحصول على معرف الفيديو من بيانات الزر
    video_id = query.data.replace("dl_", "")
    download_url = f"https://www.youtube.com/watch?v={video_id}"

    await query.edit_message_text("<b>🚀 جاري جلب الملف الصوتي...</b>", parse_mode='HTML')

    loop = asyncio.get_event_loop()
    # إعدادات جلب الرابط المباشر للخيار المختار
    single_opts = {'format': 'bestaudio/best', 'quiet': True, 'nocheckcertificate': True}
    
    try:
        with yt_dlp.YoutubeDL(single_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(download_url, download=False))
            url = info.get('url')
            title = info.get('title')
            
            if url:
                await query.message.reply_audio(audio=url, title=title, caption="✅ تم الجلب بنجاح")
                await query.message.delete()
            else:
                await query.edit_message_text("❌ فشل الحصول على الرابط.")
    except Exception as e:
        await query.edit_message_text("⚠️ حدث خطأ أثناء المعالجة.")

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    # إضافة معالج الأزرار
    app.add_handler(CallbackQueryHandler(button_callback))
    
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
