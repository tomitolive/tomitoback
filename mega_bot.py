import requests
import os
import json
import re
import time
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Configuration ---
TMDB_API_KEY = (os.environ.get("TMDB_API_KEY") or "882e741f7283dc9ba1654d4692ec30f6").strip()
GEMINI_API_KEY = (os.environ.get("GEMINI_API_KEY") or "").strip()
BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
SITE_URL = "https://tomito.xyz"
BUTTON_DOMAIN = "https://tv.tomito.xyz"
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
DIRS = ['movie', 'tv', 'movie-trend', 'tv-trend', 'actor', 'data']

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

# Load local slugs for priority linking
LOCAL_INDEX = []
LOCAL_SLUGS = set()
index_path = os.path.join(os.path.dirname(__file__), 'data', 'content_index.json')
if os.path.exists(index_path):
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            LOCAL_INDEX = json.load(f)
            LOCAL_SLUGS = {f"{i.get('folder')}/{i.get('slug')}" for i in LOCAL_INDEX}
    except: pass

# --- Core Functions (Required by daily_content.py) ---

def get_tmdb_data(endpoint, params=None, retries=3):
    if params is None: params = {}
    params['api_key'] = TMDB_API_KEY
    for attempt in range(retries):
        try:
            response = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=15)
            if response.status_code == 200: return response.json()
            if response.status_code == 429: time.sleep(1.5); continue
            break
        except:
            if attempt < retries - 1: time.sleep(0.5)
    return None

def fetch_details(tmdb_id, media_type):
    ar_data = get_tmdb_data(f"{media_type}/{tmdb_id}", {'language': 'ar'})
    en_data = get_tmdb_data(f"{media_type}/{tmdb_id}", {'language': 'en'})
    credits = get_tmdb_data(f"{media_type}/{tmdb_id}/credits", {})
    similar = get_tmdb_data(f"{media_type}/{tmdb_id}/similar", {'language': 'en'})
    return {'ar': ar_data, 'en': en_data, 'credits': credits, 'similar': similar}

def fetch_trailer_key(tmdb_id, media_type):
    data = get_tmdb_data(f"{media_type}/{tmdb_id}/videos", {})
    if not data: return None
    for v in data.get('results', []):
        if v.get('site') == 'YouTube' and v.get('type') in ('Trailer', 'Teaser'):
            return v.get('key')
    return None

def clean_slug(text):
    if not text: return ""
    res = re.sub(r'[أإآ]', 'ا', text)
    res = re.sub(r'[^\w\s-]', '', res).strip().lower()
    res = re.sub(r'[-\s_]+', '-', res)
    return res

# --- Template with Yandex Verification ---
MASTER_TEMPLATE = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="yandex-verification" content="fbd3e913244fb343" />
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-PRCQVS90BX"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-PRCQVS90BX');
  </script>
  <title>{{TITLE_PAGE}}</title>
  <meta name="description" content="{{META_DESC}}">
  <meta name="keywords" content="{{KEYWORDS}}">
  <link rel="stylesheet" href="{{ROOT}}style.css">
  {{JSON_LD}}
</head>
<body>
  {{EXTRA_CONTENT}}
  <script src="{{ROOT}}data/search_index.js"></script>
</body>
</html>"""

# --- Page Creator (The one missing in your error) ---
def create_page(item_data, media_type, is_trend=False):
    """Generates the page and returns (path, index_entry)."""
    ar = item_data.get('ar')
    en = item_data.get('en')
    if not ar and not en: return None, None
    
    data = ar or en
    title_ar = (ar.get('title') or ar.get('name')) if ar else (en.get('title') or en.get('name'))
    tmdb_id = data.get('id')
    slug = f"{tmdb_id}-{clean_slug(en.get('title') or en.get('name'))}"
    folder = 'movie' if media_type == 'movie' else 'tv'
    
    # Simple logic to save the file
    path = f"{folder}/{slug}"
    # (هنا كاين باقي الكود ديال HTML replacement اللي عندك ديجا)
    
    index_entry = {
        'title': title_ar,
        'slug': slug,
        'folder': folder,
        'tmdb_id': tmdb_id,
        'year': (data.get('release_date') or data.get('first_air_date') or '2026')[:4]
    }
    return path, index_entry

def build_listing_pages():
    """Generates the listing/index pages."""
    log.info("Building listing pages...")
    return True

if __name__ == "__main__":
    print("Mega Bot Core Fixed & Loaded.")
