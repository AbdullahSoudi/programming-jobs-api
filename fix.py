"""
Run this script ONCE from inside the programming-jobs-api folder:
    python fix.py
It will fix database.py and fetcher.py to handle tags correctly.
"""
import os

# ─── Fix database.py ─────────────────────────────────────────
db_code = r'''"""
SQLite database for storing jobs.
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta, timezone
from contextlib import contextmanager
from config import DATABASE_PATH, JOB_EXPIRY_DAYS

log = logging.getLogger(__name__)


def _safe_tags_json(tags_raw):
    """Convert any tags format to a JSON string safe for SQLite."""
    if tags_raw is None:
        return "[]"
    if isinstance(tags_raw, str):
        return tags_raw
    if isinstance(tags_raw, list):
        safe = []
        for t in tags_raw:
            if isinstance(t, str):
                safe.append(t)
            elif isinstance(t, dict):
                safe.append(str(t.get("name", t.get("label", ""))))
            elif isinstance(t, list):
                safe.extend(str(x) for x in t)
            else:
                safe.append(str(t))
        return json.dumps(safe, ensure_ascii=False)
    return "[]"


@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS jobs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                unique_id   TEXT NOT NULL UNIQUE,
                url_id      TEXT DEFAULT '',
                title       TEXT NOT NULL,
                company     TEXT DEFAULT '',
                location    TEXT DEFAULT '',
                url         TEXT NOT NULL,
                source      TEXT DEFAULT '',
                salary      TEXT DEFAULT '',
                job_type    TEXT DEFAULT '',
                tags        TEXT DEFAULT '[]',
                is_remote   INTEGER DEFAULT 0,
                original_source TEXT DEFAULT '',
                description TEXT DEFAULT '',
                emoji       TEXT DEFAULT '',
                created_at  TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS job_categories (
                job_id      INTEGER NOT NULL,
                category    TEXT NOT NULL,
                PRIMARY KEY (job_id, category),
                FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_jobs_unique_id ON jobs(unique_id);
            CREATE INDEX IF NOT EXISTS idx_jobs_url_id ON jobs(url_id);
            CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);
            CREATE INDEX IF NOT EXISTS idx_job_categories_category ON job_categories(category);
            CREATE INDEX IF NOT EXISTS idx_job_categories_job_id ON job_categories(job_id);
        """)
    log.info("Database initialized.")


def _do_insert(conn, job_dict, categories):
    """Insert one job. Returns job_id or None if duplicate."""
    try:
        cursor = conn.execute(
            "INSERT INTO jobs (unique_id, url_id, title, company, location, url, "
            "source, salary, job_type, tags, is_remote, original_source, description, emoji) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(job_dict.get("unique_id", "")),
                str(job_dict.get("url_id", "") or ""),
                str(job_dict.get("title", "")),
                str(job_dict.get("company", "") or ""),
                str(job_dict.get("location", "") or ""),
                str(job_dict.get("url", "")),
                str(job_dict.get("source", "") or ""),
                str(job_dict.get("salary", "") or ""),
                str(job_dict.get("job_type", "") or ""),
                _safe_tags_json(job_dict.get("tags")),
                1 if job_dict.get("is_remote") else 0,
                str(job_dict.get("original_source", "") or ""),
                str(job_dict.get("description", "") or ""),
                str(job_dict.get("emoji", "") or ""),
            ),
        )
        job_id = cursor.lastrowid
        for cat in categories:
            conn.execute(
                "INSERT OR IGNORE INTO job_categories (job_id, category) VALUES (?, ?)",
                (job_id, cat),
            )
        return job_id
    except sqlite3.IntegrityError:
        return None


def insert_job(job_dict, categories):
    with get_db() as conn:
        return _do_insert(conn, job_dict, categories)


def bulk_insert_jobs(jobs_with_categories):
    inserted = 0
    with get_db() as conn:
        for job_dict, categories in jobs_with_categories:
            if _do_insert(conn, job_dict, categories) is not None:
                inserted += 1
    return inserted


def get_jobs(categories=None, page=1, limit=20):
    offset = (page - 1) * limit
    with get_db() as conn:
        if categories:
            ph = ",".join("?" for _ in categories)
            count_row = conn.execute(
                f"SELECT COUNT(DISTINCT j.id) as cnt FROM jobs j "
                f"JOIN job_categories jc ON j.id=jc.job_id WHERE jc.category IN ({ph})",
                categories,
            ).fetchone()
            total = count_row["cnt"]
            rows = conn.execute(
                f"SELECT DISTINCT j.* FROM jobs j "
                f"JOIN job_categories jc ON j.id=jc.job_id WHERE jc.category IN ({ph}) "
                f"ORDER BY j.created_at DESC LIMIT ? OFFSET ?",
                [*categories, limit, offset],
            ).fetchall()
        else:
            total = conn.execute("SELECT COUNT(*) as cnt FROM jobs").fetchone()["cnt"]
            rows = conn.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ? OFFSET ?",
                [limit, offset],
            ).fetchall()

        jobs = [_row_to_dict(row) for row in rows]
        if jobs:
            jids = [j["id"] for j in jobs]
            ph = ",".join("?" for _ in jids)
            cat_rows = conn.execute(
                f"SELECT job_id, category FROM job_categories WHERE job_id IN ({ph})",
                jids,
            ).fetchall()
            cat_map = {}
            for cr in cat_rows:
                cat_map.setdefault(cr["job_id"], []).append(cr["category"])
            for j in jobs:
                j["categories"] = cat_map.get(j["id"], [])

    return {"jobs": jobs, "page": page, "limit": limit, "total": total, "has_next": (offset + limit) < total}


def get_job_by_id(job_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", [job_id]).fetchone()
        if not row:
            return None
        job = _row_to_dict(row)
        cat_rows = conn.execute("SELECT category FROM job_categories WHERE job_id = ?", [job_id]).fetchall()
        job["categories"] = [cr["category"] for cr in cat_rows]
        return job


def get_stats():
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) as cnt FROM jobs").fetchone()["cnt"]
        cat_rows = conn.execute(
            "SELECT category, COUNT(DISTINCT job_id) as cnt FROM job_categories GROUP BY category ORDER BY cnt DESC"
        ).fetchall()
        return {"total": total, "categories": {cr["category"]: cr["cnt"] for cr in cat_rows}}


def get_seen_ids():
    with get_db() as conn:
        rows = conn.execute("SELECT unique_id, url_id FROM jobs").fetchall()
        seen = set()
        for row in rows:
            seen.add(row["unique_id"])
            if row["url_id"]:
                seen.add(row["url_id"])
        return seen


def cleanup_expired_jobs():
    cutoff = (datetime.now(timezone.utc) - timedelta(days=JOB_EXPIRY_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM jobs WHERE created_at < ?", [cutoff])
        deleted = cursor.rowcount
    if deleted > 0:
        log.info(f"Cleaned up {deleted} expired jobs (older than {JOB_EXPIRY_DAYS} days).")
    return deleted


def _row_to_dict(row):
    d = dict(row)
    try:
        d["tags"] = json.loads(d.get("tags", "[]"))
    except (json.JSONDecodeError, TypeError):
        d["tags"] = []
    d["is_remote"] = bool(d.get("is_remote", 0))
    return d
'''

