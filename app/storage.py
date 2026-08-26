"""In-memory storage layer for the Task Tracker API.

Uses a module-level dictionary. Not persistent across restarts; this is
intentional for Modules 1-3 scope (no database yet).
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from app.models import TaskCreate, TaskPriority, TaskResponse, TaskStatus, TaskUpdate

_tasks: dict[str, TaskResponse] = {}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def add_task(payload: TaskCreate) -> TaskResponse:
    task_id = str(uuid.uuid4())
    now = _now()
    task = TaskResponse(
        id=task_id,
        title=payload.title,
        description=payload.description or "",
        status=payload.status,
        priority=payload.priority,
        assignee=payload.assignee,
        created_at=now,
        updated_at=now,
    )
    _tasks[task_id] = task
    return task


def get_all_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
) -> list[TaskResponse]:
    results = list(_tasks.values())
    if status is not None:
        results = [t for t in results if t.status == status]
    if priority is not None:
        results = [t for t in results if t.priority == priority]
    return results


def get_task_by_id(task_id: str) -> Optional[TaskResponse]:
    return _tasks.get(task_id)


def update_task(task_id: str, payload: TaskUpdate) -> Optional[TaskResponse]:
    existing = _tasks.get(task_id)
    if existing is None:
        return None
    updates = payload.model_dump(exclude_unset=True)
    updated = existing.model_copy(update=updates)
    updated.updated_at = _now()
    _tasks[task_id] = updated
    return updated


def delete_task(task_id: str) -> bool:
    if task_id in _tasks:
        del _tasks[task_id]
        return True
    return False


def _reset() -> None:
    """Clear all stored tasks. Used only by tests."""
    _tasks.clear()
