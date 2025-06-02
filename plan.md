# 🏗️ Unified Scraping & Ingestion Architecture

## 🎯 Architecture Overview

This plan creates a unified architecture for scraping forums and ingesting content into LightRAG, following our North Star principles of simplicity and elegance.

### Data Flow
```
Forum → Scraper → JSON → Converter → Plain Text → Ingestion Pipeline → LightRAG
```

### Directory Structure
```
scraping/
├── base_scraper.py           # Abstract base class for all forum scrapers
├── converters/               # JSON to text converters
│   ├── base_converter.py     # Abstract converter interface
│   └── discourse_converter.py # Discourse forum converter
├── scrapers/                 # Forum-specific scrapers
│   └── ecommercefuel.py      # EcommerceFuel implementation
├── data/                     # Scraped data organized by source
│   └── ecommercefuel/        
│       ├── raw/              # Raw JSON posts
│       ├── progress.json     # Scraping progress
│       └── cookies.json      # Session cookies
└── scrape.py                 # Unified CLI interface

content/
├── transcripts/              # Converted plain text ready for LightRAG
└── [existing pipeline dirs]  # inbox, downloading, etc.
```

## 🏛️ Core Architecture

### 1. Base Scraper Pattern

```python
# scraping/base_scraper.py
from abc import ABC, abstractmethod
from pathlib import Path
import json
import logging

class BaseScraper(ABC):
    """Abstract base class for all forum scrapers"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.raw_dir = data_dir / "raw"
        self.progress_file = data_dir / "progress.json"
        self.cookies_file = data_dir / "cookies.json"
        
        # Ensure directories exist
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        
        # Load progress
        self.progress = self.load_progress()
        
    @abstractmethod
    def scrape(self, limit: int = None) -> int:
        """Scrape forum and return number of posts scraped"""
        pass
        
    @abstractmethod
    def get_converter(self) -> 'BaseConverter':
        """Return the appropriate converter for this scraper's data"""
        pass
        
    def load_progress(self) -> dict:
        """Load scraping progress"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return self.default_progress()
        
    @abstractmethod
    def default_progress(self) -> dict:
        """Return default progress structure"""
        pass
        
    def save_progress(self):
        """Save current progress"""
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)
```

### 2. Base Converter Pattern

```python
# scraping/converters/base_converter.py
from abc import ABC, abstractmethod
from pathlib import Path
import hashlib

class BaseConverter(ABC):
    """Abstract base class for converting scraped data to plain text"""
    
    @abstractmethod
    def convert(self, json_path: Path) -> str:
        """Convert a single JSON file to plain text format"""
        pass
        
    def generate_filename(self, content: dict) -> str:
        """Generate a safe, unique filename"""
        # Use content hash to ensure uniqueness
        content_hash = hashlib.md5(
            json.dumps(content, sort_keys=True).encode()
        ).hexdigest()[:8]
        
        # Create readable filename
        title = content.get('title', 'untitled')
        safe_title = re.sub(r'[^a-zA-Z0-9-_]', '_', title)[:50]
        
        return f"{safe_title}_{content_hash}.txt"
```

### 3. Unified CLI Interface

```python
# scraping/scrape.py
import click
from pathlib import Path
from scrapers import get_scraper
from converters import get_converter

@click.command()
@click.argument('source', type=click.Choice(['ecommercefuel', 'other_forum']))
@click.option('--limit', type=int, help='Maximum posts to scrape')
@click.option('--convert', is_flag=True, help='Convert after scraping')
@click.option('--output-dir', default='../content/transcripts', 
              help='Output directory for converted files')
def scrape(source, limit, convert, output_dir):
    """Unified scraping interface"""
    # Get appropriate scraper
    scraper = get_scraper(source)
    
    # Scrape
    count = scraper.scrape(limit=limit)
    click.echo(f"Scraped {count} posts from {source}")
    
    # Convert if requested
    if convert:
        converter = scraper.get_converter()
        output_path = Path(output_dir)
        
        converted = 0
        for json_file in scraper.raw_dir.glob('*.json'):
            text = converter.convert(json_file)
            filename = converter.generate_filename(json.load(open(json_file)))
            
            (output_path / filename).write_text(text)
            converted += 1
            
        click.echo(f"Converted {converted} posts to {output_path}")
```

