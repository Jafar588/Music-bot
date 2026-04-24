import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def is_url(text):
    return re.match(r'https?://', text)

def pagination(results, page=1):
    per = 5
    start = (page-1)*per
    end = start+per

    keys = []
    for i, r in enumerate(results[start:end]):
        keys.append([InlineKeyboardButton(r.get("title","🎵")[:35], callback_data=f"d_{start+i}")])

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"p_{page-1}"))

    nav.append(InlineKeyboardButton(f"{page}", callback_data="x"))

    if end < len(results):
        nav.append(InlineKeyboardButton("➡️", callback_data=f"p_{page+1}"))

    keys.append(nav)

    return InlineKeyboardMarkup(keys)
