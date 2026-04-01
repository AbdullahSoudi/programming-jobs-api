"""
Fetcher pipeline — runs on a schedule (every 20 minutes).
Flow: fetch from all sources → filter → dedup → categorize → save to DB → cleanup old.
"""

import logging
import time
from models import filter_jobs
from dedup import deduplicate
from category_router import route_job
from database import bulk_insert_jobs, cleanup_expired_jobs, get_seen_ids
from config import MAX_JOBS_PER_RUN

log = logging.getLogger(__name__)

# Import is deferred to avoid circular imports at module level
_fetchers = None


def _get_fetchers():
    global _fetchers
    if _fetchers is None:
        from sources import ALL_FETCHERS
        _fetchers = ALL_FETCHERS
    return _fetchers


def run_fetch_pipeline():
    """
    Main pipeline: fetch → filter → dedup → categorize → insert into DB → cleanup.
    Called by the background scheduler every 20 minutes.
    """
    start = time.time()
    log.info("=" * 60)
    log.info("📡 Fetch pipeline — Starting run")
    log.info("=" * 60)

    # ── 1. Fetch from all sources ───────────────────────────
    all_jobs = []
    for name, fetcher in _get_fetchers():
        try:
            log.info(f"  Fetching from {name}...")
            jobs = fetcher()
            all_jobs.extend(jobs)
            log.info(f"  ✓ {name}: {len(jobs)} raw jobs")
        except Exception as e:
            log.error(f"  ✗ {name} failed: {e}")

    log.info(f"Total raw jobs fetched: {len(all_jobs)}")

    # ── 2. Filter (keywords + geo) ─────────────────────────
    filtered = filter_jobs(all_jobs)
    log.info(f"After filtering: {len(filtered)} jobs")

    # ── 3. Deduplicate against DB ───────────────────────────
    seen = get_seen_ids()
    new_jobs = deduplicate(filtered, seen)
    log.info(f"New jobs to insert: {len(new_jobs)}")

    # ── 4. Cap to prevent huge inserts ──────────────────────
    if len(new_jobs) > MAX_JOBS_PER_RUN:
        log.warning(f"Capping to {MAX_JOBS_PER_RUN} (had {len(new_jobs)} new)")
        new_jobs = new_jobs[:MAX_JOBS_PER_RUN]

    # ── 5. Categorize + prepare for bulk insert ─────────────
    jobs_with_categories = []
    for job in new_jobs:
        categories = route_job(job)
        # Safely flatten tags to a list of strings
        raw_tags = job.tags if isinstance(job.tags, list) else []
        safe_tags = []
        for t in raw_tags:
            if isinstance(t, str):
                safe_tags.append(t)
            elif isinstance(t, dict):
                safe_tags.append(str(t.get("name", t.get("label", ""))))
            elif isinstance(t, list):
                safe_tags.extend(str(x) for x in t)
            else:
                safe_tags.append(str(t))

        job_dict = {
            "unique_id": job.unique_id,
            "url_id": job.url_id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "url": job.url,
            "source": job.source,
            "salary": job.salary or "",
            "job_type": job.job_type or "",
            "tags": safe_tags,
            "is_remote": job.is_remote,
            "original_source": job.original_source or "",
            "description": job.description or "",
            "emoji": job.emoji,
        }
        jobs_with_categories.append((job_dict, categories))

    # ── 6. Bulk insert into DB ──────────────────────────────
    if jobs_with_categories:
        inserted = bulk_insert_jobs(jobs_with_categories)
        log.info(f"✅ Inserted {inserted} new jobs into database.")
    else:
        log.info("No new jobs to insert.")

    # ── 7. Cleanup expired jobs (older than 5 days) ─────────
    cleanup_expired_jobs()

    elapsed = time.time() - start
    log.info(f"Pipeline complete in {elapsed:.1f}s")
    log.info("=" * 60)
