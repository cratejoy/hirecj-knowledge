#!/usr/bin/env python3
"""
Analyze and work with scraped forum data
Example utilities for processing the scraped posts
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from collections import Counter, defaultdict


class ForumDataAnalyzer:
    """Analyze scraped forum data"""
    
    def __init__(self, data_dir: str = "forum_data"):
        self.data_dir = Path(data_dir)
        self.posts = []
        self.load_posts()
    
    def load_posts(self):
        """Load all scraped posts"""
        json_files = list(self.data_dir.glob("*.json"))
        
        for file_path in json_files:
            if file_path.name == "scraping_summary.json":
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    post = json.load(f)
                    self.posts.append(post)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        print(f"Loaded {len(self.posts)} posts")
    
    def get_top_authors(self, limit: int = 10) -> List[tuple]:
        """Get most active authors"""
        author_posts = Counter()
        author_replies = Counter()
        
        for post in self.posts:
            # Count original posts
            author = post.get('author', 'Unknown')
            author_posts[author] += 1
            
            # Count replies
            for reply in post.get('replies', []):
                reply_author = reply.get('author', 'Unknown')
                author_replies[reply_author] += 1
        
        # Combine counts
        total_activity = Counter()
        for author in set(author_posts.keys()) | set(author_replies.keys()):
            total_activity[author] = author_posts[author] + author_replies[author]
        
        return total_activity.most_common(limit)
    
    def get_category_stats(self) -> Dict:
        """Get statistics by category"""
        stats = defaultdict(lambda: {
            'posts': 0,
            'total_replies': 0,
            'total_views': 0,
            'avg_replies': 0,
            'avg_views': 0
        })
        
        for post in self.posts:
            category = post.get('category', 'Unknown')
            stats[category]['posts'] += 1
            stats[category]['total_replies'] += len(post.get('replies', []))
            
            # Use list stats if available
            if 'list_stats' in post:
                stats[category]['total_views'] += post['list_stats'].get('views', 0)
        
        # Calculate averages
        for category, data in stats.items():
            if data['posts'] > 0:
                data['avg_replies'] = data['total_replies'] / data['posts']
                data['avg_views'] = data['total_views'] / data['posts']
        
        return dict(stats)
    
    def search_posts(self, query: str, in_title: bool = True, in_content: bool = True) -> List[Dict]:
        """Search posts by keyword"""
        query_lower = query.lower()
        results = []
        
        for post in self.posts:
            found = False
            
            # Search in title
            if in_title and query_lower in post.get('title', '').lower():
                found = True
            
            # Search in replies content
            if in_content and not found:
                for reply in post.get('replies', []):
                    if query_lower in reply.get('content_text', '').lower():
                        found = True
                        break
            
            if found:
                results.append({
                    'title': post.get('title'),
                    'url': post.get('full_url'),
                    'author': post.get('author'),
                    'replies': len(post.get('replies', [])),
                    'category': post.get('category')
                })
        
        return results
    
    def get_trending_topics(self, days: int = 7) -> List[Dict]:
        """Get topics with most activity in recent days"""
        # This is simplified - in real use, you'd parse the actual timestamps
        trending = []
        
        for post in self.posts:
            activity = post.get('list_stats', {}).get('last_activity', '')
            
            # Simple check for recent activity
            if any(unit in activity for unit in ['m', 'h']) or (activity.endswith('d') and int(activity[:-1]) <= days):
                trending.append({
                    'title': post.get('title'),
                    'replies': len(post.get('replies', [])),
                    'last_activity': activity,
                    'category': post.get('category')
                })
        
        # Sort by reply count
        trending.sort(key=lambda x: x['replies'], reverse=True)
        return trending[:20]
    
    def export_to_markdown(self, output_file: str = "forum_analysis.md"):
        """Export analysis to markdown report"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# EcommerceFuel Forum Analysis\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Overview
            f.write("## Overview\n\n")
            f.write(f"- Total Posts: {len(self.posts)}\n")
            f.write(f"- Total Replies: {sum(len(p.get('replies', [])) for p in self.posts)}\n")
            f.write(f"- Categories: {len(set(p.get('category') for p in self.posts))}\n\n")
            
            # Top Authors
            f.write("## Top Contributors\n\n")
            for author, count in self.get_top_authors(10):
                f.write(f"1. **{author}**: {count} contributions\n")
            f.write("\n")
            
            # Category Stats
            f.write("## Category Statistics\n\n")
            stats = self.get_category_stats()
            f.write("| Category | Posts | Avg Replies | Avg Views |\n")
            f.write("|----------|-------|-------------|----------|\n")
            
            for category, data in sorted(stats.items(), key=lambda x: x[1]['posts'], reverse=True)[:10]:
                f.write(f"| {category} | {data['posts']} | {data['avg_replies']:.1f} | {data['avg_views']:.0f} |\n")
            
            f.write("\n")
            
            # Popular Tags
            f.write("## Popular Tags\n\n")
            all_tags = []
            for post in self.posts:
                all_tags.extend(post.get('tags', []))
            
            tag_counts = Counter(all_tags)
            for tag, count in tag_counts.most_common(15):
                f.write(f"- `{tag}`: {count} posts\n")
        
        print(f"Analysis exported to {output_file}")
    
    def find_unanswered_questions(self) -> List[Dict]:
        """Find posts with no replies"""
        unanswered = []
        
        for post in self.posts:
            if len(post.get('replies', [])) <= 1:  # Only original post
                unanswered.append({
                    'title': post.get('title'),
                    'author': post.get('author'),
                    'url': post.get('full_url'),
                    'category': post.get('category'),
                    'created': post.get('created_at')
                })
        
        return unanswered


def main():
    """Example usage"""
    analyzer = ForumDataAnalyzer()
    
    print("\n=== Top Contributors ===")
    for author, count in analyzer.get_top_authors(5):
        print(f"{author}: {count} contributions")
    
    print("\n=== Category Statistics ===")
    stats = analyzer.get_category_stats()
    for category, data in sorted(stats.items(), key=lambda x: x[1]['posts'], reverse=True)[:5]:
        print(f"{category}: {data['posts']} posts, {data['avg_replies']:.1f} avg replies")
    
    print("\n=== Search Example ===")
    results = analyzer.search_posts("shopify")
    print(f"Found {len(results)} posts mentioning 'shopify'")
    for result in results[:3]:
        print(f"- {result['title']} by {result['author']}")
    
    print("\n=== Trending Topics ===")
    trending = analyzer.get_trending_topics(7)
    for topic in trending[:5]:
        print(f"- {topic['title']} ({topic['replies']} replies, active {topic['last_activity']})")
    
    # Export full analysis
    analyzer.export_to_markdown()
    
    print("\n=== Unanswered Questions ===")
    unanswered = analyzer.find_unanswered_questions()
    print(f"Found {len(unanswered)} posts with no replies")


if __name__ == "__main__":
    main()