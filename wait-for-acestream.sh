#!/bin/bash

echo "Waiting for 15 seconds before starting the health check..."
sleep 60

# Loop until the health check succeeds
while true; do
  # Fetch the response from the URL and parse the JSON
  response=$(curl -s http://server:6878/webui/api/service?method=get_version)
  
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
exec "$@"
