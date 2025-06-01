#!/usr/bin/env python3
"""
Safe processing of pending LightRAG documents with better error handling
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

async def safe_process_documents(rag):
    """Process documents with error handling for entity extraction issues"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            print(f"\nProcessing attempt {retry_count + 1}/{max_retries}")
            await rag.apipeline_process_enqueue_documents()
            
            # Wait a bit to let processing start
            await asyncio.sleep(5)
            
            # Check status
            status_counts = await rag.get_processing_status()
            processing = status_counts.get(DocStatus.PROCESSING, 0)
            
            if processing > 0:
                print(f"Documents are being processed: {processing} in progress")
                # Wait for processing to complete or error
                await asyncio.sleep(30)
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            if "invalid entity type" in error_msg or "Entity extraction error" in error_msg:
                print(f"⚠️  Entity extraction error encountered: {error_msg[:200]}...")
                print("   Continuing with next batch...")
                retry_count += 1
                await asyncio.sleep(2)
            else:
                print(f"❌ Unexpected error: {error_msg}")
                raise
    
    return False

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
        
        # Process in batches to handle errors better
        batch_size = 10
        processed = 0
        
        while pending_count > 0:
            print(f"\nProcessing batch starting at {processed}...")
            
            success = await safe_process_documents(rag)
            
            if not success:
                print("⚠️  Batch processing encountered errors, moving to next batch")
            
            # Check new status
            await asyncio.sleep(5)
            status_counts = await rag.get_processing_status()
            new_pending = status_counts.get(DocStatus.PENDING, 0)
            
            if new_pending >= pending_count:
                print("⚠️  No progress made, some documents may be stuck")
                break
                
            processed += (pending_count - new_pending)
            pending_count = new_pending
            
            print(f"Progress: {processed} documents processed")
            
            if pending_count > 0:
                print(f"Remaining: {pending_count} documents")
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