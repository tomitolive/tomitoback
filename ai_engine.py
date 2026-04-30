import os
import requests
import json
import time
import random
import logging
import re

log = logging.getLogger(__name__)
API_KEY = os.environ.get("GROQ_API_KEY", "").strip()

# قائمة التصنيفات
BOT_MISSIONS = [
    {"name": "Action", "id": 28, "label": "أكشن", "type": "genre"},
    {"name": "Adventure", "id": 12, "label": "مغامرة", "type": "genre"},
    {"name": "Animation", "id": 16, "label": "أنمي", "type": "genre"},
    {"name": "Comedy", "id": 35, "label": "كوميديا", "type": "genre"},
    {"name": "Crime", "id": 80, "label": "جريمة", "type": "genre"},
    {"name": "Drama", "id": 18, "label": "دراما", "type": "genre"},
    {"name": "Horror", "id": 27, "label": "رعب", "type": "genre"},
    {"name": "Sci-Fi", "id": 878, "label": "خيال علمي", "type": "genre"},
    {"name": "Thriller", "id": 53, "label": "إثارة", "type": "genre"},
    {"name": "Romance", "id": 10749, "label": "رومانسية", "type": "genre"},
    {"name": "Disney", "id": 2, "label": "ديزني", "type": "company", "logo": "https://image.tmdb.org/t/p/w300/w890vH9m7S8N7S2pX9jH9rL7yH.png"},
    {"name": "Netflix", "id": 175965, "label": "نتفليكس", "type": "company", "logo": "https://image.tmdb.org/t/p/w200/wwemzKWzjKYJFfCeiB57q3r4Bcm.png"},
    {"name": "HBO", "id": 101, "label": "HBO", "type": "company", "logo": "https://image.tmdb.org/t/p/w300/tuomPhY2UtuPTqqKB4vJuRGAs24.png"}
]

# قائمة الـ 20 طريق لضمان تنوع الأوصاف
NARRATIVE_STYLES = [
    "Start directly with the main character's struggle or a pivotal event.",
    "Start by describing the atmosphere or the visual tone of the world.",
    "Start with a philosophical or suspenseful statement related to the plot.",
    "Start by highlighting the hidden secrets or the main mystery.",
    "Focus on the emotional core or the high stakes of the story.",
    "Begin with an action-packed or intense moment from the synopsis.",
    "Start with a prophecy, a fate, or a turning point that changes everything.",
    "Focus on the protagonist's personality and their inner conflict.",
    "Start with the aftermath of a big event and then build the story.",
    "Use a warning or a cautionary tone about the dangers in the story.",
    "Start by describing the unique location where the events take place.",
    "Focus on the ticking clock or the limited time the characters have.",
    "Begin like an ancient legend or a forgotten tale coming back to life.",
    "Start by describing the main villain or the opposing force.",
    "Focus on the quest or the search for something lost or hidden.",
    "Start by contrasting the peace before the chaos or the light before the dark.",
    "Describe the story from the perspective of an observer or the world at large.",
    "Start by posing a 'What if' scenario based on the story's premise.",
    "Focus on the themes of betrayal, trust, or hidden alliances.",
    "Start with a single decision that triggers the entire chain of events."
]

def _call_llm(system_msg, user_msg):
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ],
        "temperature": 0.6, 
        "response_format": {"type": "json_object"}
    }
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    time.sleep(16)
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=45)
        data = res.json()
        if 'choices' in data:
            return data['choices'][0]['message']['content'].strip()
        return None
    except Exception as e:
        log.error(f"Error: {e}")
        return None

LIVE_TRENDS_CACHE = {}
def get_live_trends(title, geo):
    cache_key = f"{title}_{geo}"
    if cache_key not in LIVE_TRENDS_CACHE:
        try:
            from trends_fetcher import fetch_related_keywords
            trends = fetch_related_keywords(title, geo)
            LIVE_TRENDS_CACHE[cache_key] = trends
        except Exception:
            LIVE_TRENDS_CACHE[cache_key] = ""
    return LIVE_TRENDS_CACHE[cache_key]

