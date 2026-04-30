import json
import os

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
INDEX_JSON = os.path.join(BASE_PATH, 'data', 'content_index.json')
SEARCH_JS = os.path.join(BASE_PATH, 'data', 'search_index.js')

def generate():
    if not os.path.exists(INDEX_JSON):
        print(f"Error: {INDEX_JSON} not found.")
        return

    with open(INDEX_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # We only need specific fields for search to keep the file size manageable
    # title, title_ar, title_en, folder, slug, poster
    # Note: the original index might already have these, but we ensure consistency.
    
    compact_data = []
    for item in data:
        compact_data.append({
            "title": item.get("title", ""),
            "title_ar": item.get("title_ar", ""),
            "title_en": item.get("title_en", ""),
            "folder": item.get("folder", "movie"),
            "slug": item.get("slug", ""),
            "poster": item.get("poster", "")
        })

    js_content = f"const FULL_INDEX = {json.dumps(compact_data, ensure_ascii=False)};"
    
    with open(SEARCH_JS, 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    print(f"✅ Generated {SEARCH_JS}")

if __name__ == '__main__':
    generate()
