import sys
import os
sys.path.append(os.getcwd()) # سطر سحري ليجد الملفات في المجلد الرئيسي
from config import SEARCH_SC, SEARCH_AM
import yt_dlp
import asyncio
from config import SEARCH_SC, SEARCH_AM

async def search(query):
    loop = asyncio.get_event_loop()

    try:
        with yt_dlp.YoutubeDL(SEARCH_SC) as ydl:
            data = await loop.run_in_executor(None, lambda: ydl.extract_info(query, download=False))
            return data.get("entries", [])
    except:
        pass

    try:
        with yt_dlp.YoutubeDL(SEARCH_AM) as ydl:
            data = await loop.run_in_executor(None, lambda: ydl.extract_info(query, download=False))
            return data.get("entries", [])
    except:
        return []