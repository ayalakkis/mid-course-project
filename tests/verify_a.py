"""Module 2 Part 2.1 model-verification script.

Run with: python -m tests.verify_a
Prints PASS/FAIL for each check on the models/storage layer.
"""

from pydantic import ValidationError

from app.models import TaskCreate, TaskUpdate


def check(label: str, condition: bool) -> None:
    print(f"{'PASS' if condition else 'FAIL'}: {label}")


def main() -> None:
    # 1. Whitespace title rejected.
    try:
        TaskCreate(title="   ")
        check("Whitespace title rejected", False)
    except ValidationError:
        check("Whitespace title rejected", True)

    # 2. Empty title rejected.
    try:
        TaskCreate(title="")
        check("Empty title rejected", False)
    except ValidationError:
        check("Empty title rejected", True)

    # 3. Title over 200 characters rejected.
    try:
        TaskCreate(title="x" * 201)
        check("Title over 200 characters rejected", False)
    except ValidationError:
        check("Title over 200 characters rejected", True)

    # 4. Defaults applied: status ToDo, priority Medium, empty description.
    task = TaskCreate(title="Sample")
    check(
        "Defaults applied (status=ToDo, priority=Medium, description='')",
        task.status.value == "ToDo" and task.priority.value == "Medium" and task.description == "",
    )

    # 5. Extra field rejected on TaskCreate.
    try:
        TaskCreate(title="Sample", extra_field="nope")  # type: ignore[call-arg]
        check("Extra field rejected on TaskCreate", False)
    except ValidationError:
        check("Extra field rejected on TaskCreate", True)

    # 6. id rejected on TaskCreate.
    try:
        TaskCreate(title="Sample", id="123")  # type: ignore[call-arg]
        check("id rejected on TaskCreate", False)
    except ValidationError:
        check("id rejected on TaskCreate", True)

    # 7. created_at rejected on TaskUpdate.
    try:
        TaskUpdate(created_at="2024-01-01T00:00:00Z")  # type: ignore[call-arg]
        check("created_at rejected on TaskUpdate", False)
    except ValidationError:
        check("created_at rejected on TaskUpdate", True)

    # 8. Invalid status rejected.
    try:
        TaskCreate(title="Sample", status="NotAStatus")  # type: ignore[arg-type]
        check("Invalid status rejected", False)
    except ValidationError:
        check("Invalid status rejected", True)


if __name__ == "__main__":
    main()
