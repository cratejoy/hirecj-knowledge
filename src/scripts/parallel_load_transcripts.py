#!/usr/bin/env python3
"""
Load transcripts with parallel processing for faster loading
"""
import os
import sys
import asyncio
import time
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
    
    # Get parallel processing level from environment or user
    default_parallel = int(os.getenv("MAX_PARALLEL_INSERT", 4))
    print(f"Current parallel processing level: {default_parallel}")
    user_input = input(f"Enter desired parallel processing level (1-10, default={default_parallel}): ").strip()
    
    if user_input:
        try:
            parallel_level = int(user_input)
            if 1 <= parallel_level <= 10:
                default_parallel = parallel_level
            else:
                print("Invalid input. Using default.")
        except ValueError:
            print("Invalid input. Using default.")
    
    print(f"\nUsing parallel processing level: {default_parallel}")
    
    # Initialize LightRAG with parallel processing
    print("Initializing LightRAG with parallel processing...")
    rag = LightRAG(
        working_dir=str(WORKING_DIR),
        llm_model_func=gpt_4o_mini_complete,
        embedding_func=openai_embed,
        max_parallel_insert=default_parallel,  # Enable parallel processing
        # Increase async limits for better parallelism
        embedding_func_max_async=32,  # Increase embedding parallelism
        llm_model_max_async=8,  # Increase LLM parallelism
    )
    
    await rag.initialize_storages()
    await initialize_pipeline_status()
    
    # Load transcripts
    transcript_files = list(TRANSCRIPTS_DIR.glob("*.txt"))
    
    # Filter out non-transcript files
    exclude_files = {'requirements.txt', 'runtime.txt', 'aider.txt', 'scripts.txt', 
                     'analysis_iteration_0.txt', 'overall_summary.txt'}
    transcript_files = [f for f in transcript_files if f.name not in exclude_files]
    
    print(f"\nFound {len(transcript_files)} transcript files")
    print(f"Loading with parallel processing (level={default_parallel})...\n")
    
    # Start timing
    start_time = time.time()
    
    # Load all files at once - LightRAG will handle parallelization internally
    try:
        # Read all file contents
        contents = []
        file_paths = []
        
        for file_path in transcript_files:
            print(f"Reading: {file_path.name}")
            with open(file_path, 'r', encoding='utf-8') as f:
                contents.append(f.read())
                file_paths.append(str(file_path.name))
        
        print(f"\nInserting {len(contents)} documents in parallel...")
        print("This will be faster than sequential processing!\n")
        
        # Insert all at once - LightRAG handles parallelization
        await rag.ainsert(
            contents,  # List of all documents
            file_paths=file_paths  # List of all file paths
        )
        
    except Exception as e:
        print(f"Error during parallel processing: {e}")
    
    # Calculate time taken
    elapsed_time = time.time() - start_time
    print(f"\nAll transcripts loaded in {elapsed_time:.2f} seconds!")
    print(f"Average time per document: {elapsed_time/len(transcript_files):.2f} seconds")
    
    # Show processing stats
    status_counts = await rag.get_processing_status()
    print("\nProcessing status:")
    for status, count in status_counts.items():
        print(f"  {status}: {count}")
    
    # Cleanup
    await rag.finalize_storages()

if __name__ == "__main__":
    asyncio.run(main())