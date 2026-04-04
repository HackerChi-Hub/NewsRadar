"""AI summarizer using Google Gemini API (google-genai SDK)."""

import json
import re
import time
from datetime import datetime, timezone

from google import genai

MODEL = "gemini-2.5-flash-lite"
RATE_LIMIT_DELAY = 6
MAX_PER_RUN = 10  # Stay well under free tier limits per run


def _parse_json_response(text: str) -> dict:
    """Extract JSON from a potentially markdown-wrapped response."""
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        text = match.group(1)
    return json.loads(text.strip())


VALID_CATEGORIES = {"LLM", "CV", "机器人", "AI产品", "研究", "行业", "政策", "开源"}


def summarize_articles(articles: list[dict], api_key: str) -> list[dict]:
    """Summarize up to MAX_PER_RUN articles. Returns enriched articles.
    Remaining articles are returned without summary (to be processed in later runs)."""
    client = genai.Client(api_key=api_key)

    to_summarize = articles[:MAX_PER_RUN]
    skip = articles[MAX_PER_RUN:]

    print(f"  Will summarize {len(to_summarize)} of {len(articles)} (max {MAX_PER_RUN}/run, model: {MODEL})")

    enriched = []
    quota_hit = False

    for i, article in enumerate(to_summarize):
        if quota_hit:
            # Quota exhausted, save remaining without summary
            enriched.append(_fallback(article))
            continue

        try:
            prompt = (
                "You are an AI news analyst. Analyze this article and respond with ONLY a JSON object (no markdown).\n\n"
                "Required fields:\n"
                '- "title_zh": Chinese translation of the title (keep original if already Chinese)\n'
                '- "summary_zh": A concise 2-3 sentence summary in Chinese\n'
                f'- "category": ONE of [{", ".join(VALID_CATEGORIES)}]\n'
                '- "tags": 2-3 relevant tags in Chinese\n\n'
                f"Title: {article['title']}\n"
                f"Content: {article.get('content', '')[:3000]}\n\n"
                'Respond ONLY with JSON: {"title_zh": "...", "summary_zh": "...", "category": "...", "tags": ["..."]}'
            )

            response = client.models.generate_content(model=MODEL, contents=prompt)
            result = _parse_json_response(response.text)

            category = result.get("category", "未分类")
            if category not in VALID_CATEGORIES:
                category = "未分类"

            enriched.append({
                **{k: v for k, v in article.items() if k != "extra"},
                "title_zh": result.get("title_zh", article["title"]),
                "summary_zh": result.get("summary_zh", ""),
                "category": category,
                "tags": result.get("tags", [])[:5],
                "collected": datetime.now(timezone.utc).isoformat(),
            })
            print(f"  ✓ [{i+1}/{len(to_summarize)}] {article['title'][:50]}...")

            if i < len(to_summarize) - 1:
                time.sleep(RATE_LIMIT_DELAY)

        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                print(f"  ✗ [{i+1}/{len(to_summarize)}] Quota hit, stopping summarization")
                quota_hit = True
                enriched.append(_fallback(article))
            else:
                print(f"  ✗ [{i+1}/{len(to_summarize)}] Error: {e}")
                enriched.append(_fallback(article))

    # Remaining articles saved without summary
    for article in skip:
        enriched.append(_fallback(article))

    summarized = sum(1 for a in enriched if a["category"] != "未分类")
    print(f"  Result: {summarized} summarized, {len(enriched) - summarized} pending")

    return enriched


def _fallback(article: dict) -> dict:
    return {
        **{k: v for k, v in article.items() if k != "extra"},
        "title_zh": article["title"],
        "summary_zh": article.get("content", "")[:200],
        "category": "未分类",
        "tags": [],
        "collected": datetime.now(timezone.utc).isoformat(),
    }
