---
name: tdd
description: >
  Develops a ticket test-first with the red → green loop: agrees with the user the seams
  (public interfaces the tests go through), then for one acceptance criterion at a time writes
  one failing pytest test, watches it fail for the right reason, writes the minimal code to pass
  it and stops for review after every cycle. Use when the user asks to develop or implement a
  ticket written by plan-ticket (a <KEY>-<NNN>-*.md file with acceptance criteria), to work
  test-first, mentions TDD or red-green, or wants to fix a bug starting from a failing test. If
  there is no ticket with acceptance criteria yet, run plan-ticket first. Not for tickets whose
  deliverable is data or documents (downloads, tables, written docs): those are checked by review.
---

# Test-Driven Development

TDD is the red → green loop. This skill makes that loop produce tests worth keeping, in the projects of this repo. It covers what a good test is, where tests go (seams), what to mock, the anti-patterns and the rules of the loop. Every section applies on every cycle: consult them before and during the loop, not after.

The input is a **ticket from `plan-ticket`**: its acceptance criteria (ACs) are the list of behaviors to build, one cycle each. If the user asks to implement something and there is no ticket, run the `plan-ticket` skill first and come back with its file.

## Rules that override everything else

0. **Don't invent anything: implement it the way the repo already does.** Everything the user asks to build has a reference somewhere in this repo:
   - class material in the `NN_*` folders;
   - `Ejercicios/` and `Skills-mario/`;
   - the user's own projects (e.g. `llm-customer-support-triage/`);
   - the code already in the folder.

   Find it and read it **whole** before the first test. The code you write in *green* must run the same as the reference: same libraries, same calls, same algorithm, same parameters and values. Names, files and organization may change; code in English, comments and docs in Spanish. Only change what the project's rules force (uv workspace, types, ruff/ty, tests) or what the reference doesn't cover. Any such change is a **deviation**: you state it in the seams proposal and the user approves it. Don't use another implementation even if it looks better. **If there is no reference in the repo, or it doesn't cover a piece the AC needs, say so and ask the user before writing code.** Never fill the gap with your own idea.
1. **Red before green.** Write the failing test first, run it, and see it fail **for the reason you expect**. Only then write code, and only enough to pass that test. Don't anticipate later ACs or add speculative features.
2. **One slice at a time.** One AC, one seam, one test, one minimal implementation per cycle. **Vertical slices**, never all the tests first and then all the code.
3. **Tests only at agreed seams.** No test is written at a seam the user hasn't confirmed.
4. **Stop after every cycle.** Report and wait for the user's OK before the next AC.
5. **Never bend a test to the code.** Don't weaken an assertion, skip a test, or edit an earlier test to make new code pass. If that seems necessary, a behavior is changing: stop and agree it with the user.
6. **Refactoring is not part of the loop.** It happens after the last AC, with the suite green (see *Closing*).
7. **No commits.** At the end, propose a commit message; the user commits.

Load `python-developer` before writing any test or code, and follow the folder's own rules where they differ (Python version, `requirements.txt`, no `src/` layout…). Read `references/good-tests.md`, `references/seams.md` and `references/mocking.md` before the first cycle.

## Before the loop (once per ticket)

0. **Check the ticket needs code.** If its deliverable is data or documents and its ACs are checked by a review or an existing command, TDD doesn't apply: tell the user and stop. Don't propose seams for it.
1. **Read the ticket and its context.** The ticket, the `AGENTS.md` / `CLAUDE.md` / `README.md` of the folder and of the subfolder the change touches, and the code and tests around it.
2. **Find the reference (rule 0).** Look in this order and stop at the first that covers the feature:
   1. the ticket's *References read*;
   2. the folder's `AGENTS.md` (in `travel-agency/`, the row of the phase in *Hoja de ruta y dónde mirar en el repo*);
   3. a search of the repo for the library, concept or function involved (`grep -rn`, class folders first).

   Read every reference **whole**, not just the function you need. Write down, for each AC, which reference (`file:function`) its code will reproduce. If you find none, stop and ask the user where it is or how to proceed, before proposing seams.
