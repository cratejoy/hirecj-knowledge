#!/usr/bin/env python3
"""
EcommerceFuel Forum Playwright Scraper
Elegant browser automation framework with session persistence and visual feedback
"""

import json
import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
import hashlib
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from playwright._impl._api_types import TimeoutError as PlaywrightTimeout

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('playwright_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EcommerceFuelScraper:
    """Elegant Playwright-based scraper with session management and visual feedback"""
    
    def __init__(self, headless: bool = False, debug: bool = True):
        self.base_url = "https://forum.ecommercefuel.com"
        self.headless = headless
        self.debug = debug
        self.state_dir = Path("scraper_state")
        self.data_dir = Path("forum_data")
        self.screenshots_dir = Path("screenshots")
        
        # Create directories
        for dir_path in [self.state_dir, self.data_dir, self.screenshots_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # State management
        self.state_file = self.state_dir / "browser_state.json"
        self.cookies_file = self.state_dir / "cookies.json"
        self.progress_file = self.state_dir / "scraping_progress.json"
        
        # Tracking
        self.scraped_posts: Set[str] = set()
        self.scraped_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        
        # Load previous progress
        self.load_progress()
    
    def load_progress(self):
        """Load previous scraping progress"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                progress = json.load(f)
                self.scraped_posts = set(progress.get('scraped_posts', []))
                self.scraped_urls = set(progress.get('scraped_urls', []))
                self.failed_urls = set(progress.get('failed_urls', []))
                logger.info(f"Loaded progress: {len(self.scraped_posts)} posts already scraped")
    
    def save_progress(self):
        """Save scraping progress"""
        progress = {
            'scraped_posts': list(self.scraped_posts),
            'scraped_urls': list(self.scraped_urls),
            'failed_urls': list(self.failed_urls),
            'last_updated': datetime.now().isoformat()
        }
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
    
    def get_post_filename(self, post_url: str) -> Path:
        """Generate consistent filename for a post"""
        # Extract post ID from URL
        parts = post_url.strip('/').split('/')
        if len(parts) >= 2:
            post_slug = parts[-2]
            post_id = parts[-1].split('?')[0]
            filename = f"{post_slug}_{post_id}.json"
        else:
            # Fallback to hash
            url_hash = hashlib.md5(post_url.encode()).hexdigest()[:8]
            filename = f"post_{url_hash}.json"
        
        return self.data_dir / filename
    
    def take_screenshot(self, page: Page, name: str):
        """Take a screenshot for debugging"""
        if self.debug:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = self.screenshots_dir / f"{timestamp}_{name}.png"
            page.screenshot(path=str(screenshot_path))
            logger.debug(f"Screenshot saved: {screenshot_path}")
    
    def check_login_status(self, page: Page) -> bool:
        """Check if user is logged in"""
        try:
            # Look for user menu or login button
            user_menu = page.locator('[data-user-menu]').first
            if user_menu.is_visible(timeout=5000):
                logger.info("User is logged in")
                return True
            
            # Alternative check - look for "New Topic" button
            new_topic = page.locator('button:has-text("New Topic")').first
            if new_topic.is_visible(timeout=5000):
                logger.info("User is logged in (New Topic button visible)")
                return True
                
        except:
            pass
        
        logger.info("User is not logged in")
        return False
    
    def handle_login(self, page: Page):
        """Handle login process"""
        logger.info("Login required. Please log in manually in the browser.")
        print("\n" + "="*50)
        print("MANUAL LOGIN REQUIRED")
        print("="*50)
        print("Please log in to the forum in the browser window.")
        print("Press Enter when you have logged in successfully...")
        print("="*50 + "\n")
        
        # Wait for user to log in
        input()
        
        # Verify login
        if self.check_login_status(page):
            logger.info("Login successful, saving cookies...")
            # Save cookies
            cookies = page.context.cookies()
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f)
            logger.info("Cookies saved for future sessions")
        else:
            raise Exception("Login verification failed")
    
    def create_browser_context(self, playwright) -> Tuple[Browser, BrowserContext]:
        """Create browser with persistent context"""
        browser = playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        # Create context with saved state if available
        context_options = {
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        # Load cookies if available
        if self.cookies_file.exists():
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)
                context_options['storage_state'] = {'cookies': cookies}
        
        context = browser.new_context(**context_options)
        return browser, context
    
    def extract_post_list(self, page: Page) -> List[Dict]:
        """Extract post information from the topic list"""
        posts = []
        
        # Wait for table to load
        page.wait_for_selector('table[aria-label*="topics"]', timeout=10000)
        
        # Get all topic rows
        rows = page.locator('table[aria-label*="topics"] tbody tr').all()
        
        for row in rows:
            try:
                # Extract post data
                title_elem = row.locator('h2 a').first
                author_elem = row.locator('td:first-child a').first
                category_elem = row.locator('a[href*="/c/"]').first
                
                post_data = {
                    'title': title_elem.inner_text() if title_elem else '',
                    'url': title_elem.get_attribute('href') if title_elem else '',
                    'author': author_elem.inner_text() if author_elem else '',
                    'category': category_elem.inner_text() if category_elem else '',
                    'replies': 0,
                    'views': 0,
                    'last_activity': '',
                    'tags': []
                }
                
                # Extract stats
                stats_cells = row.locator('td').all()
                if len(stats_cells) >= 4:
                    # Replies
                    replies_text = stats_cells[2].inner_text()
                    post_data['replies'] = int(replies_text.split()[0]) if replies_text else 0
                    
                    # Views
                    views_text = stats_cells[3].inner_text()
                    if 'k' in views_text:
                        post_data['views'] = int(float(views_text.replace('k', '')) * 1000)
                    else:
                        post_data['views'] = int(views_text) if views_text.isdigit() else 0
                    
                    # Last activity
                    post_data['last_activity'] = stats_cells[4].inner_text()
                
                # Extract tags
                tags = row.locator('a[href*="/tag/"]').all()
                post_data['tags'] = [tag.inner_text() for tag in tags]
                
                if post_data['url']:
                    posts.append(post_data)
                    
            except Exception as e:
                logger.error(f"Error extracting post row: {e}")
                continue
        
        logger.info(f"Extracted {len(posts)} posts from current view")
        return posts
    
    def scrape_post_content(self, page: Page, post_url: str) -> Optional[Dict]:
        """Scrape full content of a single post including all replies"""
        try:
            full_url = urljoin(self.base_url, post_url)
            logger.info(f"Scraping post: {full_url}")
            
            page.goto(full_url, wait_until='networkidle')
            page.wait_for_selector('.post-stream', timeout=10000)
            
            # Take screenshot for debugging
            self.take_screenshot(page, f"post_{post_url.replace('/', '_')}")
            
            # Extract post metadata
            post_data = {
                'url': post_url,
                'full_url': full_url,
                'title': '',
                'author': '',
                'category': '',
                'tags': [],
                'created_at': '',
                'replies': [],
                'stats': {},
                'scraped_at': datetime.now().isoformat()
            }
            
            # Title
            title_elem = page.locator('h1').first
            if title_elem:
                post_data['title'] = title_elem.inner_text()
            
            # Category
            category_elem = page.locator('.category-name').first
            if category_elem:
                post_data['category'] = category_elem.inner_text()
            
            # Tags
            tag_elems = page.locator('.discourse-tags a').all()
            post_data['tags'] = [tag.inner_text() for tag in tag_elems]
            
            # Extract all posts (original + replies)
            posts = page.locator('.topic-post').all()
            
            for idx, post in enumerate(posts):
                try:
                    reply_data = {
                        'index': idx,
                        'author': '',
                        'author_username': '',
                        'content': '',
                        'created_at': '',
                        'post_number': idx + 1,
                        'likes': 0,
                        'is_original': idx == 0
                    }
                    
                    # Author
                    author_elem = post.locator('.username a').first
                    if author_elem:
                        reply_data['author'] = author_elem.inner_text()
                        reply_data['author_username'] = author_elem.get_attribute('data-user-card')
                    
                    # Content
                    content_elem = post.locator('.cooked').first
                    if content_elem:
                        reply_data['content'] = content_elem.inner_html()
                        reply_data['content_text'] = content_elem.inner_text()
                    
                    # Timestamp
                    time_elem = post.locator('time').first
                    if time_elem:
                        reply_data['created_at'] = time_elem.get_attribute('datetime')
                    
                    # Likes
                    likes_elem = post.locator('.like-count').first
                    if likes_elem:
                        likes_text = likes_elem.inner_text()
                        reply_data['likes'] = int(likes_text) if likes_text.isdigit() else 0
                    
                    # Add to replies
                    post_data['replies'].append(reply_data)
                    
                    # Set original post author
                    if idx == 0:
                        post_data['author'] = reply_data['author']
                        post_data['created_at'] = reply_data['created_at']
                        
                except Exception as e:
                    logger.error(f"Error extracting reply {idx}: {e}")
                    continue
            
            # Extract stats
            stats_elem = page.locator('.topic-map-stats').first
            if stats_elem:
                stat_items = stats_elem.locator('.topic-map-stat').all()
                for stat in stat_items:
                    label = stat.locator('.label').inner_text().lower()
                    value = stat.locator('.value').inner_text()
                    post_data['stats'][label] = value
            
            logger.info(f"Scraped post with {len(post_data['replies'])} replies")
            return post_data
            
        except Exception as e:
            logger.error(f"Error scraping post {post_url}: {e}")
            self.failed_urls.add(post_url)
            return None
    
    def save_post_data(self, post_data: Dict):
        """Save post data to JSON file"""
        filename = self.get_post_filename(post_data['url'])
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(post_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved post data to {filename}")
        self.scraped_posts.add(post_data['url'])
        self.save_progress()
    
    def handle_infinite_scroll(self, page: Page) -> bool:
        """Handle infinite scroll to load more posts"""
        try:
            # Scroll to bottom
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            # Wait for potential new content
            time.sleep(2)
            
            # Check if loading indicator appears
            loading = page.locator('.loading-container').first
            if loading.is_visible():
                loading.wait_for(state='hidden', timeout=10000)
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error handling scroll: {e}")
            return False
    
    def scrape_topic_list(self, page: Page, max_scrolls: int = 50) -> List[Dict]:
        """Scrape all posts from the topic list with infinite scroll"""
        all_posts = []
        seen_urls = set()
        scroll_count = 0
        
        while scroll_count < max_scrolls:
            # Extract current posts
            posts = self.extract_post_list(page)
            
            # Add new posts
            new_posts = 0
            for post in posts:
                if post['url'] not in seen_urls:
                    seen_urls.add(post['url'])
                    all_posts.append(post)
                    new_posts += 1
            
            logger.info(f"Scroll {scroll_count}: Found {new_posts} new posts")
            
            # Try to load more
            if not self.handle_infinite_scroll(page):
                logger.info("No more posts to load")
                break
                
            scroll_count += 1
            
            # Take periodic screenshots
            if scroll_count % 5 == 0:
                self.take_screenshot(page, f"scroll_{scroll_count}")
        
        return all_posts
    
    def run(self, start_url: str = None, max_posts: int = None):
        """Main scraping process"""
        with sync_playwright() as playwright:
            browser, context = self.create_browser_context(playwright)
            page = context.new_page()
            
            try:
                # Navigate to forum
                url = start_url or f"{self.base_url}/latest"
                logger.info(f"Navigating to {url}")
                page.goto(url, wait_until='networkidle')
                
                # Check login status
                if not self.check_login_status(page):
                    self.handle_login(page)
                
                # Take initial screenshot
                self.take_screenshot(page, "initial_state")
                
                # Phase 1: Collect all post URLs
                logger.info("Phase 1: Collecting post URLs...")
                all_posts = self.scrape_topic_list(page)
                logger.info(f"Found {len(all_posts)} total posts")
                
                # Filter out already scraped posts
                posts_to_scrape = [
                    post for post in all_posts 
                    if post['url'] not in self.scraped_posts
                ]
                logger.info(f"{len(posts_to_scrape)} posts to scrape")
                
                # Apply max_posts limit if specified
                if max_posts:
                    posts_to_scrape = posts_to_scrape[:max_posts]
                
                # Phase 2: Scrape each post
                logger.info("Phase 2: Scraping individual posts...")
                for idx, post in enumerate(posts_to_scrape, 1):
                    logger.info(f"Scraping post {idx}/{len(posts_to_scrape)}: {post['title']}")
                    
                    post_data = self.scrape_post_content(page, post['url'])
                    if post_data:
                        # Merge list data with full content
                        post_data.update({
                            'list_stats': {
                                'replies': post['replies'],
                                'views': post['views'],
                                'last_activity': post['last_activity']
                            }
                        })
                        self.save_post_data(post_data)
                    
                    # Rate limiting
                    time.sleep(1)
                
                logger.info("Scraping completed!")
                self.generate_summary()
                
            except KeyboardInterrupt:
                logger.info("Scraping interrupted by user")
            except Exception as e:
                logger.error(f"Fatal error: {e}")
                raise
            finally:
                browser.close()
    
    def generate_summary(self):
        """Generate summary of scraped data"""
        summary = {
            'total_posts_scraped': len(self.scraped_posts),
            'failed_urls': len(self.failed_urls),
            'data_directory': str(self.data_dir),
            'last_run': datetime.now().isoformat(),
            'posts': []
        }
        
        # Analyze scraped posts
        for post_file in self.data_dir.glob('*.json'):
            try:
                with open(post_file, 'r') as f:
                    post_data = json.load(f)
                    summary['posts'].append({
                        'title': post_data.get('title'),
                        'author': post_data.get('author'),
                        'replies_count': len(post_data.get('replies', [])),
                        'file': post_file.name
                    })
            except:
                continue
        
        # Save summary
        summary_file = self.data_dir / 'scraping_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n{'='*50}")
        print(f"Scraping Summary:")
        print(f"{'='*50}")
        print(f"Total posts scraped: {summary['total_posts_scraped']}")
        print(f"Failed URLs: {summary['failed_urls']}")
        print(f"Data saved to: {summary['data_directory']}")
        print(f"{'='*50}\n")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='EcommerceFuel Forum Scraper')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--no-debug', action='store_true', help='Disable debug screenshots')
    parser.add_argument('--max-posts', type=int, help='Maximum number of posts to scrape')
    parser.add_argument('--start-url', help='Starting URL (default: /latest)')
    parser.add_argument('--reset', action='store_true', help='Reset progress and start fresh')
    
    args = parser.parse_args()
    
    # Initialize scraper
    scraper = EcommerceFuelScraper(
        headless=args.headless,
        debug=not args.no_debug
    )
    
    # Reset if requested
    if args.reset:
        logger.info("Resetting progress...")
        scraper.scraped_posts.clear()
        scraper.scraped_urls.clear()
        scraper.failed_urls.clear()
        scraper.save_progress()
    
    # Run scraper
    scraper.run(
        start_url=args.start_url,
        max_posts=args.max_posts
    )


if __name__ == "__main__":
    main()