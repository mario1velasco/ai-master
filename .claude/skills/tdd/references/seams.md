# Seams: where tests go in this repo

A **seam** is the public boundary a test goes through: the interface where you observe behavior without reaching inside. Tests live at seams, never against internals. You can't test everything, so agreeing the seams up front puts the effort on the critical paths and the complex logic.

Before the first test, ask: *what is the public interface, and which seams do we test?* Give each proposed seam one line on what it catches and what it misses.

## Choosing the seam

1. **Prefer the highest seam that is still fast and deterministic**: it tests what a caller really gets and survives the most refactoring.
2. **Go down one level when the combinations explode**: the boundaries of a rule (`"123"`, `"1234"`, `"1234567890"`, `"12345678901"`) are clearer as a parametrized domain test than as four pairs of HTTP calls. Keep one test at the higher seam to prove the path is wired.
3. **A module inside a package can be a seam** when it is a deep unit with a contract of its own (e.g. the SQL guard of `text2sql`), but only if agreed explicitly. A private helper (`_name`) never is.
4. **Never test through another package's internals.** In `travel-agency/`, each package exposes one public function with types from `contracts/`; tests of package A use only the public function of package B.

## `llm-customer-support-triage/`

| Seam | How | Catches | Misses |
|---|---|---|---|
| HTTP API | `TestClient(app)` from `app.main`, with `config.USE_MOCK_LLM = True` set before importing the app (see `tests/test_api.py`) | Wiring end to end: DTO validation (422), status codes, the operation chosen, state across turns | Real model behavior; rule combinations are slow to cover here |
| Domain rules | Pure functions in `app/domain/business_rules.py` (`apply_business_rules`, `merge_state`, `determine_next_operation`) with `ConversationState` built in the test | Every branch and boundary of a business rule, fast and parametrizable | Whether the service really calls them, and in which order |
| LLM adapter | `app/llm/mock.py` (and the Anthropic client) | Used to **replace** the model, not as a seam to assert on | — |

Commands, from the folder (Python 3.11, `requirements.txt`):

```bash
.venv/bin/python -m pytest tests/test_business_rules.py::test_name   # one test (red / green)
make test                                                             # whole suite
```

No lint or type checker is configured: don't add one without asking.

## `travel-agency/` (uv workspace)

| Seam | How | Catches | Misses |
|---|---|---|---|
| Package public function | The one function each package exposes, with `contracts/` types | The contract other packages rely on | Internal edge cases are slower to reach |
| Agreed internal unit | A module with its own contract (e.g. `text2sql.guard.run_safe_sql`) | All the cases of a safety or calculation rule | Whether the public function uses it |
| Semantic layer | `open_db()` connection (session fixture `con` in `database/tests/conftest.py`) + SQL against the views | Data integrity checks (`CHECKS`), views, comments, the generated schema | — |
| API (phase 7) | `TestClient` over `api/app`, as in triage | HTTP contract and session handling | Model quality |
| LLM client (Ollama) | Replaced by a fake or by saved real outputs (`mocking.md`) | — | — |

Commands, from `travel-agency/`:

```bash
uv run pytest text2sql/tests/test_text2sql_guard.py::test_name   # one test
uv run pytest text2sql/tests                                      # the package
uv run pytest                                                     # whole workspace
uv run ruff check . && uv run ruff format . && uv run ty check    # closing
```

## Other folders

Course folders (`NN_*`) and `Ejercicios/` often have no tests or no `tests/` folder. Read how the folder runs things (`README.md`, `Makefile`, `requirements.txt`) and propose where the tests go before the first cycle; don't restructure the folder.
