"""AI summarizer: Gemini (primary) + Groq (fallback). Both free tier."""

import json
import re
import time
from datetime import datetime, timezone

import httpx

MAX_PER_RUN = 10
RATE_LIMIT_DELAY = 6

VALID_CATEGORIES = {"LLM", "CV", "机器人", "AI产品", "研究", "行业", "政策", "开源"}

PROMPT_TEMPLATE = (
    "You are an AI news analyst. Respond with ONLY a JSON object.\n\n"
    "Fields:\n"
    '- "title_zh": Chinese translation of the title (keep if already Chinese)\n'
    '- "summary_zh": 2-3 sentence summary in Chinese\n'
    '- "category": ONE of [LLM, CV, 机器人, AI产品, 研究, 行业, 政策, 开源]\n'
    '- "tags": 2-3 tags in Chinese\n\n'
    "Title: {title}\nContent: {content}\n\n"
    'JSON only: {{"title_zh":"...","summary_zh":"...","category":"...","tags":["..."]}}'
)


def _parse_json(text: str) -> dict:
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        text = match.group(1)
    text = text.strip()
    # Fix invalid unicode escapes from LLMs
    text = re.sub(r'\\u(?![0-9a-fA-F]{4})', r'\\\\u', text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try fixing common LLM JSON issues: trailing commas, single quotes
        text = re.sub(r',\s*([}\]])', r'\1', text)
        return json.loads(text)


def _call_gemini(api_key: str, prompt: str) -> dict:
    from google import genai
    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(model="gemini-2.5-flash-lite", contents=prompt)
    return _parse_json(resp.text)


def _call_groq(api_key: str, prompt: str) -> dict:
    resp = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": prompt}]},
        timeout=30,
    )
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"]
    return _parse_json(text)


def summarize_batch(articles: list[dict], gemini_key: str = "", groq_key: str = "") -> None:
    """Enhance articles in-place with AI summaries. Stops on quota hit."""
    for i, article in enumerate(articles):
        prompt = PROMPT_TEMPLATE.format(
            title=article.get("title", ""),
            content=article.get("content", article.get("summary_zh", ""))[:3000],
        )
        try:
            if groq_key:
                result = _call_groq(groq_key, prompt)
            elif gemini_key:
                result = _call_gemini(gemini_key, prompt)
            else:
                return

            cat = result.get("category", "")
            if cat in VALID_CATEGORIES:
                article["category"] = cat
            article["title_zh"] = result.get("title_zh", article.get("title_zh", ""))
            article["summary_zh"] = result.get("summary_zh", article.get("summary_zh", ""))
            article["tags"] = result.get("tags", [])[:5]
            print(f"  ✓ [{i+1}] {article['title'][:45]}...")

            if i < len(articles) - 1:
                time.sleep(RATE_LIMIT_DELAY)

        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print(f"  ✗ [{i+1}] Quota hit, stopping")
                return
            print(f"  ✗ [{i+1}] {e}")


DIGEST_PROMPT = """You are a senior AI news editor. Given these recent AI news articles, pick the 10 MOST important/impactful ones and write a brief Chinese digest.

Articles:
{articles_text}

Respond with ONLY a JSON object:
{{
  "items": [
    {{"rank": 1, "title": "中文标题", "summary": "一句话中文摘要（30字以内）", "id": "article_id"}},
    ...10 items
  ]
}}

Selection criteria: industry impact > technical breakthrough > product launch > funding. Prefer diverse categories. JSON only, no markdown."""


def generate_digest(articles: list[dict], gemini_key: str = "", groq_key: str = "") -> list[dict]:
    """Generate a top-10 digest from recent articles using LLM."""
    if not (groq_key or gemini_key):
        return []
    if len(articles) < 5:
        return []

    # Build article list for prompt (limit to 50 newest)
    candidates = articles[:50]
    lines = []
    for a in candidates:
        title = a.get("title_zh", a.get("title", ""))
        src = a.get("source", "")
        cat = a.get("category", "")
        lines.append(f'- [{a["id"]}] [{cat}] [{src}] {title}')

    prompt = DIGEST_PROMPT.format(articles_text="\n".join(lines))

    try:
        if groq_key:
            result = _call_groq(groq_key, prompt)
        elif gemini_key:
            result = _call_gemini(gemini_key, prompt)
        else:
            return []

        items = result.get("items", [])
        # Enrich with article data
        id_map = {a["id"]: a for a in candidates}
        digest = []
        for item in items[:10]:
            aid = item.get("id", "")
            article = id_map.get(aid, {})
            digest.append({
                "rank": item.get("rank", len(digest) + 1),
                "title": item.get("title", article.get("title_zh", "")),
                "summary": item.get("summary", ""),
                "url": article.get("url", ""),
                "source": article.get("source", ""),
                "category": article.get("category", ""),
            })
        print(f"  ✓ Digest generated: {len(digest)} items")
        return digest

    except Exception as e:
        print(f"  ✗ Digest failed: {e}")
        return []
