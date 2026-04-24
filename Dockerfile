FROM python:3.10-slim
# تثبيت aria2c و ffmpeg بضغطة واحدة لتسريع عملية البناء في Railway
RUN apt-get update && apt-get install -y aria2 ffmpeg
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "-m", "bot.bot"]
