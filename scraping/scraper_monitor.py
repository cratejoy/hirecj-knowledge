#!/usr/bin/env python3
"""
Real-time monitoring and control interface for the scraper
Provides visual feedback and allows adjustments during scraping
"""

import json
import time
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import threading
import queue

# For terminal UI
try:
    from rich.console import Console
    from rich.table import Table
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.live import Live
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Install 'rich' for better monitoring: pip install rich")


class ScraperMonitor:
    """Real-time monitoring interface for the scraper"""
    
    def __init__(self):
        self.state_dir = Path("scraper_state")
        self.data_dir = Path("forum_data")
        self.screenshots_dir = Path("screenshots")
        self.progress_file = self.state_dir / "scraping_progress.json"
        self.console = Console() if RICH_AVAILABLE else None
        
        # Monitoring state
        self.is_running = True
        self.update_queue = queue.Queue()
        
    def load_progress(self) -> Dict:
        """Load current progress"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {
            'scraped_posts': [],
            'scraped_urls': [],
            'failed_urls': [],
            'last_updated': None
        }
    
    def get_latest_screenshot(self) -> str:
        """Get the most recent screenshot"""
        screenshots = list(self.screenshots_dir.glob("*.png"))
        if screenshots:
            latest = max(screenshots, key=lambda p: p.stat().st_mtime)
            return latest.name
        return "No screenshots yet"
    
    def get_post_stats(self) -> Dict:
        """Get statistics from scraped posts"""
        stats = {
            'total_posts': 0,
            'total_replies': 0,
            'categories': {},
            'authors': {},
            'recent_posts': []
        }
        
        json_files = list(self.data_dir.glob("*.json"))
        stats['total_posts'] = len(json_files)
        
        # Get recent posts
        recent_files = sorted(
            json_files, 
            key=lambda p: p.stat().st_mtime, 
            reverse=True
        )[:5]
        
        for post_file in recent_files:
            try:
                with open(post_file, 'r') as f:
                    post_data = json.load(f)
                    
                    # Count replies
                    stats['total_replies'] += len(post_data.get('replies', []))
                    
                    # Track categories
                    category = post_data.get('category', 'Unknown')
                    stats['categories'][category] = stats['categories'].get(category, 0) + 1
                    
                    # Track authors
                    author = post_data.get('author', 'Unknown')
                    stats['authors'][author] = stats['authors'].get(author, 0) + 1
                    
                    # Add to recent posts
                    stats['recent_posts'].append({
                        'title': post_data.get('title', 'Untitled')[:50] + '...',
                        'replies': len(post_data.get('replies', [])),
                        'time': datetime.fromtimestamp(post_file.stat().st_mtime).strftime('%H:%M:%S')
                    })
            except:
                continue
        
        return stats
    
    def create_dashboard(self) -> Layout:
        """Create the monitoring dashboard"""
        if not RICH_AVAILABLE:
            return None
            
        layout = Layout()
        
        # Create sections
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=4)
        )
        
        layout["main"].split_row(
            Layout(name="stats", ratio=1),
            Layout(name="activity", ratio=2)
        )
        
        # Header
        header = Panel(
            Text("EcommerceFuel Forum Scraper Monitor", style="bold cyan", justify="center"),
            style="cyan"
        )
        layout["header"].update(header)
        
        # Progress
        progress = self.load_progress()
        stats = self.get_post_stats()
        
        # Stats panel
        stats_table = Table(show_header=False, padding=0, box=None)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")
        
        stats_table.add_row("Posts Scraped", str(len(progress['scraped_posts'])))
        stats_table.add_row("Total Replies", str(stats['total_replies']))
        stats_table.add_row("Failed URLs", str(len(progress['failed_urls'])))
        stats_table.add_row("Categories", str(len(stats['categories'])))
        stats_table.add_row("Unique Authors", str(len(stats['authors'])))
        stats_table.add_row("Latest Screenshot", self.get_latest_screenshot())
        
        layout["stats"].update(Panel(stats_table, title="Statistics", border_style="blue"))
        
        # Activity panel
        activity_table = Table(title="Recent Activity", padding=0)
        activity_table.add_column("Time", style="dim", width=10)
        activity_table.add_column("Post Title", style="cyan")
        activity_table.add_column("Replies", justify="right", style="green")
        
        for post in stats['recent_posts']:
            activity_table.add_row(
                post['time'],
                post['title'],
                str(post['replies'])
            )
        
        layout["activity"].update(Panel(activity_table, border_style="green"))
        
        # Footer - Instructions
        footer_text = "[cyan]Commands:[/cyan] [yellow]q[/yellow] - Quit | [yellow]r[/yellow] - Refresh | [yellow]s[/yellow] - Screenshot folder | [yellow]d[/yellow] - Data folder"
        layout["footer"].update(Panel(footer_text, title="Controls", border_style="yellow"))
        
        return layout
    
    def simple_monitor(self):
        """Simple monitoring for when rich is not available"""
        while self.is_running:
            os.system('clear')
            
            progress = self.load_progress()
            stats = self.get_post_stats()
            
            print("="*50)
            print("EcommerceFuel Forum Scraper Monitor")
            print("="*50)
            print(f"Posts Scraped: {len(progress['scraped_posts'])}")
            print(f"Total Replies: {stats['total_replies']}")
            print(f"Failed URLs: {len(progress['failed_urls'])}")
            print(f"Last Updated: {progress.get('last_updated', 'Never')}")
            print("="*50)
            print("Recent Posts:")
            for post in stats['recent_posts'][:5]:
                print(f"  - {post['title']} ({post['replies']} replies)")
            print("="*50)
            print("Press Ctrl+C to exit")
            
            time.sleep(2)
    
    def run(self):
        """Run the monitor"""
        if not RICH_AVAILABLE:
            try:
                self.simple_monitor()
            except KeyboardInterrupt:
                print("\nMonitor stopped")
            return
        
        # Rich UI monitoring
        with Live(self.create_dashboard(), refresh_per_second=1, screen=True) as live:
            try:
                while self.is_running:
                    # Update display
                    live.update(self.create_dashboard())
                    
                    # Check for user input (non-blocking)
                    # In a real implementation, you'd handle keyboard input
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                self.is_running = False
                
        self.console.print("[green]Monitor stopped[/green]")


class ScraperController:
    """Control interface for the scraper"""
    
    def __init__(self):
        self.control_file = Path("scraper_state/control.json")
        
    def send_command(self, command: str, data: Dict = None):
        """Send a command to the scraper"""
        control_data = {
            'command': command,
            'data': data or {},
            'timestamp': datetime.now().isoformat()
        }
        
        with open(self.control_file, 'w') as f:
            json.dump(control_data, f)
    
    def pause_scraper(self):
        """Pause the scraper"""
        self.send_command('pause')
        print("Pause command sent")
    
    def resume_scraper(self):
        """Resume the scraper"""
        self.send_command('resume')
        print("Resume command sent")
    
    def set_rate_limit(self, seconds: float):
        """Set rate limiting"""
        self.send_command('rate_limit', {'seconds': seconds})
        print(f"Rate limit set to {seconds} seconds")
    
    def skip_post(self, post_url: str):
        """Skip a specific post"""
        self.send_command('skip_post', {'url': post_url})
        print(f"Skip command sent for: {post_url}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scraper Monitor and Controller')
    parser.add_argument('--control', action='store_true', help='Launch control interface')
    parser.add_argument('--pause', action='store_true', help='Pause the scraper')
    parser.add_argument('--resume', action='store_true', help='Resume the scraper')
    parser.add_argument('--rate-limit', type=float, help='Set rate limit in seconds')
    
    args = parser.parse_args()
    
    if args.control or args.pause or args.resume or args.rate_limit:
        # Control mode
        controller = ScraperController()
        
        if args.pause:
            controller.pause_scraper()
        elif args.resume:
            controller.resume_scraper()
        elif args.rate_limit:
            controller.set_rate_limit(args.rate_limit)
        else:
            print("Control interface launched")
            print("Available commands:")
            print("  --pause     : Pause the scraper")
            print("  --resume    : Resume the scraper")
            print("  --rate-limit N : Set rate limit to N seconds")
    else:
        # Monitor mode
        monitor = ScraperMonitor()
        monitor.run()


if __name__ == "__main__":
    main()