#!/usr/bin/env python3
"""
Compare sequential vs parallel document loading speeds
"""
import os
import sys
import asyncio
import time
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lightrag import LightRAG
from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
from lightrag.kg.shared_storage import initialize_pipeline_status

# Load environment variables
load_dotenv()

# Configuration
WORKING_DIR_BASE = project_root / "lightrag_speed_test"
TRANSCRIPTS_DIR = project_root / "transcripts"

async def test_loading_speed(parallel_level, test_name, num_docs=5):
    """Test loading speed with given parallel level"""
    
    working_dir = WORKING_DIR_BASE / test_name
    
    # Clean up previous test
    if working_dir.exists():
        shutil.rmtree(working_dir)
    working_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"Testing: {test_name}")
    print(f"Parallel level: {parallel_level}")
    print(f"Number of documents: {num_docs}")
    print('='*60)
    
    # Initialize LightRAG
    rag = LightRAG(
        working_dir=str(working_dir),
        llm_model_func=gpt_4o_mini_complete,
        embedding_func=openai_embed,
        max_parallel_insert=parallel_level,
        embedding_func_max_async=32 if parallel_level > 1 else 16,
        llm_model_max_async=8 if parallel_level > 1 else 4,
    )
    
    await rag.initialize_storages()
    await initialize_pipeline_status()
    
    # Load transcripts
    transcript_files = list(TRANSCRIPTS_DIR.glob("*.txt"))
    exclude_files = {'requirements.txt', 'runtime.txt', 'aider.txt', 'scripts.txt', 
                     'analysis_iteration_0.txt', 'overall_summary.txt'}
    transcript_files = [f for f in transcript_files if f.name not in exclude_files][:num_docs]
    
    # Prepare documents
    contents = []
    file_paths = []
    
    for file_path in transcript_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            contents.append(f.read())
            file_paths.append(str(file_path.name))
    
    # Time the insertion
    start_time = time.time()
    
    if parallel_level == 1:
        # Sequential loading
        print("Loading documents sequentially...")
        for i, (content, file_path) in enumerate(zip(contents, file_paths), 1):
            print(f"  [{i}/{num_docs}] Processing: {file_path}")
            await rag.ainsert(content, file_paths=[file_path])
    else:
        # Parallel loading
        print(f"Loading documents in parallel (workers={parallel_level})...")
        await rag.ainsert(contents, file_paths=file_paths)
    
    elapsed_time = time.time() - start_time
    
    # Get final status
    status_counts = await rag.get_processing_status()
    processed = status_counts.get('PROCESSED', 0)
    failed = status_counts.get('FAILED', 0)
    
    # Results
    print(f"\nResults:")
    print(f"  Total time: {elapsed_time:.2f} seconds")
    print(f"  Documents processed: {processed}")
    print(f"  Documents failed: {failed}")
    print(f"  Average time per document: {elapsed_time/num_docs:.2f} seconds")
    
    # Cleanup
    await rag.finalize_storages()
    
    return {
        'test_name': test_name,
        'parallel_level': parallel_level,
        'total_time': elapsed_time,
        'docs_processed': processed,
        'docs_failed': failed,
        'avg_time': elapsed_time/num_docs
    }

async def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: Please set OPENAI_API_KEY")
        return
    
    print("Document Loading Speed Comparison")
    print("="*60)
    
    # Get number of documents to test
    num_docs = 5
    user_input = input(f"Number of documents to test (default={num_docs}): ").strip()
    if user_input:
        try:
            num_docs = int(user_input)
        except ValueError:
            print("Invalid input. Using default.")
    
    # Clean up test directory
    if WORKING_DIR_BASE.exists():
        shutil.rmtree(WORKING_DIR_BASE)
    
    # Run tests
    results = []
    
    # Test sequential loading
    result1 = await test_loading_speed(1, "sequential", num_docs)
    results.append(result1)
    
    # Test parallel loading with different levels
    for level in [2, 4, 8]:
        result = await test_loading_speed(level, f"parallel_{level}", num_docs)
        results.append(result)
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    print(f"{'Test':<20} {'Time (s)':<12} {'Avg/Doc (s)':<12} {'Speedup':<10}")
    print('-'*60)
    
    baseline_time = results[0]['total_time']
    for result in results:
        speedup = baseline_time / result['total_time']
        print(f"{result['test_name']:<20} "
              f"{result['total_time']:<12.2f} "
              f"{result['avg_time']:<12.2f} "
              f"{speedup:<10.2f}x")
    
    print(f"\nBest performance: {min(results, key=lambda x: x['total_time'])['test_name']}")
    
    # Clean up
    if WORKING_DIR_BASE.exists():
        shutil.rmtree(WORKING_DIR_BASE)

if __name__ == "__main__":
    asyncio.run(main())