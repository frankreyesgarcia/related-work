#!/usr/bin/env python3
"""Build the daily digest from individual summary .md files and send via SMTP."""

import smtplib
import yaml
import os
from pathlib import Path
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def load_config():
    return yaml.safe_load(open("config.yaml"))


def build_digest(date_str):
    summaries_dir = Path("summaries")
    files = sorted(summaries_dir.glob(f"{date_str}_*.md"))

    if not files:
        return None, 0

    digest = f"# Research Digest — {date_str}\n\n"
    digest += f"**{len(files)} papers summarized**\n\n---\n\n"
    for f in files:
        digest += f.read_text(encoding="utf-8")
        digest += "\n\n---\n\n"

    Path("digests").mkdir(exist_ok=True)
    digest_file = Path("digests") / f"digest_{date_str}.md"
    digest_file.write_text(digest, encoding="utf-8")
    print(f"Digest saved to {digest_file}")
    return digest, len(files)


def md_to_html(md_text):
    """Minimal Markdown → HTML conversion for email body."""
    lines = md_text.split("\n")
    html = [
        "<html><body style='font-family:Georgia,serif;max-width:800px;"
        "margin:0 auto;padding:20px;color:#222'>"
    ]
    for line in lines:
        if line.startswith("# "):
            html.append(f"<h1 style='color:#1a1a2e'>{line[2:]}</h1>")
        elif line.startswith("## "):
            html.append(f"<h2 style='color:#c84b2f'>{line[3:]}</h2>")
        elif line.startswith("### "):
            html.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("**") and line.endswith("**"):
            html.append(f"<p><strong>{line.strip('*')}</strong></p>")
        elif line.startswith("- "):
            html.append(f"<li>{line[2:]}</li>")
        elif line == "---":
            html.append("<hr style='border:1px solid #ccc;margin:20px 0'>")
        elif line.strip():
            html.append(f"<p>{line}</p>")
    html.append("</body></html>")
    return "\n".join(html)


def send_email(subject, body_md, cfg):
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    email_from = os.environ.get("EMAIL_FROM", smtp_user)

    if not smtp_user or not smtp_pass:
        print("Error: SMTP_USER and SMTP_PASS environment variables are required.")
        raise SystemExit(1)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = email_from
    msg["To"] = cfg["email"]["to"]

    msg.attach(MIMEText(body_md, "plain", "utf-8"))
    msg.attach(MIMEText(md_to_html(body_md), "html", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)


if __name__ == "__main__":
    cfg = load_config()
    date_str = datetime.now().strftime("%Y-%m-%d")

    print(f"Building digest for {date_str}...")
    digest, count = build_digest(date_str)

    if not digest:
        print("No summaries found for today. Run summarize.py first.")
        raise SystemExit(0)

    prefix = cfg["email"].get("subject_prefix", "Research Digest")
    subject = f"{prefix} {date_str} — {count} papers on '{cfg['topic']}'"

    send_email(subject, digest, cfg)
    print(f"Email sent to {cfg['email']['to']} with {count} summaries")
