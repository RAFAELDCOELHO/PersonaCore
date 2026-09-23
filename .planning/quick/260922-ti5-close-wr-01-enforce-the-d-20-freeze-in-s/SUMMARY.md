---
phase: quick-260922-ti5
plan: 01
status: complete
subsystem: scripts / report renderer freeze
tags: [WR-01, S-1, D-20, freeze, phase28]
requires: [28-REVIEW.md WR-01, 28-SECURITY.md S-1, scripts/phase28_report.py install]
provides: [install() refuses a present sentinel pair, 2 tests in tests/test_phase28_report.py section (9)]
affects: [scripts/phase28_report.py, tests/test_phase28_report.py]
key-files:
  created: []
  modified: [scripts/phase28_report.py, tests/test_phase28_report.py]
decisions:
  - "Refusal lives in install(), not main(): install is the write verb's only route, so any future direct caller is covered too; the n_begin == 1 replace-in-place branch is deleted, not guarded"
  - "Tests run only against tmp_path copies via monkeypatched REPORT_PATH/README_PATH; the strip helper is proved faithful by round-tripping to the published bytes"
  - "Natural RED: tests appended and run first (2 x DID NOT RAISE), then the renderer changed"
commit: 8a466d8
metrics:
  duration: ~8 min
  completed: 2026-09-22
---

# Quick 260922-ti5: Close WR-01 — D-20 freeze enforced in code

`scripts/phase28_report.py write` now raises `SystemExit("[phase28_report] write refused: ...")`
whenever a `PHASE28-REPORT` or `PHASE28-GLANCE` sentinel pair is already present, before any
`write_text`. The replace-in-place branch that WR-01 / S-1 named is gone. Pre-publish behaviour is
unchanged: on stripped copies `write` still installs both blocks and the result is byte-identical
to the published `docs/REPORT.md` and `README.md`.

## Commit

`8a466d8` — `fix(quick-260922-ti5): WR-01 — write refuses once the published blocks exist (D-20 freeze enforced in code, not prose)`

```
 scripts/phase28_report.py    | 14 +++++-----
 tests/test_phase28_report.py | 61 ++++++++++++++++++++++++++++++++++++++++++++
 2 files changed, 68 insertions(+), 7 deletions(-)
```

## Where the refusal lives and why

`install()` (scripts/phase28_report.py) — right after the existing `n_begin == n_end <= 1` proof:

```python
_prove(
    n_begin == 0,
    f"write refused: {stem} is already installed in {path} (D-20 — corrections are dated "
    "continuations through scripts/_addendum.py; `check` is the only post-publish verb)",
)
```

The `if n_begin == 1: ... replace in place` branch (and its dead `prefix`/`suffix` split) is
deleted; `elif glance_heading` became `if`. `install` is the only route `main(["write"])` has, so
no caller can reach a replace-in-place of a frozen span. Templates, `render_*`, `_span`, `check`
and `main` are untouched. The message avoids `rev-parse` / `logs/` / `mitigation_point_verdict`
(the AST guard `test_renderer_has_no_clock_and_no_head_sha` stays green).

## Tests (tests/test_phase28_report.py, section (9))

- `test_write_refuses_once_installed` — real published bytes copied to tmp_path, paths
  monkeypatched, `main(["write"])` raises `SystemExit` matching `write refused`, copies unchanged.
- `test_write_installs_pre_publish_then_refuses` — `_stripped()` removes
  `"\n" + BEGIN + span + END + "\n"` once from each file; `main(["write"]) == 0`; tmp bytes equal the
  committed bytes (strip + write round-trips, proving the strip faithful); second `write` refuses
  and the bytes are still identical.

Neither test writes `_ROOT/docs/REPORT.md` or `_ROOT/README.md`.

## RED transcript (tests appended, renderer unchanged at c0cf11b)

```
$ .venv/bin/pytest tests/test_phase28_report.py -q -k "write_refuses or write_installs"
...
>       with pytest.raises(SystemExit, match="write refused"):
E       Failed: DID NOT RAISE <class 'SystemExit'>

tests/test_phase28_report.py:648: Failed
----------------------------- Captured stdout call -----------------------------
[phase28_report] installed both blocks (pre-publish only, D-20)
_________________ test_write_installs_pre_publish_then_refuses _________________
...
        assert phase28_report.main(["write"]) == 0
        assert tmp_report.read_bytes() == (_ROOT / _REPORT_REL).read_bytes()
        assert tmp_readme.read_bytes() == (_ROOT / _README_REL).read_bytes()
>       with pytest.raises(SystemExit, match="write refused"):
E       Failed: DID NOT RAISE <class 'SystemExit'>

tests/test_phase28_report.py:666: Failed
----------------------------- Captured stdout call -----------------------------
[phase28_report] installed both blocks (pre-publish only, D-20)
[phase28_report] installed both blocks (pre-publish only, D-20)
=========================== short test summary info ============================
FAILED tests/test_phase28_report.py::test_write_refuses_once_installed - Fail...
FAILED tests/test_phase28_report.py::test_write_installs_pre_publish_then_refuses
2 failed, 24 deselected in 0.80s
```

(`git status --short docs/ README.md` empty after the RED run — the rewrite hit tmp copies only.)

## GREEN transcript (after the `install()` change)

```
$ .venv/bin/pytest tests/test_phase28_report.py -q -k "write_refuses or write_installs"
..                                                                       [100%]
2 passed, 24 deselected in 0.61s

$ .venv/bin/pytest tests/test_phase28_report.py -q
..........................                                               [100%]
26 passed in 1.68s
```

## Freeze verification

```
$ .venv/bin/python scripts/phase28_report.py check
check exit=0
$ git diff --exit-code 3b63b7d -- docs/REPORT.md README.md
diff exit=0            (before and after the commit)
$ git status --short docs/ README.md
(empty)
$ make lint
.venv/bin/ruff check . && .venv/bin/ruff format --check .
All checks passed!
288 files already formatted
$ grep -c "write refused" scripts/phase28_report.py
1
```

Sibling and census run (post-commit, clean tree):

```
$ .venv/bin/pytest tests/test_phase28_prereg.py tests/test_phase28_ledger.py tests/test_phase18_docs.py \
    tests/test_phase15_docs.py tests/test_phase25_driver.py tests/test_phase25_epsilon.py \
    tests/test_phase25_plots.py tests/test_phase25_watch.py tests/test_phase21_sc5.py -q
100 passed in 20.58s
```

Full suite not run (orchestrator's).

## Gates

No `== 10` literal, no `os.replace`, no `inject_lora` / `train_arm(` / `train_never_taught`;
renderer stays torch-free with no `today()` / `now` / `rev-parse` / `logs/` (the only grep hits are
the pre-existing guard tests themselves).

## Closure

28-REVIEW.md WR-01 and 28-SECURITY.md S-1 (T-28-02 residual) are closed by commit `8a466d8`.
Those two review files are not edited here — ledger/STATE rows are the orchestrator's.

## Deviations from Plan

None — plan executed as written.

## Self-Check: PASSED

- scripts/phase28_report.py, tests/test_phase28_report.py modified and in commit 8a466d8 (`git show --stat HEAD` lists exactly the two).
- docs/REPORT.md, README.md byte-identical to 3b63b7d; working tree clean for docs/ and README.md.
