# LightRAG Input Requirements and Best Practices

Based on exploration of the LightRAG source code, here are the key findings about input formats and processing requirements:

## Input Format Acceptance

### 1. Basic Text Input
- **Primary Input Method**: `insert()` method accepts either:
  - Single string: `rag.insert("Your text here")`
  - List of strings: `rag.insert(["Document 1", "Document 2", "Document 3"])`

### 2. Document Identification
- **Document IDs**: Optional unique identifiers for each document
  - If not provided, MD5 hash IDs are automatically generated
  - Must be unique across all documents
  - Example: `rag.insert(texts, ids=["doc1", "doc2", "doc3"])`

### 3. Source Attribution (Citation Support)
- **File Paths**: Optional file paths for citation purposes
  - Used to track the source of each document
  - If not provided, defaults to "unknown_source"
  - Example: `rag.insert(texts, file_paths=["path/to/doc1.txt", "path/to/doc2.txt"])`

## Text Processing Pipeline

### 1. Text Cleaning
- **Minimal Cleaning**: LightRAG applies very minimal text cleaning:
  ```python
  def clean_text(text: str) -> str:
      return text.strip().replace("\x00", "")
  ```
- Only removes:
  - Leading/trailing whitespace
  - Null bytes (0x00)

### 2. Chunking Strategy
- **Default Chunking**: By token size (default: 1200 tokens)
- **Overlap**: 100 tokens overlap between chunks (configurable)
- **Character-based splitting**: Optional split by specific character (e.g., "\n\n" for paragraphs)
  ```python
  rag.insert(text, split_by_character="\n\n")
  ```

### 3. Token Limits
- **Chunk Size**: Default 1200 tokens per chunk (configurable via `CHUNK_SIZE` env var)
- **Overlap Size**: Default 100 tokens (configurable via `CHUNK_OVERLAP_SIZE` env var)
- **Tokenizer**: Uses tiktoken with "gpt-4o-mini" model by default

## What Makes Content "Clean" for LightRAG

### 1. Text Quality Requirements
- **Plain Text**: LightRAG works best with plain text content
- **No Special Formatting Required**: The system handles raw text well
- **Preserve Structure**: Natural paragraph breaks help with chunking

### 2. Optimal Content Characteristics
- **Coherent Chunks**: Text should be logically organized (paragraphs, sections)
- **Complete Sentences**: Avoid cutting off mid-sentence when preparing content
- **Contextual Completeness**: Each chunk should ideally contain complete thoughts/concepts

### 3. Things to Avoid
- **Binary Data**: Remove any binary content
- **Excessive Formatting**: Strip excessive HTML/markdown if not needed
- **Null Bytes**: These are automatically removed but better to clean beforehand

## Special Input Methods

### 1. Custom Chunks
- You can provide pre-chunked content via `insert_custom_chunks()`
- Useful when you have specific chunking requirements

### 2. Custom Knowledge Graph
- Direct insertion of entities and relationships via `insert_custom_kg()`
- Format:
  ```python
  custom_kg = {
      "entities": [...],
      "relationships": [...],
      "chunks": [...]
  }
  ```

### 3. Multiple File Types (via textract)
- Mentioned support for PDF, DOC, PPT, CSV
- Requires additional dependencies

## Best Practices for Content Preparation

1. **Preserve Natural Structure**: Keep paragraph breaks and section divisions
2. **Clean Encoding**: Ensure UTF-8 encoding without special characters
3. **Meaningful Chunks**: If splitting manually, ensure each chunk is self-contained
4. **Source Tracking**: Always provide file_paths for better citation support
5. **Unique IDs**: Use meaningful IDs if managing document updates

## Configuration Options

Key parameters that affect input processing:
- `chunk_token_size`: Maximum tokens per chunk
- `chunk_overlap_token_size`: Overlap between chunks
- `tiktoken_model_name`: Tokenizer model
- `entity_extract_max_gleaning`: Retries for entity extraction
- `summary_to_max_tokens`: Maximum tokens for summaries

## Example Usage

```python
# Simple text insertion
rag.insert("Your document content here")

# Multiple documents with metadata
texts = ["Document 1 content", "Document 2 content"]
ids = ["doc_001", "doc_002"]
paths = ["docs/doc1.txt", "docs/doc2.txt"]
rag.insert(texts, ids=ids, file_paths=paths)

# With custom chunking
rag.insert(long_text, split_by_character="\n\n", split_by_character_only=True)
```