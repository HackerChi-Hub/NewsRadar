"""Hacker News API source for AI-related stories."""

import httpx
from datetime import datetime, timezone

HN_API = "https://hacker-news.firebaseio.com/v0"

AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "neural network", "llm", "large language model", "gpt", "openai",
    "anthropic", "claude", "gemini", "mistral", "llama", "transformer",
    "diffusion", "stable diffusion", "midjourney", "dall-e", "sora",
    "chatbot", "copilot", "agent", "rag", "fine-tuning",
    "nlp", "computer vision", "robotics", "autonomous",
    "deepseek", "nvidia", "cuda", "gpu", "tpu",
]


def _is_ai_related(title: str) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in AI_KEYWORDS)


def fetch_hackernews() -> list[dict]:
    """Fetch AI-related stories from Hacker News top stories."""
    try:
        client = httpx.Client(timeout=15)
        resp = client.get(f"{HN_API}/topstories.json")
        resp.raise_for_status()
        story_ids = resp.json()[:60]  # check top 60

        articles = []
        for sid in story_ids:
            try:
                item = client.get(f"{HN_API}/item/{sid}.json").json()
                if not item or item.get("type") != "story":
                    continue
                title = item.get("title", "")
                if not _is_ai_related(title):
                    continue
                url = item.get("url", f"https://news.ycombinator.com/item?id={sid}")
                published = datetime.fromtimestamp(
                    item.get("time", 0), tz=timezone.utc
                ).isoformat()
                articles.append({
                    "title": title,
                    "url": url,
                    "source": "Hacker News",
                    "published": published,
                    "content": f"{title}. Score: {item.get('score', 0)}, Comments: {item.get('descendants', 0)}",
                })
            except Exception:
                continue

        print(f"  [Hacker News] fetched {len(articles)} AI stories")
        client.close()
        return articles
    except Exception as e:
        print(f"  [Hacker News] error: {e}")
        return []
