def remove_fav(user, url):
    cur.execute("DELETE FROM fav WHERE user_id=? AND url=?", (user, url))
    conn.commit()
