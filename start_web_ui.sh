#!/bin/bash

echo "Starting LightRAG Web UI..."
echo ""
echo "The web interface will be available at: http://localhost:9621"
echo ""

# Activate virtual environment
source venv/bin/activate

# Set the working directory to use existing database
export LIGHTRAG_WORKING_DIR="./lightrag_transcripts_db"

# Run the server
cd ../third-party/LightRAG
lightrag-server --working-dir "../../hirecj-knowledge/lightrag_transcripts_db" --input-dir "../../hirecj-knowledge/transcripts"