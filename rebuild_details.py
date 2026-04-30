import os
import json
import logging
from mega_bot import create_page

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
        # Re-map data to common format if needed
        # create_page(media_type, tmdb_id, slug=None, folder=None, meta_data=None, tri=None)
        # Note: In our current index, we store them as already processed items
        # But we need the raw TMDB ID and media_type to re-generate properly.
        tmdb_id = item.get('tmdb_id')
        media_type = 'movie' if item.get('folder') == 'movie' else 'tv'
        slug = item.get('slug')
        
        if not tmdb_id: continue
        
        try:
            # We pass meta_data and tri as None to let mega_bot fetch/use its cache
            create_page(media_type, tmdb_id, slug=slug, folder=item.get('folder'))
            count += 1
            if count % 100 == 0:
                log.info(f"Rebuilt {count} pages...")
        except Exception as e:
            log.error(f"Failed to rebuild {slug}: {e}")

    log.info(f"✅ Rebuild complete. Total: {count} pages.")

if __name__ == '__main__':
    rebuild()
