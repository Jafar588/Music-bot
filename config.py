import os

TOKEN = os.getenv("BOT_TOKEN")

USER_AGENT = "Mozilla/5.0 Chrome/124.0.0.0"

BASE_OPTS = {
    'quiet': True,
    'nocheckcertificate': True,
    'user_agent': USER_AGENT
}

SEARCH_SC = {**BASE_OPTS, 'default_search': 'scsearch50', 'extract_flat': True}
SEARCH_AM = {**BASE_OPTS, 'default_search': 'amsearch50', 'extract_flat': True}

TEMP_PATH = "temp/"
