#!/usr/bin/env bash
# Panel Health Check Script
# Tests both /health endpoint and root / for React apps

set -e

URL="${1:-http://localhost:3001}"

# Try multiple endpoints
for path in /health /index.html /; do
  if curl -fsS --max-time 3 "$URL$path" >/dev/null 2>&1; then
    echo "OK:$path"
    exit 0
  fi
done

echo "FAIL"
exit 1







