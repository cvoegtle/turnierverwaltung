# Google Cloud Run Dockerfile for Turnierverwaltung
FROM python:3.13-slim

# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

WORKDIR /app

# Copy dependency definition and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ ./src/
COPY run.py .

# Expose port (Cloud Run sets PORT env var dynamically)
EXPOSE 8080

# Run gunicorn server with Cloud Run recommended concurrency settings
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 "src.web.app:create_app()"
