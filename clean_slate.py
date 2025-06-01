#!/usr/bin/env python
"""
Clean slate script - removes all content and LightRAG database
WARNING: This will delete all processed content and knowledge graph data!
"""
import shutil
from pathlib import Path
import sys

def clean_slate():
    """Remove all content and database files"""
    
    print("🧹 CLEAN SLATE - This will delete:")
    print("  - All content in the pipeline (inbox, downloading, transcripts, etc.)")
    print("  - The entire LightRAG knowledge graph database")
    print("  - All cached responses and processing state")
    print()
    
    response = input("Are you sure you want to delete everything? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Cancelled - nothing was deleted")
        return
    
    # Directories to clean
    dirs_to_clean = [
        'content/inbox',
        'content/downloading', 
        'content/downloaded',
        'content/audio',
        'content/chunks',
        'content/transcribing',
        'content/transcripts',
        'content/loaded',
        'content/failed',
        'lightrag_transcripts_db'
    ]
    
    base_dir = Path('.')
    
    for dir_name in dirs_to_clean:
        dir_path = base_dir / dir_name
        if dir_path.exists():
            if dir_path.name == 'lightrag_transcripts_db':
                # Completely remove the database directory
                print(f"  🗑️  Removing database: {dir_path}")
                shutil.rmtree(dir_path)
            else:
                # For content dirs, just empty them but keep the directory
                print(f"  📁 Emptying: {dir_path}")
                for item in dir_path.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
    
    # Also remove any debug logs
    for log_file in ['lightrag_debug.log', 'process.log', 'process_debug.log', 'test_process.log']:
        log_path = base_dir / log_file
        if log_path.exists():
            print(f"  📄 Removing log: {log_path}")
            log_path.unlink()
    
    print()
    print("✅ Clean slate complete!")
    print()
    print("You can now:")
    print("1. Add new content: python src/ingest.py add <URL>")
    print("2. Process content: python src/ingest.py process")
    print("3. Or use both: python src/ingest.py")

if __name__ == "__main__":
    clean_slate()