#!/usr/bin/env python3
import os
import json
import requests
import time
from concurrent.futures import ThreadPoolExecutor

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
INDEX_FILE = os.path.join(BASE_PATH, 'data', 'content_index.json')
IMG_DIR = os.path.join(BASE_PATH, 't', 'p', 'w500')
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

os.makedirs(IMG_DIR, exist_ok=True)

def download_image(item):
    poster_path = item.get('poster')
    if not poster_path or "tmdb.org" not in poster_path:
        return False
    
    # Extract filename from TMDB URL
    filename = poster_path.split('/')[-1]
    local_path = os.path.join(IMG_DIR, filename)
    
    if os.path.exists(local_path):
        return False # Already exists
    
    try:
        resp = requests.get(poster_path, timeout=10)
        if resp.status_code == 200:
            with open(local_path, 'wb') as f:
                f.write(resp.content)
            return True
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
    return False

def main():
    if not os.path.exists(INDEX_FILE):
        print("Index file not found.")
        return

    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        all_index = json.load(f)

    print(f"Starting sync for {len(all_index)} items...")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(download_image, all_index))
    
    downloaded = sum(results)
    print(f"Done! Downloaded {downloaded} new images.")

if __name__ == '__main__':
    main()
