"""
SQLite database for storing jobs.
Handles: create tables, insert jobs, query with pagination,
         cleanup expired jobs (older than 5 days), dedup tracking.
"""

import sqlite3
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from contextlib import contextmanager

from config import DATABASE_PATH, JOB_EXPIRY_DAYS

log = logging.getLogger(__name__)

# ─── Connection Management ──────────────────────────────────

@contextmanager
def get_db():
    """Thread-safe connection with WAL mode for concurrent reads."""
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


# ─── Schema ─────────────────────────────────────────────────

def init_db():
    """Create tables if they don't exist."""
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
                emoji       TEXT DEFAULT '💻',
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


# ─── Insert ─────────────────────────────────────────────────

def insert_job(job_dict: dict, categories: list[str]) -> int | None:
    """
    Insert a job into the database. Returns the job id, or None if duplicate.
    job_dict keys: unique_id, url_id, title, company, location, url, source,
                   salary, job_type, tags, is_remote, original_source, description, emoji
    """
    with get_db() as conn:
        try:
            # Safely serialize tags — bulletproof: force every element to str
            try:
                tags_raw = job_dict.get("tags", [])
                if isinstance(tags_raw, str):
                    tags_json = tags_raw
                else:
                    tags_list = tags_raw if isinstance(tags_raw, list) else []
                    tags_json = json.dumps(
                        [str(t) for t in tags_list],
                        ensure_ascii=False,
                    )
            except Exception:
                tags_json = "[]"

            cursor = conn.execute("""
                INSERT INTO jobs (unique_id, url_id, title, company, location, url,
                                  source, salary, job_type, tags, is_remote,
                                  original_source, description, emoji)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_dict["unique_id"],
                job_dict.get("url_id", ""),
                job_dict["title"],
                job_dict.get("company", ""),
                job_dict.get("location", ""),
                job_dict["url"],
                job_dict.get("source", ""),
                job_dict.get("salary", "") or "",
                job_dict.get("job_type", "") or "",
                tags_json,
                1 if job_dict.get("is_remote") else 0,
                job_dict.get("original_source", "") or "",
                job_dict.get("description", "") or "",
                job_dict.get("emoji", "💻"),
            ))
            job_id = cursor.lastrowid

            # Insert categories
            for cat in categories:
                conn.execute(
                    "INSERT OR IGNORE INTO job_categories (job_id, category) VALUES (?, ?)",
                    (job_id, cat)
                )

            return job_id

        except sqlite3.IntegrityError:
            # Duplicate unique_id — skip
            return None


def bulk_insert_jobs(jobs_with_categories: list[tuple[dict, list[str]]]) -> int:
    """Insert multiple jobs. Returns count of newly inserted jobs."""
    inserted = 0
    with get_db() as conn:
        for job_dict, categories in jobs_with_categories:
            try:
                # Safely serialize tags — bulletproof: force every element to str
                try:
                    tags_raw = job_dict.get("tags", [])
                    if isinstance(tags_raw, str):
                        tags_json = tags_raw
                    else:
                        tags_list = tags_raw if isinstance(tags_raw, list) else []
                        tags_json = json.dumps(
                            [str(t) for t in tags_list],
                            ensure_ascii=False,
                        )
                except Exception:
                    tags_json = "[]"

                cursor = conn.execute("""
                    INSERT INTO jobs (unique_id, url_id, title, company, location, url,
                                      source, salary, job_type, tags, is_remote,
                                      original_source, description, emoji)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job_dict["unique_id"],
                    job_dict.get("url_id", ""),
                    job_dict["title"],
                    job_dict.get("company", ""),
                    job_dict.get("location", ""),
                    job_dict["url"],
                    job_dict.get("source", ""),
                    job_dict.get("salary", "") or "",
                    job_dict.get("job_type", "") or "",
                    tags_json,
                    1 if job_dict.get("is_remote") else 0,
                    job_dict.get("original_source", "") or "",
                    job_dict.get("description", "") or "",
                    job_dict.get("emoji", "💻"),
                ))
                job_id = cursor.lastrowid

                for cat in categories:
                    conn.execute(
                        "INSERT OR IGNORE INTO job_categories (job_id, category) VALUES (?, ?)",
                        (job_id, cat)
                    )
                inserted += 1

            except Exception:
                continue

    return inserted


# ─── Query ──────────────────────────────────────────────────

