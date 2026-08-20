---
phase: 17-multi-persona-isolation-matrix
plan: 02
subsystem: training-instrument-widening
tags: [iso-06, d-14, d-16, d-20, additive-widening, ast-guard, provenance]
requires:
  - scripts/teach_persona.py (the committed Phase 14/16 training recipe — widened, never copied)
  - src/personacore/lora/inject.py (the runtime scale audit landed by quick task 260814-d0j)
provides:
  - teach_persona.arm_outputs(arm, *, prefix="phase14")
  - teach_persona.build_arm_bins(..., seed=SEED, prefix="phase14")
  - teach_persona.train_arm(..., seed=SEED, prefix="phase14") — both keywords threaded through
  - tests/test_phase14_teaching.py::test_seed_parameter_defaults_to_the_module_constant
  - tests/test_phase14_teaching.py::test_arm_outputs_prefix_is_additive (4 arms)
  - tests/test_phase14_teaching.py::test_prefix_reaches_both_arm_outputs_call_sites
  - tests/test_lora_inject.py::test_every_inject_lora_consumer_reads_the_artifact_config
  - tests/test_lora_inject.py::INJECT_LORA_CONSUMERS / INJECT_LORA_PRODUCERS (the allowlists)
affects:
  - plan 17-06 (the Phase 17 training driver — calls train_arm(seed=..., prefix="phase17"))
  - plans 17-09 / 17-10 (assert checkpoints/phase17_*; the path is proved below)
  - any future plan adding an inject_lora consumer — one visible line in INJECT_LORA_CONSUMERS
tech-stack:
  added: []
  patterns:
    - additive widening of a committed instrument, defaults preserving every existing run
      bit-for-bit ("import, never copy" — D-16, Phase 16)
    - the keyword is threaded to the function that WRITES, not only the one that NAMES
    - AST guard proving the parameter reached the call sites, not merely that it exists
    - producer/consumer classification with hard equality on three buckets + collapsed-glob guard
    - guards mutation-proved — watched failing before being trusted
key-files:
  created: []
  modified:
    - scripts/teach_persona.py (additive: 3 signatures, 2 call sites, 3 seed sites, 2 prints)
    - tests/test_phase14_teaching.py (additive: 3 tests, 0 deletions)
    - tests/test_lora_inject.py (additive: 1 test + helpers, 0 deletions)
decisions:
  - bin/mask deliberately NOT prefixed — they carry no phase label today and prefixing them
    would MOVE an existing path, which is a rename wearing an additive change's clothes
  - the real-arm shippable adapter exception stays UNCONDITIONAL on prefix
  - producer sites keep bare LoRAConfig() — they DEFINE a config rather than read one, and
    that literal is D-20's diagonal anchor
metrics:
  duration: 17min
  tasks: 2
  files: 3
  completed: 2026-08-14
---

# Phase 17 Plan 02: Widen the Training Instrument, Pin the ISO-06 Fix Summary

`train_arm(arm, ..., seed=1338, prefix="phase17")` now writes
`checkpoints/phase17_{arm}_adapter.pt` at seed 1338 from **both** internal `arm_outputs` call
sites, every existing Phase 14 arm resolves to byte-identical paths at the same seed, and a
future LoRA consumer that drops `**artifact["lora_config"]` turns a committed test red in CI
instead of mis-scaling an adapter in the middle of a GPU sweep.

## What Was Built

### Task 1 — the additive widening (commit `89a53dc`)

Four edits to `scripts/teach_persona.py`, each defaulting to today's behaviour:

| Site | Before | After |
|---|---|---|
| `arm_outputs` signature | `(arm)` | `(arm, *, prefix="phase14")` |
| `adapter` / `csv` / `checkpoint` paths | `phase14_` literal | `{prefix}_` |
| `build_arm_bins` signature | `(..., replay_ratio=0.0)` | `+ seed=SEED, prefix="phase14"` |
| `build_arm_bins:409` | `arm_outputs(arm)` | `arm_outputs(arm, prefix=prefix)` |
| `build_arm_bins:412` | `seed_everything(SEED)` | `seed_everything(seed)` |
| `train_arm` signature | `(..., replay_ratio=0.0)` | `+ seed=SEED, prefix="phase14"` |
| `train_arm:516` | `arm_outputs(arm)` | `arm_outputs(arm, prefix=prefix)` |
| `train_arm:539` | `build_arm_bins(arm, ...)` | `+ seed=seed, prefix=prefix` |
| `train_arm:563` | `seed_everything(SEED)` | `seed_everything(seed)` |
| `train_arm:603` | `TrainConfig(seed=SEED)` | `TrainConfig(seed=seed)` |
| both provenance prints | `seed={SEED}` | `seed={seed}` |

