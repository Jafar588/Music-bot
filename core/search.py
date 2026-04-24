import logging
import asyncio
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import YDL_SEARCH_OPTIONS

logger = logging.getLogger(__name__)

# دالة لحذف الرسالة (القائمة) بعد مرور وقت محدد (دقيقتين)
async def delete_message_later(message, delay):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception as e:
        pass

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
    
    # تشغيل مؤقت لحذف القائمة
    asyncio.create_task(delete_message_later(status_msg, 120))
