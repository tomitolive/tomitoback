import os
import requests
import json
import time
import random
import logging
import re

log = logging.getLogger(__name__)
API_KEY = os.environ.get("GROQ_API_KEY", "").strip()

# قائمة التصنيفات كما هي في كودك الأصلي
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
    {"name": "Disney", "id": 2, "label": "ديزني", "type": "collection"}
]

# --- التعديل الوحيد هنا لضبط الكيوردس ---
def get_targeted_keywords(title_ar, title_en, media_type, year):
    label = "فيلم" if media_type == 'movie' else "مسلسل"
    suffixes = ["مترجم", "اون لاين", "مشاهدة مباشرة", "بجودة عالية", "كامل HD", "ايجي بست", "watch online", "stream"]
    keywords = []
    for s in suffixes:
        keywords.append(f"{label} {title_ar} {s}")
        keywords.append(f"{title_en} {s}")
    keywords.append(f"مشاهدة {title_ar} على توميتو")
    keywords.append(f"tomito {title_en} {year}")
    selected = random.sample(keywords, min(len(keywords), 10))
    return ", ".join(selected)

def generate_meta_tags(title_ar, title_en, year, media_type='movie', *args, **kwargs):
    final_keywords = get_targeted_keywords(title_ar, title_en, media_type, year)
    label = "فيلم" if media_type == 'movie' else "مسلسل"
    meta_desc = f"مشاهدة {label} {title_ar} ({year}) مترجم بجودة عالية HD اون لاين حصرياً على توميتو (tomito.xyz)."
    return {"meta_desc": meta_desc, "keywords": final_keywords}
# ---------------------------------------

def ask_groq(prompt):
    if not API_KEY: return ""
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        data = {
            "model": "llama3-8b-8192",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        r = requests.post(url, headers=headers, json=data, timeout=10)
        return r.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        log.error(f"Groq Error: {e}")
        return ""

def generate_bilingual_description(title_ar, title_en, overview, *args, **kwargs):
    # كود الترجمة والوصف كما هو
    prompt = f"Write a professional Arabic SEO description for the movie/series {title_ar}. Summary: {overview}"
    desc_ar = ask_groq(prompt) or overview
    return {
        "desc_ar": desc_ar,
        "seo_title_ar": f"مشاهدة {title_ar} مترجم اون لاين - توميتو",
        "meta_desc": f"مشاهدة {title_ar} مترجم بجودة عالية.",
        "keywords": "" # سيتم تعويضه بـ generate_meta_tags
    }

def generate_seo_content(title, overview, media_type, year, genres=[], *args, **kwargs):
    res = generate_bilingual_description(title, title, overview)
    tags = generate_meta_tags(title, title, year, media_type)
    if res:
        return {
            "seo_title": f"مشاهدة {title} ({year}) مترجم HD - توميتو",
            "ai_description": res["desc_ar"],
            "meta_desc": tags["meta_desc"],
            "keywords": tags["keywords"]
        }
    return None

def generate_faq(title_ar, *args, **kwargs):
    return f'<div class="faq-item"><h4>أين يمكنني مشاهدة {title_ar}؟</h4><p>يمكنك مشاهدته بجودة عالية على توميتو.</p></div>'

def generate_tomito_opinion(title_ar, *args, **kwargs):
    return f"تقييم توميتو: {title_ar} عمل يستحق المشاهدة."

def generate_page_intro_outro(title, media_type, year, *args, **kwargs):
    label = "فيلم" if media_type == 'movie' else "مسلسل"
    return {
        "intro": f"نقدم لكم اليوم مشاهدة {label} {title}...",
        "outro": f"نتمنى أن تنال مشاهدة {title} إعجابكم."
    }

def get_live_trends(query, geo):
    # معطلة لضمان جودة الكيووردس
    return ""
