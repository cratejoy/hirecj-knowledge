#!/usr/bin/env python3
"""
Test script to demonstrate how LightRAG citations work
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

# Load environment variables
load_dotenv()

# Configuration
WORKING_DIR = project_root / "test_citations_db"
TRANSCRIPTS_DIR = project_root / "transcripts"

async def main():
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: Please set OPENAI_API_KEY in your .env file")
        return
    
    # Initialize LightRAG
    print("Initializing LightRAG...")
    if not WORKING_DIR.exists():
        WORKING_DIR.mkdir(parents=True)
    
    rag = LightRAG(
        working_dir=str(WORKING_DIR),
        embedding_func=openai_embed,
        llm_model_func=gpt_4o_mini_complete,
    )
    
    await rag.initialize_storages()
    
    # Load a few transcripts WITH file paths
    print("\nLoading transcripts with file path metadata...")
    
    test_files = [
        "Marketing on Zero Budget.txt",
        "How to build a brand in 7mins _ Gary Vaynerchuk.txt",
        "Email Copywriting For Ecommerce In 2022 _As A Copywriter OR Online Store Owner_.txt"
    ]
    
    for filename in test_files:
        filepath = TRANSCRIPTS_DIR / filename
        if filepath.exists():
            print(f"Loading: {filename}")
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                # Pass the file path for citation
                await rag.ainsert(
                    content, 
                    file_paths=str(filepath)
                )
    
    print("\nWaiting for knowledge graph to build...")
    await asyncio.sleep(10)
    
    # Test queries
    print("\n" + "="*60)
    print("TESTING CITATIONS")
    print("="*60)
    
    queries = [
        "What marketing strategies work with zero budget?",
        "How does Gary Vaynerchuk suggest building a brand?",
        "What email copywriting tips are mentioned for ecommerce?"
    ]
    
    for query in queries:
        print(f"\n📝 Query: {query}")
        print("-" * 60)
        
        try:
            result = await rag.aquery(query, param=QueryParam(mode="hybrid"))
            print(f"💡 Answer:\n{result}\n")
            
            # Check if citations are included
            if "[KG]" in result or "[DC]" in result or "file_path:" in result:
                print("✅ Citations found in response!")
            else:
                print("❌ No citations found in response")
            
        except Exception as e:
            print(f"Error: {e}")
    
    # Cleanup
    await rag.finalize_storages()
    
    # Clean up test directory
    import shutil
    if WORKING_DIR.exists():
        shutil.rmtree(WORKING_DIR)
    
    print("\nTest complete!")

if __name__ == "__main__":
    asyncio.run(main())