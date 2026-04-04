"""RSS feed sources for AI news."""

import feedparser
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

RSS_FEEDS = [
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
    },
    {
        "name": "The Verge AI",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    },
    {
        "name": "MIT Tech Review",
        "url": "https://www.technologyreview.com/feed/",
        "ai_filter": True,
    },
    {
        "name": "VentureBeat AI",
        "url": "https://venturebeat.com/category/ai/feed/",
    },
    {
        "name": "Ars Technica AI",
        "url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
        "ai_filter": True,
    },
    {
        "name": "机器之心",
        "url": "https://www.jiqizhixin.com/rss",
    },
]

AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "neural", "llm", "large language model", "gpt", "openai", "anthropic",
    "claude", "gemini", "mistral", "llama", "transformer", "diffusion",
    "chatbot", "copilot", "agent", "rag", "nlp", "computer vision",
    "robotics", "deepseek", "nvidia", "cuda", "gpu",
    "人工智能", "大模型", "机器学习", "深度学习", "语言模型",
]


def _is_ai_related(title: str, summary: str = "") -> bool:
    text = (title + " " + summary).lower()
    return any(kw in text for kw in AI_KEYWORDS)


def _parse_date(entry) -> str:
    """Extract published date from a feed entry."""
    for field in ("published", "updated", "created"):
        raw = entry.get(field)
        if raw:
            try:
                dt = parsedate_to_datetime(raw)
                return dt.astimezone(timezone.utc).isoformat()
            except Exception:
                pass
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            return dt.isoformat()
        except Exception:
            pass
    return datetime.now(timezone.utc).isoformat()


def _strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    import re
    clean = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", clean).strip()


def fetch_rss(feed_info: dict) -> list[dict]:
    """Fetch articles from a single RSS feed."""
    try:
        feed = feedparser.parse(feed_info["url"])
        articles = []
        for entry in feed.entries[:20]:
            title = entry.get("title", "")
            summary = _strip_html(entry.get("summary", "") or entry.get("description", ""))

            if feed_info.get("ai_filter") and not _is_ai_related(title, summary):
                continue

            articles.append({
                "title": title,
                "url": entry.get("link", ""),
                "source": feed_info["name"],
                "published": _parse_date(entry),
                "content": summary[:2000],
            })
        print(f"  [{feed_info['name']}] fetched {len(articles)} articles")
        return articles
    except Exception as e:
        print(f"  [{feed_info['name']}] error: {e}")
        return []


def fetch_all_rss() -> list[dict]:
    """Fetch articles from all RSS feeds."""
    articles = []
    for feed_info in RSS_FEEDS:
        articles.extend(fetch_rss(feed_info))
    return articles