def generate_bilingual_description(title_ar, title_en, overview_ar, overview_en, year, genres, media_type):
    genres_str = ", ".join(genres) if isinstance(genres, list) else str(genres)
    selected_style = random.choice(NARRATIVE_STYLES)
    trend_arab = get_live_trends(title_ar, 'AR')
    trend_us = get_live_trends(title_en, 'US')

    system = f"""🛡️ The "Ultimate Narrative Master" Style Prompt
    Task: RETELL the story of "{title_ar}" in a unique way.
    DIRECTION: {selected_style}
    
    ⚠️ MANDATORY RULES (STRICT):
    1. STYLE: Creative storytelling. DO NOT copy-paste.
    2. HERO & NAMES: Mention the MAIN CHARACTER'S NAME (role name) ONLY if clearly known. Transliterate names to Arabic (e.g. Sarah -> سارة). NEVER translate names literally (e.g. Never use 'Himself' as a person's name).
    3. NO CLICHES: NEVER start with "في عالم..." or "في قلب...". 
    4. GRAMMAR: Start the first sentence with a NOUN (اسم) or an ACTION (فعل), never a preposition (حرف جر).
    5. LANGUAGE: Pure Arabic (أ-ي). No foreign characters.
    6. FORBIDDEN: NO actor names, NO years, NO SEO keywords like "مشاهدة" in the narrative.
    
    📥 Format (Strict JSON):
    {{
      "arabic": {{
        "description": "Narrative retelling in Arabic...",
        "meta_description": "Suspenseful summary...",
        "seo_headers": {{ "title": "Cinematic Title" }}
      }},
      "english": {{
        "description": "Creative narrative in English...",
        "seo_headers": {{ "title": "US Title" }}
      }}
    }}"""

    user = f"Title: {title_ar}. Type: {genres_str}. Original Story: {overview_ar}."
    
    if not API_KEY or API_KEY.startswith("AIza"):
        res = json.dumps({"arabic": {"description": "Fallback text...","meta_description": "Fallback...","seo_headers": {"title": "Title"}},"english": {"description": "Fallback...","seo_headers": {"title": "Title"}}})
    else:
        res = _call_llm(system, user)

    try:
        data = json.loads(res or "{}")
        arabic = data.get("arabic", {})
        english = data.get("english", {})
        seo_ar = arabic.get("seo_headers", {})
        try:
            from trends_fetcher import clean_strict
        except ImportError:
            def clean_strict(t): return t
        desc_ar = clean_strict(arabic.get("description", ""))
        if len(desc_ar) < 200 and overview_ar:
             desc_ar = clean_strict(f"{desc_ar}\n\n{overview_ar}")
        raw_keywords = ", ".join([k for k in [trend_arab, trend_us] if k]).strip()
        return {
            "desc_ar": desc_ar,
            "desc_en": clean_strict(english.get("description", "")),
            "meta_desc": clean_strict(arabic.get("meta_description", "") or arabic.get("description", "")[:155]),
            "keywords": clean_strict(raw_keywords),
            "seo_title_ar": clean_strict(seo_ar.get("title", "")),
            "seo_title_en": clean_strict(english.get("seo_headers", {}).get("title", ""))
        }
    except:
        return {}

def generate_seo_content(title, overview, media_type, genres=[], *args, **kwargs):
    res = generate_bilingual_description(title, title, overview, None, None, None, genres)
    if res and res.get("desc_ar"):
        return {
            "seo_title": res.get("seo_title_ar", f"مشاهدة {title} مترجم"),
            "ai_description": res["desc_ar"],
            "meta_desc": res.get("meta_desc", ""),
            "keywords": res.get("keywords", "")
        }
    return None

def generate_meta_tags(title_ar, title_en, year, *args, **kwargs):
    trend_arab = get_live_trends(title_ar, 'AR')
    trend_us = get_live_trends(title_en, 'US')
    final_keywords = ", ".join([k for k in [trend_arab, trend_us] if k]).strip()
    return {"meta_desc": f"مشاهدة {title_ar} مترجم {year} بجودة عالية.", "keywords": final_keywords}

def generate_faq(*args, **kwargs): return '<div class="faq-item">تفاصيل القصة قريباً...</div>'
def generate_tomito_opinion(*args, **kwargs): return "تقييم توميتو: عمل يستحق المشاهدة."

def generate_page_intro_outro(title, media_type, year, *args, **kwargs):
    starts = ["نقدم لكم اليوم", "استعدوا لرحلة مشوقة مع", "حصرياً على توميتو، شاهد"]
    mids = [f"الفيلم المنتظر {title}", f"الحبكة الدرامية لـ {title}"]
    ends = ["بترجمة احترافية.", "بصورة فائقة الجودة HD."]
    intro = f"{random.choice(starts)} {random.choice(mids)} {random.choice(ends)}"
    outro = f"في الختام، نتمنى لك مشاهدة طيبة لـ {title}."
    return intro, outro
