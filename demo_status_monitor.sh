#!/bin/bash

echo "📺 Demo: Pipeline Status Monitor"
echo "================================"
echo ""
echo "1. Regular status (one-time):"
echo "   python src/ingest.py status"
echo ""
echo "2. Monitor status with default 5s refresh:"
echo "   python src/ingest.py status -t"
echo ""
echo "3. Monitor status with 10s refresh:"
echo "   python src/ingest.py status -t 10"
echo ""
echo "Starting monitor with 3 second refresh..."
echo "Press Ctrl+C to stop"
echo ""
sleep 2

python src/ingest.py status -t 3