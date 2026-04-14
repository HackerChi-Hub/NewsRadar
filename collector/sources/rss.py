"""RSS feed sources for news across domains."""

import feedparser
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

RSS_FEEDS = [
    # ══════════════════════════════════════════════════
    # 🤖 AI — 中文
    # ══════════════════════════════════════════════════
    {"name": "量子位", "url": "https://www.qbitai.com/feed", "domain": "AI"},
    {"name": "雷锋网 AI", "url": "https://www.leiphone.com/feed/categoryRss/name/ai", "domain": "AI"},
    {"name": "机器之心", "url": "https://www.jiqizhixin.com/rss", "domain": "AI"},
    # 🤖 AI — 英文媒体
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "domain": "AI"},
    {"name": "The Verge AI", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "domain": "AI"},
    {"name": "The Decoder", "url": "https://the-decoder.com/feed/", "domain": "AI"},
    {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/", "domain": "AI"},
    {"name": "Wired AI", "url": "https://www.wired.com/feed/tag/ai/latest/rss", "domain": "AI"},
    {"name": "InfoQ AI", "url": "https://feed.infoq.com/ai-ml-data-eng/", "domain": "AI"},
    # 🤖 AI — 公司博客
    {"name": "OpenAI Blog", "url": "https://openai.com/news/rss.xml", "domain": "AI"},
    {"name": "DeepMind Blog", "url": "https://deepmind.google/blog/rss.xml", "domain": "AI"},
    {"name": "Google AI Blog", "url": "https://blog.google/technology/ai/rss/", "domain": "AI"},
    {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/feed.xml", "domain": "AI"},
    {"name": "Microsoft AI Blog", "url": "https://blogs.microsoft.com/ai/feed/", "domain": "AI"},
    {"name": "Meta AI Blog", "url": "https://engineering.fb.com/category/ml-applications/feed/", "domain": "AI"},
    {"name": "AWS AI Blog", "url": "https://aws.amazon.com/blogs/ai/feed/", "domain": "AI"},

    # ══════════════════════════════════════════════════
    # 🔒 安全
    # ══════════════════════════════════════════════════
    {"name": "The Hacker News", "url": "https://feeds.feedburner.com/TheHackersNews", "domain": "安全"},
    {"name": "BleepingComputer", "url": "https://www.bleepingcomputer.com/feed/", "domain": "安全"},
    {"name": "Krebs on Security", "url": "https://krebsonsecurity.com/feed/", "domain": "安全"},
    {"name": "SecurityWeek", "url": "https://www.securityweek.com/feed/", "domain": "安全"},
    {"name": "FreeBuf", "url": "https://www.freebuf.com/feed", "domain": "安全"},
    {"name": "嘶吼", "url": "https://www.4hou.com/feed", "domain": "安全"},

    # ══════════════════════════════════════════════════
    # 💰 经济
    # ══════════════════════════════════════════════════
    {"name": "Bloomberg Markets", "url": "https://feeds.bloomberg.com/markets/news.rss", "domain": "经济"},
    {"name": "CNBC", "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html", "domain": "经济"},
    {"name": "Reuters Business", "url": "https://www.reutersagency.com/feed/", "domain": "经济"},

    # ══════════════════════════════════════════════════
    # 💻 科技（综合）
    # ══════════════════════════════════════════════════
    {"name": "Engadget", "url": "https://www.engadget.com/rss.xml", "domain": "科技"},
    {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index", "domain": "科技"},
    {"name": "MIT Tech Review", "url": "https://www.technologyreview.com/feed/", "domain": "科技"},
    {"name": "NVIDIA Blog", "url": "https://developer.nvidia.com/blog/feed", "domain": "科技", "ai_filter": False},
    {"name": "IT之家", "url": "https://www.ithome.com/rss/", "domain": "科技"},

    # ══════════════════════════════════════════════════
    # 🌍 国际
    # ══════════════════════════════════════════════════
    {"name": "UN News", "url": "https://news.un.org/feed/subscribe/en/news/all/rss.xml", "domain": "国际"},
    {"name": "BBC World", "url": "https://feeds.bbci.co.uk/news/world/rss.xml", "domain": "国际"},
    {"name": "NPR World", "url": "https://feeds.npr.org/1004/rss.xml", "domain": "国际"},
    {"name": "Reuters World", "url": "https://www.reutersagency.com/feed/", "domain": "国际"},
    {"name": "NASA", "url": "https://www.nasa.gov/feed/", "domain": "国际"},
    {"name": "新华网", "url": "http://www.news.cn/rss/english.xml", "domain": "国际"},
    {"name": "环球时报", "url": "https://www.globaltimes.cn/rss/outbrain.xml", "domain": "国际"},

    # ══════════════════════════════════════════════════
    # 🌐 综合（按关键词自动分域）
    # ══════════════════════════════════════════════════
    # {"name": "36氪", "url": "https://36kr.com/feed", "domain": "auto"},  # DISABLED — 聚合源
    # {"name": "InfoQ 中文", "url": "https://www.infoq.cn/feed", "domain": "auto"},  # DISABLED — 聚合/翻译源
    # {"name": "虎嗅", "url": "https://rss.huxiu.com/", "domain": "auto"},  # DISABLED — 聚合源，摘要质量差
    # {"name": "钛媒体", "url": "https://www.tmtpost.com/rss.xml", "domain": "auto"},  # DISABLED — 聚合源
    # {"name": "爱范儿", "url": "https://www.ifanr.com/feed", "domain": "auto"},  # DISABLED — 聚合源
    # {"name": "少数派", "url": "https://sspai.com/feed", "domain": "auto"},  # DISABLED — 聚合源
    {"name": "Bloomberg Tech", "url": "https://feeds.bloomberg.com/technology/news.rss", "domain": "auto"},
]


def _parse_date(entry) -> str:
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
    import re
    clean = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", clean).strip()


def fetch_rss(feed_info: dict) -> list[dict]:
    try:
        feed = feedparser.parse(feed_info["url"])
        articles = []
        for entry in feed.entries[:20]:
            title = entry.get("title", "")
            summary = _strip_html(entry.get("summary", "") or entry.get("description", ""))

            articles.append({
                "title": title,
                "url": entry.get("link", ""),
                "source": feed_info["name"],
                "domain": feed_info.get("domain", "auto"),
                "published": _parse_date(entry),
                "content": summary[:2000],
            })
        print(f"  [{feed_info['name']}] {len(articles)}")
        return articles
    except Exception as e:
        print(f"  [{feed_info['name']}] error: {e}")
        return []


def fetch_all_rss() -> list[dict]:
    articles = []
    for feed_info in RSS_FEEDS:
        articles.extend(fetch_rss(feed_info))
    return articles