## 🔄 Integration Points

### 1. EcommerceFuel Integration

Refactor existing scraper to follow base pattern:

```python
# scraping/scrapers/ecommercefuel.py
from ..base_scraper import BaseScraper
from ..converters.discourse_converter import DiscourseConverter

class EcommerceFuelScraper(BaseScraper):
    def __init__(self):
        super().__init__(Path('data/ecommercefuel'))
        self.base_url = 'https://forum.ecommercefuel.com'
        
    def get_converter(self):
        return DiscourseConverter()
        
    def scrape(self, limit=None):
        # Move existing implementation here
        # Key changes:
        # - Save to self.raw_dir instead of posts/
        # - Use self.progress instead of local progress
        # - Return count of scraped posts
        pass
```

### 2. Discourse Converter

Convert Discourse forum JSON to clean text:

```python
# scraping/converters/discourse_converter.py
from ..base_converter import BaseConverter

class DiscourseConverter(BaseConverter):
    def convert(self, json_path: Path) -> str:
        """Convert Discourse forum post to plain text"""
        with open(json_path) as f:
            data = json.load(f)
            
        # Build header
        lines = [
            f"Title: {data['title']}",
            f"URL: {data['url']}",
            f"Category: {data['category']}",
            f"Tags: {', '.join(data.get('tags', []))}",
            f"Created: {data['created_at']}",
            f"Last Activity: {data['stats']['last_activity']}",
            "",
            "===== Discussion =====",
            ""
        ]
        
        # Convert posts to conversation format
        for post in data['posts']:
            author = post['author']['display_name']
            lines.extend([
                f"{author} ({post['author']['badges']}):",
                post['content_text'],
                ""
            ])
            
        return "\n".join(lines)
```

### 3. Ingestion Pipeline Integration

No changes needed! The existing pipeline already:
- Monitors `content/transcripts/` for new files
- Loads them into LightRAG with proper source attribution
- Tracks processing status

## 📋 Implementation Steps

### Phase 1: Core Architecture
- [ ] Create `base_scraper.py` with abstract interface
- [ ] Create `base_converter.py` with abstract interface
- [ ] Set up new directory structure
- [ ] Create unified CLI with click

### Phase 2: EcommerceFuel Migration
- [ ] Refactor existing scraper to inherit from BaseScraper
- [ ] Move data to new directory structure
- [ ] Implement DiscourseConverter
- [ ] Test end-to-end flow

### Phase 3: Pipeline Integration
- [ ] Run converter on existing scraped data
- [ ] Verify files appear in content/transcripts/
- [ ] Confirm ingestion pipeline processes them
- [ ] Test LightRAG queries return forum content

### Phase 4: Documentation
- [ ] Update scraping/README.md with new architecture
- [ ] Document how to add new forum scrapers
- [ ] Add examples of extending base classes

## 🎯 Benefits of This Architecture

1. **Simplicity**: One pattern for all scrapers
2. **Extensibility**: Easy to add new forums
3. **Separation of Concerns**: Scraping vs conversion
4. **Integration**: Works with existing ingestion pipeline
5. **Maintainability**: Changes to base class benefit all scrapers
6. **Testability**: Can test converters independently

## 🚫 What We're NOT Doing

1. **No Database**: Just JSON files and progress tracking
2. **No Complex Formats**: Plain text output only
3. **No Over-Engineering**: Simple base classes, no frameworks
4. **No Breaking Changes**: Existing pipeline continues to work
5. **No Manual Steps**: Fully automated from scrape to LightRAG

---

# 🕷️ EcommerceFuel Forum Scraper - Detailed Implementation Plan

## 🌟 North Star Principles

1. **Simplify, Simplify, Simplify**: Every decision should make the code simpler, not more complex
2. **No Cruft**: Remove all redundant code, validation, and unnecessary complexity
3. **Break It & Fix It Right**: No backwards compatibility shims - make breaking changes and migrate properly
4. **Long-term Elegance**: Choose performant, compiler-enforced solutions that prevent subtle bugs
5. **Backend-Driven**: Let the backend handle complexity, frontend should be a thin client
6. **Single Source of Truth**: One pattern, one way to do things, no alternatives
7. **No Over-Engineering**: Design for current needs only - no hypothetical features, no "maybe later" code
8. **Thoughtful Logging & Instrumentation**: We value visibility into system behavior with appropriate log levels

