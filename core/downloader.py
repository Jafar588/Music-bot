import yt_dlp
import asyncio
import os
from config import BASE_OPTS, TEMP_PATH
from core.progress import hook

async def extract(url):
    loop = asyncio.get_event_loop()

    def run():
        with yt_dlp.YoutubeDL(BASE_OPTS) as ydl:
            return ydl.extract_info(url, download=False)

    return await loop.run_in_executor(None, run)


async def download_mp3(url):
    filename = os.path.join(TEMP_PATH, "%(title)s.%(ext)s")

    opts = {
        **BASE_OPTS,
        "format": "bestaudio/best",
        "outtmpl": filename,
        "progress_hooks": [hook],
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

    return filename.replace("%(title)s.%(ext)s", "")


async def download_video(url):
    filename = os.path.join(TEMP_PATH, "%(title)s.%(ext)s")

    opts = {
        **BASE_OPTS,
        "outtmpl": filename
    }

    loop = asyncio.get_event_loop()

    def run():
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    await loop.run_in_executor(None, run)

    return filename