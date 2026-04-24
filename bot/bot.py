import sys
import os

# ضبط مسارات المشروع ليتعرف على المجلدات
sys.path.append(os.getcwd())

# سحب التوكن مباشرة من إعدادات Railway (بدون ملف config)
TOKEN = os.getenv("BOT_TOKEN")

# استيراد مكتبات تليجرام
from telegram import *
from telegram.ext import *
from telegram.request import HTTPXRequest

# استيراد ملفات مشروعك (core و database)
from core.search import search
from core.downloader import extract, download_mp3
from core.utils import pagination, is_url
from core.anti_spam import is_spam
from database.db import add_fav

# --- هنا تبدأ دوال البوت (start و handle) ---


async def start(update: Update, context):
    await update.message.reply_text("👋 اضغط /start ثم اكتب اسم الأغنية 🎵")

async def handle(update: Update, context):
    user = update.effective_user.id

    if is_spam(user):
        return

    text = update.message.text

    if is_url(text):
        info = await extract(text)
        await send_options(update.message, info.get("title"), text)
        return

    res = await search(text)

    if not res:
        await update.message.reply_text("❌ لا نتائج")
        return

    context.user_data["r"] = res
    await update.message.reply_text("🎯 النتائج:", reply_markup=pagination(res,1))

async def send_options(msg, title, url):
    kb = [
        [InlineKeyboardButton("🎧 MP3", callback_data=f"mp3|{url}")],
        [InlineKeyboardButton("🎥 فيديو", callback_data=f"vid|{url}")],
        [InlineKeyboardButton("⭐ مفضلة", callback_data=f"fav|{title}|{url}")]
    ]
    await msg.reply_text(title, reply_markup=InlineKeyboardMarkup(kb))

async def buttons(update: Update, context):
    q = update.callback_query
    await q.answer()

    data = q.data

    if data.startswith("p_"):
        page = int(data.split("_")[1])
        await q.edit_message_reply_markup(reply_markup=pagination(context.user_data["r"], page))

    elif data.startswith("d_"):
        idx = int(data.split("_")[1])
        item = context.user_data["r"][idx]
        await send_options(q.message, item["title"], item["url"])

    elif data.startswith("mp3"):
        url = data.split("|")[1]
        msg = await q.message.reply_text("⏳ جاري التحويل...")

        await download_mp3(url)

        for f in os.listdir("temp"):
            if f.endswith(".mp3"):
                await q.message.reply_audio(audio=open(f"temp/{f}", "rb"))
                os.remove(f"temp/{f}")

        await msg.delete()

    elif data.startswith("vid"):
        url = data.split("|")[1]
        msg = await q.message.reply_text("⏳ جاري التحميل...")

        await download_video(url)

        for f in os.listdir("temp"):
            await q.message.reply_video(video=open(f"temp/{f}", "rb"))
            os.remove(f"temp/{f}")

        await msg.delete()

    elif data.startswith("fav"):
        _, title, url = data.split("|",2)
        add_fav(q.from_user.id, title, url)
        await q.answer("⭐ تمت الإضافة")

def main():
    req = HTTPXRequest(connect_timeout=60, read_timeout=60)

    app = ApplicationBuilder().token(TOKEN).request(req).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle))
    app.add_handler(CallbackQueryHandler(buttons))

    app.run_polling()

if __name__ == "__main__":
    main()