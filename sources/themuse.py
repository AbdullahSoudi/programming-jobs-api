"""The Muse — free API for job listings and company profiles."""

import logging
from models import Job, strip_html
from sources.http_utils import get_json

log = logging.getLogger(__name__)

PARAMS_LIST = [
    {"category": "Software Engineering", "page": 0},
    {"category": "Data Science", "page": 0},
]


def fetch_themuse() -> list[Job]:
    jobs = []
    for base_url in [
        "https://www.themuse.com/api/public/jobs",
        "https://www.themuse.com/api/public/v2/jobs",
    ]:
        if jobs:
            break
        for params in PARAMS_LIST:
            data = get_json(base_url, params=params)
            if not data or "results" not in data:
                continue
            for item in data.get("results", []):
                locations = item.get("locations", [])
                loc_names = [l.get("name", "") for l in locations if isinstance(l, dict) and l.get("name")]
                location = ", ".join(loc_names) if loc_names else "Not specified"

                levels = item.get("levels", [])
                level = levels[0].get("name", "") if levels and isinstance(levels[0], dict) else ""

                is_remote = any("remote" in l.lower() or "flexible" in l.lower()
                              for l in loc_names)

                company_obj = item.get("company", {})
                company = company_obj.get("name", "") if isinstance(company_obj, dict) else ""

                cats = item.get("categories", [])
                tag_names = []
                for c in cats:
                    if isinstance(c, dict):
                        tag_names.append(c.get("name", ""))
                    elif isinstance(c, str):
                        tag_names.append(c)

                # The Muse returns job description in "contents" field
                desc_html = item.get("contents", "") or ""

                jobs.append(Job(
                    title=item.get("name", ""),
                    company=company,
                    location=location,
                    url=item.get("refs", {}).get("landing_page", ""),
                    source="themuse",
                    job_type=level,
                    tags=tag_names,
                    is_remote=is_remote,
                    description=strip_html(desc_html),
                ))
    log.info(f"The Muse: fetched {len(jobs)} jobs.")
    return jobs
