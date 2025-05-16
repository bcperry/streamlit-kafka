#!/bin/bash
# This script can be used as an entrypoint for Docker containers
# to perform additional setup before starting the application

echo "🚀 Starting Streamlit-Kafka IoT Analytics Dashboard"

# Check if we're running in a Docker container
if [ -f /.dockerenv ]; then
  echo "🐳 Running in Docker environment"
  
  # Use Docker-specific environment settings if available
  if [ -f .env.docker ]; then
    echo "Loading Docker environment settings"
    export $(grep -v '^#' .env.docker | xargs)
  fi

  # Wait for Kafka to be ready in Docker environment
  if [[ "$KAFKA_BROKER" == kafka* ]]; then
    echo "Waiting for Kafka to be ready..."
    
    # Extract host and port from KAFKA_BROKER (format: host:port)
    KAFKA_HOST=$(echo $KAFKA_BROKER | cut -d: -f1)
    KAFKA_PORT=$(echo $KAFKA_BROKER | cut -d: -f2)
    
    echo "Attempting to connect to Kafka at ${KAFKA_HOST}:${KAFKA_PORT}"
    
    # Keep trying for 2 minutes (24 x 5 seconds)
    RETRIES=24
    WAIT_TIME=5
    
    for i in $(seq 1 $RETRIES); do
      echo "Attempt $i of $RETRIES: Connecting to Kafka at $KAFKA_HOST:$KAFKA_PORT..."
      
      # Try to connect to Kafka
      if nc -z $KAFKA_HOST $KAFKA_PORT >/dev/null 2>&1; then
        echo "✅ Successfully connected to Kafka!"
        break
      fi
      
      # If this is the last attempt, exit with an error
      if [ $i -eq $RETRIES ]; then
        echo "❌ Failed to connect to Kafka after $RETRIES attempts. Exiting."
        exit 1
      fi
      
      echo "⏳ Waiting for Kafka to be available... (retry in ${WAIT_TIME}s)"
      sleep $WAIT_TIME
    done
  fi
fi

# Default to starting Streamlit unless a command is specified
if [ $# -eq 0 ]; then
  echo "Starting Streamlit application"
  streamlit run main.py --server.address=0.0.0.0
else
  echo "Running custom command: $@"
  exec "$@"
fi
