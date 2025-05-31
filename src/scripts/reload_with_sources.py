#!/usr/bin/env python3
"""
Reload transcripts with proper source tracking
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
from lightrag.kg.shared_storage import initialize_pipeline_status

# Load environment variables
load_dotenv()

# Configuration
WORKING_DIR = project_root / "lightrag_transcripts_db"
TRANSCRIPTS_DIR = project_root / "transcripts"

async def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: Please set OPENAI_API_KEY")
        return
    
    print("This will reload all transcripts with proper source tracking.")
    response = input("Continue? This will clear existing data. (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    # Clear existing database
    print("\nClearing existing database...")
    import shutil
    if WORKING_DIR.exists():
        shutil.rmtree(WORKING_DIR)
    WORKING_DIR.mkdir(parents=True)
    
    # Initialize LightRAG
    print("Initializing LightRAG...")
    rag = LightRAG(
        working_dir=str(WORKING_DIR),
        llm_model_func=gpt_4o_mini_complete,
        embedding_func=openai_embed,
    )
    
    await rag.initialize_storages()
    await initialize_pipeline_status()
    
    # Load transcripts with proper file tracking
    transcript_files = list(TRANSCRIPTS_DIR.glob("*.txt"))
    
    # Filter out non-transcript files
    exclude_files = {'requirements.txt', 'runtime.txt', 'aider.txt', 'scripts.txt', 
                     'analysis_iteration_0.txt', 'overall_summary.txt'}
    transcript_files = [f for f in transcript_files if f.name not in exclude_files]
    
    print(f"\nFound {len(transcript_files)} transcript files")
    print("Loading with source tracking...\n")
    
    for i, file_path in enumerate(transcript_files, 1):
        try:
            print(f"[{i}/{len(transcript_files)}] Processing: {file_path.name}")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Insert with proper file path
            await rag.ainsert(
                content, 
                file_paths=[str(file_path.name)]  # This will show up in the source
            )
            
        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")
    
    print("\nAll transcripts loaded with source tracking!")
    print("Sources will now show the actual filename instead of 'unknown_source'")
    
    # Cleanup
    await rag.finalize_storages()

if __name__ == "__main__":
    asyncio.run(main())