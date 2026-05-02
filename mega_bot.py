import requests
import os
import json
import re
import time
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load local slugs for priority linking
LOCAL_INDEX = []
LOCAL_SLUGS = set()
index_path = os.path.join(os.path.dirname(__file__), 'data', 'content_index.json')
if os.path.exists(index_path):
    with open(index_path, 'r', encoding='utf-8') as f:
        LOCAL_INDEX = json.load(f)
        LOCAL_SLUGS = {f"{i.get('folder')}/{i.get('slug')}" for i in LOCAL_INDEX}

def get_item_url(folder, slug, root='./'):
    """Improved URL generator: absolute local path if exists, otherwise external tomito.xyz."""
    if not slug:
        return "https://tv.tomito.xyz/"
    key = f"{folder}/{slug}"
    if key in LOCAL_SLUGS:
        return f"{SITE_URL}/{folder}/{slug}"
    return f"https://tv.tomito.xyz/{folder}/{slug}"

# Import Google Indexing function
try:
    from google_indexer import index_new_page
except ImportError:
    log.error("google_indexer.py not found. Live indexing will be disabled.")
    def index_new_page(url): return "IMPORT_ERROR"

# Import trends_fetcher functions
try:
    from trends_fetcher import clean_strict, fetch_related_keywords
except ImportError:
    log.error("trends_fetcher.py not found or incomplete.")
    def clean_strict(text): return str(text)
    def fetch_related_keywords(title, geo='SA'): return ""

# --- Configuration ---
TMDB_API_KEY = (os.environ.get("TMDB_API_KEY") or "882e741f7283dc9ba1654d4692ec30f6").strip()
GEMINI_API_KEY = (os.environ.get("GEMINI_API_KEY") or "").strip()
BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
SITE_URL = "https://tomito.xyz"
BUTTON_DOMAIN = "https://tv.tomito.xyz"
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
DIRS = ['movie', 'tv', 'movie-trend', 'tv-trend', 'actor', 'data']

# --- Global Content Index Cache ---
_AVAILABLE_IDS = None
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

def get_available_ids():
    global _AVAILABLE_IDS
    if _AVAILABLE_IDS is not None:
        return _AVAILABLE_IDS
    _AVAILABLE_IDS = set()
    path = os.path.join(BASE_PATH, 'data', 'content_index.json')
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
                for item in index_data:
                    tid = item.get('tmdb_id')
                    if tid:
                        _AVAILABLE_IDS.add(int(tid))
        except Exception:
            pass
    return _AVAILABLE_IDS

# SEO keyword banks
SEO_AR = ["مشاهدة", "تحميل", "اون لاين", "بجودة عالية", "HD", "مترجم", "حصري", "2026"]
SEO_EN = ["Watch Online", "Download", "HD Quality", "Full Movie", "Free Streaming"]

# --- Master Template مع إضافة Yandex Verification Tag ---
MASTER_TEMPLATE = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <!-- Yandex Verification -->
  <meta name="yandex-verification" content="fbd3e913244fb343" />
  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-PRCQVS90BX"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-PRCQVS90BX');
  </script>
  <title>{{TITLE_PAGE}}</title>
  <meta name="description" content="{{META_DESC}}">
  <meta name="keywords" content="{{KEYWORDS}}">
  <meta name="robots" content="index, follow, max-image-preview:large">
  <meta property="og:title" content="{{TITLE_OG}}">
  <meta property="og:description" content="{{META_DESC}}">
  <meta property="og:image" content="{{POSTER_URL}}">
  <meta property="og:url" content="{{PAGE_URL}}">
  <meta property="og:type" content="{{OG_TYPE}}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{{TITLE_OG}}">
  <meta name="twitter:image" content="{{POSTER_URL}}">
  <link rel="stylesheet" href="{{ROOT}}style.css">
  <link rel="icon" href="{{ROOT}}favicon.ico">
  <script src="{{ROOT}data/search_index.js"></script>
  <script>const LOCAL_PAGES = {{LOCAL_PAGES_JSON}};</script>
  {{JSON_LD}}
