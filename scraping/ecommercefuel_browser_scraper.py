#!/usr/bin/env python3
"""
EcommerceFuel Forum Browser Scraper
Uses browser automation to scrape forum posts from the EcommerceFuel community
"""

import json
import csv
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ecommercefuel_browser_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BrowserInstructions:
    """Instructions for manual browser navigation"""
    
    @staticmethod
    def get_navigation_steps():
        return """
=== BROWSER NAVIGATION INSTRUCTIONS ===

1. Navigate to: https://forum.ecommercefuel.com/
2. If not logged in, click "Login" and enter credentials
3. Once on the forum page, use the browser MCP tools to:
   - Take a snapshot of the page
   - Extract post data from the table
   - Click "Next" or pagination links to navigate pages
   - Repeat until all pages are scraped

4. For each post, capture:
   - Author name and avatar
   - Post title and URL
   - Category/subcategory
   - Tags
   - Number of replies
   - View count
   - Last activity time
   
5. To get full post content:
   - Click on each post title
   - Take a snapshot of the post page
   - Extract the main content, comments, and metadata
   - Navigate back to the list

6. Continue until all desired posts are scraped
"""


class EcommerceFuelBrowserScraper:
    def __init__(self, output_dir: str = "scraped_data"):
        self.output_dir = output_dir
        self.posts_data = []
        self.post_details = {}
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
    def parse_snapshot_data(self, snapshot: str) -> List[Dict]:
        """Parse the browser snapshot to extract post data"""
        posts = []
        
        # This would parse the YAML-like snapshot format
        # For now, returning empty list as placeholder
        logger.info("Parsing snapshot data...")
        
        return posts
    
    def extract_post_from_row(self, row_data: str) -> Optional[Dict]:
        """Extract post information from a table row"""
        # Pattern matching for the row format seen in the snapshot
        pattern = r'row "([^"]+)" \[ref=([^\]]+)\]'
        match = re.match(pattern, row_data)
        
        if match:
            row_content = match.group(1)
            ref_id = match.group(2)
            
            # Parse the row content
            parts = row_content.split()
            
            post_data = {
                'ref_id': ref_id,
                'raw_content': row_content,
                'scraped_at': datetime.now().isoformat()
            }
            
            return post_data
        
        return None
    
    def save_snapshot(self, snapshot: str, filename: str):
        """Save a browser snapshot to file"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(snapshot)
        logger.info(f"Saved snapshot to {filepath}")
    
    def save_post_content(self, post_id: str, content: Dict):
        """Save individual post content"""
        filename = f"post_{post_id}.json"
        filepath = os.path.join(self.output_dir, "posts", filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved post content to {filepath}")
    
    def process_pagination_info(self, snapshot: str) -> Tuple[int, int]:
        """Extract pagination information from snapshot"""
        # Look for pagination indicators
        current_page = 1
        total_pages = 1
        
        # This would parse the snapshot for pagination info
        
        return current_page, total_pages
    
    def generate_scraping_script(self):
        """Generate a step-by-step script for browser automation"""
        script = """
// Browser Automation Script for EcommerceFuel Forum

// Step 1: Navigate to forum
await browser.navigate('https://forum.ecommercefuel.com/');

// Step 2: Wait for page load
await browser.wait(2);

// Step 3: Take initial snapshot
let snapshot = await browser.snapshot();

// Step 4: Extract posts from current page
// Look for table with posts (ref pattern: s1e135)

// Step 5: For each post row:
//   - Extract author, title, URL, stats
//   - Store in array

// Step 6: Check for pagination
// Look for "Next" button or page numbers

// Step 7: Navigate to next page if exists
// Repeat from Step 3

