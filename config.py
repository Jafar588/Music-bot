import os

# 1. توكن البوت (يجلب تلقائياً من Variables في Railway)
TOKEN = os.getenv("BOT_TOKEN")

# 2. إعدادات محرك البحث - ساوند كلاود (SEARCH_SC)
SEARCH_SC = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'scsearch50', # جلب 50 نتيجة
    'nocheckcertificate': True,
    'extract_flat': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
}

# 3. إعدادات محرك البحث - أوديومك (SEARCH_AM)
SEARCH_AM = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'amsearch50',
    'nocheckcertificate': True,
    'extract_flat': True,
}

# 4. إعدادات التحميل العميق (للسحب النهائي للملف)
DOWNLOAD_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
}

# 5. مسارات المجلدات (مهمة لطلاب نظم المعلومات)
BASE_DIR = os.getcwd()
TEMP_DIR = os.path.join(BASE_DIR, "temp")

# التأكد من وجود مجلد temp عند تشغيل الكود
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)
