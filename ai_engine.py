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
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyBR4yA0jCHdet9iv6XSZBS2wSDMJrFFt54").strip()

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

def ask_gemini(prompt):
    if not GEMINI_API_KEY:
        log.error("خطأ: GEMINI_API_KEY غير موجود!")
        return ""
    try:
        # Using Gemini 2.5 Flash (Authoritative model for this project)
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        r = requests.post(url, headers=headers, json=data, timeout=30)
        
        if r.status_code == 200:
            res = r.json()
            if 'candidates' in res and len(res['candidates']) > 0:
                text = res['candidates'][0]['content']['parts'][0]['text']
                # Clean up markdown if AI returns it
                text = re.sub(r'```json\s*|\s*```', '', text).strip()
                return text
            return ""
        else:
            log.warning(f"Gemini API Error: {r.status_code} - {r.text}")
            return ""
    except Exception as e:
        log.error(f"حدث خطأ أثناء الاتصال بـ Gemini: {e}")
        return ""

def get_rising_seo_tags(subject_name):
    """
    الدمج بين المواقع الشهيرة والكلمات النامية (Breakout) من PyTrends
    """
    try:
        from trends_fetcher import fetch_related_keywords
        # Fetching rising keywords (Breakout focus)
        rising_keywords = fetch_related_keywords(subject_name)
    except ImportError:
        rising_keywords = ""

    # القائمة الثابتة للمواقع (Fix Keywords)
    fixed_sites = "ايجي بست, شاهد, ماي سيما, EgyBest, Shahid, MyCima, Netflix, Canal+, Streaming, Watch online, Regarder en ligne"
    
    # دمج الكل
    all_keywords = f"{subject_name}, {fixed_sites}"
    if rising_keywords:
        all_keywords += f", {rising_keywords}"
    
    # تنظيف النص: إبقاء Ar, En, Fr فقط وحذف أي رموز غريبة
    cleaned_keywords = re.sub(r'[^a-zA-Z0-9\u0600-\u06FF\s,éèàçëêîôû]', '', all_keywords)
    # إزالة المسافات الزائدة
    cleaned_keywords = re.sub(r'\s+', ' ', cleaned_keywords).strip()
    
    return cleaned_keywords

def generate_meta_tags(title_ar, title_en, year, media_type='movie', *args, **kwargs):
    keywords = get_rising_seo_tags(title_ar)
    
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

def generate_bilingual_description(title_ar, title_en, overview_ar, overview_en, year, genres_ar, media_type, *args, **kwargs):
    """
    توليد محتوى SEO احترافي بـ 3 لغات باستخدام Gemini مع الحفاظ على القالبV7
    """
    prompt = f"""
    Act as an SEO expert for a movie streaming site called 'Tomito'. 
    Generate a JSON response for the {media_type} '{title_ar}' ({title_en}) released in {year}.
    
    Input Overviews:
    AR: {overview_ar}
    EN: {overview_en}
    
    Requirements:
    1. 'desc_ar': A long professional SEO description in Arabic (Ar). Use emotional and catchy language. Mention keywords like 'مشاهدة', 'تحميل', 'اون لاين'.
    2. 'desc_en': A professional SEO description in English (En).
    3. 'opinion': A catchy 'Tomito Opinion' in Arabic (one short paragraph) starting with something like 'رأي توميتو:'.
    4. 'seo_title_ar': A click-worthy title in Arabic (Ar) like 'مشاهدة [Title] مترجم اون لاين - توميتو'.
    5. 'meta_desc': A perfect meta description (max 155 chars) in Arabic.
    
    Return ONLY valid JSON.
    """
    
    ai_res = ask_gemini(prompt)
    try:
        data = json.loads(ai_res)
        return {
            "desc_ar": data.get("desc_ar", overview_ar),
            "desc_en": data.get("desc_en", overview_en),
            "opinion": data.get("opinion", ""),
            "seo_title_ar": data.get("seo_title_ar", f"مشاهدة {title_ar} مترجم اون لاين - توميتو"),
            "meta_desc": data.get("meta_desc", f"مشاهدة {title_ar} مترجم بجودة عالية."),
            "keywords": get_rising_seo_tags(title_ar)
        }
    except:
        log.warning("Failed to parse Gemini JSON output. Using fallbacks.")
        return {
            "desc_ar": overview_ar,
            "desc_en": overview_en,
            "opinion": f"تقييم توميتو: {title_ar} عمل يستحق المشاهدة.",
            "seo_title_ar": f"مشاهدة {title_ar} مترجم اون لاين - توميتو",
            "meta_desc": f"مشاهدة {title_ar} مترجم بجودة عالية.",
            "keywords": get_rising_seo_tags(title_ar)
        }

def generate_seo_content(title, overview, media_type, year, genres=[], *args, **kwargs):
    res = generate_bilingual_description(title, title, overview, overview, year, genres, media_type)
    
    if res:
        return {
            "seo_title": res["seo_title_ar"],
            "ai_description": res["desc_ar"],
            "meta_desc": res["meta_desc"],
            "keywords": res["keywords"]
        }
    return None

def generate_faq(title_ar, title_en, year, media_type):
    label = "الفيلم" if media_type == 'movie' else "المسلسل"
    return f"""
    <div class="faq-item">
        <div class="faq-question">أين يمكنني مشاهدة {label} {title_ar} مترجم؟</div>
        <div class="faq-answer">يمكنك مشاهدة {label} {title_ar} ({title_en}) مترجماً بالكامل بجودة عالية على توميتو (tomito.xyz) بدون إعلانات مزعجة.</div>
    </div>
    <div class="faq-item">
        <div class="faq-question">هل يتوفر تحميل {title_ar} بجودة HD؟</div>
        <div class="faq-answer">نعم، يوفر موقع توميتو روابط تحميل مباشرة لـ {title_ar} بمختلف الجودات (4K, 1080p, 720p) وبسيرفرات سريعة.</div>
    </div>
    """

def generate_tomito_opinion(title_ar, *args, **kwargs):
    return f"رأي توميتو: {title_ar} يقدم تجربة سينمائية فريدة تستحق المتابعة."

def generate_page_intro_outro(title_ar, title_en, year, genres_ar, media_type, desc_ar):
    label = "فيلم" if media_type == 'movie' else "مسلسل"
    intro = f"نقدم لكم اليوم {label} {title_ar} ({year})، واحد من أكثر الأعمال المطلوبة حالياً. استمتع بمشاهدة {title_en} مترجم حصرياً."
    outro = f"في الختام، نتمنى أن ينال {label} {title_ar} إعجابكم. لا تنسوا متابعة جديد الأفلام والمسلسلات على موقعكم توميتو."
    return intro, outro
