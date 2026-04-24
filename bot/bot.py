import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# إعداد السجلات (Logs)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# سحب التوكن من Railway
TOKEN = os.getenv("BOT_TOKEN")

# 1. إعدادات البحث (سريعة جداً وبدون تحميل)
YDL_SEARCH_OPTIONS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'extract_flat': True, # هذه الميزة تجلب الأسماء والروابط فقط بدون تحميل
    'no_warnings': True,
    'ignoreerrors': True,
}

# 2. إعدادات التحميل (تُستخدم فقط عند الضغط على الزر)
YDL_DOWNLOAD_OPTIONS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚡ **مرحباً بك في بوت الموسيقى المطور!**\n\n"
        "أرسل اسم الأغنية وسأعرض لك 5 نسخ لتختار منها.\n\n"
        "💡 **في المجموعات:** ابدأ طلبك بكلمة 'بحث' (مثال: بحث انتي السند).\n"
        "📱 **في الخاص:** أرسل الاسم مباشرة."
    )

# دالة البحث السريع وعرض الأزرار
async def search_and_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = update.message.text
    chat_type = update.message.chat.type

    if chat_type in ['group', 'supergroup'] and raw_text.startswith("بحث "):
        query = raw_text.replace("بحث ", "", 1).strip()
    else:
        query = raw_text.strip()

    if not query:
        return

    status_msg = await update.message.reply_text(f"🔍 جاري البحث عن 5 نسخ لـ: {query}...")

    try:
        # البحث في SoundCloud عن 5 نتائج (يمكنك تغيير scsearch5 إلى ytsearch5 للبحث في يوتيوب)
        with yt_dlp.YoutubeDL(YDL_SEARCH_OPTIONS) as ydl:
            info = ydl.extract_info(f"scsearch5:{query}", download=False)
            
        if not info or 'entries' not in info or len(info['entries']) == 0:
            await status_msg.edit_text("❌ لم يتم العثور على نتائج. جرب اسماً آخر.")
            return

        keyboard = []
        results_dict = {}
        
        # ترتيب النتائج في أزرار
        for idx, entry in enumerate(info['entries'][:5]):
            title = entry.get('title', 'Unknown Title')
            url = entry.get('url') or entry.get('webpage_url')
            
            if url:
                # حفظ الرابط والاسم في قاموس مؤقت
                results_dict[str(idx)] = {'url': url, 'title': title}
                keyboard.append([InlineKeyboardButton(f"{idx+1}. {title}", callback_data=f"dl_{idx}")])
        
        if not keyboard:
            await status_msg.edit_text("❌ حدث خطأ في استخراج الروابط.")
            return
            
        # حفظ النتائج في ذاكرة المحادثة باستخدام ID الرسالة لكي يتذكرها البوت عند الضغط
        context.chat_data[status_msg.message_id] = results_dict
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await status_msg.edit_text("🔍 تم العثور على هذه النسخ، اختر واحدة للتحميل:", reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Search Error: {e}")
        await status_msg.edit_text("⚠️ حدث خطأ فني أثناء البحث.")

# دالة الاستجابة لضغطات الأزرار والتحميل
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # لإخفاء علامة التحميل (الساعة الرملية) في الزر
    
    data = query.data
    if data.startswith("dl_"):
        idx = data.split("_")[1]
        msg_id = query.message.message_id
        
        # استدعاء معلومات الأغنية من الذاكرة بناءً على الزر الذي تم ضغطه
        song_info = context.chat_data.get(msg_id, {}).get(idx)
        
        if not song_info:
            await query.edit_message_text("❌ انتهت صلاحية هذه القائمة، يرجى البحث من جديد.")
            return
            
        url = song_info['url']
        title = song_info['title']
        
        await query.edit_message_text(f"⏳ جاري تحميل النسخة المختارة:\n{title}...")
        
        try:
            if not os.path.exists('downloads'):
                os.makedirs('downloads')
                
            file_path = None
            metadata = {}
            
            # التحميل الفعلي
            with yt_dlp.YoutubeDL(YDL_DOWNLOAD_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=True)
                if info:
                    file_path = ydl.prepare_filename(info)
                    metadata = {
                        'title': info.get('title', 'Unknown'),
                        'uploader': info.get('uploader', 'Unknown')
                    }
                
            if file_path and os.path.exists(file_path):
                # إرسال الملف الصوتي
                await query.message.reply_audio(
                    audio=open(file_path, 'rb'),
                    title=metadata['title'],
                    performer=metadata['uploader']
                )
                os.remove(file_path)
                await query.edit_message_text(f"✅ تم إرسال الأغنية:\n{title}")
            else:
                await query.edit_message_text("❌ عذراً، هذه النسخة لا تعمل أو غير قابلة للتحميل. جرب نسخة أخرى من القائمة.")
                
        except Exception as e:
            logger.error(f"Download Error: {e}")
            await query.edit_message_text("⚠️ فشل التحميل بسبب خطأ في المصدر. جرب زر آخر.")

def main():
    if not TOKEN: 
        print("Error: No BOT_TOKEN found!")
        return

    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))

    # فلتر المجموعات والخاص
    group_filter = filters.ChatType.GROUPS & filters.Regex(r'^بحث\s+')
    private_filter = filters.ChatType.PRIVATE
    
    # معالج النصوص (للبحث فقط)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & (private_filter | group_filter), 
        search_and_list
    ))
    
    # معالج الأزرار (للتحميل عند الضغط)
    application.add_handler(CallbackQueryHandler(button_callback))
    
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
