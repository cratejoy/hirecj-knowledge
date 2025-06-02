#!/usr/bin/env python3
"""
Debug script to understand cookie behavior on EcommerceFuel forum
"""

import json
import time
from playwright.sync_api import sync_playwright
from datetime import datetime


def debug_cookies():
    """Debug cookie saving issues"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        print("1. Navigating to forum...")
        page.goto("https://forum.ecommercefuel.com")
        page.wait_for_load_state('networkidle')
        
        # Check initial cookies
        cookies = context.cookies()
        print(f"\n2. Initial cookies before login: {len(cookies)} cookies")
        for cookie in cookies:
            print(f"   - {cookie['name']} on domain {cookie['domain']}")
        
        print("\n3. Please log in manually in the browser window")
        print("After logging in, press Enter here...")
        input()
        
        # Check cookies immediately
        cookies = context.cookies()
        print(f"\n4. Cookies immediately after login: {len(cookies)} cookies")
        for cookie in cookies:
            print(f"   - {cookie['name']} on domain {cookie['domain']}")
        
        # Wait a bit
        print("\n5. Waiting 3 seconds...")
        time.sleep(3)
        
        cookies = context.cookies()
        print(f"\n6. Cookies after waiting: {len(cookies)} cookies")
        for cookie in cookies:
            print(f"   - {cookie['name']} on domain {cookie['domain']}")
        
        # Navigate to trigger cookie setting
        print("\n7. Navigating to /latest to trigger any lazy cookie setting...")
        page.goto("https://forum.ecommercefuel.com/latest")
        page.wait_for_load_state('networkidle')
        
        cookies = context.cookies()
        print(f"\n8. Cookies after navigation: {len(cookies)} cookies")
        for cookie in cookies:
            print(f"   - {cookie['name']} on domain {cookie['domain']}")
        
        # Try getting cookies for all URLs
        print("\n9. Getting cookies for all URLs...")
        all_cookies = context.cookies()
        print(f"Total cookies: {len(all_cookies)}")
        
        # Group by domain
        domains = {}
        for cookie in all_cookies:
            domain = cookie['domain']
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(cookie['name'])
        
        print("\n10. Cookies grouped by domain:")
        for domain, names in domains.items():
            print(f"   {domain}: {names}")
        
        # Save for analysis
        with open('debug_cookies.json', 'w') as f:
            json.dump(all_cookies, f, indent=2)
        print("\n11. Saved all cookies to debug_cookies.json for analysis")
        
        # Check storage
        print("\n12. Checking localStorage and sessionStorage...")
        local_storage = page.evaluate("() => Object.keys(localStorage)")
        session_storage = page.evaluate("() => Object.keys(sessionStorage)")
        print(f"   localStorage keys: {local_storage}")
        print(f"   sessionStorage keys: {session_storage}")
        
        print("\nPress Enter to close browser...")
        input()
        
        browser.close()


if __name__ == "__main__":
    debug_cookies()