## 📁 Target Implementation Structure

```
scraping/
├── ecommercefuel_scraper.py      # Main scraper script
├── cookies.json                  # Persistent cookie storage (auto-created)
├── progress.json                 # Scraping progress tracker (auto-created)
├── posts/                        # Scraped post data
│   ├── t_86921_faire-is-doing-fulfillment.json
│   ├── t_86917_my-first-ai-coding-project.json
│   ├── t_82309_klaviyo-suddenly-inflating.json
│   └── ... (one file per forum thread)
└── logs/
    └── scraper_2025-01-06.log   # Daily log files

# Usage:
python ecommercefuel_scraper.py           # Run full scraper
python ecommercefuel_scraper.py --days 30 # Scrape last 30 days only

# Files created automatically:
- cookies.json: After first login
- progress.json: Tracks scraped URLs and position
- posts/*.json: One per forum thread with all replies
```

### Sample Post JSON Structure
```json
{
  "url": "/t/faire-is-doing-fulfillment/86921",
  "title": "Faire Is Doing Fulfillment?",
  "category": "Channels",
  "tags": ["b2b", "experience-share", "wholesale"],
  "created_at": "2024-01-05T14:30:00Z",
  "author": {
    "username": "BethSnyder",
    "display_name": "Beth Snyder",
    "post_count": 234,
    "join_date": "Oct 2019",
    "trust_level": 3,
    "badges": ["Regular"]
  },
  "stats": {
    "replies": 7,
    "views": 27,
    "likes": 5,
    "last_activity": "2024-01-06T10:15:00Z"
  },
  "posts": [
    {
      "index": 0,
      "author": {
        "username": "BethSnyder",
        "display_name": "Beth Snyder",
        "post_count": 234,
        "join_date": "Oct 2019",
        "trust_level": 3,
        "badges": ["Regular"]
      },
      "content_html": "<p>Original post content...</p>",
      "content_text": "Original post content...",
      "timestamp": "2024-01-05T14:30:00Z",
      "likes": 3,
      "is_original": true
    },
    {
      "index": 1,
      "author": {
        "username": "JohnDoe",
        "display_name": "John Doe",
        "post_count": 567,
        "join_date": "Mar 2018",
        "trust_level": 4,
        "badges": ["Leader", "Anniversary"]
      },
      "content_html": "<p>Reply content...</p>",
      "content_text": "Reply content...",
      "timestamp": "2024-01-05T15:45:00Z",
      "likes": 1,
      "is_original": false
    }
  ],
  "scraped_at": "2024-01-06T12:00:00Z"
}
```

### Progress JSON Structure
```json
{
  "last_run": "2024-01-06T12:00:00Z",
  "newest_seen": {
    "url": "/t/latest-thread/99999",
    "last_activity": "5m",
    "timestamp": "2024-01-06T11:55:00Z"
  },
  "oldest_seen": {
    "url": "/t/older-thread/88888",
    "last_activity": "45d",
    "timestamp": "2024-01-06T10:00:00Z"
  },
  "threads": {
    "/t/faire-is-doing-fulfillment/86921": {
      "last_scraped": "2024-01-05T10:00:00Z",
      "last_activity": "13m",
      "reply_count": 7
    },
    "/t/my-first-ai-coding-project/86917": {
      "last_scraped": "2024-01-06T09:00:00Z", 
      "last_activity": "2h",
      "reply_count": 12
    }
  },
  "failed_urls": [],
  "total_scraped": 523
}
```

### Simple Update Logic
- **New thread**: Not in progress.json → Scrape it
- **Active thread**: last_activity changed → Re-scrape it  
- **Inactive thread**: last_activity same → Skip it
- **Failed thread**: In failed_urls → Retry once per run

### 🎯 Time-Based Cursor Architecture (The Elegant Solution)

**Problem with Batch Approach**: Trying to scroll through 20 years of forum posts BEFORE scraping any threads is insane.

**Solution: Time-Based Cursor with Stream Processing**

