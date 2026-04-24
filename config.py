import os

TOKEN = os.getenv("BOT_TOKEN")

# يوزر المجموعة (ميزة الاشتراك الإجباري)
FORCE_SUB_CHANNEL = "@cdzo1song"

YDL_SEARCH_OPTIONS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'extract_flat': True,
    'no_warnings': True,
    'ignoreerrors': True,
}

# --- (الكود 6: إعدادات السرعة القصوى الصاروخية) ---
YDL_DOWNLOAD_OPTIONS = {
    'format': 'm4a/bestaudio[ext=m4a]/bestaudio', # إجبار البوت على صيغة m4a لمنع التحويل البطيء
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'outtmpl': 'temp/%(title)s.%(ext)s', 
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    
    # محركات التوربو لتسريع التحميل
    'concurrent_fragment_downloads': 7, # تحميل 7 أجزاء من الأغنية في نفس الوقت
    'http_chunk_size': 10485760,        # تحميل أجزاء بحجم 10 ميجا
    'noprogress': True,                 # إيقاف طباعة نسبة التحميل لتخفيف الضغط على السيرفر
}
