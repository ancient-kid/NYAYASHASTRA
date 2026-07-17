#!/bin/bash

echo "==================================================="
echo "🏛️ NYAYASHASTRA - Starting Docker Environment..."
echo "==================================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "[ERROR] Docker is not running. Please start Docker Desktop/Daemon and try again."
    exit 1
fi

# Build and start the containers in detached mode
echo "[INFO] Running docker compose up..."
docker compose up -d --build

if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to start Docker Compose services."
    exit 1
fi

echo "[INFO] Waiting for backend to initialize and database to seed..."
echo "[INFO] This might take a moment on first startup."

# Loop to wait for backend
health_url="http://localhost:8000/health"
attempt=1
max_attempts=30

while [ $attempt -le $max_attempts ]; do
    if curl -s -f "$health_url" >/dev/null 2>&1; then
        echo ""
        echo "[SUCCESS] Backend is healthy and ready!"
        break
    fi
    printf ". "
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    echo ""
    echo "[WARNING] Backend did not respond within time limit."
fi

echo "[INFO] Opening NYAYASHASTRA in default browser..."
# Detect OS and open browser
if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:5173
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open http://localhost:5173
    else
        echo "Please open http://localhost:5173 in your browser."
    fi
else
    echo "Please open http://localhost:5173 in your browser."
fi

echo ""
echo "[SUCCESS] NYAYASHASTRA is running!"
echo "- Frontend: http://localhost:5173"
echo "- Backend API: http://localhost:8000"
echo "- API Docs: http://localhost:8000/docs"
echo ""
read -p "Press [Enter] to stop the services and clean up..."

echo "[INFO] Stopping Docker containers..."
docker compose down
echo "[SUCCESS] NYAYASHASTRA stopped."
