import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# سحب التوكن
TOKEN = os.getenv("BOT_TOKEN")

# إعدادات البحث (لجلب 10 أسماء بسرعة)
YDL_SEARCH_OPTIONS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'extract_flat': True,
    'no_warnings': True,
    'ignoreerrors': True,
}

# إعدادات التحميل (عند الضغط على الزر)
YDL_DOWNLOAD_OPTIONS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

# دالة لحذف الرسالة (القائمة) بعد مرور وقت محدد (دقيقتين)
async def delete_message_later(message, delay):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception as e:
        pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚡ **مرحباً بك في بوت الموسيقى المطور!**\n\n"
        "💡 **في المجموعات:** ابدأ طلبك بكلمة 'بحث' (مثال: بحث انتي السند).\n"
        "📱 **في الخاص:** أرسل الاسم مباشرة."
    )

async def search_and_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = update.message.text
    chat_type = update.message.chat.type

    # فلتر المجموعات
    if chat_type in ['group', 'supergroup'] and raw_text.startswith("بحث "):
        query = raw_text.replace("بحث ", "", 1).strip()
    elif chat_type == 'private':
        query = raw_text.strip()
    else:
        return

    if not query: return

    status_msg = await update.message.reply_text(f"🔍 جاري البحث عن 10 نسخ لـ: {query}...")
    
    # محركات البحث (نبحث عن 10 نتائج)
    engines = ['scsearch10', 'amsearch10', 'dzsearch10', 'spsearch10']
    keyboard = []
    results_dict = {}
    found = False

    with yt_dlp.YoutubeDL(YDL_SEARCH_OPTIONS) as ydl:
        for engine in engines:
            try:
                info = ydl.extract_info(f"{engine}:{query}", download=False)
                if info and 'entries' in info and len(info['entries']) > 0:
                    for idx, entry in enumerate(info['entries'][:10]):
                        title = entry.get('title', 'Unknown Title')
                        url = entry.get('url') or entry.get('webpage_url')
                        if url:
                            results_dict[str(idx)] = {
                                'url': url, 
                                'title': title, 
                                'source': "SoundCloud" if "sc" in engine else "Other"
                            }
                            keyboard.append([InlineKeyboardButton(f"{idx+1}. {title[:40]}", callback_data=f"dl_{idx}")])
                    found = True
                    break 
            except Exception as e:
                logger.error(f"Search Engine {engine} failed: {e}")
                continue

    if not found or not keyboard:
        await status_msg.edit_text("❌ لم يتم العثور على نتائج. جرب اسماً آخر.")
        return

    # حفظ النتائج في الذاكرة
    context.chat_data[status_msg.message_id] = results_dict
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await status_msg.edit_text("🔍 تم العثور على 10 نسخ، اختر واحدة للتحميل:\n⏳ *(القائمة ستختفي بعد دقيقتين)*", reply_markup=reply_markup)
    
    # تشغيل مؤقت لحذف القائمة بعد 120 ثانية (دقيقتين)
    asyncio.create_task(delete_message_later(status_msg, 120))


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() 
    data = query.data

    if data.startswith("dl_"):
        idx = data.split("_")[1]
        msg_id = query.message.message_id
        song_info = context.chat_data.get(msg_id, {}).get(idx)

        if not song_info:
            await query.message.reply_text("❌ انتهت صلاحية هذا الزر، يرجى البحث من جديد.")
            return

        url = song_info['url']
        loading_msg = await query.message.reply_text(f"⏳ جاري تحميل النسخة رقم {int(idx)+1}:\n{song_info['title']}...")

        try:
            if not os.path.exists('downloads'):
                os.makedirs('downloads')

            file_path = None
            metadata = {}

            with yt_dlp.YoutubeDL(YDL_DOWNLOAD_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=True)
                if info:
                    file_path = ydl.prepare_filename(info)
                    metadata = {
                        'title': info.get('title', 'Unknown'),
                        'uploader': info.get('uploader', 'Unknown'),
                        'thumbnail': info.get('thumbnail'),
                        'url': url,
                        'source': song_info['source']
                    }

            if file_path and os.path.exists(file_path):
                # إعطاء النظام ثانية واحدة ليتأكد من كتابة الملف بالكامل قبل محاولة إرساله
                await asyncio.sleep(1)

                caption = (
                    f"✅ **تم العثور على الأغنية!**\n\n"
                    f"🎵 **الأسم:** {metadata['title']}\n"
                    f"👤 **الفنان:** {metadata['uploader']}\n"
                    f"🌐 **المصدر:** {metadata['source']}\n"
                    f"🔗 [رابط الأغنية]({metadata['url']})"
                )

                # 1. إرسال الصورة
                if metadata.get('thumbnail'):
                    try:
                        await query.message.reply_photo(photo=metadata['thumbnail'], caption=caption, parse_mode="Markdown")
                    except:
                        await query.message.reply_text(caption, parse_mode="Markdown")
                else:
                    await query.message.reply_text(caption, parse_mode="Markdown")

                # 2. إرسال الصوت (الحل الجديد: نظام المحاولات المتكررة وزيادة وقت الرفع)
                audio_sent = False
                for attempt in range(3): # سيحاول إرسالها 3 مرات بالخفاء
                    try:
                        with open(file_path, 'rb') as audio_file:
                            await query.message.reply_audio(
                                audio=audio_file,
                                title=metadata['title'],
                                performer=metadata['uploader'],
                                read_timeout=120,    # إعطاء سيرفر تلغرام دقيقتين للرفع بدلاً من الوقت الافتراضي القصير
                                write_timeout=120,
                                connect_timeout=120
                            )
                        audio_sent = True
                        break # نجح الإرسال! نخرج من حلقة المحاولات
                    except Exception as e:
                        logger.warning(f"Audio send attempt {attempt + 1} failed: {e}")
                        await asyncio.sleep(2) # انتظار ثانيتين قبل المحاولة التي تليها

                # تنظيف الملف من السيرفر
                try:
                    os.remove(file_path)
                except:
                    pass

                # معالجة النتيجة النهائية
                if audio_sent:
                    await loading_msg.delete() 
                else:
                    await loading_msg.edit_text("❌ لم أتمكن من إرسال المقطع الصوتي بسبب ضعف الاتصال بسيرفر تلغرام، القائمة لا تزال في الأعلى، جرب مرة أخرى.")
            else:
                await loading_msg.edit_text("❌ عذراً، هذه النسخة تالفة. القائمة لا تزال في الأعلى، جرب زراً آخر.")

        except Exception as e:
            logger.error(f"Download Error: {e}")
            await loading_msg.edit_text("⚠️ فشل التحميل بسبب خطأ في المصدر. القائمة لا تزال في الأعلى، جرب زراً آخر.")

def main():
    if not TOKEN: 
        print("Error: No BOT_TOKEN found!")
        return

    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    group_filter = filters.ChatType.GROUPS & filters.Regex(r'^بحث\s+')
    private_filter = filters.ChatType.PRIVATE
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & (private_filter | group_filter), search_and_list))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
