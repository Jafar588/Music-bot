FROM python:3.10-slim
# أزلنا aria2 لأن السيرفر يمنعه، وتركنا ffmpeg فقط
RUN apt-get update && apt-get install -y ffmpeg
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "-m", "bot.bot"]
