import os
import requests
import json
import time
import random
import logging
import re

log = logging.getLogger(__name__)

# Load GEMINI_API_KEY from .env if it exists
if os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                os.environ["GEMINI_API_KEY"] = line.split("=")[1].strip()

# Security: Key is read from environment for safety
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

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
    """Wrapper for Gemini 2.5 Flash following the user's Groq style."""
    if not GEMINI_API_KEY: return None
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"System: {system_msg}\n\nUser: {user_msg}"}
                ]
            }
        ]
    }
    headers = {"Content-Type": "application/json"}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=45)
        if res.status_code != 200:
            log.error(f"Gemini Error {res.status_code}: {res.text}")
            return None
        data = res.json()
        if 'candidates' in data and len(data['candidates']) > 0:
            text = data['candidates'][0]['content']['parts'][0]['text']
            return re.sub(r'```json\s*|\s*```', '', text).strip()
        return None
    except Exception as e:
        log.error(f"Gemini API Error: {e}")
        return None

LIVE_TRENDS_CACHE = {}
def get_live_trends(title, geo='SA'):
    cache_key = f"{title}_{geo}"
    if cache_key not in LIVE_TRENDS_CACHE:
        try:
            from trends_fetcher import fetch_related_keywords
            trends = fetch_related_keywords(title, geo)
            LIVE_TRENDS_CACHE[cache_key] = trends
        except Exception:
            LIVE_TRENDS_CACHE[cache_key] = ""
    return LIVE_TRENDS_CACHE[cache_key]

def get_rising_seo_tags(subject_name):
    """
    الدمج بين المواقع الشهيرة والكلمات النامية (Breakout) من PyTrends فقط
    """
    rising_keywords = get_live_trends(subject_name)
    fixed_sites = "ايجي بست, شاهد, ماي سيما, EgyBest, Shahid, MyCima, Netflix, Canal+, Streaming, Watch online, Regarder en ligne"
    
    all_keywords = f"{fixed_sites}, {rising_keywords}" if rising_keywords else fixed_sites
    # تنظيف النص
    cleaned = re.sub(r'[^a-zA-Z0-9\u0600-\u06FF\s,éèàçëêîôû]', '', all_keywords)
    return re.sub(r'\s+', ' ', cleaned).strip()

def generate_bilingual_description(title_ar, title_en, overview_ar, overview_en, year, genres_ar, media_type, *args, **kwargs):
    """🛡️ The Ultimate Narrative Master Implementation with Gemini 2.5 Flash"""
    genres_str = ", ".join(genres_ar) if isinstance(genres_ar, list) else str(genres_ar)
    selected_style = random.choice(NARRATIVE_STYLES)
    
    system = f"""🛡️ The "Ultimate Narrative Master" Style Prompt
    Task: RETELL the story of "{title_ar}" in a unique, cinematic, and CONCISE way.
    DIRECTION: {selected_style}
    
    ⚠️ MANDATORY RULES (STRICT):
    1. UNIQUENESS: Every generation MUST be unique. DO NOT use common or repetitive patterns. 
    2. STARTING WORD: Ensure the first word of the description is DIFFERENT for every movie (e.g., Verb, Noun, Question). DO NOT always start with the same pattern.
    3. LENGTH: Aim for 3 to 5 short and powerful sentences (Approx 3-4 lines). DO NOT exceed 6 lines under any circumstances.
    4. STYLE: Creative storytelling. DO NOT copy-paste.
    5. HERO & NAMES: Mention the MAIN CHARACTER'S NAME ONLY if clearly known. 
    6. NO CLICHES: NEVER start with "في عالم..." or "في قلب...". 
    7. GRAMMAR: Start the first sentence with a NOUN (اسم) or an ACTION (فعل).
    8. FORBIDDEN: NO actor names, NO years, NO SEO keywords like "مشاهدة" in the actual narrative description.
    
    📥 Format (Strict JSON):
    {{
      "desc_ar": "3-5 cinematic sentences with a UNIQUE START...",
      "meta_desc": "Suspenseful brief summary (max 155 chars)...",
      "seo_title_ar": "Cinematic Title",
      "desc_en": "3-5 cinematic sentences with a UNIQUE START...",
      "opinion": "Critical perspective (1-2 sentences)..."
    }}"""

    user = f"Title: {title_ar}. Type: {genres_str}. Original Story: {overview_ar}."
    
    res = _call_llm(system, user)

    try:
        data = json.loads(res or "{}")
        # Integration of Rising Keywords
        data["keywords"] = get_rising_seo_tags(title_ar)
        
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
    label = "فيلم" if media_type == 'movie' else "مسلسل"
    
    starts = [
        "نقدم لكم اليوم", "استعدوا لرحلة مشوقة مع", "حصرياً على توميتو، شاهد", 
        "لمحبي السينما، إليكم", "نغوص اليوم في تفاصيل", "اكتشف معنا قصة", 
        "برؤية فنية مميزة، نعرض", "إليك مراجعة شاملة لـ", "توميتو يقدم لكم",
        "عش أجواء الإثارة مع", "بصورة فائقة الجودة، شاهد", "بعيداً عن المألوف، إليك",
        "من أقوى إنتاجات السنة،", "في هذه الصفحة تجد", "بترجمة احترافية، نضع بين يديك",
        "استمتع بمتابعة العمل المنتظر", "إليك نظرة حصرية على", "لكل عشاق الدراما،",
        "تجربة مشاهدة فريدة لـ", "لا تفوت فرصة مشاهدة"
    ]
    
    mids = [
        f"العمل الفني {title_ar}", f"تحفة {title_ar} ({year})", f"قصة {title_ar} المشوقة",
        f"أحداث {title_ar} التي هزت العالم", f"تفاصيل {title_ar} المثيرة", f"الحبكة الدرامية لـ {title_ar}",
        f"الفيلم العالمي {title_ar}", f"المسلسل الرائع {title_ar}", f"تطور أحداث {title_ar}"
    ]
    
    ends = [
        "بترجمة احترافية.", "بصورة فائقة الجودة HD.", "حصرياً على منصتنا.",
        "بجودة صوت وصورة مذهلة.", "اون لاين بدون إعلانات.", "لكل محبي هذا النوع.",
        "قصة تستحق المتابعة.", "على سيرفرات توميتو السريعة.", "من البداية حتى النهاية.",
        "بروابط مباشرة وسريعة.", "في تجربة لا تُنسى."
    ]
    
    intro = f"{random.choice(starts)} {random.choice(mids)} {random.choice(ends)}"
    outro = f"في الختام، نتمنى أن ينال {label} {title_ar} إعجابكم. لا تنسوا متابعة جديد الأفلام والمسلسلات على موقعكم توميتو."
    return intro, outro
