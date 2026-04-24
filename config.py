import os

TOKEN = os.getenv("BOT_TOKEN")

# --- (ميزة الكود 5: الاشتراك الإجباري) ---
# ضع هنا يوزر المجموعة أو القناة (مع علامة @)
# تنبيه: يجب أن ترفع البوت كـ "مشرف" (Admin) في هذه المجموعة لكي يتمكن من معرفة المشتركين!
FORCE_SUB_CHANNEL = "@YourChannelUsername" # استبدلها بيوزر مجموعتك

YDL_SEARCH_OPTIONS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'extract_flat': True,
    'no_warnings': True,
    'ignoreerrors': True,
}

YDL_DOWNLOAD_OPTIONS = {
    'format': 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best', 
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'outtmpl': 'temp/%(title)s.%(ext)s', 
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}
