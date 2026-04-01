"""
FastAPI REST API endpoints for the mobile app.
4 endpoints: categories, jobs (paginated), job detail, stats.
"""

from fastapi import APIRouter, Query, HTTPException
from config import APP_CATEGORIES, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from database import get_jobs, get_job_by_id, get_stats

router = APIRouter(prefix="/api")


# ─── GET /api/categories ────────────────────────────────────

@router.get("/categories")
def list_categories():
    """
    Returns the 9 app categories for the onboarding screen.
    Response: [{ "key": "android", "name": "Android", "icon": "android" }, ...]
    """
    return [
        {
            "key": key,
            "name": cat["name"],
            "icon": cat["icon"],
        }
        for key, cat in APP_CATEGORIES.items()
    ]


# ─── GET /api/jobs ──────────────────────────────────────────

@router.get("/jobs")
def list_jobs(
    categories: str = Query(default="", description="Comma-separated category keys, e.g. 'android,ios'"),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Jobs per page"),
):
    """
    Returns paginated jobs filtered by categories.
    If no categories specified, returns all jobs.
    Supports infinite scroll — client increments `page` until `has_next` is false.

    Response:
    {
        "jobs": [ { id, title, company, location, job_type, is_remote, emoji, source, created_at, categories } ],
        "page": 1,
        "limit": 20,
        "total": 150,
        "has_next": true
    }
    """
    cat_list = [c.strip() for c in categories.split(",") if c.strip()] if categories else None

    # Validate category keys
    if cat_list:
        valid_keys = set(APP_CATEGORIES.keys())
        invalid = [c for c in cat_list if c not in valid_keys]
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid categories: {invalid}. Valid: {sorted(valid_keys)}"
            )

    result = get_jobs(categories=cat_list, page=page, limit=limit)

    # Slim down job objects for listing (no description — that's for detail page)
    for job in result["jobs"]:
        job.pop("description", None)
        job.pop("unique_id", None)
        job.pop("url_id", None)
        job.pop("updated_at", None)

    return result


# ─── GET /api/jobs/{job_id} ─────────────────────────────────

@router.get("/jobs/{job_id}")
def job_detail(job_id: int):
    """
    Returns full job details including description, for the detail screen.
    Response: { id, title, company, location, description, url, salary, ... }
    """
    job = get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Clean up internal fields
    job.pop("unique_id", None)
    job.pop("url_id", None)
    job.pop("updated_at", None)

    return job


# ─── GET /api/stats ─────────────────────────────────────────

@router.get("/stats")
def stats():
    """
    Returns job counts per category + total.
    Response: { "total": 150, "categories": { "backend": 45, "frontend": 30, ... } }
    """
    return get_stats()
