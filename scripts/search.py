#!/usr/bin/env python3
"""Search papers on arXiv and Semantic Scholar and save them as JSON."""

import feedparser
import requests
import json
import yaml
from datetime import datetime, timedelta, timezone
from pathlib import Path


def load_config():
    return yaml.safe_load(open("config.yaml"))


def search_arxiv(query, categories, max_results=5, since: datetime | None = None):
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
        pub = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        if since and pub < since:
            continue
        papers.append({
            "id": entry.id.split("/abs/")[-1],
            "title": entry.title.replace("\n", " ").strip(),
            "abstract": entry.summary.replace("\n", " ").strip(),
            "authors": [a.name for a in entry.authors[:3]],
            "url": entry.link,
            "date": entry.published[:10],
            "source": "arxiv",
            "topic": query,
        })
    return papers


def search_semantic_scholar(query, api_key="", max_results=5, since: datetime | None = None):
    headers = {"x-api-key": api_key} if api_key else {}
    params = {
        "query": query,
        "limit": max_results,
        "fields": "title,abstract,year,authors,openAccessPdf,externalIds,publicationDate",
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
        pub_date_str = p.get("publicationDate") or str(p.get("year", ""))
        if since and pub_date_str:
            try:
                pub = datetime.fromisoformat(pub_date_str)
                # date-only (no time) — compare by date to stay inclusive for the day
                if pub.tzinfo is None and len(pub_date_str) <= 10:
                    if pub.date() < since.date():
                        continue
                else:
                    pub = pub if pub.tzinfo else pub.replace(tzinfo=timezone.utc)
                    if pub < since:
                        continue
            except ValueError:
                pass  # year-only string — keep the paper
        papers.append({
            "id": p["paperId"],
            "title": p["title"],
            "abstract": p["abstract"],
            "authors": [a["name"] for a in p.get("authors", [])[:3]],
            "url": f"https://semanticscholar.org/paper/{p['paperId']}",
            "date": pub_date_str,
            "source": "semantic_scholar",
            "topic": query,
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
    topics = cfg.get("topics") or [cfg.get("topic", "")]
    max_per_topic = cfg["max_papers"]

    # Only fetch papers from the last 24 hours
    since = datetime.now(tz=timezone.utc) - timedelta(days=1)
    print(f"Fetching papers published since {since.strftime('%Y-%m-%d %H:%M UTC')}")

    all_papers = []

    for query in topics:
        print(f"Searching: '{query}'")

        if "arxiv" in cfg["sources"]:
            found = search_arxiv(query, cfg.get("arxiv_categories", ["cs.AI"]), max_per_topic, since=since)
            print(f"  arXiv: {len(found)} recent papers found")
            all_papers += found

        if "semantic_scholar" in cfg["sources"]:
            found = search_semantic_scholar(
                query,
                cfg.get("semantic_scholar_api_key", ""),
                max_per_topic,
                since=since,
            )
            print(f"  Semantic Scholar: {len(found)} recent papers found")
            all_papers += found

    all_papers = deduplicate(all_papers)

    out = Path("summaries") / f"papers_{datetime.now().strftime('%Y-%m-%d')}.json"
    out.parent.mkdir(exist_ok=True)
    json.dump(all_papers, open(out, "w"), ensure_ascii=False, indent=2)
    print(f"Done: {len(all_papers)} papers saved to {out} (across {len(topics)} topics)")
