#!/usr/bin/env python
"""Check LightRAG status from command line"""
import requests
import json
import sys

def check_status(host="localhost", port=9621):
    base_url = f"http://{host}:{port}"
    
    print("🔍 Checking LightRAG Status...")
    print("=" * 60)
    
    try:
        # Check server health
        health = requests.get(f"{base_url}/health")
        if health.status_code != 200:
            print("❌ LightRAG server not responding")
            return
        
        # Get pipeline status
        pipeline_resp = requests.get(f"{base_url}/documents/pipeline_status")
        if pipeline_resp.status_code == 200:
            pipeline = pipeline_resp.json()
            print("\n📊 Pipeline Status:")
            print(f"  Busy: {'Yes' if pipeline.get('busy') else 'No'}")
            print(f"  Current Job: {pipeline.get('job_name', 'None')}")
            print(f"  Documents: {pipeline.get('docs', 0)}")
            print(f"  Current Batch: {pipeline.get('cur_batch', 0)}/{pipeline.get('batchs', 0)}")
            print(f"  Latest: {pipeline.get('latest_message', 'No message')}")
        
        # Get document statuses
        docs_resp = requests.get(f"{base_url}/documents")
        if docs_resp.status_code == 200:
            docs_data = docs_resp.json()
            
            # LightRAG returns statuses grouped by status type
            if isinstance(docs_data, dict) and 'statuses' in docs_data:
                statuses = docs_data['statuses']
                
                print("\n📄 Document Status:")
                status_emojis = {
                    'processed': '✅',
                    'pending': '🔄',
                    'processing': '⏳',
                    'failed': '❌'
                }
                
                total_docs = 0
                for status, docs in statuses.items():
                    count = len(docs) if isinstance(docs, list) else 0
                    total_docs += count
                    if count > 0:
                        emoji = status_emojis.get(status, '❓')
                        print(f"  {emoji} {status.capitalize()}: {count}")
                
                print(f"\n  Total Documents: {total_docs}")
                
                # Show pending documents details
                pending_docs = statuses.get('pending', [])
                if pending_docs:
                    print(f"\n🔄 Pending Documents Details:")
                    for doc in pending_docs[:3]:
                        print(f"  - ID: {doc.get('id', 'unknown')}")
                        print(f"    File: {doc.get('file_path', 'unknown')}")
                        print(f"    Size: {doc.get('content_length', 0):,} chars")
                        print(f"    Created: {doc.get('created_at', 'unknown')[:19]}")
                    if len(pending_docs) > 3:
                        print(f"  ... and {len(pending_docs) - 3} more")
                    
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to LightRAG server")
        print(f"   Make sure it's running on {base_url}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    # Allow custom host/port
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9621
    
    check_status(host, port)