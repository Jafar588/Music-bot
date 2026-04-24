import yt_dlp
import asyncio
from config import BASE_OPTS

async def extract(url):
    loop = asyncio.get_event_loop()

    def run():
        with yt_dlp.YoutubeDL(BASE_OPTS) as ydl:
            return ydl.extract_info(url, download=False)

    return await loop.run_in_executor(None, run)


async def download_mp3(url, path):
    opts = {
        **BASE_OPTS,
        "outtmpl": path,
        "postprocessors": [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }]
    }

    loop = asyncio.get_event_loop()

    def run():
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    await loop.run_in_executor(None, run)
