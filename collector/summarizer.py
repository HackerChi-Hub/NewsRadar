"""AI summarizer using Google Gemini API (google-genai SDK)."""

import json
import re
import time
from datetime import datetime, timezone

from google import genai

MODELS = ["gemini-2.5-flash-lite", "gemini-2.0-flash-lite", "gemini-1.5-flash"]
RATE_LIMIT_DELAY = 4


def _parse_json_response(text: str) -> dict:
    """Extract JSON from a potentially markdown-wrapped response."""
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        text = match.group(1)
    return json.loads(text.strip())


VALID_CATEGORIES = {"LLM", "CV", "机器人", "AI产品", "研究", "行业", "政策", "开源"}


def _call_gemini(client, prompt: str) -> dict:
    """Try each model in MODELS list until one works."""
    last_err = None
    for model in MODELS:
        try:
            response = client.models.generate_content(model=model, contents=prompt)
            return _parse_json_response(response.text)
        except Exception as e:
            last_err = e
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                print(f"    Model {model} quota exhausted, trying next...")
                continue
            raise
    raise last_err  # type: ignore[misc]


def summarize_articles(articles: list[dict], api_key: str) -> list[dict]:
    """Summarize articles using Gemini API. Returns enriched articles."""
    client = genai.Client(api_key=api_key)
    print(f"  Models priority: {MODELS}")

    enriched = []
    for i, article in enumerate(articles):
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

            result = _call_gemini(client, prompt)

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
            print(f"  [{i+1}/{len(articles)}] {article['title'][:50]}...")

            if i < len(articles) - 1:
                time.sleep(RATE_LIMIT_DELAY)

        except Exception as e:
            print(f"  [{i+1}/{len(articles)}] Error: {e} - saving without summary")
            enriched.append({
                **{k: v for k, v in article.items() if k != "extra"},
                "title_zh": article["title"],
                "summary_zh": article.get("content", "")[:200],
                "category": "未分类",
                "tags": [],
                "collected": datetime.now(timezone.utc).isoformat(),
            })

    return enriched
