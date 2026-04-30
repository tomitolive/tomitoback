#!/usr/bin/env python3
"""Build index.html with hybrid link logic and localized prioritization."""

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

LOCAL_DATA = load_index()
LOCAL_SLUGS = {f"{i.get('folder')}/{i.get('slug')}" for i in LOCAL_DATA}

def get_url(folder, slug, root="./"):
    key = f"{folder}/{slug}"
    if key in LOCAL_SLUGS:
        return f"{root}{folder}/{slug}"
    return f"https://tv.tomito.xyz/{folder}/{slug}"

def card_html(item, root="./"):
    poster = item.get('poster', '/favicon.ico').replace('/original/', '/w300/')
    title = item.get('title') or item.get('title_ar') or ''
    folder = item.get('folder', 'movie')
    slug = item.get('slug', '')
    href = get_url(folder, slug, root)
    rating = item.get('rating', '')
    badge = f"{rating}⭐" if rating else "حصري"
    
    return f'''    <a class="card" href="{href}" style="text-decoration:none;">
      <img class="card-poster" src="{poster}" alt="{title}" loading="lazy" onerror="this.src='/favicon.ico'">
      <div class="card-overlay"><div class="card-meta">{badge}</div></div>
      <div class="card-bottom"><div class="card-title">{title}</div></div>
    </a>'''

def build_mini_carousel(section_id, title_ar, items, view_all_url, count=20):
    if not items: return ''
    cards = ''
    for item in items[:count]:
        folder = item.get('folder', 'movie')
        slug   = item.get('slug', '')
        href   = get_url(folder, slug)
        poster = item.get('poster', '/favicon.ico').replace('/original/', '/w300/')
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
      <div class="simple-header" style="display:flex;justify-content:space-between;align-items:center;border-bottom: 1px solid #222; padding-bottom: 8px; margin-bottom:15px;">
        <h2 style="color:#fff;font-size:1.3rem;margin:0;font-weight:bold;">{title_ar}</h2>
        <a href="{view_all_url}" style="color:#FF6D1F;font-size:0.85rem;text-decoration:none;">عرض الكل ←</a>
      </div>
      <div class="simple-viewport">{cards}</div>
    </section>'''

def build_carousel(trends):
    if not trends: return ''
    cards = ''
    for item in trends[:30]:
        folder = item.get('folder', 'movie')
        slug = item.get('slug', '')
        href = get_url(folder, slug)
        poster = item.get('poster', '/favicon.ico').replace('/original/', '/w300/')
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
    index = LOCAL_DATA
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
    
    final_local = [i for i in trends if str(i.get('tmdb_id')) in local_ids]
    final_external = [i for i in trends if str(i.get('tmdb_id')) not in local_ids]
    final = final_local + final_external
    
    if len(final) < 30:
        exist = {str(i.get('tmdb_id')) for i in final}
        for item in index:
            if str(item.get('tmdb_id')) not in exist: final.append(item)
            if len(final) >= 30: break
    return final[:30]

def build():
    index = LOCAL_DATA
    index.sort(key=lambda x: (x.get('timestamp', 0), str(x.get('year', ''))), reverse=True)
    movies = [i for i in index if i.get('folder') == 'movie'][:200]
    series = [i for i in index if i.get('folder') == 'tv'][:200]
    anime = [i for i in index if any(g in str(i.get('genres', [])) for g in ['أنمي', 'رسوم متحركة', 'Anime', 'Animation'])][:30]

    def section(sid, title, items):
        if not items: return ''
        grid_html = '<div class="grid">'
        for i, it in enumerate(items):
            hc = ' hidden-card' if i >= 24 else ''
            grid_html += card_html(it).replace('class="card"', f'class="card{hc}"')
        grid_html += '</div>'
        if len(items) > 24:
            grid_html += '<div class="load-more-container"><button class="load-more-btn" onclick="showMoreCards(this)"><span>عرض المزيد</span> <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg></button></div>'
        return f'<section class="section" id="{sid}"><h2 class="section-title">{title}</h2>{grid_html}</section>'

    movies_section = section('movies', 'أحدث الأفلام', movies)
    series_section = section('series', 'أحدث المسلسلات', series)
    anime_section = section('anime', 'أنمي مترجم', anime)

    new_movies_carousel = build_mini_carousel('new-movies', '🎬 أحدث الأفلام', movies, '/genre/movie', count=20)
    new_tv_carousel     = build_mini_carousel('new-tv', '📺 أحدث المسلسلات', series, '/genre/tv-show', count=20)

    trends = build_interleaved_trending()
    carousel_section = build_carousel(trends)

    from mega_bot import get_category_links_html
    cat_links = get_category_links_html(root_path="./")

    template = '''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TOMITO — مشاهدة وتحميل أفلام ومسلسلات وأنمي 2026</title>
  <link rel="stylesheet" href="./style.css">
  <link rel="icon" href="./favicon.ico">
  <script src="./data/search_index.js"></script>
  <script>const LOCAL_PAGES = {{LOCAL_PAGES_JSON}};</script>
