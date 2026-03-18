#!/usr/bin/env bash
# Render runs this script during every deploy

set -o errexit   # exit on any error

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Create superuser if it doesn't exist yet
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created.')
else:
    print('Superuser already exists.')
"
