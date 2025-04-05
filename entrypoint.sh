#!/bin/sh

python3 manage.py makemigrations  || echo "making Migration failed"

python3 manage.py migrate || echo "Migration failed"

python3 manage.py runserver 0.0.0.0:8000 || echo "Server failed to start"
