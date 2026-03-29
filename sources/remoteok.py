"""RemoteOK — public JSON feed."""

import logging
from models import Job, strip_html
from sources.http_utils import get_json

log = logging.getLogger(__name__)

URL = "https://remoteok.com/api"


def fetch_remoteok() -> list[Job]:
    data = get_json(URL, headers={"User-Agent": "ProgrammingJobsBot/1.0"})
    if not data or not isinstance(data, list):
        log.warning("RemoteOK: no data.")
        return []

    jobs = []
    for item in data:
        if not isinstance(item, dict) or "id" not in item:
            continue
        salary = ""
        if item.get("salary_min") and item.get("salary_max"):
            salary = f"${item['salary_min']:,}–${item['salary_max']:,}"

        jobs.append(Job(
            title=item.get("position", ""),
            company=item.get("company", ""),
            location=item.get("location", "Remote"),
            url=item.get("url", f"https://remoteok.com/remote-jobs/{item.get('id', '')}"),
            source="remoteok",
            salary=salary,
            job_type="",
            tags=item.get("tags", []) or [],
            is_remote=True,
            description=strip_html(item.get("description", "")),
        ))
    log.info(f"RemoteOK: fetched {len(jobs)} jobs.")
    return jobs
