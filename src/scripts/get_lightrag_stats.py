#!/usr/bin/env python3
"""Get statistics from LightRAG instance"""

import asyncio
import sys
sys.path.append('..')

from lightrag import LightRAG
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.types import GPTKeywordExtractionFormat
from lightrag.utils import EmbeddingFunc
import os

# Get OpenAI API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

async def get_lightrag_stats():
    """Get statistics from the LightRAG database"""
    
    # Initialize embedding function
    embedding_func = EmbeddingFunc(
        embedding_dim=1536,
        max_token_size=8192,
        func=lambda texts: openai_embed(
            texts,
            model="text-embedding-3-small",
            api_key=OPENAI_API_KEY
        )
    )
    
    # Initialize RAG
    rag = LightRAG(
        working_dir="../../lightrag_transcripts_db",
        llm_model_func=lambda prompt, **kwargs: openai_complete_if_cache(
            "gpt-4o-mini",
            prompt,
            api_key=OPENAI_API_KEY,
            **kwargs
        ),
        llm_model_name="gpt-4o-mini",
        embedding_func=embedding_func,
        enable_llm_cache=True,
    )
    
    try:
        # Initialize storages
        await rag.initialize_storages()
        
        print("LightRAG Database Statistics")
        print("=" * 50)
        
        # Get graph statistics
        # Access the underlying NetworkX graph through the storage
        if hasattr(rag.chunk_entity_relation_graph, '_graph'):
            graph = rag.chunk_entity_relation_graph._graph
            num_nodes = graph.number_of_nodes()
            num_edges = graph.number_of_edges()
            print(f"Graph nodes (entities): {num_nodes}")
            print(f"Graph edges (relationships): {num_edges}")
        else:
            print("Could not access graph statistics directly")
            
        # Get entities count from vector storage
        if hasattr(rag.entities_vdb, '_client'):
            entities_count = len(rag.entities_vdb._client)
            print(f"Entities in vector DB: {entities_count}")
        else:
            print("Could not access entities vector DB count")
            
        # Get relationships count from vector storage
        if hasattr(rag.relationships_vdb, '_client'):
            relationships_count = len(rag.relationships_vdb._client)
            print(f"Relationships in vector DB: {relationships_count}")
        else:
            print("Could not access relationships vector DB count")
            
        # Get chunks count from vector storage
        if hasattr(rag.chunks_vdb, '_client'):
            chunks_count = len(rag.chunks_vdb._client)
            print(f"Chunks in vector DB: {chunks_count}")
        else:
            print("Could not access chunks vector DB count")
            
        # Get text chunks count from KV storage
        all_chunks = await rag.text_chunks.get_all()
        text_chunks_count = len(all_chunks)
        print(f"Text chunks in KV storage: {text_chunks_count}")
        
        # Get document status counts
        if hasattr(rag, 'doc_status_storage') and hasattr(rag.doc_status_storage, 'get_status_counts'):
            try:
                status_counts = await rag.doc_status_storage.get_status_counts()
                print("\nDocument Status:")
                for status, count in status_counts.items():
                    print(f"  {status}: {count}")
            except Exception as e:
                print(f"\nCould not get document status: {e}")
        
        # Get all node labels (a sample)
        labels = await rag.chunk_entity_relation_graph.get_all_labels()
        print(f"\nTotal unique entity labels: {len(labels)}")
        print(f"Sample labels (first 10): {labels[:10]}")
        
    except Exception as e:
        print(f"Error getting statistics: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        await rag.finalize_storages()

if __name__ == "__main__":
    asyncio.run(get_lightrag_stats())