# Example session: developing TRIAGE-001 test-first

Ticket: `.claude/skills/plan-ticket/examples/TRIAGE-001-validate-order-id.md` (8 ACs, `llm-customer-support-triage/`).
Outputs are shortened to the lines that matter. The code shown is the minimal code of each cycle, not the final design.

## Before the loop

**Context read:** the ticket, `llm-customer-support-triage/README.md`, `app/domain/business_rules.py`, `app/llm/mock.py`, `app/services/event_service.py`, `tests/`. Loaded `python-developer`; the folder wins where they differ: Python 3.11, `requirements.txt`, package `app/` without `src/`, no lint or type checker configured.

**Reference (rule 0):** triage comes from **Tema 4**. `04_api_sdks_ia/Clases/06/app/domain/business_rules.py` and `tests/test_business_rules.py`, read whole, have the same structure as the folder: `REQUIRED_FIELDS`, `merge_state`, `apply_business_rules`, `determine_next_operation`, tests that build `ConversationState` directly. A search for order-id format validation (`isdigit`, `fullmatch`, `validate_order`) in `04_api_sdks_ia/` and the rest of the repo finds nothing: **the reference doesn't cover the validation itself.** Asked the user before going on:

> The class pattern covers *where* the rule goes (`apply_business_rules` / `merge_state`, tests on `ConversationState`), but nothing in the repo validates the order-id format. Should I write that check inside the existing functions, in the same style, and declare it as a deviation, or is there a reference I missed?

Answer: write it inside the existing functions, as a deviation. **Deviations:** (1) the order-id format check, because the reference doesn't cover it.

**Baseline:**

```text
$ make test
6 passed in 0.41s
```

**Seams proposed to the user:**

| AC | Seam | Test | File |
|---|---|---|---|
| AC-1 (guard) | Domain rules | `test_valid_order_id_allows_refund` | `tests/test_business_rules.py` |
| AC-7 | Domain rules | `test_non_numeric_order_id_is_missing` | same |
| AC-2 | Domain rules | `test_order_id_hash_prefix_is_removed` | same |
| AC-3 | Domain rules | `test_order_id_spaces_are_trimmed` | same |
| AC-4 | Domain rules | `test_order_id_length_boundaries` (parametrized) | same |
| AC-5 | Domain rules | `test_merge_state_ignores_invalid_order_id` | same |
| AC-6 (guard) | Domain rules | `test_technical_support_does_not_ask_for_order_id` | same |
| AC-8 | HTTP API | `test_api_asks_again_for_too_long_order_id` | `tests/test_api.py` |

- **Domain rules** (`apply_business_rules`, `merge_state`, `determine_next_operation`): catch every branch and boundary of the rule, fast and parametrizable. They miss whether the service applies them.
- **HTTP API** (`TestClient`, mock LLM): catches the wiring from the message to the response. It misses rule combinations, which are too slow to cover at this level.

Every AC follows `Clases/06/app/domain/business_rules.py` (rules inside the existing functions) and `Clases/06/tests/` (state built in the test, `TestClient` with the mock). Deviation (1) is the only one.

Order: the AC-1 guard first; AC-7 next, because it introduces the rule; then the normalizations (AC-2, AC-3), the length (AC-4), the merge (AC-5), the AC-6 guard, and the API last. **The user confirms.**

## Cycle 1: AC-1 (guard)

```python
def test_valid_order_id_allows_refund() -> None:
    state = ConversationState(
        process_type=ProcessType.refund_request, order_id="8921", reason="damaged_item", priority=Priority.medium
    )

    state = apply_business_rules(state)

    assert state.missing_fields == []
    assert state.ready_for_next_step is True
    assert determine_next_operation(state) == "start_refund_validation"
```

```text
$ .venv/bin/python -m pytest tests/test_business_rules.py::test_valid_order_id_allows_refund
1 passed
```

Passes on the first run, as expected for a guard. No code change. **Checkpoint → user OK.**

## Cycle 2: AC-7, a non-numeric order id is treated as missing

**Red**

```python
def test_non_numeric_order_id_is_missing() -> None:
    state = ConversationState(
        process_type=ProcessType.refund_request, order_id="ABC123", reason="damaged_item", priority=Priority.medium
    )

    state = apply_business_rules(state)

    assert state.order_id is None
    assert state.missing_fields == ["order_id"]
    assert determine_next_operation(state) == "ask_for_order_id"
```

```text
$ .venv/bin/python -m pytest tests/test_business_rules.py::test_non_numeric_order_id_is_missing
FAILED ... - AssertionError: assert 'ABC123' is None
```

Right reason: the rule doesn't exist, so the value is kept.

**Green.** Minimal change at the start of `apply_business_rules` in `app/domain/business_rules.py`:

```python
def apply_business_rules(state: ConversationState) -> ConversationState:
    if state.order_id is not None and not state.order_id.isdigit():
        state.order_id = None
    ...
```

```text
$ .venv/bin/python -m pytest tests/test_business_rules.py::test_non_numeric_order_id_is_missing
1 passed
$ make test
8 passed in 0.43s
```

**Checkpoint, as reported to the user:**

> **AC-7** · `tests/test_business_rules.py::test_non_numeric_order_id_is_missing`
> - Red: `AssertionError: assert 'ABC123' is None` (the value was kept)
> - Change: `app/domain/business_rules.py`: a non-numeric order id becomes `None` before the missing fields are computed
> - Green: `8 passed`
> - Noted for refactoring: the check will grow (`#`, spaces, length), so it can become its own function at the end
>
> Next: AC-2. OK?

**User OK.**

## Cycles 3-7: AC-2, AC-3, AC-4, AC-5, AC-6

Same pattern, one checkpoint each:

- AC-2 is red because `"#8921"` becomes `None`. Green: strip one leading `#`.
- AC-3 is red because of `"  8921 "`. Green: `.strip()` first.
- AC-4 is red on `"123"` and `"12345678901"`. Green: check 4 to 10 digits.
- AC-5 is red because `merge_state` copies `"abc"` over `"8921"`. Green: `merge_state` skips an order id that normalizes to `None`.
- AC-6 is a guard: passes on the first run.

`make test` → `14 passed` (AC-4 counts 4 cases).

## Cycle 8: AC-8, an unexpected first-run pass

```text
$ .venv/bin/python -m pytest tests/test_api.py::test_api_asks_again_for_too_long_order_id
1 passed
```

It isn't a guard, but it passed on the first run, so the loop **stops**. Report to the user: `event_service.process_event` already runs `merge_state` and then `apply_business_rules`, so once AC-4 was green the API path had the behavior. The test checks what AC-8 says: it went red when run with the AC-4 change temporarily reverted. Proposal: keep it as a **guard** of the wiring. **User OK.**

## Closing

1. `make test` → `15 passed`. No lint or type checker in this folder.
2. `simplify` on the changes. It extracts `normalize_order_id(value: str | None) -> str | None` with `ORDER_ID_MIN_DIGITS` / `ORDER_ID_MAX_DIGITS`, used by `apply_business_rules` and `merge_state`. `make test` → `15 passed`, no test edited.
3. `AGENTS.md`: the folder has none, and a domain rule change isn't important by the root criteria. Mentioned, not created.
4. Ticket DoD ticked. Still open: the ticket's question on bumping `rules_version`.
5. Proposed commit message:

   ```text
   Validate order id format before starting order workflows

   Order ids must be 4-10 digits; a leading "#" and surrounding spaces are removed.
   An invalid id counts as missing and never overwrites a valid stored one.
   ```

   Suggested `/code-review` before committing.
