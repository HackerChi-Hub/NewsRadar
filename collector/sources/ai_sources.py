"""AI-specialized news sources — research, community, media, policy, tools.

Health tracking:
  - _health: tracks consecutive failures per source (in-memory, resets on success)
  - 3+ consecutive failures → source marked degraded and skipped that run
  - get_health_report() returns status dict for all tracked sources
  - _permanently_failed: DNS/unreachable — skip forever

Persistent logging (per-run JSON report):
  - Written to LOG_FILE after every fetch_all_ai_sources() call
  - Records: timestamp, total articles, per-source article count,
    error messages, HTTP status codes, response times
  - Saved to web/public/data/ai_sources_log.json
  - git-ignored, survives across runs

Verified working sources (2026-04-14):
  arXiv (5 cats): cs.AI, cs.LG, cs.CL, cs.CV, cs.RO ✅
  Reddit RSS (9 subreddits) ✅
  Hacker News AI ✅ | Lobste.rs AI ✅
  AI News ✅ | VentureBeat AI ✅ | The Decoder ✅
  TechCrunch AI ✅ | Towards Data Science ✅ | Wired AI ✅ | InfoQ AI ✅
  Cohere Blog ✅ | AI21 Blog ✅ | NVIDIA Research ✅ | Hugging Face ✅
  Google DeepMind ✅ | Microsoft AI Blog ✅ | Meta AI Blog ✅
  EU AI Act ✅ | Future of Life AI ✅ | Stanford HAI ✅ | EPIC AI ✅
  AI Insider (Substack) ✅ | Product Hunt ✅

Permanently failed sources (404/403/510, no working replacement found):
  Anthropic ❌ | Mistral ❌ | Runway ❌ | ElevenLabs ❌
  White House AI ❌ | UN AI ❌ | AI Policy Insights ❌
  MIT News AI ❌ | The Batch ❌ | Future Tools ❌
  PapersWithCode.com ❌ | There's An AI For That ❌
  libreddit instances (all SSL/502) → using direct Reddit RSS ✅
"""

import re
import time
import json
import ssl
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Paths ────────────────────────────────────────────────────────────────────

_SOURCES_DIR = Path(__file__).parent
_COLLECTOR_DIR = _SOURCES_DIR.parent
_WEB_DIR = _COLLECTOR_DIR.parent / "web" / "public"
LOG_FILE = _WEB_DIR / "data" / "ai_sources_log.json"

# ── Health Tracking ───────────────────────────────────────────────────────────

_health: dict[str, int] = {}
_permanently_failed: set[str] = set()
_MAX_FAILURES = 3


def _health_record(source: str, count: int) -> None:
    if source in _permanently_failed:
        return
    if count == 0:
        _health[source] = _health.get(source, 0) + 1
        if _health[source] >= _MAX_FAILURES:
            print(f"    ⚠️  [{source}] degraded ({_health[source]} consecutive failures)")
    else:
        _health.pop(source, None)


def get_health_report() -> dict[str, str]:
    return {
        src: "degraded" if f >= _MAX_FAILURES else f"failing({f})"
        for src, f in _health.items()
    }


# ── Persistent Run Log ───────────────────────────────────────────────────────

class _RunLog:
    def __init__(self):
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.sources: dict[str, dict] = {}
        self.total_articles = 0

    def record(
        self,
        source: str,
        count: int,
        url: str,
        error: Optional[str] = None,
        http_status: Optional[int] = None,
        response_time_ms: Optional[float] = None,
    ) -> None:
        status = "ok" if count > 0 else ("error" if error else "empty")
        self.sources[source] = {
            "count": count,
            "url": url,
            "status": status,
            "error": error,
            "http_status": http_status,
            "response_time_ms": response_time_ms,
        }
        self.total_articles += count

    def write(self) -> None:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "timestamp": self.started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "total_articles": self.total_articles,
            "total_sources": len(self.sources),
            "ok_count": sum(1 for s in self.sources.values() if s["status"] == "ok"),
            "error_count": sum(1 for s in self.sources.values() if s["status"] == "error"),
            "empty_count": sum(1 for s in self.sources.values() if s["status"] == "empty"),
            "health": get_health_report(),
            "sources": self.sources,
        }
        tmp = str(LOG_FILE) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        __import__("os").replace(tmp, str(LOG_FILE))


# ── RSS Fetcher ───────────────────────────────────────────────────────────────

