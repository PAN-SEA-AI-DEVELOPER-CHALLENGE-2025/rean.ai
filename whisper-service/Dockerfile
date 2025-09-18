# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (optimized for whisper-tiny)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements_fastapi.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_fastapi.txt

# Copy application code
COPY app_fastapi.py .

# Copy Google Cloud credentials
COPY white-fiber-470711-s7-efbed390336b.json /app/google-credentials.json

# Create non-root user for security
RUN useradd -m -u 1000 whisper && chown -R whisper:whisper /app && chmod 644 /app/google-credentials.json
USER whisper

# Expose port
EXPOSE 8000

# Environment variables (optimized for CPU)
ENV HOST=0.0.0.0
ENV PORT=8000
ENV WHISPER_MODEL_SIZE=tiny
ENV TORCH_NUM_THREADS=2
ENV OMP_NUM_THREADS=2

# Health check (optimized for whisper-tiny startup)
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Copy Gunicorn configuration for FastAPI
COPY gunicorn-fastapi.conf.py .

# Create logs directory with proper permissions
RUN mkdir -p /app/logs && chown -R whisper:whisper /app/logs && chmod 755 /app/logs

# Run the application with Gunicorn + Uvicorn workers for production
CMD ["gunicorn", "--config", "gunicorn-fastapi.conf.py", "app_fastapi:app"]
