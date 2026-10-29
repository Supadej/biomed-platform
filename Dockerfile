FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
ENV PYTHONUNBUFFERED=1 BIOMED_HOST=0.0.0.0 BIOMED_DATABASE_PATH=/data/biomed.sqlite3 BIOMED_HTTPS=1
CMD ["python", "serve.py"]
