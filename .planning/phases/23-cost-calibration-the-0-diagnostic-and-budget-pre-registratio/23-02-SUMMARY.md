---
phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
plan: 02
subsystem: testing
tags: [pytest, subprocess, import-graph, pre-registration, structural-guard, cal-02]

requires:
  - phase: 20-pre-registration-of-the-three-condition-gate
    provides: "the FROZEN scripts/mitigation_gate.py pin and the STATIC half of the guard — tests/test_phase20_prereg.py::test_mitigation_gate_import_graph_is_stdlib_and_erasure_gate_only, which already names mitigation_budget by string"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "tests/test_phase22_accountant.py::test_accountant_imports_math_only — the out-of-process probe shape this plan copies in structure, and the project's stated standard of 'guarded statically AND transitively'"
provides:
  - "tests/test_phase23_budget.py — CAL-02's transitive half: an out-of-process probe that execs the real frozen gate and asserts mitigation_budget never enters sys.modules"
  - "the sentinel meta-guard (NEVER_TAUGHT_ARM read off the exec'd module) that separates 'the gate loaded and was clean' from 'exec_module silently failed'"
  - "test_the_transitive_probe_detects_a_module_that_does_load_the_budget — a PERMANENT tmp_path positive control, re-proving the probe reddens on every suite run"
  - "the measured zero-headroom import ceiling recorded as a dated OBSERVATION comment block in a test file, with 23-09's three obligations named"
  - "both static assertions reproduced RED in this working tree, with literal failure text, and the tree proven byte-clean afterwards"
affects: [23-09 writes scripts/mitigation_budget.py under the recorded ceiling, any later plan that adds a scripts/mitigation_*.py sibling]

tech-stack:
  added: []
  patterns:
    - "static AST guard PLUS an out-of-process subprocess probe — the accountant's two-half shape, now applied to the gate/budget split"
    - "one _import_probe builder shared by the real-gate test and its positive control, so the control cannot drift into exercising a different probe"
    - "meta-guard asserted BEFORE the verdict it qualifies — a sentinel printed off the exec'd module, so a collapsed walk reddens instead of passing empty"

key-files:
  created:
    - tests/test_phase23_budget.py
  modified: []

key-decisions:
  - "23-02: the STATIC half is NOT duplicated here — tests/test_phase20_prereg.py:153-155's rule is that a lookalike copy proves something about a different function than the one CI executes"
  - "23-02: the positive control lives permanently in tmp_path rather than as a one-off hand observation in scripts/ — a watched RED that runs every suite run is strictly better evidence, and it cannot leak a scratch module into the tree"
  - "23-02: the control's scratch loader reaches the budget through sys.path, not by sitting in the mitigation_*.py glob — that is precisely the shape the static AST scan cannot see, so the RED is the RED that matters"
  - "23-02: the zero-headroom ceiling is recorded in the TEST FILE, not only in the plan — 23-09 must read the test file and may never read a planning document"
  - "23-02: widening the allow-set to give the budget module import room was considered and REFUSED — it weakens a committed guard to accommodate a module nobody has written yet"

patterns-established:
  - "A guard nobody has watched fail is not evidence: reproduce the RED in THIS tree with literal failure text, never cite a prior session's observation"
  - "Transient evidence gets a permanent form where one is available — a hand observation that must be deleted becomes a tmp_path positive control that need not be"

requirements-completed: [CAL-02]

duration: 26min
completed: 2026-08-26
---

# Phase 23 Plan 02: The Transitive Gate/Budget Import Guard Summary

**SC3's "structurally unable to import" now rests on real execution evidence rather than only on an AST walk: an out-of-process probe execs the real frozen `scripts/mitigation_gate.py` and proves `mitigation_budget` never enters `sys.modules`, closing the `gate → erasure_gate → budget` route that sits outside the `mitigation_*.py` glob — and all three halves were watched RED before any of them was trusted.**

## Performance

- **Duration:** 26 min
- **Tasks:** 2
- **Commits:** 2 task commits + this metadata commit
- **Suite:** 1366 passed, 1 skipped (baseline 1364 + 2 new tests; the skip is the pre-existing CUDA-only fp16 AMP smoke at `tests/test_train_loop.py:81`)

## What Was Built

### Task 1 — the transitive out-of-process probe (`66f42d4`)

`tests/test_phase23_budget.py::test_gate_does_not_transitively_load_the_budget` builds a probe
string with `importlib.util.spec_from_file_location` against `scripts/mitigation_gate.py`
**relative to `_ROOT`**, `exec_module`s it in a fresh interpreter via
`subprocess.run([sys.executable, "-c", probe], cwd=_ROOT, capture_output=True, text=True)`, and
exits 1 if any of `("mitigation_budget", "torch", "numpy", "scipy")` reached `sys.modules`. The
offender list is printed so a failure names which one got in.

