#!/bin/bash

# Script to deploy the ToDo application with proper network segmentation
# Usage: ./run-service.sh [start|stop|restart]

set -e

# Default action if none provided
ACTION=${1:-"start"}

# Create Docker networks if they don't exist
create_networks() {
  echo "Setting up Docker networks..."
  docker network create public_net || echo "Public network already exists"
  docker network create --internal private_net || echo "Private network already exists"
}

# Start the application
start_app() {
  echo "Starting ToDo application..."
  
  # Ensure acme.json exists with proper permissions
  touch acme.json
  chmod 600 acme.json

  # Start the containers
  docker-compose up -d
  
  echo "Application started successfully!"
  echo "- Traefik dashboard: https://traefik.todo.tradesync.software"
  echo "- ToDo App: https://todo.tradesync.software"
  echo "- PostgreSQL database is secured in a private network"
}

# Stop the application
stop_app() {
  echo "Stopping ToDo application..."
  docker-compose down
  echo "Application stopped successfully!"
}

# Restart the application
restart_app() {
  echo "Restarting ToDo application..."
  docker-compose down
  docker-compose up -d
  echo "Application restarted successfully!"
}

# Check if docker-compose.yml needs updating for network security
update_docker_compose() {
  if [ ! -f docker-compose.yml ]; then
    echo "docker-compose.yml not found. Please create it first."
    exit 1
  else
    # Just verify the file contains the necessary security configurations
    if ! grep -q "private_net" docker-compose.yml || ! grep -q "internal: true" docker-compose.yml; then
      echo "WARNING: docker-compose.yml exists but may not have secure network configuration!"
      echo "Please ensure private_net network is configured with internal: true"
    else
      echo "Docker Compose configuration has secure networking configured correctly."
    fi
  fi
}

# Update entrypoint.sh to include database connection check
update_entrypoint() {
  if ! grep -q "Wait for database" entrypoint.sh; then
    echo "Updating entrypoint.sh with database connection check..."
    
    # Make a backup of the current entrypoint.sh
    cp entrypoint.sh entrypoint.sh.bak
    
    # Add the database connection check
    sed -i '/sleep 5/a\
# Wait for database to be ready\
echo "Waiting for PostgreSQL..."\
while ! nc -z database 5432; do\
  sleep 1\
done\
echo "PostgreSQL started"' entrypoint.sh
    
    # Ensure it's executable
    chmod +x entrypoint.sh
    
    echo "Entrypoint script updated!"
  fi
}

# Update Dockerfile to include netcat for health checks
update_dockerfile() {
  if ! grep -q "netcat" Dockerfile; then
    echo "Updating Dockerfile to include netcat for health checks..."
    
    # Make a backup of the current Dockerfile
    cp Dockerfile Dockerfile.bak
    
    # Add netcat to the package list
    sed -i '/librdkafka-dev@edge/a \    netcat-openbsd \\' Dockerfile
    
    echo "Dockerfile updated!"
  fi
}

# Main execution
echo "ToDo App Service Manager"
echo "========================"

# Setup phase - make sure networks and configs are correct
create_networks
update_docker_compose
update_entrypoint
update_dockerfile

# Take action based on argument
case "$ACTION" in
  start)
    start_app
    ;;
  stop)
    stop_app
    ;;
  restart)
    restart_app
    ;;
  *)
    echo "Usage: $0 [start|stop|restart]"
    exit 1
    ;;
esac

exit 0