"""AI summarizer: Gemini (primary) + Groq (fallback). Both free tier."""

import json
import re
import time
from datetime import datetime, timezone

import httpx

MAX_PER_RUN = 10
RATE_LIMIT_DELAY = 4  # seconds between calls (TPM-safe for both providers)

VALID_CATEGORIES = {"LLM", "CV", "机器人", "AI产品", "研究", "行业", "政策", "开源"}

PROMPT_TEMPLATE = (
    "You are an AI news analyst. Respond with ONLY a JSON object.\n\n"
    "Fields:\n"
    '- "title_zh": Chinese translation of the title (keep if already Chinese)\n'
    '- "summary_zh": 2-3 sentence summary in Chinese\n'
    '- "category": ONE of [LLM, CV, 机器人, AI产品, 研究, 行业, 政策, 开源]\n'
    '- "tags": 2-3 tags in Chinese\n\n'
    "Title: {title}\nContent: {content}\n\n"
    'JSON only: {"title_zh":"...","summary_zh":"...","category":"...","tags":["..."]}'
)


def _parse_json(text: str) -> dict:
    """Parse LLM JSON output with fallback corrections."""
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        text = match.group(1)
    text = text.strip()
    text = re.sub(r"\\\\u(?![0-9a-fA-F]{4})", r"\\\\\\\\u", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    text = re.sub(r",\s*([}\]])", r"\1", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"(\{.*\})", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Could not parse JSON from: {text[:200]}")


def _call_gemini(api_key: str, prompt: str) -> dict:
    from google import genai
    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(model="gemini-2.5-flash-lite", contents=prompt)
    return _parse_json(resp.text)


def _call_groq(api_key: str, prompt: str, model: str = "llama-3.3-70b-versatile") -> dict:
    resp = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}]},
        timeout=60,
    )
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"]
    return _parse_json(text)


def summarize_batch(articles: list[dict], gemini_key: str = "", groq_key: str = "") -> None:
    """Enhance articles in-place with AI summaries. Tries Gemini first, falls back to Groq."""
    for i, article in enumerate(articles):
        prompt = PROMPT_TEMPLATE.replace("{title}", article.get("title", "")).replace(
            "{content}", article.get("content", article.get("summary_zh", ""))[:3000]
        )
        result = None
        last_error = ""
        for provider, key, fn in [
            ("Gemini", gemini_key, lambda p: _call_gemini(gemini_key, p)),
            ("Groq",   groq_key,   lambda p: _call_groq(groq_key, p)),
        ]:
            if not key:
                continue
            try:
                result = fn(prompt)
                print(f"  [rank {i+1}] {provider} OK: {article.get('title','')[:40]}")
                break
            except Exception as e:
                last_error = str(e)
                if "429" in last_error or "RESOURCE_EXHAUSTED" in last_error:
                    print(f"  [rank {i+1}] {provider} quota hit, trying next...")
                    continue
                print(f"  [rank {i+1}] {provider} error: {last_error[:60]}")
                break

        if result is None:
            print(f"  [rank {i+1}] ALL PROVIDERS FAILED: {last_error[:60]}")
            continue

        cat = result.get("category", "")
        if cat in VALID_CATEGORIES:
            article["category"] = cat
        article["title_zh"] = result.get("title_zh", article.get("title_zh", ""))
        article["summary_zh"] = result.get("summary_zh", article.get("summary_zh", ""))
        article["tags"] = result.get("tags", [])[:5]

        if i < len(articles) - 1:
            time.sleep(RATE_LIMIT_DELAY)


DIGEST_ITEMS_EXAMPLE = (
    '{"items": ['
    '{"rank": 1, "title": "中文标题", "summary": "一句话中文摘要（30字以内）", "id": "article_id"},'
    "...up to 10 items"
    ']}'
)

DIGEST_PROMPT = (
    "You are a senior AI news editor. Given these recent news articles, "
    "pick the 10 MOST important/impactful ones and write a brief Chinese digest.\n\n"
    "Articles:\n"
    "%s\n\n"
    "Selection criteria: industry impact > technical breakthrough > product launch > funding. "
    "Prefer diverse categories. "
    "Respond with ONLY a JSON object following this exact format:\n"
    + DIGEST_ITEMS_EXAMPLE + "\n"
    "JSON only, no markdown."
)


