"""RSS feed sources for AI news."""

import feedparser
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

RSS_FEEDS = [
    # ── 中文 AI 新闻（高优先级） ──
    {"name": "量子位", "url": "https://www.qbitai.com/feed"},
    {"name": "雷锋网 AI", "url": "https://www.leiphone.com/feed/categoryRss/name/ai"},
    {"name": "机器之心", "url": "https://www.jiqizhixin.com/rss"},
    {"name": "36氪", "url": "https://36kr.com/feed", "ai_filter": True},
    {"name": "InfoQ 中文", "url": "https://www.infoq.cn/feed", "ai_filter": True},
    {"name": "虎嗅", "url": "https://rss.huxiu.com/", "ai_filter": True},
    {"name": "钛媒体", "url": "https://www.tmtpost.com/rss.xml", "ai_filter": True},
    {"name": "爱范儿", "url": "https://www.ifanr.com/feed", "ai_filter": True},
    {"name": "少数派", "url": "https://sspai.com/feed", "ai_filter": True},
    # ── 英文 AI 媒体 ──
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"name": "The Verge AI", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"},
    {"name": "The Decoder", "url": "https://the-decoder.com/feed/"},
    {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/"},
    {"name": "MIT Tech Review", "url": "https://www.technologyreview.com/feed/", "ai_filter": True},
    {"name": "Ars Technica AI", "url": "https://feeds.arstechnica.com/arstechnica/technology-lab", "ai_filter": True},
    {"name": "Wired AI", "url": "https://www.wired.com/feed/tag/ai/latest/rss"},
    {"name": "Bloomberg Tech", "url": "https://feeds.bloomberg.com/technology/news.rss", "ai_filter": True},
    {"name": "InfoQ AI", "url": "https://feed.infoq.com/ai-ml-data-eng/"},
    # ── 公司 / 实验室官方博客 ──
    {"name": "OpenAI Blog", "url": "https://openai.com/news/rss.xml"},
    {"name": "DeepMind Blog", "url": "https://deepmind.google/blog/rss.xml"},
    {"name": "Google AI Blog", "url": "https://blog.google/technology/ai/rss/"},
    {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "Microsoft AI Blog", "url": "https://blogs.microsoft.com/ai/feed/"},
    {"name": "Meta AI Blog", "url": "https://engineering.fb.com/category/ml-applications/feed/"},
    {"name": "AWS AI Blog", "url": "https://aws.amazon.com/blogs/ai/feed/"},
    {"name": "NVIDIA Blog", "url": "https://developer.nvidia.com/blog/feed", "ai_filter": True},
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
