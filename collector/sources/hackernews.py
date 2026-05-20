"""Hacker News API source — covers AI, security, economy, tech."""

import httpx
from datetime import datetime, timezone
from categorizer import detect_domain

HN_API = "https://hacker-news.firebaseio.com/v0"


def fetch_hackernews() -> list[dict]:
    """Fetch top stories from HN, auto-detect domain."""
    try:
        client = httpx.Client(timeout=15)
        resp = client.get(f"{HN_API}/topstories.json")
        resp.raise_for_status()
        story_ids = resp.json()[:80]

        articles = []
        for sid in story_ids:
            try:
                item = client.get(f"{HN_API}/item/{sid}.json").json()
                if not item or item.get("type") != "story":
                    continue
                title = item.get("title", "")
                url = item.get("url", f"https://news.ycombinator.com/item?id={sid}")
                published = datetime.fromtimestamp(
                    item.get("time", 0), tz=timezone.utc
                ).isoformat()
                articles.append({
                    "title": title,
                    "url": url,
                    "source": "Hacker News",
                    "domain": "auto",
                    "published": published,
                    "content": f"{title}. Score: {item.get('score', 0)}, Comments: {item.get('descendants', 0)}",
                })
            except Exception:
                continue

        print(f"  [Hacker News] {len(articles)} stories")
        client.close()
        return articles
    except Exception as e:
        print(f"  [Hacker News] error: {e}")
        return []
