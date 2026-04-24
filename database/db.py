import sqlite3

conn = sqlite3.connect("data.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS fav(
user_id INTEGER,
title TEXT,
url TEXT
)
""")

def add_fav(user, title, url):
    cur.execute("INSERT INTO fav VALUES (?,?,?)", (user, title, url))
    conn.commit()

def get_fav(user):
    return cur.execute("SELECT title,url FROM fav WHERE user_id=?", (user,)).fetchall()
