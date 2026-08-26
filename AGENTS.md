# AGENTS.md

Guardrails for any AI tool (or human) working in this repository. Read this file, the
root `README.md`, and `docs/midcourse/` before changing anything.

## Stack

- Python 3.11, FastAPI, Pydantic v2, Uvicorn (backend, `app/`)
- pytest + httpx `TestClient` (tests, `tests/`)
- Vanilla HTML/CSS/JavaScript, no build step, no framework (frontend, `frontend/index.html`)
- In-memory storage only (`app/storage.py`) - data does not persist across restarts, and
  there is no database to migrate or seed.

## Commands

```bash
# Backend, local
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Tests
pytest tests/ -v

# Frontend (static file, no build step)
cd frontend && python3 -m http.server 5500

# Docker
docker build -t task-tracker .
docker run --rm -p 8000:8000 task-tracker
curl http://localhost:8000/health
```

## Read-first guardrail

Before writing code, read the relevant existing pattern and follow it rather than
inventing a new one. Concretely: `app/main.py`'s PATCH route already uses Pydantic's
`exclude_unset` so a partial update only touches fields the client actually sent -
extend that pattern for any new optional field instead of writing bespoke None-handling.
Same idea for validation (`app/models.py` field validators) and status-transition rules
(`app/business_rules.py`) - check whether the rule you're about to add already has a
sibling rule nearby before writing a new one from scratch.

## Project rules

- **No new product features.** Do not add comments, authentication, a production
  database, notifications, or unrelated UI changes. This repo is being hardened and
  documented for the final-project checkpoint, not extended.
- **Protect `app/` and `frontend/`.** Only touch these for a small, explainable bug fix,
  security fix, or a correction backed by documentation. Any such change must be
  described in `docs/final-ai-review.md` (what changed, why, and what was verified).
- **No secrets or real personal data.** Never paste credentials, `.env` values, API
  tokens, production logs, or real personal/customer data into an AI tool or into this
  repo. `.env` is git-ignored; only `.env.example` (placeholder values) is tracked.
- **Do not silently rewrite user input.** Validators should reject bad input, not
  "helpfully" transform it (e.g. do not lowercase or reformat a field the user typed
  unless that was explicitly requested) - see `docs/midcourse/reflection.md` for why
  this rule exists.
- **State transitions are the one business rule that matters.** `ToDo -> InProgress ->
  Done -> InProgress` is allowed; `Done -> ToDo` and same-status moves are rejected
  server-side. Don't loosen this without updating `app/business_rules.py`,
  `tests/test_tasks.py`, and the docs together.
- **You own the result.** If you can't explain a changed line, a command, a config
  choice, or an AI suggestion in your own words, don't submit it as final work.

## Before finishing any change

1. Run `pytest tests/ -v` - it must pass, or a failure must be recorded as expected and
   explained.
2. If you touched `app/` or `frontend/`, re-run `python scripts/browser_verify.py`
   (needs the backend on `:8000` and frontend on `:5500`) to confirm the UI contract
   still holds.
3. Record what you changed and why in the relevant `docs/` file - undocumented changes
   are treated as not done.
