import os
import logging
import asyncio
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes
from config import YDL_DOWNLOAD_OPTIONS

logger = logging.getLogger(__name__)

def run_fast_download(url):
    if not os.path.exists('temp'):
        os.makedirs('temp')
        
    with yt_dlp.YoutubeDL(YDL_DOWNLOAD_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=True)
        if info:
            file_path = ydl.prepare_filename(info)
            return file_path, info
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

        # -------------------------------------------------------------
        # الخدعة الأولى (الذاكرة السحرية): هل الأغنية محملة مسبقاً؟
        # -------------------------------------------------------------
        if 'song_cache' not in context.bot_data:
            context.bot_data['song_cache'] = {}

        if url in context.bot_data['song_cache']:
            # إذا وجدناها، نرسلها في لمح البصر بدون أي تحميل!
            file_id = context.bot_data['song_cache'][url]
            await query.message.reply_audio(
                audio=file_id,
                caption=f"⚡ **(تم الجلب من الذاكرة السريعة)**\n🎵 {song_info['title']}"
            )
            return
        # -------------------------------------------------------------

        loading_msg = await query.message.reply_text(f"🚀 جاري التنزيل لـ:\n{song_info['title']}...")

        try:
            file_path, info = await asyncio.to_thread(run_fast_download, url)

            if file_path and os.path.exists(file_path):
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
                        pass # لتسريع العملية نتجاهل الخطأ إذا فشلت الصورة

                audio_sent = False
                for attempt in range(3): 
                    try:
                        with open(file_path, 'rb') as audio_file:
                            # حفظ الرسالة التي تم إرسالها لسرقة كود الملف منها
                            sent_message = await query.message.reply_audio(
                                audio=audio_file,
                                title=metadata['title'],
                                performer=metadata['uploader'],
                                read_timeout=120,
                                write_timeout=120,
                                connect_timeout=120
                            )
                            
                            # تخزين كود الأغنية في ذاكرة البوت للمرات القادمة
                            context.bot_data['song_cache'][url] = sent_message.audio.file_id
                            
                        audio_sent = True
                        break 
                    except Exception as e:
                        logger.warning(f"Audio send attempt {attempt + 1} failed: {e}")
                        await asyncio.sleep(1)

                try:
                    os.remove(file_path)
                except:
                    pass

                if audio_sent:
                    await loading_msg.delete() 
                else:
                    await loading_msg.edit_text("❌ لم أتمكن من إرسال المقطع الصوتي بسبب ضعف الاتصال، جرب مرة أخرى.")
            else:
                await loading_msg.edit_text("❌ عذراً، هذه النسخة تالفة. جرب زراً آخر.")

        except Exception as e:
            logger.error(f"Download Error: {e}")
            await loading_msg.edit_text("⚠️ فشل التحميل. جرب زراً آخر.")
