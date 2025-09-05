#!/usr/bin/env python3
"""
Gunicorn configuration for AutoLT v2
"""
import os

# Get current directory for log files
current_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(current_dir, 'log')

# Create log directory if it doesn't exist
os.makedirs(log_dir, exist_ok=True)

# Server socket
bind = "127.0.0.1:5000"
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

# Logging to files in log directory
errorlog = os.path.join(log_dir, 'gunicorn_error.log')
loglevel = "info"
accesslog = os.path.join(log_dir, 'gunicorn_access.log')
access_log_format = '%(asctime)s [ACCESS] %(h)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process ID file
pidfile = "/tmp/autoltv2.pid"

# Daemon mode
daemon = False

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Capture output for application logs
capture_output = True