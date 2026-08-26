"""Pydantic v2 data models for the Task Tracker API.

Defines the enums and request/response models used across the API.
Server-managed fields (id, created_at, updated_at) are intentionally
excluded from client input models (TaskCreate, TaskUpdate).
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

MAX_TAGS = 5
MAX_TAG_LENGTH = 30


class TaskStatus(str, Enum):
    TODO = "ToDo"
    IN_PROGRESS = "InProgress"
    DONE = "Done"


class TaskPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


def _validate_title(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("Title is required and cannot be blank")
    if len(stripped) > 200:
        raise ValueError("Title must be 200 characters or fewer")
    return stripped


def _normalize_due_date(value: Optional[datetime]) -> Optional[datetime]:
    """Treat a due date with no timezone info as UTC.

    Client-supplied due dates should not be ambiguous. Pydantic already
    rejects a value that cannot be parsed as a datetime at all (HTTP 422);
    this only fills in a timezone when one was not provided, so overdue
    comparisons never raise on naive-vs-aware datetimes.
    """
    if value is None:
        return value
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _validate_tags(tags: Optional[list[str]]) -> Optional[list[str]]:
    """Trim each tag, reject blanks, and enforce count/length limits.

    Tags are kept in the case the client sent them (not lowercased):
    an earlier AI draft suggested normalizing to lowercase, but that was
    rejected because it silently rewrites what the user typed with no
    clear benefit for a single-list, no-autocomplete tag field at this
    project's scope. See docs/midcourse/mini-adr.md.
    """
    if tags is None:
        return tags
    if len(tags) > MAX_TAGS:
        raise ValueError(f"A task may have at most {MAX_TAGS} tags")
    cleaned: list[str] = []
    for tag in tags:
        stripped = tag.strip()
        if not stripped:
            raise ValueError("Tags cannot be blank")
        if len(stripped) > MAX_TAG_LENGTH:
            raise ValueError(f"Each tag must be {MAX_TAG_LENGTH} characters or fewer")
        cleaned.append(stripped)
    return cleaned


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: Optional[str] = ""
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: list[str] = Field(default_factory=list)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return _validate_title(value)

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, value: Optional[datetime]) -> Optional[datetime]:
        return _normalize_due_date(value)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str]) -> list[str]:
        return _validate_tags(value) or []


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: Optional[list[str]] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return _validate_title(value)

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, value: Optional[datetime]) -> Optional[datetime]:
        return _normalize_due_date(value)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        return _validate_tags(value)


class TaskResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    assignee: Optional[str]
    due_date: Optional[datetime] = None
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def overdue(self) -> bool:
        """True when due_date is in the past and the task is not Done.

        Computed at read/serialization time (not stored) so it always
        reflects the current time rather than the time the task was last
        written.
        """
        if self.due_date is None or self.status == TaskStatus.DONE:
            return False
        return self.due_date < datetime.now(timezone.utc)
