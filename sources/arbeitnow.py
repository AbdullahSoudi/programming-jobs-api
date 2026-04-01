"""Arbeitnow — free job board API."""

import logging
from models import Job, strip_html
from sources.http_utils import get_json

log = logging.getLogger(__name__)

URL = "https://www.arbeitnow.com/api/job-board-api"


def fetch_arbeitnow() -> list[Job]:
    data = get_json(URL)
    if not data or "data" not in data:
        log.warning("Arbeitnow: no data.")
        return []

    jobs = []
    for item in data["data"]:
        jobs.append(Job(
            title=item.get("title", ""),
            company=item.get("company_name", ""),
            location=item.get("location", ""),
            url=item.get("url", ""),
            source="arbeitnow",
            salary="",
            job_type="",
            tags=item.get("tags", []) or [],
            is_remote=item.get("remote", False),
            description=strip_html(item.get("description", "")),
        ))
    log.info(f"Arbeitnow: fetched {len(jobs)} jobs.")
    return jobs
