#!/bin/bash

# wait-for-acestream.sh
echo "$(date '+%Y-%m-%d %H:%M:%S') - Waiting for AceStream to start..."
sleep 5

set -e

host="$1"
shift
cmd="$@"

until curl -s "http://$host/webui/api/service?method=get_version" > /dev/null; do
  >&2 echo "$(date '+%Y-%m-%d %H:%M:%S') - AceStream is unavailable - http://$host/webui/api/service?method=get_version"
  sleep 5
done

>&2 echo "$(date '+%Y-%m-%d %H:%M:%S') - AceStream is up - executing command"
exec $cmd
