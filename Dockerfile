FROM python:3.10-slim
RUN apt-get update && apt-get install -y ffmpeg
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
# السماح بفتح منفذ Hugging Face
EXPOSE 7860
CMD ["python", "-m", "bot.bot"]