**The `:539` edit is the load-bearing one.** That call REBINDS `paths`, so the export half at
the bottom of `train_arm` writes to whatever dict `build_arm_bins` returned. Threading the
prefix at `:516` but not `:539` would guard the `phase17_` paths with `refuse_if_exists` while
exporting the adapter to `phase14_` — a Phase-17 artifact under a Phase-14 name, which is a
false provenance claim rather than a cosmetic mismatch. `test_prefix_reaches_both_arm_outputs_call_sites`
exists for exactly that failure and says so in its message.

Three deliberate non-changes, each with the reason recorded in code:

- **`bin` / `mask` are not prefixed.** They carry no phase label today
  (`data/persona_{arm}_train.bin`); inventing one would MOVE an existing path.
- **The `real`-arm adapter exception is unconditional on `prefix`.** It is the shippable
  `checkpoints/persona_adapter.pt` that `phase14_recall.ADAPTER_PATH` and the Gradio demo both
  hardcode. Phase 17 never passes `real`, so a prefix-aware exception would be dead code that
  weakened a cross-plan contract to serve a caller that does not exist.
- **`_require_go_verdict(FACTSET_REPORT)` at `:507`, `LORA_CFG = LoRAConfig()` at `:478` and the
  bare `arm_outputs(arm)` in the reload path are untouched** (verified: 1 hit each, the reload
  path's default keeps it byte-identical).

Three tests, 6 test cases (`test_arm_outputs_prefix_is_additive` is parametrized over
`tp.ARMS`). The seed test has two halves and needs both: `inspect.signature` proves the keyword
exists and defaults to `SEED`; the AST half proves **no `seed_everything(SEED)` call survived**,
because a widened signature whose body still reads the module global accepts a seed and ignores
it — worse than no widening, since it looks like it worked.

### Task 2 — the ISO-06 static guard (commit `c27059f`)

`tests/test_lora_inject.py::test_every_inject_lora_consumer_reads_the_artifact_config`.
AST-scans `scripts/*.py` + `src/**/*.py` (**72 files**) for every `inject_lora(...)` call and
classifies its second positional argument into three buckets, asserted with **hard equality**:

| Bucket | Sites | Form |
|---|---|---|
| CONSUMER | `personalize_demo.build_demo`, `phase14_recall.load_adapted_model`, `phase14_recall.run_bit_identity_control` | `LoRAConfig(**x["lora_config"])` |
| PRODUCER | `teach_persona.train_arm`, `train_adapter_smoke.main` | bare `LoRAConfig()` |
| UNCLASSIFIED | — | must be empty |

`len(scanned) >= 2` is asserted **first**, so a broken glob cannot make the guard green by
scanning nothing.

**A bare `ast.Name` second argument is resolved through the module's own top-level
assignments.** Both producers pass the `LORA_CFG` constant rather than an inline call, so the
plan's literal "a bare `LoRAConfig()`" rule only classifies them after that resolution. The
resolution is also what gives the guard extra reach: a rebind to `LORA_CFG = LoRAConfig(alpha=32.0)`
lands in the unclassified bucket and fails — D-20's anchor moving is exactly what should be caught.

The allowlists are module-level tuples so a Phase-17 driver extends them by **one visible line**
rather than by weakening the assertion to a membership check.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] A Task-1 acceptance criterion is arithmetically unsatisfiable**

- **Found during:** Task 1 acceptance criteria.
- **Issue:** the criterion reads *"`grep -n "seed=seed"` and `grep -n "prefix=prefix"` each
  return at least 3 hits (the two `arm_outputs` calls plus the `build_arm_bins` call)"*. The
  parenthetical is only true for `prefix=prefix`. **`arm_outputs` has no `seed` parameter** —
  the plan's own action §1 specifies `arm_outputs(arm, *, prefix="phase14")` — so `seed=seed`
  cannot appear at either `arm_outputs` call site. Satisfying "at least 3" would have required
  inventing a `seed=` keyword on `arm_outputs` that nothing reads.
