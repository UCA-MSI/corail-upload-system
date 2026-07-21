#!/bin/bash
set -e

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
IMAGE_NAME="ircan/corail:latest"

cd "$APP_DIR"

echo "==> Pulling latest code..."
git pull

echo "==> Building Docker image..."
docker build -t "$IMAGE_NAME" .

echo "==> Restarting containers..."
docker compose down
docker compose up -d

echo "==> Done. Checking status..."
docker compose ps
