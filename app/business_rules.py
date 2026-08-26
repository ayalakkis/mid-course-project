"""Status-transition business rules for the Task Tracker.

The backend is the trusted enforcement point for status transitions:
a UI can hide invalid buttons, but a client could still call the API
directly, so the rule must live here.
"""

from fastapi import HTTPException, status

from app.models import TaskStatus

VALID_TRANSITIONS: frozenset[tuple[TaskStatus, TaskStatus]] = frozenset(
    {
        (TaskStatus.TODO, TaskStatus.IN_PROGRESS),
        (TaskStatus.IN_PROGRESS, TaskStatus.DONE),
        (TaskStatus.DONE, TaskStatus.IN_PROGRESS),
    }
)


def validate_status_transition(current: TaskStatus, new: TaskStatus) -> None:
    """Raise HTTP 422 if (current, new) is not an allowed transition.

    Same-status "transitions" are intentionally invalid (no-op moves are
    rejected), and only the three pairs above are otherwise allowed.
    """
    if (current, new) not in VALID_TRANSITIONS:
        allowed = sorted(f"{f.value}->{t.value}" for f, t in VALID_TRANSITIONS)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Invalid status transition from {current.value} to {new.value}. "
                f"Allowed transitions: {allowed}"
            ),
        )
