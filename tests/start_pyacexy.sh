#!/bin/bash
# Script to run pyacexy standalone on port 8080

cd "$(dirname "$0")/../pyacexy"

echo "Starting pyacexy on port 8080..."
echo "AceStream Engine: localhost:6878"
echo ""

python3 -m pyacexy.proxy \
    --host 0.0.0.0 \
    --port 8080 \
    --acestream-host localhost \
    --acestream-port 6878

