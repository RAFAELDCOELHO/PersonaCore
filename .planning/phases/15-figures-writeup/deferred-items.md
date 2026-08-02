# Phase 15 — Deferred Items (out of scope, logged not fixed)

## DEF-15-01: `make lint` resolves a stale global `ruff 0.1.15` instead of the pinned venv ruff

**Found during:** Plan 15-01, Task 1 (running the `make lint` acceptance criterion)

**Symptom:** `make lint` fails with `Would reformat: tests/test_gpt_lora_seam.py` on a file this
phase never touches (last modified in commit `129c4ea`, Phase 04).

**Root cause:** `Makefile:16` calls bare `ruff`, which resolves through the pyenv shim to
`ruff 0.1.15` (`/Users/juliorcoelho/.pyenv/shims/ruff`). The project pins `ruff~=0.15` in
`pyproject.toml`'s `dev` extra, and `.venv/bin/ruff` is `0.15.16`. The two versions disagree on
the formatting of `tests/test_gpt_lora_seam.py`. The `format` target already uses the explicit
`.venv/bin/ruff` path (`Makefile:22`); only `lint` uses the bare name.

**Evidence the failure is pre-existing and unrelated to this plan:**

```
.venv/bin/ruff check .          -> All checks passed!
.venv/bin/ruff format --check . -> 134 files already formatted
ruff check scripts/phase15_stats.py && ruff format --check scripts/phase15_stats.py -> clean
```

Both ruff versions accept every file this plan wrote. CI (`.github/workflows/ci.yml`) installs
`.[cpu,dev]` into a fresh env, so CI sees the pinned 0.15 and is green — this reproduces on the
local dev box only.

**Deferred because:** `Makefile` is not in this plan's `files_modified`, and the failing file
belongs to Phase 04. Fixing it means changing the shared lint entry point, which is a
tooling-wide decision rather than a Phase 15 change.

**Suggested fix (one line, whenever someone picks it up):** point `Makefile:16` at
`.venv/bin/ruff`, matching `Makefile:22`'s `format` target.
