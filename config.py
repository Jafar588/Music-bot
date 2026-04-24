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

# إعدادات التهريب: سحب ملفات خفيفة جداً لكي لا يختنق السيرفر
YDL_DOWNLOAD_OPTIONS = {
    # إجبار البوت على جودة منخفضة (حجم صغير جداً = تحميل صاروخي)
    'format': 'bestaudio[ext=m4a][abr<=96]/bestaudio[ext=mp3][abr<=96]/worstaudio', 
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'outtmpl': 'temp/%(title)s.%(ext)s', 
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    
    'external_downloader': 'aria2c',
    'external_downloader_args': ['-x', '16', '-s', '16', '-k', '1M']
}