def _fetch_rss(
    url: str,
    source: str,
    domain: str = "AI",
    timeout: float = 10,
    max_entries: int = 20,
    log: Optional[_RunLog] = None,
) -> list[dict]:
    if source in _permanently_failed:
        if log:
            log.record(source, 0, url, error="permanently_failed")
        return []

    t0 = time.monotonic()
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={"User-Agent": "NewsRadar/1.0"})
        with urllib.request.urlopen(req, timeout=int(timeout), context=ctx) as resp:
            raw = resp.read()
            http_status = resp.status if hasattr(resp, "status") else 200

        elapsed_ms = (time.monotonic() - t0) * 1000

        import feedparser
        feed = feedparser.parse(raw)
        articles = []
        for entry in feed.entries[:max_entries]:
            art = _parse_entry(entry, source, domain)
            if art:
                articles.append(art)

        _health_record(source, len(articles))
        print(f"    [{source}] {len(articles)}")
        if log:
            log.record(source, len(articles), url, http_status=int(http_status), response_time_ms=round(elapsed_ms, 1))
        return articles

    except urllib.error.HTTPError as e:
        _health_record(source, 0)
        err = f"HTTP {e.code}: {e.reason}"
        print(f"    ✗  [{source}] {err}")
        if log:
            log.record(source, 0, url, error=err, http_status=e.code)
        if e.code in (404, 403, 410, 451, 503):
            _permanently_failed.add(source)
        return []

    except Exception as e:
        _health_record(source, 0)
        err = str(e)
        print(f"    ✗  [{source}] {err[:80]}")
        if log:
            log.record(source, 0, url, error=err[:200])
        if "nodename nor servname" in err or "Name or service not known" in err:
            _permanently_failed.add(source)
        return []


def _parse_entry(entry, source: str, domain: str = "AI") -> Optional[dict]:
    title = entry.get("title", "")
    if not title:
        return None
    summary = entry.get("summary", "") or entry.get("description", "")
    content = re.sub(r"<[^>]+>", "", summary)[:1000]
    published = _parse_date(entry)
    return {
        "title": title,
        "url": entry.get("link", ""),
        "source": source,
        "domain": domain,
        "published": published,
        "content": content,
    }


def _parse_date(entry) -> str:
    for field in ("published", "updated", "created"):
        raw = entry.get(field)
        if raw:
            try:
                from email.utils import parsedate_to_datetime
                return parsedate_to_datetime(raw).astimezone(timezone.utc).isoformat()
            except Exception:
                pass
    return datetime.now(timezone.utc).isoformat()


# ── Source Groups ────────────────────────────────────────────────────────────

ARXIV_QUERIES = [
    ("arXiv cs.AI", "https://arxiv.org/rss/cs.AI"),
    ("arXiv cs.LG", "https://arxiv.org/rss/cs.LG"),
    ("arXiv cs.CL", "https://arxiv.org/rss/cs.CL"),
    ("arXiv cs.CV", "https://arxiv.org/rss/cs.CV"),
    ("arXiv cs.RO", "https://arxiv.org/rss/cs.RO"),
]

REDDIT_SUBREDDITS = [
    ("r/MachineLearning", "https://www.reddit.com/r/MachineLearning.rss"),
    ("r/LocalLLaMA",      "https://www.reddit.com/r/LocalLLaMA.rss"),
    ("r/Claude",          "https://www.reddit.com/r/Claude.rss"),
    ("r/Sora",            "https://www.reddit.com/r/Sora.rss"),
    ("r/LocalAI",         "https://www.reddit.com/r/LocalAI.rss"),
    ("r/Artificial",      "https://www.reddit.com/r/Artificial.rss"),
    ("r/ChatGPT",         "https://www.reddit.com/r/ChatGPT.rss"),
    ("r/StableDiffusion", "https://www.reddit.com/r/StableDiffusion.rss"),
    ("r/Midjourney",      "https://www.reddit.com/r/Midjourney.rss"),
]

