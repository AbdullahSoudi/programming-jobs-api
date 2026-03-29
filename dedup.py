"""
Deduplication using database.
Checks unique_id (title+company) and url_id against existing jobs in DB.
"""

import logging
from models import Job
from database import get_seen_ids

log = logging.getLogger(__name__)


def deduplicate(jobs: list[Job], seen: set | None = None) -> list[Job]:
    """
    Return only jobs whose unique_id is NOT already in the database.
    Deduplicates by BOTH title+company AND URL.
    """
    if seen is None:
        seen = get_seen_ids()

    new_jobs = []
    batch_ids = set()

    for job in jobs:
        uid = job.unique_id
        url_id = job.url_id

        if uid in seen or uid in batch_ids:
            continue
        if url_id and (url_id in seen or url_id in batch_ids):
            continue

        batch_ids.add(uid)
        if url_id:
            batch_ids.add(url_id)
        new_jobs.append(job)

    log.info(f"Dedup: {len(jobs)} total → {len(new_jobs)} new jobs.")
    return new_jobs
