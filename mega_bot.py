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

def get_item_url(folder, slug, root="./"):
    key = f"{folder}/{slug}"
    if key in LOCAL_SLUGS:
        return f"{root}{folder}/{slug}.html"
    return f"https://tv.tomito.xyz/{folder}/{slug}"

# Import Google Indexing function
try:
    from google_indexer import index_new_page
except ImportError:
    log.error("google_indexer.py not found. Live indexing will be disabled.")
    def index_new_page(url): return "IMPORT_ERROR"

# Import trends_fetcher functions at top to avoid ImportError in creator functions
try:
    from trends_fetcher import clean_strict, fetch_related_keywords
except ImportError:
    log.error("trends_fetcher.py not found or incomplete.")
    def clean_strict(text): return str(text)
    def fetch_related_keywords(title, geo='SA'): return ""

# --- Configuration ---
TMDB_API_KEY = (os.environ.get("TMDB_API_KEY") or "882e741f7283dc9ba1654d4692ec30f6").strip()
GEMINI_API_KEY = (os.environ.get("GEMINI_API_KEY") or "AIzaSy...").strip()
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
SEO_AR = [
    "مشاهدة", "تحميل", "اون لاين", "بجودة عالية", "HD", "مترجم",
    "حصري", "2026", "2025", "2024", "بدون اعلانات", "مجاناً",
    "كامل", "جودة BluRay", "مسلسلات", "افلام", "انمي"
]
SEO_EN = [
    "Watch Online", "Download", "HD Quality", "Full Movie", "Free Streaming",
    "English Subtitles", "BluRay", "2026", "Exclusive", "No Ads"
]

# --- Master Template (CSS uses style.css — flat path for all pages) ---
MASTER_TEMPLATE = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
  <script src="{{ROOT}}data/search_index.js"></script>
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
      <div class="menu-categories">
        {{CATEGORIES_LINKS}}
      </div>
    </div>

  {{EXTRA_CONTENT}}

  <footer class="footer">
    <p>© 2026 <a href="{{ROOT}}" class="logo-link" style="display:inline-flex; vertical-align:middle; gap:0.25rem;"><span class="logo-text" style="font-size:1.1rem; filter:none;">TOMITO</span></a> — جميع الحقوق محفوظة | <a href="https://myactivity.google.com/">Google Activity</a> | مشاهدة افلام ومسلسلات اون لاين</p>
  </footer>

  <script>
  function getUrl(folder, slug, root = './') {
    const key = `${folder}/${slug}`;
    if (typeof LOCAL_PAGES !== 'undefined' && LOCAL_PAGES.includes(key)) {
      return `${root}${folder}/${slug}.html`;
    }
    return `https://tv.tomito.xyz/${folder}/${slug}`;
  }

  async function siteSearch() {
    const q = document.getElementById('site-search').value.toLowerCase();
    const suggCont = document.getElementById('search-suggestions');
    if (q.length < 1) { suggCont.style.display = 'none'; return; }

    if (typeof FULL_INDEX === 'undefined' || FULL_INDEX.length === 0) {
      console.error("Search index not loaded.");
      return;
    }

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
        const slug = item.slug;
        const href = getUrl(folder, slug, '{{ROOT}}');
        const img = item.poster;
        const type = folder === 'movie' ? 'فيلم' : 'مسلسل';
        const div = document.createElement('a');
        div.className = 'suggestion-item';
        div.href = href;
        div.innerHTML = `<img src="${img}"> <div><div>${item.title}</div><span class="type">${type}</span></div>`;
        suggCont.appendChild(div);
      });
    } else { suggCont.style.display = 'none'; }
  }

  function toggleMenu() {
    const menu = document.getElementById('menu-overlay');
    if (menu) menu.classList.toggle('active');
    if (menu && menu.classList.contains('active')) {
      const s = document.getElementById('site-search');
      if (s) s.focus();
    }
  }

  document.addEventListener('click', (e) => {
    const menu = document.getElementById('menu-overlay');
    if (menu && !menu.contains(e.target) && !e.target.closest('.categories-link') && !e.target.closest('.mobile-menu-btn')) {
      menu.classList.remove('active');
    }
    if (!e.target.closest('.header-search-wrapper')) {
      const suggs = document.getElementById('search-suggestions');
      if (suggs) suggs.style.display = 'none';
    }
  });

  function showMoreCards(btn) {
    const section = btn.closest('.section');
    const hidden = section.querySelectorAll('.card.hidden-card');
    hidden.forEach((c, i) => {
      if (i < 20) c.classList.remove('hidden-card');
    });
    if (section.querySelectorAll('.card.hidden-card').length === 0) {
      btn.parentElement.style.display = 'none';
    }
  }
  </script>
