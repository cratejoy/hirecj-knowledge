# LightRAG Source Attribution Guide

## Overview

LightRAG supports proper source attribution through the `file_paths` parameter when inserting documents. This guide explains how to ensure meaningful source citations appear in query responses instead of cryptic file IDs.

## Understanding [KG] and [DC] Prefixes

When LightRAG returns query results, it includes references at the bottom with prefixes:
- **[KG]** = Knowledge Graph (entities and relationships extracted from documents)
- **[DC]** = Document Chunks (raw text chunks from documents)

## The Problem

Without proper file path configuration, LightRAG shows cryptic references like:
```
[KG] rss_bdd50e88_epccad8a79.txt
[KG] rss_cfe7bb3c_epb272212c.txt
```

## The Solution

Pass meaningful file paths when inserting documents into LightRAG:

```python
# Instead of this:
rag.insert(content)  # Results in MD5 hash as source

# Or this:
rag.insert(content, file_paths=["rss_abc123_ep456.txt"])  # Cryptic ID

# Do this:
source_path = f"{podcast_name} - {episode_title} [{episode_url}]"
rag.insert(content, file_paths=[source_path])
```

This produces meaningful references like:
```
[KG] Marketing Masters Podcast - Test Episode About Marketing [https://example.com/episode123]
```

## Implementation in ingest.py

The `_process_audio` method already implements this correctly:

```python
# Create meaningful source path
title_clean = re.sub(r'[^\w\s-]', '', metadata.get('title', 'Unknown')).strip()[:50]
feed_clean = re.sub(r'[^\w\s-]', '', metadata.get('feed_title', 'Unknown Feed')).strip()[:30]

# Format: "Podcast Name - Episode Title [URL]"
source_path = f"{feed_clean} - {title_clean}"
if metadata.get('url'):
    source_path = f"{source_path} [{metadata.get('url')}]"

# Insert with meaningful source
self._load_to_lightrag(enriched, item_id, source_path)
```

## How LightRAG Uses file_paths

1. **Storage**: File paths are stored with chunks, entities, and relationships during insertion
2. **Retrieval**: When querying, LightRAG includes the file_path in the context
3. **Response**: The RAG prompt specifically asks to include file paths in references:
   ```
   List up to 5 most important reference sources at the end under "References" section. 
   Clearly indicating whether each source is from Knowledge Graph (KG) or Document Chunks (DC), 
   and include the file path if available, in the following format: [KG/DC] file_path
   ```

## Best Practices

1. **Always provide file_paths** when inserting documents
2. **Use descriptive paths** that include:
   - Source name (podcast, website, etc.)
   - Content title
   - URL if available
3. **Keep paths reasonable length** - aim for under 100 characters
4. **Be consistent** with formatting across your application

## Testing Source Attribution

To verify source attribution is working:

```python
from lightrag import LightRAG
from lightrag.base import QueryParam

# Insert with meaningful path
rag.insert(content, file_paths=["Podcast Name - Episode Title [URL]"])

# Query and check references
response = rag.query("your query", param=QueryParam(mode="mix"))
print(response)  # Should show meaningful references at the bottom
```

## Episode Filename Format

As of the latest update, RSS episode filenames themselves are now meaningful:
- Old format: `rss_bdd50e88_epccad8a79.json`
- New format: `HowToBuildConfidence_TheTimFerrissShow_abc123.json`

This ensures that even if metadata is lost, the filename itself provides context. The format is:
```
{EpisodeTitle}_{PodcastName}_{shortHash}
```

Where:
- `EpisodeTitle`: Sanitized episode title (max 50 chars) - comes first for better sorting
- `PodcastName`: Sanitized podcast name (max 30 chars)
- `shortHash`: 6-character hash for uniqueness

This format makes it easy to:
- See what the episode is about at a glance
- Sort episodes alphabetically by title
- Group episodes from the same podcast together

## Troubleshooting

If you're still seeing cryptic IDs:
1. Check that you're passing `file_paths` parameter to `insert()`
2. Verify the file path string is not empty
3. Ensure you're using the latest LightRAG version
4. Check that existing documents were inserted with proper file paths (may need to re-insert)
5. For RSS feeds added before this update, re-add them to get meaningful filenames