The forum isn't moving so fast that we can't catch up. We should always be making progress backwards through time:

1. **Track Progress with Bookmarks**:
   - `newest_seen`: The newest topic we've processed
   - `oldest_seen`: How far back we've gone (our bookmark)

2. **Two-Phase Approach**:
   ```python
   def scrape_forum():
       progress = load_progress()
       
       # Phase 1: Catch up on new content since last run
       if progress['newest_seen']:
           new_topics = scrape_until_seen(progress['newest_seen'])
           process_topics(new_topics)
       
       # Phase 2: Continue backwards from our bookmark
       if progress['oldest_seen']:
           scroll_to_bookmark(progress['oldest_seen'])
       
       # Keep going backwards in time
       while not reached_time_limit():
           topics = get_visible_topics()
           process_topics(topics)
           update_oldest_seen(topics[-1])
           scroll_for_more()
   ```

3. **Tab Management**: Keep topic list in main tab, open threads in new tabs
4. **Always Making Progress**: Every run moves us further back in time
5. **Never Miss New Content**: Always check for new posts first

### Thread Tracking Strategy
The key insight: We track `last_activity` from the topic list (e.g., "13m", "2h", "3d") along with when we last scraped each thread. This gives us a simple decision tree:

1. **As We Scroll** (Streaming):
   - See a topic with URL and last_activity
   - Check progress.json: Is it new? Has activity changed?
   - If yes → Scrape it immediately in a new tab
   - If no → Skip and continue scrolling

2. **Example Flow**:
   ```
   Scroll → See topic: /t/some-thread/123 with last_activity: "2h"
   Check progress.json: last_activity: "2h" 
   → Skip (no change)
   
   Scroll → See topic: /t/other-thread/456 with last_activity: "15m"
   Check progress.json: Not found
   → Open new tab, scrape thread, close tab, continue scrolling
   ```

## ✅ Phase Checklist

- [x] **Phase 1**: Browser Setup & Cookie Persistence ✅ IMPLEMENTED
  - [x] 1.1 Basic Browser Launch
  - [x] 1.2 Cookie Management
  - [x] 1.3 Login Flow
- [x] **Phase 2**: Forum Structure Discovery ✅ IMPLEMENTED
  - [x] 2.1 Topic List Structure
  - [x] 2.2 Post Data Extraction (Note: Author extraction needs fixing)
  - [x] 2.3 Infinite Scroll Detection
- [x] **Phase 3-5**: Streaming Implementation ✅ INTEGRATED
  - [x] 3.1 Fix Author Extraction (selector: img.avatar + data-user-card) 
  - [x] 3.2 Time-Based Cursor Tracking (newest_seen, oldest_seen)
  - [x] 3.3 Stream Processing (scrape as we scroll)
  - [x] 3.4 Tab Management (main tab + thread tabs)
  - [x] 5.1 Progress Tracking with Bookmarks
  - [x] 5.2 Two-Phase Scraping (catch up on new, continue backwards)
  - [x] 5.3 Scroll Position Recovery (find bookmark after restart)
  - [x] 5.4 Single Source of Truth (all in main scraper)
- [x] **Phase 6**: Full Implementation ✅ COMPLETE
  - [x] 6.1 Combined streaming approach in main scraper
  - [x] 6.2 Simple command line: `python scraper.py [num_topics]`
  - [x] 6.3 Error handling with progress saves and resume capability

## 🎯 What We're Building

We need a simple, elegant Playwright-based scraper for the EcommerceFuel forum that:

1. **Handles Authentication**: Uses persistent cookies so you only log in once manually
2. **Scrapes Intelligently**: Stream processes topics as it scrolls, not batch collection
3. **Captures Author Data**: For each post/reply, capture all visible author information
4. **Manages Infinite Scroll**: Uses tab-based approach to maintain scroll position
5. **Saves Incrementally**: Each post saved immediately after scraping
6. **No Database**: Just JSON files - one for cookies, one for progress, one per forum post

## ⚠️ Critical Architecture Decision

**❌ WRONG: Batch Processing (Current Implementation)**
```
1. Scroll through ALL topics (could be 20 years worth!)
2. Save list of 10,000+ topics to memory
3. Go back and scrape each thread
Problem: Forum could have millions of posts. This will never complete.
```

