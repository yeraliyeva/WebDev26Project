#!/bin/sh
set -e

python manage.py migrate --noinput

python manage.py shell -c "
import os
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin')

if not User.objects.filter(username=username).exists():
  User.objects.create_superuser(username=username, email=email, password=password)
  print('Created superuser:', username)
else:
  print('Superuser already exists:', username)
"

python manage.py collectstatic --noinput

# Start the Kafka consumer in the background
python manage.py run_leaderboard_consumer &

# Start Uvicorn (ASGI) — handles both HTTP and WebSocket
exec uvicorn config.asgi:application \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 2 \
  --log-level info
