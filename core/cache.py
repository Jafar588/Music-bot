import json
import time

CACHE = {}

def set_cache(key, value, ttl=3600):
    CACHE[key] = {
        "data": value,
        "exp": time.time() + ttl
    }

def get_cache(key):
    if key in CACHE:
        if CACHE[key]["exp"] > time.time():
            return CACHE[key]["data"]
        else:
            del CACHE[key]
    return None
