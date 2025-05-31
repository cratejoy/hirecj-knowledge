#!/usr/bin/env python3
"""LightRAG statistics module - provides functions to get graph statistics"""

import asyncio
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

from lightrag import LightRAG
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc


@dataclass
class LightRAGStats:
    """Container for LightRAG statistics"""
    graph_nodes: int = 0
    graph_edges: int = 0
    entities_vdb_count: int = 0
    relationships_vdb_count: int = 0
    chunks_vdb_count: int = 0
    text_chunks_count: int = 0
    unique_labels_count: int = 0
    sample_labels: list[str] = None
    document_status: Dict[str, int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "graph": {
                "nodes": self.graph_nodes,
                "edges": self.graph_edges
            },
            "vector_db": {
                "entities": self.entities_vdb_count,
                "relationships": self.relationships_vdb_count,
                "chunks": self.chunks_vdb_count
            },
            "storage": {
                "text_chunks": self.text_chunks_count
            },
            "labels": {
                "unique_count": self.unique_labels_count,
                "samples": self.sample_labels or []
            },
            "documents": self.document_status or {}
        }


async def get_lightrag_stats(working_dir: str = "../../lightrag_transcripts_db", 
                            sample_labels_count: int = 10) -> LightRAGStats:
    """
    Get statistics from a LightRAG database
    
    Args:
        working_dir: Path to the LightRAG working directory
        sample_labels_count: Number of sample labels to return
        
    Returns:
        LightRAGStats object containing the statistics
    """
    # Get OpenAI API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    # Initialize embedding function
    embedding_func = EmbeddingFunc(
        embedding_dim=1536,
        max_token_size=8192,
        func=lambda texts: openai_embed(
            texts,
            model="text-embedding-3-small",
            api_key=api_key
        )
    )
    
    # Initialize RAG
    rag = LightRAG(
        working_dir=working_dir,
        llm_model_func=lambda prompt, **kwargs: openai_complete_if_cache(
            "gpt-4o-mini",
            prompt,
            api_key=api_key,
            **kwargs
        ),
        llm_model_name="gpt-4o-mini",
        embedding_func=embedding_func,
        enable_llm_cache=True,
    )
    
    stats = LightRAGStats()
    
    try:
        # Initialize storages
        await rag.initialize_storages()
        
        # Get graph statistics
        if hasattr(rag.chunk_entity_relation_graph, '_graph'):
            graph = rag.chunk_entity_relation_graph._graph
            stats.graph_nodes = graph.number_of_nodes()
            stats.graph_edges = graph.number_of_edges()
            
        # Get entities count from vector storage
        if hasattr(rag.entities_vdb, '_client'):
            stats.entities_vdb_count = len(rag.entities_vdb._client)
            
        # Get relationships count from vector storage
        if hasattr(rag.relationships_vdb, '_client'):
            stats.relationships_vdb_count = len(rag.relationships_vdb._client)
            
        # Get chunks count from vector storage
        if hasattr(rag.chunks_vdb, '_client'):
            stats.chunks_vdb_count = len(rag.chunks_vdb._client)
            
        # Get text chunks count from KV storage
        all_chunks = await rag.text_chunks.get_all()
        stats.text_chunks_count = len(all_chunks)
        
        # Get document status counts
        if hasattr(rag, 'doc_status_storage') and hasattr(rag.doc_status_storage, 'get_status_counts'):
            try:
                stats.document_status = await rag.doc_status_storage.get_status_counts()
            except Exception:
                pass
        
        # Get all node labels
        labels = await rag.chunk_entity_relation_graph.get_all_labels()
        stats.unique_labels_count = len(labels)
        stats.sample_labels = labels[:sample_labels_count]
        
    finally:
        # Clean up
        await rag.finalize_storages()
    
    return stats


async def print_lightrag_stats(working_dir: str = "../../lightrag_transcripts_db"):
    """Print LightRAG statistics to console"""
    stats = await get_lightrag_stats(working_dir)
    
    print("LightRAG Database Statistics")
    print("=" * 50)
    print(f"Graph nodes (entities): {stats.graph_nodes}")
    print(f"Graph edges (relationships): {stats.graph_edges}")
    print(f"Entities in vector DB: {stats.entities_vdb_count}")
    print(f"Relationships in vector DB: {stats.relationships_vdb_count}")
    print(f"Chunks in vector DB: {stats.chunks_vdb_count}")
    print(f"Text chunks in KV storage: {stats.text_chunks_count}")
    
    if stats.document_status:
        print("\nDocument Status:")
        for status, count in stats.document_status.items():
            print(f"  {status}: {count}")
    
    print(f"\nTotal unique entity labels: {stats.unique_labels_count}")
    print(f"Sample labels (first {len(stats.sample_labels)}): {stats.sample_labels}")


if __name__ == "__main__":
    asyncio.run(print_lightrag_stats())