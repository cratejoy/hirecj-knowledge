#!/usr/bin/env python3
"""
Enhanced EcommerceFuel Forum Scraper with Control Integration
"""

import json
import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
import hashlib
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from ecommercefuel_playwright_scraper import EcommerceFuelScraper


class EnhancedEcommerceFuelScraper(EcommerceFuelScraper):
    """Enhanced scraper with control integration and better feedback"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.control_file = self.state_dir / "control.json"
        self.is_paused = False
        self.rate_limit = 1.0  # Default 1 second between requests
        self.skip_urls = set()
        
    def check_control_commands(self):
        """Check for control commands from the monitor"""
        if not self.control_file.exists():
            return
            
        try:
            with open(self.control_file, 'r') as f:
                control = json.load(f)
            
            command = control.get('command')
            data = control.get('data', {})
            
            if command == 'pause':
                self.is_paused = True
                logger.info("Scraper paused by control command")
            elif command == 'resume':
                self.is_paused = False
                logger.info("Scraper resumed by control command")
            elif command == 'rate_limit':
                self.rate_limit = data.get('seconds', 1.0)
                logger.info(f"Rate limit set to {self.rate_limit} seconds")
            elif command == 'skip_post':
                url = data.get('url')
                if url:
                    self.skip_urls.add(url)
                    logger.info(f"Skipping post: {url}")
            
            # Clear the control file
            os.remove(self.control_file)
            
        except Exception as e:
            logger.error(f"Error processing control command: {e}")
    
    def wait_if_paused(self):
        """Wait while paused"""
        while self.is_paused:
            logger.info("Scraper is paused. Waiting...")
            time.sleep(1)
            self.check_control_commands()
    
    def update_live_status(self, status: Dict):
        """Update live status for monitor"""
        status_file = self.state_dir / "live_status.json"
        status['timestamp'] = datetime.now().isoformat()
        
        with open(status_file, 'w') as f:
            json.dump(status, f)
    
    def scrape_post_content_with_feedback(self, page: Page, post_url: str, post_info: Dict) -> Optional[Dict]:
        """Enhanced post scraping with live feedback"""
        # Check control commands
        self.check_control_commands()
        self.wait_if_paused()
        
        # Check if should skip
        if post_url in self.skip_urls:
            logger.info(f"Skipping post as requested: {post_url}")
            return None
        
        # Update live status
        self.update_live_status({
            'current_action': 'scraping_post',
            'current_post': post_info.get('title', 'Unknown'),
            'current_url': post_url,
            'progress': {
                'scraped': len(self.scraped_posts),
                'total': len(self.scraped_posts) + len(self.scraped_urls)
            }
        })
        
        # Scrape the post
        result = self.scrape_post_content(page, post_url)
        
        # Rate limiting
        time.sleep(self.rate_limit)
        
        return result
    
    def extract_post_list_enhanced(self, page: Page) -> List[Dict]:
        """Enhanced post extraction with better error handling"""
        posts = []
        
        try:
            # Wait for table with multiple strategies
            selectors = [
                'table[aria-label*="topics"]',
                'table.topic-list',
                '.topic-list-body'
            ]
            
            table_found = False
            for selector in selectors:
                try:
                    page.wait_for_selector(selector, timeout=5000)
                    table_found = True
                    break
                except:
                    continue
            
            if not table_found:
                logger.warning("Could not find topic table")
                return posts
            
            # Try multiple row selectors
            row_selectors = [
                'table[aria-label*="topics"] tbody tr',
                'table.topic-list tbody tr',
                '.topic-list-item'
            ]
            
            rows = []
            for selector in row_selectors:
                rows = page.locator(selector).all()
                if rows:
                    break
            
            logger.info(f"Found {len(rows)} topic rows")
            
            for idx, row in enumerate(rows):
                try:
                    # Multiple strategies for extracting data
                    post_data = self.extract_post_from_row(row, idx)
                    if post_data and post_data.get('url'):
                        posts.append(post_data)
                except Exception as e:
                    logger.error(f"Error extracting row {idx}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error in post list extraction: {e}")
            
        return posts
    
    def extract_post_from_row(self, row, idx: int) -> Dict:
        """Extract post data from a row with multiple strategies"""
        post_data = {
            'title': '',
            'url': '',
            'author': '',
            'category': '',
            'replies': 0,
            'views': 0,
            'last_activity': '',
            'tags': []
        }
        
        # Title and URL - try multiple selectors
        title_selectors = ['h2 a', '.topic-link', 'a.title']
        for selector in title_selectors:
            try:
                title_elem = row.locator(selector).first
                if title_elem:
                    post_data['title'] = title_elem.inner_text()
                    post_data['url'] = title_elem.get_attribute('href')
                    if post_data['title']:
                        break
            except:
                continue
        
        # Author
        author_selectors = ['td:first-child a', '.topic-poster a', 'a[data-user-card]']
        for selector in author_selectors:
            try:
                author_elem = row.locator(selector).first
                if author_elem:
                    post_data['author'] = author_elem.inner_text()
                    if post_data['author']:
                        break
            except:
                continue
        
        # Category
        category_selectors = ['a[href*="/c/"]', '.category-name', '.badge-category']
        for selector in category_selectors:
            try:
                category_elem = row.locator(selector).first
                if category_elem:
                    post_data['category'] = category_elem.inner_text()
                    if post_data['category']:
                        break
            except:
                continue
        
        # Extract stats with flexible parsing
        try:
            cells = row.locator('td').all()
            if len(cells) >= 3:
                # Find numeric cells
                for i, cell in enumerate(cells):
                    text = cell.inner_text().strip()
                    
                    # Replies
                    if i == 2 or 'repl' in text.lower():
                        num = self.extract_number(text)
                        if num is not None:
                            post_data['replies'] = num
                    
                    # Views
                    elif i == 3 or 'view' in text.lower():
                        num = self.extract_number(text)
                        if num is not None:
                            post_data['views'] = num
                    
                    # Last activity
                    elif any(unit in text for unit in ['m', 'h', 'd', 'mo', 'y']):
                        post_data['last_activity'] = text
        except:
            pass
        
        # Tags
        try:
            tags = row.locator('a[href*="/tag/"]').all()
            post_data['tags'] = [tag.inner_text() for tag in tags]
        except:
            pass
        
        return post_data
    
    def extract_number(self, text: str) -> Optional[int]:
        """Extract number from text with k/m suffix support"""
        try:
            text = text.strip().lower()
            if 'k' in text:
                return int(float(text.replace('k', '')) * 1000)
            elif 'm' in text:
                return int(float(text.replace('m', '')) * 1000000)
            else:
                # Extract first number
                import re
                match = re.search(r'\d+', text)
                if match:
                    return int(match.group())
        except:
            pass
        return None
    
    def run_with_resume(self, start_url: str = None, max_posts: int = None):
        """Run scraper with better resume capability"""
        logger.info("Starting enhanced scraper with control integration")
        
        # Update status
        self.update_live_status({
            'current_action': 'initializing',
            'start_time': datetime.now().isoformat()
        })
        
        try:
            self.run(start_url, max_posts)
        except Exception as e:
            logger.error(f"Scraper error: {e}")
            self.update_live_status({
                'current_action': 'error',
                'error': str(e)
            })
            raise
        finally:
            self.update_live_status({
                'current_action': 'completed',
                'end_time': datetime.now().isoformat()
            })


def main():
    """Enhanced main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced EcommerceFuel Forum Scraper')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--no-debug', action='store_true', help='Disable debug screenshots')
    parser.add_argument('--max-posts', type=int, help='Maximum number of posts to scrape')
    parser.add_argument('--start-url', help='Starting URL (default: /latest)')
    parser.add_argument('--reset', action='store_true', help='Reset progress and start fresh')
    parser.add_argument('--rate-limit', type=float, default=1.0, help='Seconds between requests')
    
    args = parser.parse_args()
    
    # Initialize enhanced scraper
    scraper = EnhancedEcommerceFuelScraper(
        headless=args.headless,
        debug=not args.no_debug
    )
    
    # Set initial rate limit
    scraper.rate_limit = args.rate_limit
    
    # Reset if requested
    if args.reset:
        logger.info("Resetting progress...")
        scraper.scraped_posts.clear()
        scraper.scraped_urls.clear()
        scraper.failed_urls.clear()
        scraper.save_progress()
    
    # Run scraper
    scraper.run_with_resume(
        start_url=args.start_url,
        max_posts=args.max_posts
    )


if __name__ == "__main__":
    main()