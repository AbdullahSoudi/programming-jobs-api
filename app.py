"""
Programming Jobs Mobile API — Main entry point.
FastAPI server + background scheduler (fetches jobs every 20 minutes).
"""

import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from database import init_db
from api import router
from fetcher import run_fetch_pipeline
from config import FETCH_INTERVAL_MINUTES

# ─── Logging ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("app")

# ─── Scheduler ──────────────────────────────────────────────
scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB, start scheduler, run first fetch. Shutdown: stop scheduler."""

    # Initialize database tables
    init_db()
    log.info("✅ Database initialized.")

    # Schedule the fetcher pipeline every 20 minutes
    scheduler.add_job(
        run_fetch_pipeline,
        "interval",
        minutes=FETCH_INTERVAL_MINUTES,
        id="fetch_pipeline",
        max_instances=1,           # prevent overlapping runs
        coalesce=True,             # if missed, run once
    )
    scheduler.start()
    log.info(f"⏰ Scheduler started — fetching every {FETCH_INTERVAL_MINUTES} minutes.")

    # Run the first fetch in a background thread (don't block server startup)
    threading.Thread(target=run_fetch_pipeline, daemon=True).start()
    log.info("🚀 Initial fetch started in background.")

    yield

    # Shutdown
    scheduler.shutdown(wait=False)
    log.info("Scheduler stopped.")


# ─── FastAPI App ────────────────────────────────────────────
app = FastAPI(
    title="Programming Jobs API",
    description="REST API for programming jobs mobile app. "
                "Aggregates jobs from 15 sources, categorizes, and serves via paginated endpoints.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow all origins for mobile app access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(router)


# ─── Root / Health Check ────────────────────────────────────
@app.get("/")
def root():
    return {
        "name": "Programming Jobs API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "categories": "/api/categories",
            "jobs": "/api/jobs?categories=android,ios&page=1&limit=20",
            "job_detail": "/api/jobs/{id}",
            "stats": "/api/stats",
        }
    }


@app.get("/health")
def health():
    from database import get_stats
    stats = get_stats()
    return {"status": "ok", "total_jobs": stats["total"]}