</head>
<body>
  <header class="tomito-header">
  <div class="top-bar">
    <div class="header-container">
      <ul class="top-nav">
        <li><a href="{{ROOT}}">الرئيسية</a></li>
        <li><a href="{{ROOT}}#movies">أفلام</a></li>
        <li><a href="{{ROOT}}#series">مسلسلات</a></li>
        <li><a href="{{ROOT}}genre/animation">أنمي</a></li>
        <li><a href="javascript:void(0)" onclick="toggleMenu()" class="categories-link">التصنيفات ▾</a></li>
      </ul>
      <div class="social-links">
        <a href="https://tv.tomito.xyz/" aria-label="Twitter" target="_blank" rel="noopener noreferrer"><svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24"><path d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z"/></svg></a>
        <a href="https://tv.tomito.xyz/" aria-label="Facebook" target="_blank" rel="noopener noreferrer"><svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24"><path d="M9 8h-3v4h3v12h5v-12h3.642l.358-4h-4v-1.667c0-.955.192-1.333 1.115-1.333h2.885v-5h-3.808c-3.596 0-5.192 1.583-5.192 4.615v3.385z"/></svg></a>
      </div>
    </div>
  </div>
  <div class="bottom-bar">
    <div class="header-container">
      <div class="logo-and-menu">
        <a href="{{ROOT}}" class="logo-link">
          <span class="logo-text">TOMITO</span>
        </a>
        <button class="mobile-menu-btn" onclick="toggleMenu()" aria-label="القائمة">
          <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24"><path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/></svg>
        </button>
      </div>
      <div class="header-search-wrapper">
        <input type="text" id="site-search" placeholder="ابحث عن فيلم أو مسلسل..." onkeyup="siteSearch()" autocomplete="off">
        <div class="search-icon-inside"><svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24"><path d="M21.71 20.29l-5.01-5.01C17.54 13.68 18 11.91 18 10c0-4.41-3.59-8-8-8S2 5.59 2 10s3.59 8 8 8c1.91 0 3.68-.46 5.28-1.3l5.01 5.01c.39.39 1.02.39 1.41 0 .39-.39.39-1.02 0-1.41zM4 10c0-3.31 2.69-6 6-6s6 2.69 6 6-2.69 6-6 6-6-2.69-6-6z"/></svg></div>
        <button class="search-btn" aria-label="بحث">بحث</button>
        <div id="search-suggestions"></div>
      </div>
    </div>
  </div>
</header>
<div class="menu-overlay" id="menu-overlay">
  <div class="menu-categories">{{CATEGORIES_LINKS}}</div>
</div>
{{EXTRA_CONTENT}}
<footer class="footer">
  <p>© 2026 <a href="{{ROOT}}" class="logo-link" style="display:inline-flex; vertical-align:middle; gap:0.25rem;"><span class="logo-text" style="font-size:1.1rem; filter:none;">TOMITO</span></a> — جميع الحقوق محفوظة | <a href="https://myactivity.google.com/">Google Activity</a> | مشاهدة افلام ومسلسلات اون لاين</p>
</footer>
<script>
function getUrl(folder, slug, root = './') {
  const key = `${folder}/${slug}`;
  if (typeof LOCAL_PAGES !== 'undefined' && LOCAL_PAGES.includes(key)) {
    return `${root}${folder}/${slug}`;
  }
  return `https://tv.tomito.xyz/${folder}/${slug}`;
}
async function siteSearch() {
  const q = document.getElementById('site-search').value.toLowerCase();
  const suggCont = document.getElementById('search-suggestions');
  if (q.length < 1) { suggCont.style.display = 'none'; return; }
  if (typeof FULL_INDEX === 'undefined' || FULL_INDEX.length === 0) return;
  const matches = FULL_INDEX.filter(item => {
    const t = (item.title || "").toLowerCase();
    const ta = (item.title_ar || "").toLowerCase();
    const te = (item.title_en || "").toLowerCase();
    return t.includes(q) || ta.includes(q) || te.includes(q);
  });
  matches.sort((a, b) => {
    const aKey = `${a.folder || 'movie'}/${a.slug}`;
    const bKey = `${b.folder || 'movie'}/${b.slug}`;
    const aLocal = typeof LOCAL_PAGES !== 'undefined' && LOCAL_PAGES.includes(aKey);
    const bLocal = typeof LOCAL_PAGES !== 'undefined' && LOCAL_PAGES.includes(bKey);
    if (aLocal && !bLocal) return -1;
    if (!aLocal && bLocal) return 1;
    return 0;
  });
  const topMatches = matches.slice(0, 15);
  if (topMatches.length > 0) {
    suggCont.style.display = 'block';
    suggCont.innerHTML = '';
    topMatches.forEach(item => {
      const folder = item.folder || 'movie';
      const href = getUrl(folder, item.slug, '{{ROOT}}');
      const div = document.createElement('a');
      div.className = 'suggestion-item';
      div.href = href;
      div.innerHTML = `<img src="${item.poster}"> <div><div>${item.title}</div><span class="type">${folder==='movie'?'فيلم':'مسلسل'}</span></div>`;
      suggCont.appendChild(div);
    });
  } else { suggCont.style.display = 'none'; }
}
function toggleMenu() {
  const menu = document.getElementById('menu-overlay');
  if (menu) menu.classList.toggle('active');
}
</script>
</body>
</html>"""

# --- باقي الدوال (create_page, build_listing_pages, etc.) تبقى كما هي تماماً في ملف mega_bot.py ---
