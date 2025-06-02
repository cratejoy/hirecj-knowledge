# EcommerceFuel Forum Scraper

An elegant, production-ready forum scraper with browser automation, session persistence, and real-time monitoring.

## Features

- 🌐 **Browser Automation**: Uses Playwright for reliable scraping of JavaScript-heavy content
- 🔐 **Session Management**: Saves cookies between runs, handles login detection
- 📊 **Real-time Monitoring**: Visual dashboard showing scraping progress
- 🎮 **Control Interface**: Pause, resume, and control scraping in real-time
- 💾 **Smart Storage**: One JSON file per post with all content and replies
- 🔄 **Resume Capability**: Automatically resume from where you left off
- 📸 **Visual Feedback**: Screenshots for debugging and verification
- 🚦 **Rate Limiting**: Configurable delays to be respectful

## Quick Start

```bash
# Run the interactive menu
./run_scraper.sh

# Or run directly
python scraper_enhanced.py
```

## Installation

1. **Clone/Download the scraper files**

2. **Install Python 3.8+** (if not already installed)

3. **Run the setup**:
   ```bash
   ./run_scraper.sh
   # Select option 9 to setup dependencies
   ```

## Usage

### Interactive Mode (Recommended)

```bash
./run_scraper.sh
```

This provides a menu with options:
- Start scraper with monitor
- Resume previous session
- View statistics
- Reset and start fresh

### Command Line Mode

```bash
# Basic usage
python scraper_enhanced.py

# Run headless (no browser window)
python scraper_enhanced.py --headless

# Limit number of posts
python scraper_enhanced.py --max-posts 100

# Start from specific URL
python scraper_enhanced.py --start-url "https://forum.ecommercefuel.com/top"

# Reset progress and start fresh
python scraper_enhanced.py --reset

# Set custom rate limit (seconds between requests)
python scraper_enhanced.py --rate-limit 2.5
```

### Monitor Mode

Run in a separate terminal to see real-time progress:

```bash
python scraper_monitor.py
```

### Control Commands

While scraper is running, you can control it:

```bash
# Pause scraping
python scraper_monitor.py --pause

# Resume scraping
python scraper_monitor.py --resume

# Change rate limit
python scraper_monitor.py --rate-limit 3.0
```

## Output Structure

```
forum_data/
├── post_title_12345.json    # Individual post with all replies
├── post_title_67890.json
└── scraping_summary.json    # Overall statistics

screenshots/
├── 20240602_143022_initial_state.png
├── 20240602_143025_post_example.png
└── ...

scraper_state/
├── browser_state.json       # Browser state
├── cookies.json            # Saved cookies
├── scraping_progress.json  # Progress tracking
└── live_status.json        # Real-time status
```

## Post Data Format

Each post is saved as a JSON file with the following structure:

```json
{
  "url": "/t/post-slug/12345",
  "full_url": "https://forum.ecommercefuel.com/t/post-slug/12345",
  "title": "Post Title",
  "author": "John Doe",
  "category": "Category Name",
  "tags": ["tag1", "tag2"],
  "created_at": "2024-06-02T10:30:00Z",
  "replies": [
    {
      "index": 0,
      "author": "John Doe",
      "content": "Original post content...",
      "content_text": "Plain text version...",
      "created_at": "2024-06-02T10:30:00Z",
      "likes": 5,
      "is_original": true
    },
    {
      "index": 1,
      "author": "Jane Smith",
      "content": "Reply content...",
      "created_at": "2024-06-02T11:00:00Z",
      "likes": 2,
      "is_original": false
    }
  ],
  "stats": {
    "replies": "15",
    "views": "234",
    "users": "8"
  },
  "scraped_at": "2024-06-02T14:30:00Z"
}
```

## Handling Login

1. The scraper will detect if you're not logged in
2. It will pause and ask you to log in manually
3. Complete the login in the browser window
4. Press Enter in the terminal
5. Cookies will be saved for future sessions

## Troubleshooting

### "No module named 'playwright'"
Run: `pip install -r requirements_scraper.txt`

### "Playwright browsers not installed"
Run: `playwright install chromium`

### "Login keeps being required"
- Check if cookies are being saved in `scraper_state/cookies.json`
- Try deleting the cookies file and logging in fresh

### "Scraper seems stuck"
- Check the monitor for current status
- Look at screenshots folder for recent activity
- Check `playwright_scraper.log` for errors

## Advanced Configuration

### Custom Selectors

Edit `scraper_enhanced.py` to modify selectors:

```python
# In extract_post_list_enhanced method
title_selectors = ['h2 a', '.topic-link', 'a.title']
author_selectors = ['td:first-child a', '.topic-poster a']
```

### Rate Limiting

Adjust the delay between requests:

```python
scraper.rate_limit = 2.5  # 2.5 seconds between requests
```

### Debug Mode

Enable/disable screenshot taking:

```python
scraper = EnhancedEcommerceFuelScraper(debug=True)  # Take screenshots
scraper = EnhancedEcommerceFuelScraper(debug=False) # No screenshots
```

## Ethics and Best Practices

- Be respectful of the website's resources
- Use appropriate rate limiting
- Don't scrape during peak hours
- Respect robots.txt and terms of service
- Consider reaching out to the site owners

## License

This is a specialized scraper for educational/research purposes. Use responsibly.