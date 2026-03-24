#!/usr/bin/env python3
"""Search papers on arXiv and Semantic Scholar and save them as JSON."""

import feedparser
import requests
import json
import yaml
import sys
from datetime import datetime
from pathlib import Path


def load_config():
    return yaml.safe_load(open("config.yaml"))


def search_arxiv(query, categories, max_results=5):
    cat_filter = "+OR+".join(f"cat:{c}" for c in categories)
    url = (
        f"http://export.arxiv.org/api/query?"
        f"search_query=({query})+AND+({cat_filter})"
        f"&sortBy=submittedDate&sortOrder=descending"
        f"&max_results={max_results}"
    )
    feed = feedparser.parse(url)
    papers = []
    for entry in feed.entries:
        papers.append({
            "id": entry.id.split("/abs/")[-1],
            "title": entry.title.replace("\n", " ").strip(),
            "abstract": entry.summary.replace("\n", " ").strip(),
            "authors": [a.name for a in entry.authors[:3]],
            "url": entry.link,
            "date": entry.published[:10],
            "source": "arxiv",
        })
    return papers


def search_semantic_scholar(query, api_key="", max_results=5):
    headers = {"x-api-key": api_key} if api_key else {}
    params = {
        "query": query,
        "limit": max_results,
        "fields": "title,abstract,year,authors,openAccessPdf,externalIds",
    }
    try:
        r = requests.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params=params,
            headers=headers,
            timeout=15,
        )
    except requests.RequestException as e:
        print(f"  Warning: Semantic Scholar request failed: {e}")
        return []

    if r.status_code != 200:
        print(f"  Warning: Semantic Scholar returned status {r.status_code}")
        return []

    papers = []
    for p in r.json().get("data", []):
        if not p.get("abstract"):
            continue
        papers.append({
            "id": p["paperId"],
            "title": p["title"],
            "abstract": p["abstract"],
            "authors": [a["name"] for a in p.get("authors", [])[:3]],
            "url": f"https://semanticscholar.org/paper/{p['paperId']}",
            "date": str(p.get("year", "N/A")),
            "source": "semantic_scholar",
        })
    return papers


def deduplicate(papers):
    """Remove duplicates by normalized title prefix (60 chars)."""
    seen, unique = set(), []
    for p in papers:
        key = p["title"].lower()[:60]
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


if __name__ == "__main__":
    cfg = load_config()
    query = cfg["topic"]
    print(f"Searching: '{query}'")

    papers = []

    if "arxiv" in cfg["sources"]:
        found = search_arxiv(query, cfg.get("arxiv_categories", ["cs.AI"]), cfg["max_papers"])
        print(f"  arXiv: {len(found)} papers found")
        papers += found

    if "semantic_scholar" in cfg["sources"]:
        found = search_semantic_scholar(
            query,
            cfg.get("semantic_scholar_api_key", ""),
            cfg["max_papers"],
        )
        print(f"  Semantic Scholar: {len(found)} papers found")
        papers += found

    papers = deduplicate(papers)[: cfg["max_papers"]]

    out = Path("summaries") / f"papers_{datetime.now().strftime('%Y-%m-%d')}.json"
    out.parent.mkdir(exist_ok=True)
    json.dump(papers, open(out, "w"), ensure_ascii=False, indent=2)
    print(f"Done: {len(papers)} papers saved to {out}")
