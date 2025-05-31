# Content Pipeline Fix Plan

## 🌟 North Star Principles

1. **Simplify, Simplify, Simplify**: Every decision should make the code simpler, not more complex
2. **No Cruft**: Remove all redundant code, validation, and unnecessary complexity  
3. **Break It & Fix It Right**: No backwards compatibility shims - make breaking changes and migrate properly
4. **Long-term Elegance**: Choose performant, compiler-enforced solutions that prevent subtle bugs
5. **Single Source of Truth**: One pattern, one way to do things, no alternatives
6. **No Over-Engineering**: Design for current needs only - no hypothetical features

## ✅ Fix Checklist

- [ ] **Make RSS feeds resumable** - Don't delete RSS feed file until ALL episodes processed
- [ ] **Add episode progress tracking** - Track which episodes succeeded/failed per RSS feed
- [ ] **Handle timeouts gracefully** - Save progress and allow continuation 
- [ ] **Fix count discrepancy** - Ensure status command shows accurate totals
- [ ] **Add RSS resume command** - Simple way to continue processing interrupted feeds
- [ ] **Improve error visibility** - Show WHY episodes failed, not just that they failed

## 🔍 Problem Diagnosis

### The Core Issue
We discovered that when processing the eCommerceFuel RSS feed with 591 episodes:
1. Only ~4 episodes were successfully processed before timeout
2. The RSS feed tracking file was deleted after the timeout
3. No way to resume processing the remaining 587 episodes
4. No visibility into what happened to those episodes

### Root Causes

#### 1. Destructive Cleanup
```python
finally:
    # This ALWAYS runs, even on timeout/interrupt
    downloading_file = self.base_dir / 'downloading' / item_file.name  
    if downloading_file.exists():
        downloading_file.unlink()  # ← Deletes RSS feed tracker!
```

#### 2. No Progress Persistence
- RSS feeds process all episodes in a single run
- No checkpointing between episodes
- No record of which episodes were attempted

#### 3. Silent Failures
- Episodes that fail to download continue silently
- No aggregate reporting of success/failure rates
- No way to retry failed episodes

## 📋 Detailed Fix Plans

### 1. Make RSS Feeds Resumable

**Current behavior**: RSS feed file deleted after ANY exit (success, failure, timeout)

**Fix**: Move RSS feed file to a "completed" state only after ALL episodes processed

```python
def _process_rss(self, rss_url: str, feed_id: str, limit: int = None):
    # ... existing code ...
    
    # Track progress
    total_episodes = len(audio_episodes)
    processed_episodes = 0
    failed_episodes = 0
    
    for episode in audio_episodes:
        try:
            self._process_episode(episode, episode_id, feed_title, rss_url)
            processed_episodes += 1
        except Exception as e:
            failed_episodes += 1
            
    # Only mark as complete if ALL episodes processed
    if processed_episodes + failed_episodes >= total_episodes:
        return "completed"
    else:
        return "partial"  # Don't delete the feed file!
```

### 2. Add Episode Progress Tracking

**Current behavior**: No record of which episodes from a feed have been processed

**Fix**: Create a progress file for each RSS feed

```python
# content/progress/rss_{feed_id}.json
{
    "feed_url": "https://example.com/rss",
    "total_episodes": 591,
    "processed_episodes": ["ep12345", "ep67890"],
    "failed_episodes": {"ep11111": "Download timeout"},
    "last_updated": "2024-05-31T10:00:00"
}
```

### 3. Handle Timeouts Gracefully

**Current behavior**: Timeout kills entire process, loses all state

**Fix**: Catch timeout at episode level, save progress after each episode

```python
def _process_episode_with_timeout(self, episode, episode_id, feed_title, feed_url, timeout=300):
    """Process single episode with timeout protection"""
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Episode processing timeout")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    
    try:
        self._process_episode(episode, episode_id, feed_title, feed_url)
    finally:
        signal.alarm(0)  # Cancel timeout
        self._save_progress()  # Always save progress
```

### 4. Fix Count Discrepancy

**Current behavior**: Status shows items in pipeline but not total episodes in RSS feeds

**Fix**: Show RSS feed episode counts in status

```python
def status(self):
    # ... existing code ...
    
    # Add RSS feed status section
    print("\n📡 RSS Feed Status")
    print("=" * 60)
    
    # Check progress files
    progress_files = list((self.base_dir / 'progress').glob('rss_*.json'))
    for pf in progress_files:
        with open(pf) as f:
            progress = json.load(f)
        total = progress['total_episodes']
        done = len(progress['processed_episodes'])
        failed = len(progress['failed_episodes'])
        remaining = total - done - failed
        
        print(f"Feed: {progress['feed_url'][:50]}...")
        print(f"  Total: {total}, Done: {done}, Failed: {failed}, Remaining: {remaining}")
```

### 5. Add RSS Resume Command

**Current behavior**: No way to resume interrupted RSS feeds

**Fix**: Add `resume` command that finds partial RSS feeds

```python
elif command == "resume":
    # Find RSS feeds that were partially processed
    partial_feeds = processor.find_partial_feeds()
    if partial_feeds:
        print(f"Found {len(partial_feeds)} partial feed(s) to resume")
        for feed in partial_feeds:
            processor.resume_rss_feed(feed)
    else:
        print("No partial feeds to resume")
```

### 6. Improve Error Visibility

**Current behavior**: Episodes fail silently with generic errors

**Fix**: Create detailed error log for each RSS feed

```python
# content/logs/rss_{feed_id}_errors.log
2024-05-31 10:00:00 - Episode 45: "Interview with CEO" - FAILED
  Error: HTTP 503 - Server temporarily unavailable
  URL: https://example.com/episode45.mp3
  Retry attempts: 3

2024-05-31 10:05:00 - Episode 89: "Q4 Report" - FAILED  
  Error: File too large (312MB) - exceeds timeout
  URL: https://example.com/episode89.mp3
```

## 🚀 Implementation Priority

1. **Immediate**: Fix RSS feed deletion (prevents data loss)
2. **High**: Add progress tracking (enables resumption)
3. **Medium**: Add resume command (user convenience)
4. **Low**: Enhanced error logging (debugging aid)

## 💡 Alternative Approach

If we want to stay simple per our North Stars, we could:
1. Process RSS feeds one episode at a time
2. Treat each episode as a separate work item
3. Delete RSS feed only after creating all episode work items

This would naturally make everything resumable without complex state tracking.