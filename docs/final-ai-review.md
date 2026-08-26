# Final AI Review and Ownership Evidence

## AGENTS.md guardrails

- Repo-specific stack and commands included: yes (`AGENTS.md` "Stack" and "Commands" -
  Python/FastAPI/Pydantic/pytest/vanilla JS, plus the exact run/test/Docker commands).
- Docs-first/read-first guardrail included: yes (`AGENTS.md` "Read-first guardrail" -
  points at the existing `exclude_unset` PATCH pattern and the existing validator style
  so new fields extend a pattern instead of inventing one).
- Unexpected app/frontend edits rule included: yes (`AGENTS.md` "Protect `app/` and
  `frontend/`" - only small, explainable, documented fixes; everything else is scope
  creep).

## AI code review mini-log

Diff reviewed: this branch's new/changed files (`Dockerfile`, `.dockerignore`,
`.github/workflows/ci.yml`, `app/main.py`, `app/models.py`).

| AI comment | Grade | Reason | Verification or decision |
|---|---|---|---|
| Dockerfile has no `HEALTHCHECK`; add one so `docker ps`/an orchestrator can see the container is actually serving traffic, not just running. | Useful | Zero-risk, one line, matches the assignment's "runtime verification" ask. | Accepted - added a `HEALTHCHECK` using `python -c "urllib.request..."` (the slim image has no `curl`), interval 30s, 3 retries. |
| CI's `push`/`pull_request` triggers were set to `branches: ["**"]`, which double-runs the workflow on every PR from a branch in this same repo (once for the push, once for the PR). | Useful | Real cost (wasted Actions minutes), one-line fix, no behavior change to what gets tested. | Accepted - narrowed to the three branches actually in use (`main`, `mid-course-project`, `final-project`). |
| `python:3.11-slim` isn't pinned to a digest, so a rebuild months from now could pull a different underlying image. | Noise (for this project) | True in general, but this is a course checkpoint with no deployment target; digest-pinning adds a maintenance burden (bumping a hash by hand) disproportionate to the risk here, and `3.11-slim` is already a reasonably specific tag. | Rejected - noted here instead of acted on, so the reasoning is visible rather than silently ignored. |
| `AGENTS.md`'s "Read-first guardrail" restates a decision that's already in `docs/midcourse/mini-adr.md`, almost verbatim - could just link out. | Noise | `AGENTS.md` is meant to be read on its own by an agent that may not open every doc file first; a short self-contained restatement is more useful there than a citation-only link. | Rejected - kept the restatement, added the `mini-adr.md` reference alongside it rather than replacing it. |

## AI security mini-review

Read-only pass over `app/`, `Dockerfile`, `.dockerignore`, and `.github/workflows/ci.yml`.

| Finding | File evidence | Grade | Reason | Next action |
|---|---|---|---|---|
| `.dockerignore`'s `__pycache__/` pattern does **not** exclude nested directories (e.g. `app/__pycache__/`) - Docker's ignore-file matching isn't the same as `.gitignore`'s. | `.dockerignore` (before fix); reproduced with a throwaway `FROM scratch` build that copied `app/` and inspected the output - `app/__pycache__/models.cpython-311.pyc` was present in the build output. | Valid | Confirmed by an actual build, not just reading the file - stray `.pyc` files (or worse, an accidentally-generated `.env`-adjacent cache file) could ride into the image. | Fixed - changed to `**/__pycache__/`, `**/*.pyc`, etc.; re-ran the same scratch-image test and confirmed the directory no longer appears in the build output. |
| CORS `allow_methods=["*"]` and `allow_headers=["*"]` on a fixed, non-wildcard origin list is broader than the API needs. | `app/main.py` (before fix), CORS middleware config | Valid, low severity | The API only implements `GET/POST/PATCH/DELETE` on `/tasks*` and only ever receives a `Content-Type` header from this frontend; `"*"` doesn't add real risk here (origins are already restricted) but it's an easy, correct narrowing. | Fixed - explicit method/header lists; re-ran `scripts/browser_verify.py` (17/17 PASS) to confirm the real frontend still works with the narrower policy. |
| `description` and `assignee` had no length limit, while `title` (200 chars) and each `tag` (30 chars) already do - an inconsistency, and an unbounded string into an in-memory, never-evicted dict is a real (if low-severity, single-user-tool) memory-growth vector. | `app/models.py` (before fix) | Valid, low severity | Matches an existing validation pattern rather than inventing a new rule; doesn't change any documented behavior for normal-sized input. | Fixed - added `MAX_DESCRIPTION_LENGTH=2000` / `MAX_ASSIGNEE_LENGTH=100`, same style as the title/tag validators; added 4 tests (`test_create_task_description_over_limit_returns_422` and siblings), full suite still passes (31/31). |
| `requirements.txt` pins every dependency with `>=` only (e.g. `fastapi>=0.110`), so `pip install -r requirements.txt` can silently resolve a newer, potentially breaking version at any time, including in CI. | `requirements.txt` | Valid, deferred | Real supply-chain/reproducibility risk, but fixing it properly (lock file or `==` pins with a documented upgrade process) is an infrastructure decision bigger than a "small fix," and out of scope for this checkpoint. | Not fixed - recorded here as a known gap rather than silently left out. |
| `HTTPException(..., detail=f"Task with id {task_id} not found")` interpolates a client-supplied `task_id` into an error message - a naive pattern-matching scanner flags any f-string built from request input as a potential injection risk. | `app/main.py` (`get_task`, `patch_task`, `delete_task`) | False Positive | `task_id` is only ever returned as plain JSON text in an HTTP response; it is never rendered as HTML, executed, or used to build a query/command, so there is no actual injection path here. | No action - documented so the same non-issue isn't re-flagged and re-investigated later. |

