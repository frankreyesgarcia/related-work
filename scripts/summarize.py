#!/usr/bin/env python3
"""Call OpenCode CLI per paper and save FAT summaries as individual .md files."""

import json
import subprocess
import yaml
from datetime import datetime
from pathlib import Path


def load_config():
    return yaml.safe_load(open("config.yaml"))


def safe_filename(title):
    return "".join(c if c.isalnum() or c in " -_" else "_" for c in title)[:60].strip()


def build_prompt(prompt_template, paper):
    return f"""{prompt_template}

---

TÍTULO: {paper['title']}
AUTORES: {', '.join(paper['authors'])}
FECHA: {paper['date']}
FUENTE: {paper['source']}
URL: {paper['url']}

ABSTRACT:
{paper['abstract']}
"""


def summarize_paper(paper, prompt_template, model, out_file):
    prompt = build_prompt(prompt_template, paper)
    result = subprocess.run(
        ["opencode", "-p", prompt, "--model", model],
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        print(f"  ❌ Error: {result.stderr[:200]}")
        return False

    # Each summary file: paper title as H1, then metadata, then FAT body
    md = f"# {paper['title']}\n\n"
    md += f"**Autores:** {', '.join(paper['authors'])}  \n"
    md += f"**Fecha:** {paper['date']} | **Fuente:** {paper['source']}  \n"
    md += f"**URL:** {paper['url']}\n\n"
    md += "---\n\n"
    md += result.stdout.strip()
    md += "\n"

    out_file.write_text(md, encoding="utf-8")
    return True


if __name__ == "__main__":
    cfg = load_config()
    model = cfg["opencode_model"]
    date = datetime.now().strftime("%Y-%m-%d")

    papers_file = Path("summaries") / f"papers_{date}.json"
    if not papers_file.exists():
        print(f"❌ No papers file found for today: {papers_file}")
        print("   Run scripts/search.py first.")
        raise SystemExit(1)

    papers = json.load(open(papers_file))
    prompt_template = open("prompts/fat_summary.md").read()

    print(f"📝 Generating {len(papers)} summaries with OpenCode ({model})...")

    ok, skipped, failed = 0, 0, 0
    for i, paper in enumerate(papers, 1):
        safe_title = safe_filename(paper["title"])
        out_file = Path("summaries") / f"{date}_{i:02d}_{safe_title}.md"

        if out_file.exists():
            print(f"  ⏭  Already exists: {out_file.name}")
            skipped += 1
            continue

        print(f"  [{i}/{len(papers)}] {paper['title'][:70]}...")
        success = summarize_paper(paper, prompt_template, model, out_file)
        if success:
            print(f"  ✅ Saved: {out_file.name}")
            ok += 1
        else:
            failed += 1

    print(f"\n✅ Done — {ok} new, {skipped} skipped, {failed} failed")
