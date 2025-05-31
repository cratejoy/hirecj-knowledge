#!/usr/bin/env python3
"""
Monitor parallel document loading with real-time progress
"""
import os
import sys
import asyncio
import time
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
from lightrag.kg.shared_storage import initialize_pipeline_status, get_namespace_data
from lightrag.base import DocStatus

# Load environment variables
load_dotenv()

# Configuration
WORKING_DIR = project_root / "lightrag_transcripts_db"
TRANSCRIPTS_DIR = project_root / "transcripts"

async def monitor_progress(rag, total_docs):
    """Monitor the progress of document processing"""
    print("\nMonitoring progress...")
    print("-" * 60)
    
    start_time = time.time()
    last_processed = 0
    
    while True:
        # Get current status
        status_counts = await rag.get_processing_status()
        
        # Calculate totals
        processed = status_counts.get(DocStatus.PROCESSED, 0)
        processing = status_counts.get(DocStatus.PROCESSING, 0)
        pending = status_counts.get(DocStatus.PENDING, 0)
        failed = status_counts.get(DocStatus.FAILED, 0)
        
        # Calculate progress
        total_done = processed + failed
        elapsed_time = time.time() - start_time
        
        # Calculate rate
        if elapsed_time > 0 and processed > last_processed:
            rate = (processed - last_processed) / (elapsed_time if last_processed == 0 else 1)
            last_processed = processed
        else:
            rate = 0
        
        # Clear line and print status
        print(f"\r[{datetime.now().strftime('%H:%M:%S')}] "
              f"Processed: {processed}/{total_docs} | "
              f"Processing: {processing} | "
              f"Pending: {pending} | "
              f"Failed: {failed} | "
              f"Rate: {rate:.1f} docs/sec", end='', flush=True)
        
        # Check if done
        if total_done >= total_docs or (pending == 0 and processing == 0):
            print("\n" + "-" * 60)
            print(f"Total time: {elapsed_time:.2f} seconds")
            print(f"Average: {elapsed_time/max(total_done, 1):.2f} seconds per document")
            break
        
        # Check pipeline status for more detailed info
        pipeline_status = await get_namespace_data("pipeline_status")
        if pipeline_status.get("busy"):
            latest_msg = pipeline_status.get("latest_message", "")
            if latest_msg:
                print(f"\n└─> {latest_msg}", end='', flush=True)
        
        await asyncio.sleep(1)

async def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: Please set OPENAI_API_KEY")
        return
    
    # Configuration
    parallel_level = int(os.getenv("MAX_PARALLEL_INSERT", 4))
    print(f"Parallel processing level: {parallel_level}")
    
    # Initialize LightRAG
    print("Initializing LightRAG...")
    rag = LightRAG(
        working_dir=str(WORKING_DIR),
        llm_model_func=gpt_4o_mini_complete,
        embedding_func=openai_embed,
        max_parallel_insert=parallel_level,
        embedding_func_max_async=32,
        llm_model_max_async=8,
    )
    
    await rag.initialize_storages()
    await initialize_pipeline_status()
    
    # Load transcripts
    transcript_files = list(TRANSCRIPTS_DIR.glob("*.txt"))
    exclude_files = {'requirements.txt', 'runtime.txt', 'aider.txt', 'scripts.txt', 
                     'analysis_iteration_0.txt', 'overall_summary.txt'}
    transcript_files = [f for f in transcript_files if f.name not in exclude_files]
    
    print(f"\nFound {len(transcript_files)} transcript files")
    
    # Prepare documents
    contents = []
    file_paths = []
    
    print("\nPreparing documents...")
    for file_path in transcript_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            contents.append(f.read())
            file_paths.append(str(file_path.name))
    
    # Start monitoring task
    monitor_task = asyncio.create_task(monitor_progress(rag, len(transcript_files)))
    
    # Insert documents
    print(f"\nStarting parallel insertion with {parallel_level} workers...")
    
    try:
        await rag.ainsert(contents, file_paths=file_paths)
    except Exception as e:
        print(f"\nError during insertion: {e}")
    
    # Wait for monitoring to complete
    await monitor_task
    
    # Final status
    print("\nFinal status:")
    status_counts = await rag.get_processing_status()
    for status, count in status_counts.items():
        if count > 0:
            print(f"  {status}: {count}")
    
    # Cleanup
    await rag.finalize_storages()

if __name__ == "__main__":
    asyncio.run(main())