## Manual security check

I didn't just take the `.dockerignore` finding above on faith from reading the file. A
lot of people (and a fair number of AI reviewers) assume `.dockerignore` matches nested
paths the same way `.gitignore` does - it doesn't always, depending on the pattern.
Rather than trust that assumption, I built a throwaway `FROM scratch` Dockerfile that
just does `COPY app/ /out/app/`, ran it with `docker build -o` to export the actual
build context Docker would send, and inspected the output directory by hand for a
`__pycache__` folder I'd deliberately created first. It was there - confirming the bug
for real rather than by inference. After the fix, I reran the exact same experiment and
confirmed the folder no longer appears in the exported output. I also manually skimmed
`.env.example` and `.gitignore` end to end (not via a scanner) to confirm the only
tracked env file is the placeholder (`PORT`, `APP_ENV` - no real values) and that `.env`
itself is ignored.

## One AI output I rejected or corrected

While narrowing the CORS `allow_methods` list (see the security table above), the
faster fix would have been to allow only the methods this particular frontend build
currently calls - `GET`, `POST`, `PATCH` - since a grep of `frontend/index.html` shows
no `DELETE` call today. I corrected that before applying it: `DELETE /tasks/{id}` is a
real, tested (`tests/test_tasks.py::test_delete_existing_returns_204_no_body` and
`test_delete_missing_returns_404`), documented (README "Task Tracker scope") part of
this API's contract, not dead code. Dropping it from CORS just because today's UI
doesn't happen to call it would have been an undocumented behavior change disguised as
a "security fix" - exactly the kind of change `AGENTS.md`'s "protect app/" rule and the
project's own "don't silently rewrite behavior nobody asked to change" pattern (see
`docs/midcourse/reflection.md`) warns against. I kept `DELETE` in the allowlist and
narrowed only the truly unused wildcard scope (`*` -> an explicit list).

## Three AI usage rules

1. **Never paste:** real credentials, `.env` values, tokens, production logs, or real
   personal/customer data into an AI tool or into this repo - only synthetic data
   (`aya`, `"Ship the release notes"`, etc.) ever appears in prompts, tests, or docs.
2. **Always verify:** a claim about behavior with an actual command - run the tests,
   hit the endpoint, build the image, read the diff - before writing it down as fact.
   Every "Fixed" row above has a re-run test/build attached to it, not just a stated
   intention.
3. **Record AI contributions by:** keeping the actual before/after (a failing check
   that then passes, a table row with a real grade and reason) rather than a generic
   "AI helped with security" sentence - see `docs/midcourse/prompt-log.md` for the same
   standard applied earlier in the course.

## Ownership statement

I'm comfortable submitting this repo as my own work because every claim in this
document traces to something I actually ran: the `.dockerignore` bug was caught by a
real build, not a guess; the CORS and length-limit fixes were verified against the
existing test suite and the real frontend (`scripts/browser_verify.py`, 17/17); and the
one CI/Dockerfile improvement I declined (dependency pinning) is recorded as a
conscious trade-off, not an oversight. I can explain every changed line in `app/`,
`Dockerfile`, `.dockerignore`, and `.github/workflows/ci.yml` in my own words, and the
one place I corrected an AI suggestion (keeping `DELETE` in CORS) came from checking the
actual test suite and README scope, not from a hunch. Nothing here was accepted because
it sounded plausible - it was accepted because I checked it.
