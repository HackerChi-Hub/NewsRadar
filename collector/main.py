#!/usr/bin/env python3
"""NewsRadar collector - fetches AI news, categorizes, translates, and optionally summarizes."""

import json
import hashlib
import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

from sources import fetch_all_rss, fetch_hackernews, fetch_arxiv
from categorizer import categorize, detect_domain

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


def _is_chinese(text: str) -> bool:
    return any("\u4e00" <= c <= "\u9fff" for c in text)


def _translate_titles(articles: list[dict]) -> None:
    """Translate non-Chinese titles using Google Translate (free, no API key)."""
    to_translate = [a for a in articles if not _is_chinese(a.get("title", ""))]
    if not to_translate:
        return

    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source="auto", target="zh-CN")
    except ImportError:
        print("  deep-translator not installed, skipping translation")
        return

    print(f"  Translating {len(to_translate)} titles...")
    success = 0
    for a in to_translate:
        try:
            translated = translator.translate(a["title"][:500])
            if translated:
                a["title_zh"] = translated
                success += 1
        except Exception:
            pass  # Keep original title
    print(f"  Translated {success}/{len(to_translate)} titles")


def _enrich_article(article: dict) -> dict:
    """Add domain, category, title_zh, summary_zh using keyword matching."""
    title = article.get("title", "")
    content = article.get("content", "")
    raw_domain = article.get("domain", "auto")

    # Determine domain
    if raw_domain == "auto":
        domain = detect_domain(title, content)
    else:
        domain = raw_domain

    cat = categorize(title, content, domain)
    title_zh = article.get("title_zh", title)
    summary = re.sub(r"\s+", " ", content[:200]).strip()

    return {
        **{k: v for k, v in article.items() if k != "extra"},
        "title_zh": title_zh,
        "summary_zh": summary,
        "domain": domain,
        "category": cat,
        "tags": [],
        "collected": datetime.now(timezone.utc).isoformat(),
    }


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
        # Still try to AI-enhance old uncategorized articles
        _ai_enhance_old(data)
        _save(data)
        return

    # 1. Translate titles (free Google Translate, no API key)
    _translate_titles(new_articles)

    # 2. Keyword categorize + enrich all new articles (instant, no API)
    enriched = [_enrich_article(a) for a in new_articles]
    categorized = sum(1 for a in enriched if a["category"] != "未分类")
    print(f"Keyword categorized: {categorized}/{len(enriched)}\n")

    # Merge with existing articles
    all_articles = enriched + data["articles"]

    # Backfill: translate + re-categorize old articles
    _backfill_old(all_articles)

    # Prune old
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
    before = len(all_articles)
    all_articles = [a for a in all_articles if _parse_date(a.get("published", "")) > cutoff]
    pruned = before - len(all_articles)
    if pruned:
        print(f"Pruned {pruned} old articles")

    all_articles.sort(key=lambda a: a.get("published", ""), reverse=True)
    data["articles"] = all_articles

    # 3. AI tasks (Groq preferred, 14400 RPD free)
    api_key = os.environ.get("GEMINI_API_KEY", "")
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if api_key or groq_key:
        # Digest FIRST — most visible, only 1 API call
        from summarizer import generate_digest
        print("\nGenerating digest...")
        digest = generate_digest(all_articles, api_key, groq_key)
        if digest:
            data["digest"] = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "items": digest,
            }

        # Then enhance individual articles with remaining quota
        _ai_enhance(enriched, api_key, groq_key)

    _save(data)


BACKFILL_TRANSLATE_PER_RUN = 20


def _backfill_old(articles: list[dict]) -> None:
    """Translate untranslated old articles + re-categorize uncategorized ones."""
    # Find articles where title_zh == title and title is not Chinese (untranslated)
    untranslated = [
        a for a in articles
        if a.get("title_zh") == a.get("title") and not _is_chinese(a.get("title", ""))
    ]

    if untranslated:
        batch = untranslated[:BACKFILL_TRANSLATE_PER_RUN]
        try:
            from deep_translator import GoogleTranslator
            translator = GoogleTranslator(source="auto", target="zh-CN")
            import time as _time
            success = 0
            for a in batch:
                try:
                    translated = translator.translate(a["title"][:500])
                    if translated:
                        a["title_zh"] = translated
                        success += 1
                    _time.sleep(0.5)
                except Exception:
                    break  # Stop on error to avoid being blocked
            print(f"Backfill translated: {success}/{len(batch)} (remaining: {len(untranslated) - len(batch)})")
        except ImportError:
            pass

    # Re-categorize + detect domain for old articles
    recategorized = 0
    for a in articles:
        # Detect domain if missing
        if not a.get("domain") or a.get("domain") == "auto":
            a["domain"] = detect_domain(
                a.get("title", "") + " " + a.get("title_zh", ""),
                a.get("summary_zh", "") + " " + a.get("content", ""),
            )
        if a.get("category") == "未分类":
            new_cat = categorize(
                a.get("title", "") + " " + a.get("title_zh", ""),
                a.get("summary_zh", "") + " " + a.get("content", ""),
                a.get("domain", ""),
            )
            if new_cat != "未分类":
                a["category"] = new_cat
                recategorized += 1
    if recategorized:
        print(f"Backfill re-categorized: {recategorized}")


def _ai_enhance(articles: list[dict], gemini_key: str, groq_key: str) -> None:
    """Optional AI enhancement for better summaries (max 10/run)."""
    from summarizer import summarize_batch, MAX_PER_RUN
    to_enhance = articles[:MAX_PER_RUN]
    print(f"AI-enhancing {len(to_enhance)} articles...")
    summarize_batch(to_enhance, gemini_key, groq_key)


def _ai_enhance_old(data: dict) -> None:
    """Re-enhance old articles that lack good summaries."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if not (api_key or groq_key):
        return
    # Find articles with very short summaries (likely not AI-enhanced)
    candidates = [a for a in data["articles"] if len(a.get("summary_zh", "")) < 50][:5]
    if candidates:
        print(f"\nRe-enhancing {len(candidates)} old articles with short summaries...")
        from summarizer import summarize_batch
        summarize_batch(candidates, api_key, groq_key)


def _save(data: dict) -> None:
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(data['articles'])} articles")
    print("Done!")


def _parse_date(date_str: str) -> datetime:
    try:
        dt = datetime.fromisoformat(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return datetime(1970, 1, 1, tzinfo=timezone.utc)


if __name__ == "__main__":
    main()
