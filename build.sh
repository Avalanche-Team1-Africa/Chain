#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Verify gunicorn is installed
pip install gunicorn

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate