import os
import requests
import json
import time
import random
import logging
import re

log = logging.getLogger(__name__)
API_KEY = os.environ.get("GROQ_API_KEY", "").strip()

# قائمة التصنيفات لضمان استقرار العمليات
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
    # Major Production Companies (The Majors)
    {"name": "Disney", "id": 2, "label": "ديزني", "type": "company", "logo": "https://image.tmdb.org/t/p/w300/w890vH9m7S8N7S2pX9jH9rL7yH.png"},
    {"name": "Warner Bros", "id": 174, "label": "وارنر بروذرز", "type": "company", "logo": "https://image.tmdb.org/t/p/w300/ky0xOc3wYvc0T6Ozs0Vjp72rQcR.png"},
    {"name": "Universal", "id": 33, "label": "يونيفرسال", "type": "company", "logo": "https://image.tmdb.org/t/p/w300/8lvHyhZg3p239v9M9S9ZpZpZpZp.png"},
    {"name": "Paramount", "id": 4, "label": "باراماونت", "type": "company", "logo": "https://image.tmdb.org/t/p/w300/jay6WcMgagAklUt7i9Euwj1pzTF.png"},
    {"name": "Sony", "id": 57, "label": "سوني", "type": "company", "logo": "https://image.tmdb.org/t/p/w300/zV7uuh4RlLMtH66nHNzodGiOmEe.png"},
    {"name": "20th Century", "id": 12792, "label": "فوكس", "type": "company", "logo": "https://image.tmdb.org/t/p/w300/789z86SkhM9r6oYp9fSsh9Yp9fS.png"},
    # Streaming
    {"name": "Netflix", "id": 175965, "label": "نتفليكس", "type": "company", "logo": "https://image.tmdb.org/t/p/w200/wwemzKWzjKYJFfCeiB57q3r4Bcm.png"},
    {"name": "Amazon", "id": 24208, "label": "أمازون", "type": "company", "logo": "https://image.tmdb.org/t/p/w200/68vAnvFc9O6O9S9ZpZpZpZpZpZp.png"},
    {"name": "Apple", "id": 127928, "label": "آبل", "type": "company", "logo": "https://image.tmdb.org/t/p/w300/h0rjX5vjW5r8yEnUBStFarjcLT4.png"},
    # Powerhouses & Independents
    {"name": "A24", "id": 41077, "label": "A24", "type": "company", "logo": "https://image.tmdb.org/t/p/w300/1ZXsGaFPgrgS6ZZGS37AqD5uU12.png"},
    {"name": "Lionsgate", "id": 1632, "label": "لايونزجيت", "type": "company", "logo": "https://image.tmdb.org/t/p/w300/cisLn1YAUuptXVBa0xjq7ST9cH0.png"},
    {"name": "Marvel", "id": 420, "label": "مارفل", "type": "company", "logo": "https://image.tmdb.org/t/p/w300/hUzeosd33nzE5MCNsZxCGEKTXaQ.png"},
    {"name": "Lucasfilm", "id": 1, "label": "لوكاس فيلم", "type": "company", "logo": "https://image.tmdb.org/t/p/w300/tlVSws0RvvtPBwViUyOFAO0vcQS.png"},
    {"name": "Legendary", "id": 923, "label": "ليجنداري", "type": "company", "logo": "https://image.tmdb.org/t/p/w300/5UQsZrfbfG2dYJbx8DxfoTr2Bvu.png"},
    {"name": "Blumhouse", "id": 3172, "label": "بلوم هاوس", "type": "company", "logo": "https://image.tmdb.org/t/p/w300/rzKluDcRkIwHZK2pHsiT667A2Kw.png"},
    {"name": "New Line", "id": 12, "label": "نيو لاين", "type": "company", "logo": "https://image.tmdb.org/t/p/w300/2ycs64eqV5rqKYHyQK0GVoKGvfX.png"},
    {"name": "DreamWorks", "id": 521, "label": "دريم ووركس", "type": "company", "logo": "https://image.tmdb.org/t/p/w300/3BPX5VGBov8SDqTV7wC1L1xShAS.png"},
    # Arab Production
    {"name": "MBC Studios", "id": 125925, "label": "MBC", "type": "company", "logo": "https://image.tmdb.org/t/p/w300/9CeuSVhXnE5xkynAosEddIrbEiw.png"},
    {"name": "Synergy", "id": 104523, "label": "Synergy", "type": "company", "logo": "https://image.tmdb.org/t/p/w300/fH9m7S8N7S2pX9jH9rL7yH.png"},
    {"name": "HBO", "id": 101, "label": "HBO", "type": "company", "logo": "https://image.tmdb.org/t/p/w300/tuomPhY2UtuPTqqKB4vJuRGAs24.png"}
]

def _call_llm(system_msg, user_msg):
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ],
        "temperature": 0.5, 
        "response_format": {"type": "json_object"}
    }
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    time.sleep(16)
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=45)
        data = res.json()
        if 'choices' in data:
            return data['choices'][0]['message']['content'].strip()
        else:
            log.error(f"Error: No choices in response: {data}")
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
    
    # Fetch live multi-geo trends
    trend_arab = get_live_trends(title_ar, 'AR')
    trend_us = get_live_trends(title_en, 'US')

    system = f"""🛡️ The "Ultimate Narrative Master" Style Prompt
    
    Task: Use your intelligence to UNDERSTAND the story of "{title_ar}" and RETELL it in a unique, suspenseful way.
    
    ⚠️ MANDATORY RULES (STRICT):
    1. STYLE: Creative storytelling. DO NOT copy-paste or just rephrase. You must "think" and tell the core events from a narrator's perspective.
    2. LANGUAGE: Pure Arabic (أ-ي) for the main description. No English/French/Foreign characters allowed inside the Arabic paragraphs.
    3. FORBIDDEN:
       - NO names of actors, directors, or producers.
       - NO release years (e.g., 2024, 1995).
       - NO SEO keywords like "مشاهدة", "تحميل", "مترجم", "بجودة عالية" inside the story text.
    4. STRUCTURE: 3 to 4 sections (Intro + Body + Suspenseful Outro).
    5. LENGTH: Strictly between 2.8 lines (min) and 4.1 lines (max) per section logic.
    6. UNIQUENESS: Every generation must be fresh. Adapt the tone to the Genre: {genres_str}.
    
    📥 Format (Strict JSON):
    {{
      "arabic": {{
        "description": "Narrative retelling in Arabic (Pure AR, no names, no years)...",
        "meta_description": "Suspenseful summary (Max 155 chars)...",
        "seo_headers": {{
          "title": "Cinematic Title"
        }}
      }},
      "english": {{
        "description": "Creative narrative in English...",
        "seo_headers": {{
          "title": "US Title"
        }}
      }}
    }}"""

    user = f"Title: {title_ar}. Type: {genres_str}. Original Story: {overview_ar}."
    
    # Fallback to avoid complete failure if AI API key is missing
    if not API_KEY or API_KEY.startswith("AIza"): # placeholder check
        log.warning("No valid GROQ_API_KEY found. Using static fallback for testing.")
        res = json.dumps({
            "arabic": {
                "description": f"شاهد واستمتع بفيلم {title_ar} {year} الذي ينتمي لفئة {genres_str}. تدور أحداث قصته حول تجربة فريدة ومشوقة تأخذك في رحلة لا تنسى. استمتع بمشاهدة {title_ar} بجودة عالية HD مترجم حصرياً.",
                "meta_description": f"مشاهدة {title_ar} مترجم {year} بجودة عالية اون لاين.",
                "seo_headers": {"title": f"مشاهدة {title_ar} مترجم HD"}
            },
            "english": {
                "description": f"Experience the amazing story of {title_en} ({year}). Join this journey in {genres_str} with full HD quality and English subtitles.",
                "seo_headers": {"title": f"Watch {title_en} online HD"}
            }
        })
    else:
        res = _call_llm(system, user)

    try:
        data = json.loads(res or "{}")
        arabic = data.get("arabic", {})
        english = data.get("english", {})
        seo_ar = arabic.get("seo_headers", {})
        seo_en = english.get("seo_headers", {})
        
        # Add cleaning pass
        try:
            from trends_fetcher import clean_strict
        except ImportError:
            def clean_strict(t): return t
            
        desc_ar = clean_strict(arabic.get("description", ""))
        # Protect against short descriptions (fallback to overview if needed)
        if len(desc_ar) < 200 and overview_ar:
             desc_ar = clean_strict(f"{desc_ar}\n\n{overview_ar}")

        # 100% Pytrends keywords (Merge Arab and US trends)
        raw_keywords = ", ".join([k for k in [trend_arab, trend_us] if k]).strip()
        final_keywords = clean_strict(raw_keywords)

        return {
            "desc_ar": desc_ar,
            "desc_en": clean_strict(english.get("description", "")),
            "meta_desc": clean_strict(arabic.get("meta_description", "") or arabic.get("description", "")[:155]),
            "keywords": final_keywords,
            "seo_title_ar": clean_strict(seo_ar.get("title", "")),
            "seo_title_en": clean_strict(seo_en.get("title", ""))
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
    return {
        "meta_desc": f"مشاهدة {title_ar} مترجم {year} بجودة عالية على توميتو.",
        "keywords": final_keywords
    }

def generate_faq(*args, **kwargs):
    return '<div class="faq-item">تفاصيل القصة قريباً...</div>'

def generate_tomito_opinion(*args, **kwargs):
    return "تقييم توميتو: عمل يستحق المشاهدة."

def generate_page_intro_outro(title, media_type, year, *args, **kwargs):
    """توليد مقدمة وخاتمة متغيرة بشكل كبير لضمان عدم التكرار (أكثر من 6000 تشكيلة)"""
    
    starts = [
        "نقدم لكم اليوم", "استعدوا لرحلة مشوقة مع", "إليكم مراجعة حصرية لـ", "حصرياً على توميتو، شاهد",
        "عشاق السينما على موعد مع", "إليك كل ما يخص", "تعمق في تفاصيل عمل سينمائي رائع وهو", "هل أنت جاهز لاكتشاف أسرار",
        "بجودة عالية وبدون إعلانات، شاهد", "نغوص اليوم في أحداث", "مغامرة فنية جديدة تنتظرك مع", "إليك نظرة شاملة على",
        "بلا شك، ستستمتع بمتابعة", "من أقوى إصدارات هذا العام، إليك", "بين يديكم الآن قصة", "اكتشف ما يخبئه لك",
        "في تجربة سينمائية فريدة، نتابع", "للباحثين عن المتعة والإثارة، إليكم", "بصورة فائقة النقاء، تابع", "إليك العمل الفني الذي أثار الجدل وهو"
    ]
    
    mids = [
        f"المحتوى الحصري {title}", f"العمل الفني المذهل {title}", f"الفيلم المنتظر {title}", f"هذا الإنتاج الضخم {title}",
        f"التجربة الفريدة {title}", f"الإصدار الجديد {title}", f"هذا العمل السينمائي {title}", f"التحفة الفنية {title}",
        f"المسلسل المثير {title}", f"الإنتاج المميز {title}", f"الحبكة الدرامية لـ {title}", f"الأحداث المشوقة في {title}",
        f"العالم الخاص بـ {title}", f"المشروع السينمائي {title}", f"الرواية البصرية لـ {title}", f"هذا العمل الذي يجمع النجوم في {title}",
        f"التفاصيل المخفية لـ {title}", f"رحلة الشخصيات في {title}", f"الصراع المثير في {title}", f"الإبداع الفني في {title}"
    ]
    
    ends = [
        "بترجمة احترافية ودقة عالية.", "وبصورة فائقة الجودة HD.", "الذي سيحبس أنفاسك بالتأكيد.", "في رحلة سينمائية لا تُنسى.",
        "مباشرة أون لاين على موقعنا.", "الآن على شاشتك وبسهولة تامة.", "بتقنيات حديثة تضمن لك أفضل رؤية.", "فقط وحصرياً هنا على توميتو.",
        "الذي طال انتظاره من قبل الملايين.", "الذي يعد بصمة جديدة في التصنيف.", "بكل تفاصيله المثيرة والغامضة.", "الذي يستحق أن تمنحه وقتك الكامل.",
        "بصيغ متعددة تتناسب مع جهازك.", "من البداية حتى النهاية المشوقة.", "الذي سيأخذك إلى عالم آخر من المتعة."
    ]
    
    # Outros (Closers)
    o_starts = [
        "في الختام، نتمنى لك", "نأمل أن تستمتع بمتابعة", "شكراً لاختيارك توميتو لمشاهدة", "كانت هذه لمحة بسيطة عن",
        "نعدك دائماً بالأفضل مع", "لا تنسى مشاركة رأيك حول", "نتمنى لك وقت ممتع مع", "إلى هنا تنتهي رحلتنا مع"
    ]
    o_ends = [
        "بأفضل جودة ممكنة.", "في انتظار آرائكم ومقترحاتكم.", "لا تفوت باقي أعمالنا الحصرية.", "نتمنى لك مشاهدة طيبة.",
        "تابع صفحتنا للمزيد من التحديثات.", "انتظروا المزيد من المفاجآت السينمائية.", "دائماً معكم في قلب الإثارة.", "بجودة أصلية وبدون تقطيع."
    ]

    intro = f"{random.choice(starts)} {random.choice(mids)} {random.choice(ends)}"
    outro = f"{random.choice(o_starts)} {title} {random.choice(o_ends)}"
    
    return intro, outro
