# 1. استخدام بيئة بايثون خفيفة وسريعة لتوفير مساحة السيرفر
FROM python:3.10-slim

# 2. تحديث النظام وتثبيت محرك الصوت (ffmpeg) لكي تعمل الأغاني وشازام
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# 3. تحديد مجلد العمل داخل السيرفر
WORKDIR /app

# 4. نسخ كل ملفات ومجلدات مشروعك إلى السيرفر
COPY . .

# 5. تثبيت جميع المكتبات المطلوبة
RUN pip install --no-cache-dir -r requirements.txt

# 6. أمر التشغيل (السر هنا: أخبرنا السيرفر أن ملف التشغيل داخل مجلد bot)
CMD ["python", "-m", "bot.bot"]
