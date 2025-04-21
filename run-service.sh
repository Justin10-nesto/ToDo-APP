#!/bin/bash

# This script is used to run the ToDo application service.

docker network create public_net || true
docker network create private_net || true

docker compose down

docker compose -f docker-compose.yml up -d


