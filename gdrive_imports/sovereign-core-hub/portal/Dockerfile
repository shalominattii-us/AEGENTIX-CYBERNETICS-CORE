FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY portal_main.py app.py
COPY ui ui
EXPOSE 8080
HEALTHCHECK --interval=5s --timeout=3s --retries=20 CMD curl -f http://localhost:8080/health || exit 1
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
