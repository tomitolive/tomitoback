import os
import json
import logging
import mega_bot

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
INDEX_FILE = os.path.join(BASE_PATH, 'data', 'content_index.json')

def rebuild():
    if not os.path.exists(INDEX_FILE):
        log.error("Index file not found.")
        return

    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    log.info(f"Starting rebuild of {len(data)} pages...")
    
    count = 0
    for item in data:
        # mega_bot.create_page(item_data, media_type, is_trend=False)
        # We need to make sure 'id' is in item (it's often 'tmdb_id' in our index, so we map it)
        if 'id' not in item and 'tmdb_id' in item:
            item['id'] = item['tmdb_id']
            
        media_type = 'movie' if item.get('folder') == 'movie' else 'tv'
        
        try:
            mega_bot.create_page(item, media_type)
            count += 1
            if count % 100 == 0:
                log.info(f"Rebuilt {count} pages...")
        except Exception as e:
            log.error(f"Failed to rebuild {item.get('slug')}: {e}")

    log.info(f"✅ Rebuild complete. Total: {count} pages.")

if __name__ == '__main__':
    rebuild()
