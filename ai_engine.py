import os
import requests
import json
import time
import random
import logging
import re

log = logging.getLogger(__name__)

# Load COHERE_API_KEY from .env if it exists
if os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("COHERE_API_KEY="):
                os.environ["COHERE_API_KEY"] = line.split("=")[1].strip()

# Security: Key is read strictly from environment to avoid Github Secret Scanning blocks
COHERE_API_KEY = os.environ.get("COHERE_API_KEY", "").strip()

# قائمة مأموريات البوت: التركيز حصرياً على أقوى 20 شركة في العالم
BOT_MISSIONS = [
    {"name": "Netflix", "id": 213, "label": "نيتفلكس", "type": "company"},
    {"name": "Marvel Studios", "id": 420, "label": "مارفل", "type": "company"},
    {"name": "Disney", "id": 2, "label": "ديزني", "type": "company"},
    {"name": "Warner Bros.", "id": 174, "label": "وارنر بروس", "type": "company"},
    {"name": "Universal Pictures", "id": 33, "label": "يونيفرسال", "type": "company"},
    {"name": "Paramount", "id": 4, "label": "باراماونت", "type": "company"},
    {"name": "20th Century Studios", "id": 127928, "label": "القرن العشرين", "type": "company"},
    {"name": "Columbia Pictures", "id": 5, "label": "كولومبيا", "type": "company"},
    {"name": "HBO", "id": 459, "label": "HBO", "type": "company"},
    {"name": "Amazon Studios", "id": 20580, "label": "أمازون", "type": "company"},
    {"name": "Apple TV+", "id": 2552, "label": "أبل TV", "type": "company"},
    {"name": "Hulu", "id": 453, "label": "هولو", "type": "company"},
    {"name": "Lionsgate", "id": 1632, "label": "لايونزجيت", "type": "company"},
    {"name": "Pixar", "id": 3, "label": "بيكسار", "type": "company"},
    {"name": "DreamWorks", "id": 521, "label": "دريم ووركس", "type": "company"},
    {"name": "MBC Group (Shahid)", "id": 2697, "label": "شاهد / MBC", "type": "company"},
    {"name": "Canal+", "id": 104, "label": "كانال بلس", "type": "company"},
    {"name": "Miramax", "id": 14, "label": "ميراماكس", "type": "company"},
    {"name": "New Line Cinema", "id": 12, "label": "نيو لاين سينما", "type": "company"},
    {"name": "Sony Pictures", "id": 57, "label": "سوني", "type": "company"}
]

# قائمة الـ 20 طريق لضمان تنوع الأوصاف (Ultimate Narrative Master Styles)
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
    """Wrapper for Cohere API (command-r) explicitly configured for Arabic."""
    if not COHERE_API_KEY: return None
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
            log.error(f"Cohere Error {res.status_code}: {res.text[:300]}")
            return None
        data = res.json()
        if 'message' in data and 'content' in data['message'] and len(data['message']['content']) > 0:
            text = data['message']['content'][0]['text']
            return re.sub(r'```json\s*|\s*```', '', text).strip()
        return None
    except Exception as e:
        log.error(f"Cohere API Error: {e}")
        return None

LIVE_TRENDS_CACHE = {}
def get_live_trends(query, geo='SA', is_arabic_content=False):
    """Fallback-heavy trending logic to avoid 429s."""
    cache_key = f"{query}_{geo}"
    if cache_key in LIVE_TRENDS_CACHE: return LIVE_TRENDS_CACHE[cache_key]
    
    # Try TMDB Trending if it's a general genre search
    if "أفلام" in query or "مسلسلات" in query:
        media = "movie" if "أفلام" in query else "tv"
        try:
            from mega_bot import get_tmdb_data
            data = get_tmdb_data(f"trending/{media}/day", {})
            if data and data.get('results'):
                keywords = [r.get('title') or r.get('name') for r in data['results'][:5] if r.get('title') or r.get('name')]
                res = ", ".join(keywords)
                LIVE_TRENDS_CACHE[cache_key] = res
                return res
        except: pass

    # Otherwise try pyTrends with heavy safety
    try:
        from trends_fetcher import fetch_related_keywords
        trends = fetch_related_keywords(query, geo, is_arabic_content)
        LIVE_TRENDS_CACHE[cache_key] = trends
        return trends
    except:
        return ""

# --- Genre-based LSI Dictionary (SEO 2026) ---
GENRE_LSI = {
    "Action": ["مطاردات", "قتال", "سيناريو", "إخراج", "تصوير سينمائي", "أدرينالين"],
    "Adventure": ["مغامرة", "استكشاف", "رحلة", "غموض", "أبطال"],
    "Animation": ["أنمي", "رسوم متحركة", "عالم خيالي", "عائلي", "تحريك"],
    "Comedy": ["ضحك", "مواقف كوميدية", "ترفيه", "فكاهة"],
    "Crime": ["جريمة", "تحقيق", "غموض", "إثارة", "شرطة"],
    "Drama": ["دراما", "قصة مؤثرة", "مشاعر", "تطور الشخصيات"],
    "Horror": ["رعب", "تشويق", "غموض", "أحداث مرعبة", "خوف"],
    "Sci-Fi": ["خيال علمي", "المستقبل", "تكنولوجيا", "الفيزياء", "المنطق البشري"],
    "Thriller": ["إثارة", "تشويق", "توتر", "شك", "مفاجأة"]
}

