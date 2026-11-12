"""
Gunicorn production server configuration for Sitewright.
"""
import multiprocessing
import os

# Server socket (Render injects PORT environment variable)
port = os.environ.get("PORT", "8000")
bind = os.environ.get("GUNICORN_BIND", f"0.0.0.0:{port}")
backlog = 2048

# Worker processes
# Recommended: 2-4 workers per CPU core; default to 3 if single-core container
cpu_count = multiprocessing.cpu_count()
workers = int(os.environ.get("WEB_CONCURRENCY", min(cpu_count * 2 + 1, 8)))
worker_class = os.environ.get("GUNICORN_WORKER_CLASS", "gthread")
threads = int(os.environ.get("GUNICORN_THREADS", "4"))
worker_connections = 1000

# Worker lifecycle & memory management (restarts workers after N requests to prevent leaks)
max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.environ.get("GUNICORN_MAX_REQUESTS_JITTER", "50"))
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "60"))
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", "5"))
graceful_timeout = int(os.environ.get("GUNICORN_GRACEFUL_TIMEOUT", "30"))

# Process naming
proc_name = "sitewright_gunicorn"

# Logging: output to stdout / stderr for container runtimes & log aggregators
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sµs'

