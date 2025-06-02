# LightRAG Citations: Complete Flow Documentation

## Overview

LightRAG provides automatic citation/source attribution in its responses. This document explains the complete flow from filename → LightRAG → user-visible citation.

## Key Discovery: The `file_paths` Parameter

The `ainsert` method in LightRAG accepts a `file_paths` parameter specifically for citations:

```python
async ainsert(
    self, 
    input: str | list[str], 
    file_paths: str | list[str] | None = None  # ← This is for citations!
)
```

## Current Implementation Status

### ❌ What's Currently Happening
In the existing scripts (`lightrag_transcripts_demo.py`, `simple_demo.py`), documents are inserted WITHOUT file path metadata:

```python
# Current implementation - NO file path passed
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
    await rag.ainsert(content)  # ← Missing file_paths parameter!
```

### ✅ What Should Be Happening
To enable proper citations, the file path should be passed:

```python
# Correct implementation - WITH file path
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
    await rag.ainsert(content, file_paths=str(file_path))
```

## Citation Types in LightRAG

Based on the output from running the demos, LightRAG shows two types of citations:

1. **Knowledge Graph Citations**: `[KG] filename.txt`
   - These appear when information comes from the knowledge graph
   - Shows just the filename, not the full path

2. **Document Chunk Citations**: `[DC] file_path: "Title [URL]"`
   - These appear when information comes directly from document chunks
   - Can include more detailed source information

## Full Flow: Filename → LightRAG → User Citation

1. **File Loading**:
   ```python
   file_path = Path("transcripts/Marketing on Zero Budget.txt")
   content = file_path.read_text()
   ```

2. **Insert with Metadata**:
   ```python
   await rag.ainsert(
       content,
       file_paths=str(file_path)  # Critical: Pass the file path!
   )
   ```

3. **LightRAG Processing**:
   - Document is chunked and processed
   - Entities and relationships are extracted
   - File path metadata is associated with each chunk

4. **Query Time**:
   ```python
   result = await rag.aquery("What marketing strategies work?")
   ```

5. **User-Visible Citation**:
   ```
   Marketing strategies include...
   
   ### References
   - [KG] Marketing on Zero Budget.txt
   ```

## Fixing Existing Scripts

To enable citations in the existing codebase:

### 1. Update `lightrag_transcripts_demo.py`:
```python
# Line 72, change from:
await rag.ainsert(content)

# To:
await rag.ainsert(content, file_paths=str(file_path))
```

### 2. Update `simple_demo.py`:
```python
# Line 67, change from:
await rag.ainsert(content)

# To:
await rag.ainsert(content, file_paths=str(filepath))
```

## Testing Citations

Use the test script created at `src/scripts/test_citations.py` to verify citation functionality:

```bash
python src/scripts/test_citations.py
```

This script:
1. Loads transcripts WITH file paths
2. Runs test queries
3. Checks if citations appear in responses
4. Cleans up after testing

## Important Notes

1. **Existing Data**: Documents already loaded without file paths won't have citations. You'll need to reload them with the file_paths parameter.

2. **File Path Format**: LightRAG extracts just the filename from the full path for display in citations.

3. **Citation Appearance**: Citations appear at the end of responses in a "References" section.

4. **Multiple Documents**: When inserting multiple documents, pass a list of file paths:
   ```python
   await rag.ainsert(
       [content1, content2],
       file_paths=[path1, path2]
   )
   ```

## Next Steps

1. Update existing scripts to pass file_paths
2. Reload existing transcripts with proper metadata
3. Consider adding source URLs or other metadata for richer citations
4. Test with the eCommerceFuel forum data to ensure citations work for scraped content