"""arXiv API source for AI research papers."""

import httpx
from xml.etree import ElementTree
from datetime import datetime, timezone

ARXIV_API = "https://export.arxiv.org/api/query"
ATOM_NS = "{http://www.w3.org/2005/Atom}"

QUERY = "cat:cs.AI OR cat:cs.CL OR cat:cs.CV OR cat:cs.LG OR cat:cs.RO"


def fetch_arxiv() -> list[dict]:
    """Fetch recent AI papers from arXiv."""
    try:
        client = httpx.Client(timeout=30)
        resp = client.get(
            ARXIV_API,
            params={
                "search_query": QUERY,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
                "max_results": "30",
            },
        )
        resp.raise_for_status()
        client.close()

        root = ElementTree.fromstring(resp.content)
        articles = []
        for entry in root.findall(f"{ATOM_NS}entry"):
            title_el = entry.find(f"{ATOM_NS}title")
            title = title_el.text.strip().replace("\n", " ") if title_el is not None and title_el.text else ""

            summary_el = entry.find(f"{ATOM_NS}summary")
            summary = summary_el.text.strip().replace("\n", " ") if summary_el is not None and summary_el.text else ""

            link_el = entry.find(f"{ATOM_NS}id")
            url = link_el.text.strip() if link_el is not None and link_el.text else ""

            published_el = entry.find(f"{ATOM_NS}published")
            if published_el is not None and published_el.text:
                published = published_el.text.strip()
            else:
                published = datetime.now(timezone.utc).isoformat()

            # Get categories
            categories = []
            for cat_el in entry.findall("{http://arxiv.org/schemas/atom}primary_category"):
                term = cat_el.get("term", "")
                if term:
                    categories.append(term)

            articles.append({
                "title": title,
                "url": url,
                "source": "arXiv",
                "published": published,
                "content": summary[:2000],
                "extra": {"categories": categories},
            })

        print(f"  [arXiv] fetched {len(articles)} papers")
        return articles
    except Exception as e:
        print(f"  [arXiv] error: {e}")
        return []
