import time

LAST = {}

def hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '0%')
        print(f"تحميل: {percent}")