def get_jobs(categories: list[str] | None = None,
             page: int = 1,
             limit: int = 20) -> dict:
    """
    Get jobs with optional category filtering and pagination.
    Returns: { "jobs": [...], "page", "limit", "total", "has_next" }
    """
    offset = (page - 1) * limit

    with get_db() as conn:
        if categories:
            placeholders = ",".join("?" for _ in categories)

            # Count total matching jobs
            count_row = conn.execute(f"""
                SELECT COUNT(DISTINCT j.id) as cnt
                FROM jobs j
                JOIN job_categories jc ON j.id = jc.job_id
                WHERE jc.category IN ({placeholders})
            """, categories).fetchone()
            total = count_row["cnt"]

            # Get paginated jobs
            rows = conn.execute(f"""
                SELECT DISTINCT j.*
                FROM jobs j
                JOIN job_categories jc ON j.id = jc.job_id
                WHERE jc.category IN ({placeholders})
                ORDER BY j.created_at DESC
                LIMIT ? OFFSET ?
            """, [*categories, limit, offset]).fetchall()
        else:
            count_row = conn.execute("SELECT COUNT(*) as cnt FROM jobs").fetchone()
            total = count_row["cnt"]

            rows = conn.execute("""
                SELECT * FROM jobs
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, [limit, offset]).fetchall()

        jobs = [_row_to_dict(row) for row in rows]

        # Attach categories to each job
        if jobs:
            job_ids = [j["id"] for j in jobs]
            placeholders = ",".join("?" for _ in job_ids)
            cat_rows = conn.execute(f"""
                SELECT job_id, category FROM job_categories
                WHERE job_id IN ({placeholders})
            """, job_ids).fetchall()

            cat_map = {}
            for cr in cat_rows:
                cat_map.setdefault(cr["job_id"], []).append(cr["category"])

            for j in jobs:
                j["categories"] = cat_map.get(j["id"], [])

    return {
        "jobs": jobs,
        "page": page,
        "limit": limit,
        "total": total,
        "has_next": (offset + limit) < total,
    }


def get_job_by_id(job_id: int) -> dict | None:
    """Get a single job with full details including categories."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", [job_id]).fetchone()
        if not row:
            return None

        job = _row_to_dict(row)

        cat_rows = conn.execute(
            "SELECT category FROM job_categories WHERE job_id = ?", [job_id]
        ).fetchall()
        job["categories"] = [cr["category"] for cr in cat_rows]

        return job


def get_stats() -> dict:
    """Get job count per category + total."""
    with get_db() as conn:
        total_row = conn.execute("SELECT COUNT(*) as cnt FROM jobs").fetchone()
        total = total_row["cnt"]

        cat_rows = conn.execute("""
            SELECT category, COUNT(DISTINCT job_id) as cnt
            FROM job_categories
            GROUP BY category
            ORDER BY cnt DESC
        """).fetchall()

        categories = {cr["category"]: cr["cnt"] for cr in cat_rows}

    return {"total": total, "categories": categories}


# ─── Dedup Check ────────────────────────────────────────────

def get_seen_ids() -> set:
    """Get all unique_id and url_id from the database for dedup."""
    with get_db() as conn:
        rows = conn.execute("SELECT unique_id, url_id FROM jobs").fetchall()
        seen = set()
        for row in rows:
            seen.add(row["unique_id"])
            if row["url_id"]:
                seen.add(row["url_id"])
        return seen


# ─── Cleanup ────────────────────────────────────────────────

def cleanup_expired_jobs() -> int:
    """Delete jobs older than JOB_EXPIRY_DAYS. Returns count deleted."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=JOB_EXPIRY_DAYS)).strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        # CASCADE will delete from job_categories too
        cursor = conn.execute("DELETE FROM jobs WHERE created_at < ?", [cutoff])
        deleted = cursor.rowcount

    if deleted > 0:
        log.info(f"🗑️ Cleaned up {deleted} expired jobs (older than {JOB_EXPIRY_DAYS} days).")
    return deleted


# ─── Helpers ────────────────────────────────────────────────

def _row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a Row to a clean dict for API responses."""
    d = dict(row)
    # Parse tags JSON
    try:
        d["tags"] = json.loads(d.get("tags", "[]"))
    except (json.JSONDecodeError, TypeError):
        d["tags"] = []
    # Convert is_remote to bool
    d["is_remote"] = bool(d.get("is_remote", 0))
    return d
