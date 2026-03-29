"""Working Nomads — JSON API + RSS fallback for development jobs."""

import logging
from models import Job, strip_html
from sources.http_utils import get_json

log = logging.getLogger(__name__)

URL = "https://www.workingnomads.com/api/exposed_jobs/"


def fetch_workingnomads() -> list[Job]:
    data = get_json(URL)
    if not data or not isinstance(data, list):
        from sources.http_utils import get_text
        xml_text = get_text("https://www.workingnomads.com/jobsrss?category=development")
        if not xml_text:
            log.warning("Working Nomads: no data from API or RSS.")
            return []
        return _parse_rss(xml_text)

    jobs = []
    for item in data:
        cat = item.get("category_name", "")
        if cat.lower() not in ("development", "dev", "sysadmin", "devops"):
            continue
        jobs.append(Job(
            title=item.get("title", ""),
            company=item.get("company_name", ""),
            location="Remote",
            url=item.get("url", "") or item.get("external_url", ""),
            source="workingnomads",
            tags=[cat] if cat else [],
            is_remote=True,
            description=strip_html(item.get("description", "")),
        ))
    log.info(f"Working Nomads: fetched {len(jobs)} jobs.")
    return jobs


def _parse_rss(xml_text: str) -> list[Job]:
    import xml.etree.ElementTree as ET
    jobs = []
    try:
        root = ET.fromstring(xml_text)
        for item in root.findall(".//item"):
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            category = item.findtext("category", "")
            desc_html = item.findtext("description", "")
            company = ""
            if " at " in title:
                parts = title.rsplit(" at ", 1)
                title = parts[0].strip()
                company = parts[1].strip()
            jobs.append(Job(
                title=title, company=company, location="Remote",
                url=link.strip(), source="workingnomads",
                tags=[category] if category else [], is_remote=True,
                description=strip_html(desc_html),
            ))
    except ET.ParseError as e:
        log.warning(f"Working Nomads RSS parse error: {e}")
    log.info(f"Working Nomads: fetched {len(jobs)} jobs (RSS fallback).")
    return jobs
