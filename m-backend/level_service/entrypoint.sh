#!/bin/sh
set -e

echo "Waiting for postgres..."
until python -c "
import psycopg, os
psycopg.connect(
    host=os.environ['POSTGRES_HOST'],
    dbname=os.environ['POSTGRES_DB'],
    user=os.environ['POSTGRES_USER'],
    password=os.environ['POSTGRES_PASSWORD'],
)
" 2>/dev/null; do
  sleep 1
done

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 60