def get_rising_seo_tags(subject_name, media_type='movie', year='2026', genres_ar=None, actor=None, platform=None, is_arabic_content=False):
    """
    Hybrid SEO Cocktail (v2026):
    - Intent Keywords: What users search for (watch, story, etc.)
    - Entity Keywords: Actors, Platforms, Similar Titles
    - Real-time Trends: From TMDB Trending API (reliable alternative to pyTrends)
    - LSI: Genre-specific synonyms
    """
    label = "فيلم" if media_type == 'movie' else "مسلسل"
    tag_label = "مترجم" if media_type == 'movie' else "مترجم كامل"
    
    # 1. Intent Mix
    intents = [
        f"{subject_name} {tag_label}", 
        f"قصة {label} {subject_name}",
        f"مشاهدة {subject_name} {year}",
        f"أحداث {subject_name} بالتفصيل"
    ]
    
    # 2. Trending Mix (TMDB Fallback)
    trending_query = f"{label} {genres_ar[0]}" if genres_ar else label
    trends = get_live_trends(trending_query)
    
    # 3. LSI & Genre Mix
    lsi = []
    if genres_ar:
        for g in genres_ar:
            if g in GENRE_LSI: lsi.extend(GENRE_LSI[g])
    selected_lsi = random.sample(lsi, min(3, len(lsi))) if lsi else []

    # 4. Final Cocktail
    cocktail = intents + selected_lsi + ([trends] if trends else []) + [f"توميتو {subject_name}"]
    random.shuffle(cocktail)
    
    res = ", ".join([c.strip() for c in cocktail if c])
    return re.sub(r'\s+', ' ', res).strip()

def generate_bilingual_description(title_ar, title_en, overview_ar, overview_en, year, genres_ar, media_type, actor=None, platform=None, is_arabic_content=False, *args, **kwargs):
    """🛡️ The Ultimate Narrative Master Implementation with Gemini 2.5 Flash"""
    genres_str = ", ".join(genres_ar) if isinstance(genres_ar, list) else str(genres_ar)
    selected_style = random.choice(NARRATIVE_STYLES)
    
    system = f"""🛡️ Role: Cinematic Storyteller & Movie Blogger
    Task: Write a UNIQUE and NATURAL review/description for "{title_ar}".
    
    ⚠️ MANDATORY RULES (REMOVE AI FOOTPRINT):
    1. STYLE: Write like a human movie fan on a blog. NO "bot" or "assistant" tone.
    2. STARTING: NEVER start with cliches like "في عالم..." or "في قلب..." or "تدور أحداث...". Start with a strong hook, a question, or a bold statement about the character's situation.
    3. LANGUAGE: Use professional but accessible Arabic (Fusha/Light). NO actor names, NO release years.
    4. NO AI CLICHES: Avoid words like "تحفة", "ملحمة", "مذهل" if used generically. Be specific about the tension or emotion.
    5. STRUCTURE: 3-5 short, punchy sentences.
    6. INTRO/OUTRO: Include a custom dynamic intro and outro within the JSON that sounds like a personal recommendation.

    📥 Return strictly as JSON:
    {{
      "intro": "A natural, non-repetitive opening hook...",
      "desc_ar": "The unique 3rd-person cinematic narrative...",
      "meta_desc": "Suspenseful hook (max 155 chars)...",
      "seo_title_ar": "Creative SEO Title",
      "outro": "A natural friendly closing recommendation..."
    }}"""

    user = f"Title: {title_ar}. Type: {genres_str}. Original Story: {overview_ar}."
    res = _call_llm(system, user)
    
    if not res:
        log.error("❌ Cohere returned an empty response. Verify API Key limits or safety filters.")

    try:
        data = json.loads(res or "{}")
        # Integration of Rising Keywords
        t_query = title_ar if title_ar and title_ar.strip() else title_en
        data["keywords"] = get_rising_seo_tags(t_query, media_type, year, genres_ar, actor, platform, is_arabic_content)
        
        # Ensure we have all fields
        if "desc_ar" not in data and "arabic" in data: # handle different formats
             data["desc_ar"] = data["arabic"].get("description", overview_ar)
             data["meta_desc"] = data["arabic"].get("meta_description", "")
             data["seo_title_ar"] = data["arabic"].get("seo_headers", {}).get("title", "")
             data["desc_en"] = data.get("english", {}).get("description", overview_en)
        
        return data
    except:
        log.warning("AI failed to return valid JSON. Using fallbacks.")
        return {
            "desc_ar": overview_ar, 
            "desc_en": overview_en,
            "meta_desc": f"مشاهدة {title_ar} مترجم بجودة عالية على توميتو.",
            "keywords": get_rising_seo_tags(title_ar),
            "seo_title_ar": f"مشاهدة {title_ar} مترجم اون لاين - توميتو",
            "opinion": "عمل سينمائي مذهل يستحق المتابعة."
        }

def generate_seo_content(title, overview, media_type, year, genres=[], *args, **kwargs):
    res = generate_bilingual_description(title, title, overview, overview, year, genres, media_type)
    if res:
        return {
            "seo_title": res.get("seo_title_ar", f"مشاهدة {title} مترجم"),
            "ai_description": res.get("desc_ar", overview),
            "meta_desc": res.get("meta_desc", ""),
            "keywords": res.get("keywords", "")
        }
    return None

def generate_meta_tags(title_ar, title_en, year, media_type='movie', *args, **kwargs):
    return {
        "meta_desc": f"مشاهدة {title_ar} ({year}) مترجم اون لاين بجودة عالية HD حصرياً على توميتو.",
        "keywords": get_rising_seo_tags(title_ar)
    }

def generate_faq(*args, **kwargs): return '<div class="faq-item">تفاصيل القصة قريباً...</div>'
def generate_tomito_opinion(title_ar, *args, **kwargs): return f"رأي توميتو: {title_ar} عمل يستحق الاستكشاف."

def generate_page_intro_outro(title_ar, title_en, year, genres_ar, media_type, desc_ar):
    """Placeholder: Now handled by generate_bilingual_description within the same AI call."""
    return "", ""