// Step 8: Save all data
"""
        
        filepath = os.path.join(self.output_dir, "browser_script.js")
        with open(filepath, 'w') as f:
            f.write(script)
        
        logger.info(f"Generated browser script at {filepath}")
        
        return script
    
    def create_data_extraction_template(self):
        """Create a template for manual data extraction"""
        template = {
            "instructions": "Fill in the extracted data from the browser",
            "posts": [
                {
                    "id": "",
                    "author": "",
                    "author_url": "",
                    "title": "",
                    "url": "",
                    "category": "",
                    "tags": [],
                    "replies": 0,
                    "views": 0,
                    "last_activity": "",
                    "content": "",
                    "created_at": "",
                    "scraped_at": datetime.now().isoformat()
                }
            ],
            "pagination": {
                "current_page": 1,
                "total_pages": 1,
                "posts_per_page": 30,
                "total_posts": 0
            }
        }
        
        filepath = os.path.join(self.output_dir, "extraction_template.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2)
        
        logger.info(f"Created extraction template at {filepath}")
        
        return template
    
    def merge_extracted_data(self, extracted_files: List[str]):
        """Merge multiple extracted data files"""
        all_posts = []
        
        for filename in extracted_files:
            filepath = os.path.join(self.output_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'posts' in data:
                        all_posts.extend(data['posts'])
        
        self.posts_data = all_posts
        logger.info(f"Merged {len(all_posts)} posts from {len(extracted_files)} files")
        
        return all_posts
    
    def export_data(self):
        """Export all scraped data to various formats"""
        # JSON export
        json_file = os.path.join(self.output_dir, "all_posts.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.posts_data, f, indent=2, ensure_ascii=False)
        
        # CSV export
        if self.posts_data:
            csv_file = os.path.join(self.output_dir, "all_posts.csv")
            
            # Flatten the data for CSV
            flattened_data = []
            for post in self.posts_data:
                flat_post = post.copy()
                # Convert lists to strings
                if 'tags' in flat_post and isinstance(flat_post['tags'], list):
                    flat_post['tags'] = ', '.join(flat_post['tags'])
                flattened_data.append(flat_post)
            
            # Write CSV
            fieldnames = flattened_data[0].keys()
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(flattened_data)
        
        logger.info(f"Exported data to {self.output_dir}")
    
    def generate_stats_report(self):
        """Generate statistics report from scraped data"""
        if not self.posts_data:
            logger.warning("No data to generate stats")
            return
        
        stats = {
            "total_posts": len(self.posts_data),
            "unique_authors": len(set(p.get('author', '') for p in self.posts_data)),
            "categories": {},
            "tags": {},
            "most_replied": None,
            "most_viewed": None,
            "date_range": {
                "earliest": None,
                "latest": None
            }
        }
        
        # Calculate category distribution
        for post in self.posts_data:
            cat = post.get('category', 'Unknown')
            stats['categories'][cat] = stats['categories'].get(cat, 0) + 1
        
        # Calculate tag distribution
        for post in self.posts_data:
            for tag in post.get('tags', []):
                stats['tags'][tag] = stats['tags'].get(tag, 0) + 1
        
        # Find most engaged posts
        if self.posts_data:
            stats['most_replied'] = max(self.posts_data, 
                                      key=lambda x: x.get('replies', 0))
            stats['most_viewed'] = max(self.posts_data, 
                                     key=lambda x: x.get('views', 0))
        
        # Save stats
        stats_file = os.path.join(self.output_dir, "scraping_stats.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Generated stats report at {stats_file}")
        
        return stats


# CLI Interface
def main():
    """Main function to run the scraper"""
    print("=== EcommerceFuel Forum Browser Scraper ===\n")
    
    scraper = EcommerceFuelBrowserScraper()
    
    # Print instructions
    print(BrowserInstructions.get_navigation_steps())
    
    # Generate helper files
    scraper.generate_scraping_script()
    scraper.create_data_extraction_template()
    
    print(f"\nHelper files created in: {scraper.output_dir}")
    print("\nNext steps:")
    print("1. Use the browser MCP to navigate the forum")
    print("2. Extract data using the template")
    print("3. Save extracted data as JSON files")
    print("4. Run this script with --merge flag to combine all data")
    
    # Check for merge flag
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--merge':
        print("\nMerging extracted data files...")
        
        # Find all extraction files
        extraction_files = [f for f in os.listdir(scraper.output_dir) 
                          if f.startswith('extracted_') and f.endswith('.json')]
        
        if extraction_files:
            scraper.merge_extracted_data(extraction_files)
            scraper.export_data()
            stats = scraper.generate_stats_report()
            
            print(f"\nScraping Summary:")
            print(f"Total posts: {stats['total_posts']}")
            print(f"Unique authors: {stats['unique_authors']}")
            print(f"Categories: {len(stats['categories'])}")
            print(f"Unique tags: {len(stats['tags'])}")
        else:
            print("No extraction files found to merge.")


if __name__ == "__main__":
    main()