import os
import json
import xml.etree.ElementTree as ET
import requests
from google.oauth2 import service_account
import google.auth.transport.requests
import time
import sys
import re

# ==========================================
# الإعدادات (Settings)
# ==========================================
SERVICE_ACCOUNT_FILE = 'mythical-module-493722-n6-e2da3325c496.json'
SCOPES = ['https://www.googleapis.com/auth/indexing']
ENDPOINT = 'https://indexing.googleapis.com/v3/urlNotifications:publish'

SITE_URL = 'https://tomito.xyz'
SITEMAPS = ['sitemap_movie.xml', 'sitemap_tv.xml', 'sitemap_actor.xml']
PROGRESS_FILE = 'indexer_progress.json'
LINKS_PER_SITEMAP = 100 

def get_url_id(url):
    """Extract ID from URL."""
    match = re.search(r'/(?:movie|tv)/(\d+)', url)
    if match:
        return match.group(1)
    last_part = url.split('/')[-1]
    match = re.search(r'^(\d+)', last_part)
    if match:
        return match.group(1)
    return url

# ==========================================
# وظيفة الحصول على التوكن (Auth)
# ==========================================
def get_access_token():
    # المحاولة الأولى: القراءة من Secret (GitHub Actions)
    gcp_key = os.environ.get('GCP_INDEXING_KEY')
    
    if gcp_key:
        try:
            info = json.loads(gcp_key)
            credentials = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
            auth_request = google.auth.transport.requests.Request()
            credentials.refresh(auth_request)
            return credentials.token
        except Exception as e:
            print(f"❌ Error parsing GCP_INDEXING_KEY Secret: {e}")
            return None
    
    # المحاولة الثانية: القراءة من ملف Local (للتجربة عندك في الحاسوب)
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        try:
            credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            auth_request = google.auth.transport.requests.Request()
            credentials.refresh(auth_request)
            return credentials.token
        except Exception as e:
            print(f"❌ Error loading service account file: {e}")
            return None
            
    print("❌ No Authentication method found (No Secret or JSON file).")
    return None

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"indexed_ids": []}

def save_progress(progress):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def notify_google_index(url):
    token = get_access_token()
    if not token:
        return "AUTH_ERROR"
        
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    payload = {
        'url': url,
        'type': 'URL_UPDATED'
    }
    
    try:
        response = requests.post(ENDPOINT, headers=headers, json=payload)
        if response.status_code == 200:
            print(f"✅ Success: {url}")
            return "SUCCESS"
        elif response.status_code == 429:
            print(f"🚨 Rate limit hit (429): {url}")
            return "RATE_LIMIT"
        else:
            print(f"⚠️ Error {response.status_code}: {response.text}")
            return "ERROR"
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return "ERROR"

def index_new_page(url):
    """Index a single URL and save it to progress JSON to avoid duplicate indexing."""
    progress = load_progress()
    indexed_ids = set(map(str, progress.get("indexed_ids", [])))
    
    url_id = get_url_id(url)
    if url_id in indexed_ids:
        print(f"✅ Already indexed: {url}")
        return "ALREADY_INDEXED"
    
    print(f"📡 Sending to Google Indexing API: {url}")
    status = notify_google_index(url)
    if status == "SUCCESS" or status == "ERROR":
        indexed_ids.add(url_id)
        progress["indexed_ids"] = list(indexed_ids)
        save_progress(progress)
        
    return status

def main():
    print(f"🚀 Starting Indexing for {SITE_URL}...")
    progress = load_progress()
    indexed_ids = set(map(str, progress.get("indexed_ids", [])))
    
    total_indexed = 0
    
    for sitemap_path in SITEMAPS:
        if not os.path.exists(sitemap_path):
            print(f"❓ Sitemap not found: {sitemap_path}")
            continue
            
        print(f"📖 Reading {sitemap_path}...")
        tree = ET.parse(sitemap_path)
        root = tree.getroot()
        
        # التعامل مع الـ Namespaces في XML
        ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        urls_to_index = []
        for url_node in root.findall('ns:url/ns:loc', ns):
            url = url_node.text
            url_id = get_url_id(url)
            if url_id not in indexed_ids:
                urls_to_index.append((url, url_id))
        
        if not urls_to_index:
            print(f"✅ All links in {sitemap_path} are already indexed.")
            continue

        urls_to_process = urls_to_index[:LINKS_PER_SITEMAP]
        print(f"▶️ Indexing {len(urls_to_process)} new links out of {len(urls_to_index)} remaining...")
        
        rate_limit_hit = False
        for url, url_id in urls_to_process:
            status = notify_google_index(url)
            if status == "SUCCESS":
                total_indexed += 1
                indexed_ids.add(url_id)
            elif status == "RATE_LIMIT":
                rate_limit_hit = True
                break
            else:
                # نعتبرها تمت (أو فيها مشكل) باش ما نبقاوش نعاودو نفس الغلط
                indexed_ids.add(url_id)
            
            # حفظ التقدم أول بأول
            progress["indexed_ids"] = list(indexed_ids)
            save_progress(progress)
            time.sleep(1) # باش ما نضغطوش على الـ API
            
        if rate_limit_hit:
            print("🚨 Stopping due to Rate Limit.")
            break

    print(f"\n🎉 Done! Indexed {total_indexed} links in this session.")

if __name__ == "__main__":
    main()
