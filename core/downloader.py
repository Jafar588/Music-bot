import logging
import asyncio
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# إعدادات استخراج الرابط فقط (بدون تحميل)
YDL_EXTRACT_OPTIONS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

# دالة الجاسوس: تجلب الرابط السري المباشر ولا تحمل الملف
def get_direct_url(url):
    with yt_dlp.YoutubeDL(YDL_EXTRACT_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=False) # السر هنا: download=False
        if info:
            # نحاول الحصول على أفضل رابط مباشر للصوت
            direct_url = info.get('url')
            return direct_url, info
    return None, None

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

        # الذاكرة السحرية (تعمل كالمعتاد)
        if 'song_cache' not in context.bot_data:
            context.bot_data['song_cache'] = {}

        if url in context.bot_data['song_cache']:
            file_id = context.bot_data['song_cache'][url]
            await query.message.reply_audio(
                audio=file_id,
                caption=f"⚡ **(تم الجلب من الذاكرة السريعة)**\n🎵 {song_info['title']}"
            )
            return

        loading_msg = await query.message.reply_text(f"🚀 جاري تمرير الطلب لسيرفرات تلغرام لـ:\n{song_info['title']}...")

        try:
            # سحب الرابط المباشر فقط (يأخذ ثانية واحدة)
            direct_url, info = await asyncio.to_thread(get_direct_url, url)

            if direct_url:
                metadata = {
                    'title': info.get('title', 'Unknown'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'thumbnail': info.get('thumbnail'),
                    'url': url,
                    'source': song_info['source']
                }

                caption = (
                    f"✅ **تم العثور على الأغنية!**\n\n"
                    f"🎵 **الأسم:** {metadata['title']}\n"
                    f"👤 **الفنان:** {metadata['uploader']}\n"
                    f"🌐 **المصدر:** {metadata['source']}\n"
                    f"🔗 [رابط الأغنية]({metadata['url']})"
                )

                if metadata.get('thumbnail'):
                    try:
                        await query.message.reply_photo(photo=metadata['thumbnail'], caption=caption, parse_mode="Markdown")
                    except:
                        pass 

                # هنا الخدعة: نعطي الرابط المباشر لتلغرام ليقوم هو بالتحميل
                try:
                    sent_message = await query.message.reply_audio(
                        audio=direct_url, # إرسال عبر الرابط وليس الملف!
                        title=metadata['title'],
                        performer=metadata['uploader'],
                        read_timeout=60,
                        connect_timeout=60
                    )
                    
                    # حفظ الملف في الذاكرة للمرات القادمة
                    context.bot_data['song_cache'][url] = sent_message.audio.file_id
                    await loading_msg.delete() 

                except Exception as e:
                    logger.error(f"Telegram failed to download via direct URL: {e}")
                    await loading_msg.edit_text("❌ سيرفرات تلغرام رفضت الرابط المباشر لهذه الأغنية بالذات. جرب نسخة أخرى من القائمة.")
            else:
                await loading_msg.edit_text("❌ عذراً، لم أتمكن من استخراج الرابط المباشر. جرب زراً آخر.")

        except Exception as e:
            logger.error(f"Extraction Error: {e}")
            await loading_msg.edit_text("⚠️ فشل استخراج الطلب. جرب زراً آخر.")
