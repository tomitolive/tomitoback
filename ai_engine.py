import os
import requests
import json
import time
import random
import logging
import re

# إعداد اللوغز باش تعرف فين كاين المشكل بلا ما يوقف السكريبت
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# تأكد بلي الـ API KEY محطوط في السيرفر أو تيرموكس
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

def ask_groq(prompt):
    if not API_KEY: 
        log.error("خطأ: GROQ_API_KEY غير موجود!")
        return ""
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        data = {
            "model": "llama3-8b-8192",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        # زدنا Timeout لـ 15 ثانية باش نتفاداو بطء السيرفر
        r = requests.post(url, headers=headers, json=data, timeout=15)
        
        if r.status_code == 200:
            return r.json()['choices'][0]['message']['content'].strip()
        else:
            log.warning(f"Groq API Error: {r.status_code}")
            return ""
    except Exception as e:
        log.error(f"حدث خطأ أثناء الاتصال بـ Groq: {e}")
        return ""

def get_live_trends(query, geo='AR'):
    """
    إصلاح مشكلة الكيووردس: نركز فقط على كلمات البحث الخاصة بالأفلام
    """
    suffixes = ["مترجم", "اون لاين", "مشاهدة مباشرة", "بجودة عالية", "كامل HD", "تحميل", "tomito", "ايجي بست"]
    targeted_keywords = [f"{query} {s}" for s in suffixes]
    # اختيار 5 كلمات عشوائية
    return ", ".join(random.sample(targeted_keywords, min(len(targeted_keywords), 5)))

def generate_meta_tags(title_ar, title_en, year, media_type='movie', *args, **kwargs):
    # جلب كلمات دلالية نقية
    keywords = get_live_trends(title_ar)
    
    label = "فيلم" if media_type == 'movie' else "مسلسل"
    if media_type == 'tv': label = "برنامج"
    
    meta_desc = (
        f"مشاهدة {label} {title_ar} ({year}) مترجم بجودة عالية HD اون لاين "
        f"حصرياً على توميتو (tomito.xyz). استمتع بمتابعة {title_en}."
    )
    
    return {
        "meta_desc": meta_desc,
        "keywords": keywords
    }

def generate_bilingual_description(title_ar, title_en, overview, *args, **kwargs):
    prompt = f"Write a professional Arabic SEO description for the movie/series {title_ar}. Summary: {overview}"
    desc_ar = ask_groq(prompt)
    
    # إذا فشل AI، نستخدم الـ Overview الأصلي كـ Backup
    final_desc = desc_ar if desc_ar else overview
    
    return {
        "desc_ar": final_desc,
        "seo_title_ar": f"مشاهدة {title_ar} مترجم اون لاين - توميتو",
        "meta_desc": f"مشاهدة {title_ar} مترجم بجودة عالية.",
        "keywords": ""
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
    return f'<div class="faq-item"><h4>أين يمكنني مشاهدة {title_ar}؟</h4><p>على موقع توميتو بجودة عالية.</p></div>'

def generate_tomito_opinion(title_ar, *args, **kwargs):
    return f"تقييم توميتو: {title_ar} عمل يستحق المشاهدة."

def generate_page_intro_outro(title, media_type, year, *args, **kwargs):
    label = "فيلم" if media_type == 'movie' else "مسلسل"
    return {
        "intro": f"نقدم لكم مشاهدة {label} {title} ({year}) مترجم...",
        "outro": f"نتمنى أن تنال مشاهدة {title} إعجابكم."
    }
