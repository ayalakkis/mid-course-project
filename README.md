# Task Tracker

A small Task Tracker built for the *AI-Assisted Coding* course: a FastAPI backend with an
in-memory data layer, and a vanilla HTML/CSS/JS Kanban frontend. Built across Modules 1-3;
extended for the mid-course project with two additional features (see below).

## Stack

- Python 3.11, FastAPI, Pydantic v2, Uvicorn
- pytest + httpx (TestClient) for backend tests
- Vanilla HTML/CSS/JavaScript frontend (no build step, no framework)

## Project structure

```
app/
  main.py            FastAPI app and routes
  models.py          Pydantic v2 request/response models
  storage.py         In-memory storage layer
  business_rules.py  Status-transition validation
frontend/
  index.html         Kanban board (fetch/render, drag-and-drop, modal)
tests/
  conftest.py        Fixtures (TestClient, storage reset, created_task)
  test_tasks.py       API test suite
  verify_a.py         Standalone model-verification script
scripts/
  browser_verify.py   Headless-browser (Playwright) UI verification, see below
docs/
  midcourse/          Mid-course project documentation (see below)
```

## Run the backend locally

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Verify it's running:

```bash
curl http://localhost:8000/health
# {"status":"ok","timestamp":"..."}
```

Swagger UI is available at http://localhost:8000/docs.

## Open the frontend

The frontend is a static file with no build step. With the backend running on port 8000,
open `frontend/index.html` directly in a browser, or serve it with any static server, e.g.:

```bash
cd frontend
python3 -m http.server 5500
# then open http://localhost:5500/index.html
```

`http://localhost:5500` and `http://127.0.0.1:5500` are already allowed by the backend's CORS
configuration in `app/main.py`; add your own local origin there if you serve the frontend
from a different port.

## Run tests

```bash
source venv/bin/activate
pytest tests/ -v
```

Model-only verification script (Module 2 style, checks validation/enum/extra-field rules
without going through the API):

```bash
python -m tests.verify_a
```

## Task Tracker scope

Included: create/view/update/delete tasks; filter by status and priority; status-transition
rules enforced server-side (ToDo -> InProgress -> Done -> InProgress; Done -> ToDo and
same-status "moves" are rejected).

Explicitly excluded (by course design): authentication, user accounts, multi-tenancy,
real-time updates, a production database, and deployment.

## Mid-course project: added features

This repo's `mid-course-project` branch adds two scoped features on top of the Modules 1-3
baseline:

1. **Due dates + overdue filter** - optional `due_date` on tasks, an `overdue` flag computed
   by the backend, and an `overdue=true` query filter on `GET /tasks`.
2. **Tags / labels** - an optional `tags` list on tasks (trimmed, non-empty, max 5 tags of
   up to 30 characters each), with an optional `tag=` query filter on `GET /tasks`.

Both features are visible in the Kanban UI (modal fields, card display, and filter
controls above the board).

See `docs/midcourse/` for user stories, the mini-ADR, the prompt log, verification evidence
(including Break Test proof), and the final reflection.

### Re-running the UI verification evidence

`docs/midcourse/screenshots/` and the manual-browser-check results in
`docs/midcourse/verification.md` were produced by driving the real frontend against the real
backend in headless Chromium, rather than by hand. To reproduce it:

```bash
pip install -r requirements-dev.txt
playwright install chromium   # only needed if you don't already have a Chromium install
uvicorn app.main:app --port 8000 &
python3 -m http.server 5500 --directory frontend &
python scripts/browser_verify.py
```

The script prints PASS/FAIL for each behavior-contract item and exits non-zero if any check
fails.

## Run with Docker

```bash
docker build -t task-tracker .
docker run --rm -p 8000:8000 task-tracker
curl http://localhost:8000/health
```

The image only contains the backend (`app/` + `requirements.txt`); the frontend is still a
plain static file, opened or served separately as described above. The container runs as a
non-root user and does not copy `.env`, tests, docs, or dev tooling - see `Dockerfile` and
`.dockerignore`.

## Final Project

Branch reviewed: `final-project`

### What this submission demonstrates

- The existing Task Tracker app still runs inside the intended course scope - no new
  product features were added on this branch.
- CI (`.github/workflows/ci.yml`) runs the pytest suite on every push and pull request.
- The Docker image builds and runs, and `/health` returns `200`.
- AI review, security, and ownership evidence is in `docs/release-evidence.md`,
  `docs/final-ai-review.md`, and `docs/ai-playbook.md`.

### How to run locally

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### How to run tests

```bash
pytest tests/ -v
```

### How to run with Docker

```bash
docker build -t task-tracker .
docker run --rm -p 8000:8000 task-tracker
curl http://localhost:8000/health
```

### Evidence files

- `docs/release-evidence.md`
- `docs/final-ai-review.md`
- `docs/ai-playbook.md`

### AI assistance summary

AI helped draft or review: the CI workflow, the Dockerfile, `AGENTS.md`, the release/AI-review
docs, and a read-only security pass over `app/` and the new release files.

I verified the work by: running the full pytest suite, hitting `/health` on both the local
`uvicorn` server and the built Docker container, re-running `scripts/browser_verify.py`
against the unchanged frontend, and reading every changed file myself before accepting it.

One AI suggestion I rejected or corrected: see `docs/final-ai-review.md#one-ai-output-i-rejected-or-corrected`.
