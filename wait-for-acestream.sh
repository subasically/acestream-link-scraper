#!/bin/bash

echo "Waiting for 10 seconds before starting the health check..."
sleep 10

# Read SERVER_IP from environment variable
SERVER_IP=${SERVER_IP:-server:6878}  # Default to 'server:6878' if not set

echo "Waiting for $SERVER_IP to be ready..."

# Loop until the health check succeeds
while true; do
  # Fetch the response from the URL and parse the JSON
  response=$(curl -s http://$SERVER_IP/webui/api/service?method=get_version)
  
  # Extract the 'version' field from the JSON response
  version=$(echo "$response" | jq -r '.result.version' 2>/dev/null)
  
  # Check if the version field is not null or empty
  if [[ -n "$version" && "$version" != "null" ]]; then
    echo "Acestream is ready! Version: $version"
    break
  else
    echo "Acestream is not ready yet. Retrying in 5 seconds..."
    sleep 5
  fi
done

# Run the main application
echo "Starting main.py..."
python /usr/src/app/main.py

# Check if the application started
if [[ $? -ne 0 ]]; then
  echo "Error: main.py failed to start."
else
  echo "main.py started successfully."
fi
