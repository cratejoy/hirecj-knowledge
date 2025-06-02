#!/usr/bin/env python
"""
Simple content ingestion pipeline for RSS/podcasts -> Whisper -> LightRAG
Following North Star principles: Simple, no cruft, elegant
"""
import sys
import json
import hashlib
import shutil
import asyncio
import subprocess
import logging
import os
import re
import unicodedata
import time
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

import feedparser
import requests
import yt_dlp
from openai import OpenAI
from pydub import AudioSegment
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging based on environment variable
if os.getenv('LIGHTRAG_DEBUG') == '1':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('lightrag_debug.log'),
            logging.StreamHandler()
        ]
    )
    logging.getLogger('lightrag').setLevel(logging.DEBUG)
    logging.getLogger('openai').setLevel(logging.INFO)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    print("🐛 Debug logging enabled - check lightrag_debug.log")


class ContentProcessor:
    def __init__(self, base_dir: Path = Path("content")):
        self.base_dir = base_dir
        self.ensure_directories()
        self.openai = OpenAI()
    
    def _sanitize_for_filename(self, text: str, max_length: int = 50) -> str:
        """Sanitize text to be safe for use in filenames
        
        Args:
            text: The text to sanitize
            max_length: Maximum length of the output (default 50)
            
        Returns:
            A filesystem-safe string
        """
        # Remove or replace unsafe characters
        # First, normalize unicode characters
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ascii', 'ignore').decode('ascii')
        
        # Replace spaces with underscores
        text = text.replace(' ', '_')
        
        # Remove any character that isn't alphanumeric, underscore, or dash
        text = re.sub(r'[^a-zA-Z0-9_-]', '', text)
        
        # Remove multiple underscores/dashes
        text = re.sub(r'[_-]+', '_', text)
        
        # Trim to max length
        if len(text) > max_length:
            text = text[:max_length].rstrip('_-')
        
        # Ensure it's not empty
        if not text:
            text = 'Unknown'
            
        return text
    
    def ensure_directories(self):
        """Create all required directories"""
        dirs = ['inbox', 'downloading', 'downloaded', 'audio', 
                'chunks', 'transcribing', 'transcripts', 'loaded', 'failed']
        for d in dirs:
            (self.base_dir / d).mkdir(parents=True, exist_ok=True)
    
    def add_url(self, url: str, limit: int = None):
        """Add URL to inbox - user-friendly interface
        
        Args:
            url: The URL to add
            limit: For RSS feeds, max number of episodes to process (default: all)
        """
        # Create unique ID from URL
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        
        # Determine content type
        if 'youtube.com' in url or 'youtu.be' in url:
            prefix = 'youtube'
        elif any(x in url for x in ['.rss', '/rss', 'feed', 'podcast', 'libsyn']):
            prefix = 'rss'
        else:
            prefix = 'content'
        
        filename = f"{prefix}_{url_hash}.json"
        filepath = self.base_dir / 'inbox' / filename
        
        # For RSS feeds, don't check for duplicates at feed level
        # Episodes are checked individually during processing
        if prefix != 'rss':
            # Check if already exists in any directory
            existing_locations = []
            for dir_name in ['inbox', 'downloading', 'downloaded', 'transcripts', 'loaded']:
                check_path = self.base_dir / dir_name / filename
                if dir_name in ['transcripts', 'loaded']:
                    check_path = self.base_dir / dir_name / f"{prefix}_{url_hash}.txt"
                elif dir_name in ['downloaded', 'downloading']:
                    check_path = self.base_dir / dir_name / f"{prefix}_{url_hash}"
                    
                if check_path.exists():
                    existing_locations.append(dir_name)
            
            if existing_locations:
                print(f"⚠️  URL already exists in: {', '.join(existing_locations)}")
                print(f"   {url}")
                return
        else:
            # For RSS, just check if it's already in inbox
            if filepath.exists():
                print(f"⚠️  RSS feed already in inbox, will check for new episodes on process")
                return
        
        # Check failed directory
        failed_path = self.base_dir / 'failed' / f"{prefix}_{url_hash}.error"
        if failed_path.exists():
            print(f"⚠️  URL previously failed. Delete {failed_path} to retry.")
            return
        
        # Store as JSON for richer metadata
        data = {
            'url': url,
            'added_at': datetime.now().isoformat(),
            'type': prefix,
            'limit': limit  # How many episodes to process
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        # For RSS feeds, immediately atomize into episodes
        if prefix == 'rss':
            created, skipped, total = self._atomize_rss_feed(url, f"{prefix}_{url_hash}", limit)
            print(f"✓ Added RSS feed: {url}")
            print(f"  📊 {created} new episodes added to inbox")
            if skipped > 0:
                print(f"  ⏭️  {skipped} episodes already processed")
            if limit and limit < total:
                print(f"  📌 Limited to {limit} episodes (out of {total} total)")
            # Delete the RSS file since we've atomized it
            filepath.unlink()
        else:
            print(f"✓ Added {prefix} content: {url}")
    
    def process_inbox(self):
        """Process all items in inbox and resume any incomplete work"""
        import gc
        import tempfile
        
        # First, check for stuck documents in LightRAG
        # TEMP: Disabled due to entity extraction errors blocking processing
        # self._check_pending_lightrag_docs()
        
        # Check for abandoned chunks that need transcribing
        chunks_dirs = list((self.base_dir / 'chunks').glob('*'))
        if chunks_dirs:
            print(f"📂 Found {len(chunks_dirs)} item(s) with chunks to transcribe")
            for chunks_dir in chunks_dirs:
                try:
                    item_id = chunks_dir.name
                    print(f"\n🔄 Resuming: Transcribing chunks for {item_id}...")
                    
                    # Look for metadata in downloaded or audio directory
                    metadata = {}
                    metadata_paths = [
                        self.base_dir / 'downloaded' / item_id / 'metadata.json',
                        self.base_dir / 'audio' / item_id / 'metadata.json'
                    ]
                    
                    for metadata_path in metadata_paths:
                        if metadata_path.exists():
                            with open(metadata_path) as f:
                                metadata = json.load(f)
                            break
                    
                    # Move to transcribing directory
                    transcribing_dir = self.base_dir / 'transcribing' / item_id
                    shutil.move(str(chunks_dir), str(transcribing_dir))
                    
                    # Transcribe chunks
                    chunks = sorted(transcribing_dir.glob('chunk_*.mp3'))
                    print(f"  🎙️ Found {len(chunks)} chunks to transcribe")
                    
                    transcripts = []
                    for i, chunk in enumerate(chunks):
                        print(f"  📝 Transcribing chunk {i+1}/{len(chunks)}: {chunk.name}")
                        text = self._transcribe_chunk(chunk)
                        print(f"     ✅ Received {len(text)} characters")
                        transcripts.append(text)
                    
                    # Save transcript
                    full_transcript = '\n'.join(transcripts)
                    print(f"\n  📄 Total transcript length: {len(full_transcript):,} characters")
                    
                    enriched = f"""Title: {metadata.get('title', 'Unknown')}
Feed: {metadata.get('feed_title', 'Unknown')}
URL: {metadata.get('url', 'Unknown')}
Date: {metadata.get('download_date', 'Unknown')}

{full_transcript}
"""
                    
                    transcript_file = self.base_dir / 'transcripts' / f"{item_id}.txt"
                    transcript_file.write_text(enriched, encoding='utf-8')
                    print(f"  💾 Saved transcript to: {transcript_file}")
                    
                    # Clean up
                    shutil.rmtree(transcribing_dir)
                    print(f"  🧹 Cleaned up chunks")
                    
                    # Force garbage collection
                    gc.collect()
                    
                except Exception as e:
                    print(f"  ❌ Failed to transcribe {item_id}: {str(e)}")
                    # Move back to chunks to retry later
                    if transcribing_dir.exists():
                        shutil.move(str(transcribing_dir), str(chunks_dir))
        
        # Then check for transcripts that need loading
        transcripts_to_load = list((self.base_dir / 'transcripts').glob('*.txt'))
        if transcripts_to_load:
            print(f"📋 Found {len(transcripts_to_load)} transcript(s) to load into LightRAG")
            for transcript_file in transcripts_to_load:
                try:
                    filename = transcript_file.stem
                    print(f"\n🔄 Resuming: Loading {filename} into LightRAG...")
                    with open(transcript_file, encoding='utf-8') as f:
                        content = f.read()
                    
                    # Try to extract metadata from transcript for better source attribution
                    source_path = None
                    lines = content.split('\n')
                    title = ""
                    feed = ""
                    url = ""
                    
                    # First, try to extract from transcript content
                    for line in lines[:10]:  # Check first 10 lines for metadata
                        if line.startswith("Title: "):
                            title = line[7:].strip()[:50]
                        elif line.startswith("Feed: "):
                            feed = line[6:].strip()[:30]
                        elif line.startswith("URL: "):
                            url = line[5:].strip()
                    
                    # If we have metadata from content, use it
                    if feed and title:
                        source_path = f"{feed} - {title}"
                        if url:
                            source_path = f"{source_path} [{url}]"
                    # Otherwise, try to parse meaningful filename (new format)
                    elif filename.count('_') >= 2:
                        # Format: EpisodeTitle_PodcastName_hash
                        parts = filename.split('_')
                        if len(parts) >= 3:
                            # Everything except last two parts is episode title
                            episode_title = '_'.join(parts[:-2]).replace('_', ' ')
                            podcast_name = parts[-2].replace('_', ' ')
                            source_path = f"{podcast_name} - {episode_title}"
                            print(f"  📎 Extracted from filename: {source_path}")
                    
                    self._load_to_lightrag(content, filename, source_path)
                    print(f"  ✅ Successfully loaded into knowledge graph!")
                    
                    # Move to loaded directory
                    loaded_file = self.base_dir / 'loaded' / transcript_file.name
                    shutil.move(str(transcript_file), str(loaded_file))
                    print(f"  📁 Moved to loaded directory")
                    
                except Exception as e:
                    print(f"  ❌ Failed to load {transcript_file.stem}: {str(e)}")
                    # Don't move to failed - leave in transcripts to retry
        
        # Now process inbox items
        inbox = self.base_dir / 'inbox'
        items = list(inbox.glob('*.json'))
        
        if not items and not transcripts_to_load and not chunks_dirs:
            print("No new items to process")
            # Don't return - let it continue to check other things
        
        if items:
            # Deduplicate by URL
            seen_urls = set()
            unique_items = []
            
            for item_file in items:
                try:
                    with open(item_file) as f:
                        data = json.load(f)
                        url = data['url']
                        
                    if url not in seen_urls:
                        seen_urls.add(url)
                        unique_items.append(item_file)
                    else:
                        print(f"⚠️  Skipping duplicate: {item_file.name} (same URL already queued)")
                except Exception as e:
                    print(f"⚠️  Error reading {item_file}: {e}")
                    unique_items.append(item_file)  # Process anyway
            
            print(f"\n📥 Processing {len(unique_items)} new item(s)...")
            
            for item_file in unique_items:
                try:
                    print(f"\n📥 Processing: {item_file.stem}")
                    self.process_item(item_file)
                    print(f"✓ Completed: {item_file.stem}")
                except Exception as e:
                    print(f"✗ Failed: {item_file.stem} - {str(e)}")
                    # Check if it's in downloading (RSS might be partial)
                    downloading_file = self.base_dir / 'downloading' / item_file.name
                    if downloading_file.exists():
                        # Move to failed since we don't know the state
                        self._move_to_failed(downloading_file, str(e))
                    else:
                        self._move_to_failed(item_file, str(e))
    
    def process_item(self, item_file: Path):
        """Process single item through all stages"""
        with open(item_file) as f:
            data = json.load(f)
        
        url = data['url']
        content_type = data['type']
        item_id = item_file.stem
        
        # Move to downloading
        item_file.rename(self.base_dir / 'downloading' / item_file.name)
        
        if content_type == 'rss':
            # Atomize RSS feed into individual episode items
            limit = data.get('limit')
            self._atomize_rss_feed(url, item_id, limit)
            # Delete RSS file - its job is done
            downloading_file = self.base_dir / 'downloading' / item_file.name
            if downloading_file.exists():
                downloading_file.unlink()
        elif content_type == 'youtube':
            self._process_youtube(url, item_id)
            # YouTube is single item, safe to delete
            downloading_file = self.base_dir / 'downloading' / item_file.name
            if downloading_file.exists():
                downloading_file.unlink()
        elif content_type == 'episode':
            self._process_episode(data, item_id)
            # Episode is single item, safe to delete
            downloading_file = self.base_dir / 'downloading' / item_file.name
            if downloading_file.exists():
                downloading_file.unlink()
        else:
            raise NotImplementedError(f"Type {content_type} not yet supported")
    
    def _atomize_rss_feed(self, rss_url: str, feed_id: str, limit: int = None):
        """Convert RSS feed into individual episode work items"""
        print(f"  📡 Parsing RSS feed: {rss_url}")
        feed = feedparser.parse(rss_url)
        
        feed_title = feed.feed.get('title', 'Unknown Feed')
        print(f"  📰 Feed title: {feed_title}")
        
        # Find episodes with audio
        audio_episodes = []
        for i, entry in enumerate(feed.entries):
            audio_url = None
            
            # Check enclosures first (most common for podcasts)
            if hasattr(entry, 'enclosures'):
                for enc in entry.enclosures:
                    if enc.get('type', '').startswith('audio/'):
                        audio_url = enc.get('href', enc.get('url'))
                        break
            
            # Also check links
            if not audio_url and hasattr(entry, 'links'):
                for link in entry.links:
                    if link.get('type', '').startswith('audio/'):
                        audio_url = link['href']
                        break
            
            if audio_url:
                audio_episodes.append({
                    'url': audio_url,
                    'title': entry.get('title', 'Unknown Episode'),
                    'published': entry.get('published', None),
                    'description': entry.get('description', '')[:500],  # First 500 chars
                    'index': i
                })
        
        if not audio_episodes:
            print(f"  ❌ No audio episodes found in RSS feed")
            return
        
        print(f"  ✅ Found {len(audio_episodes)} audio episode(s)")
        
        # Apply limit if specified
        episodes_to_create = audio_episodes[:limit] if limit else audio_episodes
        
        # Create individual episode items
        created = 0
        skipped = 0
        
        for episode in episodes_to_create:
            # Create meaningful ID for this episode
            # Sanitize feed title and episode title for filename
            feed_name_clean = self._sanitize_for_filename(feed_title, max_length=30)
            episode_title_clean = self._sanitize_for_filename(episode['title'], max_length=50)
            
            # Add short hash for uniqueness (in case of duplicate titles)
            episode_hash = hashlib.md5(episode['url'].encode()).hexdigest()[:6]
            
            # Format: EpisodeTitle_PodcastName_hash
            episode_id = f"{episode_title_clean}_{feed_name_clean}_{episode_hash}"
            
            # Check if already exists anywhere
            if self._is_episode_processed(episode_id):
                skipped += 1
                print(f"     ⏭️  Skipping existing: {episode_title_clean}")
                continue
            
            # Check if episode item already exists in inbox
            episode_file = self.base_dir / 'inbox' / f"{episode_id}.json"
            if episode_file.exists():
                skipped += 1
                continue
            
            # Create episode work item
            episode_data = {
                'url': episode['url'],
                'type': 'episode',
                'title': episode['title'],
                'feed_title': feed_title,
                'feed_url': rss_url,
                'description': episode['description'],
                'published': episode['published'],
                'added_at': datetime.now().isoformat()
            }
            
            with open(episode_file, 'w') as f:
                json.dump(episode_data, f, indent=2)
            created += 1
            print(f"     ✅ Created: {episode_id}")
        
        print(f"  📦 Created {created} episode items, skipped {skipped} existing")
        
        if limit and limit < len(audio_episodes):
            print(f"  📌 Limited to {limit} episodes (out of {len(audio_episodes)} total)")
        
        return created, skipped, len(audio_episodes)
    
    def _process_rss(self, rss_url: str, feed_id: str, limit: int = None):
        """[DEPRECATED - Now using atomic episode processing]
        Process RSS feed - download and process multiple episodes
        
        Returns:
            'completed' if all episodes processed (or hit limit)
            'partial' if some episodes remain unprocessed
        """
        print(f"  📡 Parsing RSS feed: {rss_url}")
        feed = feedparser.parse(rss_url)
        
        feed_title = feed.feed.get('title', 'Unknown Feed')
        print(f"  📰 Feed title: {feed_title}")
        print(f"  📊 Total entries: {len(feed.entries)}")
        
        # Track processing stats
        total_episodes = 0
        processed_episodes = 0
        failed_episodes = 0
        skipped_episodes = 0
        
        # Find episodes with audio
        audio_episodes = []
        
        for i, entry in enumerate(feed.entries):
            audio_url = None
            
            # Check enclosures first (most common for podcasts)
            if hasattr(entry, 'enclosures'):
                for enc in entry.enclosures:
                    if enc.get('type', '').startswith('audio/'):
                        audio_url = enc.get('href', enc.get('url'))
                        break
            
            # Also check links
            if not audio_url and hasattr(entry, 'links'):
                for link in entry.links:
                    if link.get('type', '').startswith('audio/'):
                        audio_url = link['href']
                        break
            
            if audio_url:
                audio_episodes.append({
                    'url': audio_url,
                    'title': entry.get('title', 'Unknown Episode'),
                    'published': entry.get('published_parsed', None),
                    'index': i
                })
        
        if not audio_episodes:
            print(f"  ❌ No audio episodes found in RSS feed")
            raise ValueError("No audio episodes found in RSS feed")
        
        print(f"  ✅ Found {len(audio_episodes)} audio episode(s)")
        
        total_episodes = len(audio_episodes)
        
        # Apply limit to processing
        episodes_to_process = audio_episodes
        if limit and limit < len(audio_episodes):
            episodes_to_process = audio_episodes[:limit]
            print(f"  📌 Limited to {limit} episode(s) as requested (out of {total_episodes} total)")
        
        # Process each episode
        for ep_num, episode in enumerate(episodes_to_process, 1):
            print(f"\n  {'='*60}")
            print(f"  📻 Episode {ep_num}/{len(episodes_to_process)}: {episode['title'][:60]}...")
            
            # Create unique ID for this episode
            episode_hash = hashlib.md5(episode['url'].encode()).hexdigest()[:8]
            episode_id = f"{feed_id}_ep{episode_hash}"
            
            # Check if already processed
            if self._is_episode_processed(episode_id):
                print(f"  ⏭️  Skipping - already processed")
                skipped_episodes += 1
                continue
            
            try:
                # Download and process this episode
                self._process_episode_content(episode, episode_id, feed_title, rss_url)
                processed_episodes += 1
                
            except Exception as e:
                print(f"  ❌ Failed to process episode: {str(e)}")
                failed_episodes += 1
                # Continue with next episode instead of failing entire feed
                continue
        
        # Summary and return status
        print(f"\n  📊 RSS Feed Processing Summary:")
        print(f"     Total episodes in feed: {total_episodes}")
        print(f"     Episodes attempted: {len(episodes_to_process)}")
        print(f"     Processed: {processed_episodes}")
        print(f"     Skipped (already done): {skipped_episodes}")
        print(f"     Failed: {failed_episodes}")
        
        # Determine completion status
        # If we processed all episodes in the feed, or hit our limit, we're "complete"
        # Only return "partial" if we were interrupted before hitting our target
        episodes_done = processed_episodes + skipped_episodes + failed_episodes
        target_episodes = len(episodes_to_process)
        
        if episodes_done >= target_episodes:
            # We processed everything we intended to
            if limit and limit < total_episodes:
                print(f"  ✅ Completed processing limit of {limit} episodes")
                # Still mark as partial so we can resume for more episodes
                return 'partial'
            else:
                return 'completed'
        else:
            # We were interrupted
            print(f"  ⚠️  Only processed {episodes_done}/{target_episodes} episodes")
            return 'partial'
    
    def _is_episode_processed(self, episode_id: str) -> bool:
        """Check if episode is already processed"""
        # Check in various directories
        checks = [
            self.base_dir / 'downloaded' / episode_id,
            self.base_dir / 'transcripts' / f"{episode_id}.txt",
            self.base_dir / 'loaded' / f"{episode_id}.txt"
        ]
        
        return any(path.exists() for path in checks)
    
    def _process_episode(self, data: dict, item_id: str):
        """Process an atomic episode item"""
        # Extract episode data
        episode = {
            'url': data['url'],
            'title': data.get('title', 'Unknown Episode')
        }
        feed_title = data.get('feed_title', 'Unknown Feed')
        feed_url = data.get('feed_url', '')
        
        print(f"  📻 Processing episode: {episode['title'][:60]}...")
        
        # Process using existing logic
        self._process_episode_content(episode, item_id, feed_title, feed_url)
    
    def _process_episode_content(self, episode: dict, episode_id: str, feed_title: str, feed_url: str):
        """Process a single episode's content"""
        # Download audio
        download_dir = self.base_dir / 'downloaded' / episode_id
        download_dir.mkdir(exist_ok=True)
        
        audio_file = download_dir / 'audio.mp3'
        print(f"  💾 Downloading: {episode['url']}")
        
        response = requests.get(episode['url'], stream=True)
        response.raise_for_status()
        
        # Get total size if available
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(audio_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\r  📥 Progress: {downloaded:,} / {total_size:,} bytes ({percent:.1f}%)", end='', flush=True)
        
        print(f"\n  ✅ Download complete! File size: {audio_file.stat().st_size:,} bytes")
        
        # Save metadata
        metadata = {
            'url': feed_url,
            'audio_url': episode['url'],
            'title': episode['title'],
            'feed_title': feed_title,
            'download_date': datetime.now().isoformat()
        }
        
        with open(download_dir / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Copy to audio dir
        audio_dir = self.base_dir / 'audio' / episode_id
        audio_dir.mkdir(exist_ok=True)
        shutil.copy2(audio_file, audio_dir / 'audio.mp3')
        
        # Process audio through chunking and transcription
        self._process_audio(audio_dir / 'audio.mp3', episode_id, metadata)
    
    def _process_youtube(self, youtube_url: str, video_id: str):
        """Process YouTube video - download and extract audio"""
        print(f"  🎥 Processing YouTube video: {youtube_url}")
        
        # Download video
        download_dir = self.base_dir / 'downloaded' / video_id
        download_dir.mkdir(exist_ok=True)
        
        print(f"  💾 Downloading video...")
        
        ydl_opts = {
            'outtmpl': str(download_dir / 'video.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            # Get best quality audio
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=True)
                
                # Get video metadata
                title = info.get('title', 'Unknown Video')
                channel = info.get('uploader', 'Unknown Channel')
                upload_date = info.get('upload_date', 'Unknown')
                duration = info.get('duration', 0)
                
                print(f"  📺 Title: {title}")
                print(f"  👤 Channel: {channel}")
                print(f"  📅 Upload date: {upload_date}")
                print(f"  ⏱️  Duration: {duration//60}:{duration%60:02d}")
                
                # Save metadata
                metadata = {
                    'url': youtube_url,
                    'title': title,
                    'channel': channel,
                    'upload_date': upload_date,
                    'duration': duration,
                    'download_date': datetime.now().isoformat()
                }
                
                with open(download_dir / 'metadata.json', 'w') as f:
                    json.dump(metadata, f, indent=2)
                
        except Exception as e:
            print(f"  ❌ Failed to download video: {str(e)}")
            raise
        
        # Find the downloaded audio file
        audio_files = list(download_dir.glob('*.mp3'))
        if not audio_files:
            # If no mp3, look for the video file and extract audio
            video_files = list(download_dir.glob('video.*'))
            if not video_files:
                raise Exception("No video or audio file found after download")
            
            video_file = video_files[0]
            print(f"  🎵 Extracting audio from video...")
            
            audio_file = download_dir / 'audio.mp3'
            self._extract_audio_from_video(video_file, audio_file)
        else:
            audio_file = audio_files[0]
            # Rename to standard name
            new_audio_file = download_dir / 'audio.mp3'
            audio_file.rename(new_audio_file)
            audio_file = new_audio_file
        
        print(f"  ✅ Audio ready: {audio_file.stat().st_size:,} bytes")
        
        # Copy to audio directory
        audio_dir = self.base_dir / 'audio' / video_id
        audio_dir.mkdir(exist_ok=True)
        shutil.copy2(audio_file, audio_dir / 'audio.mp3')
        
        # Process audio through chunking and transcription
        self._process_audio(audio_dir / 'audio.mp3', video_id, metadata)
    
    def _extract_audio_from_video(self, video_path: Path, audio_path: Path):
        """Extract audio from video using ffmpeg"""
        cmd = [
            'ffmpeg', '-i', str(video_path),
            '-vn',  # No video
            '-acodec', 'mp3',
            '-ab', '192k',  # Audio bitrate
            '-ar', '44100',  # Sample rate
            '-y',  # Overwrite output
            str(audio_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"ffmpeg failed: {result.stderr}")
    
    def _process_audio(self, audio_file: Path, item_id: str, metadata: dict):
        """Chunk and transcribe audio"""
        # Chunk audio
        print(f"\n  🔪 Chunking audio file: {audio_file}")
        print(f"  📏 File size: {audio_file.stat().st_size:,} bytes ({audio_file.stat().st_size / 1024 / 1024:.1f} MB)")
        
        chunks_dir = self.base_dir / 'chunks' / item_id
        chunks_dir.mkdir(exist_ok=True)
        
        chunks = self._chunk_audio(audio_file, chunks_dir)
        print(f"  ✅ Created {len(chunks)} chunks")
        for i, chunk in enumerate(chunks):
            print(f"     - Chunk {i+1}: {chunk.name} ({chunk.stat().st_size:,} bytes)")
        
        # Transcribe
        print(f"\n  🎙️ Starting transcription...")
        shutil.move(str(chunks_dir), str(self.base_dir / 'transcribing' / item_id))
        transcribing_dir = self.base_dir / 'transcribing' / item_id
        
        transcripts = []
        for i, chunk in enumerate(sorted(transcribing_dir.glob('chunk_*.mp3'))):
            print(f"  📝 Transcribing chunk {i+1}/{len(chunks)}: {chunk.name}")
            print(f"     Sending to Whisper API...")
            text = self._transcribe_chunk(chunk)
            print(f"     ✅ Received {len(text)} characters")
            print(f"     Preview: {text[:100]}..." if len(text) > 100 else f"     Text: {text}")
            transcripts.append(text)
        
        # Save transcript
        full_transcript = '\n'.join(transcripts)
        print(f"\n  📄 Total transcript length: {len(full_transcript):,} characters")
        
        enriched = f"""Title: {metadata.get('title', 'Unknown')}
Feed: {metadata.get('feed_title', 'Unknown')}
URL: {metadata.get('url', 'Unknown')}
Date: {metadata.get('download_date', 'Unknown')}

{full_transcript}
"""
        
        transcript_file = self.base_dir / 'transcripts' / f"{item_id}.txt"
        transcript_file.write_text(enriched, encoding='utf-8')
        print(f"  💾 Saved transcript to: {transcript_file}")
        
        # Load into LightRAG with meaningful source attribution
        print(f"\n  🧠 Loading into LightRAG...")
        
        # Create a meaningful file path for source attribution
        # Clean up title and feed name for file path
        import re
        title_clean = re.sub(r'[^\w\s-]', '', metadata.get('title', 'Unknown')).strip()[:50]
        feed_clean = re.sub(r'[^\w\s-]', '', metadata.get('feed_title', 'Unknown Feed')).strip()[:30]
        
        # Format: "Podcast Name - Episode Title [URL]"
        source_path = f"{feed_clean} - {title_clean}"
        if metadata.get('url'):
            source_path = f"{source_path} [{metadata.get('url')}]"
        
        self._load_to_lightrag(enriched, item_id, source_path)
        print(f"  ✅ Successfully loaded into knowledge graph!")
        
        # Move to loaded directory
        loaded_file = self.base_dir / 'loaded' / f"{item_id}.txt"
        shutil.move(str(transcript_file), str(loaded_file))
        print(f"  📁 Moved to loaded directory")
        
        # Cleanup
        print(f"\n  🧹 Cleaning up temporary files...")
        shutil.rmtree(transcribing_dir)
        print(f"  ✅ Pipeline complete for {item_id}!")
    
    def _chunk_audio(self, audio_path: Path, output_dir: Path, max_size_mb: int = 10):
        """Split audio into chunks under 10MB for Whisper API"""
        import gc
        import tempfile
        
        print(f"     Loading audio with pydub...")
        
        # Set pydub temp directory to ensure cleanup
        original_tempdir = tempfile.gettempdir()
        temp_dir = tempfile.mkdtemp(prefix="pydub_")
        tempfile.tempdir = temp_dir
        
        try:
            audio = AudioSegment.from_mp3(audio_path)
            
            duration_seconds = len(audio) / 1000
            print(f"     Audio duration: {duration_seconds:.1f} seconds ({duration_seconds/60:.1f} minutes)")
            
            # Calculate chunk duration for ~9MB chunks (safety margin)
            bitrate = 128  # kbps
            max_duration_ms = (max_size_mb * 8 * 1024) / bitrate * 1000
            chunk_duration_minutes = max_duration_ms / 1000 / 60
            print(f"     Max chunk duration: {chunk_duration_minutes:.1f} minutes per chunk")
            
            chunks = []
            for i, start in enumerate(range(0, len(audio), int(max_duration_ms))):
                chunk = audio[start:start + int(max_duration_ms)]
                chunk_path = output_dir / f"chunk_{i:03d}.mp3"
                print(f"     Creating chunk {i+1}: {start/1000:.1f}s - {(start + len(chunk))/1000:.1f}s")
                
                # Export and immediately close any file handles
                chunk.export(chunk_path, format="mp3", bitrate="128k")
                
                # Explicitly delete chunk to free memory
                del chunk
                
                chunks.append(chunk_path)
            
            # Explicitly delete audio object
            del audio
            
        finally:
            # Restore original temp directory
            tempfile.tempdir = original_tempdir
            
            # Clean up temp directory
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass
            
            # Force garbage collection to clean up any remaining references
            gc.collect()
        
        return chunks
    
    def _transcribe_chunk(self, audio_path: Path) -> str:
        """Transcribe audio chunk using Whisper API"""
        with open(audio_path, 'rb') as f:
            response = self.openai.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="text"
            )
        return response
    
    def _load_to_lightrag(self, content: str, item_id: str = None, source_path: str = None):
        """Load transcript into LightRAG with optional source path for better citations
        
        IMPORTANT: Always pass a meaningful source_path to ensure proper source attribution.
        Without it, LightRAG will show cryptic IDs like [KG] rss_abc123_ep456.txt
        See docs/lightrag-source-attribution.md for details.
        """
        try:
            from lightrag import LightRAG
            from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
            from lightrag.kg.shared_storage import initialize_pipeline_status
            from lightrag.base import DocStatus
            
            rag = LightRAG(
                working_dir="./lightrag_transcripts_db",
                embedding_func=openai_embed,
                llm_model_func=gpt_4o_mini_complete,
            )
            
            # Initialize storages and pipeline status using asyncio
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(rag.initialize_storages())
                loop.run_until_complete(initialize_pipeline_status())
            finally:
                loop.close()
            
            # Use synchronous insert method with meaningful source path
            if source_path:
                # Use the provided source path for better citations
                rag.insert(content, file_paths=[source_path])
            elif item_id:
                # Fallback to item_id if no source path provided
                rag.insert(content, file_paths=[f"{item_id}.txt"])
            else:
                rag.insert(content)
                
            # The synchronous insert should complete processing before returning
            # But let's check to be sure
            import time
            time.sleep(1)
            
            # Check processing status
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                status_counts = loop.run_until_complete(rag.get_processing_status())
                pending = status_counts.get(DocStatus.PENDING, 0)
                processing = status_counts.get(DocStatus.PROCESSING, 0)
                if pending > 0 or processing > 0:
                    print(f"  ⏳ Documents still being processed: {pending} pending, {processing} processing")
            finally:
                loop.close()
                
        except Exception as e:
            # If it fails with history_messages, it might already be loaded
            if 'history_messages' in str(e):
                print(f"  ⚠️  Note: May already be in LightRAG (got '{e}')")
                # Don't raise - treat as success
            elif 'Entity extraction error' in str(e) or 'invalid entity type' in str(e):
                print(f"  ⚠️  LightRAG entity extraction error, document saved but may have incomplete entities")
                # Don't raise - document is saved, just entity extraction failed
            else:
                raise
    
    def _check_pending_lightrag_docs(self):
        """Check for and reprocess any pending documents in LightRAG"""
        try:
            from lightrag import LightRAG
            from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
            from lightrag.base import DocStatus
            from lightrag.kg.shared_storage import initialize_pipeline_status
            
            print("🔍 Checking for pending documents in LightRAG...")
            
            # Initialize LightRAG to check doc status
            rag = LightRAG(
                working_dir="./lightrag_transcripts_db",
                embedding_func=openai_embed,
                llm_model_func=gpt_4o_mini_complete,
            )
            
            # Use async to check status
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Initialize storages and pipeline status
                loop.run_until_complete(rag.initialize_storages())
                loop.run_until_complete(initialize_pipeline_status())
                
                # Get status counts
                status_counts = loop.run_until_complete(rag.get_processing_status())
                pending_count = status_counts.get(DocStatus.PENDING, 0)
                
                if pending_count > 0:
                    print(f"🔄 Found {pending_count} pending document(s) in LightRAG")
                    
                    # Get pending documents
                    pending_docs = loop.run_until_complete(rag.doc_status.get_docs_by_status(DocStatus.PENDING))
                    
                    for doc_id, doc_info in pending_docs.items():
                        try:
                            print(f"  📄 Reprocessing pending document: {doc_id}")
                            
                            # The content is stored in doc_info
                            content = doc_info.content if hasattr(doc_info, 'content') else str(doc_info.get('content', ''))
                            
                            if content:
                                # Extract a reasonable item_id from file_path or doc_id
                                file_path = doc_info.file_path if hasattr(doc_info, 'file_path') else doc_info.get('file_path', f"{doc_id}.txt")
                                if file_path == "unknown_source":
                                    file_path = f"{doc_id.replace('doc-', '')[:8]}.txt"
                                
                                # Re-insert to trigger processing
                                loop.run_until_complete(rag.ainsert(content, file_paths=[file_path]))
                                print(f"    ✅ Successfully reprocessed with source: {file_path}")
                            else:
                                print(f"    ⚠️  No content found for document")
                                
                        except Exception as e:
                            error_msg = str(e)
                            if 'Entity extraction error' in error_msg or 'invalid entity type' in error_msg:
                                print(f"    ⚠️  Entity extraction error - document loaded but entities incomplete")
                            else:
                                print(f"    ❌ Failed to reprocess: {error_msg[:200]}")
                else:
                    print("  ✅ No pending documents found")
                            
            finally:
                loop.close()
                
        except Exception as e:
            # Log the error but continue
            print(f"  ⚠️  Could not check pending docs: {str(e)}")
    
    def status(self, interval=None):
        """Show pipeline status with counts at each stage
        
        Args:
            interval: If specified, refresh status every interval seconds
        """
        if interval:
            print(f"📊 Monitoring pipeline status (updating every {interval}s, press Ctrl+C to stop)\n")
            try:
                while True:
                    # Clear screen (works on both Unix and Windows)
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print(f"📊 Pipeline Status Monitor (refreshing every {interval}s)")
                    print(f"🕐 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print("Press Ctrl+C to stop\n")
                    self._print_status()
                    time.sleep(interval)
            except KeyboardInterrupt:
                print("\n\n✋ Monitoring stopped")
                return
        else:
            self._print_status()
    
    def _print_status(self):
        """Print the actual status information"""
        print("🚀 Content Pipeline")
        print("=" * 60)
        
        # Count files at each stage
        stages = [
            ("📥 Inbox", self.base_dir / "inbox", "*.json"),
            ("⬇️  Downloading", self.base_dir / "downloading", "*"),
            ("💾 Downloaded", self.base_dir / "downloaded", "*"),
            ("🎵 Audio", self.base_dir / "audio", "*"),
            ("🔪 Chunks", self.base_dir / "chunks", "*"),
            ("🎙️  Transcribing", self.base_dir / "transcribing", "*"),
            ("📝 Transcripts", self.base_dir / "transcripts", "*.txt"),
            ("✅ Loaded", self.base_dir / "loaded", "*.txt"),
            ("❌ Failed", self.base_dir / "failed", "*.error"),
        ]
        
        total_items = 0
        for name, path, pattern in stages:
            if path.exists():
                items = list(path.glob(pattern))
                # For directories with subdirs, count the subdirs not files
                if name in ["⬇️  Downloading", "💾 Downloaded", "🎵 Audio", "🔪 Chunks", "🎙️  Transcribing"]:
                    items = [item for item in items if item.is_dir()]
                count = len(items)
                total_items += count
                
                if count > 0:
                    print(f"{name:<20} {count:>5} items")
                    # Show first few items for context
                    for item in items[:3]:
                        print(f"  └─ {item.name}")
                    if count > 3:
                        print(f"  └─ ... and {count - 3} more")
            else:
                print(f"{name:<20}     0 items")
        
        print("-" * 60)
        print(f"{'Total in Pipeline:':<20} {total_items:>5} items")
        
        # Check LightRAG status
        print("\n🧠 LightRAG Database Status")
        print("=" * 60)
        
        try:
            from lightrag import LightRAG
            from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
            from lightrag.base import DocStatus
            from lightrag.kg.shared_storage import initialize_pipeline_status
            
            # Initialize LightRAG
            rag = LightRAG(
                working_dir="./lightrag_transcripts_db",
                embedding_func=openai_embed,
                llm_model_func=gpt_4o_mini_complete,
            )
            
            # Use async to get actual counts
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Initialize storages and pipeline status
                loop.run_until_complete(rag.initialize_storages())
                loop.run_until_complete(initialize_pipeline_status())
                
                # Get processing status
                status_counts = loop.run_until_complete(rag.get_processing_status())
                
                # Display status counts
                statuses = [
                    ("✅ Processed", DocStatus.PROCESSED),
                    ("⏳ Processing", DocStatus.PROCESSING),
                    ("🔄 Pending", DocStatus.PENDING),
                    ("❌ Failed", DocStatus.FAILED),
                ]
                
                total_docs = 0
                for name, status in statuses:
                    count = status_counts.get(status, 0)
                    total_docs += count
                    if count > 0:
                        print(f"{name:<20} {count:>5} documents")
                
                print("-" * 60)
                print(f"{'Total Documents:':<20} {total_docs:>5} documents")
                
                # Get some stats about the knowledge graph
                print("\n📈 Knowledge Graph Stats")
                print("=" * 60)
                
                # Count entities and relationships
                try:
                    # Access the underlying NanoVectorDB clients
                    # Note: This is accessing private members, but it's the only way
                    # to get counts without modifying LightRAG itself
                    entity_count = 0
                    relationship_count = 0
                    chunk_count = 0
                    
                    # Try to get entity count
                    if hasattr(rag.entities_vdb, '_client') and rag.entities_vdb._client:
                        entity_count = len(rag.entities_vdb._client)
                    
                    # Try to get relationship count
                    if hasattr(rag.relationships_vdb, '_client') and rag.relationships_vdb._client:
                        relationship_count = len(rag.relationships_vdb._client)
                    
                    # Try to get chunk count
                    if hasattr(rag.chunks_vdb, '_client') and rag.chunks_vdb._client:
                        chunk_count = len(rag.chunks_vdb._client)
                    
                    # Also try to count nodes and edges in the graph storage
                    node_count = 0
                    edge_count = 0
                    if hasattr(rag.chunk_entity_relation_graph, '_graph_impl'):
                        graph = rag.chunk_entity_relation_graph._graph_impl
                        if hasattr(graph, 'number_of_nodes'):
                            node_count = graph.number_of_nodes()
                        if hasattr(graph, 'number_of_edges'):
                            edge_count = graph.number_of_edges()
                    
                    print(f"{'🏷️  Entities:':<20} {entity_count:>5}")
                    print(f"{'🔗 Relationships:':<20} {relationship_count:>5}")
                    print(f"{'📄 Chunks:':<20} {chunk_count:>5}")
                    
                    if node_count > 0 or edge_count > 0:
                        print(f"{'🔵 Graph Nodes:':<20} {node_count:>5}")
                        print(f"{'🔴 Graph Edges:':<20} {edge_count:>5}")
                        
                except Exception as e:
                    print(f"  ⚠️  Could not retrieve graph statistics: {str(e)}")
                    # Try a simpler approach - just check if the files exist and their size
                    try:
                        from pathlib import Path as PathLib
                        db_path = PathLib("./lightrag_transcripts_db")
                        if db_path.exists():
                            vdb_entities = db_path / "vdb_entities.json"
                            vdb_relationships = db_path / "vdb_relationships.json" 
                            vdb_chunks = db_path / "vdb_chunks.json"
                            
                            if vdb_entities.exists():
                                size_mb = vdb_entities.stat().st_size / 1024 / 1024
                                print(f"  📊 Entities DB: {size_mb:.1f} MB")
                            if vdb_relationships.exists():
                                size_mb = vdb_relationships.stat().st_size / 1024 / 1024
                                print(f"  📊 Relations DB: {size_mb:.1f} MB")
                            if vdb_chunks.exists():
                                size_mb = vdb_chunks.stat().st_size / 1024 / 1024
                                print(f"  📊 Chunks DB: {size_mb:.1f} MB")
                    except:
                        pass
                
            finally:
                loop.close()
                
        except Exception as e:
            print(f"  ⚠️  Could not connect to LightRAG: {str(e)}")
        
        print("\n💡 Tip: Run 'python src/ingest.py process' to process pending items")
        print()
    
    def _move_to_failed(self, item_file: Path, error: str):
        """Move failed item and record error"""
        error_file = self.base_dir / 'failed' / f"{item_file.stem}.error"
        
        # Read original data
        if item_file.exists():
            with open(item_file) as f:
                data = json.load(f)
        else:
            # Try downloading location
            downloading = self.base_dir / 'downloading' / item_file.name
            if downloading.exists():
                with open(downloading) as f:
                    data = json.load(f)
                downloading.unlink()
            else:
                data = {"url": "unknown"}
        
        # Write error info
        error_data = {
            'original': data,
            'error': error,
            'failed_at': datetime.now().isoformat()
        }
        
        with open(error_file, 'w') as f:
            json.dump(error_data, f, indent=2)
    


def main():
    """CLI interface"""
    processor = ContentProcessor()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python src/ingest.py add URL [--limit N]  # Add content to process")
        print("  python src/ingest.py process               # Process all pending items")
        print("  python src/ingest.py status                # Show pipeline status")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "add" and len(sys.argv) > 2:
        url = sys.argv[2]
        limit = None
        
        # Check for --limit flag
        if len(sys.argv) > 3 and sys.argv[3] == "--limit" and len(sys.argv) > 4:
            try:
                limit = int(sys.argv[4])
            except ValueError:
                print("Error: --limit must be followed by a number")
                sys.exit(1)
        
        processor.add_url(url, limit)
    
    elif command == "process":
        processor.process_inbox()
    
    elif command == "status":
        # Check for -t flag
        interval = None
        if len(sys.argv) > 2 and sys.argv[2] == "-t":
            if len(sys.argv) > 3:
                try:
                    interval = int(sys.argv[3])
                    if interval < 1:
                        print("Error: Interval must be at least 1 second")
                        sys.exit(1)
                except ValueError:
                    print("Error: -t must be followed by a number of seconds")
                    sys.exit(1)
            else:
                # Default to 5 seconds if -t is specified without a value
                interval = 5
        
        processor.status(interval)
    
    else:
        print("Usage:")
        print("  python src/ingest.py add URL [--limit N]   # Add content to process")
        print("  python src/ingest.py process                # Process all pending items")
        print("  python src/ingest.py status [-t [seconds]]  # Show status (optionally refresh every N seconds)")
        print("\nExamples:")
        print("  python src/ingest.py status                 # Show status once")
        print("  python src/ingest.py status -t              # Monitor status (refresh every 5s)")
        print("  python src/ingest.py status -t 10           # Monitor status (refresh every 10s)")
        sys.exit(1)


if __name__ == "__main__":
    main()