import os
import random
import logging
import re
import time
from pytrends.request import TrendReq
import urllib3
# Monkey-patch urllib3 to handle pytrends compatibility with urllib3 2.0+
try:
    from urllib3.util import retry
    _original_retry_init = retry.Retry.__init__
    def patched_retry_init(self, *args, **kwargs):
        # If method_whitelist is passed (common in pytrends), move it to allowed_methods
        if 'method_whitelist' in kwargs:
            val = kwargs.pop('method_whitelist')
            if 'allowed_methods' not in kwargs:
                kwargs['allowed_methods'] = val
        _original_retry_init(self, *args, **kwargs)
    retry.Retry.__init__ = patched_retry_init
    
    # Also add the property so it can be read back if needed
    if not hasattr(retry.Retry, 'method_whitelist'):
        retry.Retry.method_whitelist = property(
            lambda self: getattr(self, 'allowed_methods', None),
            lambda self, v: setattr(self, 'allowed_methods', v)
        )
except Exception as e:
    print(f"Monkey-patch failed: {e}")

log = logging.getLogger(__name__)

PROXIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Webshare 10 proxies.txt')

def is_clean_text(text):
    """
    Strict Rule: Only Arabic (أ-ي), English (A-Z, a-z), Numbers (0-9), and basic punctuation.
    Filters out ALL other scripts (Chinese, Japanese, Hindi, French accents, etc).
    """
    if not text: return False
    # Arabic range: \u0621-\u064A and \u0660-\u0661-\u0669 (digits)
    # English range: a-zA-Z
    # Symbols: \s, . , - , : , ( , ) , / , !
    pattern = r'^[a-zA-Z0-9\s\u0621-\u064A\u0660-\u0669\.\-\:\(\)\/\!\،\؟]+$'
    return bool(re.match(pattern, str(text)))

def clean_strict(text):
    """Removes any character that doesn't match the strict Ar/En pattern."""
    if not text: return ""
    # Added ',' to the pattern to preserve keyword commas
    keep_pattern = r'[^a-zA-Z0-9\s\u0621-\u064A\u0660-\u0669\.\-\:\(\)\/\!\،\؟\,]'
    cleaned = re.sub(keep_pattern, '', str(text))
    return re.sub(r'\s+', ' ', cleaned).strip()

def get_random_proxy():
    secret_proxy = os.environ.get('PROXY_URL')
    if secret_proxy: return secret_proxy
    if os.path.exists(PROXIES_FILE):
        with open(PROXIES_FILE, 'r') as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        if lines:
            line = random.choice(lines)
            parts = line.split(':')
            if len(parts) == 4:
                ip, port, user, pwd = parts
                return f"http://{user}:{pwd}@{ip}:{port}"
    return None

import xml.etree.ElementTree as ET
import requests

def fetch_related_keywords(title, geo='SA'):
    """Fetch Top and Rising related queries from target regions (SA, MA, EG, DZ, TN, US)."""
    is_arab = geo in ['SA', 'MA', 'EG', 'DZ', 'TN', 'AR']
    target_geos = ['SA', 'MA', 'EG', 'DZ', 'TN'] if is_arab else ['US']
    
    all_queries = []
    seen = set()

    # Timeframes to check
    timeframes = ['now 7-d', 'now 1-d']

    proxy = get_random_proxy()
    proxies = [proxy] if proxy else []

    try:
        # Use slightly higher backoff and retries to handle 429 graciously
        pytrends = TrendReq(hl='ar' if is_arab else 'en-US', tz=360, timeout=(10,25), proxies=proxies, retries=3, backoff_factor=2)
        
        for tf in timeframes:
            if len(all_queries) >= 12: break
            for g_code in target_geos:
                try:
                    log.info(f"Fetching trends for '{title}' in {g_code} ({tf})...")
                    pytrends.build_payload([title], cat=0, timeframe=tf, geo=g_code)
                    data = pytrends.related_queries().get(title)
                    
                    if data:
                        if data.get('rising') is not None and not data['rising'].empty:
                            all_queries.extend(data['rising']['query'].tolist())
                        if data.get('top') is not None and not data['top'].empty:
                            all_queries.extend(data['top']['query'].tolist())
                except Exception as e:
                    err_msg = str(e)
                    log.warning(f"Failed payload for {title} in {g_code} ({tf}): {err_msg}")
                    if '429' in err_msg or 'too many' in err_msg.lower():
                        log.warning("Google is rate-limiting (429). Falling back to smart keywords for this title.")
                        break # Break the geo loop
            
            # If we broke the geo loop due to 429, we should also break the timeframe loop
            if '429' in locals().get('err_msg', '') or 'too many' in locals().get('err_msg', '').lower():
                break

        # Deduplicate and clean
        clean_queries = []
        for q in all_queries:
            q_str = str(q).strip()
            if q_str and q_str.lower() not in seen:
                if is_clean_text(q_str):
                    clean_queries.append(q_str)
                    seen.add(q_str.lower())
        
        # Inject high-intent keywords (Prioritized)
        intent_keywords = [
            f"مشاهدة {title} مجانية", f"مشاهدة {title} مباشرة", f"تحميل {title} مجانا",
            f"{title} اون لاين", f"{title} مترجم", f"mochahada {title} majaniya"
        ] if is_arab else [
            f"watch {title} free", f"stream {title} online", f"download {title} HD"
        ]
        
        for ik in intent_keywords:
            if len(clean_queries) >= 25: break
            if ik.lower() not in seen:
                clean_queries.insert(0, ik) 
                seen.add(ik.lower())

        return ", ".join(clean_queries[:25])
            
    except Exception as e:
        log.warning(f"Pytrends failed for '{title}': {e}")

    # Fallback Smart Keywords
    if is_arab:
        return f"مشاهدة {title}, تحميل فيلم {title}, {title} اون لاين, {title} جودة عالية HD, {title} مترجم, قصة {title}, {title} ايجي بست"
    else:
        return f"watch {title} online, {title} full movie streaming, download {title} HD, {title} release date"



if __name__ == "__main__":
    print(f"Testing SA trends: {fetch_related_keywords('Title test', 'SA')}")
    print(f"Testing US trends: {fetch_related_keywords('Title test', 'US')}")