def generate_digest(articles: list[dict], gemini_key: str = "", groq_key: str = "") -> list[dict]:
    """Generate a top-10 digest from recent articles. Tries Gemini then Groq with retries."""
    if not (groq_key or gemini_key):
        print("  [digest] No API keys available")
        return []
    if len(articles) < 5:
        print(f"  [digest] Only {len(articles)} articles, need >= 5")
        return []

    candidates = articles[:25]
    lines = []
    for a in candidates:
        title = a.get("title_zh", a.get("title", ""))
        src   = a.get("source", "")
        cat   = a.get("category", "")
        lines.append("- [%s] [%s] [%s] %s" % (a["id"], cat, src, title))

    prompt = DIGEST_PROMPT % "\n".join(lines)

    tried = []
    for provider, key, fn in [
        ("Gemini", gemini_key, lambda p: _call_gemini(gemini_key, p)),
        ("Groq",   groq_key,   lambda p: _call_groq(groq_key, p)),
    ]:
        if not key:
            continue
        tried.append(provider)
        for attempt in range(3):
            try:
                result = fn(prompt)
                items = result.get("items", [])
                id_map = {a["id"]: a for a in candidates}
                digest = []
                for item in items[:10]:
                    aid = item.get("id", "")
                    article = id_map.get(aid, {})
                    digest.append({
                        "rank":     item.get("rank", len(digest) + 1),
                        "title":    item.get("title", article.get("title_zh", "")),
                        "summary":  item.get("summary", ""),
                        "url":      article.get("url", ""),
                        "source":   article.get("source", ""),
                        "category": article.get("category", ""),
                    })
                print(f"  [digest:%s] generated %d items" % (provider, len(digest)))
                return digest
            except Exception as e:
                err = str(e)
                is_retryable = any(x in err for x in ["429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE", "timeout", "rate"])
                if attempt < 2 and is_retryable:
                    wait = 2 ** attempt * 3
                    print(f"  [digest:%s] attempt %d failed (%s), retry in %ds..." % (provider, attempt+1, err[:50], wait))
                    time.sleep(wait)
                    continue
                print(f"  [digest:%s] FAILED (attempt %d): %s" % (provider, attempt+1, err[:80]))
                break

    print(f"  [digest] All providers exhausted (%s), returning empty digest" % ", ".join(tried))
    return []


ALL_DOMAINS_ITEMS_EXAMPLE = (
    '{"AI": [{"rank":1,"title":"中文标题","summary":"一句话（30字）","id":"id"},...up to 10],'
    '"安全": [...],'
    '"经济": [...],'
    '"科技": [...],'
    '"国际": [...]}'
)

ALL_DOMAINS_DIGEST_PROMPT = (
    "You are a senior news editor covering 5 domains: AI, 安全, 经济, 科技, 国际.\n"
    "For EACH domain below, pick the top 10 most important articles.\n\n"
    "%s\n\n"
    "Selection: industry impact > technical breakthrough > product launch > funding. "
    "Prefer diverse categories within each domain.\n"
    "Respond with ONLY a JSON object with exactly these 5 keys: AI, 安全, 经济, 科技, 国际.\n"
    "Each value is an array of objects with keys: rank, title, summary, id.\n"
    "Example format:\n"
    + ALL_DOMAINS_ITEMS_EXAMPLE + "\n"
    "JSON only, no markdown."
)


def generate_all_digests(all_articles: list[dict], gemini_key: str = "", groq_key: str = "") -> dict:
    """Generate top-10 digests for all 5 domains in one API call."""
    if not (groq_key or gemini_key):
        return {}

    domains = ["AI", "安全", "经济", "科技", "国际"]
    domain_articles = {}
    for dom in domains:
        dom_arts = [a for a in all_articles if a.get("domain") == dom]
        if len(dom_arts) >= 3:
            domain_articles[dom] = dom_arts[:20]

    if not domain_articles:
        return {}

    sections = []
    all_candidates = {}
    for dom, arts in domain_articles.items():
        lines = []
        for a in arts:
            title = a.get("title_zh", a.get("title", ""))
            src   = a.get("source", "")
            cat   = a.get("category", "")
            lines.append("- [%s] [%s] [%s] %s" % (a["id"], cat, src, title))
            all_candidates[a["id"]] = a
        sections.append("=== %s (%d articles) ===\n%s" % (dom, len(arts), "\n".join(lines)))

    prompt = ALL_DOMAINS_DIGEST_PROMPT % "\n\n".join(sections)

    tried = []
    # Groq scout (30K TPM) best for large prompts; Gemini as fallback
    for provider, key, fn in [
        ("Groq-scout", groq_key,   lambda p: _call_groq(groq_key, p, "meta-llama/llama-4-scout-17b-16e-instruct")),
        ("Gemini",     gemini_key, _call_gemini),
    ]:
        if not key:
            continue
        tried.append(provider)
        for attempt in range(2):
            try:
                result = fn(prompt)
                digest_data = {}
                for dom in domains:
                    items = result.get(dom, [])
                    if not items:
                        continue
                    digest = []
                    for item in items[:10]:
                        aid = item.get("id", "")
                        article = all_candidates.get(aid, {})
                        digest.append({
                            "rank":     item.get("rank", len(digest) + 1),
                            "title":    item.get("title", article.get("title_zh", "")),
                            "summary":  item.get("summary", ""),
                            "url":      article.get("url", ""),
                            "source":   article.get("source", ""),
                            "category": article.get("category", ""),
                        })
                    if digest:
                        digest_data[dom] = digest
                print("  [all-digest:%s] domains: %s" % (provider, list(digest_data.keys())))
                return digest_data
            except Exception as e:
                err = str(e)
                if attempt == 0 and any(x in err for x in ["429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE"]):
                    wait = 6
                    print("  [all-digest:%s] retry in %ds (%s...)" % (provider, wait, err[:50]))
                    time.sleep(wait)
                    continue
                print("  [all-digest:%s] FAILED: %s" % (provider, err[:80]))
                break

    print("  [all-digest] All providers exhausted (%s)" % ", ".join(tried))
    return {}
