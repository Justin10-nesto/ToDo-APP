#!/bin/sh
# Create networks if they don't exist
docker network create public_net || true
docker network create private_net || true

# Prepare ACME file for certificates
touch acme.json && chmod 600 acme.json

# Stop existing containers
docker compose down

# Start containers with the new configuration
docker compose up --build -d