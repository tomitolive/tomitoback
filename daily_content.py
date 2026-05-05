#!/usr/bin/env python3
import os
import sys
import json
import logging
import subprocess
import random
import argparse
from datetime import datetime
from ai_engine import BOT_MISSIONS

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_PATH)

from mega_bot import get_tmdb_data, fetch_details, create_page, build_listing_pages
from trends_rss import get_trending_titles
import generate_search_index

INDEX_FILE = os.path.join(BASE_PATH, 'data', 'content_index.json')
DEFAULT_COUNT = 2  # total pages per run (50 movies and 50 tv per 24 hours => 2 pages per 30 minutes)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)


def load_index():
    """Load existing content index and return (list, seen_ids set)."""
    if os.path.exists(INDEX_FILE):
        try:
            with open(INDEX_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            seen = set()
            for item in data:
                tid = str(item.get('tmdb_id', ''))
                # We store as "media_type-id" to avoid collisions (e.g., movie-155 vs tv-155)
                m_type = item.get('folder', 'movie') # fallback to 'movie' if folder is missing
                if tid:
                    seen.add(f"{m_type}-{tid}")
                elif item.get('slug'):
                    parts = item['slug'].split('-')
                    if parts[0].isdigit():
                        seen.add(f"{m_type}-{parts[0]}")
            return data, seen
        except Exception:
            pass
    return [], set()


def fetch_fresh_items(media_type, seen_ids, target, mission=None):
    """
    Fetch `target` unseen TMDB items of `media_type`.
    Tries the provided mission first, then falls back to random popular pages.
    Never returns an ID already in seen_ids.
    """
    collected = []

    def _add(item):
        tid = str(item.get('id', ''))
        unique_key = f"{media_type}-{tid}"
        if tid and unique_key not in seen_ids:
            collected.append((tid, media_type))
            seen_ids.add(unique_key)
            return True
        return False

    # ── Primary: mission-based fetch ────────────────────────────────────────
    if mission:
        m_type = mission.get('type')
        for page in range(1, 30):
            if len(collected) >= target:
                break
            params = {'page': page, 'sort_by': 'popularity.desc', 'language': 'ar-SA'}
            endpoint = f'discover/{media_type}'
            if m_type == 'genre':
                params['with_genres'] = mission['id']
            elif m_type == 'company':
                params['with_companies'] = mission['id']
            elif m_type == 'trending':
                endpoint = f'trending/{media_type}/day'
            elif m_type == 'era':
                year_start, year_end = mission['range']
                params['primary_release_date.gte'] = f'{year_start}-01-01'
                params['primary_release_date.lte'] = f'{year_end}-12-31'
            data = get_tmdb_data(endpoint, params)
            if not data or 'results' not in data:
                break
            for item in data['results']:
                if item.get('vote_average', 0) > 7.0 and item.get('vote_count', 0) >= 2:
                    if _add(item) and len(collected) >= target:
                        break

    # ── Fallback: random foreign/popular pages ──────────────────────────────
    attempts = 0
    while len(collected) < target and attempts < 150:
        attempts += 1
        page = random.randint(1, 450)
        # Removed 'language': 'ar-SA' to allow fetching random foreign movies without restriction
        params = {'page': page, 'sort_by': 'popularity.desc'}
        data = get_tmdb_data(f'discover/{media_type}', params)
        if not data or 'results' not in data:
            continue
        for item in data['results']:
            if item.get('vote_average', 0) > 7.0 and item.get('vote_count', 0) >= 2:
                if _add(item) and len(collected) >= target:
                    break

    return collected

def fetch_from_tmdb_trends(seen_ids, target, min_popularity=40):
    """Fetch newly trending items with ratings > 7.0."""
    collected = []
    for media_type in ['movie', 'tv']:
        if len(collected) >= target: break
        log.info(f"Fetching newly rising TMDB Trending {media_type}...")
        data = get_tmdb_data(f'trending/{media_type}/day', {'language': 'ar-SA'})
        if data and data.get('results'):
            for item in data['results']:
                if len(collected) >= target: break
                tid = str(item.get('id', ''))
                pop = item.get('popularity', 0)
                rating = item.get('vote_average', 0)
                vote_count = item.get('vote_count', 0)
                
                unique_key = f"{media_type}-{tid}"
                if tid and unique_key not in seen_ids and pop >= min_popularity and rating > 7.0 and vote_count >= 2:
                    collected.append((tid, media_type))
                    seen_ids.add(unique_key)
                    log.info(f"Matched Newly Rising Trend: {tid} ({media_type}) - Pop: {pop} - Rating: {rating}")
    return collected

def fetch_from_rss_trends(seen_ids, target):
    collected = []
    trend_titles = get_trending_titles()
    if not trend_titles: return []
    log.info(f"Checking {len(trend_titles)} RSS trends against TMDB (EN/AR only)...")
    def _add(item, media_type):
        tid = str(item.get('id', ''))
        orig_lang = item.get('original_language', '')
        if tid and tid not in seen_ids and orig_lang in ['en', 'ar']:
            collected.append((tid, media_type))
            seen_ids.add(tid)
            return True
        return False
    for title in trend_titles:
        if len(collected) >= target: break
        # Search movie
        movie_data = get_tmdb_data('search/movie', {'query': title, 'language': 'ar-SA'})
        if movie_data and movie_data.get('results'):
            if _add(movie_data['results'][0], 'movie'):
                log.info(f"Matched RSS Trend '{title}' to Movie ID {collected[-1][0]} (Lang: {movie_data['results'][0].get('original_language')})")
                continue
        # Search TV
        tv_data = get_tmdb_data('search/tv', {'query': title, 'language': 'ar-SA'})
        if tv_data and tv_data.get('results'):
            if _add(tv_data['results'][0], 'tv'):
                log.info(f"Matched RSS Trend '{title}' to TV ID {collected[-1][0]} (Lang: {tv_data['results'][0].get('original_language')})")
                continue
    return collected


def pick_missions(count):
    """
    Pick count missions divided equally between movies and tv shows.
    By default (count=2), it picks exactly 1 random movie and 1 random tv show.
    """
    slots = []
    movie_count = max(1, count // 2)
    tv_count = count - movie_count

    movie_pool = random.sample(BOT_MISSIONS, min(movie_count, len(BOT_MISSIONS)))
    for m in movie_pool:
        slots.append(('movie', m))

    tv_pool = random.sample(BOT_MISSIONS, min(tv_count, len(BOT_MISSIONS)))
    for m in tv_pool:
        slots.append(('tv', m))

    random.shuffle(slots)
    return slots[:count]   # limit to requested count


def main():
    parser = argparse.ArgumentParser(description='Tomito content generator')
    parser.add_argument('--count', type=int, default=DEFAULT_COUNT,
                        help='Number of NEW pages to generate this run')
    args = parser.parse_args()
    total = max(2, args.count)

    # ── Load seen IDs from content_index.json (the source of truth in git) ──
    all_index, seen_ids = load_index()
    print(f"📚 Already have {len(all_index)} pages. Seen IDs: {len(seen_ids)}")

    # ── Collect fresh TMDB IDs ───────────────────────────────────────────────
    tasks = []
    
    # Balance slots between movie and tv
    movie_count = total // 2
    tv_count = total - movie_count
    slots = (['movie'] * movie_count) + (['tv'] * tv_count)
    random.shuffle(slots)

    # 1. NEW LOGIC: Fetch newly rising (reach yalah tal3e) trends > 7.0 stars FIRST
    log.info("🚀 Fetching newly rising trends with high ratings (>7.0)...")
    trend_target = max(1, total // 2)
    trend_items = fetch_from_tmdb_trends(seen_ids, trend_target, min_popularity=40)
    if trend_items:
        tasks.extend(trend_items)

    # 2. Company missions as legacy fetcher logic
    log.info("🚀 Focusing on specialized company missions...")
    company_missions = [m for m in BOT_MISSIONS if m.get('type') == 'company']
    random.shuffle(company_missions)
    
    for i, mission in enumerate(company_missions):
        if len(tasks) >= total: break
        media_type = slots[len(tasks)] if len(tasks) < len(slots) else random.choice(['movie', 'tv'])
        items = fetch_fresh_items(media_type, seen_ids, 1, mission=mission)
        if items:
            tasks.extend(items)
            log.info(f"Found item from {mission['name']} ({media_type})")

    if len(tasks) < total:
        log.info(f"Seeking more from authorized pool...")
        random.shuffle(company_missions)
        for mission in company_missions:
            if len(tasks) >= total: break
            media_type = random.choice(['movie', 'tv'])
            items = fetch_fresh_items(media_type, seen_ids, 1, mission=mission)
            if items:
                tasks.extend(items)

    # Trim to exact count
    tasks = tasks[:total]

    if not tasks:
        print("⚠️  No new items found. All popular content may already be indexed.")
        return

    print(f"\n🚀 Generating {len(tasks)} new pages...\n")

    created = 0
    for i, (tid, mt) in enumerate(tasks, 1):
        print(f"[{i:02d}/{len(tasks)}] 📥 {mt.upper()} ID: {tid}")
        details = fetch_details(tid, mt)
        if not details:
            print(f"       ❌ TMDB fetch failed — skipping")
            continue

        data = details.get('ar') or details.get('en') or {}
        title = data.get('title') or data.get('name') or tid
        print(f"       ⚙️  AI descriptions for '{title}'...")

        page_path, entry = create_page(details, mt, is_trend=True)
        if entry:
            all_index.append(entry)
            created += 1
            print(f"       ✅ Created: {page_path}")
            # Trigger Indexing immediately
            try:
                import google_indexer
                idx_url = f"https://tomito.xyz/{page_path}"
                status = google_indexer.index_new_page(idx_url)
                if status == "SUCCESS":
                    print(f"       📡 Indexing: DONE")
                elif status == "ALREADY_INDEXED":
                    print(f"       📡 Indexing: SKIP (Already Done)")
                else:
                    print(f"       📡 Indexing: {status}")
            except Exception as e:
                log.warning(f"Failed to auto-index {page_path}: {e}")
        else:
            print(f"       ❌ AI failed or empty — page skipped")

    print(f"\n✅ Done! Created {created}/{len(tasks)} pages.")

    # ── Save updated index ───────────────────────────────────────────────────
    os.makedirs(os.path.dirname(INDEX_FILE), exist_ok=True)
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_index, f, ensure_ascii=False, indent=2)
    print(f"💾 content_index.json updated ({len(all_index)} total entries)")

    # ── Rebuild homepage & sitemaps ──────────────────────────────────────────
    # ── Rebuild homepage & sitemaps ──────────────────────────────────────────
    try:
        import build_homepage
        build_homepage.build()
        if hasattr(build_homepage, 'build_all_pages'):
            build_homepage.build_all_pages()
        
        from mega_bot import build_listing_pages
        build_listing_pages()
        print("🏗️  Homepage and listing pages rebuilt.")
        
        # ── Update Search Index ──────────────────────────────────────────────
        generate_search_index.generate()
        print("🔍 Search index updated.")
    except Exception as e:
        log.warning(f"Rebuild warning: {e}")

    # ── Git push (local runs only — GitHub Actions handles its own push) ─────
    git_sync = os.path.join(BASE_PATH, 'git_sync.sh')
    if os.path.exists(git_sync):
        try:
            subprocess.run(['bash', git_sync], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass


if __name__ == '__main__':
    main()
