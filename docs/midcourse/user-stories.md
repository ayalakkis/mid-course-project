# Mid-Course Project — User Stories

Two features were added to the Task Tracker built in Modules 1-3: **due dates + overdue
filter** and **tags / labels**. Both were reviewed against the existing Task Tracker scope
(no auth, no database, no unrelated UI changes) before implementation.

## Feature 1: Due dates + overdue filter

**Story 1 — Set a due date when creating a task**
As a team member, I want to give a task a due date so that I know when it needs to be
finished.
- Acceptance criteria:
  - The create/edit modal has an optional due-date field.
  - A task can be created with no due date (`due_date` is `null`).
  - A due date that is not a valid date is rejected with HTTP 422.

**Story 2 — See at a glance which tasks are late**
As a team member, I want overdue tasks to be visibly marked so that I can prioritize them.
- Acceptance criteria:
  - A task whose due date is in the past shows an "Overdue" pill on its card.
  - A task with no due date, or a due date in the future, never shows the pill.
  - A task that is already Done does not show the pill even if its due date has passed.

**Story 3 — Update a task's due date**
As a team member, I want to change a task's due date so that I can reschedule it.
- Acceptance criteria:
  - `PATCH /tasks/{id}` accepts a `due_date` field on its own, without requiring other
    fields to be resent.
  - The updated due date is reflected immediately in the response and on the card.

**Story 4 — Filter the board to only overdue work**
As a team member, I want to filter the task list to overdue tasks only so that I can focus
on what is late.
- Acceptance criteria:
  - `GET /tasks?overdue=true` returns only tasks currently overdue.
  - The frontend has an "Overdue only" checkbox that applies the same filter.
  - Turning the filter off restores the full board.

**AI assumption corrected:** the first draft of the `overdue` logic flagged a task as
overdue purely from `due_date < now`, with no regard for status. That would have shown a
"Done" task with a past due date as still overdue on the board, which is misleading for a
team member scanning the columns — a finished task isn't "late" anymore. The rule was
corrected to exclude `Done` tasks from the overdue computation (see
`app/models.py::TaskResponse.overdue` and `docs/midcourse/mini-adr.md`).

## Feature 2: Tags / labels

**Story 5 — Label a task with one or more tags**
As a team member, I want to add short tags to a task so that I can group related work.
- Acceptance criteria:
  - The create/edit modal has a comma-separated tags input.
  - Each tag is trimmed of surrounding whitespace before saving.
  - A task can have zero tags.

**Story 6 — Reject junk tag input**
As a team member, I want the system to reject blank or excessive tags so that the tag list
stays useful.
- Acceptance criteria:
  - A blank tag (empty after trimming) is rejected with HTTP 422.
  - More than 5 tags on one task is rejected with HTTP 422.
  - A single tag longer than 30 characters is rejected with HTTP 422.

**Story 7 — See tags on the board**
As a team member, I want to see a task's tags on its card so that I don't have to open the
task to know what it relates to.
- Acceptance criteria:
  - Tags render as small chips on the card, in the order they were saved.
  - A task with no tags shows no tag row (no empty chip container).

**Story 8 — Filter the board by tag**
As a team member, I want to filter tasks by a single tag so that I can see just that group
of work.
- Acceptance criteria:
  - `GET /tasks?tag=backend` returns only tasks that have that tag (case-insensitive match).
  - The frontend has a tag filter input above the board that applies the same filter.
  - Clearing the filter restores the full board.

**AI assumption corrected:** the first draft of the tag validator normalized every tag to
lowercase before storing it. That was rejected — silently rewriting what the user typed
(e.g. "API" becoming "api") has no real benefit for a single free-text tag field with no
autocomplete or canonical tag list at this project's scope, and it would surprise a user who
typed a tag in a specific case for a reason. Tags are now stored exactly as typed, only
trimmed; the tag *filter* still compares case-insensitively so `?tag=Backend` and
`?tag=backend` both match a task tagged `"backend"`.
