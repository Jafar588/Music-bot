import os

# سحب التوكن
TOKEN = os.getenv("BOT_TOKEN")

# إعدادات البحث (لجلب 10 أسماء بسرعة)
YDL_SEARCH_OPTIONS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'extract_flat': True,
    'no_warnings': True,
    'ignoreerrors': True,
}

# إعدادات التحميل السريعة (صيغ خفيفة)
YDL_DOWNLOAD_OPTIONS = {
    'format': 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best', 
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'outtmpl': 'temp/%(title)s.%(ext)s', # تم تغيير المسار إلى مجلد temp الخاص بك
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}
