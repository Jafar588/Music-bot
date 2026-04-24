import yt_dlp
import asyncio
import logging

logging.basicConfig(level=logging.INFO)

# إعدادات التخفي الجديدة (تركنا yt-dlp يتصرف بذكائه الخاص)
SEARCH_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'extract_flat': True,
    'source_address': '0.0.0.0', # إجبار السيرفر على الهروب من حظر IPv6
    'compat_opts': ['no-youtube-unavailable-videos'],
}

async def search(query):
    loop = asyncio.get_event_loop()
    # قللنا العدد إلى 10 لكي لا ننبه أنظمة الحماية
    engines = ['scsearch10', 'amsearch10', 'ytsearch10']
    
    for prefix in engines:
        try:
            logging.info(f"⚡ جاري اختراق محرك: {prefix}...")
            with yt_dlp.YoutubeDL({**SEARCH_OPTS, 'default_search': prefix}) as ydl:
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(query, download=False))
                
                entries = info.get('entries', [])
                valid_entries = []
                
                for e in entries:
                    url = e.get("url") or e.get("webpage_url")
                    title = e.get("title")
                    if url and title:
                        valid_entries.append({
                            "t": title, 
                            "u": url, 
                            "d": e.get("duration")
                        })
                
                if valid_entries:
                    logging.info(f"✅ تم السحب بنجاح من {prefix}")
                    return valid_entries
                    
        except Exception as e:
            # هنا سنصطاد رسالة الحظر الحقيقية!
            logging.error(f"❌ فشل {prefix} والسبب: {e}")
            continue
            
    return []
