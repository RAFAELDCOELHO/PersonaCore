# Deferred Items — Phase 02 (from-scratch-bpe-tokenizer)

Out-of-scope discoveries logged during execution (not fixed; see scope boundary rule).

## D1: `make test` fails under bare `pytest` (pre-existing, Plan 01/02)

- **Discovered during:** Plan 02-03, Task 3 full-suite verification.
- **Symptom:** `make test` (which runs bare `pytest -q`) fails to collect
  `tests/test_tokenizer_roundtrip.py` and `tests/test_tokenizer_oracle.py` with
  `ModuleNotFoundError: No module named 'tests'` (and `personacore` when run outside
  the venv). Tests use `from tests.fixtures.tricky_strings import TRICKY_STRINGS`.
- **Root cause:** bare `pytest` does not add the repo root to `sys.path`, so the
  `tests` package is not importable; `.venv/bin/python -m pytest` works because
  `python -m` prepends cwd. The Makefile `test:` target calls `pytest`, not
  `python -m pytest`.
- **Why deferred:** Pre-existing — introduced in `7ba75fc` (Plan 02-01) when the
  `tests`-namespaced fixture imports were added; not caused by Plan 02-03 changes.
  Out of this plan's scope (only `io.py`, `__init__.py`, `train_tokenizer.py`,
  `tokenizer.json`, `test_tokenizer_oracle.py`).
- **Authoritative local run is green:** `.venv/bin/python -m pytest -q` → 54 passed.
- **Suggested fix (future, small):** change Makefile `test:` to
  `python -m pytest -q`, OR add `[tool.pytest.ini_options] pythonpath = ["."]` (or a
  root `conftest.py`) so bare `pytest` resolves the `tests` package. CI invokes
  `pytest` after `pip install -e` — verify the same import path there.
