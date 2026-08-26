# Prompt Log — Mid-Course Project

This project was built with Claude working directly in the repository (a Claude Code–style
terminal/agentic workflow, the same category of tool introduced in Module 4). The prompts
below are the actual task specifications used to drive each implementation step, written the
way Module 1-3 teach it: role/context, task, constraints, output format. For each one, this
log records what Claude produced and what was accepted, edited, or rejected before it was
verified and committed.

## Feature 1: Due dates + overdue filter

### Prompt 1 — Design the field and the overdue rule (weak → strong)

**Weak version:**
> Add a due date to tasks.

**Why it's weak:** it doesn't say where `overdue` should be computed, whether it's stored or
derived, how it interacts with status, or what happens to naive vs. timezone-aware input —
exactly the kind of missing non-functional requirement Module 1 warns about.

**Strong version actually used:**
> You are extending the Module 2 Task Tracker models in `app/models.py`. Add an optional
> `due_date: datetime` field to `TaskCreate` and `TaskUpdate`, and to `TaskResponse`. Add a
> read-only `overdue: bool` on `TaskResponse` computed from `due_date` and `status` — do not
> store it. Constraints: a `Done` task must never read as overdue even if its due date has
> passed; a due date with no timezone must be treated as UTC, not compared naively against
> an aware "now" (that would raise `TypeError`); an unparseable due date must return HTTP 422
> through normal Pydantic validation, not a custom check. Output: the updated model file only.

**What Claude returned / what was accepted or corrected:** the first pass computed
`overdue` from `due_date < now` with no status check, matching the "AI assumption
corrected" flagged in `docs/midcourse/user-stories.md`. This was rejected and corrected to
exclude `Done` tasks. The timezone-normalization validator and the choice of
`@computed_field` (over a stored field) were accepted as proposed after inspecting that
`computed_field` output shows up correctly in the FastAPI response schema.

### Prompt 2 — Wire the overdue filter into the existing GET /tasks route

> Context: `GET /tasks` in `app/main.py` already filters by `status` and `priority` via
> `storage.get_all_tasks`. Add an `overdue: bool | None = None` query parameter to both the
> route and `get_all_tasks`, filtered the same way the existing filters are — do not change
> the existing status/priority filter behavior, and do not add a separate endpoint.

**Accepted as-is** after inspecting the diff confirmed the new filter followed the same
`if x is not None: results = [...]` pattern as the existing two filters, and manually
verified with `curl "http://localhost:8000/tasks?overdue=true"` against a mix of overdue and
non-overdue tasks (see `docs/midcourse/verification.md`).

### Prompt 3 — Diagnose an actual failure during testing

While writing `test_overdue_detection_true_for_past_due_todo_task_false_once_done`, the
first run of the test failed with `TypeError: can't compare offset-naive and offset-aware
datetimes` on a task created with a plain `"2000-01-01T00:00:00Z"` string.

> Here is the exact traceback: [pasted]. The due date was sent as an ISO string with a `Z`
> suffix. Diagnose whether this is a timezone-normalization bug in `_normalize_due_date` or
> a Pydantic parsing issue, and give the smallest fix.

**Root cause found and accepted:** `Z` was being parsed by Pydantic into an aware datetime
already, so the bug was actually in a task created *without* a timezone suffix elsewhere in
manual testing, not this specific test — Claude's diagnosis correctly pointed at
`_normalize_due_date`'s `if value.tzinfo is None` branch as the fix location, which was
already present and correct. The real issue was a stray manual curl test using a bad literal;
no source change was needed. This is recorded because Module 1/2 explicitly teach that not
every "it failed" moment is a code bug — sometimes the evidence shows the test input was
wrong, and the fix is to redo the check, not the code.

## Feature 2: Tags / labels

### Prompt 4 — Design tag validation (weak → strong)

**Weak version:**
> Let tasks have tags.

**Strong version actually used:**
> Add `tags: list[str]` to `TaskCreate` (default empty list) and `TaskResponse`, and
> `tags: list[str] | None` to `TaskUpdate` (`None` = don't touch, matching the existing
> `exclude_unset` PATCH pattern; `[]` explicitly clears tags). Constraints: trim each tag;
> reject a task with more than 5 tags; reject any tag over 30 characters; reject a blank tag
> (empty after trim) with HTTP 422. Do not lowercase or dedupe tags. Output: the updated
> model file, plus a one-line note on why lowercasing was or wasn't included.

**What was accepted vs. rejected:** Claude's first draft *did* lowercase tags "for
consistent filtering." That was explicitly rejected in this same turn — the constraint above
was added after seeing that first draft, specifically to stop it from rewriting user input.
The final version keeps tags as typed and instead makes the *filter* comparison
case-insensitive in `storage.get_all_tasks`, which was accepted after confirming both
`?tag=backend` and `?tag=Backend` match a task tagged `"backend"`.

### Prompt 5 — Case-insensitive tag filter without changing storage

> Add a `tag: str | None` query parameter to `GET /tasks` and `storage.get_all_tasks` that
> matches a task if any of its tags equals the given tag, case-insensitively. Do not change
> how tags are stored or returned — only the filter comparison should be case-insensitive.

**Accepted as-is.** Verified with three tasks (`"backend"`, `"frontend"`, no tags) and
`GET /tasks?tag=backend` returning exactly the one match — see
`docs/midcourse/verification.md`.

### Prompt 6 — Frontend tag input without a chip-editor widget

> Add a single text input to the modal for tags, comma-separated (e.g. "backend, urgent"),
> not a chip-based multi-select widget. Reasoning to follow: a full tag-chip input with
> autocomplete is more UI than this feature's scope calls for. Split the input on commas,
> trim each part, drop empty parts before sending to the API.

**Accepted, with one correction:** the first draft sent the raw comma-separated string
straight to the API and let the backend's blank-tag rejection catch trailing commas (e.g.
`"backend, "` producing `["backend", ""]`). That was corrected to filter out empty strings
client-side after splitting, so a trailing comma is silently ignored in the UI rather than
surfacing a confusing 422 for what looks like valid input.

## Notes on scope discipline

Every prompt above was scoped to one file or one route at a time, matching the Module 2/4
"one task per prompt" rule. No prompt in this project asked for both features at once, and
none touched `app/business_rules.py` (the status-transition rules), which the brief's ground
rules protect from unrelated changes.