**The hole this closes, restated as measured fact.** The static scan walks
`scripts/mitigation_*.py` and nothing else. The gate's own import list is
`pathlib`, `sys`, `erasure_gate` (`scripts/mitigation_gate.py:49-63`) — and `scripts/erasure_gate.py`
is **outside that glob**. So `gate → erasure_gate → budget` is invisible to any AST walk over
`mitigation_*.py`, however careful. `erasure_gate.py` imports only `math` today
(`scripts/erasure_gate.py:68`), so the route is empty *in fact* — but "empty in fact" is not
"structurally unable to import", and SC3 asks for the second.

**The meta-guard (T-23-07), and it was watched biting.** The probe prints
`GATE_SENTINEL=<repr of the exec'd module's NEVER_TAUGHT_ARM>` and the test asserts that string
arrived **before** it reads the return code. Without it, a probe whose `exec_module` silently
failed would pass by loading nothing at all. Confirmed by pointing `_run_probe` at
`scripts/erasure_gate.py` (a real module with no such attribute):

```
rc= 1
stdout= ''
stderr tail= AttributeError: module 'probe_target' has no attribute 'NEVER_TAUGHT_ARM'
```

The sentinel is absent, so the meta-guard assertion fires first with its own message rather than
letting a crashed probe be read as a clean gate.

**The static half is not rewritten.** `tests/test_phase20_prereg.py::test_mitigation_gate_import_graph_is_stdlib_and_erasure_gate_only`
already exists, already names `mitigation_budget` by string, and already scans the glob that will
admit `scripts/mitigation_budget.py` the moment 23-09 creates it. `tests/test_phase20_prereg.py:153-155`
is explicit that a lookalike copy proves something about a *different* function than the one CI
executes, and `scripts/mitigation_gate.py` is FROZEN. The module docstring records all three facts.

### Task 2 — three halves watched RED, and the ceiling written where 23-09 will read it (`4a4064d`)

## Watched-RED Observations (reproduced in THIS working tree)

Every literal below was produced against the real committed guard at this base commit. None is
copied from `23-RESEARCH.md`.

### (a) The negative assertion — `"mitigation_budget" not in imported`

Scratch files: `scripts/mitigation_budget.py` containing `Z_SWEEP = ()`, and
`scripts/mitigation_zzprobe.py` containing `import mitigation_budget`.

```
$ .venv/bin/python -m pytest tests/test_phase20_prereg.py -k import_graph -q
>       assert "mitigation_budget" not in imported, (
E       AssertionError: a mitigation_*.py module imports mitigation_budget (imports:
        ['erasure_gate', 'mitigation_budget', 'pathlib', 'sys']). The GATE holds OUTCOME
        thresholds and the BUDGET holds RESOURCE parameters, and `.planning/ROADMAP.md:139-144`
        requires that separation to be structurally enforced: ...
E       assert 'mitigation_budget' not in {'erasure_gate', 'mitigation_budget', 'pathlib', 'sys'}
1 failed, 24 deselected in 0.04s
```

Both scratch files deleted.

### (b) The subset assertion — the ceiling

Scratch file: `scripts/mitigation_budget.py` containing `import json` plus a literal.

```
$ .venv/bin/python -m pytest tests/test_phase20_prereg.py -k import_graph -q
E       AssertionError: the mitigation modules import ['json'] beyond the allow-set
        ['erasure_gate', 'pathlib', 'sys']. This is asserted as a SUBSET rather than as a list of
        forbidden names deliberately: ...
E       assert {'erasure_gat...thlib', 'sys'} <= {'erasure_gat...thlib', 'sys'}
E         Extra items in the left set:
E         'json'
1 failed, 24 deselected in 0.04s
```

Scratch file deleted.

### (c) The transitive probe — RED as a PERMANENT positive control

`test_the_transitive_probe_detects_a_module_that_does_load_the_budget(tmp_path)` writes a scratch
`mitigation_budget.py` and a scratch loader under `tmp_path`, where the loader inserts `tmp_path`
on `sys.path` and does `import mitigation_budget`. It runs through the **same** `_import_probe`
builder as the real-gate test, and asserts `returncode == 1` with `mitigation_budget` named on
stdout — plus the same sentinel meta-guard first, so a crash cannot be mistaken for a detection.

Two reasons this is better than a hand observation, both deliberate:

1. It runs on **every** suite run. The plan's own framing — "a watched RED that runs on every suite
   run is strictly better evidence than one performed once by hand" — is why (c) landed as code
   while (a) and (b) could not.
2. It lives in `tmp_path`, so it is structurally incapable of leaving a scratch module in
   `scripts/` (T-23-08). The loader reaches the budget through `sys.path` rather than by sitting in
   the `mitigation_*.py` glob, which is exactly the shape the static AST scan cannot see.

**What it does NOT claim:** anything about the real gate. It proves the *probe* detects the route;
`test_gate_does_not_transitively_load_the_budget` is what covers the gate. The shared builder is
what stops the control drifting into exercising a different probe than the one that guards.

### (d) Restore, proven

```
$ git status --short scripts/
                            # (empty)
$ git diff --exit-code -- scripts/
                            # exit 0
$ ls scripts/mitigation_budget.py scripts/mitigation_zzprobe.py
ls: scripts/mitigation_budget.py: No such file or directory
ls: scripts/mitigation_zzprobe.py: No such file or directory
```

