import time
from collections import defaultdict

user_cooldowns = defaultdict(lambda: 0)

def is_spam(user_id, cooldown_time=3):
    current_time = time.time()
    if current_time - user_cooldowns[user_id] < cooldown_time:
        return True
    user_cooldowns[user_id] = current_time
    return False
