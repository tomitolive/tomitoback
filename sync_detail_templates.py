#!/usr/bin/env python3
"""Syncs all detail pages with hybrid link logic and premium header."""

import os
import json
import re

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

def load_index():
    path = os.path.join(BASE_PATH, 'data', 'content_index.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

LOCAL_DATA = load_index()
LOCAL_SLUGS = {f"{i.get('folder')}/{i.get('slug')}" for i in LOCAL_DATA}
LOCAL_PAGES_JSON = json.dumps(list(LOCAL_SLUGS))

def get_category_links_html(root_path="./"):
    try:
        from mega_bot import get_category_links_html as gcl
        return gcl(root_path=root_path)
    except:
        return ""

HEADER_HTML_TEMPLATE = r'''
<header class="tomito-header">
  <div class="top-bar">
    <div class="header-container">
      <ul class="top-nav">
        <li><a href="{root}">الرئيسية</a></li>
        <li><a href="{root}#movies">أفلام</a></li>
        <li><a href="{root}#series">مسلسلات</a></li>
        <li><a href="{root}genre/animation">أنمي</a></li>
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
        <a href="{root}" class="logo-link">
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
    {cat_links}
  </div>
</div>
'''

JS_FUNCTIONS = r'''
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
    if (typeof FULL_INDEX === 'undefined' || FULL_INDEX.length === 0) return;

    const matches = FULL_INDEX.filter(item => {
      const t = (item.title || "").toLowerCase();
      const ta = (item.title_ar || "").toLowerCase();
      return t.includes(q) || ta.includes(q);
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
        const root = document.querySelector('link[href*="style.css"]').getAttribute('href').replace('style.css','');
        const href = getUrl(folder, item.slug, root);
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
    const section = btn.closest('.section') || btn.closest('.extra-content');
    const grid = section.querySelector('.grid');
    const hidden = grid.querySelectorAll('.card.hidden-card');
    hidden.forEach((c, i) => {
      if (i < 24) c.classList.remove('hidden-card');
    });
    if (grid.querySelectorAll('.card.hidden-card').length === 0) {
      btn.parentElement.style.display = 'none';
    }
  }
'''

def patch_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Determing root path
    root = "../" if "/movie/" in filepath or "/tv/" in filepath or "/genre/" in filepath else "./"
    
    # 1. Update Head: script references
    if '<script src="' + root + 'data/search_index.js"></script>' not in content:
        content = content.replace('</head>', f'<script src="{root}data/search_index.js"></script>\n<script>const LOCAL_PAGES = {LOCAL_PAGES_JSON};</script>\n</head>')
    elif 'LOCAL_PAGES =' not in content:
        content = content.replace('search_index.js"></script>', f'search_index.js"></script>\n<script>const LOCAL_PAGES = {LOCAL_PAGES_JSON};</script>')
    else:
         content = re.sub(r'const LOCAL_PAGES = \[.*?\];', f'const LOCAL_PAGES = {LOCAL_PAGES_JSON};', content)

    # 2. Update Header
    header_pattern = re.compile(r'<header.*?</header>\s*(<div class="menu-overlay" id="menu-overlay">.*?</div>)?', re.DOTALL)
    cat_links = get_category_links_html(root_path=root)
    new_header = HEADER_HTML_TEMPLATE.format(root=root, cat_links=cat_links)
    content = header_pattern.sub(new_header, content)

    # 3. Update JavaScript functions
    script_pattern = re.compile(r'<script>\s*(async function siteSearch.*?)\s*</script>', re.DOTALL)
    if script_pattern.search(content):
        content = script_pattern.sub(f'<script>\n{JS_FUNCTIONS}\n</script>', content)
    else:
        # Fallback: find any script block and replace it or append at end
        if 'siteSearch' in content:
             content = re.sub(r'async function siteSearch.*?\}', JS_FUNCTIONS, content, flags=re.DOTALL)

    # 4. Hybrid Link Fix in Detail Page Similar Grids
    # Find links like href="https://tv.tomito.xyz/movie/..." and fix them if local
    def fix_link(match):
        prefix = match.group(1)
        folder = match.group(1)
        slug = match.group(2)
        key = f"{folder}/{slug}"
        if key in LOCAL_SLUGS:
            return f'href="{root}{folder}/{slug}.html"'
        return match.group(0)

    content = re.sub(r'href="https://tv\.tomito\.xyz/(movie|tv)/([a-zA-Z0-9\-_]+)"', fix_link, content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    count = 0
    # Detail pages
    for folder in ['movie', 'tv']:
        dir_path = os.path.join(BASE_PATH, folder)
        if os.path.exists(dir_path):
            for filename in os.listdir(dir_path):
                if filename.endswith('.html'):
                    patch_file(os.path.join(dir_path, filename))
                    count += 1
                    if count % 100 == 0: print(f"Updated {count} files...")
    
    # Genre pages
    genre_path = os.path.join(BASE_PATH, 'genre')
    if os.path.exists(genre_path):
        for filename in os.listdir(genre_path):
            if filename.endswith('.html'):
                patch_file(os.path.join(genre_path, filename))
                count += 1

    # index.html (already built by build_homepage but let's be sure about head)
    # patch_file(os.path.join(BASE_PATH, 'index.html'))
    
    print(f"✅ Total site-wide hybrid URL sync complete. Total files updated: {count}")

if __name__ == '__main__':
    main()
