# Mini-ADR — Mid-Course Project Features

## Context

The Task Tracker from Modules 1-3 supports create/view/update/delete with status and
priority only. The mid-course brief asks for two small, end-to-end features on top of that,
each touching backend validation, storage, tests, and the frontend. The two chosen were
**due dates + overdue filter** and **tags / labels** — both scoped small enough to finish
end-to-end with real verification, and both visible in the Kanban UI as the brief requires.

## Decision

- **Due dates**: add an optional `due_date: datetime` field to `TaskCreate`/`TaskUpdate`,
  stored on `TaskResponse`. `overdue` is **not** a stored field — it's a Pydantic
  `@computed_field` property evaluated at serialization time from `due_date` and `status`.
  `GET /tasks` gained an `overdue: bool | None` query parameter, filtered in
  `storage.get_all_tasks` alongside the existing `status`/`priority` filters.
- **Tags**: add a `tags: list[str]` field (default `[]`) to `TaskCreate`/`TaskResponse`, and
  `tags: list[str] | None` to `TaskUpdate` (so `None` means "don't touch tags" under the
  existing `exclude_unset` PATCH semantics, while `[]` explicitly clears them). Validation
  trims each tag, rejects blanks, and caps the list at 5 tags of 30 characters each.
  `GET /tasks` gained a `tag: str | None` query parameter with a case-insensitive match.

## Alternatives considered

- **Compute `overdue` in the frontend instead of the backend.** Rejected: the backend
  already owns all task business rules (see the Module 2 status-transition rules), and the
  overdue *filter* (`GET /tasks?overdue=true`) has to run server-side anyway since the
  frontend only ever sees whatever page of tasks the backend returns. Computing it twice
  (once server-side for filtering, once client-side for display) would let the two
  definitions drift apart. One computed property, read by both the filter and the response
  body, is the smaller and safer design.
- **Store `overdue` as a persisted boolean, updated on write.** Rejected: it would go stale
  the moment time passes without a write to that task (a task due yesterday should read as
  overdue today even if nobody touched it since last week). A computed field recalculated on
  every read has no staleness problem and needed no extra migration/backfill logic.
- **Model tags as a separate `Tag` resource with its own id/color, or a tags table.**
  Rejected as out of scope — the brief explicitly excludes new product surfaces beyond the
  two chosen features, and the course's storage layer is intentionally an in-memory dict, not
  a relational model. A plain `list[str]` field on the task is the smallest change that
  satisfies the acceptance criteria (create with tags, filter by tag, chips on the card).
- **Auto-lowercase tags for consistency.** Rejected — see
  `docs/midcourse/user-stories.md`'s "AI assumption corrected" note for Feature 2. Tags are
  kept exactly as typed; only the filter comparison is case-insensitive.
- **Let the frontend send raw comma-separated tag text to the backend** and validate/split
  it there. Rejected — the API already accepts a list for other structured fields, and
  parsing a raw string into tags is a presentation-layer concern that belongs in the
  frontend's `saveTask()`, not in the API contract.

## Trade-offs

- Computing `overdue` at read time means it's slightly more CPU work per response than
  reading a stored boolean, which is irrelevant at this project's scale (in-memory dict,
  no persistence) but would need revisiting for a real database-backed version.
- Capping tags at 5 of 30 characters is a judgment call, not something the brief specifies
  numerically. It was picked to keep the tag row on a card readable without wrapping into
  the rest of the card, and documented explicitly rather than left as a "reasonable default"
  the grader has to infer.
- The tag filter is single-tag (`?tag=backend`), not `AND`/`OR` across multiple tags. The
  brief's "Search + combined filters" is a separate, unselected feature option — extending
  tag filtering to multiple tags at once was left out to keep this feature scoped small
  enough to finish end-to-end, per the brief's own guidance that a smaller, fully verified
  feature beats an ambitious partial one.

## Consequences

- `TaskResponse` now has two new fields (`due_date`, `tags`) plus the computed `overdue`
  field; any other client of this API (there are none yet) would need to tolerate the new
  fields, which is safe since they're additive and optional.
- The existing 17 Module 1-3 tests needed no changes — `due_date` and `tags` are optional
  with safe defaults, so none of the original CRUD/business-rule behavior changed. This was
  confirmed by rerunning the full suite after each feature (see
  `docs/midcourse/verification.md`).
- The frontend modal grew two more fields; `frontend/index.html` was refactored once
  (`populateForm`/`readFormValues` helpers) specifically because those two new fields made
  the old copy-pasted `document.getElementById(...).value = ...` blocks long enough to be
  worth deduplicating.

## Open question carried into the reflection

Whether `overdue` should also consider a grace period (e.g. "due today" is not yet
"overdue") was raised while implementing Story 2, but left out — the brief's feature
description says "overdue," not "due soon," and adding a second computed state would widen
the feature beyond what was scoped for this checkpoint.
