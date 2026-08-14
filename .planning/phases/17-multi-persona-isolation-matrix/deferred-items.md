# Phase 17 — Deferred Items

Out-of-scope discoveries logged during execution. Not fixed here; recorded so they are not
rediscovered as new.

## DEF-17-01 — `make lint` is red on this machine from a stale PATH `ruff` (pre-existing)

**Found during:** 17-01 verification (`make lint`).

**What:** `Makefile:16` runs bare `ruff check . && ruff format --check .`. On this dev box `ruff`
resolves to a pyenv shim holding **ruff 0.1.15** (Jan 2024), while the project pins `ruff~=0.15` in
the `dev` extra and `.venv/bin/ruff` is **0.15.16**. The two formatters disagree, so `make lint`
fails locally on files nobody touched.

**Evidence it is pre-existing and not caused by this plan:** ruff 0.1.15 wants to reformat 8 files,
and 7 of them are untouched by plan 17-01 —

```
tests/test_gpt_lora_seam.py        tests/test_phase16_driver.py
tests/test_phase14_demo.py         tests/test_phase16_fixture_regen.py
tests/test_phase15_docs.py         tests/test_phase16_ladder.py
tests/test_phase15_plots.py
```

`ruff check .` passes under both versions; only `ruff format --check` disagrees.

**Why CI is unaffected:** `.github/workflows/ci.yml:36-38` installs `.[cpu,dev,demo]` into a bare
interpreter and then runs `ruff` from PATH — which is the freshly installed **0.15.x** from the
`dev` extra. CI's `ruff` and `.venv/bin/ruff` are the same version family, and
`.venv/bin/ruff format --check` is clean on every file this plan wrote.

**Not fixed here because:** it is an environment condition in 7 unrelated files, outside plan
17-01's scope. It also intersects an already-recorded finding — `STATE.md` DEF-15-01 notes that
pointing `Makefile:16` at `.venv/bin/ruff` would break CI (which has no `.venv`), and that the
correct fix is `python -m ruff`. That fix belongs in its own quick task, together with a
reformat-or-not decision for the 7 stale files.

**Suggested resolution:** quick task — change `Makefile:16` to `python -m ruff check . && python -m
ruff format --check .`, then run `make format` once and commit the resulting no-op-behaviour diff.
