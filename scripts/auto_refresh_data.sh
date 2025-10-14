#!/bin/bash
# Auto-refresh market data every 60 seconds
while true; do
  ./scripts/keep_data_fresh.sh > /dev/null 2>&1
  sleep 60
done
