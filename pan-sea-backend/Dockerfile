# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    ffmpeg \
    libpq-dev \
    wget \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads/audio /tmp /var/tmp /usr/tmp && \
    chmod 1777 /tmp /var/tmp /usr/tmp

# Create cache directory for models
RUN mkdir -p /root/.cache/whisper && \
    chmod -R 755 /root/.cache

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV TMPDIR=/tmp
ENV PYTHONDONTWRITEBYTECODE=1

# Command to run the application
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--workers", "2", "--threads", "2", "--access-logfile", "-", "--timeout", "30", "--graceful-timeout", "20", "--limit-request-line", "16384", "--limit-request-field_size", "16384", "app.main:app"]
