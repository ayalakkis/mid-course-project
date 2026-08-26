# Reflection — Mid-Course Project

For this checkpoint I worked with Claude directly inside the repository, in an agentic
terminal-style session rather than copy-pasting between a separate chat window and my editor
— closer to the Claude Code workflow Module 4 previews than the browser-based Module 1
workflow. I used it for the full loop on both features: drafting the model changes, writing
the pytest cases, wiring the frontend fields, and running the actual verification commands
(pytest, curl, and a headless-browser script) rather than just asking it to describe what the
code should do.

One moment it clearly helped: getting the status-quo-safe PATCH semantics right for the new
`tags` field. I hadn't thought through that `tags: None` needs to mean "leave tags alone" on
a partial update, while `tags: []` needs to mean "clear them," until it was pointed out that
this is the same `exclude_unset` pattern the Module 2 PATCH route already uses for every
other field. Reusing an existing pattern instead of inventing a new one for tags was the
right call, and I would not have automatically extended past behavior to a new field without
that connection being made explicit.

One moment it slowed things down, in a way that turned out to be worth it: the first draft of
the tag validator silently lowercased every tag "for consistent filtering." It took an extra
pass — noticing that this rewrites input the user typed for no requested reason — to reject
it and ask for the alternative (keep tags as typed, make the *filter* comparison
case-insensitive instead). That's a small change, but it's exactly the kind of quiet
assumption the course keeps warning about: technically reasonable-sounding, not something I
asked for, easy to miss on a quick read of a passing test suite.

The place my review changed the actual result the most was the overdue rule. The first
version flagged any task with a past due date as overdue, full stop. Sitting with the Kanban
board for a second — a task sitting in the Done column with a red "Overdue" pill — made it
obvious that wasn't right before it ever reached a test. That correction (exclude `Done` from
the overdue check) is now the one line in `app/models.py` I'd point to as the actual design
decision in this feature, not the field definition around it.
