#!/bin/bash

echo "Waiting for 15 seconds before starting the health check..."
sleep 15

set -e

host="$1"
shift
cmd="$@"

until curl -s "http://$host/webui/api/service?method=get_version" > /dev/null; do
  >&2 echo "AceStream is unavailable - sleeping"
  sleep 1
done

# Run the main application
echo "Starting main.py..."
exec python /usr/src/app/main.py
