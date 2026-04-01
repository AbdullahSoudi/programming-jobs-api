"""
Category routing — classifies each job into one or more app categories.
Replaces Telegram topic routing with mobile app category assignment.
"""

import logging
from models import Job, _flatten_tags
from config import APP_CATEGORIES, EGYPT_PATTERNS, SAUDI_PATTERNS

log = logging.getLogger(__name__)


def route_job(job: Job) -> list[str]:
    """
    Determine which app categories a job belongs to.
    Returns list of category keys (e.g. ["backend", "internships"]).
    A job can belong to multiple categories.
    """
    categories = []
    tags_str = _flatten_tags(job.tags)
    searchable = f"{job.title} {job.company} {tags_str}".lower()

    for key, cat in APP_CATEGORIES.items():
        keywords = cat.get("keywords", [])
        if any(kw.lower() in searchable for kw in keywords):
            categories.append(key)

    return categories
