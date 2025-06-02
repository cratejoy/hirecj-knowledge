#!/usr/bin/env python3
"""
EcommerceFuel Forum Scraper
Scrapes forum posts from the EcommerceFuel community forum
"""

import json
import csv
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ecommercefuel_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EcommerceFuelScraper:
    def __init__(self, base_url: str = "https://forum.ecommercefuel.com"):
        self.base_url = base_url
        self.posts_data = []
        
    def parse_time_ago(self, time_str: str) -> str:
        """Convert relative time (e.g., '2h', '3m') to approximate timestamp"""
        now = datetime.now()
        
        # Extract number and unit
        match = re.match(r'(\d+)([hmd])', time_str)
        if not match:
            return time_str
            
        num = int(match.group(1))
        unit = match.group(2)
        
        if unit == 'm':  # minutes
            delta = num * 60
        elif unit == 'h':  # hours
            delta = num * 3600
        elif unit == 'd':  # days
            delta = num * 86400
        else:
            return time_str
            
        timestamp = now.timestamp() - delta
        return datetime.fromtimestamp(timestamp).isoformat()
    
    def extract_post_data(self, post_element: Dict) -> Optional[Dict]:
        """Extract data from a single post element"""
        try:
            post_data = {
                'author': '',
                'title': '',
                'url': '',
                'category': '',
                'tags': [],
                'replies': 0,
                'views': 0,
                'last_activity': '',
                'scraped_at': datetime.now().isoformat()
            }
            
            # This would be populated from the browser data
            # For now, creating structure for manual population
            
            return post_data
            
        except Exception as e:
            logger.error(f"Error extracting post data: {e}")
            return None
    
    def scrape_page(self, page_data: List[Dict]) -> List[Dict]:
        """Scrape posts from a single page"""
        posts = []
        
        for post in page_data:
            post_data = self.extract_post_data(post)
            if post_data:
                posts.append(post_data)
                logger.info(f"Scraped post: {post_data['title']}")
        
        return posts
    
    def save_to_json(self, filename: str = "ecommercefuel_posts.json"):
        """Save scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.posts_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(self.posts_data)} posts to {filename}")
    
    def save_to_csv(self, filename: str = "ecommercefuel_posts.csv"):
        """Save scraped data to CSV file"""
        if not self.posts_data:
            logger.warning("No data to save")
            return
            
        fieldnames = self.posts_data[0].keys()
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.posts_data)
        
        logger.info(f"Saved {len(self.posts_data)} posts to {filename}")
    
    def manual_add_posts(self, posts: List[Dict]):
        """Manually add posts data extracted from browser"""
        self.posts_data.extend(posts)
        logger.info(f"Added {len(posts)} posts manually")


# Manual data extraction from the browser snapshot
def extract_from_browser_snapshot():
    """Extract posts from the browser snapshot provided"""
    posts = [
        {
            'author': 'Beth Snyder',
            'title': 'Faire Is Doing Fulfillment?',
            'url': '/t/faire-is-doing-fulfillment/86921',
            'category': 'Channels',
            'tags': ['b2b', 'experience-share', 'wholesale'],
            'replies': 7,
            'views': 26,
            'last_activity': '2m',
            'scraped_at': datetime.now().isoformat()
        },
        {
            'author': 'Dana Eriksson',
            'title': 'Welcome Thomas Ferris - Clucking into DTC with Roostys',
            'url': '/t/welcome-thomas-ferris-clucking-into-dtc-with-roostys/86931',
            'category': 'Delta Cohort',
            'tags': [],
            'replies': 0,
            'views': 1,
            'last_activity': '6m',
            'scraped_at': datetime.now().isoformat()
        },
        {
            'author': 'Noah Chanin',
            'title': 'My First AI Coding Project, Looking for Advice on Speeding up Development',
            'url': '/t/my-first-ai-coding-project-looking-for-advice-on-speeding-up-development/86917',
            'category': 'SAAS Apps and Software',
            'tags': ['ai'],
            'replies': 8,
            'views': 27,
            'last_activity': '16m',
            'scraped_at': datetime.now().isoformat()
        },
        {
            'author': 'DonCole',
            'title': 'Editions.dev Ramblings',
            'url': '/t/editions-dev-ramblings/86924',
            'category': 'Shopify',
            'tags': [],
            'replies': 2,
            'views': 15,
            'last_activity': '24m',
            'scraped_at': datetime.now().isoformat()
        },
        {
            'author': 'Nate Dadosky',
            'title': 'What Cybersecurity Protection Do You Have in Place?',
            'url': '/t/what-cybersecurity-protection-do-you-have-in-place/86847',
            'category': 'Employees',
            'tags': [],
            'replies': 2,
            'views': 33,
            'last_activity': '43m',
            'scraped_at': datetime.now().isoformat()
        },
        {
            'author': 'JeffRasmussen',
            'title': 'Klaviyo Suddenly Inflating Number Of Profiles',
            'url': '/t/klaviyo-suddenly-inflating-number-of-profiles/82309',
            'category': 'SAAS Apps and Software',
            'tags': [],
            'replies': 97,
            'views': 685,
            'last_activity': '1h',
            'scraped_at': datetime.now().isoformat()
        },
        {
            'author': 'Michael Jelliff 🏓',
            'title': 'eBay Customers Using the Empty Envelope Return Scam',
            'url': '/t/ebay-customers-using-the-empty-envelope-return-scam/47574',
            'category': 'eBay',
            'tags': ['returns'],
            'replies': 49,
            'views': 583,
            'last_activity': '1h',
            'scraped_at': datetime.now().isoformat()
        },
        {
            'author': 'RobHampton',
            'title': 'How We Run EOS L10 Meetings & Track Rocks in ClickUp (Loom + SOP + Template)',
            'url': '/t/how-we-run-eos-l10-meetings-track-rocks-in-clickup-loom-sop-template/85378',
            'category': 'Team',
            'tags': ['traction-eos'],
            'replies': 4,
            'views': 86,
            'last_activity': '1h',
            'scraped_at': datetime.now().isoformat()
        },
        {
            'author': 'Jeremy Roberts',
            'title': 'Checkout Started (Abandoned) Flow - What Are Your Send Filter Settings?',
            'url': '/t/checkout-started-abandoned-flow-what-are-your-send-filter-settings/86893',
            'category': 'Email Marketing',
            'tags': [],
            'replies': 2,
            'views': 29,
            'last_activity': '1h',
            'scraped_at': datetime.now().isoformat()
        },
        {
            'author': 'Kaylin Marcotte Roche',
            'title': 'From 15% to 36% Open Rates - Our Customer Research Playbook',
            'url': '/t/from-15-to-36-open-rates-our-customer-research-playbook/85216',
            'category': 'Email Marketing',
            'tags': ['agency', 'ai', 'experience-share'],
            'replies': 9,
            'views': 195,
            'last_activity': '2h',
            'scraped_at': datetime.now().isoformat()
        },
        {
            'author': 'Melita Cyril',
            'title': 'Bid Cap Whatsapp Group?',
            'url': '/t/bid-cap-whatsapp-group/81210',
            'category': 'Not Visible to Vendors (Store Owners Only)',
            'tags': [],
            'replies': 35,
            'views': 282,
            'last_activity': '2h',
            'scraped_at': datetime.now().isoformat()
        },
        {
            'author': 'EricBandholz',
            'title': 'Well, I Got Sued Again, This Time for Patent Infringement',
            'url': '/t/well-i-got-sued-again-this-time-for-patent-infringement/86687',
            'category': 'Legal',
            'tags': ['patents'],
            'replies': 57,
            'views': 775,
            'last_activity': '2h',
            'scraped_at': datetime.now().isoformat()
        },
        {
            'author': 'ScottMacco',
            'title': 'Filing IP Trademark/Copyright/Patent infringements on AliExpress or Alibaba?',
            'url': '/t/filing-ip-trademark-copyright-patent-infringements-on-aliexpress-or-alibaba/72274',
            'category': 'Legal',
            'tags': ['copyright', 'intell-prop-ip', 'trademarks'],
            'replies': 14,
            'views': 140,
            'last_activity': '2h',
            'scraped_at': datetime.now().isoformat()
        },
        {
            'author': 'Erich Jackson',
            'title': 'Retention Email Specialist Needed',
            'url': '/t/retention-email-specialist-needed/85181',
            'category': 'Email Marketing',
            'tags': [],
            'replies': 7,
            'views': 106,
            'last_activity': '3h',
            'scraped_at': datetime.now().isoformat()
        }
    ]
    
    # Add all the Delta Cohort welcome posts
    delta_cohort_posts = [
        ('Dana Eriksson', 'Welcome Tyler Westpfahl - Building Big with a Small-but-Mighty Team', '/t/welcome-tyler-westpfahl-building-big-with-a-small-but-mighty-team/86867', 4, 13, '2h'),
        ('Dana Eriksson', 'Welcome Back Tal Atid - Flooring Legend Turned Food Trailblazer', '/t/welcome-back-tal-atid-flooring-legend-turned-food-trailblazer/86896', 3, 9, '2h'),
        ('Dana Eriksson', 'Welcome Ted Mueller - Mastermind Behind Custom Gifting Made Easy', '/t/welcome-ted-mueller-mastermind-behind-custom-gifting-made-easy/86865', 4, 11, '2h'),
        ('Dana Eriksson', 'Welcome Curt Lee - Bath Mat Boss & Marketplace Pro', '/t/welcome-curt-lee-bath-mat-boss-marketplace-pro/86866', 2, 8, '2h'),
        ('Dana Eriksson', 'Welcome Tristan Broughton - Suds, Smarts, and a Cleaner Supply Chain', '/t/welcome-tristan-broughton-suds-smarts-and-a-cleaner-supply-chain/86776', 4, 14, '2h'),
        ('Dana Eriksson', 'Welcome Anthony Martin - A Century of Health Innovation', '/t/welcome-anthony-martin-a-century-of-health-innovation/86738', 7, 17, '2h'),
        ('Dana Eriksson', 'Welcome Kyle Czarnecki - From Backyard Game to Viral Fame', '/t/welcome-kyle-czarnecki-from-backyard-game-to-viral-fame/86793', 5, 11, '2h'),
        ('Dana Eriksson', 'Welcome Kody Lukens - Wearable Calm, Bootstrapped Brilliance', '/t/welcome-kody-lukens-wearable-calm-bootstrapped-brilliance/86801', 4, 12, '2h'),
        ('Dana Eriksson', 'Welcome James Bertram - Keeping Performance Sparkling at Abbott Lyon', '/t/welcome-james-bertram-keeping-performance-sparkling-at-abbott-lyon/86799', 3, 7, '2h'),
        ('Dana Eriksson', 'Welcome Jason Piller - Splashing Innovation Into the Golf World', '/t/welcome-jason-piller-splashing-innovation-into-the-golf-world/86794', 3, 8, '2h'),
        ('Dana Eriksson', 'Welcome Abbas Dar - Tracking Success From Kickstarter to Connected Tech', '/t/welcome-abbas-dar-tracking-success-from-kickstarter-to-connected-tech/86772', 3, 11, '2h'),
        ('Dana Eriksson', 'Welcome Hilal Kanafani - Powering Up Comfort for Gamers & Crafters Alike', '/t/welcome-hilal-kanafani-powering-up-comfort-for-gamers-crafters-alike/86769', 4, 11, '2h'),
        ('Dana Eriksson', 'Welcome Joey Bryja - Throwing Big Wins into the eCom Ring', '/t/welcome-joey-bryja-throwing-big-wins-into-the-ecom-ring/86768', 3, 8, '3h'),
        ('Dana Eriksson', 'Welcome Isaac Mertens - Lacing Up Big Growth with Flux', '/t/welcome-isaac-mertens-lacing-up-big-growth-with-flux/86765', 3, 8, '3h'),
        ('Dana Eriksson', 'Welcome Brendan Hastings - Scaling Tech, Teams & Tulle With Birdy Grey', '/t/welcome-brendan-hastings-scaling-tech-teams-tulle-with-birdy-grey/86761', 3, 13, '3h'),
        ('Dana Eriksson', 'Welcome Mike Ettenberg - Bringing Clarity to First Responders, One Pair at a Time', '/t/welcome-mike-ettenberg-bringing-clarity-to-first-responders-one-pair-at-a-time/86792', 4, 17, '3h'),
    ]
    
    for author, title, url, replies, views, last_activity in delta_cohort_posts:
        posts.append({
            'author': author,
            'title': title,
            'url': url,
            'category': 'Delta Cohort',
            'tags': [],
            'replies': replies,
            'views': views,
            'last_activity': last_activity,
            'scraped_at': datetime.now().isoformat()
        })
    
    return posts


# Example usage
if __name__ == "__main__":
    # Initialize scraper
    scraper = EcommerceFuelScraper()
    
    # Extract posts from browser snapshot
    posts = extract_from_browser_snapshot()
    
    # Add posts to scraper
    scraper.manual_add_posts(posts)
    
    # Save to both formats
    scraper.save_to_json()
    scraper.save_to_csv()
    
    logger.info(f"Scraping completed. Total posts: {len(scraper.posts_data)}")
    
    # Print summary
    print("\n=== Scraping Summary ===")
    print(f"Total posts scraped: {len(scraper.posts_data)}")
    print(f"Categories found: {len(set(p['category'] for p in scraper.posts_data))}")
    print(f"Unique authors: {len(set(p['author'] for p in scraper.posts_data))}")
    print(f"Posts with tags: {len([p for p in scraper.posts_data if p['tags']])}")
    print(f"Most replied post: {max(scraper.posts_data, key=lambda x: x['replies'])['title']} ({max(p['replies'] for p in scraper.posts_data)} replies)")
    print(f"Most viewed post: {max(scraper.posts_data, key=lambda x: x['views'])['title']} ({max(p['views'] for p in scraper.posts_data)} views)")