### (e) The zero-headroom ceiling, recorded where 23-09 will read it (T-23-10)

Import surfaces **re-measured in this tree** by walking each module's AST rather than trusting the
research document:

| Module | Imports |
|---|---|
| `scripts/mitigation_accountant.py` | none |
| `scripts/mitigation_unit.py` | none |
| `scripts/mitigation_gate.py` | `erasure_gate`, `pathlib`, `sys` |

The union is **exactly** `{"pathlib", "sys", "erasure_gate"}` — the allow-set — so the ceiling has
zero headroom. That, its date, both literal RED texts, and three named obligations for 23-09 now
live in a comment block at `tests/test_phase23_budget.py:60-101`:

1. `scripts/mitigation_budget.py` must have **zero imports** — the `scripts/phase19_floor.py` shape
   (literal assignments plus provenance comments) satisfies this for free.
2. It may **not** `import mitigation_gate` either — that adds `mitigation_gate` to `imported` and
   breaks the subset assertion just as surely as `json` does, and it is the import a reader would
   most naturally reach for since the budget's K must agree with the gate's closed menu.
3. So a selected K is **restated as a literal** with a provenance comment naming
   `scripts/mitigation_gate.py::K_RUNGS`, and 23-09 must ship a **test asserting the literal and the
   menu agree**. A restated constant with no test agreeing it is a copy waiting to drift.

Widening `allowed` is recorded as **considered and refused** — it weakens a committed guard to
accommodate a module that does not exist yet.

## Verification

```
$ .venv/bin/python -m pytest tests/test_phase23_budget.py -v
2 passed

$ .venv/bin/python -m pytest tests/test_phase23_budget.py tests/test_phase20_prereg.py -q
27 passed in 3.78s

$ git status --short scripts/                                                  # empty
$ git diff --exit-code -- scripts/mitigation_gate.py scripts/mitigation_accountant.py pyproject.toml
                                                                               # exit 0
$ .venv/bin/python -m pytest tests/ -q
1366 passed, 1 skipped, 83 warnings in 256.94s

$ make lint
All checks passed!  /  231 files already formatted
```

Acceptance greps: `grep -c "subprocess.run"` → 1, `grep -c "cwd="` → 1,
`grep -n "NEVER_TAUGHT_ARM\|sentinel"` → matches at `:64` and `:67`,
`grep -n "zero headroom"` → matches at `:74`.

## Frozen-Pin Discipline

Neither frozen pin moved. `git diff --exit-code -- scripts/mitigation_gate.py scripts/mitigation_accountant.py`
exits 0 (T-23-09), and `pyproject.toml` is byte-unchanged (RPT-03, T-23-SC — **zero installs**).
The two commits in this plan touch exactly one file, `tests/test_phase23_budget.py`, and nothing
under `scripts/` or `results/`.

## Deviations from Plan

**1. [Rule 1 — Bug] `grep -n "zero headroom"` did not match the first draft of the ceiling block**

- **Found during:** Task 2, acceptance-criteria check
- **Issue:** The ceiling block was first written with the emphatic all-caps `**ZERO HEADROOM.**`,
  which the case-sensitive acceptance grep does not find. The criterion is the artifact 23-09 will
  use to locate the ceiling, so a block it cannot grep is a block that is not recorded.
- **Fix:** Reworded to `... so the ceiling has **zero headroom**.` — same emphasis, matchable.
- **Commit:** `4a4064d`

**2. [Rule 1 — Bug] One `E501` at 101 chars in Task 1's failure message**

- **Found during:** Task 1, `make lint`
- **Fix:** Rewrapped one f-string fragment. `make lint` clean.
- **Commit:** `66f42d4`

**No artifact-naming discrepancies.** Every name the plan cited resolved against the code as
written: `mitigation_gate.NEVER_TAUGHT_ARM` (`scripts/mitigation_gate.py:341`) exists and is
`"never-taught"`; `K_RUNGS` (`:254`) is `(48, 24, 16, 8)`; `_GATE_MODULES`
(`tests/test_phase20_prereg.py:73`) is the `mitigation_*.py` glob; `scripts/erasure_gate.py:68` is
`import math` and is the file's only import. The import-surface table in `23-RESEARCH.md` §R2.3 was
re-measured rather than cited and matched exactly.

## Threat Flags

None. This plan adds no network endpoint, no auth path, no file write outside `tmp_path`, and no
schema. Its only subprocess call runs `sys.executable` with a `-c` string built from repository
paths, never from external input.

## Known Stubs

None. `scripts/mitigation_budget.py` is deliberately **not** written here — 23-09 owns it, and this
plan's entire output is the guard plus the observed evidence that tells 23-09 what the module may
contain.

## Self-Check: PASSED

- `tests/test_phase23_budget.py` — FOUND
- Commit `66f42d4` — FOUND
- Commit `4a4064d` — FOUND
- `scripts/mitigation_budget.py` — correctly ABSENT
- `scripts/mitigation_zzprobe.py` — correctly ABSENT
