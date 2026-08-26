# Release Evidence

## Baseline

- Branch: `final-project` (branched from `mid-course-project`, which already carries the
  Modules 1-3 baseline plus the two mid-course features).
- Date: 2026-08-26.
- Local app run command: `uvicorn app.main:app --port 8000`.
- `/health` result: `HTTP 200`, `{"status":"ok","timestamp":"2026-08-26T10:24:21.935589+00:00"}`.
- Frontend check: served with `python3 -m http.server 5500 --directory frontend`; driven
  with the existing headless-browser script (`scripts/browser_verify.py`, real Chromium,
  real backend) rather than just eyeballing it - the Kanban board renders, and the
  create/edit modal flow (open -> fill -> save -> card appears) is confirmed working:
  **17/17 checks PASS** (full output: evidence run on 2026-08-26).
- Test command: `pytest tests/ -v`.
- Test result: **31 passed, 0 failed** (27 pre-existing from the mid-course branch + 4
  new tests added during this checkpoint's security pass - see "AI security
  mini-review" in `docs/final-ai-review.md`). No pre-existing or newly-introduced
  failures.

## CI evidence

- Workflow file: `.github/workflows/ci.yml`.
- Latest run link or note: pushed to `origin/final-project` on
  `github.com/ayalakkis/mid-course-project`; first Actions run completed successfully -
  https://github.com/ayalakkis/mid-course-project/actions/runs/32981345650
- Test command used by CI: `pytest tests/ -v` (same command as the local baseline above,
  after `pip install -r requirements.txt` on Python 3.11 - matches the local
  environment exactly, so a CI failure can't be explained away as "works on my machine").
- Shortcut check: no `continue-on-error`, no `|| true`, pytest is not skipped or made
  conditional, Python version is pinned (`3.11`, matching local), dependency
  installation is an explicit step (not assumed present on the runner). Verified by
  reading `.github/workflows/ci.yml` directly, not by trusting a description of it.

## Docker evidence

- **Status: build/run verified for real**, in a GitHub Codespace on `origin/final-project`
  (`docker --version`: `Docker version 29.3.0-1, build 5927d80`) - not the local machine,
  which has no Docker install, and not the earlier drafting sandbox, which blocked
  `registry-1.docker.io` outbound (`403 Forbidden` on the base-image pull - a network-egress
  restriction of that sandbox, not a problem with the `Dockerfile`).
- Build command: `docker build -t task-tracker .` - succeeded, final image
  `docker.io/library/task-tracker:latest` (259MB disk / 61.4MB content), `DONE 3.8s` for
  the export stage.
- Run command: `docker run -d --rm --name tt -p 8000:8000 task-tracker` - container started
  (id `378e6ed1d1b7`).
- `/health` check: `curl -s -w '\nHTTP_STATUS:%{http_code}\n' http://localhost:8000/health`
  -> `{"status":"ok","timestamp":"2026-08-26T14:46:52.892510+00:00"}` / `HTTP_STATUS:200`.
- Non-root check: confirmed by execing into the running container -
  `docker exec tt whoami` -> `appuser`; `docker exec tt id` ->
  `uid=1000(appuser) gid=1000(appuser) groups=1000(appuser)` - the process is not root.
- No-baked-secrets check: confirmed by execing into the running container -
  `find / -maxdepth 3 -iname '*.env*'` returned nothing, and `ls /app` shows only `app/`
  and `requirements.txt` - no `.env`, tests, docs, or scripts made it into the image.
- Cleaned up after verification: `docker stop tt` (container was `--rm`, so it was removed
  on stop); the Codespace used to run this was deleted afterward.

## Documentation claim-vs-reality log

| Claim checked | Evidence used | Result | Change made, if any |
|---|---|---|---|
| README: `GET /health` returns `{"status":"ok","timestamp":"..."}` with HTTP 200 | `curl -s -w "\nHTTP_STATUS:%{http_code}\n" http://localhost:8000/health` against a freshly started server | Confirmed exactly as documented | None |
| README/AGENTS.md: status transitions only allow `ToDo -> InProgress -> Done -> InProgress`; `Done -> ToDo` and same-status moves are rejected | `pytest tests/test_tasks.py -k "transition or same_status" -v` - both `test_patch_invalid_transition_todo_to_done_returns_422` and `test_patch_same_status_returns_422` pass | Confirmed | None |
| `.dockerignore`'s `__pycache__/` pattern excludes nested cache directories from the Docker build context (an assumption carried over from `.gitignore` habits) | Built a throwaway `FROM scratch` image copying `app/` (with a deliberately created `app/__pycache__/*.pyc`) and inspected the exported build output | **False** - the bare pattern only matched the context root; the nested file was copied in | Rewrote the Python section of `.dockerignore` to use `**/__pycache__/`, `**/*.pyc`, etc.; re-ran the same test and confirmed the file no longer appears in the build output |
| pytest suite size/result as stated in `docs/midcourse/verification.md` ("27 passed") still holds unchanged on this branch | `pytest tests/ -v` on `final-project` | **Outdated, not wrong** - now 31 passed (4 new tests added for the description/assignee length fix in this checkpoint) | Recorded the new count here rather than silently leaving the old "27" claim to stand uncontextualized |
