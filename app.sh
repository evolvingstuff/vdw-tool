#!/bin/bash

# Check if Docker is running and start it if needed
echo "Checking Docker status..."
if ! docker info >/dev/null 2>&1; then
    echo "Docker is not running. Attempting to start Docker Desktop..."
    
    # Try to start Docker Desktop on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if [ -e "/Applications/Docker.app" ]; then
            echo "Starting Docker Desktop..."
            open -a Docker
            echo "Waiting for Docker to start..."
            # Wait up to 60 seconds for Docker to be ready
            for i in {1..60}; do
                if docker info >/dev/null 2>&1; then
                    echo "Docker is now running!"
                    break
                fi
                echo "Waiting... ($i/60)"
                sleep 1
            done
            
            # Final check
            if ! docker info >/dev/null 2>&1; then
                echo "❌ Docker failed to start. Please start Docker Desktop manually and try again."
                exit 1
            fi
        else
            echo "❌ Docker Desktop not found at /Applications/Docker.app"
            echo "Please install Docker Desktop or start it manually."
            exit 1
        fi
    else
        echo "❌ Docker is not running. Please start Docker and try again."
        echo "On Linux, try: sudo systemctl start docker"
        exit 1
    fi
else
    echo "✅ Docker is running"
fi

echo "Building VDW Tool Docker container..."
docker build -t vdw-tool ./_src

if [ $? -ne 0 ]; then
    echo "Build failed!"
    exit 1
fi

echo "Build successful! Running VDW Tool..."

# Kill any NON-DOCKER process using port 1313 before starting Docker
echo "Checking for processes on port 1313..."
if command -v lsof >/dev/null 2>&1; then
    # Get detailed process info to avoid killing Docker itself
    PROCESSES=$(lsof -i :1313 2>/dev/null | grep -v COMMAND)
    if [ ! -z "$PROCESSES" ]; then
        echo "Found processes on port 1313:"
        echo "$PROCESSES"
        
        # Only kill processes that are NOT docker-related
        echo "$PROCESSES" | while read line; do
            if [ ! -z "$line" ]; then
                PID=$(echo "$line" | awk '{print $2}')
                COMMAND=$(echo "$line" | awk '{print $1}')
                
                # Skip Docker-related processes
                if [[ "$COMMAND" != *"docker"* ]] && [[ "$COMMAND" != *"com.docker"* ]]; then
                    echo "Killing non-Docker process: $COMMAND (PID: $PID)"
                    kill -9 "$PID" 2>/dev/null || true
                else
                    echo "Skipping Docker-related process: $COMMAND (PID: $PID)"
                fi
            fi
        done
        sleep 1
    else
        echo "No processes found on port 1313"
    fi
else
    echo "lsof not available, attempting to start Docker anyway..."
fi

docker run -it --rm -p 1313:1313 -v "$(pwd)":/data -w /data --memory="8g" --memory-swap="8g" vdw-tool