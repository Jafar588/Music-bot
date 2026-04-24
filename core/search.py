import yt_dlp
import asyncio

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
    engines = ['scsearch50', 'amsearch50']
    
    for prefix in engines:
        try:
            with yt_dlp.YoutubeDL({**SEARCH_OPTS, 'default_search': prefix}) as ydl:
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(query, download=False))
                entries = info.get('entries', [])
                if entries:
                    return [{"t": e.get("title", "Audio"), "u": e.get("url") or e.get("webpage_url"), "d": e.get("duration")} for e in entries]
        except:
            continue
    return []
