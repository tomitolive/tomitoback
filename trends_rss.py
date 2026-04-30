import requests
import xml.etree.ElementTree as ET
import logging
import re

log = logging.getLogger(__name__)

RSS_FEEDS = {
    'EG': 'https://trends.google.com/trends/trendingsearches/daily/rss?geo=EG',
    'SA': 'https://trends.google.com/trends/trendingsearches/daily/rss?geo=SA',
    'US': 'https://trends.google.com/trends/trendingsearches/daily/rss?geo=US'
}

def is_clean_text(text):
    """Golden Rule: Only Arabic, English, and Numbers allowed."""
    if not text: return False
    import re
    pattern = r'^[a-zA-Z0-9\s\u0621-\u064A\u0660-\u0669]+$'
    return bool(re.match(pattern, text))

def get_trending_titles():
    titles = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    for geo, url in RSS_FEEDS.items():
        try:
            log.info(f"Fetching RSS trends for {geo}...")
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200: continue
            root = ET.fromstring(resp.text)
            for item in root.findall('.//item'):
                title_node = item.find('title')
                if title_node is not None and title_node.text:
                    title = title_node.text.strip()
                    if title and title not in titles:
                        if is_clean_text(title):
                            titles.append(title)
                        else:
                            log.info(f"Filtering out foreign RSS trend: {title}")
        except Exception as e: log.warning(f"Failed to fetch RSS for {geo}: {e}")
    return titles
