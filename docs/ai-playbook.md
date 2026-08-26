# My AI Playbook

*(Draft written from this course's actual sessions - see the note at the end. Read it
and edit anything that doesn't sound like you before you submit it.)*

## When I reach for AI first

Scaffolding I already know the shape of but don't want to type by hand: a CRUD route,
a Pydantic model, a pytest fixture, a Dockerfile for a stack I've containerized before.
Also anything with a fast, checkable answer - "does this endpoint return 422 or 404
here," "does this regex match" - where I can verify the answer in one command instead
of reasoning it out by hand. And repetitive review passes: reading a diff for the third
time looking for the same class of mistake (silently rewritten input, a validation rule
that doesn't match its sibling field) is exactly the kind of thing I'd rather have
flagged for me and then check myself.

## When I do not reach for AI first

Anything where the "obvious" fix changes behavior nobody asked to change - status rules,
what counts as overdue, what a filter matches. Those I work out on paper (or on the
actual UI) first, because the two biggest corrections I've had to make this course
(lowercasing tags I never asked to lowercase, calling a Done task overdue) were both
cases where the AI's first draft was internally consistent and still wrong. I also don't
start with AI for anything touching git/repo structure I don't already understand -
the nested-repo/submodule mixup that broke my GitHub submission came from running
commands without knowing what they'd do, not from AI giving bad advice.

## My non-negotiables

- Never paste real credentials, `.env` values, tokens, production logs, or real
  personal/customer data into an AI tool or a prompt - only synthetic data.
- Never accept a change to `app/` or `frontend/` I can't explain in one sentence.
- Never let a "cleaner"-looking rewrite change behavior I didn't ask to change.
- Every claim in a doc I submit gets checked against something real (a command, a test,
  a running server) before I write it down - "I checked it" always names what I ran.

## My review rules

I read the diff before I read the summary of the diff. For anything touching validation
or a business rule, I run the existing tests first, then write a new one that would have
caught the specific thing I'm worried about, then make sure it actually fails before the
fix and passes after. For anything infrastructure-shaped (CI, Docker), I don't trust a
description of what it does - I run it, or in this course's case, honestly, that also
means: if I can't run it (like Docker Hub being blocked in a sandbox), the doc says so
instead of pretending it passed. When I grade an AI finding, "sounds right" isn't a
grade - I need a file, a command, or a test result attached before it counts as Valid.

## What I am still figuring out

How much dependency-pinning discipline (lock files, hash-pinning) is worth the ongoing
maintenance cost on a small solo project versus a team one - I deferred that finding in
this checkpoint rather than resolve it. Also still figuring out where the line is
between "small security fix I can make to app/ without asking" and "this needs a real
conversation before I touch protected code" - the CORS/length-limit changes in this
checkpoint felt clearly on the small-fix side, but I don't have a crisp rule for the
next one yet.

## Decision Card

| Situation | My one rule |
|---|---|
| New feature | Don't build it if it's not asked for, even if AI offers to. |
| Code review | Grade every comment (Useful/Noise/Wrong) with a reason before acting on it - "helpful-sounding" isn't a reason. |
| Debugging | Reproduce it first, fix it second - never patch a symptom I haven't confirmed matches the actual failure. |
| Infrastructure (CI/Docker) | Don't write down that it works until I've actually run it - "should work" is not evidence. |
| Never paste | Real credentials, `.env` values, tokens, logs, or personal/customer data - synthetic data only. |

---

*Note on how this draft came to exist: I (Claude) wrote this first pass by looking back*
*at the real corrections that happened across this course's sessions - the tag-*
*lowercasing rejection, the Done/overdue fix, the nested-git-repo submission bug, and*
*this checkpoint's CORS/dockerignore findings - rather than writing generic AI-safety*
*language. It's meant as a starting point that's already grounded in your actual work,*
*not a finished, submit-as-is document - the assignment specifically wants this to*
*sound like you, so read it, cut anything that doesn't, and add anything it's missing*
*before this goes in.*
