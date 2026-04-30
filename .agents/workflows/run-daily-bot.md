---
description: Generate 5 pages (movies + tv) every 30 minutes in a continuous loop
---

# Daily Bot — 5 Pages Every 30 Minutes

This workflow runs the content bot in a continuous loop, generating 5 new pages (≈2-3 movies + 2-3 tv shows) every 30 minutes, then pushing to GitHub.

> **Stop the loop**: Press `Ctrl+C` in the terminal to stop.

## Steps

// turbo
1. Start the bot loop (5 pages every 30 min):
```bash
cd /home/tomito/Desktop/tomitoback-e48be058bdb6595a0e6a7d8473c71c141a10fb91 && while true; do
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "🚀 [$(date '+%H:%M:%S')] Starting run: 5 pages..."
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  python3 daily_content.py --count 5
  echo ""
  echo "✅ Done. Waiting 30 minutes until next run..."
  echo "⏳ Next run at: $(date -d '+30 minutes' '+%H:%M:%S')"
  sleep 1800
done
```
