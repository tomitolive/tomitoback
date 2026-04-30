#!/usr/bin/env python3
"""Build index.html with interleaved trending carousel and a minimalist search box."""

import os
import json

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
SITE_URL = "https://tomito.xyz"

def load_index():
    path = os.path.join(BASE_PATH, 'data', 'content_index.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def card_html(item):
    poster = item.get('poster', '/favicon.ico')
    title = item.get('title') or item.get('title_ar') or ''
    folder = item.get('folder', 'movie')
    slug = item.get('slug', '')
    href = f"/{folder}/{slug}"
    rating = item.get('rating', '')
    badge = f"{rating}⭐" if rating else "حصري"
    
    return f'''    <a class="card" href="{href}" style="text-decoration:none;">
      <img class="card-poster" src="{poster}" alt="{title} — مشاهدة وتحميل اون لاين" loading="lazy" onerror="this.src='/favicon.ico'">
      <div class="card-overlay"><div class="card-meta">{badge}</div></div>
      <div class="card-bottom"><div class="card-title">{title}</div></div>
    </a>'''

def build_carousel(trends):
    if not trends: return ''
    cards = ''
    for item in trends[:30]:
        folder = item.get('folder', 'movie')
        slug = item.get('slug', '')
        href = f"/{folder}/{slug}"
        poster = item.get('poster', '/favicon.ico')
        title = item.get('title', '')
        rating = item.get('rating', '')
        badge = f"{rating}⭐" if rating else "NEW"
        cards += f'''
        <div class="simple-carousel-item">
            <a href="{href}">
                <div class="simple-poster-container">
                    <img src="{poster}" alt="{title}" loading="lazy" onerror="this.src='/favicon.ico'">
                    <div class="simple-rating">{badge}</div>
                </div>
                <div class="simple-title">{title}</div>
            </a>
        </div>'''
        
    css = '''
    <style>
    .simple-carousel-section { margin: 20px auto; padding: 0 5%; max-width: 1400px; }
    .simple-header { margin-bottom: 15px; border-bottom: 1px solid #222; padding-bottom: 8px; }
    .simple-header h2 { color: #fff; font-size: 1.3rem; margin: 0; font-weight: bold; }
    .simple-viewport { display: flex; gap: 15px; overflow-x: auto; padding-bottom: 15px; scrollbar-width: none; }
    .simple-viewport::-webkit-scrollbar { display: none; }
    .simple-carousel-item { flex: 0 0 150px; min-width: 150px; }
    .simple-carousel-item a { text-decoration: none; }
    .simple-poster-container { position: relative; border-radius: 10px; overflow: hidden; aspect-ratio: 2/3; margin-bottom: 5px; }
    .simple-poster-container img { width: 100%; height: 100%; object-fit: cover; }
    .simple-rating { position: absolute; top: 5px; right: 5px; background: rgba(0,0,0,0.8); color: #FF6D1F; font-size: 0.6rem; padding: 2px 5px; border-radius: 4px; }
    .simple-title { color: #ccc; font-size: 0.8rem; text-align: center; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; min-height: 2.2em; }
    @media (max-width: 768px) { .simple-carousel-item { flex: 0 0 120px; min-width: 120px; } }
    </style> '''
    
    return f'''{css}
    <section class="simple-carousel-section">
      <div class="simple-header"><h2>🔥 التريند الآن</h2></div>
      <div class="simple-viewport">{cards}</div>
    </section>'''

def build_interleaved_trending():
    index = load_index()
    local_ids = {str(item.get('tmdb_id')) for item in index}
    movies, tv = [], []
    for fname, lst in [('trend_movies.json', movies), ('trend_tv.json', tv)]:
        path = os.path.join(BASE_PATH, 'data', fname)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f: lst.extend(json.load(f))
    trends = []
    for m, t in zip(movies, tv): trends.extend([m, t])
    if len(movies) > len(tv): trends.extend(movies[len(tv):])
    elif len(tv) > len(movies): trends.extend(tv[len(movies):])
    final = [i for i in trends if str(i.get('tmdb_id')) in local_ids]
    if len(final) < 10:
        exist = {str(i.get('tmdb_id')) for i in final}
        for item in index[:30]:
            if str(item.get('tmdb_id')) not in exist: final.append(item)
            if len(final) >= 30: break
    return final

def build_all_pages():
    """Build dedicated movie/index.html and tv/index.html listing all content."""
    index = load_index()
    # Sort newest first (timestamp desc, fallback to year)
    index.sort(key=lambda x: (x.get('timestamp', 0), str(x.get('year', ''))), reverse=True)

    movies = [i for i in index if i.get('folder') == 'movie']
    tv     = [i for i in index if i.get('folder') == 'tv']

    def listing_page(title_ar, items, folder, page_url):
        cards = ''.join(card_html(i) for i in items)
        return f'''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title_ar} — TOMITO</title>
  <meta name="description" content="{title_ar} — مشاهدة وتحميل اون لاين بجودة HD على توميتو">
  <link rel="stylesheet" href="../style.css">
  <link rel="icon" href="../favicon.ico">
</head>
<body>
  <header class="header">
    <a href="/" class="logo-link"><span class="logo-text">TOMITO</span></a>
    <ul class="nav">
      <li><a href="/movie" class="nav-btn">أفلام</a></li>
      <li><a href="/tv" class="nav-btn">مسلسلات</a></li>
    </ul>
    <a class="header-btn" href="https://tv.tomito.xyz">الموقع الرسمي</a>
  </header>
  <section class="section" id="{folder}">
    <h1 class="section-title" style="font-size:1.6rem;">{title_ar} <span style="color:#888;font-size:0.9rem;">({len(items)})</span></h1>
    <div class="grid">{cards}</div>
  </section>
  <footer class="footer"><p>© 2026 <span class="logo-text" style="font-size:1.1rem;">TOMITO</span></p></footer>
</body>
</html>'''

    import os
    BASE_PATH_LOCAL = os.path.dirname(os.path.abspath(__file__))
    for folder_name, items, label in [('movie', movies, 'جميع الأفلام'), ('tv', tv, 'جميع المسلسلات')]:
        folder_dir = os.path.join(BASE_PATH_LOCAL, folder_name)
        os.makedirs(folder_dir, exist_ok=True)
        html = listing_page(label, items, folder_name, f"{SITE_URL}/{folder_name}")
        with open(os.path.join(folder_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html)
    print(f"Built movie/index.html ({len(movies)} movies) and tv/index.html ({len(tv)} TV shows).")


def build_mini_carousel(section_id, title_ar, items, view_all_url, count=20):
    """Build a compact horizontal carousel with a 'view all' link."""
    if not items:
        return ''
    cards = ''
    for item in items[:count]:
        folder = item.get('folder', 'movie')
        slug   = item.get('slug', '')
        href   = f"/{folder}/{slug}"
        poster = item.get('poster', '/favicon.ico')
        title  = item.get('title') or item.get('title_ar') or ''
        rating = item.get('rating', '')
        badge  = f"{rating}⭐" if rating else 'NEW'
        cards += f'''
        <div class="simple-carousel-item">
            <a href="{href}">
                <div class="simple-poster-container">
                    <img src="{poster}" alt="{title}" loading="lazy" onerror="this.src='/favicon.ico'">
                    <div class="simple-rating">{badge}</div>
                </div>
                <div class="simple-title">{title}</div>
            </a>
        </div>'''
    return f'''
    <section class="simple-carousel-section" id="{section_id}">
      <div class="simple-header" style="display:flex;justify-content:space-between;align-items:center;">
        <h2 style="color:#fff;font-size:1.3rem;margin:0;font-weight:bold;">{title_ar}</h2>
        <a href="{view_all_url}" style="color:#FF6D1F;font-size:0.85rem;text-decoration:none;">عرض الكل ←</a>
      </div>
      <div class="simple-viewport">{cards}</div>
    </section>'''


def build():
    index = load_index()
    # Sort newest first (timestamp desc, fallback to year)
    index.sort(key=lambda x: (x.get('timestamp', 0), str(x.get('year', ''))), reverse=True)
    movies = [i for i in index if i.get('folder') == 'movie'][:200]
    series = [i for i in index if i.get('folder') == 'tv'][:200]
    anime = [i for i in index if any(g in str(i.get('genres', [])) for g in ['أنمي', 'رسوم متحركة', 'Anime', 'Animation'])][:30]

    def section(sid, title, items):
        if not items: return ''
        cards = '\n'.join(card_html(i) for i in items)
        return f'<section class="section" id="{sid}"><h2 class="section-title">{title}</h2><div class="grid">{cards}</div></section>'

    movies_section = section('movies', 'أحدث الأفلام', movies)
    series_section = section('series', 'أحدث المسلسلات', series)
    anime_section = section('anime', 'أنمي مترجم', anime)

    # New carousels — newest movies & newest TV with "view all" links
    new_movies_carousel = build_mini_carousel('new-movies', '🎬 أحدث الأفلام', movies, '/movie', count=20)
    new_tv_carousel     = build_mini_carousel('new-tv', '📺 أحدث المسلسلات', series, '/tv', count=20)

    trends = build_interleaved_trending()
    carousel_section = build_carousel(trends)

    from mega_bot import get_category_links_html
    cat_links = get_category_links_html(root_path="./")

    template = '''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-PRCQVS90BX"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-PRCQVS90BX');
  </script>
  <title>TOMITO — مشاهدة وتحميل أفلام ومسلسلات وأنمي 2026</title>
  <link rel="stylesheet" href="./style.css">
  <link rel="icon" href="./favicon.ico">
  <script>const FULL_INDEX = {FULL_INDEX_JSON};</script>
  <style>
    /* Header Responsiveness Fix */
    @media (max-width: 768px) {
      .header { padding: 10px 3%; }
      .nav { gap: 10px; }
      .nav a { font-size: 12px; }
      .logo-text { font-size: 1.4rem; }
      .header-btn { padding: 8px 15px; font-size: 12px; }
    }
    @media (max-width: 480px) {
      .logo-text { font-size: 1.2rem; }
      .nav-search-btn span { font-size: 11px; }
      .nav li.mobile-hide { display: none; }
    }
    .mini-search-box { 
      padding: 30px 5% 15px; 
      display: flex; 
      justify-content: center; 
      background: linear-gradient(180deg, rgba(222, 103, 24, 0.08) 0%, transparent 100%); 
      position: relative;
    }
    .search-wrapper { position: relative; width: 100%; max-width: 380px; }
    .mini-search-box input { 
      width: 100%; 
      padding: 12px 15px 12px 45px; 
      border-radius: 4px; 
      border: 1px solid rgba(255,255,255,0.1); 
      background: #0a0a0a; 
      color: #fff; 
      font-size: 0.95rem;
      outline: none; 
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      box-shadow: 0 4px 20px rgba(0,0,0,0.5);
      border-left: 3px solid #FF6D1F;
    }
    .mini-search-box input:focus { 
      border-color: #FF6D1F; 
      background: #111;
      box-shadow: 0 10px 40px rgba(222, 103, 24, 0.15); 
    }
    .search-icon-inside {
      position: absolute;
      left: 15px;
      top: 50%;
      transform: translateY(-50%);
      color: #FF6D1F;
      font-size: 1.1rem;
      pointer-events: none;
      opacity: 0.8;
    }
    
    #search-suggestions {
      position: absolute;
      top: 100%;
      left: 0;
      right: 0;
      background: #0d0d0d;
      border: 1px solid #222;
      border-top: none;
      z-index: 1000;
      max-height: 400px;
      overflow-y: auto;
      display: none;
      box-shadow: 0 20px 50px rgba(0,0,0,0.9);
      border-radius: 0 0 8px 8px;
    }
    .suggestion-item {
      padding: 10px 15px;
      color: #eee;
      cursor: pointer;
      border-bottom: 1px solid #1a1a1a;
      display: flex;
      align-items: center;
      gap: 12px;
      text-decoration: none;
      transition: background 0.2s;
    }
    .suggestion-item:hover { background: #1a1a1a; color: #FF6D1F; }
    .suggestion-item img { width: 30px; height: 45px; object-fit: cover; border-radius: 2px; }
    .suggestion-item .type { font-size: 0.7rem; background: #222; padding: 2px 5px; border-radius: 3px; color: #888; }
    .mini-search-box input::placeholder { color: rgba(255,255,255,0.4); }

    /* Unified Search/Menu Dropdown */
    .menu-overlay {
      position: absolute;
      top: 60px;
      left: 5%;
      right: 5%;
      background: #0d0d0d;
      border: 1px solid #222;
      border-radius: 12px;
      box-shadow: 0 20px 50px rgba(0,0,0,0.9);
      display: none;
      z-index: 2000;
      padding: 20px;
      max-width: 500px;
      margin: 0 auto;
    }
    .menu-overlay.active { display: block; animation: fadeInDown 0.3s ease; }
    @keyframes fadeInDown {
      from { opacity: 0; transform: translateY(-10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .menu-search-wrapper { position: relative; margin-bottom: 20px; }
    .menu-search-wrapper input {
      width: 100%;
      padding: 12px 15px;
      background: #1a1a1a;
      border: 1px solid #333;
      border-radius: 8px;
      color: #fff;
      outline: none;
      border-left: 3px solid #FF6D1F;
    }
    .menu-categories {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 10px;
      border-top: 1px solid #222;
      padding-top: 15px;
    }
    .menu-categories a {
      color: #ccc;
      text-decoration: none;
      font-size: 0.9rem;
      padding: 8px 12px;
      background: #111;
      border-radius: 6px;
      transition: all 0.2s;
      text-align: center;
    }
    .menu-categories a:hover { background: #FF6D1F; color: #000; }
    
    /* Search Suggestions inside Menu */
    #search-suggestions {
      position: absolute;
      top: 100%; left: 0; right: 0;
      background: #111;
      border: 1px solid #222;
      z-index: 2001;
      max-height: 300px;
      overflow-y: auto;
      border-radius: 0 0 8px 8px;
    }
    
    .nav-search-btn {
      background: #1a1a1a;
      color: #FF6D1F;
      border: 1px solid #333;
      padding: 6px 12px;
      border-radius: 6px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: bold;
    }
    .nav-search-btn:hover { background: #222; border-color: #FF6D1F; }

    .nav-btn {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        padding: 5px 12px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 800;
        color: #ccc;
    }
    .nav-btn:hover { background: #FF6D1F; color: #000; border-color: #FF6D1F; }
  </style>
</head>
<body>
    <header class="header">
      <a href="/" class="logo-link">
        <span class="logo-text">TOMITO</span>
      </a>
      <ul class="nav">
        <li class="mobile-hide"><a href="/#movies" class="nav-btn">أفلام</a></li>
        <li class="mobile-hide"><a href="/#series" class="nav-btn">مسلسلات</a></li>
        <li>
          <button class="nav-search-btn" onclick="toggleMenu()" aria-label="البحث والتصنيفات">
             <span>البحث والتصنيفات</span>
          </button>
        </li>
      </ul>
      <a class="header-btn" href="https://tv.tomito.xyz">الموقع الرسمي</a>
    </header>

    <div class="menu-overlay" id="menu-overlay">
      <div class="menu-search-wrapper">
        <input type="text" id="site-search" placeholder="ابحث عن فيلم أو مسلسل..." onkeyup="siteSearch()" autocomplete="off">
        <div id="search-suggestions"></div>
      </div>
      <div class="menu-categories">
        {CAT_LINKS}
      </div>
    </div>

    {CAROUSEL}
    {NEW_MOVIES_CAROUSEL}
    {NEW_TV_CAROUSEL}
    {MOVIES_SECTION}
    {SERIES_SECTION}
    {ANIME_SECTION}

    <footer class="footer">
      <p>© 2026 <span class="logo-text" style="font-size:1.1rem; filter:none;">TOMITO</span> — جميع الحقوق محفوظة</p>
    </footer>

    <script>
    function siteSearch() {
      const q = document.getElementById('site-search').value.toLowerCase();
      const suggCont = document.getElementById('search-suggestions');
      const cards = Array.from(document.querySelectorAll('.card'));
      
      if (q.length < 1) {
        suggCont.style.display = 'none';
        cards.forEach(c => c.style.display = '');
        document.querySelectorAll('.section').forEach(s => s.style.display = '');
        return;
      }

      // 1. Local Filtering (on-page items)
      cards.forEach(card => {
        const title = card.querySelector('.card-title').innerText.toLowerCase();
        card.style.display = title.includes(q) ? '' : 'none';
      });

      // 2. Global Results (full index)
      const matches = FULL_INDEX.filter(item => {
          const t = item.title.toLowerCase();
          const ta = (item.title_ar || "").toLowerCase();
          const te = (item.title_en || "").toLowerCase();
          return t.includes(q) || ta.includes(q) || te.includes(q);
      });

      // Sort: startsWith comes first
      matches.sort((a, b) => {
          const aTitle = a.title.toLowerCase();
          const bTitle = b.title.toLowerCase();
          const aStarts = aTitle.startsWith(q);
          const bStarts = bTitle.startsWith(q);
          if (aStarts && !bStarts) return -1;
          if (!aStarts && bStarts) return 1;
          return 0;
      });

      const topMatches = matches.slice(0, 15);
      if (topMatches.length > 0) {
        suggCont.style.display = 'block';
        suggCont.innerHTML = '';
        topMatches.forEach(item => {
          const title = item.title;
          const href = `/${item.folder}/${item.slug}`;
          const img = item.poster;
          const type = item.folder === 'movie' ? 'فيلم' : 'مسلسل';
          
          const div = document.createElement('a');
          div.className = 'suggestion-item';
          div.href = href;
          div.innerHTML = `<img src="${img}"> <div><div>${title}</div><span class="type">${type}</span></div>`;
          suggCont.appendChild(div);
        });
      } else {
        suggCont.style.display = 'none';
      }

      document.querySelectorAll('.section').forEach(sec => {
          const visible = Array.from(sec.querySelectorAll('.card')).filter(c => c.style.display !== 'none').length;
          sec.style.display = visible > 0 ? '' : 'none';
      });
    }

    function toggleMenu() {
      const menu = document.getElementById('menu-overlay');
      menu.classList.toggle('active');
      if (menu.classList.contains('active')) {
        document.getElementById('site-search').focus();
      }
    }

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
      const menu = document.getElementById('menu-overlay');
      const btn = document.querySelector('.nav-search-btn');
      if (!menu.contains(e.target) && !btn.contains(e.target)) {
        menu.classList.remove('active');
      }
    });

    // Close suggestions when clicking outside
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.menu-search-wrapper')) {
        document.getElementById('search-suggestions').style.display = 'none';
      }
    });
    </script>
</body>
</html>'''

    html = template.replace('{CAT_LINKS}', cat_links)\
                   .replace('{CAROUSEL}', carousel_section)\
                   .replace('{NEW_MOVIES_CAROUSEL}', new_movies_carousel)\
                   .replace('{NEW_TV_CAROUSEL}', new_tv_carousel)\
                   .replace('{MOVIES_SECTION}', movies_section)\
                   .replace('{SERIES_SECTION}', series_section)\
                   .replace('{ANIME_SECTION}', anime_section)\
                   .replace('{FULL_INDEX_JSON}', json.dumps(index, ensure_ascii=False))

    with open(os.path.join(BASE_PATH, 'index.html'), 'w', encoding='utf-8') as f: f.write(html)
    print(f"Built index.html with carousel and global search.")

if __name__ == '__main__':
    build()
    build_all_pages()
