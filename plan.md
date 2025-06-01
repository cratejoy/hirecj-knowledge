# 🚀 Atomic RSS Episode Processing

## 📋 Mission: Transform RSS Processing from Monolithic to Atomic

Currently, when processing an RSS feed with 591 episodes, if the process is interrupted after episode 10, we lose track of episodes 11-591. This forces us to re-fetch the entire feed and re-check all episodes. We're fixing this by atomizing RSS feeds into individual episode work items immediately upon receipt.

## 🌟 North Star Principles

1. **Simplify, Simplify, Simplify**: Every decision should make the code simpler, not more complex
2. **No Cruft**: Remove all redundant code, validation, and unnecessary complexity  
3. **Break It & Fix It Right**: No backwards compatibility shims - make breaking changes and migrate properly
4. **Long-term Elegance**: Choose performant, compiler-enforced solutions that prevent subtle bugs
5. **Single Source of Truth**: One pattern, one way to do things, no alternatives
6. **No Over-Engineering**: Design for current needs only - no hypothetical features

## ✅ Implementation Checklist

### Core Changes
- [ ] Create new `episode` content type in `add_url()`
- [ ] Implement `_atomize_rss_feed()` method to split RSS into episodes
- [ ] Update `process_item()` to atomize RSS feeds instead of processing inline
- [ ] Add `_process_episode()` handler for individual episode items
- [ ] Remove old monolithic `_process_rss()` flow
- [ ] Update `_is_episode_processed()` to check for episode work items too

### Edge Cases
- [ ] Handle RSS feeds with no audio episodes gracefully
- [ ] Respect `--limit` flag during atomization
- [ ] Ensure episode deduplication works across all states

### Testing
- [ ] Test atomization of new RSS feed
- [ ] Test resumption after interruption (kill process mid-atomization)
- [ ] Test deduplication (re-add same RSS feed)
- [ ] Test with `--limit` flag
- [ ] Verify no episodes are lost or duplicated

## 🧪 Simple Test Plan

### Test 1: Basic Atomization
```bash
# Add RSS feed
python src/ingest.py add "https://example.com/podcast.rss"

# Check inbox has individual episodes
ls content/inbox/rss_*_ep*.json | wc -l  # Should match episode count

# Original RSS file should be gone
ls content/inbox/rss_*.json  # Should not include the feed file
```

### Test 2: Interruption Recovery
```bash
# Add large RSS feed
python src/ingest.py add "https://ecommercefuel.libsyn.com/rss"

# Start processing
python src/ingest.py process &

# Kill after a few episodes
sleep 30 && kill %1

# Check nothing lost
ls content/inbox/rss_*_ep*.json  # Unprocessed episodes still in inbox
```

### Test 3: Deduplication
```bash
# Add RSS feed twice
python src/ingest.py add "https://example.com/podcast.rss"
python src/ingest.py add "https://example.com/podcast.rss"

# Should not create duplicate episode files
# Second add should report "0 new episodes"
```

### Test 4: Limit Enforcement
```bash
# Add with limit
python src/ingest.py add "https://example.com/podcast.rss" --limit 5

# Should create exactly 5 episode files
ls content/inbox/rss_*_ep*.json | wc -l  # Should be 5
```

## 🏗️ Architecture

### Before (Monolithic)
```
RSS Feed → Process all 591 episodes in memory → Crash = Lose 580 episodes
```

### After (Atomic)
```
RSS Feed → Create 591 episode files → Delete RSS → Each episode independent
         ↓
    inbox/
    ├── rss_abc_ep001.json  ← Process individually
    ├── rss_abc_ep002.json  ← Interrupt safe
    ├── rss_abc_ep003.json  ← Resume anytime
    └── ...
```

## 🎯 Success Criteria

1. **Zero data loss** - Interruption at any point loses nothing
2. **No reprocessing** - Already processed episodes never re-download
3. **Clean inbox** - One file per work item, no compound objects
4. **Natural resumption** - Just run `process` again, it figures it out

## 📝 LightRAG Document Processing Issue Investigation

### Problem
Documents were getting stuck in "pending" status after being inserted with `ainsert()`.

### Root Cause
LightRAG is designed with an asynchronous processing pipeline. The `ainsert()` method:
1. Enqueues documents for processing
2. Calls `apipeline_process_enqueue_documents()` internally
3. BUT - the actual processing happens asynchronously in a background worker

### Solution
1. Added proper initialization of storages and pipeline status
2. Changed from async `ainsert()` to sync `insert()` method which uses `asyncio.run()`
3. Added status checking after insert to report on pending/processing documents
4. Created `process_pending_docs.py` script to manually trigger processing of pending documents

### Key Findings
- Must call `initialize_storages()` and `initialize_pipeline_status()` before using LightRAG
- The `insert()` method is synchronous but still processes documents asynchronously
- Documents may remain in "pending" status until the processing pipeline runs
- Can manually trigger processing with `apipeline_process_enqueue_documents()`
- The LightRAG server mode (`lightrag-server`) likely handles background processing automatically