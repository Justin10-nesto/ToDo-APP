# Use the lightweight Python 3.9 Alpine image
FROM python:3.9-alpine

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Enable edge repos to get latest librdkafka
RUN echo "@edge http://dl-cdn.alpinelinux.org/alpine/edge/main" >> /etc/apk/repositories && \
    echo "@edgecommunity http://dl-cdn.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories

# Install system dependencies and build tools
COPY requirements.txt /app/
RUN apk update && \
    apk add --no-cache \
    bash \
    python3-dev \
    gcc \
    g++ \
    libc-dev \
    libffi-dev \
    musl-dev \
    openssl-dev \
    libxml2-dev \
    supervisor \
    libxslt-dev \
    linux-headers \
    librdkafka-dev@edge \
    netcat-openbsd && \
    pip install --upgrade pip && \
    pip install -r /app/requirements.txt && \
    pip install --upgrade markdown

# Copy the rest of the application code
COPY . /app/

# Expose ports
EXPOSE 8000 5432

# Ensure the entrypoint script is executable
COPY ./entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Use bash to run the entrypoint script
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
