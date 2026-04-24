import time

USERS = {}

def is_spam(user_id):
    now = time.time()

    if user_id in USERS:
        if now - USERS[user_id] < 2:
            return True

    USERS[user_id] = now
    return False
