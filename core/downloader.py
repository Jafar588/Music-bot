import yt_dlp
import asyncio

async def extract(url):
    loop = asyncio.get_event_loop()
    try:
        with yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'quiet': True}) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            return info
    except Exception as e:
        return None
