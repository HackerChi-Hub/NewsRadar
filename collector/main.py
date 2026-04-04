#!/usr/bin/env python3
"""NewsRadar collector - fetches AI news from multiple sources and generates summaries."""

import json
import hashlib
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

from sources import fetch_all_rss, fetch_hackernews, fetch_arxiv
from summarizer import summarize_articles

DATA_FILE = Path(__file__).parent.parent / "web" / "public" / "data" / "news.json"
MAX_AGE_DAYS = 7


def load_existing_data() -> dict:
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, KeyError):
            print("Warning: corrupted data file, starting fresh")
    return {"last_updated": "", "articles": []}


def article_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def main():
    print(f"=== NewsRadar Collector - {datetime.now(timezone.utc).isoformat()} ===\n")

    # Load existing data
    data = load_existing_data()
    existing_ids = {a["id"] for a in data["articles"]}
    print(f"Existing articles: {len(existing_ids)}\n")

    # Fetch from all sources
    raw_articles: list[dict] = []

    print("Fetching RSS feeds...")
    raw_articles.extend(fetch_all_rss())

    print("\nFetching Hacker News...")
    raw_articles.extend(fetch_hackernews())

    print("\nFetching arXiv papers...")
    raw_articles.extend(fetch_arxiv())

    print(f"\nTotal fetched: {len(raw_articles)}")

    # Deduplicate
    new_articles = []
    for article in raw_articles:
        aid = article_id(article["url"])
        if aid not in existing_ids:
            article["id"] = aid
            new_articles.append(article)
            existing_ids.add(aid)

    print(f"New articles: {len(new_articles)}\n")

    if not new_articles:
        print("No new articles found, exiting.")
        return

    # Summarize with AI
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if api_key:
        print(f"Summarizing {len(new_articles)} articles with Gemini...\n")
        enriched = summarize_articles(new_articles, api_key)
    else:
        print("No GEMINI_API_KEY set, saving articles without AI summary.\n")
        enriched = []
        for a in new_articles:
            enriched.append({
                **{k: v for k, v in a.items() if k != "extra"},
                "title_zh": a["title"],
                "summary_zh": a.get("content", "")[:200],
                "category": "未分类",
                "tags": [],
                "collected": datetime.now(timezone.utc).isoformat(),
            })

    # Merge with existing articles
    all_articles = enriched + data["articles"]

    # Prune articles older than MAX_AGE_DAYS
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
    before = len(all_articles)
    all_articles = [
        a for a in all_articles
        if _parse_date(a.get("published", "")) > cutoff
    ]
    pruned = before - len(all_articles)
    if pruned:
        print(f"Pruned {pruned} articles older than {MAX_AGE_DAYS} days")

    # Sort by published time (newest first)
    all_articles.sort(key=lambda a: a.get("published", ""), reverse=True)

    # Save
    output = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "articles": all_articles,
    }

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(all_articles)} articles to {DATA_FILE}")
    print("Done!")


def _parse_date(date_str: str) -> datetime:
    """Parse an ISO date string, returning epoch on failure."""
    try:
        dt = datetime.fromisoformat(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return datetime(1970, 1, 1, tzinfo=timezone.utc)


if __name__ == "__main__":
    main()
