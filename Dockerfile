# استخدام نسخة بايثون خفيفة
FROM python:3.10-slim

# هذه هي الأوامر التي كنت ستكتبها في Bash
# السيرفر سينفذها بدلاً عنك أثناء التثبيت
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# تحديد مجلد العمل
WORKDIR /app

# نسخ ملفاتك (requirements.txt و bot.py)
COPY . .

# تثبيت مكتبات البايثون
RUN pip install --no-cache-dir -r requirements.txt

# تشغيل البوت
CMD ["python", "bot.py"]