- **Fix:** the criterion was measured against what the plan's action actually prescribes.
  `prefix=prefix` = **3** hits (`:430`, `:550`, `:580` — both `arm_outputs` calls plus the
  `build_arm_bins` call), `seed=seed` = **2** hits (`:579` the `build_arm_bins` call, `:643`
  `TrainConfig`), which is complete: `seed_everything(seed)` passes positionally at the other
  two sites. Every site the plan's *action* names is threaded, and the two AST criteria beside
  this one — which check structure rather than a hit count — both pass.
- **Files modified:** none (a criterion-arithmetic finding, not a code defect).
- **Commit:** `89a53dc`

### Interpretation recorded

The plan's Task-2 acceptance criterion says the RED probe should fail *"naming that site as a
producer where a consumer is required"*. Both statements were verified, from opposite sides:
the classifier reports `scripts/personalize_demo.py:448 func=build_demo kind=PRODUCER`, and the
test's first assertion fails naming `('scripts/personalize_demo.py', 'build_demo')` as the
missing consumer. The consumer assertion fires first because it is written first; the producer
assertion below it would fire on the same mutation.

### Deliberate simplification

No `_function_def` / `_call_sites` helper was copied from `tests/test_phase16_stats.py` into
`tests/test_phase14_teaching.py`. The one thing needed there is "calls to X inside function Y",
which is eight lines inline as `_teach_calls`; importing a general call-site framework for two
uses would be a second copy of a scanner that can drift with nothing exercising the difference.
`tests/test_lora_inject.py` does copy `_scanned_files` / `_enclosing_functions` from
`test_phase14_scoring.py` verbatim, because there the file-set scan **is** the rule being
enforced and the two must agree on what "the repo" means.

## Deliberate-RED Proof (the guard watched failing)

`scripts/personalize_demo.py:448` changed from
`inject_lora(model, LoRAConfig(**artifact["lora_config"]))` to `inject_lora(model, LoRAConfig())`:

```
E   AssertionError: the inject_lora CONSUMER set moved. A site that dropped
E   **artifact['lora_config'] injects at LoRAConfig() defaults and applies the adapter delta at
E   the wrong scale; a NEW Phase-17 consumer belongs in INJECT_LORA_CONSUMERS as one visible line.
E       found:    [('scripts/phase14_recall.py', 'load_adapted_model'),
E                  ('scripts/phase14_recall.py', 'run_bit_identity_control')]
E       expected: [('scripts/personalize_demo.py', 'build_demo'),
E                  ('scripts/phase14_recall.py', 'load_adapted_model'),
E                  ('scripts/phase14_recall.py', 'run_bit_identity_control')]
```

Reverted from a pre-probe copy; `git diff --quiet -- scripts/personalize_demo.py` confirms the
file is byte-identical, and the file is not in either commit.

## End-to-End Path Proof (dry inspection, no training)

Resolved through the real module, `arm_outputs(arm, prefix="phase17")`:

| arm | adapter | csv | checkpoint |
|---|---|---|---|
| `persona_a` | `checkpoints/phase17_persona_a_adapter.pt` | `results/phase17_persona_a/run.csv` | `checkpoints/phase17_persona_a_latest.pt` |
| `persona_b` | `checkpoints/phase17_persona_b_adapter.pt` | `results/phase17_persona_b/run.csv` | `checkpoints/phase17_persona_b_latest.pt` |
| `persona_c` | `checkpoints/phase17_persona_c_adapter.pt` | `results/phase17_persona_c/run.csv` | `checkpoints/phase17_persona_c_latest.pt` |

`checkpoints/phase17_persona_a_adapter.pt` is exactly the path 17-09 Task 1's `test -f` asserts.

Every Phase 14 arm re-resolved at the default and is byte-identical to the committed literals,
including `real` → `checkpoints/persona_adapter.pt`.

## Verification

| Check | Result |
|---|---|
| `pytest -q tests/test_phase14_teaching.py -x` | **38 passed** (was 32; +6) |
| `pytest -q tests/test_lora_inject.py -x` | **12 passed** (11 existing + 1 new, as required) |
| `pytest -q` (full suite) | **597 passed, 1 skipped** in 121.54s (baseline 590/1) |
| `test_arm_outputs_scoped` / `test_recipe_constants` / `test_real_arm_adapter_is_the_shippable_path` | unchanged and green |
| no `seed_everything(SEED)` survivor (AST) | exits 0 |
| both internal `arm_outputs` calls pass `prefix=` (AST, exactly 2) | exits 0 |
| `grep -c "prefix=prefix"` | 3 |
| `grep -c "seed={seed}"` | 2 |
| `grep -c "LORA_CFG = LoRAConfig()"` | 1 — D-20's anchor untouched |
| `grep -c "_require_go_verdict(FACTSET_REPORT)"` | 1 — Phase 14's gate unmoved |
| `git diff -- tests/test_lora_inject.py \| grep "^-"` | empty — purely additive |
| `grep -c "PRODUCER\|producer" tests/test_lora_inject.py` | 13 |
| `.venv/bin/ruff check` + `format --check` on all 3 files | clean |
| `git diff -- pyproject.toml` | empty (STAT-04) |
| `git status --short results/` | empty — no recorded evidence touched |
| `git diff --diff-filter=D` per commit | no deletions |
| `make lint` | **red — pre-existing, unchanged**, see below |

