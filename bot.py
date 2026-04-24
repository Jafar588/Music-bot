import os
import asyncio
import yt_dlp
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")

# ⚡ إعدادات yt-dlp (مع Anti-block)
BASE_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36'
}

SEARCH_SC = {**BASE_OPTS, 'default_search': 'scsearch50', 'extract_flat': True}
SEARCH_AM = {**BASE_OPTS, 'default_search': 'amsearch50', 'extract_flat': True}

# 🎯 topic ID (غيره حسب المجموعة)
ALLOWED_TOPIC_ID = None  # حط رقم التوبيك هنا

# 📄 pagination
def keyboard(results, page=1):
    per = 5
    total = len(results)
    pages = (total + per - 1)//per

    start = (page-1)*per
    end = start+per

    keys = []
    for i, r in enumerate(results[start:end]):
        keys.append([InlineKeyboardButton(f"🎵 {r['t'][:35]}", callback_data=f"d_{start+i}")])

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"p_{page-1}"))

    nav.append(InlineKeyboardButton(f"{page}/{pages}", callback_data="x"))

    if page < pages:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"p_{page+1}"))

    keys.append(nav)
    return InlineKeyboardMarkup(keys)

# 🔎 بحث متعدد المصادر
async def search_all(query):
    loop = asyncio.get_event_loop()

    # 1️⃣ SoundCloud
    try:
        with yt_dlp.YoutubeDL(SEARCH_SC) as ydl:
            data = await loop.run_in_executor(None, lambda: ydl.extract_info(query, download=False))
            res = data.get("entries", [])
            if res:
                return res
    except:
        pass

    # 2️⃣ AudioMack fallback
    try:
        with yt_dlp.YoutubeDL(SEARCH_AM) as ydl:
            data = await loop.run_in_executor(None, lambda: ydl.extract_info(query, download=False))
            return data.get("entries", [])
    except:
        return []

# 🎬 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك!\n\n"
        "اضغط /start ثم اكتب اسم الأغنية 🎵",
        parse_mode='HTML'
    )

# 📩 البحث
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    # ❗ فلترة المجموعات
    if msg.chat.type != constants.ChatType.PRIVATE:
        if not msg.text.startswith("بحث"):
            return
        
        if ALLOWED_TOPIC_ID and msg.message_thread_id != ALLOWED_TOPIC_ID:
            return

        query = msg.text.replace("بحث", "").strip()
    else:
        query = msg.text

    if not query:
        return

    status = await msg.reply_text("🔎 جاري البحث...")

    results = await search_all(query)

    if not results:
        await status.edit_text("❌ لم يتم العثور على نتائج")
        return

    data = []
    for e in results:
        data.append({
            "t": e.get("title", "Unknown"),
            "u": e.get("url") or e.get("webpage_url"),
            "d": e.get("duration")
        })

    context.user_data["r"] = data

    await status.edit_text(
        f"🎯 {len(data)} نتيجة لـ:\n{query}",
        reply_markup=keyboard(data, 1)
    )

# 🎛️ الأزرار
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    data = q.data
    res = context.user_data.get("r")

    if not res:
        await q.answer("انتهت الجلسة", show_alert=True)
        return

    # 📄 تنقل
    if data.startswith("p_"):
        page = int(data.split("_")[1])
        await q.edit_message_reply_markup(reply_markup=keyboard(res, page))
        return

    # 🎵 تحميل
    if data.startswith("d_"):
        idx = int(data.split("_")[1])
        item = res[idx]

        msg = await q.message.reply_text("⏳ جاري التحميل...")

        try:
            with yt_dlp.YoutubeDL(BASE_OPTS) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: ydl.extract_info(item["u"], download=False)
                )

                await q.message.reply_audio(
                    audio=info["url"],
                    title=item["t"],
                    duration=int(item["d"] or 0)
                )

                await msg.delete()

        except Exception as e:
            logging.error(e)
            await msg.edit_text("❌ فشل التحميل")

# 🚀 التشغيل
def main():
    req = HTTPXRequest(
        http_version="2.0",
        connect_timeout=60,
        read_timeout=60
    )

    app = ApplicationBuilder().token(TOKEN).request(req).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.add_handler(CallbackQueryHandler(buttons))

    app.run_polling()

if __name__ == "__main__":
    main()