#!/usr/bin/env python3
"""
Manually process pending documents in LightRAG
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Add LightRAG to path
sys.path.insert(0, str(project_root.parent / "third-party" / "LightRAG"))

from lightrag import LightRAG
from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.base import DocStatus

# Load environment variables
load_dotenv()

async def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: Please set OPENAI_API_KEY")
        return
    
    print("Initializing LightRAG...")
    rag = LightRAG(
        working_dir="./lightrag_transcripts_db",
        llm_model_func=gpt_4o_mini_complete,
        embedding_func=openai_embed,
    )
    
    # Initialize storages
    await rag.initialize_storages()
    await initialize_pipeline_status()
    
    # Check current status
    print("\nChecking document status...")
    status_counts = await rag.get_processing_status()
    
    print(f"Current status:")
    print(f"  Pending: {status_counts.get(DocStatus.PENDING, 0)}")
    print(f"  Processing: {status_counts.get(DocStatus.PROCESSING, 0)}")
    print(f"  Processed: {status_counts.get(DocStatus.PROCESSED, 0)}")
    print(f"  Failed: {status_counts.get(DocStatus.FAILED, 0)}")
    
    pending_count = status_counts.get(DocStatus.PENDING, 0)
    if pending_count > 0:
        print(f"\nProcessing {pending_count} pending documents...")
        
        # Manually trigger processing
        await rag.apipeline_process_enqueue_documents()
        
        # Wait and check status again
        print("Waiting for processing to complete...")
        max_wait = 60  # seconds
        check_interval = 5
        
        for i in range(0, max_wait, check_interval):
            await asyncio.sleep(check_interval)
            status_counts = await rag.get_processing_status()
            
            pending = status_counts.get(DocStatus.PENDING, 0)
            processing = status_counts.get(DocStatus.PROCESSING, 0)
            processed = status_counts.get(DocStatus.PROCESSED, 0)
            
            print(f"\nAfter {i+check_interval}s - Pending: {pending}, Processing: {processing}, Processed: {processed}")
            
            if pending == 0 and processing == 0:
                print("\nAll documents processed!")
                break
    else:
        print("\nNo pending documents to process.")
    
    # Final status
    print("\nFinal document status:")
    status_counts = await rag.get_processing_status()
    for status in [DocStatus.PENDING, DocStatus.PROCESSING, DocStatus.PROCESSED, DocStatus.FAILED]:
        count = status_counts.get(status, 0)
        if count > 0:
            print(f"  {status.value}: {count}")

if __name__ == "__main__":
    asyncio.run(main())