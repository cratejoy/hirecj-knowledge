#!/usr/bin/env python3
"""
Integrate scraped forum data into the knowledge base system
Converts forum posts into a format suitable for LightRAG processing
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import hashlib


class ForumDataIntegrator:
    """Integrate forum posts into knowledge base"""
    
    def __init__(self, forum_data_dir: str = "forum_data", output_dir: str = "content/transcripts"):
        self.forum_data_dir = Path(forum_data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def convert_post_to_transcript(self, post_data: Dict) -> str:
        """Convert a forum post to transcript-like format for knowledge base"""
        lines = []
        
        # Header with metadata
        lines.append(f"FORUM POST: {post_data.get('title', 'Untitled')}")
        lines.append(f"Category: {post_data.get('category', 'Unknown')}")
        lines.append(f"Author: {post_data.get('author', 'Unknown')}")
        lines.append(f"URL: {post_data.get('full_url', '')}")
        
        if post_data.get('tags'):
            lines.append(f"Tags: {', '.join(post_data['tags'])}")
        
        lines.append(f"Created: {post_data.get('created_at', 'Unknown')}")
        lines.append("=" * 80)
        lines.append("")
        
        # Process all replies as a conversation
        for reply in post_data.get('replies', []):
            # Author and timestamp
            author = reply.get('author', 'Unknown')
            timestamp = reply.get('created_at', '')
            
            if reply.get('is_original'):
                lines.append(f"[ORIGINAL POST by {author}]")
            else:
                lines.append(f"[REPLY by {author}]")
            
            if timestamp:
                lines.append(f"Posted: {timestamp}")
            
            lines.append("")
            
            # Content (use plain text version)
            content = reply.get('content_text', reply.get('content', ''))
            # Clean up content
            content = content.strip()
            if content:
                lines.append(content)
            
            lines.append("")
            lines.append("-" * 40)
            lines.append("")
        
        # Add statistics at the end
        if post_data.get('stats'):
            lines.append("")
            lines.append("POST STATISTICS:")
            for key, value in post_data['stats'].items():
                lines.append(f"- {key.title()}: {value}")
        
        return "\n".join(lines)
    
    def generate_filename(self, post_data: Dict) -> str:
        """Generate a safe filename for the post"""
        title = post_data.get('title', 'untitled')
        # Clean title for filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))
        safe_title = safe_title.strip()[:50]  # Limit length
        
        # Add hash for uniqueness
        url = post_data.get('url', '')
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        
        return f"forum_{safe_title}_{url_hash}.txt"
    
    def process_all_posts(self, limit: int = None) -> List[str]:
        """Process all forum posts into transcript format"""
        processed_files = []
        json_files = list(self.forum_data_dir.glob("*.json"))
        
        if limit:
            json_files = json_files[:limit]
        
        for idx, file_path in enumerate(json_files):
            if file_path.name == "scraping_summary.json":
                continue
            
            try:
                print(f"Processing {idx + 1}/{len(json_files)}: {file_path.name}")
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    post_data = json.load(f)
                
                # Convert to transcript format
                transcript_content = self.convert_post_to_transcript(post_data)
                
                # Generate output filename
                output_filename = self.generate_filename(post_data)
                output_path = self.output_dir / output_filename
                
                # Write transcript file
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(transcript_content)
                
                processed_files.append(str(output_path))
                
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                continue
        
        print(f"\nProcessed {len(processed_files)} forum posts")
        return processed_files
    
    def create_metadata_index(self, processed_files: List[str]):
        """Create metadata index for processed files"""
        metadata = {
            'source': 'EcommerceFuel Forum',
            'processed_date': datetime.now().isoformat(),
            'total_files': len(processed_files),
            'files': []
        }
        
        for file_path in processed_files:
            # Extract basic info from filename
            filename = os.path.basename(file_path)
            metadata['files'].append({
                'filename': filename,
                'path': file_path,
                'type': 'forum_post'
            })
        
        # Save metadata
        metadata_path = self.output_dir / "forum_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Metadata index saved to {metadata_path}")
    
    def create_category_collections(self):
        """Organize posts by category for easier processing"""
        category_posts = {}
        
        json_files = list(self.forum_data_dir.glob("*.json"))
        
        for file_path in json_files:
            if file_path.name == "scraping_summary.json":
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    post_data = json.load(f)
                
                category = post_data.get('category', 'Unknown')
                if category not in category_posts:
                    category_posts[category] = []
                
                category_posts[category].append({
                    'title': post_data.get('title'),
                    'author': post_data.get('author'),
                    'replies': len(post_data.get('replies', [])),
                    'file': file_path.name
                })
                
            except Exception as e:
                continue
        
        # Save category index
        for category, posts in category_posts.items():
            safe_category = "".join(c for c in category if c.isalnum() or c in (' ', '-', '_'))
            category_file = self.output_dir / f"category_{safe_category}.json"
            
            with open(category_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'category': category,
                    'post_count': len(posts),
                    'posts': posts
                }, f, indent=2)
        
        print(f"Created {len(category_posts)} category collection files")


def prepare_for_lightrag():
    """Prepare forum data for LightRAG processing"""
    print("Preparing forum data for knowledge base integration...")
    
    integrator = ForumDataIntegrator()
    
    # Process all posts
    processed_files = integrator.process_all_posts()
    
    # Create metadata index
    integrator.create_metadata_index(processed_files)
    
    # Create category collections
    integrator.create_category_collections()
    
    print("\n=== Integration Complete ===")
    print(f"Forum posts converted to transcripts in: content/transcripts/")
    print("\nNext steps:")
    print("1. Run the transcript loading script to add to LightRAG")
    print("2. Query the knowledge base with forum-specific questions")
    
    # Example queries
    print("\nExample queries to try:")
    print('- "What are common issues with Klaviyo?"')
    print('- "How do store owners handle shipping?"')
    print('- "What email marketing strategies work best?"')
    print('- "What legal issues do ecommerce stores face?"')


if __name__ == "__main__":
    prepare_for_lightrag()