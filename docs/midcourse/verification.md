# Verification — Mid-Course Project

## Baseline (before any mid-course changes)

- Branch at baseline: `main`, commit `55f5c0c` ("Baseline Task Tracker...").
- Backend start command: `uvicorn app.main:app --reload --port 8000`.
- `GET /health` → `HTTP 200`, `{"status":"ok","timestamp":"..."}`.
- `POST /tasks` with a valid body → `HTTP 201` with the created task.
- Baseline pytest run (17 tests, all from Modules 1-2): **17 passed**, 0 failed.
- Branch `mid-course-project` created from this exact baseline commit before any feature
  work started.

## Backend test results after each feature

| Stage | Command | Result |
|---|---|---|
| Baseline | `pytest tests/ -v` | 17 passed |
| After Feature 1 (due dates) | `pytest tests/ -v` | 22 passed (17 baseline + 5 new) |
| After Feature 2 (tags) | `pytest tests/ -v` | 27 passed (22 + 5 new) |
| Final, after refactor | `pytest tests/ -v` | 27 passed, 0 failed |

New tests added (10 total, more than the required minimum of 4):

- `test_create_task_valid_due_date_returns_201_and_not_overdue`
- `test_create_task_invalid_due_date_format_returns_422`
- `test_overdue_detection_true_for_past_due_todo_task_false_once_done`
- `test_patch_updates_due_date`
- `test_filter_overdue_returns_only_overdue_tasks`
- `test_create_task_with_tags_returns_201_with_trimmed_tags`
- `test_create_task_with_blank_tag_returns_422`
- `test_patch_updates_tags`
- `test_filter_by_tag_returns_only_matching_tasks`
- `test_tags_preserved_after_unrelated_update`

## Manual backend checks (curl, live server)

```
POST /tasks {"title":"Overdue demo","due_date":"2000-01-01T00:00:00Z"}   -> 201, overdue:true
POST /tasks {"title":"Future demo","due_date":"2099-01-01T00:00:00Z"}    -> 201, overdue:false
GET  /tasks?overdue=true                                                 -> 200, only "Overdue demo"
POST /tasks {"title":"Bad date","due_date":"nope"}                       -> 422
POST /tasks {"title":"Tag demo","tags":[" backend ","urgent"]}           -> 201, tags:["backend","urgent"]
POST /tasks {"title":"Bad tag","tags":["ok","   "]}                      -> 422
GET  /tasks?tag=backend                                                  -> 200, only "Tag demo"
```

## Manual browser checks

Rather than only describing manual clicks, this project drives the real frontend against the
real backend with a headless Chromium browser (`scripts/browser_verify.py`, Playwright) and
saves screenshots as evidence in `docs/midcourse/screenshots/`. This is the same kind of
DevTools/browser evidence Module 3 asks for, made reproducible: run
`python scripts/browser_verify.py` with the backend on `:8000` and the frontend served on
`:5500` to regenerate it.

Checks performed and result (all PASS on the final code):

1. Board renders with three columns — PASS
2. Empty board shows empty-column placeholders — PASS
3. Created card (title, description, High priority, assignee, due date, tags) appears — PASS
4. Card shows the High priority badge — PASS
5. Card shows an overdue pill for a past due date — PASS
6. Card shows tag chips for its tags — PASS
7. "Overdue only" filter shows only the overdue task — PASS
8. Tag filter shows only tasks with the matching tag — PASS
9. Valid drag ToDo → InProgress moves the card and persists via PATCH — PASS
10. Valid drag InProgress → Done moves the card — PASS
11. Invalid drag Done → ToDo reverts the card back to Done — PASS
12. Invalid drag shows a server error message in the status banner — PASS
13. Cancel button closes the modal — PASS
14. Clicking the overlay closes the modal — PASS
15. Escape key closes the modal — PASS
16. A dismissed modal does not create a task — PASS
17. Error state (banner + Retry button) appears when the backend is unreachable — PASS

Screenshots: `01-empty-board.png`, `02-modal-filled.png`, `03-card-created.png`,
`04-overdue-filter.png`, `05-tag-filter.png`, `06-after-drag-to-inprogress.png`,
`07-invalid-drag-reverted.png`, `08-error-state.png`.

## Behavior contract before / after refactor

A focused refactor was made to `frontend/index.html`: the repeated
`document.getElementById(...).value = ...` blocks in `openModal()` and `saveTask()` (made
longer once due-date and tags fields were added) were extracted into `populateForm()`,
`formValuesFromTask()`, and `readFormValues()` helpers. No behavior was intended to change.

The full 17-item contract above was run once **before** the refactor and once **after**,
against the same fresh backend state:

- Before refactor: 17/17 PASS (`contract-before-refactor` run).
- After refactor: 17/17 PASS, identical results (`contract-after-refactor` run).

Git history for the checkpoint-then-refactor sequence:

```
5493530 Refactor: extract populateForm/readFormValues helpers ... (no behavior change; contract re-verified)
c22f6c7 Add mid-course docs scaffolding, browser verification script, and screenshots
d0301ac Add tags/labels feature (backend model/storage/query, tests, frontend modal/card/filter)
c4d80b5 Add due dates + overdue filter feature (backend model/storage/query, tests, frontend modal/card/filter)
55f5c0c Baseline Task Tracker: FastAPI CRUD backend, status-transition rules, pytest suite, Kanban frontend (Modules 1-3)
```

## Break Test evidence (at least two tests)

**Break Test 1 — overdue detection (`app/models.py::TaskResponse.overdue`)**

- Break introduced: replaced the real overdue logic with `return False` unconditionally.
- Tests expected to fail: `test_overdue_detection_true_for_past_due_todo_task_false_once_done`,
  `test_filter_overdue_returns_only_overdue_tasks`.
- Actual result: both failed as expected —
  `test_overdue_detection...` failed asserting `True` but got `False`;
  `test_filter_overdue_returns_only_overdue_tasks` failed with an assertion diff showing the
  expected `['Overdue']` list came back empty. `test_create_task_valid_due_date_returns_201_and_not_overdue`
  still passed (it only asserts `overdue is False`, which a broken "always False" happens to
  satisfy — expected, since that test alone can't distinguish real detection from a stub).
- Source restored; reran `pytest tests/test_tasks.py -k overdue -v` → 3 passed, 0 failed.

**Break Test 2 — blank-tag validation (`app/models.py::_validate_tags`)**

- Break introduced: removed the `if not stripped: raise ValueError(...)` blank-tag check.
- Test expected to fail: `test_create_task_with_blank_tag_returns_422`.
- Actual result: failed as expected — `assert response.status_code == 422` got `201`
  instead (`assert 201 == 422`), proving the test actually protects the blank-tag rule rather
  than passing regardless of the source.
- Source restored; reran the full suite → 27 passed, 0 failed, and `diff` confirmed
  `app/models.py` matched its pre-break-test state exactly.

## Final state

- `pytest tests/ -v` → **27 passed**, 0 failed, 0 skipped.
- `git status --short` on tracked files → clean (only new `docs/` and `scripts/` content
  added, no stray modifications left from the Break Tests).
- Frontend loads against the backend with no console errors observed during the Playwright
  run (script exits 0 only when every check passes).
