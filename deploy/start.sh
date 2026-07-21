#!/bin/bash
# Start script for production deployment
# Run this on your server to start the BloodMatch backend

set -e

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Running database migrations..."
python manage.py migrate

echo "Starting Gunicorn server..."
exec gunicorn bloodmatch.wsgi:application -c deploy/gunicorn.conf.py
