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
    return json.loads(text.strip())


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