3. **Run the baseline.** Run the project's full test suite (commands in `references/seams.md`). If the folder's environment doesn't exist yet (no `.venv`), propose the folder's install command (`make install`, `uv sync`…) and wait for the user; don't install without asking. It must be green before you touch anything. If something already fails, tell the user and agree what to do before starting: never mix pre-existing failures with new ones.
4. **Propose the seams and the references.** For each AC: the seam (public interface) it is tested through, the test file, the test name and **the reference its code follows**. Then the list of **deviations** from the references, each with the project rule that forces it (or "the reference doesn't cover it"), or "none". For each seam, one line on **what it catches and what it misses**. Mark as **guard** any AC that describes behavior that already works: its test passes on the first run and protects it from the change. Propose the order of the slices: usually the happy path first, then edge cases, errors and non-functional, with each slice buildable on the previous ones. Ask the user to confirm, with `AskUserQuestion` if there are real choices (e.g. HTTP vs domain function).

## The loop (one AC per cycle)

1. **Red.** Write one test for the AC at its agreed seam, run **only that test**, and read the output. The failure must be the missing behavior: an `AssertionError` on the value the AC describes, an HTTP status, or a `ModuleNotFoundError` / `AttributeError` for the function this cycle creates. A typo, a missing fixture or a wrong import path is a broken test, not a red: fix the test and run it again.
2. **Green.** Write the minimal code that makes that test pass, **taken from the agreed reference** (same calls and values). If the cycle needs something the reference doesn't have, stop and ask: don't invent it. Run the test, then the folder's whole suite: every earlier test stays green.
3. **Checkpoint.** Report to the user and wait:
   - the AC and its test (`file::name`);
   - the red output (the relevant lines only);
   - what changed in the code, as files plus one sentence, or a short diff, and the reference it follows;
   - the green run (`N passed`);
   - anything you noticed for later refactoring, which you note but don't do.

### When the loop doesn't go as planned

| What happens | What to do |
|---|---|
| A non-guard test passes on its first run | Stop. Either the behavior already exists (mark it as a guard and tell the user) or the test doesn't check what the AC says (fix the test). |
| A guard test fails on its first run | Stop: the behavior the ticket assumed doesn't exist. Agree with the user whether it becomes a normal cycle. |
| Making it green breaks an earlier test | Stop. Two ACs contradict each other or the earlier test is coupled to the implementation. Agree the fix with the user. |
| The AC is wrong or incomplete | Stop, agree the change, update the ticket's AC, then continue. |
| The reference doesn't cover what the AC needs, or two references disagree | Stop and ask. Don't pick one or write your own; the answer becomes a deviation. |
| The test or the code would be simpler done differently from the reference | Follow the reference anyway. Mention the idea in the checkpoint; it changes only if the user says so. |
| You need a new dependency | Ask first. In `travel-agency/`: `uv add --package travel-<folder> <lib>`. Elsewhere, the folder's own way. |
| A test is flaky (time, order, network) | It is not done: make it deterministic (`references/mocking.md`) before the checkpoint. |

## Closing (after the last AC)

1. **Full check:** the whole suite and the folder's lint and type checks (`references/seams.md`). Everything green.
2. **Refactor:** run the `simplify` skill on the changes, then the full suite again. If anything changes behavior, revert it: refactoring keeps the tests green without editing them. Refactoring may only touch names, files and organization. A suggestion that moves the code away from the reference (another library, algorithm or values) is not applied: list it for the user.
3. **Docs:** update the folder's `AGENTS.md` if the change makes it outdated (root `AGENTS.md` criteria). In `travel-agency/`, always update the phase row: status, what you followed from class (*en qué te fijaste*) and what deviated.
4. **Ticket:** tick the Definition of Done items that are met, and say which are not.
5. **Hand over:**
   - the list of ACs → tests, all green;
   - the references followed and the deviations approved;
   - the commands run and their results;
   - anything left open;
   - a proposed commit message (no AI attribution, no `Co-Authored-By`).

   Suggest `/code-review` if the user wants a review before committing.

## Examples

`examples/TRIAGE-001-session.md` shows a session on the ticket `plan-ticket/examples/TRIAGE-001-validate-order-id.md`: the seams agreed, a guard cycle, a full red → green cycle with its checkpoint, an unexpected first-run pass, and the closing.