</head>
<body>
    <header class="tomito-header">
  <div class="top-bar">
    <div class="header-container">
      <ul class="top-nav">
        <li><a href="./">الرئيسية</a></li>
        <li><a href="./#movies">أفلام</a></li>
        <li><a href="./#series">مسلسلات</a></li>
        <li><a href="./genre/animation">أنمي</a></li>
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
        <a href="./" class="logo-link">
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

    {{CAROUSEL_SECTION}}
    {{NEW_MOVIES_CAROUSEL}}
    {{NEW_TV_CAROUSEL}}
    {{MOVIES_SECTION}}
    {{SERIES_SECTION}}
    {{ANIME_SECTION}}

    <footer class="footer">
      <p>© 2026 <span class="logo-text" style="font-size:1.1rem; filter:none;">TOMITO</span> — جميع الحقوق محفوظة</p>
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
          const href = getUrl(folder, item.slug, './');
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

    document.addEventListener('click', (e) => {
      const menu = document.getElementById('menu-overlay');
      if (menu && !menu.contains(e.target) && !e.target.closest('.categories-link') && !e.target.closest('.mobile-menu-btn')) {
        menu.classList.remove('active');
      }
      if (!e.target.closest('.header-search-wrapper')) {
        document.getElementById('search-suggestions').style.display = 'none';
      }
    });

    function showMoreCards(btn) {
      const section = btn.closest('.section');
      const grid = section.querySelector('.grid');
      const hidden = grid.querySelectorAll('.card.hidden-card');
      hidden.forEach((c, i) => {
        if (i < 24) c.classList.remove('hidden-card');
      });
      if (grid.querySelectorAll('.card.hidden-card').length === 0) {
        btn.parentElement.style.display = 'none';
      }
    }
    </script>
</body>
</html>'''

    html = template.replace('{{CATEGORIES_LINKS}}', cat_links)\
                   .replace('{{CAROUSEL_SECTION}}', carousel_section)\
                   .replace('{{NEW_MOVIES_CAROUSEL}}', new_movies_carousel)\
                   .replace('{{NEW_TV_CAROUSEL}}', new_tv_carousel)\
                   .replace('{{MOVIES_SECTION}}', movies_section)\
                   .replace('{{SERIES_SECTION}}', series_section)\
                   .replace('{{ANIME_SECTION}}', anime_section)\
                   .replace('{{LOCAL_PAGES_JSON}}', json.dumps(list(LOCAL_SLUGS)))

    with open(os.path.join(BASE_PATH, 'index.html'), 'w', encoding='utf-8') as f: f.write(html)
    print(f"Built index.html with hybrid links.")

def build_all_pages():
    """Alias for daily_content compatibility."""
    build()

if __name__ == '__main__':
    build()
