# Deferred Items — Phase 07 Evaluation

Out-of-scope discoveries logged during execution (NOT fixed — outside the current task's blast radius).

## Pre-existing ruff format drift (Plan 01 files)

- **Found during:** 07-02 Task 1 (`make lint`).
- **Files:** `src/personacore/evaluation/perplexity.py`, `tests/test_perplexity.py`.
- **Issue:** `ruff format --check .` reports both files "would reformat". They were created in
  Plan 07-01 and predate this plan; the 07-02 edits do not touch them.
- **Disposition:** Deferred. Not fixed here (scope boundary — only auto-fix issues directly caused
  by the current task's changes). The files I created/edited in 07-02 (`config.py`, `gpt.py`,
  `scripts/evaluate.py`) all pass `ruff check` and `ruff format --check` cleanly.