`git diff -- scripts/teach_persona.py | grep "^-"` shows 15 lines: the 3 signatures, the 3
`arm_outputs` path lines, the 2 `arm_outputs` call lines, the `build_arm_bins` call line, the 2
`seed_everything` lines, the `TrainConfig(seed=)` line, the 2 provenance lines — plus **one
docstring line** (`` `phase14_{arm}` naming `` → `` `{prefix}_{arm}` naming ``), which the plan's
list does not enumerate but which is required for the docstring to remain true after the
widening. No deletion anywhere else.

## Deferred Issues

`make lint` fails on this machine and did so before this plan started — **the same 8 files, the
same stale PATH `ruff` 0.1.15 vs the pinned `.venv/bin/ruff` 0.15.16**, already recorded as
DEF-17-01 in this phase's `deferred-items.md`. None of this plan's three files is in that list,
and `.venv/bin/ruff check` + `format --check` (the version CI actually runs) is clean on all
three. Nothing new deferred.

## Known Stubs

None. Both keywords are exercised by committed tests, the prefix path resolution is proved
end-to-end above, and the ISO-06 guard has been watched failing. The keywords have no caller
passing a non-default value yet — plan 17-06 is the first — but that is the wave ordering, not a
stub: the defaults are the Phase 14 behaviour and are the actively-used path today.

## Handover Notes

1. **`bin` and `mask` are NOT prefixed, and a Phase-17 arm named `persona_a` therefore builds
   `data/persona_persona_a_train.bin`** (the template is `persona_{arm}_train.bin`). The doubled
   word is cosmetic — `data/` is wholly gitignored, so these are not evidence — but a later plan
   that asserts a bins path must expect it. Renaming the template would move a Phase-14 path.
2. **`train_arm` still gates on `_require_go_verdict(FACTSET_REPORT)`** — Phase 14's report,
   hardcoded, deliberately unchanged (RESEARCH F-10). The Phase 17 driver calls
   `teach_persona._require_go_verdict(PHASE17_REPORT)` itself before `train_arm`, so both gates
   fire. If Phase 14's report is ever absent, `train_arm` refuses regardless of prefix.
3. **A Phase-17 `inject_lora` consumer must be added to `INJECT_LORA_CONSUMERS`** in
   `tests/test_lora_inject.py` in the same commit that writes it. Hard equality means a new
   consumer fails the suite until it is declared — by design.
4. `test_arm_outputs_prefix_is_additive` computes its moved-key set as `{"csv", "checkpoint"}`
   plus `{"adapter"}` for every arm except `real`. If a future plan makes the `real` exception
   prefix-aware, that branch and `test_real_arm_adapter_is_the_shippable_path` both go red — which
   is the intended coupling, not an accident.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema change at a trust
boundary. Register dispositions: **TH-17-04** mitigated (the hard-equality AST scan with its
collapsed-glob guard, on top of the existing runtime scale audit at
`src/personacore/lora/inject.py:119-129`); **TH-17-05** mitigated (defaults preserve every arm,
and the no-`seed_everything(SEED)`-survivor assertion proves the parameter reached all three
sites); **TH-17-06** mitigated (`prefix=` threaded through both call sites and pinned by
`test_prefix_reaches_both_arm_outputs_call_sites`); **TH-17-SC** holds — zero packages
installed, `pyproject.toml` byte-identical.

## Self-Check: PASSED

Files:

- FOUND: `scripts/teach_persona.py` (1773 lines, was 1733)
- FOUND: `tests/test_phase14_teaching.py` (734 lines, was 611)
- FOUND: `tests/test_lora_inject.py` (407 lines, was 240)

Commits:

- FOUND: `89a53dc` feat(17-02): thread additive seed= and prefix= through the teaching recipe
- FOUND: `c27059f` test(17-02): pin every inject_lora consumer to the artifact's own lora_config
