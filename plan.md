# Simple Content Ingestion Architecture

## 🌟 North Star Principles

1. **Simplify, Simplify, Simplify**: Every decision should make the code simpler, not more complex
2. **No Cruft**: Remove all redundant code, validation, and unnecessary complexity
3. **Break It & Fix It Right**: No backwards compatibility shims - make breaking changes and migrate properly
4. **Long-term Elegance**: Choose performant, compiler-enforced solutions that prevent subtle bugs
5. **Backend-Driven**: Let the backend handle complexity, frontend should be a thin client
6. **Single Source of Truth**: One pattern, one way to do things, no alternatives
7. **No Over-Engineering**: Design for current needs only - no hypothetical features, no "maybe later" code

## Overview

A directory-based system for downloading content (YouTube videos, RSS feeds, podcasts), transcribing via Whisper API, and loading into LightRAG.

## Directory Structure as State

```
content/
├── inbox/                    # URLs to process (one .url file per source)
│   └── youtube_abc123.url
├── downloading/             # Currently downloading (move .url here)
│   └── youtube_abc123.url
├── downloaded/              # Downloaded videos/audio
│   └── youtube_abc123/
│       ├── metadata.json
│       └── video.mp4
├── audio/                   # Extracted audio files
│   └── youtube_abc123/
│       └── audio.mp3
├── chunks/                  # Audio chunks for Whisper
│   └── youtube_abc123/
│       ├── chunk_001.mp3
│       └── chunk_002.mp3
├── transcribing/           # Currently transcribing
│   └── youtube_abc123/
├── transcripts/            # Completed transcripts
│   └── youtube_abc123.txt
└── failed/                 # Failed items
    └── youtube_abc123.error
```

## Core Components

### 1. Content Downloader

```python
import yt_dlp
from pathlib import Path
import json

def download_youtube(url: str, output_dir: Path):
    """Download YouTube video and save metadata"""
    ydl_opts = {
        'outtmpl': str(output_dir / 'video.%(ext)s'),
        'quiet': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        
        # Save metadata
        metadata = {
            'url': url,
            'title': info.get('title'),
            'duration': info.get('duration'),
            'upload_date': info.get('upload_date'),
        }
        
        with open(output_dir / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
```

### 2. Audio Extractor

```python
import subprocess

def extract_audio(video_path: Path, audio_path: Path):
    """Extract audio from video using ffmpeg"""
    cmd = [
        'ffmpeg', '-i', str(video_path),
        '-vn', '-acodec', 'mp3',
        '-ab', '128k',
        str(audio_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)
```

### 3. Audio Chunker

```python
from pydub import AudioSegment

def chunk_audio(audio_path: Path, output_dir: Path, max_size_mb: int = 24):
    """Split audio into chunks under 25MB for Whisper API"""
    audio = AudioSegment.from_mp3(audio_path)
    
    # Calculate chunk duration (rough estimate)
    bitrate = 128  # kbps
    max_duration_ms = (max_size_mb * 8 * 1024) / bitrate * 1000
    
    chunks = []
    for i, start in enumerate(range(0, len(audio), int(max_duration_ms))):
        chunk = audio[start:start + max_duration_ms]
        chunk_path = output_dir / f"chunk_{i:03d}.mp3"
        chunk.export(chunk_path, format="mp3")
        chunks.append(chunk_path)
    
    return chunks
```

### 4. Transcriber

```python
from openai import OpenAI

def transcribe_chunk(client: OpenAI, audio_path: Path) -> str:
    """Transcribe audio chunk using Whisper API"""
    with open(audio_path, 'rb') as f:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="text"
        )
    return response
```

### 5. Main Processor

