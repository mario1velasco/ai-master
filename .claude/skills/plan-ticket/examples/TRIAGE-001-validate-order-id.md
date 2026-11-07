# TRIAGE-001 · Validate the order id before starting order workflows

| Field | Value |
|---|---|
| Type | Story |
| Project folder | `llm-customer-support-triage/` (`app/domain/`) |
| Status | Draft, pending review |
| Created | 2026-11-07 |
| Labels | business-rules, triage |

## User story

**As a** support operator, **I want** the triage API to accept only well-formed order ids, **so that** refund, delivery and billing workflows never start with an order id that cannot exist.

## Context

Today any non-empty `order_id` counts as present: `apply_business_rules` only checks for `None`, `""` or `[]` (`app/domain/business_rules.py`). The LLM (or the mock, which picks the first run of 4+ digits) can store values such as `"#8921"`, `" 8921 "` or an 11-digit number, and a refund then moves to `start_refund_validation` with an order id that matches nothing. Order ids in the shop are 4 to 10 digits.

**References read:** `app/domain/business_rules.py`, `app/domain/schemas.py`, `app/llm/mock.py`, `tests/test_business_rules.py`, `tests/test_api.py`, `README.md`

**Deviations from the reference pattern:** None (no class reference applies to this change).

## Scope

**In scope**
- Normalizing (trim, one leading `#`) and validating the order id for every process type that requires it.
- Treating an invalid order id as missing, so the next operation asks for it again.

**Out of scope**
- Checking that the order exists in an order system.
- Telling the customer *why* the id was rejected (wording of `assistant_message`).
- Changing the LLM prompt or the mock's extraction.

## Acceptance criteria

### Happy path

**AC-1 — A valid order id lets a refund move on**
- **Given** a refund request case with reason `damaged_item` and priority `medium`
- **When** the business rules run with order id `"8921"`
- **Then** the state has no missing fields and is ready for the next step
- **And** the next operation is `start_refund_validation`

### Edge cases

**AC-2 — A leading "#" is removed**
- **Given** a refund request case with reason `damaged_item`
- **When** the business rules run with order id `"#8921"`
- **Then** the stored order id is `"8921"` and the next operation is `start_refund_validation`

**AC-3 — Surrounding spaces are removed**
- **Given** a refund request case with reason `damaged_item`
- **When** the business rules run with order id `"  8921 "`
- **Then** the stored order id is `"8921"` and the next operation is `start_refund_validation`

**AC-4 — Only 4 to 10 digits are valid**
- **Given** a delivery delay case
- **When** the business rules run with each order id `"123"`, `"1234"`, `"1234567890"`, `"12345678901"`
- **Then** `"1234"` and `"1234567890"` are kept, and `"123"` and `"12345678901"` leave `order_id` in the missing fields

**AC-5 — An invalid new id does not overwrite a valid stored one**
- **Given** a refund case that already stores order id `"8921"`
- **When** a new turn proposes order id `"abc"`
- **Then** the case still stores order id `"8921"`

**AC-6 — Process types without an order id are not affected**
- **Given** a technical support case with reason `cannot_log_in` and no order id
- **When** the business rules run
- **Then** `order_id` is not in the missing fields and the next operation is `open_technical_ticket`

### Error states

**AC-7 — A non-numeric order id is treated as missing**
- **Given** a refund request case with reason `damaged_item`
- **When** the business rules run with order id `"ABC123"`
- **Then** the stored order id is empty and the missing fields are `["order_id"]`
- **And** the next operation is `ask_for_order_id`

**AC-8 — The API asks again for an order id that is too long**
- **Given** the API in mock mode and a new case where the customer asked to return an item
- **When** the customer sends `"The order number is 12345678901."` to `POST /cases/{case_id}/events`
- **Then** the response is HTTP 200 with `operation = "ask_for_order_id"`
- **And** `state.order_id` is `null`

### Non-functional

None for this ticket (pure domain rule; the API path is covered by AC-8 in mock mode).

## Definition of Done

- [ ] Every AC is covered by a passing automated test
- [ ] The full test suite of the project is green (`make test`)
- [ ] Lint, format and type checks pass (where the project has them)
- [ ] `AGENTS.md` of the folder updated if the change makes it outdated
- [ ] Commits without AI attribution

## Assumptions and open questions

**Assumptions**
- Order ids are 4 to 10 digits (confirmed by the user in refinement).
- Only one leading `#` is stripped; `"##8921"` is invalid.

**Open questions**
- Should `rules_version` in `config.yml` be bumped, since the business rules change?
