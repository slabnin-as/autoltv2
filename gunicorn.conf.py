#!/usr/bin/env python3
"""
Gunicorn configuration for AutoLT v2
"""

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, with up to this much jitter
max_requests = 1000
max_requests_jitter = 100

# Load application code before the worker processes are forked
preload_app = True

# Process naming
proc_name = "autoltv2"

# Logging
errorlog = "-"
loglevel = "info"
accesslog = "/home/rainbow/coding/autoltv2/logs/autoltv2.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
errorlog = "/home/rainbow/coding/autoltv2/logs/error.log"
capture_outpute = True

# Process ID file
pidfile = "/tmp/autoltv2.pid"

# Daemon mode
daemon = False

# User and group to run as
user = None
group = None

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