**✅ RIGHT: Time-Based Cursor with Stream Processing**
```
First Run:
1. Start at latest topics
2. Scrape as you scroll backwards
3. Save bookmark of oldest topic seen
4. Can stop anytime

Subsequent Runs:
1. Check for new content since newest_seen bookmark
2. Process any new topics
3. Resume from oldest_seen bookmark
4. Continue backwards through time
5. Always making progress into the past
```

**Why Streaming?** Because trying to scroll through potentially 20 years of forum history before scraping a single thread is fundamentally broken. We need to process topics as we encounter them.

The key insight from our existing experiments: The forum uses Discourse with infinite scroll (`.loading-container` appears when loading more). We have working selectors for posts, but need to refactor to streaming approach.

---

## Phase 5: Time-Based Cursor Implementation (Priority)

**Goal**: Implement elegant time-based cursor with stream processing

### 5.1 Progress Tracking with Bookmarks
```python
def load_progress_with_bookmarks(self) -> Dict:
    """Enhanced progress tracking with time-based cursors"""
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

def update_bookmarks(self, topics: List[Dict]) -> None:
    """Update our position bookmarks"""
    if topics:
        # Update newest if this is newer
        if not self.progress['newest_seen'] or self.is_newer(topics[0], self.progress['newest_seen']):
            self.progress['newest_seen'] = {
                "url": topics[0]['url'],
                "last_activity": topics[0]['last_activity'],
                "timestamp": datetime.now().isoformat()
            }
        
        # Update oldest - we're always moving backwards
        self.progress['oldest_seen'] = {
            "url": topics[-1]['url'],
            "last_activity": topics[-1]['last_activity'],
            "timestamp": datetime.now().isoformat()
        }
```

### 5.2 Two-Phase Scraping Logic
```python
def scrape_forum(self):
    """Main scraping logic with time-based cursor"""
    progress = self.load_progress_with_bookmarks()
    
    # Phase 1: Catch up on new content
    if progress['newest_seen']:
        logger.info(f"Checking for new content since {progress['newest_seen']['url']}")
        new_topics = self.scrape_new_content(progress['newest_seen'])
        self.process_topics(new_topics)
    
    # Phase 2: Continue backwards from bookmark
    if progress['oldest_seen']:
        logger.info(f"Continuing from bookmark: {progress['oldest_seen']['url']}")
        self.scroll_to_topic(progress['oldest_seen']['url'])
    else:
        logger.info("Starting fresh from latest topics")
        self.main_page.goto(f"{self.base_url}/latest")
    
    # Keep going backwards in time
    self.scrape_backwards()

def scrape_new_content(self, newest_seen: Dict) -> List[Dict]:
    """Scrape any new content since our last run"""
    new_topics = []
    self.main_page.goto(f"{self.base_url}/latest")
    
    while True:
        topics = self.extract_visible_topics()
        
        for topic in topics:
            # Stop when we reach content we've seen
            if topic['url'] == newest_seen['url']:
                return new_topics
            new_topics.append(topic)
        
        # Scroll for more
        if not self.scroll_for_more():
            break
    
    return new_topics

def scrape_backwards(self):
    """Continue scraping backwards through time"""
    seen_in_session = set()
    
    while True:
        topics = self.extract_visible_topics()
        
        for topic in topics:
            if topic['url'] in seen_in_session:
                continue
            seen_in_session.add(topic['url'])
            
            if self.needs_scraping(topic):
                # Open in new tab to preserve scroll position
                thread_page = self.context.new_page()
                try:
                    thread_data = self.scrape_thread(thread_page, topic)
                    self.save_thread(thread_data)
                    self.update_thread_progress(topic)
                finally:
                    thread_page.close()
        
        # Update our bookmark
        self.update_bookmarks(topics)
        self.save_progress(self.progress)
        
        # Continue scrolling
        if not self.scroll_for_more():
            logger.info("Reached end of forum")
            break
```

