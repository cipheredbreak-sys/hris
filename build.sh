#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit  # Exit on error

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Running database migrations..."
python manage.py migrate

echo "Creating superuser if it doesn't exist..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='admin@hris.com').exists():
    User.objects.create_superuser('admin@hris.com', 'admin@hris.com', 'AdminPassword123!')
    print('Superuser created')
else:
    print('Superuser already exists')
"

echo "Build completed successfully!"