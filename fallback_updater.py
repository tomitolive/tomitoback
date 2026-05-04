#!/usr/bin/env python3
"""
fallback_updater.py
-------------------
بوت تحديث صفحات Fallback بالذكاء الاصطناعي (Cohere).
- يقرأ fallback_pages.json
- يسحب 3 صفحات فقط
- يحذفهم مباشرة من الجيسون (ضمان عدم التكرار)
- يعيد بناء كل صفحة بوصف AI جديد (يكتب فوق القديم)
"""

import os
import sys
import json
import logging
import time
import re
import requests

# ── الضروري: حدد مسار المشروع أولاً ────────────────────────────────────────
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_PATH)

# ── مفتاح Cohere من secret أو hardcoded ──────────────────────────────────────
COHERE_API_KEY = (
    os.environ.get("COHERE_API_KEY") or
    "Eu2gSU7cjS95P2AO7w3IKHnWy13SLxtebqZ7OqEj"
)

# ── Monkey-patch: بدل ai_engine._call_llm بـ Cohere ─────────────────────────
def _cohere_call_llm(system_msg, user_msg):
    """استبدال Gemini بـ Cohere command-r-plus للنصوص العربية."""
    url = "https://api.cohere.com/v2/chat"
    headers = {
        "Authorization": f"Bearer {COHERE_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "model": "command-r-08-2024",
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=60)
        if res.status_code != 200:
            logging.error(f"Cohere Error {res.status_code}: {res.text[:300]}")
            return None
        data = res.json()
        text = data.get("message", {}).get("content", [{}])[0].get("text", "")
        if not text:
            return None
        return re.sub(r'```json\s*|\s*```', '', text).strip()
    except Exception as e:
        logging.error(f"Cohere API Error: {e}")
        return None

# ── تحميل ai_engine وتبديل الدالة ──────────────────────────────────────────
import ai_engine
ai_engine._call_llm = _cohere_call_llm

# ── تحميل mega_bot بعد التعديل ──────────────────────────────────────────────
import mega_bot

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
log = logging.getLogger(__name__)

FALLBACK_JSON = os.path.join(BASE_PATH, "fallback_pages.json")
BATCH_SIZE = 3


def load_queue():
    """تحميل قائمة الصفحات المنتظرة."""
    if not os.path.exists(FALLBACK_JSON):
        return []
    with open(FALLBACK_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def save_queue(queue):
    """حفظ القائمة بعد الحذف."""
    with open(FALLBACK_JSON, "w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)


def process_batch():
    """سحب 3 صفحات، تحديثها، وحذفها من الملف."""
    queue = load_queue()

    if not queue:
        log.info("✅ Queue is empty. All fallback pages have been updated!")
        return False  # finished

    # سحب أول 3 فقط
    batch = queue[:BATCH_SIZE]
    remaining = queue[BATCH_SIZE:]

    # حفظ القائمة فوراً قبل المعالجة (ضمان عدم التكرار)
    save_queue(remaining)
    log.info(f"📋 Processing {len(batch)} pages. {len(remaining)} remaining in queue.")

    success = 0
    for item in batch:
        tmdb_id = str(item.get("id", ""))
        media_type = item.get("type", "movie")
        file_name = item.get("file", "")

        log.info(f"🔄 [{success+1}/{len(batch)}] {media_type.upper()} ID: {tmdb_id} — {file_name}")

        try:
            details = mega_bot.fetch_details(tmdb_id, media_type)
            if not details:
                log.warning(f"   ⚠️  TMDB fetch failed for ID {tmdb_id} — skipping")
                continue

            # create_page يكتب فوق الملف الموجود تلقائياً
            page_path, entry = mega_bot.create_page(details, media_type, is_trend=True)

            if entry:
                success += 1
                log.info(f"   ✅ Updated: {page_path}")
            else:
                log.warning(f"   ❌ AI generation failed for {file_name}")

        except Exception as e:
            log.error(f"   ❌ Error processing {file_name}: {e}")

        # استراحة قصيرة بين الطلبات
        time.sleep(2)

    log.info(f"✅ Batch done: {success}/{len(batch)} updated.")
    return True  # continue


if __name__ == "__main__":
    log.info("🚀 Starting Fallback Updater Bot (Cohere)...")
    log.info(f"🔑 Using Cohere Key: {COHERE_API_KEY[:15]}...")
    has_more = process_batch()
    if not has_more:
        log.info("🎉 All done! No more pages to update.")
    else:
        remaining_count = len(load_queue())
        log.info(f"📊 {remaining_count} pages still in queue.")