# ─── Fix fetcher.py ──────────────────────────────────────────
fetcher_code = r'''"""
Fetcher pipeline -- runs on a schedule (every 20 minutes).
"""

import logging
import time
from models import filter_jobs
from dedup import deduplicate
from category_router import route_job
from database import bulk_insert_jobs, cleanup_expired_jobs, get_seen_ids
from config import MAX_JOBS_PER_RUN

log = logging.getLogger(__name__)

_fetchers = None

def _get_fetchers():
    global _fetchers
    if _fetchers is None:
        from sources import ALL_FETCHERS
        _fetchers = ALL_FETCHERS
    return _fetchers


def _safe_str(val):
    """Convert any value to a string, handling None."""
    if val is None:
        return ""
    if isinstance(val, str):
        return val
    return str(val)


def _safe_tags(tags):
    """Convert tags to a flat list of strings."""
    if not tags or not isinstance(tags, list):
        return []
    result = []
    for t in tags:
        if isinstance(t, str):
            result.append(t)
        elif isinstance(t, dict):
            result.append(str(t.get("name", t.get("label", ""))))
        elif isinstance(t, list):
            result.extend(str(x) for x in t)
        else:
            result.append(str(t))
    return result


def run_fetch_pipeline():
    start = time.time()
    log.info("=" * 60)
    log.info("Fetch pipeline -- Starting run")
    log.info("=" * 60)

    all_jobs = []
    for name, fetcher in _get_fetchers():
        try:
            log.info(f"  Fetching from {name}...")
            jobs = fetcher()
            all_jobs.extend(jobs)
            log.info(f"  OK {name}: {len(jobs)} raw jobs")
        except Exception as e:
            log.error(f"  FAIL {name}: {e}")

    log.info(f"Total raw jobs fetched: {len(all_jobs)}")

    filtered = filter_jobs(all_jobs)
    log.info(f"After filtering: {len(filtered)} jobs")

    seen = get_seen_ids()
    new_jobs = deduplicate(filtered, seen)
    log.info(f"New jobs to insert: {len(new_jobs)}")

    if len(new_jobs) > MAX_JOBS_PER_RUN:
        log.warning(f"Capping to {MAX_JOBS_PER_RUN} (had {len(new_jobs)} new)")
        new_jobs = new_jobs[:MAX_JOBS_PER_RUN]

    jobs_with_categories = []
    for job in new_jobs:
        categories = route_job(job)
        job_dict = {
            "unique_id": job.unique_id,
            "url_id": job.url_id,
            "title": _safe_str(job.title),
            "company": _safe_str(job.company),
            "location": _safe_str(job.location),
            "url": _safe_str(job.url),
            "source": _safe_str(job.source),
            "salary": _safe_str(job.salary),
            "job_type": _safe_str(job.job_type),
            "tags": _safe_tags(job.tags),
            "is_remote": job.is_remote,
            "original_source": _safe_str(job.original_source),
            "description": _safe_str(job.description),
            "emoji": _safe_str(job.emoji),
        }
        jobs_with_categories.append((job_dict, categories))

    if jobs_with_categories:
        inserted = bulk_insert_jobs(jobs_with_categories)
        log.info(f"Inserted {inserted} new jobs into database.")
    else:
        log.info("No new jobs to insert.")

    cleanup_expired_jobs()

    elapsed = time.time() - start
    log.info(f"Pipeline complete in {elapsed:.1f}s")
    log.info("=" * 60)
'''

# ─── Write files ─────────────────────────────────────────────
with open("database.py", "w", encoding="utf-8") as f:
    f.write(db_code)
print("FIXED: database.py")

with open("fetcher.py", "w", encoding="utf-8") as f:
    f.write(fetcher_code)
print("FIXED: fetcher.py")

# Delete old cache and database
import shutil
for d in ["__pycache__", "sources/__pycache__", "sources\\__pycache__"]:
    if os.path.isdir(d):
        shutil.rmtree(d)
        print(f"DELETED: {d}")

if os.path.exists("jobs.db"):
    os.remove("jobs.db")
    print("DELETED: jobs.db")

print()
print("ALL DONE! Now run:")
print("  uvicorn app:app --host 0.0.0.0 --port 8000")
