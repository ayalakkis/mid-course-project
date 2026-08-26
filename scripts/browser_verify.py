"""One-off headless-browser verification script for the mid-course project.

Not part of the pytest suite (backend logic is already covered there). This
script drives the real frontend/index.html in a real Chromium instance
against the running backend to produce genuine UI evidence for
docs/midcourse/verification.md: screenshots plus pass/fail lines.

Usage (with the backend running on :8000 and the frontend served on :5500):
    python scripts/browser_verify.py
"""

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

FRONTEND_URL = "http://localhost:5500/index.html"
SCREENSHOT_DIR = Path(__file__).resolve().parent.parent / "docs" / "midcourse" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

results: list[tuple[str, bool]] = []


def check(label: str, condition: bool) -> None:
    results.append((label, condition))
    print(f"{'PASS' if condition else 'FAIL'}: {label}")


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium", headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})

        page.goto(FRONTEND_URL)
        page.wait_for_selector(".board")
        time.sleep(0.5)
        page.screenshot(path=str(SCREENSHOT_DIR / "01-empty-board.png"))
        check("Board renders with three columns", page.locator(".column").count() == 3)
        check(
            "Empty board shows empty-column placeholders",
            page.locator(".empty-placeholder").count() == 3,
        )

        # ---- Create a High-priority task with a due date and tags ----
        page.click("#new-task-btn")
        page.fill("#field-title", "Ship the release notes")
        page.fill("#field-description", "Draft and send to the team")
        page.select_option("#field-priority", "High")
        page.fill("#field-assignee", "aya")
        page.fill("#field-due-date", "2000-01-01")  # deliberately in the past -> overdue
        page.fill("#field-tags", "backend, urgent")
        page.screenshot(path=str(SCREENSHOT_DIR / "02-modal-filled.png"))
        page.click("#save-btn")
        page.wait_for_timeout(500)
        page.screenshot(path=str(SCREENSHOT_DIR / "03-card-created.png"))

        card = page.locator(".card", has_text="Ship the release notes")
        check("Created card appears on the board", card.count() == 1)
        check("Card shows the High priority badge", card.locator(".priority-High").count() == 1)
        check("Card shows an overdue pill for a past due date", card.locator(".overdue-pill").count() == 1)
        check("Card shows tag chips for backend and urgent", card.locator(".tag-chip").count() == 2)

        # ---- Overdue filter ----
        page.click("#new-task-btn")
        page.fill("#field-title", "Not due yet")
        page.fill("#field-due-date", "2099-01-01")
        page.click("#save-btn")
        page.wait_for_timeout(500)

        page.check("#overdue-filter")
        page.wait_for_timeout(500)
        page.screenshot(path=str(SCREENSHOT_DIR / "04-overdue-filter.png"))
        visible_titles = page.locator(".card .card-title").all_inner_texts()
        check(
            "Overdue filter shows only the overdue task",
            visible_titles == ["Ship the release notes"],
        )
        page.uncheck("#overdue-filter")
        page.wait_for_timeout(500)

        # ---- Tag filter ----
        page.fill("#tag-filter", "backend")
        page.wait_for_timeout(600)
        page.screenshot(path=str(SCREENSHOT_DIR / "05-tag-filter.png"))
        visible_titles = page.locator(".card .card-title").all_inner_texts()
        check("Tag filter shows only tasks tagged backend", visible_titles == ["Ship the release notes"])
        page.fill("#tag-filter", "")
        page.wait_for_timeout(600)

        # ---- Drag and drop: ToDo -> InProgress (valid) ----
        source = page.locator(".card", has_text="Ship the release notes")
        source_box = source.bounding_box()
        target_column = page.locator('.column[data-status="InProgress"]')
        target_box = target_column.bounding_box()
        page.mouse.move(source_box["x"] + source_box["width"] / 2, source_box["y"] + 10)
        page.mouse.down()
        page.mouse.move(target_box["x"] + target_box["width"] / 2, target_box["y"] + 50, steps=10)
        page.mouse.up()
        page.wait_for_timeout(600)
        page.screenshot(path=str(SCREENSHOT_DIR / "06-after-drag-to-inprogress.png"))
        in_progress_titles = page.locator('[data-column="InProgress"] .card-title').all_inner_texts()
        check(
            "Valid drag (ToDo -> InProgress) moves the card and persists",
            "Ship the release notes" in in_progress_titles,
        )

        # ---- Drag InProgress -> Done (valid) ----
        source = page.locator(".card", has_text="Ship the release notes")
        source_box = source.bounding_box()
        done_column = page.locator('.column[data-status="Done"]')
        done_box = done_column.bounding_box()
        page.mouse.move(source_box["x"] + source_box["width"] / 2, source_box["y"] + 10)
        page.mouse.down()
        page.mouse.move(done_box["x"] + done_box["width"] / 2, done_box["y"] + 50, steps=10)
        page.mouse.up()
        page.wait_for_timeout(600)
        done_titles = page.locator('[data-column="Done"] .card-title').all_inner_texts()
        check("Valid drag (InProgress -> Done) moves the card", "Ship the release notes" in done_titles)

        # ---- Drag Done -> ToDo (invalid transition, should revert + show error) ----
        source = page.locator(".card", has_text="Ship the release notes")
        source_box = source.bounding_box()
        todo_column = page.locator('.column[data-status="ToDo"]')
        todo_box = todo_column.bounding_box()
        page.mouse.move(source_box["x"] + source_box["width"] / 2, source_box["y"] + 10)
        page.mouse.down()
        page.mouse.move(todo_box["x"] + todo_box["width"] / 2, todo_box["y"] + 50, steps=10)
        page.mouse.up()
        page.wait_for_timeout(600)
        page.screenshot(path=str(SCREENSHOT_DIR / "07-invalid-drag-reverted.png"))
        done_titles_after = page.locator('[data-column="Done"] .card-title').all_inner_texts()
        check(
            "Invalid drag (Done -> ToDo) reverts the card back to Done",
            "Ship the release notes" in done_titles_after,
        )
        check(
            "Invalid drag shows a server error message in the status banner",
            "invalid" in page.locator("#status-banner").inner_text().lower()
            or "rejected" in page.locator("#status-banner").inner_text().lower(),
        )

        # ---- Modal dismissal: Cancel, overlay click, Escape ----
        page.reload()
        page.wait_for_selector(".board")
        page.wait_for_timeout(300)

        page.click("#new-task-btn")
        page.fill("#field-title", "Should not be saved")
        page.click("#cancel-btn")
        check("Cancel button closes the modal", page.locator("#modal-overlay.hidden").count() == 1)

        page.click("#new-task-btn")
        page.click("#modal-overlay", position={"x": 5, "y": 5})
        check("Clicking the overlay closes the modal", page.locator("#modal-overlay.hidden").count() == 1)

        page.click("#new-task-btn")
        page.keyboard.press("Escape")
        check("Escape key closes the modal", page.locator("#modal-overlay.hidden").count() == 1)

        after_dismiss_titles = page.locator(".card-title", has_text="Should not be saved").count()
        check("Dismissed modal did not create a task", after_dismiss_titles == 0)

        # ---- Error state: backend unreachable ----
        page.route("**/tasks*", lambda route: route.abort())
        page.reload()
        page.wait_for_timeout(500)
        page.screenshot(path=str(SCREENSHOT_DIR / "08-error-state.png"))
        check(
            "Error state appears when the backend is unreachable",
            page.locator("#status-banner.error").count() == 1,
        )

        browser.close()
    return 0 if all(ok for _, ok in results) else 1


if __name__ == "__main__":
    sys.exit(main())
