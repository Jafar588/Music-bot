from core.downloader import extract, download_mp3, download_video
from database.db import add_fav, get_fav
from core.utils import pagination, is_url
import os

# 🎵 عند اختيار أغنية
async def send_options(msg, title, url):
    kb = [
        [InlineKeyboardButton("🎧 MP3", callback_data=f"mp3|{url}")],
        [InlineKeyboardButton("🎥 فيديو", callback_data=f"vid|{url}")],
        [InlineKeyboardButton("⭐ مفضلة", callback_data=f"fav|{title}|{url}")]
    ]
    await msg.reply_text(title, reply_markup=InlineKeyboardMarkup(kb))


async def buttons(update, context):
    q = update.callback_query
    await q.answer()

    data = q.data

    if data.startswith("mp3"):
        url = data.split("|")[1]
        msg = await q.message.reply_text("⏳ جاري التحويل...")

        file = await download_mp3(url)

        for f in os.listdir("temp"):
            if f.endswith(".mp3"):
                await q.message.reply_audio(audio=open(f"temp/{f}", "rb"))
                os.remove(f"temp/{f}")

        await msg.delete()

    elif data.startswith("vid"):
        url = data.split("|")[1]
        msg = await q.message.reply_text("⏳ جاري التحميل...")

        file = await download_video(url)

        for f in os.listdir("temp"):
            await q.message.reply_video(video=open(f"temp/{f}", "rb"))
            os.remove(f"temp/{f}")

        await msg.delete()

    elif data.startswith("fav"):
        _, title, url = data.split("|",2)
        add_fav(q.from_user.id, title, url)
        await q.answer("⭐ تمت الإضافة")

    elif data.startswith("d_"):
        idx = int(data.split("_")[1])
        item = context.user_data["r"][idx]
        await send_options(q.message, item["title"], item["url"])