### 5.3 Scroll Position Management
```python
def scroll_to_topic(self, target_url: str) -> bool:
    """Scroll until we find a specific topic"""
    max_scrolls = 100  # Safety limit
    scrolls = 0
    
    while scrolls < max_scrolls:
        topics = self.extract_visible_topics()
        
        # Check if target is visible
        for topic in topics:
            if topic['url'] == target_url:
                logger.info(f"Found bookmark topic after {scrolls} scrolls")
                return True
        
        # Scroll for more
        if not self.scroll_for_more():
            logger.warning("Reached end without finding bookmark")
            return False
        
        scrolls += 1
    
    logger.warning(f"Bookmark not found after {max_scrolls} scrolls")
    return False
```

**🛑 STOP**: Test bookmark system - ensure we can resume from exact position

---

## Phase 1: Browser Setup & Cookie Persistence
**Goal**: Get Playwright running with cookie persistence

### 1.1 Basic Browser Launch
```python
# Test basic browser launch
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto('https://forum.ecommercefuel.com')
    input("Press Enter to close...")
    browser.close()
```

**🛑 STOP**: Verify browser launches and loads forum

### 1.2 Cookie Management
```python
# Test cookie save/load
import json
import os

def save_cookies(page):
    cookies = page.context.cookies()
    json.dump(cookies, open('cookies.json', 'w'))

def load_cookies(context):
    if os.path.exists('cookies.json'):
        cookies = json.load(open('cookies.json'))
        context.add_cookies(cookies)
```

**🛑 STOP**: Test saving and loading cookies manually

### 1.3 Login Flow
```python
# Check login status - need to find right selector
def is_logged_in(page):
    # Try multiple selectors from our research:
    # - '[data-user-menu]'
    # - 'button:has-text("New Topic")'
    # - '.user-menu'
    # Test which one works!
```

**🛑 STOP**: Manually test selectors in browser console to find correct login indicator

---

## Phase 2: Forum Structure Discovery
**Goal**: Understand the forum's HTML structure through exploration

### 2.1 Topic List Structure
```python
# Navigate to latest posts
page.goto('https://forum.ecommercefuel.com/latest')

# Explore possible table selectors:
# - 'table[aria-label*="topics"]'
# - 'table.topic-list'
# - '.topic-list-item'
# - 'tbody tr'
```

**🛑 STOP**: Use browser DevTools to inspect actual structure and test selectors

### 2.2 Post Data Extraction
For each post row in the topic list, identify selectors for:
- Title: `h2 a`, `.topic-link`, `a.title`
- Author: `td:first-child a`, `.topic-poster a`
- Category: `a[href*="/c/"]`, `.category-name`
- Tags: `a[href*="/tag/"]`
- Reply count: Which cell? What format?
- View count: Look for 'k' suffix handling
- Last activity: Relative time format

Note: In the topic list, we typically only see basic author info (username). The detailed author data (post count, join date, etc.) is usually only visible when viewing the full thread.

**🛑 STOP**: Create sample extraction for 5 posts, verify data quality

### 2.3 Infinite Scroll Detection
```python
# From our research, the forum uses infinite scroll
# Look for:
# - '.loading-container' when loading
# - No "Next" button, just scroll detection
# - New rows appear in the table
```

**🛑 STOP**: Manually scroll and observe network requests, DOM changes

---

## Phase 3: Infinite Scroll Implementation
**Goal**: Reliable scroll handling without missing posts

### 3.1 Basic Scroll Test
```python
def scroll_once(page):
    # Get initial row count
    before = len(page.locator('tbody tr').all())
    
    # Scroll to bottom
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    
    # Wait for loader
    loader = page.locator('.loading-container')
    if loader.is_visible():
        loader.wait_for(state='hidden')
    
    # Check new row count
    after = len(page.locator('tbody tr').all())
    return after > before
```

**🛑 STOP**: Test scroll behavior, timing, edge cases

### 3.2 Deduplication Strategy
```python
seen_urls = set()

def extract_new_posts(page, seen_urls):
    all_rows = page.locator('tbody tr').all()
    new_posts = []
    
    for row in all_rows:
        url = row.locator('a.title').get_attribute('href')
        if url not in seen_urls:
            seen_urls.add(url)
            new_posts.append(extract_post_data(row))
    
    return new_posts
```

**🛑 STOP**: Verify no duplicates, no missed posts during scrolling

### 3.3 Scroll Completion Detection
- No new posts after scroll?
- Specific element appears at end?
- Maximum scroll count as safety?

