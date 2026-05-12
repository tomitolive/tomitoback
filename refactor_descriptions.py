#!/usr/bin/env python3
import os
import json
import logging
import time
import argparse

# Paths
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
INDEX_FILE = os.path.join(BASE_PATH, 'data', 'content_index.json')

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

# Import project modules
import mega_bot

def refactor_all(limit=10, skip=0):
    if not os.path.exists(INDEX_FILE):
        log.error("Content index not found.")
        return

    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        all_items = json.load(f)

    # Sort by timestamp (oldest first) to prioritize older AI-footprint content
    all_items.sort(key=lambda x: x.get('timestamp', 0))
    
    target_items = all_items[skip : skip + limit]
    log.info(f"🚀 Starting Global Refactor for {len(target_items)} items (skipping {skip})...")

    success = 0
    for i, item in enumerate(target_items):
        tmdb_id = item.get('tmdb_id')
        media_type = item.get('type', 'movie')
        title = item.get('title_ar') or item.get('title')
        
        log.info(f"[{i+1}/{len(target_items)}] Refactoring: {title} ({tmdb_id})")
        
        try:
            # 1. Fetch fresh TMDB data (to get original overview)
            details = mega_bot.fetch_details(str(tmdb_id), media_type)
            if not details:
                log.warning(f"   ⚠️ Could not fetch TMDB details for {tmdb_id}")
                continue
            
            # 2. Re-create the page (this calls the new AI engine with dynamic intro/outro)
            # It will also update the local HTML file and return the updated index entry
            path, updated_entry = mega_bot.create_page(details, media_type)
            
            if updated_entry:
                success += 1
                # The create_page function in mega_bot doesn't update content_index.json directly, 
                # but it returns the entry. We should ideally batch-update later.
                log.info(f"   ✅ Refactored: {path}")
            else:
                log.warning(f"   ❌ Refactor failed for {title}")
                
        except Exception as e:
            log.error(f"   ❌ Error refactoring {title}: {e}")
        
        time.sleep(2) # Avoid aggressive API hits

    log.info(f"🏁 Refactor complete. Successfully updated {success}/{len(target_items)} pages.")
    log.info("💡 Remember to run 'python3 build_homepage.py' and 'python3 generate_full_sitemap.py' after refactoring.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Global Description Refactor Bot")
    parser.add_argument("--limit", type=int, default=10, help="Number of pages to refactor")
    parser.add_argument("--skip", type=int, default=0, help="Number of pages to skip")
    args = parser.parse_args()
    
    refactor_all(limit=args.limit, skip=args.skip)
