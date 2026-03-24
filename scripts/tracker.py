#!/usr/bin/env python3
"""SQLite-based tracker to avoid re-summarizing already-seen papers."""

import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("tracker.db")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seen_papers (
            paper_id    TEXT NOT NULL,
            title       TEXT NOT NULL,
            topic       TEXT,
            source      TEXT,
            paper_date  TEXT,
            scanned_at  TEXT NOT NULL,
            PRIMARY KEY (paper_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            run_date    TEXT PRIMARY KEY,
            topics      TEXT,
            total_found INTEGER,
            total_new   INTEGER,
            ran_at      TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def is_seen(paper_id: str) -> bool:
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM seen_papers WHERE paper_id = ?", (paper_id,)
        ).fetchone()
        return row is not None


def mark_seen(paper: dict):
    with _connect() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO seen_papers
               (paper_id, title, topic, source, paper_date, scanned_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                paper["id"],
                paper["title"],
                paper.get("topic", ""),
                paper.get("source", ""),
                paper.get("date", ""),
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()


def record_run(run_date: str, topics: list, total_found: int, total_new: int):
    with _connect() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO runs
               (run_date, topics, total_found, total_new, ran_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                run_date,
                ", ".join(topics),
                total_found,
                total_new,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()


def last_run_date() -> str | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT run_date FROM runs ORDER BY ran_at DESC LIMIT 1"
        ).fetchone()
        return row[0] if row else None


def seen_count() -> int:
    with _connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM seen_papers").fetchone()[0]
