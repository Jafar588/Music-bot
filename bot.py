import os
import asyncio
import logging
import yt_dlp

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import (
    ApplicationBuilder, MessageHandler,
    CommandHandler, CallbackQueryHandler,
    filters, ContextTypes
)

TOKEN = os.getenv("BOT_TOKEN")
# إعداد السجلات (للمراقبة)
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

os.makedirs("downloads", exist_ok=True)

# ===== كاش ذكي (يحفظ الملفات لعدم تحميلها مرتين) =====
CACHE = {}

# ===== إعدادات البحث الهجين (ساوند كلاود + أوديومك) =====
YDL_SEARCH = {
    'quiet': True,
    'no_warnings': True,
    'default_search': 'scsearch10',
    'nocheckcertificate': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
}

# ===== إعدادات التحميل (مع شريط التحكم) =====
YDL_DOWNLOAD = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(id)s.%(ext)s',
    'quiet': True,
    'no_warnings': True,
    'retries': 10,
    'fragment_retries': 10,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    }
}

# ===== دالة البداية =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "<b>أهلاً بك في نظام المقاومة 🛡️</b>\n\n"
        "▫️ في الخاص: أرسل اسم الأغنية مباشرة.\n"
        "▫️ في المجموعات: اكتب كلمة <b>بحث</b> قبل الاسم لكي أستجيب لك.",
        parse_mode='HTML'
    )

# ===== محرك البحث الذكي (تم إضافة فلتر المجموعات هنا) =====
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    query_text = update.message.text.strip()
    chat_type = update.message.chat.type

    # --- 🛡️ حيلة المجموعات (Ghost Mode) ---
    if chat_type in [constants.ChatType.GROUP, constants.ChatType.SUPERGROUP]:
        if not query_text.startswith("بحث"):
            return # البوت يظل صامتاً تماماً إذا لم تبدأ الرسالة بكلمة بحث
        
        # تنظيف النص من كلمة بحث لأخذه ككلمة بحث صافية
        search_query = query_text.replace("بحث", "").strip()
    else:
        # في الخاص يبحث مباشرة
        search_query = query_text

    if not search_query: return

    msg = await update.message.reply_text("<b>🔍 جاري البحث في SoundCloud...</b>", parse_mode='HTML')

    loop = asyncio.get_event_loop()
    try:
        with yt_dlp.YoutubeDL(YDL_SEARCH) as ydl:
            info = await loop.run_in_executor(
                None, lambda: ydl.extract_info(search_query, download=False)
            )

        entries = info.get("entries", [])[:10]

        if not entries:
            await msg.edit_text("❌ ماكو نتائج، جرب غير اسم")
            return

        context.user_data["results"] = entries

        keyboard = []
        for i, e in enumerate(entries):
            title = e.get("title", "No Title")[:40]
            keyboard.append([
                InlineKeyboardButton(f"🎵 {title}", callback_data=f"dl_{i}")
            ])

        await msg.edit_text(
            f"<b>🎯 نتائج البحث لـ ({search_query}):</b>\nاختر النسخة المطلوبة:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

    except Exception as e:
        logging.error(f"SEARCH ERROR: {e}")
        await msg.edit_text("⚠️ السيرفر مشغول، حاول مرة ثانية")

# ===== التحميل الذكي مع شريط التحكم =====
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("جاري جلب الملف... ⏳")

    data_parts = query.data.split("_")
    index = int(data_parts[1])
    results = context.user_data.get("results", [])
    
    if not results:
        await query.message.edit_text("❌ انتهت صلاحية القائمة، ابحث من جديد")
        return

    entry = results[index]
    url = entry.get("webpage_url")
    song_id = entry.get("id")

    # رسالة مؤقتة لكي لا تختفي قائمة الخيارات
    status_msg = await query.message.reply_text("⏳ جاري التحميل ورفع الجودة...")

    # ===== تفقد الكاش (Cache System) =====
    if song_id in CACHE and os.path.exists(CACHE[song_id]):
        try:
            with open(CACHE[song_id], "rb") as f:
                await query.message.reply_audio(
                    audio=f,
                    title=entry.get("title"),
                    performer=entry.get("uploader"),
                    duration=int(entry.get("duration") or 0)
                )
            await status_msg.delete()
            return
        except: pass

    loop = asyncio.get_event_loop()
    try:
        with yt_dlp.YoutubeDL(YDL_DOWNLOAD) as ydl:
            info = await loop.run_in_executor(
                None, lambda: ydl.extract_info(url, download=True)
            )

        file_path = ydl.prepare_filename(info)
        CACHE[song_id] = file_path

        with open(file_path, "rb") as f:
            await query.message.reply_audio(
                audio=f,
                title=info.get("title"),
                performer=info.get("uploader"),
                duration=int(info.get("duration") or 0) # لظهور شريط التقديم
            )

        await status_msg.delete()

    except Exception as e:
        logging.error(f"DOWNLOAD ERROR: {e}")
        await status_msg.edit_text("❌ فشل التحميل، جرب خياراً آخر من القائمة")

# ===== التشغيل النهائي =====
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    # الفلتر الآن يتعامل مع النصوص لكن الدالة بداخلها منطق chat.type
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
    app.add_handler(CallbackQueryHandler(download))

    print("🚀 البوت يعمل الآن بنظام المجموعات الهادئة...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
