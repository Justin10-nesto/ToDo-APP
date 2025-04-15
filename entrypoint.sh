#!/bin/sh

# Give the opportunity for Traefik to start up first
sleep 5

python3 manage.py makemigrations  || echo "making Migration failed"

python3 manage.py migrate || echo "Migration failed"

# Create superuser if not exists
python3 manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'adminpassword')" || echo "Superuser creation failed"

# Collect static files
python3 manage.py collectstatic --noinput || echo "Static files collection failed"

# Run the server
python3 manage.py runserver 0.0.0.0:8000 || echo "Server failed to start"
