import os

# التوكن من السيرفر
TOKEN = os.getenv("BOT_TOKEN")

# يوزر المجموعة (ميزة الاشتراك الإجباري في الخاص)
FORCE_SUB_CHANNEL = "@cdzo1song"

# إعدادات البحث السريع (جلب 10 أسماء)
YDL_SEARCH_OPTIONS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'extract_flat': True,
    'no_warnings': True,
    'ignoreerrors': True,
}

# إعدادات التحميل الصاروخية (باستخدام محرك aria2c)
YDL_DOWNLOAD_OPTIONS = {
    'format': 'm4a/bestaudio[ext=m4a]/bestaudio', 
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'outtmpl': 'temp/%(title)s.%(ext)s', 
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    
    # تفعيل محرك التحميل الخارجي لكسر قيود السيرفر
    'external_downloader': 'aria2c',
    'external_downloader_args': ['-x', '16', '-s', '16', '-k', '1M']
}