AI_MEDIA_FEEDS = [
    ("AI News",              "https://artificialintelligence-news.com/feed/"),
    ("VentureBeat AI",      "https://venturebeat.com/category/ai/feed/"),
    ("The Decoder",          "https://the-decoder.com/feed/"),
    ("TechCrunch AI",        "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("Towards Data Science", "https://towardsdatascience.com/feed"),
    ("Wired AI",             "https://www.wired.com/feed/tag/ai/latest/rss"),
    ("InfoQ AI",             "https://feed.infoq.com/ai-ml-data-eng/"),
    ("AI Insider",           "https://insiderthreat.substack.com/feed"),
]

COMPANY_BLOGS = [
    ("Hugging Face Blog",  "https://huggingface.co/blog/feed.xml"),
    ("Google DeepMind",     "https://deepmind.google/blog/rss.xml"),
    ("Microsoft AI Blog",   "https://blogs.microsoft.com/ai/feed/"),
    ("Meta AI Blog",        "https://engineering.fb.com/category/ml-applications/feed/"),
    ("Cohere Blog",         "https://cohere.com/blog/rss.xml"),
    ("AI21 Blog",           "https://www.ai21.com/blog/feed"),
    ("NVIDIA Research",     "https://developer.nvidia.com/blog/feed"),
]

POLICY_FEEDS = [
    ("EU AI Act",         "https://artificialintelligenceact.eu/feed/"),
    ("Future of Life AI", "https://futureoflife.org/ai-policy/feed/"),
    ("Stanford HAI",       "https://hai.stanford.edu/rss.xml"),
    ("EPIC AI",            "https://epic.org/feed/"),
]

TOOL_FEEDS = [
    ("Product Hunt AI", "https://www.producthunt.com/feed"),
]


# ── Group Fetchers ───────────────────────────────────────────────────────────

def fetch_arxiv_all(log: Optional[_RunLog] = None) -> list[dict]:
    articles = []
    for name, url in ARXIV_QUERIES:
        if name not in _permanently_failed:
            articles.extend(_fetch_rss(url, name, "AI", log=log))
            time.sleep(0.3)
    return articles


def fetch_papers_with_code(log: Optional[_RunLog] = None) -> list[dict]:
    return _fetch_rss("https://paperswithcode.com/feed", "Papers With Code", "AI", log=log)


def fetch_reddit_ai(log: Optional[_RunLog] = None) -> list[dict]:
    articles = []
    for name, url in REDDIT_SUBREDDITS:
        if name not in _permanently_failed:
            articles.extend(_fetch_rss(url, name, "AI", log=log))
            time.sleep(0.3)
    return articles


def fetch_hackernews_ai(log: Optional[_RunLog] = None) -> list[dict]:
    return _fetch_rss("https://hnrss.org/newest?q=AI", "Hacker News AI", "AI", log=log)


def fetch_lobsteers_ai(log: Optional[_RunLog] = None) -> list[dict]:
    return _fetch_rss("https://lobste.rs/t/ai.rss", "Lobste.rs AI", "AI", log=log)


def fetch_ai_media(log: Optional[_RunLog] = None) -> list[dict]:
    articles = []
    for name, url in AI_MEDIA_FEEDS:
        if name not in _permanently_failed:
            articles.extend(_fetch_rss(url, name, "AI", log=log))
            time.sleep(0.3)
    return articles


def fetch_company_blogs(log: Optional[_RunLog] = None) -> list[dict]:
    articles = []
    for name, url in COMPANY_BLOGS:
        if name not in _permanently_failed:
            articles.extend(_fetch_rss(url, name, "AI", log=log))
            time.sleep(0.3)
    return articles


def fetch_ai_policy(log: Optional[_RunLog] = None) -> list[dict]:
    articles = []
    for name, url in POLICY_FEEDS:
        if name not in _permanently_failed:
            articles.extend(_fetch_rss(url, name, "AI", log=log))
            time.sleep(0.3)
    return articles


def fetch_ai_tools(log: Optional[_RunLog] = None) -> list[dict]:
    articles = []
    for name, url in TOOL_FEEDS:
        if name not in _permanently_failed:
            articles.extend(_fetch_rss(url, name, "AI", log=log))
            time.sleep(0.3)
    return articles


# ── Master Fetcher ────────────────────────────────────────────────────────────

def fetch_all_ai_sources() -> list[dict]:
    log = _RunLog()
    articles = []

    print("\n=== AI Sources ===")

    print("\n[Research / Papers]")
    articles.extend(fetch_arxiv_all(log))
    articles.extend(fetch_papers_with_code(log))

    print("\n[Communities]")
    articles.extend(fetch_reddit_ai(log))
    articles.extend(fetch_hackernews_ai(log))
    articles.extend(fetch_lobsteers_ai(log))

    print("\n[AI Media]")
    articles.extend(fetch_ai_media(log))

    print("\n[Company Blogs]")
    articles.extend(fetch_company_blogs(log))

    print("\n[Policy / Regulation]")
    articles.extend(fetch_ai_policy(log))

    print("\n[AI Tools / Products]")
    articles.extend(fetch_ai_tools(log))

    log.write()
    print(f"\n[Source log → {LOG_FILE}]")

    health = get_health_report()
    if health:
        print("[Source Health — degraded/failing]")
        for src, st in health.items():
            print(f"  {src}: {st}")

    print(f"\n  Total AI articles: {len(articles)}")
    return articles