**🛑 STOP**: Determine reliable end-of-content detection

---

## Phase 4: Individual Post Scraping
**Goal**: Extract full thread content including all replies

### 4.1 Thread Navigation
```python
# Test navigation to individual thread
post_url = '/t/some-thread/12345'
page.goto(f'https://forum.ecommercefuel.com{post_url}')

# Wait for content - what's the right selector?
# - '.post-stream'
# - '.topic-post'
# - '.cooked'
```

**🛑 STOP**: Verify thread pages load correctly

### 4.2 Reply Extraction
```python
# Identify post structure:
# - Original post vs replies
# - Author info location:
#   - Username/display name
#   - Post count (often shown as "Posts: 1,234")
#   - Join date (e.g. "Joined: Oct 2019")
#   - Badges/trust level
#   - Any other visible profile data
# - Content container
# - Timestamp format
# - Like counts
# - Nested quotes?

# Example author data structure:
{
    "username": "JohnDoe",
    "display_name": "John Doe",
    "post_count": 1234,
    "join_date": "Oct 2019",
    "badges": ["Regular", "Contributor"],
    "trust_level": 3,
    "avatar_url": "/path/to/avatar.png"
}
```

**🛑 STOP**: Map out complete post data structure including all visible author information

### 4.3 Thread Pagination
Some threads might have multiple pages:
- Look for pagination controls
- Or more infinite scroll?
- How to ensure we get all replies?

**🛑 STOP**: Test with long threads (50+ replies)

---

## Phase 5: Output & Resume Strategy
**Goal**: Save data intelligently, allow resumption

### 5.1 File Naming
```python
# From URL: /t/building-an-online-store/12345
# Generate: posts/t_12345_building-an-online-store.json

def url_to_filename(url):
    # Extract slug and ID
    # Handle special characters
    # Ensure uniqueness
```

**🛑 STOP**: Test filename generation with various URL formats

### 5.2 Progress Tracking
```python
# Simple JSON progress file
{
    "topic_list_scroll_position": 150,
    "scraped_post_urls": [...],
    "failed_urls": [...],
    "last_run": "2024-01-06T10:30:00"
}
```

**🛑 STOP**: Test resume scenarios

### 5.3 Data Validation
- Required fields present?
- HTML properly extracted?
- Character encoding issues?
- Image/attachment handling?

**🛑 STOP**: Validate sample of 10 posts thoroughly

---

## Phase 6: Full Implementation
**Goal**: Combine all pieces into working scraper

### 6.1 Main Script Structure
```python
async def main():
    # 1. Setup browser with cookies
    # 2. Check login
    # 3. Scrape topic list
    # 4. For each new topic, scrape full content
    # 5. Save progress regularly
    # 6. Handle interruptions gracefully
```

### 6.2 Error Handling
- Network timeouts
- Page structure changes
- Login session expiry
- Partial data extraction

### 6.3 Performance Tuning
- Concurrent page scraping?
- Request delays?
- Memory usage with many posts?

---

## 📝 Known Issues From Research

1. **Infinite Scroll**: Forum uses `.loading-container` indicator ✅ CONFIRMED
2. **Login Check**: Multiple possible selectors, need to verify
3. **View Counts**: Can have 'k' suffix (e.g., "1.2k" = 1200)
4. **URL Structure**: Relative URLs need base URL prepended
5. **Post Elements**: `.cooked` class contains post HTML content
6. **Author Extraction**: Topic list author selector `td:first-child a` returns empty - need to use `img.avatar` with `data-user-card` attribute instead ✅ FIXED
7. **Topic Stats**: Last 3 cells contain replies, views, and last_activity time
8. **Forum Size**: Forum has THOUSANDS of topics (possibly 20+ years worth) - batch processing is impossible ⚠️ CRITICAL
9. **Scroll Performance**: ~30 topics load per scroll, taking 10-20 seconds each - streaming is essential

## 🚨 Critical Decision Points

Each **🛑 STOP** represents a point where we need to:
1. Run actual code against the live site
2. Inspect results
3. Adjust approach based on findings
4. Document what we learned

This is NOT a straight-through implementation - it's an iterative discovery process.