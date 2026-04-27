import os

TOKEN = os.getenv("BOT_TOKEN")
FORCE_SUB_CHANNEL = "@cdzo1song"

# 🌟 ميزة الإصدار 14: وضع التسمية الاحترافية
# True = يضمن أن اسم الملف الصوتي يكون باللغة العربية (احترافي جداً للـ VPS)
# False = يركز على السرعة القصوى فقط (قد يظهر اسم عشوائي)
PERFECT_NAME_MODE = True

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
