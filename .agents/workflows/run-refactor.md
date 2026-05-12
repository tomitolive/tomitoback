---
description: Run the global description refactor bot (100 pages), sync images, and update sitemap
---

1. Run the refactor bot for 100 pages.
// turbo
python3 refactor_descriptions.py --limit 100

2. Rebuild the homepage to reflect any changes.
// turbo
python3 build_homepage.py

3. Update the full sitemaps.
// turbo
python3 generate_full_sitemap.py

4. Stage and push all changes.
// turbo
git add . && git commit -m "chore: automated global refactor and asset sync" && git push origin main
