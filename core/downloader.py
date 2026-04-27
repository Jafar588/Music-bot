import os
import logging
import asyncio
import urllib.request
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes
from config import YDL_EXTRACT_OPTIONS, YDL_FALLBACK_DOWNLOAD_OPTIONS

logger = logging.getLogger(__name__)

def get_direct_url_and_info(url):
    with yt_dlp.YoutubeDL(YDL_EXTRACT_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=False)
        if info:
            return info.get('url'), info
    return None, None

def download_local_fallback(url):
    """الخطة ب: تحميل الملف فعلياً إذا رفض تلغرام الرابط"""
    if not os.path.exists('temp'):
        os.makedirs('temp')
    with yt_dlp.YoutubeDL(YDL_FALLBACK_DOWNLOAD_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=True)
        if info:
            return ydl.prepare_filename(info)
    return None

def download_thumbnail(thumb_url, filename):
    try:
        urllib.request.urlretrieve(thumb_url, filename)
        return True
    except:
        return False

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

        if 'song_cache' not in context.bot_data:
            context.bot_data['song_cache'] = {}

        # الذاكرة السريعة
        if url in context.bot_data['song_cache']:
            await query.message.reply_audio(
                audio=context.bot_data['song_cache'][url],
                caption=f"⚡ **(تحميل فوري)**\n🎵 {song_info['title']}"
            )
            return

        loading_msg = await query.message.reply_text("🚀 جاري المعالجة السريعة...")

        try:
            # 1. محاولة استخراج الرابط المباشر
            direct_url, info = await asyncio.to_thread(get_direct_url_and_info, url)

            if direct_url:
                title = info.get('title', 'Unknown')
                uploader = info.get('uploader', 'Unknown')
                thumb_url = info.get('thumbnail')
                
                thumb_path = f"thumb_{msg_id}_{idx}.jpg"
                has_thumb = False

                if thumb_url:
                    has_thumb = await asyncio.to_thread(download_thumbnail, thumb_url, thumb_path)

                try:
                    # الخطة أ: إرسال الرابط المباشر لتلغرام ليقوم هو بالتحميل (السرعة القصوى)
                    sent_message = await query.message.reply_audio(
                        audio=direct_url,
                        title=title,
                        performer=uploader,
                        thumbnail=open(thumb_path, 'rb') if has_thumb else None,
                        caption=f"✅ **تم التحميل الصاروخي!**\n🌐 المصدر: {song_info['source']}",
                        read_timeout=60, connect_timeout=60
                    )
                    context.bot_data['song_cache'][url] = sent_message.audio.file_id
                    await loading_msg.delete() 
                    
                except Exception as telegram_error:
                    # الخطة ب: تلغرام رفض الرابط! لا مشكلة، نقوم بالتحميل محلياً بأنفسنا
                    logger.warning(f"Telegram rejected direct link. Triggering Fallback Plan... {telegram_error}")
                    await loading_msg.edit_text("⏳ المنصة رفضت التمرير السريع، جاري التحميل العميق (يرجى الانتظار القليل)...")
                    
                    local_file = await asyncio.to_thread(download_local_fallback, url)
                    if local_file and os.path.exists(local_file):
                        try:
                            sent_message = await query.message.reply_audio(
                                audio=open(local_file, 'rb'),
                                title=title,
                                performer=uploader,
                                thumbnail=open(thumb_path, 'rb') if has_thumb else None,
                                caption=f"✅ **تم التحميل العميق!**\n🌐 المصدر: {song_info['source']}",
                                read_timeout=120, connect_timeout=120
                            )
                            context.bot_data['song_cache'][url] = sent_message.audio.file_id
                            await loading_msg.delete()
                        finally:
                            os.remove(local_file) # تنظيف السيرفر
                    else:
                        await loading_msg.edit_text("❌ حدث خطأ في التحميل العميق. جرب نسخة أخرى.")

                finally:
                    if has_thumb and os.path.exists(thumb_path):
                        os.remove(thumb_path)
            else:
                await loading_msg.edit_text("❌ عذراً، لم أتمكن من استخراج بيانات الأغنية.")
        except Exception as e:
            logger.error(f"Extraction Error: {e}")
            await loading_msg.edit_text("⚠️ فشل التنزيل بالكامل. جرب زراً آخر.")
