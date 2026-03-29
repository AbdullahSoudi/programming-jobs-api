"""
Job data model and filtering logic.
Handles keyword matching and geo-based filtering:
  - Egypt & Saudi Arabia: all jobs (onsite + remote)
  - Rest of world: remote only
"""

from dataclasses import dataclass, field
from typing import Optional
import re
import config


def _flatten_tags(tags) -> str:
    """Safely flatten tags to a string, handling nested lists and non-string items."""
    if not tags:
        return ""
    flat = []
    for item in tags:
        if isinstance(item, list):
            flat.extend(str(i) for i in item)
        elif isinstance(item, dict):
            flat.append(str(item.get("name", item.get("label", ""))))
        else:
            flat.append(str(item))
    return " ".join(flat)


def strip_html(html: str) -> str:
    """Strip HTML tags and decode common entities. Returns clean plain text."""
    if not html:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"</?(p|div|li|ul|ol|h[1-6])[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = (text.replace("&amp;", "&").replace("&lt;", "<")
                .replace("&gt;", ">").replace("&nbsp;", " ")
                .replace("&#39;", "'").replace("&quot;", '"'))
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


@dataclass
class Job:
    title: str
    company: str
    location: str
    url: str
    source: str
    salary: str = ""
    job_type: str = ""
    tags: list = field(default_factory=list)
    is_remote: bool = False
    original_source: str = ""
    description: str = ""           # ← NEW: job description / requirements / benefits

    @property
    def unique_id(self) -> str:
        """Generate a unique ID for dedup. Based on normalized title+company."""
        title_norm = self.title.lower().strip()
        company_norm = self.company.lower().strip()
        for noise in ["inc", "inc.", "ltd", "ltd.", "llc", "corp", "corporation",
                      "co.", "company", "gmbh", "ag", "sa", "pvt"]:
            company_norm = company_norm.replace(noise, "").strip()
        return f"{title_norm}|{company_norm}"

    @property
    def url_id(self) -> str:
        """Secondary ID based on URL for additional dedup."""
        if self.url:
            clean = self.url.split("?utm")[0].split("&utm")[0]
            clean = clean.rstrip("/").lower()
            return clean
        return ""

    @property
    def display_source(self) -> str:
        """Get the display name for the source."""
        if self.original_source:
            return self.original_source
        return config.SOURCE_DISPLAY.get(self.source, self.source.title())

    @property
    def emoji(self) -> str:
        """Pick the best emoji based on title and location."""
        text = f"{self.title} {self.location} {_flatten_tags(self.tags)}".lower()
        for keyword, em in config.EMOJI_MAP.items():
            if keyword in text:
                return em
        return config.DEFAULT_EMOJI


# ─── Filtering ──────────────────────────────────────────────

def _text_matches_any(text: str, patterns) -> bool:
    text_lower = text.lower()
    return any(p.lower() in text_lower for p in patterns)


def _is_in_egypt(location: str) -> bool:
    loc = location.lower().strip()
    return any(p in loc for p in config.EGYPT_PATTERNS)


def _is_in_saudi(location: str) -> bool:
    loc = location.lower().strip()
    return any(p in loc for p in config.SAUDI_PATTERNS)


def _is_remote(job: Job) -> bool:
    if job.is_remote:
        return True
    combined = f"{job.title} {job.location} {job.job_type} {_flatten_tags(job.tags)}".lower()
    return any(p in combined for p in config.REMOTE_PATTERNS)


def _is_in_allowed_country(location: str) -> bool:
    return _is_in_egypt(location) or _is_in_saudi(location)


def is_programming_job(job: Job) -> bool:
    searchable = f"{job.title} {_flatten_tags(job.tags)}".lower()
    has_include = any(kw.lower() in searchable for kw in config.INCLUDE_KEYWORDS)
    if not has_include:
        return False
    has_exclude = any(kw.lower() in searchable for kw in config.EXCLUDE_KEYWORDS)
    if has_exclude:
        return False
    return True


def passes_geo_filter(job: Job) -> bool:
    remote_only_sources = {"remotive", "remoteok", "wwr", "workingnomads", "findwork", "reed"}
    if job.source in remote_only_sources:
        return True
    if _is_in_allowed_country(job.location):
        return True
    if _is_remote(job):
        return True
    return False


def filter_jobs(jobs: list[Job]) -> list[Job]:
    filtered = []
    for job in jobs:
        if not job.title or not job.url:
            continue
        if not is_programming_job(job):
            continue
        if not passes_geo_filter(job):
            continue
        filtered.append(job)
    return filtered
