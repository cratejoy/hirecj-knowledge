#!/usr/bin/env python3
"""
EcommerceFuel Forum Endless Scroll Scraper
Handles endless scroll pagination to extract all forum posts
"""

import json
import csv
import time
import logging
from datetime import datetime
from typing import Dict, List, Set
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ecommercefuel_endless_scroll.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EndlessScrollScraper:
    def __init__(self):
        self.all_posts = []
        self.seen_urls = set()
        self.output_dir = "ecommercefuel_data"
        os.makedirs(self.output_dir, exist_ok=True)
        
    def add_posts_from_snapshot(self, posts: List[Dict], page_num: int = 1):
        """Add posts from a browser snapshot, avoiding duplicates"""
        new_posts = 0
        
        for post in posts:
            url = post.get('url', '')
            if url and url not in self.seen_urls:
                self.seen_urls.add(url)
                post['page_scraped'] = page_num
                self.all_posts.append(post)
                new_posts += 1
        
        logger.info(f"Added {new_posts} new posts from page {page_num}")
        return new_posts
    
    def save_progress(self, page_num: int):
        """Save current progress to file"""
        filename = os.path.join(self.output_dir, f"posts_page_{page_num}.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'page': page_num,
                'total_posts': len(self.all_posts),
                'posts': self.all_posts
            }, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved progress: {len(self.all_posts)} posts up to page {page_num}")
    
    def export_final_data(self):
        """Export all collected data"""
        # JSON export
        json_file = os.path.join(self.output_dir, "all_forum_posts.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.all_posts, f, indent=2, ensure_ascii=False)
        
        # CSV export
        if self.all_posts:
            csv_file = os.path.join(self.output_dir, "all_forum_posts.csv")
            
            # Prepare flattened data
            flattened_data = []
            for post in self.all_posts:
                flat_post = post.copy()
                # Convert lists to strings
                if 'tags' in flat_post and isinstance(flat_post['tags'], list):
                    flat_post['tags'] = ', '.join(flat_post['tags'])
                flattened_data.append(flat_post)
            
            # Write CSV
            fieldnames = ['author', 'title', 'url', 'category', 'tags', 'replies', 
                         'views', 'last_activity', 'page_scraped', 'scraped_at']
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(flattened_data)
        
        # Summary statistics
        self.generate_summary()
        
        logger.info(f"Exported {len(self.all_posts)} posts to {self.output_dir}")
    
    def generate_summary(self):
        """Generate summary statistics"""
        if not self.all_posts:
            return
        
        # Calculate statistics
        categories = {}
        authors = {}
        tags_count = {}
        
        for post in self.all_posts:
            # Categories
            cat = post.get('category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1
            
            # Authors
            author = post.get('author', 'Unknown')
            authors[author] = authors.get(author, 0) + 1
            
            # Tags
            for tag in post.get('tags', []):
                tags_count[tag] = tags_count.get(tag, 0) + 1
        
        # Find top items
        top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]
        top_authors = sorted(authors.items(), key=lambda x: x[1], reverse=True)[:10]
        top_tags = sorted(tags_count.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Most engaged posts
        most_replied = max(self.all_posts, key=lambda x: x.get('replies', 0))
        most_viewed = max(self.all_posts, key=lambda x: x.get('views', 0))
        
        summary = {
            'total_posts': len(self.all_posts),
            'unique_categories': len(categories),
            'unique_authors': len(authors),
            'unique_tags': len(tags_count),
            'top_categories': top_categories,
            'top_authors': top_authors,
            'top_tags': top_tags,
            'most_replied_post': {
                'title': most_replied.get('title'),
                'replies': most_replied.get('replies'),
                'url': most_replied.get('url')
            },
            'most_viewed_post': {
                'title': most_viewed.get('title'),
                'views': most_viewed.get('views'),
                'url': most_viewed.get('url')
            },
            'scraped_at': datetime.now().isoformat()
        }
        
        # Save summary
        summary_file = os.path.join(self.output_dir, "scraping_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("\n=== Scraping Summary ===")
        print(f"Total posts scraped: {summary['total_posts']}")
        print(f"Unique categories: {summary['unique_categories']}")
        print(f"Unique authors: {summary['unique_authors']}")
        print(f"Unique tags: {summary['unique_tags']}")
        print(f"\nTop 5 Categories:")
        for cat, count in top_categories[:5]:
            print(f"  - {cat}: {count} posts")
        print(f"\nTop 5 Authors:")
        for author, count in top_authors[:5]:
            print(f"  - {author}: {count} posts")
        print(f"\nMost replied: {most_replied.get('title')} ({most_replied.get('replies')} replies)")
        print(f"Most viewed: {most_viewed.get('title')} ({most_viewed.get('views')} views)")


def create_browser_instructions():
    """Create instructions for manual browser operation"""
    instructions = """
=== BROWSER SCRAPING INSTRUCTIONS ===

1. Open https://forum.ecommercefuel.com/latest in your browser
2. Make sure you're logged in to see all posts
3. Use browser MCP tools to extract posts:

For each "page" of results (as you scroll):
   a) Take a snapshot of the current view
   b) Extract all visible posts with these fields:
      - Author name
      - Post title
      - URL
      - Category
      - Tags (if any)
      - Number of replies
      - View count
      - Last activity time
   
4. Scroll down to load more posts (endless scroll)
5. Wait for new posts to load
6. Repeat steps 3-5 until no new posts load

7. Use the scraper.add_posts_from_snapshot() method to add posts
8. Call scraper.save_progress() periodically
9. Call scraper.export_final_data() when complete

Example usage:
```python
scraper = EndlessScrollScraper()

# After extracting posts from page 1
posts_page1 = [...]  # Your extracted posts
scraper.add_posts_from_snapshot(posts_page1, 1)
scraper.save_progress(1)

# After scrolling and extracting more posts
posts_page2 = [...]  # New posts after scroll
scraper.add_posts_from_snapshot(posts_page2, 2)
scraper.save_progress(2)

# When done
scraper.export_final_data()
```
"""
    
    with open("browser_scraping_instructions.txt", "w") as f:
        f.write(instructions)
    
    print("Instructions saved to browser_scraping_instructions.txt")
    return instructions


# Sample data from current snapshot
def extract_current_snapshot():
    """Extract posts from the current browser snapshot"""
    posts = [
        {
            'author': 'Dana Eriksson',
            'title': 'Welcome Paolo Dibenedetto - Wrapping Up Big Wins with Polish Pops',
            'url': '/t/welcome-paolo-dibenedetto-wrapping-up-big-wins-with-polish-pops/86932',
            'category': 'Delta Cohort',
            'tags': [],
            'replies': 0,
            'views': 2,
            'last_activity': '6m',
            'scraped_at': datetime.now().isoformat()
        },
        {
            'author': 'Beth Snyder',
            'title': 'Faire Is Doing Fulfillment?',
            'url': '/t/faire-is-doing-fulfillment/86921',
            'category': 'Channels',
            'tags': ['b2b', 'experience-share', 'wholesale'],
            'replies': 7,
            'views': 27,
            'last_activity': '13m',
            'scraped_at': datetime.now().isoformat()
        },
        # Add all posts from current view...
    ]
    
    # Continue with all visible posts from snapshot
    more_posts = [
        {'author': 'Dana Eriksson', 'title': 'Welcome Thomas Ferris - Clucking into DTC with Roostys', 'url': '/t/welcome-thomas-ferris-clucking-into-dtc-with-roostys/86931', 'category': 'Delta Cohort', 'tags': [], 'replies': 0, 'views': 1, 'last_activity': '17m', 'scraped_at': datetime.now().isoformat()},
        {'author': 'Noah Chanin', 'title': 'My First AI Coding Project, Looking for Advice on Speeding up Development', 'url': '/t/my-first-ai-coding-project-looking-for-advice-on-speeding-up-development/86917', 'category': 'SAAS Apps and Software', 'tags': ['ai'], 'replies': 8, 'views': 28, 'last_activity': '27m', 'scraped_at': datetime.now().isoformat()},
        {'author': 'DonCole', 'title': 'Editions.dev Ramblings', 'url': '/t/editions-dev-ramblings/86924', 'category': 'Shopify', 'tags': [], 'replies': 2, 'views': 18, 'last_activity': '35m', 'scraped_at': datetime.now().isoformat()},
        {'author': 'Nate Dadosky', 'title': 'What Cybersecurity Protection Do You Have in Place?', 'url': '/t/what-cybersecurity-protection-do-you-have-in-place/86847', 'category': 'Employees', 'tags': [], 'replies': 2, 'views': 33, 'last_activity': '1h', 'scraped_at': datetime.now().isoformat()},
        {'author': 'JeffRasmussen', 'title': 'Klaviyo Suddenly Inflating Number Of Profiles', 'url': '/t/klaviyo-suddenly-inflating-number-of-profiles/82309', 'category': 'SAAS Apps and Software', 'tags': [], 'replies': 97, 'views': 685, 'last_activity': '1h', 'scraped_at': datetime.now().isoformat()},
        {'author': 'Michael Jelliff 🏓', 'title': 'eBay Customers Using the Empty Envelope Return Scam', 'url': '/t/ebay-customers-using-the-empty-envelope-return-scam/47574', 'category': 'eBay', 'tags': ['returns'], 'replies': 49, 'views': 585, 'last_activity': '1h', 'scraped_at': datetime.now().isoformat()},
        {'author': 'RobHampton', 'title': 'How We Run EOS L10 Meetings & Track Rocks in ClickUp (Loom + SOP + Template)', 'url': '/t/how-we-run-eos-l10-meetings-track-rocks-in-clickup-loom-sop-template/85378', 'category': 'Team', 'tags': ['traction-eos'], 'replies': 4, 'views': 87, 'last_activity': '1h', 'scraped_at': datetime.now().isoformat()},
        {'author': 'Jeremy Roberts', 'title': 'Checkout Started (Abandoned) Flow - What Are Your Send Filter Settings?', 'url': '/t/checkout-started-abandoned-flow-what-are-your-send-filter-settings/86893', 'category': 'Email Marketing', 'tags': [], 'replies': 2, 'views': 29, 'last_activity': '1h', 'scraped_at': datetime.now().isoformat()},
        {'author': 'Kaylin Marcotte Roche', 'title': 'From 15% to 36% Open Rates - Our Customer Research Playbook', 'url': '/t/from-15-to-36-open-rates-our-customer-research-playbook/85216', 'category': 'Email Marketing', 'tags': ['agency', 'ai', 'experience-share'], 'replies': 9, 'views': 195, 'last_activity': '2h', 'scraped_at': datetime.now().isoformat()},
        {'author': 'Melita Cyril', 'title': 'Bid Cap Whatsapp Group?', 'url': '/t/bid-cap-whatsapp-group/81210', 'category': 'Not Visible to Vendors (Store Owners Only)', 'tags': [], 'replies': 35, 'views': 283, 'last_activity': '2h', 'scraped_at': datetime.now().isoformat()},
        {'author': 'EricBandholz', 'title': 'Well, I Got Sued Again, This Time for Patent Infringement', 'url': '/t/well-i-got-sued-again-this-time-for-patent-infringement/86687', 'category': 'Legal', 'tags': ['patents'], 'replies': 57, 'views': 777, 'last_activity': '2h', 'scraped_at': datetime.now().isoformat()},
        {'author': 'ScottMacco', 'title': 'Filing IP Trademark/Copyright/Patent infringements on AliExpress or Alibaba?', 'url': '/t/filing-ip-trademark-copyright-patent-infringements-on-aliexpress-or-alibaba/72274', 'category': 'Legal', 'tags': ['copyright', 'intell-prop-ip', 'trademarks'], 'replies': 14, 'views': 140, 'last_activity': '2h', 'scraped_at': datetime.now().isoformat()},
        {'author': 'Erich Jackson', 'title': 'Retention Email Specialist Needed', 'url': '/t/retention-email-specialist-needed/85181', 'category': 'Email Marketing', 'tags': [], 'replies': 7, 'views': 106, 'last_activity': '3h', 'scraped_at': datetime.now().isoformat()},
    ]
    
    posts.extend(more_posts)
    
    # Add Delta Cohort posts
    delta_posts = [
        {'author': 'Dana Eriksson', 'title': 'Welcome Tyler Westpfahl - Building Big with a Small-but-Mighty Team', 'url': '/t/welcome-tyler-westpfahl-building-big-with-a-small-but-mighty-team/86867', 'category': 'Delta Cohort', 'tags': [], 'replies': 4, 'views': 14, 'last_activity': '2h', 'scraped_at': datetime.now().isoformat()},
        {'author': 'Dana Eriksson', 'title': 'Welcome Back Tal Atid - Flooring Legend Turned Food Trailblazer', 'url': '/t/welcome-back-tal-atid-flooring-legend-turned-food-trailblazer/86896', 'category': 'Delta Cohort', 'tags': [], 'replies': 3, 'views': 9, 'last_activity': '2h', 'scraped_at': datetime.now().isoformat()},
        {'author': 'Dana Eriksson', 'title': 'Welcome Ted Mueller - Mastermind Behind Custom Gifting Made Easy', 'url': '/t/welcome-ted-mueller-mastermind-behind-custom-gifting-made-easy/86865', 'category': 'Delta Cohort', 'tags': [], 'replies': 4, 'views': 11, 'last_activity': '2h', 'scraped_at': datetime.now().isoformat()},
        {'author': 'Dana Eriksson', 'title': 'Welcome Curt Lee - Bath Mat Boss & Marketplace Pro', 'url': '/t/welcome-curt-lee-bath-mat-boss-marketplace-pro/86866', 'category': 'Delta Cohort', 'tags': [], 'replies': 2, 'views': 8, 'last_activity': '2h', 'scraped_at': datetime.now().isoformat()},
        {'author': 'Dana Eriksson', 'title': 'Welcome Tristan Broughton - Suds, Smarts, and a Cleaner Supply Chain', 'url': '/t/welcome-tristan-broughton-suds-smarts-and-a-cleaner-supply-chain/86776', 'category': 'Delta Cohort', 'tags': [], 'replies': 4, 'views': 14, 'last_activity': '2h', 'scraped_at': datetime.now().isoformat()},
        {'author': 'Dana Eriksson', 'title': 'Welcome Anthony Martin - A Century of Health Innovation', 'url': '/t/welcome-anthony-martin-a-century-of-health-innovation/86738', 'category': 'Delta Cohort', 'tags': [], 'replies': 7, 'views': 17, 'last_activity': '2h', 'scraped_at': datetime.now().isoformat()},
        {'author': 'Dana Eriksson', 'title': 'Welcome Kyle Czarnecki - From Backyard Game to Viral Fame', 'url': '/t/welcome-kyle-czarnecki-from-backyard-game-to-viral-fame/86793', 'category': 'Delta Cohort', 'tags': [], 'replies': 5, 'views': 11, 'last_activity': '2h', 'scraped_at': datetime.now().isoformat()},
        {'author': 'Dana Eriksson', 'title': 'Welcome Kody Lukens - Wearable Calm, Bootstrapped Brilliance', 'url': '/t/welcome-kody-lukens-wearable-calm-bootstrapped-brilliance/86801', 'category': 'Delta Cohort', 'tags': [], 'replies': 4, 'views': 12, 'last_activity': '2h', 'scraped_at': datetime.now().isoformat()},
        {'author': 'Dana Eriksson', 'title': 'Welcome James Bertram - Keeping Performance Sparkling at Abbott Lyon', 'url': '/t/welcome-james-bertram-keeping-performance-sparkling-at-abbott-lyon/86799', 'category': 'Delta Cohort', 'tags': [], 'replies': 3, 'views': 7, 'last_activity': '2h', 'scraped_at': datetime.now().isoformat()},
        {'author': 'Dana Eriksson', 'title': 'Welcome Jason Piller - Splashing Innovation Into the Golf World', 'url': '/t/welcome-jason-piller-splashing-innovation-into-the-golf-world/86794', 'category': 'Delta Cohort', 'tags': [], 'replies': 3, 'views': 8, 'last_activity': '3h', 'scraped_at': datetime.now().isoformat()},
        {'author': 'Dana Eriksson', 'title': 'Welcome Abbas Dar - Tracking Success From Kickstarter to Connected Tech', 'url': '/t/welcome-abbas-dar-tracking-success-from-kickstarter-to-connected-tech/86772', 'category': 'Delta Cohort', 'tags': [], 'replies': 3, 'views': 11, 'last_activity': '3h', 'scraped_at': datetime.now().isoformat()},
        {'author': 'Dana Eriksson', 'title': 'Welcome Hilal Kanafani - Powering Up Comfort for Gamers & Crafters Alike', 'url': '/t/welcome-hilal-kanafani-powering-up-comfort-for-gamers-crafters-alike/86769', 'category': 'Delta Cohort', 'tags': [], 'replies': 4, 'views': 11, 'last_activity': '3h', 'scraped_at': datetime.now().isoformat()},
        {'author': 'Dana Eriksson', 'title': 'Welcome Joey Bryja - Throwing Big Wins into the eCom Ring', 'url': '/t/welcome-joey-bryja-throwing-big-wins-into-the-ecom-ring/86768', 'category': 'Delta Cohort', 'tags': [], 'replies': 3, 'views': 8, 'last_activity': '3h', 'scraped_at': datetime.now().isoformat()},
        {'author': 'Dana Eriksson', 'title': 'Welcome Isaac Mertens - Lacing Up Big Growth with Flux', 'url': '/t/welcome-isaac-mertens-lacing-up-big-growth-with-flux/86765', 'category': 'Delta Cohort', 'tags': [], 'replies': 3, 'views': 8, 'last_activity': '3h', 'scraped_at': datetime.now().isoformat()},
        {'author': 'Dana Eriksson', 'title': 'Welcome Brendan Hastings - Scaling Tech, Teams & Tulle With Birdy Grey', 'url': '/t/welcome-brendan-hastings-scaling-tech-teams-tulle-with-birdy-grey/86761', 'category': 'Delta Cohort', 'tags': [], 'replies': 3, 'views': 13, 'last_activity': '3h', 'scraped_at': datetime.now().isoformat()},
    ]
    
    posts.extend(delta_posts)
    
    return posts


if __name__ == "__main__":
    # Create scraper instance
    scraper = EndlessScrollScraper()
    
    # Create instructions
    create_browser_instructions()
    
    # Extract and add current snapshot data
    current_posts = extract_current_snapshot()
    scraper.add_posts_from_snapshot(current_posts, 1)
    scraper.save_progress(1)
    
    # Export what we have so far
    scraper.export_final_data()
    
    print(f"\nScraper initialized with {len(current_posts)} posts from current view")
    print("Follow the instructions in browser_scraping_instructions.txt to continue scraping")