#!/bin/sh
set -e

python manage.py migrate --noinput

# Start the Kafka consumer in the background
python manage.py run_balance_consumer &

# Start Gunicorn
exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 30