```python
import shutil
from pathlib import Path

class ContentProcessor:
    def __init__(self, base_dir: Path = Path("content")):
        self.base_dir = base_dir
        self.ensure_directories()
        self.openai = OpenAI()
    
    def ensure_directories(self):
        """Create all required directories"""
        dirs = ['inbox', 'downloading', 'downloaded', 'audio', 
                'chunks', 'transcribing', 'transcripts', 'failed']
        for d in dirs:
            (self.base_dir / d).mkdir(parents=True, exist_ok=True)
    
    def add_url(self, url: str):
        """Add URL to inbox"""
        # Create unique ID from URL
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        
        if 'youtube.com' in url or 'youtu.be' in url:
            prefix = 'youtube'
        else:
            prefix = 'content'
        
        filename = f"{prefix}_{url_hash}.url"
        
        with open(self.base_dir / 'inbox' / filename, 'w') as f:
            f.write(url)
    
    def process_inbox(self):
        """Process all items in inbox"""
        inbox = self.base_dir / 'inbox'
        
        for url_file in inbox.glob('*.url'):
            try:
                self.process_item(url_file)
            except Exception as e:
                # Move to failed
                error_file = self.base_dir / 'failed' / url_file.stem + '.error'
                with open(error_file, 'w') as f:
                    f.write(f"URL: {url_file.read_text()}\n")
                    f.write(f"Error: {str(e)}\n")
                url_file.unlink()
    
    def process_item(self, url_file: Path):
        """Process single item through all stages"""
        url = url_file.read_text().strip()
        item_id = url_file.stem
        
        # 1. Download
        url_file.rename(self.base_dir / 'downloading' / url_file.name)
        download_dir = self.base_dir / 'downloaded' / item_id
        download_dir.mkdir(exist_ok=True)
        
        download_youtube(url, download_dir)
        
        # 2. Extract audio
        video_file = next(download_dir.glob('video.*'))
        audio_dir = self.base_dir / 'audio' / item_id
        audio_dir.mkdir(exist_ok=True)
        audio_file = audio_dir / 'audio.mp3'
        
        extract_audio(video_file, audio_file)
        
        # 3. Chunk audio
        chunks_dir = self.base_dir / 'chunks' / item_id
        chunks_dir.mkdir(exist_ok=True)
        
        chunks = chunk_audio(audio_file, chunks_dir)
        
        # 4. Transcribe
        shutil.move(str(chunks_dir), str(self.base_dir / 'transcribing' / item_id))
        transcribing_dir = self.base_dir / 'transcribing' / item_id
        
        transcripts = []
        for chunk in sorted(transcribing_dir.glob('chunk_*.mp3')):
            text = transcribe_chunk(self.openai, chunk)
            transcripts.append(text)
        
        # 5. Save transcript
        full_transcript = '\n'.join(transcripts)
        
        # Load metadata
        with open(download_dir / 'metadata.json') as f:
            metadata = json.load(f)
        
        # Create enriched transcript
        enriched = f"""Title: {metadata.get('title', 'Unknown')}
URL: {url}
Date: {metadata.get('upload_date', 'Unknown')}

{full_transcript}
"""
        
        transcript_file = self.base_dir / 'transcripts' / f"{item_id}.txt"
        transcript_file.write_text(enriched)
        
        # 6. Load into LightRAG
        self.load_to_lightrag(enriched)
        
        # 7. Cleanup
        (self.base_dir / 'downloading' / url_file.name).unlink()
        shutil.rmtree(transcribing_dir)
    
    def load_to_lightrag(self, content: str):
        """Load transcript into LightRAG"""
        from lightrag import LightRAG
        from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
        
        rag = LightRAG(
            working_dir="./lightrag_transcripts_db",
            embedding_func=openai_embed,
            llm_model_func=gpt_4o_mini_complete,
        )
        
        # Synchronous wrapper for async insert
        import asyncio
        asyncio.run(rag.ainsert(content))
```

### 6. Simple CLI

```python
#!/usr/bin/env python
import sys
from pathlib import Path

processor = ContentProcessor()

if len(sys.argv) < 2:
    print("Usage: ingest.py [add URL | process | status]")
    sys.exit(1)

command = sys.argv[1]

if command == "add" and len(sys.argv) > 2:
    url = sys.argv[2]
    processor.add_url(url)
    print(f"Added: {url}")

elif command == "process":
    processor.process_inbox()
    print("Processing complete")

elif command == "status":
    dirs = ['inbox', 'downloading', 'downloaded', 'transcripts', 'failed']
    for d in dirs:
        count = len(list((processor.base_dir / d).glob('*')))
        print(f"{d}: {count} items")
```

## Usage

```bash
# Add content
python ingest.py add "https://youtube.com/watch?v=..."
python ingest.py add "https://podcast.rss.feed/..."

# Process all pending
python ingest.py process

# Check status
python ingest.py status
```

## Whisper API Documentation

### Key Details
- **Pricing**: $0.006/minute of audio
- **File Size Limit**: 25MB per file (but community reports issues with files >10MB)
- **Supported Formats**: mp3, mp4, mpeg, mpga, m4a, wav, webm
- **Model**: Currently uses large-v3 model
- **Features**: Multilingual transcription, translation, language identification

### Implementation Notes
1. **Chunking Strategy**: Keep chunks under 10MB to avoid reported issues
2. **Audio Format**: Convert to MP3 @ 128kbps for consistent size calculation
3. **Rate Limits**: Implement exponential backoff for API calls
4. **Error Handling**: Save failed chunks for retry

### Cost Estimation
- 1 hour podcast = $0.36
- 100 hours of content = $36
- Average 30min YouTube video = $0.18

## Dependencies

```txt
# Existing
lightrag
openai>=1.0.0
python-dotenv

# New (minimal)
yt-dlp>=2023.12.0      # YouTube/video downloading
feedparser>=6.0.0      # RSS feed parsing
pydub>=0.25.0         # Audio manipulation
ffmpeg-python>=0.2.0  # Audio extraction
requests>=2.31.0      # HTTP downloads
```

## Phased Implementation

### Phase 1: RSS/Podcast MVP ✅
1. Simple RSS feed parser ✅
2. Direct MP3 download from podcast URLs ✅
3. Basic chunking for Whisper ✅
4. Transcription to text files ✅
5. Automatic load into LightRAG ✅

### Phase 2: YouTube Support ✅
1. Add yt-dlp integration ✅
2. Video to audio extraction ✅
3. Metadata preservation ✅

### Phase 3: Robustness
1. Retry logic for failed downloads/transcriptions
2. Progress tracking
3. Concurrent processing

### Phase 4: Enhanced Features
1. Web UI for monitoring
2. Automatic RSS feed checking
3. Duplicate detection

## Benefits

1. **Simple**: Just directories and files, no databases
2. **Resumable**: Move files between directories to track state
3. **Debuggable**: See exactly what's happening by looking at folders
4. **Extensible**: Add new content types by adding downloaders