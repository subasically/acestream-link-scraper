#!/bin/bash

# wait-for-acestream.sh

echo "Waiting for AceStream to start..."
sleep 15

set -e

host="$1"
shift
cmd="$@"

until curl -s "http://$host/webui/api/service?method=get_version" > /dev/null; do
  >&2 echo "AceStream is unavailable - sleeping"
  sleep 1
done

>&2 echo "AceStream is up - executing command"
exec $cmd
