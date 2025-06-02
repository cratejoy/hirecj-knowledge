# Makefile for hirecj-knowledge project

.PHONY: help dangerous-clean setup process stop

help:
	@echo "Available commands:"
	@echo "  make setup           - Install dependencies and set up environment"
	@echo "  make process         - Run the ingestion pipeline"
	@echo "  make stop            - Stop any running services"
	@echo "  make dangerous-clean - ⚠️  DELETE EVERYTHING (content + database)"
	@echo ""
	@echo "Use with caution!"

# ⚠️  DANGEROUS - Deletes all content and database without confirmation
dangerous-clean:
	@echo "🔥 DANGEROUS CLEAN - Deleting everything..."
	@echo "  - Removing all content from pipeline directories..."
	@find content -type f -delete 2>/dev/null || true
	@find content -type d -mindepth 2 -empty -delete 2>/dev/null || true
	@echo "  - Removing LightRAG database..."
	@rm -rf lightrag_transcripts_db
	@echo "  - Removing log files..."
	@rm -f lightrag_debug.log process.log process_debug.log test_process.log *.log
	@echo "✅ Clean slate complete - all data deleted!"
	@echo ""
	@echo "You can now:"
	@echo "  - Add content:  python src/ingest.py add <URL>"
	@echo "  - Process all:  python src/ingest.py process"
	@echo "  - Or both:      python src/ingest.py"

setup:
	@echo "Setting up hirecj-knowledge environment..."
	@pip install -r requirements.txt
	@pip install -e ../third-party/LightRAG
	@echo "✅ Setup complete!"
	@echo ""
	@echo "Don't forget to set your OpenAI API key:"
	@echo "  export OPENAI_API_KEY='your-key-here'"

process:
	@echo "Running ingestion pipeline..."
	@python src/ingest.py

stop:
	@echo "Stopping hirecj-knowledge services..."
	@pkill -f "python src/ingest.py" 2>/dev/null || echo "No knowledge service running"