</body>
</html>"""

# --- Category Links Helper ---
def get_category_links_html(root_path="./"):
    """Generates the HTML for the categories dropdown."""
    try:
        from ai_engine import BOT_MISSIONS
    except ImportError:
        return ""
    
    links = ""
    for m in BOT_MISSIONS:
        slug = clean_slug(m["name"])
        links += f'<a href="{root_path}genre/{slug}">{m["label"]}</a>\n'
    return links

# --- Utilities ---
def clean_slug(text):
    if not text: return ""
    # Remove Arabic specific accents
    res = re.sub(r'[أإآ]', 'ا', text)
    # Remove all non-word characters except spaces and hyphens
    # \w matches letters, numbers and underscore. 
    # To keep other languages but avoid symbols, we can be more careful
    res = re.sub(r'[^\w\s-]', '', res).strip().lower()
    res = re.sub(r'[-\s_]+', '-', res)
    return res

def get_tmdb_data(endpoint, params, retries=3):
    params['api_key'] = TMDB_API_KEY
    for attempt in range(retries):
        try:
            response = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=15)
            if response.status_code == 200:
                return response.json()
            if response.status_code == 429:
                time.sleep(1.5)
                continue
            log.error(f"TMDB API Error {response.status_code}: {response.text}")
            break
        except Exception:
            if attempt < retries - 1:
                time.sleep(0.5)
    return None


def fetch_trailer_key(tmdb_id, media_type):
    """Returns the first YouTube trailer key from TMDB, or None."""
    data = get_tmdb_data(f"{media_type}/{tmdb_id}/videos", {})
    if not data:
        return None
    for v in data.get('results', []):
        if v.get('site') == 'YouTube' and v.get('type') in ('Trailer', 'Teaser'):
            return v.get('key')
    return None

def fetch_details(tmdb_id, media_type):
    ar_data = get_tmdb_data(f"{media_type}/{tmdb_id}", {'language': 'ar'})
    en_data = get_tmdb_data(f"{media_type}/{tmdb_id}", {'language': 'en'})
    credits = get_tmdb_data(f"{media_type}/{tmdb_id}/credits", {})
    similar = get_tmdb_data(f"{media_type}/{tmdb_id}/similar", {'language': 'en'})
    return {'ar': ar_data, 'en': en_data, 'credits': credits, 'similar': similar}

def build_keywords(title_ar, title_en, media_type, year, genres_ar):
    # Rule: 100% Arabic intent keywords
    kw = [
        f"مشاهدة {title_ar} مجانية", f"تحميل {title_ar} مباشر", 
        f"مشاهدة {title_ar} مترجم", f"{title_ar} اون لاين",
        f"mochahada {title_ar} majaniya", f"watch {title_en} free",
        title_ar, title_en,
    ]
    if media_type == 'movie':
        kw += [f"فيلم {title_ar} كامل", f"تحميل فيلم {title_ar}"]
    else:
        kw += [f"مسلسل {title_ar} مترجم", f"مشاهدة مسلسل {title_ar}"]
    kw += genres_ar
    return ", ".join(kw[:25])

def generate_seo_description_v2(ar_data, en_data, title_ar, year, type_label):
    """Legacy fallback — returns (desc_ar, desc_en, keywords)."""
    ar_desc = ar_data.get('overview', '') if ar_data else ''
    en_desc = en_data.get('overview', '') if en_data else ''
    seo_ar = f"مشاهدة وتحميل {title_ar} ({year}) اون لاين بجودة عالية HD مترجم حصرياً بدون إعلانات على توميتو."
    seo_en = f"Watch and download {title_ar} ({year}) online in full HD quality, translated, exclusively on TOMITO with no ads."
    full_ar = f"{ar_desc[:300]}. {seo_ar}" if len(ar_desc) > 30 else seo_ar
    full_en = f"{en_desc[:300]}. {seo_en}" if len(en_desc) > 30 else seo_en
    return full_ar.strip(), full_en.strip(), ""

def _build_v7_extra_content(
    title_ar, title_en, year, rating, rating_count,
    genres_ar, genres_en, director, cast_data_full,
    desc_ar, desc_en,
    faq_html, youtube_key, media_type,
    tomito_opinion=None,
    page_intro=None, page_outro=None
):
    """Assembles the main V7 content block injected into {{EXTRA_CONTENT}}."""
    ar_type = "فيلم" if media_type == 'movie' else "مسلسل"

    # ── 1. Intro paragraph — unique per page ─────────────────────────────────
    opinion_html = ""
    if tomito_opinion:
        opinion_html = f"""
