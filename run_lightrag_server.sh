#!/bin/bash

# Script to run LightRAG server with existing database

echo "Starting LightRAG Web UI Server..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set environment variables
export WORKING_DIR="./lightrag_transcripts_db"
export INPUT_DIR="./transcripts"

# Check if lightrag-server is available
if ! command -v lightrag-server &> /dev/null; then
    echo "Error: lightrag-server not found. Installing..."
    pip install -e "../third-party/LightRAG[api]"
fi

# Create config file for the server
cat > lightrag_config.ini << EOF
[llm]
binding = openai
model = gpt-4o-mini
api_key = ${OPENAI_API_KEY}

[embedding]
binding = openai
model = text-embedding-3-small
api_key = ${OPENAI_API_KEY}

[storage]
working_dir = ${WORKING_DIR}

[server]
input_dir = ${INPUT_DIR}
EOF

echo "Configuration:"
echo "- Working directory: ${WORKING_DIR}"
echo "- Input directory: ${INPUT_DIR}"
echo "- Server URL: http://localhost:9621"
echo ""
echo "Starting server..."

# Run the server
lightrag-server \
    --host 0.0.0.0 \
    --port 9621 \
    --input-dir "${INPUT_DIR}" \
    --working-dir "${WORKING_DIR}"