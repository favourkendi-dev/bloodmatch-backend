"""
Gunicorn configuration for production deployment.
Gunicorn is a production WSGI server that runs Django.
"""

# What address and port to listen on
bind = "0.0.0.0:8000"

# How many worker processes to run

workers = 4

# Type of worker  and sync is fine for most Django apps
worker_class = "sync"

# How many simultaneous connections each worker can handle
worker_connections = 1000

# How long to wait for a request before killing it 
timeout = 30

# How long to keep idle connections open 
keepalive = 2

# Where to log errors and access logs

errorlog = "-"
accesslog = "-"

# Capture print statements from your app
capture_output = True
enable_stdio_inheritance = True
