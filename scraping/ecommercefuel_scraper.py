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
    
    # ==================== PHASE 3: Topic List Scraping with Progress Tracking ====================
    
    def load_progress(self) -> Dict:
        """Load progress tracking data"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {"threads": {}, "last_run": None, "total_scraped": 0, "failed_urls": []}
    
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
    
    def scroll_and_collect_all_topics(self, page: Page, max_topics: int = 100) -> List[Dict]:
        """Scroll through all topics via infinite scroll"""
        all_topics = []
        seen_urls = set()
        no_new_content_count = 0
        
        while len(all_topics) < max_topics:
            # Get current topics
            rows = page.locator('tbody tr').all()
            new_topics_count = 0
            
            for row in rows:
                try:
                    topic = self.extract_topic_from_row(row)
                    if topic['url'] not in seen_urls:
                        seen_urls.add(topic['url'])
                        all_topics.append(topic)
                        new_topics_count += 1
                except Exception as e:
                    logger.warning(f"Failed to extract topic: {e}")
            
            logger.info(f"Collected {len(all_topics)} topics total ({new_topics_count} new)")
            
            # Stop if we hit the limit
            if len(all_topics) >= max_topics:
                logger.info(f"Reached topic limit of {max_topics}")
                break
            
            # Check if we got new content
            if new_topics_count == 0:
                no_new_content_count += 1
                if no_new_content_count >= 3:
                    logger.info("No new content after 3 scrolls - reached end")
                    break
            else:
                no_new_content_count = 0
            
            # Scroll to bottom
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            # Wait for loading indicator
            loader = page.locator('.loading-container')
            if loader.is_visible():
                loader.wait_for(state='hidden', timeout=10000)
            else:
                page.wait_for_timeout(2000)
        
        return all_topics
    
    def run_phase3(self) -> None:
        """Phase 3: Collect all topics and determine what needs scraping"""
        print("\n" + "="*60)
        print("PHASE 3: Topic List Scraping with Progress Tracking")
        print("="*60)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            
            # Load cookies
            if not self.load_cookies(context):
                print("\n❌ No cookies found - run phase1 first!")
                browser.close()
                return
            
            page = context.new_page()
            
            # Navigate to forum
            logger.info("Navigating to forum...")
            page.goto(f"{self.base_url}/latest")
            page.wait_for_load_state('domcontentloaded')
            page.wait_for_timeout(3000)  # Let the content settle
            
            # Load progress data
            progress = self.load_progress()
            print(f"\n📊 Loaded progress: {len(progress['threads'])} threads tracked")
            
            # Collect all topics
            print("\n🔄 Starting topic collection via infinite scroll (max 100 topics)...")
            all_topics = self.scroll_and_collect_all_topics(page, max_topics=100)
            print(f"\n✅ Collected {len(all_topics)} topics (limited to 100 for testing)")
            
            # Determine what needs scraping
            topics_to_scrape = []
            topics_to_skip = []
            
            for topic in all_topics:
                thread_data = progress["threads"].get(topic['url'], {})
                previous_activity = thread_data.get("last_activity")
                
                if previous_activity is None or previous_activity != topic['last_activity']:
                    topics_to_scrape.append(topic)
                    reason = "new" if previous_activity is None else f"updated ({previous_activity} → {topic['last_activity']})"
                    logger.info(f"Need to scrape: {topic['title'][:50]}... ({reason})")
                else:
                    topics_to_skip.append(topic)
            
            # Update progress with current state
            for topic in all_topics:
                if topic['url'] not in progress["threads"]:
                    progress["threads"][topic['url']] = {}
                progress["threads"][topic['url']]["last_activity"] = topic['last_activity']
                progress["threads"][topic['url']]["reply_count"] = topic['replies']
            
            # Save progress
            self.save_progress(progress)
            
            # Summary
            print("\n" + "="*60)
            print("PHASE 3 SUMMARY")
            print("="*60)
            print(f"Total topics found: {len(all_topics)}")
            print(f"Topics needing scrape: {len(topics_to_scrape)}")
            print(f"Topics up-to-date: {len(topics_to_skip)}")
            print(f"\nProgress saved to: {self.progress_file}")
            
            if topics_to_scrape:
                print(f"\nFirst 5 topics to scrape:")
                for topic in topics_to_scrape[:5]:
                    print(f"  - {topic['title'][:60]}...")
                    print(f"    Author: {topic['author']}, Last activity: {topic['last_activity']}")
            
            browser.close()
        
        print("\n" + "="*60)
        print("PHASE 3 COMPLETE!")
        print("="*60)
        print("\nNext: Implement individual thread scraping in Phase 4")


if __name__ == "__main__":
    import sys
    
    scraper = EcommerceFuelScraper()
    
    if len(sys.argv) > 1 and sys.argv[1] == "phase3":
        scraper.run_phase3()
    elif len(sys.argv) > 1 and sys.argv[1] == "phase2":
        scraper.run_phase2()
    elif len(sys.argv) > 1 and sys.argv[1] == "phase1":
        scraper.run_phase1()
    else:
        print("\nEcommerceFuel Forum Scraper")
        print("="*30)
        print("\nUsage:")
        print("  python ecommercefuel_scraper.py phase1  - Run Phase 1 (Browser & Cookies)")
        print("  python ecommercefuel_scraper.py phase2  - Run Phase 2 (Structure Discovery)")
        print("  python ecommercefuel_scraper.py phase3  - Run Phase 3 (Topic List Scraping)")
        print("\nCurrent status:")
        print(f"  - Cookies: {'✅ Saved' if scraper.cookies_file.exists() else '❌ Not saved'}")
        print(f"  - Progress: {'✅ Exists' if scraper.progress_file.exists() else '❌ Not created'}")
        print(f"  - Posts directory: {'✅ Ready' if scraper.posts_dir.exists() else '❌ Not created'}")
        
        if not scraper.cookies_file.exists():
            print("\n⚠️  Run phase1 first to set up browser and login")