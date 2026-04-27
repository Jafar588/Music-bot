import os
import re
import logging
import asyncio
import urllib.request
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes
from config import YDL_EXTRACT_OPTIONS, YDL_FALLBACK_DOWNLOAD_OPTIONS, PERFECT_NAME_MODE

logger = logging.getLogger(__name__)

def sanitize_filename(name):
    """تنظيف اسم الملف من أي رموز قد تسبب أخطاء في النظام"""
    clean_name = re.sub(r'[\\/*?:"<>|]', "", name).strip()
    return clean_name if clean_name else "Audio_Track"

def get_direct_url_and_info(url):
    with yt_dlp.YoutubeDL(YDL_EXTRACT_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=False)
        if info:
            return info.get('url'), info
    return None, None

def download_local_fallback(url):
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

        if url in context.bot_data['song_cache']:
            await query.message.reply_audio(
                audio=context.bot_data['song_cache'][url],
                caption=f"⚡ **(تحميل فوري - من الذاكرة)**\n🎵 {song_info['title']}"
            )
            return

        loading_msg = await query.message.reply_text("🚀 جاري معالجة الأغنية وصورة الغلاف...")

        try:
            direct_url, info = await asyncio.to_thread(get_direct_url_and_info, url)

            if direct_url:
                title = info.get('title', 'Unknown')
                uploader = info.get('uploader', 'Unknown')
                thumb_url = info.get('thumbnail')
                
                # تجهيز الاسم الاحترافي النظيف
                safe_title = sanitize_filename(title)
                thumb_path = f"thumb_{msg_id}_{idx}.jpg"
                has_thumb = False
                
                if thumb_url:
                    has_thumb = await asyncio.to_thread(download_thumbnail, thumb_url, thumb_path)

                # إرسال رسالة المعاينة (الرابط والصورة التفصيلية)
                try:
                    detailed_caption = (
                        f"✅ **تم العثور على الأغنية!**\n\n"
                        f"🎵 **الأسم:** {title}\n"
                        f"👤 **الفنان:** {uploader}\n"
                        f"🌐 **المصدر:** {song_info['source']}\n"
                        f"🔗 [رابط الأغنية]({url})"
                    )
                    if thumb_url:
                        await query.message.reply_photo(photo=thumb_url, caption=detailed_caption, parse_mode="Markdown")
                    else:
                        await query.message.reply_text(detailed_caption, parse_mode="Markdown")
                except:
                    pass

                # المعالجة: الاختيار بين السرعة العشوائية أو الاسم الاحترافي
                telegram_error = None
                if not PERFECT_NAME_MODE:
                    try:
                        # الخطة الصاروخية (قد تأتي باسم عشوائي)
                        sent_message = await query.message.reply_audio(
                            audio=direct_url,
                            title=title,
                            performer=uploader,
                            thumbnail=open(thumb_path, 'rb') if has_thumb else None, 
                            caption=f"⚡ **تم التحميل الصاروخي!**\n🌐 المصدر: {song_info['source']}",
                            read_timeout=60, connect_timeout=60
                        )
                        context.bot_data['song_cache'][url] = sent_message.audio.file_id
                        await loading_msg.delete() 
                        return
                    except Exception as e:
                        telegram_error = e

                # الخطة الاحترافية لتسمية الملف (تعمل إما كـ Plan B أو إذا كان PERFECT_NAME_MODE = True)
                if PERFECT_NAME_MODE or telegram_error:
                    await loading_msg.edit_text("⏳ جاري سحب الأغنية وتسميتها بشكل احترافي (يرجى الانتظار القليل)...")
                    local_file = await asyncio.to_thread(download_local_fallback, url)
                    
                    if local_file and os.path.exists(local_file):
                        try:
                            with open(local_file, 'rb') as audio_file:
                                sent_message = await query.message.reply_audio(
                                    audio=audio_file,
                                    filename=f"{safe_title}.mp3", # 🌟 السر هنا: إجبار تلغرام على الاسم الصحيح
                                    title=title,
                                    performer=uploader,
                                    thumbnail=open(thumb_path, 'rb') if has_thumb else None,
                                    caption=f"✅ **تم التحميل بنجاح!**\n🌐 المصدر: {song_info['source']}",
                                    read_timeout=120, connect_timeout=120
                                )
                                context.bot_data['song_cache'][url] = sent_message.audio.file_id
                                await loading_msg.delete()
                        finally:
                            os.remove(local_file) 
                    else:
                        await loading_msg.edit_text("❌ حدث خطأ في التحميل العميق. جرب نسخة أخرى.")

                # تنظيف الصورة
                if has_thumb and os.path.exists(thumb_path):
                    os.remove(thumb_path)
            else:
                await loading_msg.edit_text("❌ عذراً، لم أتمكن من استخراج بيانات الأغنية.")
        except Exception as e:
            logger.error(f"Extraction Error: {e}")
            await loading_msg.edit_text("⚠️ فشل التنزيل بالكامل. جرب زراً آخر.")
