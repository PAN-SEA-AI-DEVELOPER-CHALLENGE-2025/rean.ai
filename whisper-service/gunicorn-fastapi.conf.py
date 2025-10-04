# Gunicorn configuration for FastAPI production deployment
# Optimized for 20-30 concurrent users on Deep Learning AMI

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes (optimized for whisper-tiny)
workers = 2  # Reduced for whisper-tiny efficiency
worker_class = "uvicorn.workers.UvicornWorker"  # FastAPI with uvicorn workers
worker_connections = 1000
timeout = 1800  # 30 minutes (allow for longer audio files)
keepalive = 2

# Restart workers after this many requests (prevent memory leaks)
max_requests = 1000
max_requests_jitter = 50

# Preload application for better memory usage
preload_app = True

# Logging (container-friendly: stdout/stderr)
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "whisper-fastapi-service"

# Graceful timeout for shutdowns
graceful_timeout = 240  # Give workers more time to finish processing

# Enable stats for monitoring
statsd_host = None  # Set to your StatsD host if available

# Performance tuning
worker_tmp_dir = "/dev/shm"  # Use shared memory for better performance

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def when_ready(server):
    """Called when the server is started."""
    server.log.info("FastAPI server is ready. Spawning workers")

def worker_int(worker):
    """Called when a worker receives the INT or QUIT signal."""
    worker.log.info("worker received INT or QUIT signal")

def on_exit(server):
    """Called when gunicorn is about to exit."""
    server.log.info("FastAPI server is shutting down")

# Environment-specific overrides
if os.getenv('ENVIRONMENT') == 'development':
    workers = 1
    loglevel = "debug"
    reload = True
elif os.getenv('ENVIRONMENT') == 'production':
    workers = min(4, multiprocessing.cpu_count())  # Cap at 4 for whisper-tiny
    preload_app = True
