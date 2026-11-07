---
name: plan-ticket
description: >
  Plans a feature before any code is written: turns an implementation request into a Jira-ready
  ticket in Markdown with a user story, scope, and numbered Given/When/Then acceptance criteria
  (happy path, edge cases, error states, non-functional), agreed with the user question by
  question. Use whenever the user asks to implement, add, build or change a feature or behavior
  in any project of this repo ("implement X", "add an endpoint for Y", "make Z handle W"), or
  asks for acceptance criteria, a user story or a Jira ticket. Planning only: it stops at the
  ticket and does not write tests or production code.
---

# Plan Ticket

Input: a request to implement something. Output: **one Markdown file that reads as a Jira ticket**: user story, context, scope and acceptance criteria (ACs) in Given/When/Then. The user reviews it, keeps it, and develops from it later.

## Rules that override everything else

1. **Plan, don't build.** Do not write tests, production code or config while running this skill. The only file you write is the ticket.
2. **Don't invent requirements.** Every business rule in an AC comes from the request, the code, the project docs or an answer from the user. Anything you had to guess goes under *Assumptions* in the ticket, marked as such.
3. **Ask when in doubt.** If the answer would change an AC, ask the user (see step 3) instead of picking silently.
4. **ACs describe behavior, not implementation.** Observable outcomes only (API responses, returned values, stored state, logged events). Function names, files and data structures are decided during development, not in the ticket.
5. **Language follows the user.** Write the whole ticket (headings, Given/When/Then keywords, prose) in the language of the user's request (Spanish: *Dado / Cuando / Entonces / Y*). Code identifiers, paths and commands stay as they are.

Read `references/writing-acs.md` before drafting ACs.

## Workflow

1. **Find the scope.** Work out which project folder the request belongs to (each top-level folder of the repo is independent) and read its `AGENTS.md` / `CLAUDE.md` / `README.md`, plus the one in the subfolder the change touches. Follow the project's own rules. In `travel-agency/` ("same as in class"), read **all** the references listed in the phase's row of `travel-agency/AGENTS.md`: the ACs must fit the class pattern, and anything that differs is listed as a **deviation** in the ticket. If the phase has no reference in the repo, say so and ask before going on.
2. **Explore what exists.** Read the code the change touches and its current tests. Note what already works, so ACs don't re-specify it, and what the change could break (regression ACs).
3. **Ask the open questions.** Gather the doubts that would change an AC: limits, formats, error behavior, who sees what, what is out of scope. Ask them with `AskUserQuestion` (at most 4 per round, the recommended option first, each question understandable on its own). Do a second round only if the answers open new doubts. If the user has no preference, take the recommended option and record it under *Assumptions*.
4. **Write the user story.** *As a … I want … so that …*, plus a short *In scope / Out of scope* list. Choose the issue type: Story (new behavior), Task (technical work with no user-facing change), Bug (behavior that differs from what is documented).
5. **Draft the ACs.** Number them `AC-1 … AC-n`, continuously, grouped in this order: happy path → edge cases → error states → non-functional. Show them to the user in chat and **iterate until they agree**. This is the refinement session.
6. **Ask where to save it.** Always ask for the destination folder (suggest `<project>/docs/tickets/` as the default option). Filename: `<KEY>-<NNN>-<kebab-slug>.md`, where `<KEY>` comes from the project (`travel-agency` → `TRAVEL`, `llm-customer-support-triage` → `TRIAGE`, otherwise a short upper-case name for the folder) and `<NNN>` is the next free number among `<KEY>-*.md` already in that folder (`001` if none). The same key goes in the ticket title.
7. **Write the ticket** with `references/TEMPLATE.md` as the exact structure. Fill every section; delete none. A section that doesn't apply (e.g. no non-functional ACs) says so in one line.
8. **Hand it over.** Give the path, the AC count per group, the assumptions you made and any question still open. Stop there.

## Developing the ticket

This skill ends at the ticket. To develop it, use the `tdd` skill, with the ticket's ACs as input.

## Quality checklist

Before writing the file, verify:

- [ ] Each AC has a single Given / When / Then and one observable outcome; it passes or fails with no interpretation.
- [ ] The happy path comes first; edge cases and error states are explicit, not implied.
- [ ] Error ACs say what the caller sees (status, message, unchanged state), not just "it fails".
- [ ] Regressions the change could cause have an AC.
- [ ] No AC names a function, class or file; no AC is a process step ("code is reviewed", which belongs to the DoD).
- [ ] In `travel-agency/`, the class references read and the deviations are listed.
- [ ] Assumptions and open questions are listed; nothing guessed is hidden inside an AC.

## Examples

`examples/` has two finished tickets:

- `TRIAGE-001-validate-order-id.md`: English, a business rule plus API behavior in `llm-customer-support-triage/`.
- `TRAVEL-001-sql-guard-view-whitelist.md`: Spanish (the request was in Spanish), a safety guard in `travel-agency/` with class references and deviations.
