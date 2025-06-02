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
python ecommercefuel_scraper.py

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
  "last_scraped_at": "2024-01-06T12:00:00Z",
  "scraped_urls": [
    "/t/faire-is-doing-fulfillment/86921",
    "/t/my-first-ai-coding-project/86917"
  ],
  "failed_urls": [
    "/t/some-deleted-thread/12345"
  ],
  "scroll_position": 150,
  "total_scraped": 523
}
```

## ✅ Phase Checklist

- [ ] **Phase 1**: Browser Setup & Cookie Persistence
  - [ ] 1.1 Basic Browser Launch
  - [ ] 1.2 Cookie Management
  - [ ] 1.3 Login Flow
- [ ] **Phase 2**: Forum Structure Discovery
  - [ ] 2.1 Topic List Structure
  - [ ] 2.2 Post Data Extraction
  - [ ] 2.3 Infinite Scroll Detection
- [ ] **Phase 3**: Infinite Scroll Implementation
  - [ ] 3.1 Basic Scroll Test
  - [ ] 3.2 Deduplication Strategy
  - [ ] 3.3 Scroll Completion Detection
- [ ] **Phase 4**: Individual Post Scraping
  - [ ] 4.1 Thread Navigation
  - [ ] 4.2 Reply Extraction
  - [ ] 4.3 Thread Pagination
- [ ] **Phase 5**: Output & Resume Strategy
  - [ ] 5.1 File Naming
  - [ ] 5.2 Progress Tracking
  - [ ] 5.3 Data Validation
- [ ] **Phase 6**: Full Implementation
  - [ ] 6.1 Main Script Structure
  - [ ] 6.2 Error Handling
  - [ ] 6.3 Performance Tuning

## 🎯 What We're Building

We need a simple, elegant Playwright-based scraper for the EcommerceFuel forum that:

1. **Handles Authentication**: Uses persistent cookies so you only log in once manually
2. **Scrapes Everything**: Gets all forum posts and their complete reply threads
3. **Captures Author Data**: For each post/reply, capture all visible author information:
   - Username and display name
   - Post count
   - Join date
   - Any badges or status indicators
   - Profile information visible on the post itself (NO following links)
4. **Manages Infinite Scroll**: The forum uses endless scrolling, not pagination - we need to handle this elegantly
5. **Saves Incrementally**: Each post saved as a separate JSON file so we can resume if interrupted
6. **No Database**: Just JSON files - one for cookies, one for progress, one per forum post

The key insight from our existing experiments: The forum uses Discourse with infinite scroll (`.loading-container` appears when loading more). We have working selectors for posts, but need to validate them against the live site.

Each phase below has explicit **🛑 STOP** points where we'll run code, inspect results, and adjust before continuing. This is an iterative discovery process, not a waterfall implementation.

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

1. **Infinite Scroll**: Forum uses `.loading-container` indicator
2. **Login Check**: Multiple possible selectors, need to verify
3. **View Counts**: Can have 'k' suffix (e.g., "1.2k" = 1200)
4. **URL Structure**: Relative URLs need base URL prepended
5. **Post Elements**: `.cooked` class contains post HTML content

## 🚨 Critical Decision Points

Each **🛑 STOP** represents a point where we need to:
1. Run actual code against the live site
2. Inspect results
3. Adjust approach based on findings
4. Document what we learned

This is NOT a straight-through implementation - it's an iterative discovery process.