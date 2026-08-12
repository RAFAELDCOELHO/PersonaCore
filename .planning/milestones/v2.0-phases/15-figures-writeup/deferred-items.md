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

**Update (Plan 15-04):** the stale-ruff false-positive list has grown to **two** files —
`tests/test_gpt_lora_seam.py` (Phase 04) and now `tests/test_phase15_plots.py` (written by
Plans 15-02/15-03). The pinned `.venv/bin/ruff` still reports `All checks passed!` and
`138 files already formatted`, so both are 0.1.15-vs-0.15 disagreements, not real formatting
defects. Noted only because a reader hitting `make lint` will now see two names, not one.

**Update (Plan 15-08) — THE SUGGESTED FIX ABOVE IS WRONG. Do not apply it.** Pointing
`Makefile:16` at `.venv/bin/ruff` would **break CI**: `.github/workflows/ci.yml:25` runs
`ruff check . && ruff format --check .` **bare**, in an environment where `pip install .[cpu,dev]`
puts the pinned ruff on `PATH` and **no `.venv/` exists at all** — a hardcoded `.venv/bin/ruff`
would be a missing-file error there. CI is green today precisely *because* it calls the bare name.

**The correct fix** is to resolve ruff through the active interpreter rather than through `PATH` or
a hardcoded path — `python -m ruff check . && python -m ruff format --check .`, or a
`RUFF ?= ruff` variable the local box can override. That works in both environments. Note this
also applies to `Makefile:22-23`'s `format` target, whose hardcoded `.venv/bin/` paths have the
same portability problem in the other direction (they simply are not exercised by CI).

The false-positive list is now **three** files: `tests/test_gpt_lora_seam.py` (Phase 04),
`tests/test_phase15_plots.py` (Plans 15-02/15-03) and `tests/test_phase15_docs.py` (Plan 15-08).
The pinned `.venv/bin/ruff` reports `All checks passed!` / `140 files already formatted`.
Seventh consecutive plan to hit this.

---

## DEF-15-02 — `scripts/extract_deltas.py` states the checkpoint total as `~914 MB`; measured is ~947 MB

**Found during:** Plan 15-05, Task 1 (writing the `## Decision: Extract Once, Then Plot From the
Committed Artifact Only` section, which cites the figure).

**The discrepancy:** `scripts/extract_deltas.py:10,33,274` all state that the checkpoints it reads
are "gitignored (~914 MB)". Measured directly on this box, the six files it opens total
**946,648,137 bytes** — 902.8 MiB, or 946.6 MB decimal. Neither unit reading gives 914. The five
checkpoints named in 15-CONTEXT D-08 (without `convbase_best.pt`, the adapter's W₀) sum to
668,621,570 bytes / 637.6 MiB, so the figure is not a five-vs-six-file discrepancy either.

**Impact: cosmetic.** The number appears only in the extraction script's docstring and error
message, where its job is to tell a reader "these are large and gitignored". No gate, test or
computation reads it. `docs/REPORT.md` deliberately writes it as an *attribution*
(*"`scripts/extract_deltas.py` records them at ~914 MB"*) rather than as a direct claim, so the
report is accurate regardless of how the script's figure is resolved.

**Deferred because:** `scripts/extract_deltas.py` is not in Plan 15-05's `files_modified`, and the
plan writes markdown only. Touching the extraction script would also mean re-verifying the D-07
tier boundary for a docstring number.

**Suggested fix (whenever someone picks it up):** replace `~914 MB` with the measured `~947 MB` at
`scripts/extract_deltas.py:10,33,274`, or drop the figure and say "several hundred MB". If the
figure is corrected, `docs/REPORT.md`'s attribution sentence needs the same edit — it quotes the
script by name.
