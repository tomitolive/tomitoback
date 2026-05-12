#!/usr/bin/env python3
"""Generate sitemap index and individual category sitemaps from actual HTML files on disk."""

import os
from datetime import datetime

def generate_sitemaps():
    base_url = "https://tomito.xyz"
    img_base_url = "https://image.tomito.xyz/t/p/w500"
    root_dir = os.path.dirname(os.path.abspath(__file__))
    today = datetime.now().strftime('%Y-%m-%d')
    
    sitemap_index_urls = []
    MAX_LINKS = 300
    
    # 1. Main Root Sitemap (Homepage & Root Pages)
    root_urls = []
    root_urls.append({'loc': f"{base_url}/", 'priority': 1.0, 'freq': 'daily'})
    for f in os.listdir(root_dir):
        if f.endswith('.html') and f not in ['index.html', 'test.html', '404.html']:
            if os.path.isfile(os.path.join(root_dir, f)):
                slug = f[:-5]
                root_urls.append({'loc': f"{base_url}/{slug}", 'priority': 0.9, 'freq': 'weekly'})
    
    if root_urls:
        sitemap_index_urls.extend(write_split_sitemaps(root_dir, "root", root_urls, base_url, today, MAX_LINKS))

    # 2. Content Sitemaps
    content_dirs = ['movie', 'tv', 'genre']
    priority_map = {
        'movie': 0.8,
        'tv': 0.8,
        'genre': 0.7
    }
    
    for directory in content_dirs:
        dir_path = os.path.join(root_dir, directory)
        if not os.path.exists(dir_path):
            continue
        
        dir_urls = []
        priority = priority_map.get(directory, 0.7)
        freq = 'weekly' if directory in ['movie', 'tv'] else 'monthly'
        
        for entry in os.listdir(dir_path):
            full_path = os.path.join(dir_path, entry)
            
            if entry.endswith('.html'):
                slug = entry[:-5]
                url = f"{base_url}/{directory}/{slug}"
                
                # Image metadata attempt (assuming tmdb_id-slug format)
                img_url = None
                if '-' in entry:
                    tmdb_id = entry.split('-')[0]
                    if tmdb_id.isdigit():
                        img_url = f"{img_base_url}/{tmdb_id}.jpg"
                
                item = {'loc': url, 'priority': priority, 'freq': freq}
                if img_url: item['image'] = img_url
                dir_urls.append(item)
            elif os.path.isdir(full_path):
                # Subdirectories (like series folders)
                url = f"{base_url}/{directory}/{entry}"
                dir_urls.append({'loc': url, 'priority': priority, 'freq': freq})
                for sub_f in os.listdir(full_path):
                    if sub_f.endswith('.html') and sub_f != 'index.html':
                        sub_slug = sub_f[:-5]
                        sub_url = f"{base_url}/{directory}/{entry}/{sub_slug}"
                        dir_urls.append({'loc': sub_url, 'priority': priority - 0.1, 'freq': freq})
        
        if dir_urls:
            sitemap_index_urls.extend(write_split_sitemaps(root_dir, directory, dir_urls, base_url, today, MAX_LINKS))

    # 3. Generate Main Sitemap Index
    index_path = os.path.join(root_dir, 'sitemap.xml')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for loc in sitemap_index_urls:
            f.write(f'  <sitemap>\n')
            f.write(f'    <loc>{loc}</loc>\n')
            f.write(f'    <lastmod>{today}</lastmod>\n')
            f.write(f'  </sitemap>\n')
        f.write('</sitemapindex>')
    
    print(f"\nGenerated sitemap index: {index_path} with {len(sitemap_index_urls)} sub-sitemaps.")

def write_split_sitemaps(root_dir, name, urls, base_url, date, max_links):
    """Splits URLs into chunks of max_links and writes separate XML files."""
    # Deduplicate
    unique_urls = {}
    for u in urls:
        loc = u['loc']
        if loc not in unique_urls or u['priority'] > unique_urls[loc]['priority']:
            unique_urls[loc] = u
    
    sorted_items = sorted(unique_urls.values(), key=lambda x: x['loc'])
    chunks = [sorted_items[i:i + max_links] for i in range(0, len(sorted_items), max_links)]
    
    generated_urls = []
    for idx, chunk in enumerate(chunks, 1):
        filename = f"sitemap_{name}_{idx}.xml" if len(chunks) > 1 else f"sitemap_{name}.xml"
        filepath = os.path.join(root_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n')
            for item in chunk:
                f.write(f'  <url>\n')
                f.write(f'    <loc>{item["loc"]}</loc>\n')
                f.write(f'    <lastmod>{date}</lastmod>\n')
                f.write(f'    <changefreq>{item["freq"]}</changefreq>\n')
                f.write(f'    <priority>{item["priority"]:.1f}</priority>\n')
                if 'image' in item:
                    f.write(f'    <image:image>\n')
                    f.write(f'      <image:loc>{item["image"]}</image:loc>\n')
                    f.write(f'    </image:image>\n')
                f.write(f'  </url>\n')
            f.write('</urlset>')
        
        generated_urls.append(f"{base_url}/{filename}")
        print(f"    - {filename}: {len(chunk)} URLs")
    
    return generated_urls

if __name__ == '__main__':
    generate_sitemaps()
