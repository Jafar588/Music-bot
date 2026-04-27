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
    """جلب الرابط المباشر للملف بدون تحميله على السيرفر (لسرعة البرق)"""
    with yt_dlp.YoutubeDL(YDL_EXTRACT_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=False)
        if info:
            return info.get('url'), info
    return None, None

def download_local_fallback(url):
    """(الخطة البديلة - Plan B): تحميل الملف على السيرفر بوزن خفيف جداً إذا رفض تلغرام الرابط المباشر"""
    if not os.path.exists('temp'):
        os.makedirs('temp')
    with yt_dlp.YoutubeDL(YDL_FALLBACK_DOWNLOAD_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=True)
        if info:
            return ydl.prepare_filename(info)
    return None

def download_thumbnail(thumb_url, filename):
    """تحميل الغلاف بصورة مؤقتة لدمجه داخل الملف الصوتي"""
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

        # التحقق من أن الزر لم تنتهِ صلاحيته
        if not song_info:
            await query.message.reply_text("❌ انتهت صلاحية هذا الزر، يرجى البحث من جديد.")
            return

        url = song_info['url']

        # الذاكرة السحرية لإرسال الملفات المكررة في 0 ثانية
        if 'song_cache' not in context.bot_data:
            context.bot_data['song_cache'] = {}

        if url in context.bot_data['song_cache']:
            await query.message.reply_audio(
                audio=context.bot_data['song_cache'][url],
                caption=f"⚡ **(تحميل فوري - من الذاكرة)**\n🎵 {song_info['title']}"
            )
            return

        loading_msg = await query.message.reply_text("🚀 جاري معالجة الأغنية وصورة الغلاف (يرجى الانتظار القليل)...")

        try:
            # استخراج بيانات الأغنية
            direct_url, info = await asyncio.to_thread(get_direct_url_and_info, url)

            if direct_url:
                title = info.get('title', 'Unknown')
                uploader = info.get('uploader', 'Unknown')
                thumb_url = info.get('thumbnail')
                
                # تحميل الصورة مؤقتاً لدمجها داخل الملف
                thumb_path = f"thumb_{msg_id}_{idx}.jpg"
                has_thumb = False
                if thumb_url:
                    has_thumb = await asyncio.to_thread(download_thumbnail, thumb_url, thumb_path)

                # محاولة إرسال الصورة كمعاينة أولاً مع الرابط (بناءً على طلبك)
                try:
                    if thumb_url:
                        # إنشاء التعليق المفصل مع الرابط (بناءً على طلبك)
                        detailed_caption = (
                            f"✅ **تم العثور على الأغنية!**\n\n"
                            f"🎵 **الأسم:** {title}\n"
                            f"👤 **الفنان:** {uploader}\n"
                            f"🌐 **المصدر:** {song_info['source']}\n"
                            f"🔗 [رابط الأغنية]({url})"
                        )
                        await query.message.reply_photo(photo=thumb_url, caption=detailed_caption, parse_mode="Markdown")
                    else:
                        await query.message.reply_text(f"✅ **تم العثور على الأغنية!**\n🎵 {title}")
                except Exception as e:
                    logger.error(f"Failed to send image preview: {e}")

                try:
                    # (الخطة البديلة الصاروخية): إرسال الرابط المباشر لتلغرام ليقوم هو بالتحميل (السرعة القصوى)
                    # قمنا بدمج الصورة داخل الدائرة أيضاً لتعمل في معظم الحالات
                    sent_message = await query.message.reply_audio(
                        audio=direct_url,
                        title=title,
                        performer=uploader,
                        # هذه هي الميزة التي أضفناها لتظهر الصورة داخل الدائرة (Thumb Injector)
                        thumbnail=open(thumb_path, 'rb') if has_thumb else None, 
                        caption=f"⚡ **تم التحميل الصاروخي!**\n🌐 المصدر: {song_info['source']}",
                        read_timeout=60, connect_timeout=60
                    )
                    # حفظ الملف في الذاكرة لتكرار الطلب في ثانية
                    context.bot_data['song_cache'][url] = sent_message.audio.file_id
                    await loading_msg.delete() 
                    
                except Exception as telegram_error:
                    # (الخطة البديلة العميقة): تلغرام رفض الرابط المباشر! لا مشكلة، نقوم نحن بتحميله محلياً على السيرفر
                    # سيظل يعمل وبنفس الصورة والميزات ولكن بوزن خفيف
                    logger.warning(f"Telegram rejected direct link, falling back to local download: {telegram_error}")
                    await loading_msg.edit_text("⏳ المنصة رفضت التمرير السريع، جاري التحميل بوزن خفيف (قد يأخذ دقيقة)...")
                    
                    local_file = await asyncio.to_thread(download_local_fallback, url)
                    if local_file and os.path.exists(local_file):
                        try:
                            with open(local_file, 'rb') as audio_file:
                                sent_message = await query.message.reply_audio(
                                    audio=audio_file,
                                    title=title,
                                    performer=uploader,
                                    thumbnail=open(thumb_path, 'rb') if has_thumb else None,
                                    caption=f"✅ **تم التحميل بوزن خفيف!**\n🌐 المصدر: {song_info['source']}",
                                    read_timeout=120, connect_timeout=120
                                )
                                context.bot_data['song_cache'][url] = sent_message.audio.file_id
                                await loading_msg.delete()
                        finally:
                            # حذف الملف المحلي من السيرفر فوراً لتنظيف المساحة
                            os.remove(local_file) 
                    else:
                        await loading_msg.edit_text("❌ حدث خطأ في التحميل بوزن خفيف. جرب نسخة أخرى.")

                finally:
                    # حذف صورة الغلاف المؤقتة بعد الإرسال
                    if has_thumb and os.path.exists(thumb_path):
                        os.remove(thumb_path)
            else:
                await loading_msg.edit_text("❌ عذراً، لم أتمكن من استخراج بيانات الأغنية. جرب نسخة أخرى.")
        except Exception as e:
            logger.error(f"Extraction Error: {e}")
            await loading_msg.edit_text("⚠️ فشل التنزيل بالكامل. جرب زراً آخر.")
