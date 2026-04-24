import yt_dlp
import asyncio
import logging

# أضفنا تتبع الأخطاء لنعرف ماذا يحدث في السيرفر
logging.basicConfig(level=logging.INFO)

SEARCH_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'extract_flat': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
}

async def search(query):
    loop = asyncio.get_event_loop()
    
    # قائمة المحركات: ساوند كلاود -> أوديومك -> يوتيوب (المنقذ)
    engines = ['scsearch20', 'amsearch20', 'ytsearch15']
    
    for prefix in engines:
        try:
            logging.info(f"⚡ جاري البحث في محرك: {prefix}...")
            with yt_dlp.YoutubeDL({**SEARCH_OPTS, 'default_search': prefix}) as ydl:
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(query, download=False))
                entries = info.get('entries', [])
                
                # تنظيف النتائج لتجنب المقاطع الفارغة
                valid_entries = []
                for e in entries:
                    if e.get("title") and (e.get("url") or e.get("webpage_url")):
                        valid_entries.append({
                            "t": e.get("title", "Audio"), 
                            "u": e.get("url") or e.get("webpage_url"), 
                            "d": e.get("duration")
                        })
                
                if valid_entries:
                    logging.info(f"✅ تم إيجاد نتائج في {prefix}")
                    return valid_entries
                    
        except Exception as e:
            logging.error(f"❌ فشل المحرك {prefix}: {str(e)}")
            continue # إذا فشل محرك، انتقل للذي بعده فوراً
            
    return [] # إذا فشلت كل المحركات (نادر جداً الآن)
