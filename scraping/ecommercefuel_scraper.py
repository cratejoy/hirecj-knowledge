#!/usr/bin/env python3
"""
EcommerceFuel Forum Scraper - Phase 1: Browser Setup & Cookie Persistence
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


if __name__ == "__main__":
    scraper = EcommerceFuelScraper()
    scraper.run_phase1()