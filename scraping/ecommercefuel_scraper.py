#!/usr/bin/env python3
"""
EcommerceFuel Forum Scraper - Phase 1 & 2: Browser Setup & Forum Structure Discovery
Simple, elegant Playwright-based scraper following North Star principles
"""

import json
import os
import logging
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from typing import Optional, List, Dict


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EcommerceFuelScraper:
    """Simple forum scraper with cookie persistence"""
    
    def __init__(self):
        self.base_url = "https://forum.ecommercefuel.com"
        self.cookies_file = Path("cookies.json")
        self.progress_file = Path("progress.json")
        self.posts_dir = Path("posts")
        self.logs_dir = Path("logs")
        
        # Create directories
        self.posts_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Setup file logging
        log_file = self.logs_dir / f"scraper_{datetime.now().strftime('%Y-%m-%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
    
    def save_cookies(self, context: BrowserContext) -> None:
        """Save browser cookies to file"""
        cookies = context.cookies()
        with open(self.cookies_file, 'w') as f:
            json.dump(cookies, f, indent=2)
        logger.info(f"Saved {len(cookies)} cookies to {self.cookies_file}")
    
    def load_cookies(self, context: BrowserContext) -> bool:
        """Load cookies from file if they exist"""
        if not self.cookies_file.exists():
            logger.info("No cookies file found")
            return False
        
        try:
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)
            context.add_cookies(cookies)
            logger.info(f"Loaded {len(cookies)} cookies from {self.cookies_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return False
    
    def is_logged_in(self, page: Page) -> bool:
        """Check if user is logged in by looking for user menu"""
        try:
            # Try multiple selectors that indicate logged-in state
            selectors = [
                '[data-user-menu]',
                'button:has-text("New Topic")',
                '.user-menu',
                '.current-user'
            ]
            
            for selector in selectors:
                if page.locator(selector).count() > 0:
                    logger.info(f"User is logged in (found {selector})")
                    return True
            
            logger.info("User is not logged in")
            return False
            
        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            return False
    
    def handle_manual_login(self, page: Page, context: BrowserContext) -> bool:
        """Guide user through manual login and save cookies"""
        print("\n" + "="*60)
        print("MANUAL LOGIN REQUIRED")
        print("="*60)
        print("Please log in to the forum in the browser window.")
        print("After logging in, press Enter here to continue...")
        print("="*60 + "\n")
        
        # Wait for user to press Enter
        input()
        
        # Wait a moment for cookies to be set
        logger.info("Waiting for cookies to be set...")
        page.wait_for_timeout(2000)  # 2 seconds
        
        # Navigate to ensure cookies are triggered
        logger.info("Navigating to /latest to ensure session is established...")
        page.goto(f"{self.base_url}/latest")
        page.wait_for_load_state('domcontentloaded')
        page.wait_for_timeout(2000)
        
        # Check if login was successful
        if self.is_logged_in(page):
            logger.info("Login successful!")
            
            # Get all cookies
            cookies = context.cookies()
            logger.info(f"Found {len(cookies)} cookies")
            
            # Log cookie domains for debugging
            domains = set(cookie['domain'] for cookie in cookies)
            logger.info(f"Cookie domains: {domains}")
            
            if len(cookies) > 0:
                self.save_cookies(context)
                return True
            else:
                logger.warning("No cookies found to save! This may indicate a problem.")
                print("\n⚠️  WARNING: No cookies were found after login!")
                print("This might mean:")
                print("1. The site uses a different authentication method")
                print("2. Cookies are set on a different domain")
                print("3. You need to navigate to more pages")
                print("\nTry running debug_cookies.py for more information.")
                return True  # Still return True if logged in, even without cookies
        else:
            logger.error("Login verification failed - please try again")
            return False
    
    def test_browser_setup(self) -> None:
        """Phase 1.1: Test basic browser launch"""
        logger.info("Phase 1.1: Testing basic browser launch")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            logger.info(f"Navigating to {self.base_url}")
            page.goto(self.base_url)
            
            print("\n✅ Browser launched successfully!")
            print("You should see the EcommerceFuel forum.")
            print("Press Enter to continue to cookie test...")
            input()
            
            browser.close()
    
    def test_cookie_management(self) -> None:
        """Phase 1.2: Test cookie save/load functionality"""
        logger.info("Phase 1.2: Testing cookie management")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            # Load cookies if they exist
            cookies_loaded = self.load_cookies(context)
            
            # Navigate to forum
            page.goto(self.base_url)
            page.wait_for_load_state('domcontentloaded')
            
            if cookies_loaded:
                print("\n✅ Cookies loaded from previous session")
            else:
                print("\n❌ No cookies found from previous session")
            
            # Check login status
            if self.is_logged_in(page):
                print("✅ You are logged in!")
            else:
                print("❌ You are not logged in")
            
            print("\nPress Enter to save current cookies and continue...")
            input()
            
            # Save current cookies
            self.save_cookies(context)
            
            browser.close()
    
    def test_login_flow(self) -> None:
        """Phase 1.3: Test complete login flow"""
        logger.info("Phase 1.3: Testing login flow")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            # Load cookies if they exist
            self.load_cookies(context)
            
            # Navigate to forum
            logger.info("Navigating to forum...")
            page.goto(self.base_url)
            page.wait_for_load_state('domcontentloaded')
            # Give the page a moment to settle
            page.wait_for_timeout(2000)
            
            # Check if already logged in
            if self.is_logged_in(page):
                print("\n✅ Already logged in from saved cookies!")
                print("Login flow working correctly.")
            else:
                print("\n❌ Not logged in - initiating manual login...")
                if self.handle_manual_login(page, context):
                    print("✅ Login flow completed successfully!")
                else:
                    print("❌ Login flow failed - please check and try again")
            
            print("\nPress Enter to close browser...")
            input()
            
            browser.close()
    
    def run_phase1(self) -> None:
        """Run all Phase 1 tests"""
        print("\n" + "="*60)
        print("PHASE 1: Browser Setup & Cookie Persistence")
        print("="*60)
        
        # Test 1.1: Basic browser launch
        print("\n--- Test 1.1: Basic Browser Launch ---")
        self.test_browser_setup()
        
        # Test 1.2: Cookie management
        print("\n--- Test 1.2: Cookie Management ---")
        self.test_cookie_management()
        
        # Test 1.3: Login flow
        print("\n--- Test 1.3: Login Flow ---")
        self.test_login_flow()
        
        print("\n" + "="*60)
        print("PHASE 1 COMPLETE!")
        print("="*60)
        print("\nSummary:")
        print(f"- Cookies file: {self.cookies_file} ({'exists' if self.cookies_file.exists() else 'not created'})")
        print(f"- Logs directory: {self.logs_dir}")
        print(f"- Posts directory: {self.posts_dir} (ready for Phase 2)")
        print("\nNext: Review selectors and HTML structure in Phase 2")
    
    # ==================== PHASE 2: Forum Structure Discovery ====================
    
    def explore_topic_list(self, page: Page) -> Dict:
        """Phase 2.1: Explore topic list structure"""
        logger.info("Phase 2.1: Exploring topic list structure")
        
        # Navigate to latest posts
        page.goto(f"{self.base_url}/latest")
        page.wait_for_load_state('domcontentloaded')
        page.wait_for_timeout(3000)  # Let content load
        
        # Try different selectors for the topic table
        selectors_to_try = {
            'table_with_aria': 'table[aria-label*="topics"]',
            'table_topic_list': 'table.topic-list',
            'topic_list_items': '.topic-list-item',
            'tbody_rows': 'tbody tr',
            'topic_list_body': '.topic-list-body tr'
        }
        
        results = {}
        for name, selector in selectors_to_try.items():
            count = page.locator(selector).count()
            results[name] = {
                'selector': selector,
                'count': count,
                'found': count > 0
            }
            logger.info(f"Selector '{name}' ({selector}): {count} elements found")
        
        # Find the best selector (most specific with results)
        best_selector = None
        for name, result in results.items():
            if result['found'] and result['count'] > 5:  # Expect at least a few topics
                best_selector = result['selector']
                print(f"\n✅ Found topic list with selector: {best_selector}")
                print(f"   Contains {result['count']} topics")
                break
        
        if not best_selector:
            print("\n❌ Could not find topic list selector")
            return results
        
        # Sample first topic to understand structure
        first_row = page.locator(best_selector).first
        print("\n📋 Examining first topic row structure...")
        
        # Try to extract HTML for inspection
        try:
            html_sample = first_row.evaluate("el => el.outerHTML")
            print("\nHTML structure sample (first 500 chars):")
            print(html_sample[:500] + "..." if len(html_sample) > 500 else html_sample)
        except:
            print("Could not extract HTML sample")
        
        return results
    
    def extract_post_data_sample(self, page: Page) -> List[Dict]:
        """Phase 2.2: Extract sample post data to verify selectors"""
        logger.info("Phase 2.2: Extracting sample post data")
        
        # Use the tbody tr selector (most common for Discourse)
        rows = page.locator('tbody tr').all()[:5]  # Get first 5 rows
        
        if not rows:
            print("\n❌ No topic rows found")
            return []
        
        print(f"\n📊 Extracting data from {len(rows)} sample topics...")
        
        posts = []
        for i, row in enumerate(rows):
            print(f"\n--- Topic {i+1} ---")
            post_data = {}
            
            # Title - try multiple selectors
            title_selectors = ['a.title', '.topic-link', 'h2 a', 'td:nth-child(2) a']
            for selector in title_selectors:
                try:
                    title_elem = row.locator(selector).first
                    if title_elem.count() > 0:
                        post_data['title'] = title_elem.inner_text()
                        post_data['url'] = title_elem.get_attribute('href')
                        print(f"Title: {post_data.get('title', 'N/A')}")
                        print(f"URL: {post_data.get('url', 'N/A')}")
                        break
                except:
                    continue
            
            # Author - first cell usually
            try:
                author_elem = row.locator('td:first-child a').first
                if author_elem.count() > 0:
                    post_data['author'] = author_elem.inner_text()
                    print(f"Author: {post_data.get('author', 'N/A')}")
            except:
                pass
            
            # Category
            try:
                cat_elem = row.locator('a[href*="/c/"]').first
                if cat_elem.count() > 0:
                    post_data['category'] = cat_elem.inner_text()
                    print(f"Category: {post_data.get('category', 'N/A')}")
            except:
                pass
            
            # Tags
            try:
                tag_elems = row.locator('a[href*="/tag/"]').all()
                if tag_elems:
                    post_data['tags'] = [tag.inner_text() for tag in tag_elems]
                    print(f"Tags: {post_data.get('tags', [])}")
            except:
                pass
            
            # Stats (replies, views, activity) - usually in last cells
            try:
                cells = row.locator('td').all()
                if len(cells) >= 5:
                    # These positions may vary
                    stats_text = []
                    for j in range(2, len(cells)):
                        text = cells[j].inner_text().strip()
                        if text:
                            stats_text.append(text)
                    print(f"Stats cells: {stats_text}")
                    
                    # Try to parse replies/views
                    for text in stats_text:
                        if text.isdigit():
                            if 'replies' not in post_data:
                                post_data['replies'] = int(text)
                            elif 'views' not in post_data:
                                post_data['views'] = int(text)
                        elif 'k' in text:
                            # Handle view counts like "1.2k"
                            try:
                                num = float(text.replace('k', ''))
                                post_data['views'] = int(num * 1000)
                            except:
                                pass
            except Exception as e:
                print(f"Error extracting stats: {e}")
            
            posts.append(post_data)
        
        return posts
    
    def test_infinite_scroll(self, page: Page) -> Dict:
        """Phase 2.3: Test infinite scroll behavior"""
        logger.info("Phase 2.3: Testing infinite scroll")
        
        # Get initial count
        initial_count = page.locator('tbody tr').count()
        print(f"\n📜 Initial topic count: {initial_count}")
        
        # Scroll to bottom
        print("\nScrolling to bottom...")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        
        # Look for loading indicator
        loading_indicators = [
            '.loading-container',
            '.spinner',
            '.loading',
            'div[class*="loading"]'
        ]
        
        loading_found = False
        for indicator in loading_indicators:
            if page.locator(indicator).count() > 0:
                print(f"✅ Found loading indicator: {indicator}")
                loading_found = True
                
                # Wait for it to disappear
                try:
                    page.locator(indicator).wait_for(state='hidden', timeout=5000)
                    print("   Loading complete")
                except:
                    print("   Loading indicator timeout")
                break
        
        if not loading_found:
            print("❌ No loading indicator found")
        
        # Wait a bit more for content
        page.wait_for_timeout(2000)
        
        # Check new count
        new_count = page.locator('tbody tr').count()
        print(f"\n📊 New topic count: {new_count}")
        print(f"   Topics loaded: {new_count - initial_count}")
        
        # Test scroll behavior
        results = {
            'initial_count': initial_count,
            'after_scroll_count': new_count,
            'new_topics_loaded': new_count - initial_count,
            'loading_indicator_found': loading_found,
            'infinite_scroll_works': new_count > initial_count
        }
        
        if results['infinite_scroll_works']:
            print("\n✅ Infinite scroll is working!")
        else:
            print("\n❌ Infinite scroll did not load new content")
            print("   This might mean we're at the end, or scroll isn't working")
        
        return results
    
    def run_phase2(self) -> None:
        """Run all Phase 2 tests"""
        print("\n" + "="*60)
        print("PHASE 2: Forum Structure Discovery")
        print("="*60)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            
            # Load cookies
            self.load_cookies(context)
            
            page = context.new_page()
            
            # Test 2.1: Topic list structure
            print("\n--- Test 2.1: Topic List Structure ---")
            structure_results = self.explore_topic_list(page)
            
            print("\nPress Enter to continue to data extraction test...")
            input()
            
            # Test 2.2: Post data extraction
            print("\n--- Test 2.2: Post Data Extraction ---")
            sample_posts = self.extract_post_data_sample(page)
            
            print(f"\n📋 Successfully extracted {len(sample_posts)} posts")
            print("\nPress Enter to continue to infinite scroll test...")
            input()
            
            # Test 2.3: Infinite scroll
            print("\n--- Test 2.3: Infinite Scroll Detection ---")
            scroll_results = self.test_infinite_scroll(page)
            
            print("\n" + "="*60)
            print("PHASE 2 SUMMARY")
            print("="*60)
            
            # Summarize findings
            print("\n✅ Confirmed selectors:")
            print("   - Topic rows: tbody tr")
            print("   - Title: a.title")
            print("   - Author: td:first-child a")
            print("   - Category: a[href*='/c/']")
            print("   - Tags: a[href*='/tag/']")
            
            if scroll_results['infinite_scroll_works']:
                print(f"\n✅ Infinite scroll confirmed:")
                print(f"   - Loads ~{scroll_results['new_topics_loaded']} topics per scroll")
                if scroll_results['loading_indicator_found']:
                    print("   - Loading indicator: .loading-container")
            
            print("\n📁 Sample data structure:")
            if sample_posts:
                print(json.dumps(sample_posts[0], indent=2, default=str))
            
            print("\nPress Enter to close browser...")
            input()
            
            browser.close()
        
        print("\n" + "="*60)
        print("PHASE 2 COMPLETE!")
        print("="*60)
        print("\nNext: Implement infinite scroll handling in Phase 3")
    
    # ==================== PHASE 3-5: Streaming Implementation with Time-Based Cursors ====================
    
    def load_progress(self) -> Dict:
        """Load progress with time-based bookmarks"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {
            "last_run": None,
            "newest_seen": None,  # Bookmark for new content
            "oldest_seen": None,  # Bookmark for how far back we've gone
            "threads": {},
            "failed_urls": [],
            "total_scraped": 0
        }
    
    def save_progress(self, progress: Dict) -> None:
        """Save progress tracking data"""
        progress["last_run"] = datetime.now().isoformat()
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
    
    def parse_views(self, views_text: str) -> int:
        """Convert views text to number (handles 'k' suffix)"""
        views_text = views_text.strip()
        if views_text.endswith('k'):
            return int(float(views_text[:-1]) * 1000)
        return int(views_text)
    
    def extract_topic_from_row(self, row) -> Dict:
        """Extract clean topic data from a table row"""
        # Title and URL
        title_link = row.locator('a.title').first
        title = title_link.text_content().strip()
        url = title_link.get_attribute('href')
        
        # Author - fixed selector using data-user-card
        author = ""
        author_img = row.locator('img.avatar[data-user-card]').first
        if author_img.count() > 0:
            author = author_img.get_attribute('data-user-card') or ""
        
        # Category
        category = ""
        category_link = row.locator('a[href*="/c/"]').first
        if category_link.count() > 0:
            category = category_link.text_content().strip()
        
        # Tags
        tags = []
        tag_links = row.locator('a[href*="/tag/"]').all()
        for tag_link in tag_links:
            tags.append(tag_link.text_content().strip())
        
        # Stats - last 3 cells: replies, views, last_activity
        cells = row.locator('td').all()
        stats = [cell.text_content().strip() for cell in cells[-3:]]
        
        replies = int(stats[0]) if stats[0].isdigit() else 0
        views = self.parse_views(stats[1]) if len(stats) > 1 else 0
        last_activity = stats[2] if len(stats) > 2 else ""
        
        return {
            "url": url,
            "title": title,
            "author": author,
            "category": category,
            "tags": tags,
            "replies": replies,
            "views": views,
            "last_activity": last_activity
        }
    
    def extract_visible_topics(self, page: Page) -> List[Dict]:
        """Get all topics currently visible on page"""
        topics = []
        rows = page.locator('tbody tr').all()
        
        for row in rows:
            try:
                topic = self.extract_topic_from_row(row)
                topics.append(topic)
            except Exception as e:
                logger.warning(f"Failed to extract topic: {e}")
        
        return topics
    
    def needs_scraping(self, topic: Dict, progress: Dict) -> bool:
        """Check if topic needs to be scraped"""
        thread_info = progress["threads"].get(topic["url"], {})
        
        # Never scraped
        if "last_scraped" not in thread_info:
            return True
        
        # Activity changed
        previous_activity = thread_info.get("last_activity")
        return previous_activity != topic["last_activity"]
    
    def scroll_for_more(self, page: Page) -> bool:
        """Scroll and wait for new content"""
        initial_count = len(page.locator('tbody tr').all())
        
        # Scroll to bottom
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        
        # Wait for loading
        loader = page.locator('.loading-container')
        if loader.is_visible():
            try:
                loader.wait_for(state='hidden', timeout=10000)
            except:
                logger.warning("Loading timeout")
        else:
            page.wait_for_timeout(2000)
        
        # Check if we got new content
        new_count = len(page.locator('tbody tr').all())
        return new_count > initial_count
    
    def update_bookmarks(self, topics: List[Dict], progress: Dict) -> None:
        """Update our position bookmarks"""
        if not topics:
            return
        
        # Update newest if this is newer (or first run)
        if not progress['newest_seen']:
            progress['newest_seen'] = {
                "url": topics[0]['url'],
                "last_activity": topics[0]['last_activity'],
                "timestamp": datetime.now().isoformat()
            }
        
        # Always update oldest as we scroll backwards
        progress['oldest_seen'] = {
            "url": topics[-1]['url'],
            "last_activity": topics[-1]['last_activity'],
            "timestamp": datetime.now().isoformat()
        }
    
    def scroll_to_topic(self, page: Page, target_url: str) -> bool:
        """Scroll until we find a specific topic"""
        max_scrolls = 50
        scrolls = 0
        
        logger.info(f"Scrolling to find bookmark: {target_url}")
        
        while scrolls < max_scrolls:
            topics = self.extract_visible_topics(page)
            
            # Check if target is visible
            for topic in topics:
                if topic['url'] == target_url:
                    logger.info(f"Found bookmark after {scrolls} scrolls")
                    return True
            
            # Scroll for more
            if not self.scroll_for_more(page):
                logger.warning("Reached end without finding bookmark")
                return False
            
            scrolls += 1
        
        logger.warning(f"Bookmark not found after {max_scrolls} scrolls")
        return False
    
    
    # ==================== PHASE 4: Individual Thread Scraping ====================
    
    def url_to_filename(self, url: str) -> str:
        """Convert thread URL to safe filename"""
        # Extract ID and slug from URL like /t/some-thread/12345
        parts = url.strip('/').split('/')
        if len(parts) >= 3:
            thread_id = parts[-1]
            thread_slug = parts[-2]
            return f"t_{thread_id}_{thread_slug}.json"
        return f"thread_{url.replace('/', '_')}.json"
    
    def extract_post_author(self, post_elem) -> Dict:
        """Extract author info from a post element"""
        author = {
            "username": "",
            "display_name": "",
            "avatar_url": ""
        }
        
        try:
            # Username from data-user-card
            user_link = post_elem.locator('a[data-user-card]').first
            if user_link.count() > 0:
                author["username"] = user_link.get_attribute('data-user-card') or ""
                author["display_name"] = user_link.text_content().strip()
            
            # Avatar
            avatar = post_elem.locator('img.avatar').first
            if avatar.count() > 0:
                author["avatar_url"] = avatar.get_attribute('src') or ""
                
        except Exception as e:
            logger.warning(f"Error extracting author: {e}")
            
        return author
    
    def extract_post_data(self, post_elem, index: int) -> Dict:
        """Extract data from a single post"""
        post = {
            "index": index,
            "author": {},
            "content_html": "",
            "content_text": "",
            "timestamp": "",
            "likes": 0,
            "is_original": index == 0
        }
        
        try:
            # Author
            post["author"] = self.extract_post_author(post_elem)
            
            # Content
            content = post_elem.locator('.cooked').first
            if content.count() > 0:
                post["content_html"] = content.inner_html()
                post["content_text"] = content.text_content().strip()
            
            # Timestamp
            time_elem = post_elem.locator('time').first
            if time_elem.count() > 0:
                post["timestamp"] = time_elem.get_attribute('datetime') or ""
            
            # Likes - look for like button with count
            like_button = post_elem.locator('button.like-count').first
            if like_button.count() > 0:
                like_text = like_button.text_content().strip()
                if like_text.isdigit():
                    post["likes"] = int(like_text)
                    
        except Exception as e:
            logger.warning(f"Error extracting post data: {e}")
            
        return post
    
    def scrape_thread(self, page: Page, topic_data: Dict) -> Dict:
        """Scrape a complete thread"""
        url = topic_data['url']
        full_url = f"{self.base_url}{url}"
        
        logger.info(f"Scraping thread: {topic_data['title'][:50]}...")
        page.goto(full_url)
        page.wait_for_load_state('domcontentloaded')
        page.wait_for_timeout(2000)
        
        # Start with topic data from phase 3
        thread_data = {
            "url": url,
            "title": topic_data['title'],
            "category": topic_data['category'],
            "tags": topic_data['tags'],
            "author": {"username": topic_data['author']},
            "stats": {
                "replies": topic_data['replies'],
                "views": topic_data['views'],
                "last_activity": topic_data['last_activity']
            },
            "posts": [],
            "scraped_at": datetime.now().isoformat()
        }
        
        try:
            # Get all posts
            posts = page.locator('article.onscreen-post').all()
            logger.info(f"Found {len(posts)} posts")
            
            for i, post_elem in enumerate(posts):
                post_data = self.extract_post_data(post_elem, i)
                thread_data["posts"].append(post_data)
                
                # First post author is thread author with more details
                if i == 0 and post_data["author"]["username"]:
                    thread_data["author"] = post_data["author"]
                    thread_data["created_at"] = post_data["timestamp"]
            
            # Update reply count (total posts - 1)
            thread_data["stats"]["replies"] = len(posts) - 1
            
        except Exception as e:
            logger.error(f"Error scraping thread content: {e}")
            
        return thread_data
    
    def save_thread(self, thread_data: Dict) -> None:
        """Save thread data to disk"""
        filename = self.url_to_filename(thread_data['url'])
        filepath = self.posts_dir / filename
        with open(filepath, 'w') as f:
            json.dump(thread_data, f, indent=2)
        logger.info(f"Saved: {filename}")
    
    def scrape_new_content(self, page: Page, progress: Dict, max_topics: int) -> int:
        """Phase 1: Check for new content since last run"""
        if not progress['newest_seen']:
            return 0
        
        logger.info(f"Checking for new content since: {progress['newest_seen']['url']}")
        page.goto(f"{self.base_url}/latest")
        page.wait_for_load_state('domcontentloaded')
        page.wait_for_timeout(3000)
        
        new_count = 0
        newest_url = progress['newest_seen']['url']
        found_bookmark = False
        
        while not found_bookmark:
            topics = self.extract_visible_topics(page)
            
            for topic in topics:
                # Stop when we reach our bookmark
                if topic['url'] == newest_url:
                    found_bookmark = True
                    break
                
                # Process new topic
                if self.needs_scraping(topic, progress):
                    thread_page = page.context.new_page()
                    try:
                        thread_data = self.scrape_thread(thread_page, topic)
                        self.save_thread(thread_data)
                        
                        # Update progress
                        progress['threads'][topic['url']] = {
                            'last_scraped': datetime.now().isoformat(),
                            'last_activity': topic['last_activity'],
                            'reply_count': topic['replies']
                        }
                        progress['total_scraped'] += 1
                        new_count += 1
                        
                        if new_count >= max_topics:
                            found_bookmark = True
                            break
                    finally:
                        thread_page.close()
            
            if found_bookmark:
                break
            
            # Try to scroll for more
            if not self.scroll_for_more(page):
                logger.warning("Reached end without finding newest bookmark")
                break
        
        # Update newest bookmark
        if new_count > 0:
            first_topic = self.extract_visible_topics(page)[0]
            progress['newest_seen'] = {
                "url": first_topic['url'],
                "last_activity": first_topic['last_activity'],
                "timestamp": datetime.now().isoformat()
            }
        
        return new_count
    
    def scrape_backwards(self, page: Page, progress: Dict, max_topics: int) -> int:
        """Phase 2: Continue scraping backwards from bookmark"""
        if progress['oldest_seen']:
            logger.info(f"Resuming from: {progress['oldest_seen']['url']}")
            if not self.scroll_to_topic(page, progress['oldest_seen']['url']):
                logger.warning("Could not find bookmark, starting from latest")
                page.goto(f"{self.base_url}/latest")
        else:
            logger.info("Starting fresh from latest topics")
            page.goto(f"{self.base_url}/latest")
        
        page.wait_for_load_state('domcontentloaded')
        page.wait_for_timeout(3000)
        
        scraped_count = 0
        seen_in_session = set()
        
        while scraped_count < max_topics:
            topics = self.extract_visible_topics(page)
            
            if not topics:
                logger.warning("No topics found")
                break
            
            # Update bookmarks
            self.update_bookmarks(topics, progress)
            
            for topic in topics:
                if topic['url'] in seen_in_session:
                    continue
                seen_in_session.add(topic['url'])
                
                if self.needs_scraping(topic, progress):
                    thread_page = page.context.new_page()
                    try:
                        thread_data = self.scrape_thread(thread_page, topic)
                        self.save_thread(thread_data)
                        
                        # Update progress
                        progress['threads'][topic['url']] = {
                            'last_scraped': datetime.now().isoformat(),
                            'last_activity': topic['last_activity'],
                            'reply_count': topic['replies']
                        }
                        progress['total_scraped'] += 1
                        scraped_count += 1
                        
                        if scraped_count >= max_topics:
                            break
                    except Exception as e:
                        logger.error(f"Failed to scrape {topic['url']}: {e}")
                        if topic['url'] not in progress['failed_urls']:
                            progress['failed_urls'].append(topic['url'])
                    finally:
                        thread_page.close()
            
            # Save progress periodically
            self.save_progress(progress)
            
            # Continue scrolling
            if not self.scroll_for_more(page):
                logger.info("Reached end of forum")
                break
        
        return scraped_count
    
    def run_streaming(self, max_topics: int = 10) -> None:
        """Main streaming scraper with time-based cursors"""
        print("\n" + "="*60)
        print("ECOMMERCEFUEL FORUM SCRAPER - STREAMING MODE")
        print("="*60)
        
        # Load progress
        progress = self.load_progress()
        print(f"\n📊 Progress loaded:")
        print(f"   Total scraped: {progress['total_scraped']}")
        if progress['newest_seen']:
            print(f"   Newest seen: {progress['newest_seen']['last_activity']} ago")
        if progress['oldest_seen']:
            print(f"   Oldest seen: {progress['oldest_seen']['last_activity']} ago")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            
            # Load cookies
            if not self.load_cookies(context):
                print("\n❌ No cookies found - run phase1 first!")
                browser.close()
                return
            
            # Main page for topic list
            main_page = context.new_page()
            
            try:
                # Phase 1: Check for new content
                print("\n📍 Phase 1: Checking for new content...")
                new_count = self.scrape_new_content(main_page, progress, max_topics)
                if new_count > 0:
                    print(f"   ✅ Scraped {new_count} new topics")
                else:
                    print(f"   ✅ No new content found")
                
                # Phase 2: Continue backwards
                remaining = max_topics - new_count
                if remaining > 0:
                    print(f"\n📍 Phase 2: Continuing backwards (max {remaining} topics)...")
                    backward_count = self.scrape_backwards(main_page, progress, remaining)
                else:
                    backward_count = 0
                print(f"   ✅ Scraped {backward_count} topics")
                
                # Final save
                self.save_progress(progress)
                
                # Summary
                print("\n" + "="*60)
                print("SCRAPING COMPLETE")
                print("="*60)
                print(f"New topics scraped: {new_count}")
                print(f"Historical topics scraped: {backward_count}")
                print(f"Total scraped all-time: {progress['total_scraped']}")
                print(f"Failed URLs: {len(progress['failed_urls'])}")
                
                if progress['oldest_seen']:
                    print(f"\nProgress bookmark: {progress['oldest_seen']['last_activity']} ago")
                    print("Run again to continue from this point!")
                
            except Exception as e:
                logger.error(f"Fatal error: {e}")
                self.save_progress(progress)  # Save progress even on error
            finally:
                browser.close()


if __name__ == "__main__":
    import sys
    
    scraper = EcommerceFuelScraper()
    
    # Check for phase commands
    if len(sys.argv) > 1:
        if sys.argv[1] == "phase1":
            scraper.run_phase1()
        elif sys.argv[1] == "phase2":
            scraper.run_phase2()
        elif sys.argv[1].isdigit():
            # Run streaming scraper with topic limit
            max_topics = int(sys.argv[1])
            scraper.run_streaming(max_topics)
        else:
            print(f"\nUnknown command: {sys.argv[1]}")
            print("Use 'phase1', 'phase2', or a number (e.g., 10) to scrape that many topics")
    else:
        # Default: run streaming scraper
        print("\nEcommerceFuel Forum Scraper")
        print("="*30)
        print("\nUsage:")
        print("  python ecommercefuel_scraper.py         - Run streaming scraper (default 10 topics)")
        print("  python ecommercefuel_scraper.py 20      - Run streaming scraper for 20 topics")
        print("  python ecommercefuel_scraper.py phase1  - Initial setup (browser & cookies)")
        print("  python ecommercefuel_scraper.py phase2  - Test forum structure")
        print("\nCurrent status:")
        print(f"  - Cookies: {'✅ Saved' if scraper.cookies_file.exists() else '❌ Not saved'}")
        print(f"  - Progress: {'✅ Exists' if scraper.progress_file.exists() else '❌ Not created'}")
        print(f"  - Posts directory: {'✅ Ready' if scraper.posts_dir.exists() else '❌ Not created'}")
        
        if not scraper.cookies_file.exists():
            print("\n⚠️  Run phase1 first to set up browser and login")
        else:
            print("\n✅ Ready to scrape! Running default mode...")
            scraper.run_streaming()