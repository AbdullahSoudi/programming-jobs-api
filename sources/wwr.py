"""We Work Remotely — RSS feeds for programming job categories."""

import logging
import xml.etree.ElementTree as ET
from models import Job, strip_html
from sources.http_utils import get_text

log = logging.getLogger(__name__)

RSS_FEEDS = {
    "Full-Stack": "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
    "Back-End": "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss",
    "Front-End": "https://weworkremotely.com/categories/remote-front-end-programming-jobs.rss",
    "DevOps": "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    "Marketing": "https://weworkremotely.com/categories/remote-sales-and-marketing-jobs.rss",
}


def fetch_wwr() -> list[Job]:
    jobs = []
    for category, url in RSS_FEEDS.items():
        xml_text = get_text(url)
        if not xml_text:
            continue
        try:
            root = ET.fromstring(xml_text)
            for item in root.findall(".//item"):
                title_raw = item.findtext("title", "")
                link = item.findtext("link", "")
                desc_html = item.findtext("description", "")

                if ": " in title_raw:
                    company, title = title_raw.split(": ", 1)
                else:
                    company, title = "", title_raw

                jobs.append(Job(
                    title=title.strip(),
                    company=company.strip(),
                    location="Remote",
                    url=link.strip(),
                    source="wwr",
                    tags=[category],
                    is_remote=True,
                    description=strip_html(desc_html),
                ))
        except ET.ParseError as e:
            log.warning(f"WWR: XML parse error for {category}: {e}")

    log.info(f"WWR: fetched {len(jobs)} jobs.")
    return jobs
