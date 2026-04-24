from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def is_url(text):
    return "http://" in text or "https://" in text

def pagination(results, page=1):
    per_page = 5
    total_pages = (len(results) + per_page - 1) // per_page
    start = (page - 1) * per_page
    current_results = results[start:start + per_page]

    keyboard = []
    for i, entry in enumerate(current_results):
        title = entry.get('t', 'Audio Source')[:35]
        keyboard.append([InlineKeyboardButton(f"🎵 {title}", callback_data=f"d_{start + i}")])

    nav = []
    if page > 1: nav.append(InlineKeyboardButton("⬅️", callback_data=f"p_{page-1}"))
    nav.append(InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="none"))
    if start + per_page < len(results): nav.append(InlineKeyboardButton("➡️", callback_data=f"p_{page+1}"))
    
    keyboard.append(nav)
    return InlineKeyboardMarkup(keyboard)
