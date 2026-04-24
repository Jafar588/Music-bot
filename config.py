import os

TOKEN = os.getenv("BOT_TOKEN")
FORCE_SUB_CHANNEL = "@cdzo1song"

YDL_SEARCH_OPTIONS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'extract_flat': True,
    'no_warnings': True,
    'ignoreerrors': True,
}

# --- (الكود 7: استخدام محرك Aria2c الصاروخي) ---
YDL_DOWNLOAD_OPTIONS = {
    'format': 'm4a/bestaudio[ext=m4a]/bestaudio', 
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'outtmpl': 'temp/%(title)s.%(ext)s', 
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    
    # تفعيل المحرك الخارجي
    'external_downloader': 'aria2c',
    # إجبار المحرك على فتح 16 اتصال لتقطيع الملف وسحبه بثواني
    'external_downloader_args': ['-x', '16', '-s', '16', '-k', '1M']
}
