import os

TOKEN = os.getenv("BOT_TOKEN")
FORCE_SUB_CHANNEL = "@cdzo1song"

# 🚀 وضع السرعة القصوى (False = سرعة صاروخية بأسماء عشوائية، تناسب السيرفرات المجانية)
PERFECT_NAME_MODE = False

YDL_SEARCH_OPTIONS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'extract_flat': True,
    'no_warnings': True,
    'ignoreerrors': True,
}

YDL_EXTRACT_OPTIONS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

YDL_FALLBACK_DOWNLOAD_OPTIONS = {
    'format': 'bestaudio[ext=m4a][abr<=96]/bestaudio[ext=mp3][abr<=96]/worstaudio/best', 
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'outtmpl': 'temp/%(title)s.%(ext)s', 
}