<section class="section v7-opinion" style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px; margin-bottom: 20px; border-right: 4px solid var(--accent-color, #ff4d4d);">
  <h2 class="section-title" style="margin-top:0;">لماذا تشاهد هذا العمل؟ (رأي توميتو)</h2>
  <p class="v7-opinion-text" style="font-style: italic; color: #eee; line-height: 1.8;">
    "{tomito_opinion}"
  </p>
</section>"""

    # Use AI-generated intro if available, otherwise fallback to static template
    if page_intro and len(page_intro) > 30:
        intro_body = page_intro
    else:
        intro_body = (f"يُتيح لك موقع <strong>توميتو</strong> مشاهدة {ar_type} <strong>{title_ar}</strong> ({title_en})"
                      f" بجودة عالية HD مترجماً إلى العربية بشكل حصري وبدون إعلانات مزعجة."
                      f" استمتع بتجربة بث مباشر سلسة أو اختر التحميل المباشر بجودة تصل إلى 1080p.")

    intro_html = f"""
<section class="section v7-intro">
  <h1 class="v7-h1">مشاهدة وتحميل {ar_type} {title_ar} مترجم كامل HD بجودة عالية</h1>
  <p class="v7-intro-text">{intro_body}</p>
</section>
{opinion_html}"""

    # ── 2. Language Switcher + Bilingual Descriptions ───────────────────────
    desc_ar_safe  = desc_ar  or f"مشاهدة وتحميل {ar_type} {title_ar} {year} بجودة HD مترجم حصرياً بدون إعلانات على توميتو."
    desc_en_safe  = desc_en  or f"Watch and download {title_en} ({year}) in full HD, translated, exclusively on TOMITO."

    lang_html = f"""
<section class="section v7-lang-section">
  <div class="lang-switcher" role="tablist" aria-label="اختر اللغة">
    <button class="lang-btn active" onclick="switchLang('ar')" id="btn-ar">العربية</button>
    <button class="lang-btn" onclick="switchLang('en')" id="btn-en">English</button>
  </div>
  <div id="desc-ar" class="lang-content">{desc_ar_safe}</div>
  <div id="desc-en" class="lang-content" style="display:none;">{desc_en_safe}</div>
</section>
<script>
function switchLang(lang){{
  ['ar','en'].forEach(function(l){{
    var desc = document.getElementById('desc-'+l);
    if(desc) desc.style.display = l===lang?'block':'none';
    var btn = document.getElementById('btn-'+l);
    if(btn) btn.classList.toggle('active', l===lang);
  }});
}}
</script>"""

    # ── 3. YouTube Trailer ───────────────────────────────────────────────────
    trailer_html = ""
    if youtube_key:
        trailer_html = f"""
<section class="section v7-trailer">
  <h2 class="section-title">الإعلان الرسمي — Official Trailer</h2>
  <div class="video-container">
    <iframe
      src="https://www.youtube.com/embed/{youtube_key}?rel=0&modestbranding=1"
      title="{title_ar} — Trailer"
      width="100%" height="450"
      frameborder="0" allowfullscreen
      loading="lazy"
    ></iframe>
  </div>
</section>"""

    # ── 4. Technical Table ───────────────────────────────────────────────────
    director_str = director or "—"
    
    # Rule 4: Internal Linking (Cast)
    cast_links = []
    if cast_data_full:
        for c in cast_data_full[:8]:
            c_name = c.get('name')
            c_id = c.get('id')
            if c_name and c_id:
                c_slug = f"{c_id}-{clean_slug(c_name)}"
                cast_links.append(f'<a href="../actor/{c_slug}" class="v7-cast-link">{c_name}</a>')
    cast_str = "، ".join(cast_links) if cast_links else "—"
    
    genres_str = "، ".join(genres_ar[:4]) if genres_ar else "—"

    table_html = f"""
<section class="section v7-tech">
  <h2 class="section-title">تفاصيل العرض</h2>
  <table class="tech-table">
    <tr><th>التقييم</th><td>{rating} / 10 ⭐ ({rating_count} تقييم)</td></tr>
    <tr><th>التصنيف</th><td>{genres_str}</td></tr>
    <tr><th>الجودة المتاحة</th><td>4K · 1080p · 720p · BluRay</td></tr>
    <tr><th>الترجمة</th><td>العربية · الإنجليزية</td></tr>
  </table>
</section>"""

    # ── 5. FAQ ───────────────────────────────────────────────────────────────
    faq_block = ""
    if faq_html:
        faq_block = f"""
<section class="section v7-faq">
  <h2 class="section-title">الأسئلة الشائعة</h2>
  {faq_html}
</section>"""
    else:
        # Static fallback FAQ
        faq_block = f"""
<section class="section v7-faq">
  <h2 class="section-title">الأسئلة الشائعة</h2>
  <div class="faq-item">
    <div class="faq-question">متى يتوفر {ar_type} {title_ar} على موقع توميتو؟</div>
    <div class="faq-answer">{ar_type} {title_ar} متاح الآن للمشاهدة والتحميل مباشرةً على موقع توميتو بجودة 1080p مترجماً إلى العربية وكذلك بخيارات جودة أخرى تصل إلى 4K.</div>
  </div>
  <div class="faq-item">
    <div class="faq-question">كيف يمكنني تحميل {title_ar} بجودة 1080p؟</div>
    <div class="faq-answer">يمكنك تحميل {ar_type} {title_ar} عبر الضغط على زر التحميل في صفحة المحتوى على توميتو. تتوفر جودات متعددة من بينها 720p و1080p وBluRay بدون أي رسوم أو تسجيل.</div>
  </div>
  <div class="faq-item">
    <div class="faq-question">هل مشاهدة {title_ar} مجانية وبدون إعلانات على توميتو؟</div>
    <div class="faq-answer">نعم، يُقدِّم موقع توميتو خدمة بث مباشر مجانية لـ {ar_type} {title_ar} {year} بدون إعلانات مزعجة، مع ترجمة عربية احترافية ومزامنة دقيقة.</div>
  </div>
</section>"""

    # ── 6. Unique Outro / Closing Recommendation ─────────────────────────────
    outro_html = ""
    if page_outro and len(page_outro) > 20:
        outro_html = f"""
<section class="section v7-outro" style="background: rgba(255,109,31,0.06); padding: 20px; border-radius: 12px; border-right: 4px solid #FF6D1F; margin-top: 20px;">
  <p style="color:#eee; line-height:1.9; margin:0;">{page_outro}</p>
</section>"""

    return intro_html + lang_html + trailer_html + table_html + faq_block + outro_html

def build_similar_content_html(similar_data, media_type, genre_slug=None):
    """Build similar content HTML section with local priority."""
    if not similar_data or not similar_data.get('results'):
        return ''
    
    available_ids = get_available_ids()
    results = similar_data.get('results', [])
    
    # Priority: items from results that exist in our database
    local_similar = [r for r in results if r.get('id') and int(r.get('id')) in available_ids]
    # Rest: items that don't exist in our database
    external_similar = [r for r in results if r.get('id') and int(r.get('id')) not in available_ids]
    
    # Combined list for display (limit to 12 total)
    filtered = (local_similar + external_similar)[:12]
    if not filtered: return ''

    def card(item, folder):
        tmdb_id = item.get('id', '')
        title = item.get('title') or item.get('name') or ''
        poster = f"{IMAGE_BASE_URL}{item['poster_path']}"
        slug_part = clean_slug(title)
        slug = f"{tmdb_id}-{slug_part}" if slug_part else str(tmdb_id)
        rating = round(item.get('vote_average', 0), 1)
        badge = f"{rating}⭐" if rating else "حصري"
        
        # Determine URL based on local existence
        href = get_item_url(folder, slug, root="../")
        
        return f'''    <a class="card" href="{href}">
      <img class="card-poster" src="{poster}" alt="{title} — مشاهدة وتحميل اون لاين" loading="lazy" onerror="this.src='../favicon.ico'">
      <div class="card-overlay"><div class="card-meta">{badge}</div></div>
      <div class="card-bottom"><div class="card-title">{title}</div></div>
    </a>'''

    folder = 'movie' if media_type == 'movie' else 'tv'
    title_ar = "أفلام مشابهة" if media_type == 'movie' else "مسلسلات مشابهة"
    
    html = f'<section class="section"><h2 class="section-title">{title_ar}</h2><div class="grid">'
    html += ''.join(card(r, folder) for r in filtered)
    html += '</div>'
    
    # Link "Mazid" button to genre or category
    redirect_slug = genre_slug or ("movie" if media_type == 'movie' else "tv-show")
    html += f'''<div class="load-more-container"><a href="../genre/{redirect_slug}.html" class="load-more-btn"><span>مشاهدة المزيد</span> <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg></a></div>'''
    html += '</section>'
    return html


def create_page(item_data, media_type, is_trend=False):
    ar, en, credits = item_data['ar'], item_data['en'], item_data['credits']
    if not ar and not en:
        return None, None

    data = ar or en
    # from trends_fetcher import clean_strict (moved to top)
    title_ar = clean_strict((ar.get('title') or ar.get('name') or '') if ar else '')
    title_en = clean_strict((en.get('title') or en.get('name') or '') if en else '')
    if not title_ar: title_ar = title_en
    if not title_en: title_en = title_ar
    tmdb_id = data.get('id')
    slug = clean_slug(title_en) or f"{media_type}-{tmdb_id}"
    if media_type == 'movie' or 'tv' in media_type:
        slug = f"{tmdb_id}-{slug}"
    poster_path = data.get('poster_path') or (en.get('poster_path') if en else None) or (ar.get('poster_path') if ar else None)
    if not poster_path:
        return None, None
    poster_url = f"{IMAGE_BASE_URL}{poster_path}"
    year = (data.get('release_date') or data.get('first_air_date') or '2026')[:4]
    rating = round(data.get('vote_average', 0), 1)
    rating_count = data.get('vote_count', 0)
    
    # Fix: Ensure rating is within range 1-10 for Google Search Console
    if rating == 0:
        rating = 7.0
        rating_count = 10
    elif not rating_count or rating_count == 0:
        rating_count = 1

    # ── Genres ──────────────────────────────────────────────────────────────────
    genres_ar = [g.get('name', '') for g in (ar.get('genres', []) if ar else [])]
    genres_en = [g.get('name', '') for g in (en.get('genres', []) if en else [])]

    # ── Media-type routing (final, authoritative) ────────────────────────────
    if media_type == 'movie':
        watch_url = "#player"
        folder = 'movie'
        schema_type = 'Movie'
        type_label = "فيلم"
    elif 'anime' in media_type:
        watch_url = f"{SITE_URL}/tv/{tmdb_id}/watch?season=1&episode=1"
        folder = 'tv'
        schema_type = 'TVSeries'
        type_label = "أنمي"
    else:
        watch_url = f"{SITE_URL}/tv/{tmdb_id}/watch?season=1&episode=1"
        folder = 'tv'
        schema_type = 'TVSeries'
        type_label = "مسلسل"

    page_url = f"{SITE_URL}/{folder}/{slug}"

    # ── Director & Cast ───────────────────────────────────────────────────────
    cast_data = credits.get('cast', []) if credits else []
    crew_data = credits.get('crew', []) if credits else []
    director = next(
        (c.get('name') for c in crew_data if c.get('job') == 'Director'), None
    )
    cast_names = [c.get('name') for c in cast_data[:8] if c.get('name')]

    # ── YouTube Trailer ───────────────────────────────────────────────────────
    youtube_key = fetch_trailer_key(tmdb_id, media_type)

    # ── V7 Trilingual Description (OpenRouter large model) ───────────────────
    try:
        from ai_engine import (
            generate_bilingual_description, 
            generate_faq, 
            generate_meta_tags,
            generate_tomito_opinion,
            generate_page_intro_outro
        )
        tri = generate_bilingual_description(
            title_ar, title_en,
            ar.get('overview', '') if ar else '',
            en.get('overview', '') if en else '',
            year, genres_ar, media_type
        )
        desc_ar   = (tri or {}).get('desc_ar') or ''
        desc_en   = (tri or {}).get('desc_en') or ''
        
        # Optimized: Use results from tri or fallback to separate calls
        meta_data = tri if (tri and 'meta_desc' in tri) else generate_meta_tags(title_ar, title_en, year, genres_ar, media_type)
        tomito_opinion = (tri or {}).get('opinion') or generate_tomito_opinion(title_ar, title_en, year, media_type)
        faq_html  = generate_faq(title_ar, title_en, year, media_type)

        # Unique intro + outro per page
        page_intro, page_outro = generate_page_intro_outro(
            title_ar, title_en, year, genres_ar, media_type, desc_ar
        )

    except Exception as e:
        log.error(f"AI V7 failed ({e}). Aborting page generation to guarantee unique content.")
        return None, None

    if not desc_ar or not desc_en or len(desc_ar) < 50:
        log.error("AI returned empty or extremely short descriptions. Aborting to prevent generic fallbacks.")
        return None, None

    # Fallback for page_intro/outro if AI failed
    if 'page_intro' not in dir():
        page_intro, page_outro = None, None

    # ── Keywords ──────────────────────────────────────────────────────────────
    # Try keywords from tri first, then generate_seo_content (meta_data), then build_keywords
    keywords = (tri or {}).get('keywords') or (meta_data or {}).get('keywords')
    if not keywords:
        keywords = build_keywords(title_ar, title_en, media_type, year, genres_ar)
    
    # from trends_fetcher import clean_strict (moved to top)
    keywords = clean_strict(keywords)

    # Similar Content
    similar_html = build_similar_content_html(item_data.get('similar'), media_type)

    # ── V7 Extra Content Block ────────────────────────────────────────────────
    v7_block = _build_v7_extra_content(
        title_ar=title_ar, title_en=title_en, year=year,
        rating=rating, rating_count=rating_count,
        genres_ar=genres_ar, genres_en=genres_en,
        director=director, cast_data_full=cast_data,
        desc_ar=desc_ar, desc_en=desc_en,
        faq_html=faq_html, youtube_key=youtube_key,
        media_type=media_type,
        tomito_opinion=tomito_opinion,
        page_intro=page_intro, page_outro=page_outro
    )
    extra_content = v7_block + similar_html

    # ── Tags ──────────────────────────────────────────────────────────────────
    tags = [type_label, f"⭐ {rating}", year] + genres_en[:3]
    tags_html = '<div class="series-tags">' + ''.join(f'<span class="tag">{t}</span>' for t in tags) + '</div>'

    # ── Full Schema.org JSON-LD ───────────────────────────────────────────────
    breadcrumb_ld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "الرئيسية", "item": SITE_URL},
            {"@type": "ListItem", "position": 2, "name": type_label.split('|')[-1].strip(), "item": f"{SITE_URL}/{folder}"},
            {"@type": "ListItem", "position": 3, "name": title_ar, "item": page_url},
        ],
        "dateModified": datetime.now().strftime('%Y-%m-%d')
    }

    full_release_date = (data.get('release_date') or data.get('first_air_date') or '2026-01-01')
    if len(full_release_date) == 4: full_release_date += "-01-01"
    
    main_ld = {
        "@context": "https://schema.org",
        "@type": schema_type,
        "name": f"{title_ar} / {title_en}",
        "alternateName": title_en,
        "description": desc_ar[:500],
        "image": poster_url,
        "datePublished": year,
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": str(rating),
            "bestRating": "10",
            "ratingCount": str(rating_count),
        },
        "dateModified": datetime.now().strftime('%Y-%m-%d')
    }
    if genres_en:
        main_ld["genre"] = genres_en[:4]
    if youtube_key:
        main_ld["trailer"] = {
            "@type": "VideoObject",
            "name": f"{title_ar} — Official Trailer",
            "embedUrl": f"https://www.youtube.com/embed/{youtube_key}",
            "thumbnailUrl": poster_url,
            "uploadDate": f"{full_release_date}T00:00:00Z",
        }

    json_ld_html  = f'<script type="application/ld+json">{json.dumps(breadcrumb_ld, ensure_ascii=False)}</script>\n'
    json_ld_html += f'<script type="application/ld+json">{json.dumps(main_ld, ensure_ascii=False)}</script>'

    # ── Build page HTML ───────────────────────────────────────────────────────
    # from trends_fetcher import clean_strict (moved to top)
    meta_desc_raw = meta_data.get('meta_desc', '') if meta_data else ''
    meta_desc_raw = clean_strict(meta_desc_raw[:155]) if meta_desc_raw else f'مشاهدة وتحميل {title_ar} ({title_en}) اون لاين بجودة HD مترجم حصرياً على توميتو.'
    meta_desc = meta_desc_raw

    html = MASTER_TEMPLATE
    # Rule 5: Exclusive Meta Tags pattern
    seo_title = clean_strict((tri or {}).get('seo_title_ar') or '')
    if not seo_title:
        seo_title = f'مشاهدة {type_label} {title_ar} مترجم بجودة HD حصرياً على توميتو'
        if media_type != 'movie':
            seo_title = f'مشاهدة {title_ar} مترجم بجودة HD حصرياً على توميتو'
        seo_page_title = f'{seo_title} | {title_en}'
    else:
        seo_page_title = seo_title

    replacements = {
        '{{ROOT}}':             '../',
        '{{CATEGORIES_LINKS}}': get_category_links_html(root_path='../'),
        '{{TITLE_PAGE}}':       seo_page_title,
        '{{META_DESC}}':        meta_desc,
        '{{KEYWORDS}}':         keywords,
        '{{TITLE_OG}}':         f'{title_ar} / {title_en} — TOMITO',
        '{{OG_TYPE}}':          'video.movie' if media_type == 'movie' else 'video.tv_show',
        '{{POSTER_URL}}':       poster_url,
        '{{PAGE_URL}}':         page_url,
        '{{BUTTON_URL}}':       f"{BUTTON_DOMAIN}/{folder}/{slug}",
        '{{WATCH_URL}}':        watch_url,
        '{{TITLE_AR}}':         title_ar,
        '{{TITLE_EN}}':         title_en,
        '{{DESC_AR}}':          desc_ar,
        '{{DESC_EN}}':          desc_en,
        '{{TAGS_SECTION}}':     tags_html,
        '{{EXTRA_CONTENT}}':    extra_content,
        '{{JSON_LD}}':          json_ld_html,
        '{{FOLDER}}':           folder,
        '{{TYPE_AR}}':          type_label.split('|')[-1].strip(),
        '{{CATEGORIES_LINKS}}': get_category_links_html(root_path="../"),
        '{{ROOT}}':             '../',
    }
    for k, v in replacements.items():
        html = html.replace(k, str(v))


    path = os.path.join(BASE_PATH, folder, f"{slug}.html")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)

    # ── Live Google Indexing ──────────────────────────────────────────────────
    try:
        print(f"🚀 [INDEXING] Sending new page to Google: {page_url}")
        index_new_page(page_url)
    except Exception as e:
        log.error(f"Failed to index {page_url}: {e}")

    # Return entry for index
    g_ids = [g.get('id') for g in (en.get('genres', []) if en else [])]
    index_entry = {
        'title': f"{title_ar} / {title_en}",
        'title_ar': title_ar,
        'title_en': title_en,
        'slug': slug,
        'folder': folder,
        'poster': poster_url,
        'rating': rating,
        'year': year,
        'type': media_type,
        'tmdb_id': tmdb_id,
        'genre_ids': g_ids,
        'timestamp': int(time.time())
    }
    return f"{folder}/{slug}", index_entry

def fetch_actor_credits(actor_id):
    """Fetch top 100 most recent movies + top 100 most recent TV shows for an actor from TMDB."""
    data = get_tmdb_data(f"person/{actor_id}/combined_credits", {'language': 'en'})
    if not data:
        return [], []
    cast = data.get('cast', [])
    movies = sorted(
        [c for c in cast if c.get('media_type') == 'movie' and c.get('poster_path') and c.get('release_date')],
        key=lambda x: x.get('release_date', ''), reverse=True
    )[:100]
    tv_shows = sorted(
        [c for c in cast if c.get('media_type') == 'tv' and c.get('poster_path') and c.get('first_air_date')],
        key=lambda x: x.get('first_air_date', ''), reverse=True
    )[:100]
    return movies, tv_shows

def build_filmography_html(movies, tv_shows):
    """Build filmography HTML section with cards visually identical to the main site."""
    available_ids = get_available_ids()
    
    # Filter by what we have in index
    f_movies = [m for m in movies if m.get('id') and int(m.get('id')) in available_ids]
    f_tv = [t for t in tv_shows if t.get('id') and int(t.get('id')) in available_ids]

    if not f_movies and not f_tv:
        return ''

    def card(item, folder):
        tmdb_id = item.get('id', '')
        title = item.get('title') or item.get('name') or ''
        poster = f"{IMAGE_BASE_URL}{item['poster_path']}"
        slug_part = clean_slug(title)
        slug = f"{tmdb_id}-{slug_part}" if slug_part else str(tmdb_id)
        year = (item.get('release_date') or item.get('first_air_date') or '')[:4]
        rating = round(item.get('vote_average', 0), 1)
        badge = f"{rating}⭐" if rating else year
        
        # Using exact same card structure as the homepage `build_homepage.py`
        return f'''    <a class="card" href="https://tv.tomito.xyz/{folder}/{slug}">
      <img class="card-poster" src="{poster}" alt="{title} — مشاهدة وتحميل اون لاين" loading="lazy" onerror="this.src='../favicon.ico'">
      <div class="card-overlay"><div class="card-meta">{badge}</div></div>
      <div class="card-bottom"><div class="card-title">{title}</div></div>
    </a>'''

    html = ''
    if f_movies:
        html += '<section class="section"><h2 class="section-title">أفلامه — Movies</h2><div class="grid">'
        html += ''.join(card(m, 'movie') for m in f_movies)
        html += '</div></section>'
    if f_tv:
        html += '<section class="section"><h2 class="section-title">مسلسلاته — TV Shows</h2><div class="grid">'
        html += ''.join(card(t, 'tv') for t in f_tv)
        html += '</div></section>'
    return html

def create_actor_page(actor_id):
    ar = get_tmdb_data(f"person/{actor_id}", {'language': 'ar'})
    en = get_tmdb_data(f"person/{actor_id}", {'language': 'en'})
    if not en:
        return None
    name = en.get('name', 'Unknown')
    bio_ar = (ar.get('biography', '') if ar else '') or ''
    bio_en = en.get('biography', '') or ''
    img_url = (f"{IMAGE_BASE_URL}{en.get('profile_path')}" if en.get('profile_path') else "/favicon.ico")
    slug = f"{actor_id}-{clean_slug(name)}"

    # Fetch filmography (100 movies + 100 tv)
    movies, tv_shows = fetch_actor_credits(actor_id)
    filmography_html = build_filmography_html(movies, tv_shows)

    seo_desc = f"تعرف على {name} — سيرته الذاتية وأهم أعماله. شاهد أفلام ومسلسلات {name} اون لاين بجودة عالية HD على TOMITO."
    
    # Use trends for actors too if possible, or high quality fallbacks
    # from trends_fetcher import fetch_related_keywords (moved to top)
    trends = fetch_related_keywords(name, 'AR')
    if trends:
        keywords = trends
    else:
        keywords = f"مشاهدة افلام {name}, تحميل مسلسلات {name}, {name} مترجم, sيرة ذاتية {name}, actor {name}, filmography"

    # JSON-LD Generation (Person type does NOT support AggregateRating)
    breadcrumb_ld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "الرئيسية", "item": SITE_URL},
            {"@type": "ListItem", "position": 2, "name": "ممثلين", "item": f"{SITE_URL}/actor"},
            {"@type": "ListItem", "position": 3, "name": name, "item": f'{SITE_URL}/actor/{slug}'}
        ]
    }

    main_ld = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": name,
        "description": bio_ar,
        "image": img_url
    }

    json_ld_html = f'<script type="application/ld+json">{json.dumps(breadcrumb_ld, ensure_ascii=False)}</script>\n'
    json_ld_html += f'<script type="application/ld+json">{json.dumps(main_ld, ensure_ascii=False)}</script>'

    html = MASTER_TEMPLATE
    replacements = {
        '{{TITLE_PAGE}}': f'{name} — الممثل | TOMITO',
        '{{META_DESC}}': seo_desc,
        '{{KEYWORDS}}': keywords,
        '{{TITLE_OG}}': f'{name} — TOMITO',
        '{{OG_TYPE}}': 'profile',
        '{{POSTER_URL}}': img_url,
        '{{PAGE_URL}}': f'{SITE_URL}/actor/{slug}',
        '{{BUTTON_URL}}': f'{BUTTON_DOMAIN}/actor/{slug}',
        '{{WATCH_URL}}': '/',
        '{{TITLE_AR}}': name,
        '{{TITLE_EN}}': 'Performer | ممثل',
        '{{DESC_AR}}': bio_ar[:500],
        '{{DESC_EN}}': bio_en[:500],
        '{{TAGS_SECTION}}': '',
        '{{EXTRA_CONTENT}}': filmography_html,
        '{{JSON_LD}}': json_ld_html,
        '{{FOLDER}}': 'actor',
        '{{TYPE_AR}}': 'ممثلين',
        '{{CATEGORIES_LINKS}}': get_category_links_html(root_path="../"),
        '{{ROOT}}': '../',
    }
    for k, v in replacements.items():
        html = html.replace(k, str(v))

    path = os.path.join(BASE_PATH, 'actor', f"{slug}.html")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    return f"actor/{slug}"

# --- Fetch IDs from TMDB ---
def fetch_ids(media_type, years, target=5000, genre=None, start_page=1):
    ids = set()
    for year in years:
        page = start_page
        while len(ids) < target and page <= start_page + 500:
            params = {
                'page': page,
                'sort_by': 'popularity.desc',
                'vote_count.gte': 5,
            }
            if media_type == 'movie':
                params['primary_release_year'] = year
            else:
                params['first_air_date_year'] = year
            if genre:
                params['with_genres'] = genre
            
            data = get_tmdb_data(f"discover/{media_type}", params)
            if not data or not data.get('results'):
                break
            for r in data['results']:
                ids.add(r['id'])
            if page >= data.get('total_pages', 1):
                break
            page += 1
        if len(ids) >= target:
            break
    return list(ids)[:target]

def build_listing_pages():
    """Generates index.html and genre-specific listing pages."""
    index_path = os.path.join(BASE_PATH, 'data', 'content_index.json')
    if not os.path.exists(index_path): return
    
    with open(index_path, 'r', encoding='utf-8') as f:
        all_items = json.load(f)

    # Import missions from ai_engine (local import to avoid circular)
    try:
        from ai_engine import BOT_MISSIONS
    except ImportError:
        BOT_MISSIONS = [] # Fallback
    
    # Generate Category HTML Links for Nav
    cat_links = get_category_links_html()

    def render_list(title, items, folder=""):
        # Use simple mapping
        html = MASTER_TEMPLATE.replace('{{TITLE_PAGE}}', f"{title} — TOMITO")
        html = html.replace('{{META_DESC}}', f"استكشف {title} - مشاهدة أحدث الأفلام والمسلسلات أون لاين.")
        html = html.replace('{{KEYWORDS}}', f"{title}, افلام, مسلسلات, مترجم, tomite")
        html = html.replace('{{TITLE_OG}}', title)
        html = html.replace('{{POSTER_URL}}', "/logo.png")
        html = html.replace('{{PAGE_URL}}', SITE_URL + "/" + folder)
        html = html.replace('{{JSON_LD}}', "")
        
        # Override cat links if we are at root level (index.html) vs genre level
        root_path = "../" if "genre" in folder else "./"
        html = html.replace('{{ROOT}}', root_path)
        custom_cat_links = get_category_links_html(root_path=root_path)
        html = html.replace('{{CATEGORIES_LINKS}}', custom_cat_links)
        
        # Same for nav links
        if not "genre" in folder:
            pass # Removed local rewrite
            
        html = html.replace('{{FOLDER}}', folder)
        html = html.replace('{{TYPE_AR}}', "تصنيف")
        html = html.replace('{{TITLE_AR}}', title)
        html = html.replace('{{TITLE_EN}}', "")
        html = html.replace('{{DESC_EN}}', "")
        html = html.replace('{{DESC_AR}}', f"استمتع بمشاهدة {title} بجودة عالية HD.")
        html = html.replace('{{TAGS_SECTION}}', "")
        html = html.replace('{{BUTTON_URL}}', "#")
        html = html.replace('{{LOCAL_PAGES_JSON}}', json.dumps(list(LOCAL_SLUGS)))
        
        # Rule: Use company logo from TMDB if available, otherwise hide it or use site logo
        mission_logo = next((m.get('logo') for m in BOT_MISSIONS if m['label'] == title), None)
        if mission_logo:
             logo_html = f'<img src="{mission_logo}" alt="{title}" class="series-poster" style="width: auto; max-height: 120px; margin: 0 auto; display: block; object-fit: contain; filter: brightness(1.2); padding: 10px;">'
        else:
             # For genre pages, just hide the big poster tag
             logo_html = ''
             
        # Find the placeholder line and replace it with our specialized logo HTML
        poster_placeholder = '<img src="{{POSTER_URL}}" alt="{{TITLE_AR}} — مشاهدة وتحميل" loading="eager" class="series-poster">'
        html = html.replace(poster_placeholder, logo_html)
        
        # Sort items: local first, then external
        items.sort(key=lambda x: f"{x.get('folder')}/{x.get('slug')}" in LOCAL_SLUGS, reverse=True)

        grid = '<div class="grid">'
        for i, item in enumerate(items[:200]):
            s = item.get('slug')
            fld = item.get('folder', 'movie')
            t_ar = item.get('title_ar', 'Unknown')
            poster_url = item.get('poster', '').replace('/original/', '/w300/')
            url = get_item_url(fld, s, root="../")
            hidden_class = ' hidden-card' if i >= 20 else ''
            grid += f'''
            <a class="card{hidden_class}" href="{url}" style="text-decoration:none;">
              <img class="card-poster" src="{poster_url}" alt="{t_ar}" loading="lazy" onerror="this.src='/favicon.ico'">
              <div class="card-overlay"><div class="card-meta">حصري</div></div>
              <div class="card-bottom"><div class="card-title">{t_ar}</div></div>
            </a>'''
        grid += "</div>"
        
        # Determine Redirect URL to tv.tomito.xyz
        redirect_url = "https://tv.tomito.xyz/"
        mission = next((m for m in BOT_MISSIONS if m['label'] == title), None)
        if mission:
            m_type = mission.get('type', 'genre')
            m_id = mission.get('id')
            redirect_url = f"https://tv.tomito.xyz/category/{m_type}/{m_id}"
        elif "فيلم" in title or "الأفلام" in title:
            redirect_url = "https://tv.tomito.xyz/movie"
        elif "مسلسل" in title or "المسلسلات" in title:
            redirect_url = "https://tv.tomito.xyz/tv"

        if len(items) > 20:
             # First button shows more local cards
             grid += '<div class="load-more-container"><button class="load-more-btn" onclick="showMoreCards(this)"><span>عرض المزيد محلياً</span> <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg></button></div>'
        
        # Final redirect button to external category
        grid += f'<div class="load-more-container" style="margin-top:10px;"><a href="{redirect_url}" class="load-more-btn" style="background:#FF6D1F; color:#000;"><span>مشاهدة الكل على tv.tomito.xyz</span> <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6-6-6z"/></svg></a></div>'
        
        return html.replace('{{EXTRA_CONTENT}}', grid)

    # 1. Main Index (Removed: build_homepage.py handles this)
    # with open(os.path.join(BASE_PATH, 'index.html'), 'w', encoding='utf-8') as f:
    #     f.write(render_list("الرئيسية", all_items[::-1]))

    # 2. Genre Pages
    genre_dir = os.path.join(BASE_PATH, 'genre')
    os.makedirs(genre_dir, exist_ok=True)
    for mission in BOT_MISSIONS:
        slug = clean_slug(mission['name'])
        m_id = mission.get('id')
        m_years = mission.get('years')
        
        filtered = []
        for it in all_items:
            # Filter by Genre ID
            it_genres = it.get('genre_ids', [])
            if m_id and m_id in it_genres:
                filtered.append(it)
            # Filter by Year
            elif m_years:
                it_year = it.get('year')
                if it_year and any(str(y) in str(it_year) for y in m_years):
                    filtered.append(it)
            # Trending/latest (fallback to all recent)
            elif not m_id and not m_years:
                filtered.append(it)

        if not filtered: filtered = all_items[:200] # Fallback if empty
            
        with open(os.path.join(genre_dir, f"{slug}.html"), 'w', encoding='utf-8') as f:
            f.write(render_list(mission['label'], filtered[::-1], f"genre/{slug}"))

    print("✅ Listing pages generated.")

# --- Sitemap Generator ---
def generate_sitemap(base_url, root_dir, all_pages):
    """Splits sitemaps into movies, tv, and genres."""
    today = datetime.now().strftime('%Y-%m-%d')
    base_url = "https://tomito.xyz"
    
    # Pre-populate sitemap_genre.xml with actual genre listing pages
    try:
        from ai_engine import BOT_MISSIONS
        genre_urls = [f"genre/{clean_slug(m['name'])}" for m in BOT_MISSIONS]
    except ImportError:
        genre_urls = []

    sitemaps = {
        'sitemap_movie.xml': [p for p in all_pages if p.startswith('movie')],
        'sitemap_tv.xml': [p for p in all_pages if p.startswith('tv')],
        'sitemap_genre.xml': genre_urls + [p for p in all_pages if p.startswith('genre')],
        'sitemap_actor.xml': [p for p in all_pages if p.startswith('actor')]
    }

    def write_xml(filename, urls, priority=0.8):
        path = os.path.join(root_dir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            if filename == 'sitemap_movie.xml': # Add homepage to movie sitemap
                f.write(f'  <url><loc>{base_url}/</loc><lastmod>{today}</lastmod><priority>1.0</priority></url>\n')
            for u in urls:
                f.write(f'  <url><loc>{base_url}/{u}</loc><lastmod>{today}</lastmod><priority>{priority}</priority></url>\n')
            f.write('</urlset>')
        log.info(f"✅ Sitemap generated: {filename}")

    for fname, urls in sitemaps.items():
        if urls or fname == 'sitemap_movie.xml':
            write_xml(fname, urls)

    # Root Sitemap Index
    with open(os.path.join(root_dir, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for fname in sitemaps.keys():
            if os.path.exists(os.path.join(root_dir, fname)):
                f.write(f'  <sitemap><loc>{base_url}/{fname}</loc><lastmod>{today}</lastmod></sitemap>\n')
        f.write('</sitemapindex>')
    return 'sitemap.xml'

# --- Main API Support ---
def main_process(limit=250):
    for d in DIRS: os.makedirs(os.path.join(BASE_PATH, d), exist_ok=True)
    index_path = os.path.join(BASE_PATH, 'data', 'content_index.json')
    all_index = []
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f: all_index = json.load(f)
    existing_ids = {str(i.get('tmdb_id')) for i in all_index}
    
    # Process small batch from Trending for variety if run standalone
    print("Fetching default variety...")
    # This is just a fallback main if not called from daily_content.py

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=100)
    args = parser.parse_args()
    # build_listing_pages() is already in standalone daily_content tasks
    build_listing_pages()
