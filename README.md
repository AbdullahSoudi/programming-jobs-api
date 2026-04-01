# Programming Jobs Mobile API

REST API backend for the Programming Jobs mobile app.  
Aggregates jobs from **15 sources**, categorizes them into **9 categories**, and serves them via paginated endpoints.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set API keys (optional — sources without keys are skipped)
export RAPIDAPI_KEY="your_key"
export ADZUNA_APP_ID="your_id"
export ADZUNA_APP_KEY="your_key"
export FINDWORK_API_KEY="your_key"
export JOOBLE_API_KEY="your_key"
export REED_API_KEY="your_key"

# Run the server
uvicorn app:app --host 0.0.0.0 --port 8000

# Or with auto-reload for development
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

The server starts and immediately begins fetching jobs in the background.  
Jobs are fetched every **20 minutes** and stored in SQLite.  
Jobs older than **5 days** are automatically deleted.

## API Endpoints

### `GET /api/categories`
Returns the 9 app categories for the onboarding screen.

**Response:**
```json
[
  { "key": "android", "name": "Android", "icon": "android" },
  { "key": "ios", "name": "iOS", "icon": "apple" },
  { "key": "backend", "name": "Backend", "icon": "server" },
  { "key": "frontend", "name": "Frontend", "icon": "layout" },
  { "key": "devops", "name": "DevOps & Cloud", "icon": "cloud" },
  { "key": "ai_ml", "name": "AI/ML", "icon": "brain" },
  { "key": "cybersecurity", "name": "Cybersecurity", "icon": "shield" },
  { "key": "qa", "name": "QA & Testing", "icon": "check-circle" },
  { "key": "internships", "name": "Internships", "icon": "graduation-cap" }
]
```

---

### `GET /api/jobs`
Returns paginated jobs filtered by categories. Supports **infinite scroll**.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `categories` | string | `""` | Comma-separated category keys (e.g. `android,ios`) |
| `page` | int | `1` | Page number (1-based) |
| `limit` | int | `20` | Jobs per page (max 50) |

**Example:** `GET /api/jobs?categories=android,ios&page=1&limit=20`

**Response:**
```json
{
  "jobs": [
    {
      "id": 42,
      "title": "Senior Android Developer",
      "company": "Google",
      "location": "Mountain View, CA",
      "url": "https://...",
      "source": "jsearch",
      "salary": "USD 150,000–200,000",
      "job_type": "Full Time",
      "tags": [],
      "is_remote": false,
      "original_source": "LinkedIn",
      "emoji": "🤖",
      "created_at": "2025-03-29 10:30:00",
      "categories": ["android"]
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 150,
  "has_next": true
}
```

**Infinite scroll flow:**
1. First load: `GET /api/jobs?categories=android&page=1&limit=20`
2. User scrolls to bottom → check `has_next`
3. If `true`: `GET /api/jobs?categories=android&page=2&limit=20`
4. Repeat until `has_next` is `false`

---

### `GET /api/jobs/{id}`
Returns full job details including description.

**Example:** `GET /api/jobs/42`

**Response:**
```json
{
  "id": 42,
  "title": "Senior Android Developer",
  "company": "Google",
  "location": "Mountain View, CA",
  "url": "https://...",
  "source": "jsearch",
  "salary": "USD 150,000–200,000",
  "job_type": "Full Time",
  "tags": [],
  "is_remote": false,
  "original_source": "LinkedIn",
  "emoji": "🤖",
  "description": "We are looking for an experienced Android Developer...\n\nRequirements:\n- 5+ years Android...",
  "created_at": "2025-03-29 10:30:00",
  "categories": ["android"]
}
```

---

### `GET /api/stats`
Returns job counts per category.

**Response:**
```json
{
  "total": 350,
  "categories": {
    "backend": 120,
    "frontend": 85,
    "android": 45,
    "ios": 40,
    "devops": 35,
    "ai_ml": 30,
    "qa": 20,
    "cybersecurity": 15,
    "internships": 10
  }
}
```

---

### `GET /health`
Health check endpoint.

**Response:** `{ "status": "ok", "total_jobs": 350 }`

---

## Architecture

```
Every 20 minutes (APScheduler):
  1. Fetch:     Get jobs from 15 API/RSS sources
  2. Filter:    Apply 327 include + 47 exclude keywords + geo filter
  3. Dedup:     Compare against DB (title+company AND URL)
  4. Categorize: Assign each job to 1+ of the 9 app categories
  5. Insert:    Save new jobs to SQLite
  6. Cleanup:   Delete jobs older than 5 days

Mobile App:
  → GET /api/categories  (onboarding)
  → GET /api/jobs         (infinite scroll, filtered by selected categories)
  → GET /api/jobs/{id}    (job detail with description)
```

## Project Structure

```
programming-jobs-api/
├── app.py                 # FastAPI + APScheduler entry point
├── api.py                 # 4 REST endpoints
├── database.py            # SQLite: tables, queries, cleanup
├── config.py              # Categories, keywords, geo patterns, API keys
├── models.py              # Job dataclass + filtering logic
├── category_router.py     # Classifies jobs → app categories
├── dedup.py               # Deduplication against DB
├── fetcher.py             # Background pipeline: fetch → filter → save
├── requirements.txt
├── sources/
│   ├── __init__.py        # ALL_FETCHERS registry (15 sources)
│   ├── http_utils.py      # Shared HTTP helpers
│   ├── remotive.py        # ✓ description
│   ├── himalayas.py       # ✓ description
│   ├── jobicy.py          # ✓ description
│   ├── remoteok.py        # ✓ description
│   ├── arbeitnow.py       # ✓ description
│   ├── wwr.py             # ✓ description (from RSS content)
│   ├── workingnomads.py   # ✓ description
│   ├── jsearch.py         # ✓ description (job_description)
│   ├── linkedin.py        # ✗ no description (search HTML only)
│   ├── adzuna.py          # ✓ description
│   ├── themuse.py         # ✓ description (contents field)
│   ├── findwork.py        # ✓ description (text field)
│   ├── jooble.py          # ✓ description (snippet)
│   ├── reed.py            # ✓ description (jobDescription)
│   └── usajobs.py         # ✓ description (QualificationSummary)
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `RAPIDAPI_KEY` | Recommended | JSearch API key (free tier) |
| `ADZUNA_APP_ID` | Optional | Adzuna app ID |
| `ADZUNA_APP_KEY` | Optional | Adzuna app key |
| `FINDWORK_API_KEY` | Optional | Findwork.dev API key |
| `JOOBLE_API_KEY` | Optional | Jooble API key |
| `REED_API_KEY` | Optional | Reed.co.uk API key |
| `DATABASE_PATH` | Optional | SQLite path (default: `jobs.db`) |

## Deployment

### Railway / Render
```bash
# Procfile or start command:
uvicorn app:app --host 0.0.0.0 --port $PORT
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```
