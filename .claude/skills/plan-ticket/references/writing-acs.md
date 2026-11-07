# Writing acceptance criteria

Acceptance criteria (ACs) are the testable conditions one ticket must meet to be accepted. They say **what success looks like for this ticket**. The Definition of Done (DoD) says **what quality looks like for every ticket** (tests green, lint, docs). Keep the two apart: "unit tests added" is DoD, never an AC.

## Format: Given / When / Then

```markdown
**AC-3 — Order id with surrounding spaces is accepted**
- **Given** an open refund case that is only missing the order id
- **When** the customer sends the order id as "  8921 "
- **Then** the case stores the order id "8921"
- **And** the next operation is `start_refund_validation`
```

- **Title**: a short sentence with the outcome, not the action ("Duplicate email is rejected", not "Test duplicate email").
- **Given**: the starting state, concrete enough to set up in a test (which case, which data, which config).
- **When**: one action or event: a request, a call, a message, a time passing.
- **Then**: the observable result. Use **And** for further checks on *the same outcome*. If an *And* checks a different behavior, split it into its own AC.
- In a **data or document ticket** (no code), the *When* names how the AC is checked: an existing command (`sha256sum -c`, `git check-ignore`) or a review. Don't write ACs about tests failing: there are no tests.
- Use concrete values (`"8921"`, `LIMIT 1000`, `HTTP 422`) instead of "a valid id" or "a big number". Concrete values become test data.
- Names that are part of a public contract (an operation string, an HTTP status, a response field, a log event name) are fine to quote: they are observable. Internal names (functions, classes, modules) are not.

## Groups, in this order

1. **Happy path**: the main success flow(s). Usually 1-3 ACs.
2. **Edge cases**: limits and unusual but valid input: empty, maximum, boundaries (n-1, n, n+1), whitespace, case, unicode, duplicates, ordering, the first or last item.
3. **Error states**: invalid input, a missing or failing dependency, permissions. Each says what the caller **sees** and what **doesn't change** (no partial write, state kept).
4. **Non-functional**: only when they matter to this ticket: performance with a number, security, logging/observability (event written, no secrets logged), cost, determinism (mock mode, no network). Write them in GWT too, with a measurable Then.

Also add **regression** ACs when the change touches existing behavior that must keep working ("Given a technical support case without an order id … Then no order id is asked for"). Put them in the group they belong to.

## Do / Don't

| Do | Don't |
|---|---|
| Binary: met or not met | Vague words: "fast", "user-friendly", "correctly", "handles" |
| One outcome per AC | Three behaviors joined with *And* |
| Focus on the outcome | Tell the developer how to build it ("use a regex", "add a field to the class") |
| Specific limits and constraints | "Large files", "many requests" |
| Reflect what the user or caller needs | Criteria nobody asked for |
| Testable with the project's tests | Outcomes you can't check ("the model understands better") |
| Write them before refinement and agree on them | Process steps posing as requirements ("code reviewed", "PR approved") |

## Rewriting vague criteria

| Vague | Testable |
|---|---|
| The endpoint is fast | Given the mock LLM, when 1 event is posted, then the response arrives in under 200 ms |
| Invalid input is handled | Given … when the message is empty, then the API answers 422 and the case state is unchanged |
| The SQL is safe | Given … when the query is `DELETE FROM …`, then it is rejected with reason `only_select` and never executed |
| Errors are logged | Given … when the provider times out, then one event with `status = "error"` and `error_type = "timeout"` is written |

## LLM output

A criterion about the *rate* of good model answers ("90% of answers are faithful") is not an AC: it needs an evaluation set and belongs to the project's eval (e.g. `eval/`). An AC can still check the deterministic parts around the model: the code path when the model returns invalid JSON, the guard that rejects a bad answer, the mock-mode behavior.

## How many

Typically 4-10 per ticket. More than ~12 usually means the ticket should be split: propose the split to the user.
