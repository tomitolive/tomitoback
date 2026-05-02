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

# --- Core TMDB Functions (Fixed missing functions) ---

def get_tmdb_data(endpoint, params=None, retries=3):
    """Fetches data from TMDB API - Essential for daily_content.py"""
    if params is None: params = {}
    params['api_key'] = TMDB_API_KEY
    for attempt in range(retries):
        try:
            response = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=15)
            if response.status_code == 200:
                return response.json()
            if response.status_code == 429:
                time.sleep(1.5)
                continue
            break
        except Exception as e:
            if attempt < retries - 1: time.sleep(0.5)
    return None

def fetch_details(tmdb_id, media_type):
    """Fetches full details including credits and similar items - Essential for daily_content.py"""
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

# --- Helpers ---
def get_item_url(folder, slug, root='./'):
    if not slug: return "https://tv.tomito.xyz/"
    key = f"{folder}/{slug}"
    if key in LOCAL_SLUGS: return f"{SITE_URL}/{folder}/{slug}"
    return f"https://tv.tomito.xyz/{folder}/{slug}"

def clean_slug(text):
    if not text: return ""
    res = re.sub(r'[أإآ]', 'ا', text)
    res = re.sub(r'[^\w\s-]', '', res).strip().lower()
    res = re.sub(r'[-\s_]+', '-', res)
    return res

# --- Master Template (With Yandex Tag Inside <head>) ---
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

# --- Remaining Functions (create_page, build_listing_pages etc.) ---
# ... (يمكنك إضافة باقي منطق إنشاء الصفحات هنا إذا كنت ستحتاجه في تشغيل يدوي)

if __name__ == "__main__":
    print("Mega Bot Core Loaded Successfully.")
