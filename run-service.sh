#!/bin/sh
docker network create proxy || true

touch acme.json && chmod 600 acme.json

docker compose down

docker compose up --build -d

docker compose exec todo python manage.py migrate --noinput