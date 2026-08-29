---
phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
plan: 14
subsystem: privacy-mitigation-calibration
tags: [ctrl-03, never-taught, extraction-floor, mitigation-gate, phase18-attack-suite, detached-run]
requires:
  - results/phase23_never_taught_training.json   # 23-08's ONE scheduling — read, never rewritten
  - scripts/mitigation_budget.py                 # 23-13's CURVE_K / N_CONTROL_SEEDS pin — read only
  - results/phase23_cost.json                    # 23-11's cost bracket and sizing table
  - results/phase23_matched_verdict.json         # 23-19's `proceed` — the D-04 release this inherits
  - scripts/phase18_extraction.py                # FROZEN attack pin; predicate + rollup imported
  - scripts/mitigation_gate.py                   # FROZEN Phase-25 gate; refusals driven, never edited
provides:
  - results/phase23_never_taught.json            # the scored extraction floor + its gate provenance
  - "scripts/phase23_run.py::never_taught"       # the per-seed scoring sub-mode
  - "tests/test_phase23_ctrl.py (11 new tests)"  # gate acceptance + all five refusals watched
affects:
  - Phase 25  # consumes this floor as `extraction_ceiling`'s `extraction_noise_floor` kwarg
  - Phase 24  # the same adapters are the relearning reference
tech-stack:
  added: []
  patterns:
    - "one seed per process: the commit boundary is a PROCESS boundary, not an intention"
    - "raw draws persisted per shape, so post-processing failure costs seconds not GPU hours"
    - "assembly re-scores every seed from its retained draws and asserts equality with the reading"
key-files:
  created:
    - results/phase23_never_taught.json
    - results/phase23_never_taught_run.log
  modified:
    - scripts/phase23_run.py
    - tests/test_phase23_ctrl.py
    - .planning/REQUIREMENTS.md
decisions:
  - "pooled counts are ONE DESIGNATED SEED (the ladder's first) at n=416, not a sum across seeds"
  - "family zero is NOT run: D-01's equality is against TAUGHT rows, false by construction here"
  - "the seed stride is phase18_extraction.K, so the K=16 reading is the exact prefix of K=48"
  - "the floor is exactly 0.0 — real, but over a DEGENERATE reading set, and stated as such"
metrics:
  duration: "~10.5 h wall clock (10.137392909281836 h of it GPU generation), across 6 detached launches"
  completed: 2026-08-29
  tasks: 4
  commits: 11
---

# Phase 23 Plan 14: Score the Never-Taught Adapters at the Pinned K Summary

The five never-taught adapters 23-08 trained were scored on the Phase-18 attack suite at
`CURVE_K = 16` and returned **0 of 416 gated questions extracted, at every seed** — a committed
extraction floor of exactly `0.0` that the frozen Phase-25 gate accepts, with all five of its
refusals watched firing on degraded copies. CTRL-03 is ticked; all six of `ROADMAP.md:562`'s
requirements are now closed.

## What Was Built

| Task | Name | Commit | Key files |
|------|------|--------|-----------|
| 1 | Project, register the sub-mode, launch detached, score N seeds | `92b48a9`, `ec90611`, `8a2942f`, `6e17446`, `959dbb8`, `2bb6327`, `1274273`, `77e273d` | `scripts/phase23_run.py`, `data/phase23_run_state.json`, `results/phase23_never_taught_run.log` |
| 2 | Emit and commit the record | `956238b` | `results/phase23_never_taught.json` |
| 3 | Prove the record passes the frozen gate's refusals | `22db5b6` | `tests/test_phase23_ctrl.py` |
| 4 | Tick CTRL-03 | `87f6f2e` | `.planning/REQUIREMENTS.md` |

## The Measurement

**Every seed: `0 / 416` `core_held_out` QUESTIONS extracted at least once.**

| seed | gated successes / questions | rate | draws (gated) | A1-mild | A1-agg | A2 | A3 | hours |
|------|------|------|------|---------|--------|-----|-----|-------|
| 1337 | 0 / 416 | `0.0` | 6656 | 119.12 | 105.59 | 130.57 | 101.54 | 2.0375 |
| 2024 | 0 / 416 | `0.0` | 6656 | 120.14 | 106.05 | 131.73 | 102.56 | 2.0214 |
| 1338 | 0 / 416 | `0.0` | 6656 | 120.85 | 105.67 | 133.05 | 100.74 | 2.0264 |
| 2025 | 0 / 416 | `0.0` | 6656 | 119.76 | 105.18 | 134.31 | 101.20 | 2.0266 |
| 1339 | 0 / 416 | `0.0` | 6656 | 120.59 | 105.05 | 133.78 | 101.23 | 2.0255 |

(rates are draws/min; `hours` is the timed generation bracket, `torch.mps.synchronize()`d at both
boundaries.)

- **`extraction_noise_floor` = `0.0`** — `phase23_prereg.noise_floor([0.0, 0.0, 0.0, 0.0, 0.0])`,
  CALLED and never inlined, re-deriving under exact `==` on every suite run.
- **`nontarget_questions` IS A QUESTION COUNT**, and its source is named: the four dose-split
  attack families' `core_held_out` cells, `4 × 104 = 416`, aggregated through the imported
  `phase18_extraction.aggregate_questions`. The driver asserts `sum(n_questions) == len(cell)` per
  cell (one scored record per question — a draw count would be 16× too large and cannot survive
  it) and `total_draws == nontarget_questions × draws_per_question` (`6656 == 416 × 16`).
- **Secondary, recorded with its own denominator and NOT reduced:** the `core_taught` tier is also
  `0/112` on every family at every seed. Per-family and per-fact counts are in `per_seed[].per_cell`.
- **69,120 draws dispatched** in total (864 prompts × 16 × 5 seeds); 33,280 of them on the gated
  tier. Stop-terminated fractions were normal (seed 1337: 3028/2803/3113/2605 of 3456 per shape),
  i.e. the run sat near the `stop_ids_active` condition, not the emptied-stop-set one.

### The floor is `0.0`, and that is stated rather than left to be inferred

The five readings are **identical**, so the range reduction returns exactly `0.0`. This is a real
measurement — nothing leaked, on any family, at any seed — and `phase23_prereg.noise_floor` accepts
it (it refuses fewer than two readings and non-finite ones, not zero), as does
`mitigation_gate.extraction_ceiling`. But it is a floor over a **degenerate reading set**: it
records the *absence of leakage*, not a *measured spread*, and it says less about run-to-run
variance than a non-zero range would.

Its consequence for Phase 25 is **stricter, not looser**, and the frozen gate anticipated exactly
this. `MARGIN_K × 0.0 = 0`, so X reduces to `wilson_upper_bound(0, 416)` alone — the regime
`extraction_ceiling`'s own docstring names: *"X tolerates ZERO leaked questions … the 19-03 regime
where the criterion clears ONLY on a PERFECT ERASURE"* — and `tolerance_report` publishes which
regime a given X landed in. Phase 23 does not compute X, so nothing here acts on that; it is
recorded so Phase 25 reads the floor correctly.

## The Projection, Recorded Before Any GPU Second

Computed from the pinned constants and the committed cost record, through
`results/phase23_cost.json`'s **own** `h_per_point_composition` (not read off the sizing block, so
the two are an agreement rather than a restatement), and refusing to spend a GPU second on a >5%
disagreement:

| | stop ids ACTIVE | stop set EMPTIED |
|---|---|---|
| this run's projection, per seed | `1.853307671905495` h | `2.9312045975122603` h |
| … × N=5 | `9.266538359527477` h | `14.6560229875613` h |
| same, priced WITH family zero | `2.0157249759481055` h | `3.151282090814784` h |
| committed `sizing["16"]`, per seed | `1.9979696709667354` h | `3.1471532286150796` h |
| committed `sizing["16"]`, × N=5 | `9.989848354833677` h | `15.735766143075399` h |
| **relative delta vs sizing** | **+0.8887%** | **+0.1312%** |

No material discrepancy, so the run proceeded. **MEASURED ACTUAL: `10.137392909281836` h**, which is
1.094× the stop-ids-active projection and **0.64× the emptied-stop-set projection** — between the
two bracket ends, where a normally-terminating adapter belongs.

**Session sizing, stated in advance and borne out:** ~2.03 h per seed meant the run spanned multiple
sessions by construction — one seed per session-sized block, five launches. A kill cost at most one
*shape* (~30 min) after the first failure, and at most one *seed* (~2 h) before it.

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 1 - Bug] `TypeError: Object of type Tensor is not JSON serializable` threw away 2h22m of completed generation**

- **Found during:** Task 1, seed 1337, first attempt.
- **Issue:** the scored block echoed `phase14_recall.load_adapted_model`'s fifth return value. That
  value is the loaded persona *file* and carries the adapter **tensors**. All 13,824 draws
  completed; `_state_write`'s `json.dumps` then raised, and the seed's work was lost. The smoke I
  ran before launching exercised the *computation* and printed the block's keys — it never
  *serialized* it, which is exactly the gap the failure fell through.
- **Fix:** the field is **dropped, not repaired** — the weights are already pinned by
  `adapter_sha256`, so it bought nothing.
- **The real fix, and the reason this is worth its own commit:** raw draws are now **persisted per
  shape** to `data/phase23_never_taught_seed{N}_draws.json` as they are produced, and a re-launch
  reuses them (refused unless adapter digest, corpus digest and `k` all match). A kill now costs at
  most one shape (~30 min) instead of one seed (~2 h), and *every* post-draw step — scoring,
  aggregation, serialization — costs seconds if it fails. The block is additionally
  `json.dumps`-proved inside `score_never_taught`, where the failure is free.
- **Files:** `scripts/phase23_run.py`
- **Commit:** `ec90611`
- **Not hidden:** the crashed run's traceback is committed verbatim in
  `results/phase23_never_taught_run.log`, and its `SESSION` line is one of the six. The restart is
  not presented as a first attempt (23-20's `a629d93` precedent).

**2. [Rule 2 - Missing critical functionality] the published figure was not recomputable from the record**

- **Found during:** Task 2 design, before the record was written.
- **Issue:** the record carried per-fact counts but no per-item log, so `0/416` could be re-added up
  only from a gitignored working ledger. This project's standing rule is that no figure enters an
  artifact without its raw per-item evidence, denominator and bound.
- **Fix:** `evidence[].per_question` — 864 rows per seed, one per QUESTION, each with its own hit
  count and draw count. `pooled.nontarget_successes` is the number of gated rows with `hits > 0`.
  The assembly additionally **re-scores every seed from its retained raw draws**, in a separate
  process, through the same imported predicate, and asserts equality with the recorded count before
  writing. All five re-derived `0/416`.
- **Files:** `scripts/phase23_run.py`
- **Commit:** `8a2942f`

### Deliberate scoping decisions

**Family zero (`phase18_extraction.FAMILY_ZERO`, "A0") is NOT run.** Its entire job is D-01's
row-for-row equality against `results/phase14_recall_report.md`'s 112 **taught** rows — a
harness-sanity control for an arm that *was* taught. A never-taught adapter has seen no fact, so
that equality is false by construction and would abort a scored run rather than check anything. It
also carries no ASR ladder (D-09 spends 9 draws on it, not K) and contributes nothing to the
question-denominated counts the gate consumes. The plan's own wording scopes to "the same attack
families", and `ATTACK_FAMILIES` does not contain `A0`. **Cost consequence, stated rather than
glossed:** `sizing["16"]` prices family zero's 1,008 draws into the per-point figure, so this run is
priced *below* the committed line item — the safe direction. Both figures are in the record's
`projection` block.

**The seed stride is `phase18_extraction.K` (48), not `CURVE_K` (16).** `draw_all` seeds a fresh
generator per draw at `index + s`, so drawing 16 samples from the 48-wide stride makes this reading
the **bit-identical prefix** of the full-fidelity K=48 run — D-09's own argument for family zero's
9-draw prefix, one level up. `promote_to_full_fidelity` (16→48) therefore genuinely *extends* this
reading instead of redrawing it, and the per-question windows stay disjoint.

**`pooled` is one DESIGNATED seed, not a sum across seeds.** The ladder's first (1337), pooled over
the four attack families on the gated tier, n = 416 — `sigma_zero_verdict`'s own
`control_readings[0]` central-reading convention and `CONTROL_NOISE_FLOOR_PROVENANCE`'s "the pinned
central reading", restated. Summing to n = 2080 was **rejected with its reason recorded**: the five
seeds re-ask the *same* questions of five different adapters, so a pooled denominator would count
correlated re-measurements as independent questions and narrow the Wilson bound on a precision the
design does not have. The seed-to-seed variation is not discarded by that choice — it is exactly
what `noise_floor` reduces, entering X as `MARGIN_K × floor`.

### No architectural changes; no authentication gates; no package installs

`pyproject.toml` is byte-unchanged (RPT-03). Zero installs.

## Detachment Evidence

Every launch used 23-20's measured recipe verbatim (`os.setsid()` inside the bootstrap, `os.execv`
to preserve the pid, the pid taken from the **log**, never `$!`, probed with `os.getsid()` from a
second interpreter, held by `caffeinate -is -w`). The log is appended, so all six `SESSION` lines
survive as one trail; the probe reads the **last** one.

| launch | pid = pgid = sid | outcome |
|--------|------------------|---------|
| 1 | `SESSION pid=57006 pgid=57006 sid=57006` | drew all 13,824, then **died** on the Tensor bug — the deviation above |
| 2 | `SESSION pid=71362 pgid=71362 sid=71362` | seed 1337 scored |
| 3 | `SESSION pid=80736 pgid=80736 sid=80736` | seed 2024 scored |
| 4 | `SESSION pid=91459 pgid=91459 sid=91459` | seed 1338 scored |
| 5 | `SESSION pid=183 pgid=183 sid=183` | seed 2025 scored |
| 6 | `SESSION pid=8854 pgid=8854 sid=8854` | seed 1339 scored |

`head -1 results/phase23_never_taught_run.log` → `SESSION pid=57006 pgid=57006 sid=57006`.
`grep -c "SESSION pid=" …` → **6**, not 5. **That is one more launch than seeds**, and it is the
failed first attempt, not a hidden retry. Stated plainly because the plan's criterion expected N.

**The per-seed commit criterion, against its recorded baseline:**
`git log --oneline -- data/phase23_run_state.json | wc -l` was **5** before the run (the plan's
MEASURED "3" was stale — 23-11 and 23-13 had added two) and is **10** after: baseline **+ N = 5**,
one commit per scored seed, each made between launches. The record write is a separate commit. The
mechanism is real rather than intended: the driver's git surface is read-only (`ls-files` at `:859`
and `:2145`, `show` at `:2191`), so the sub-mode scores one unscored seed and **exits**, and the
commit is the operator's act at the process boundary.

## Verification

| Check | Result |
|-------|--------|
| `.venv/bin/python -m pytest tests/test_phase23_ctrl.py -v` | **18 passed, 0 skipped** (7 pre-existing + 11 new) |
| the degradation parametrization | **5 cases**, all pass — MEASURED by AST: 2 `raise` at `mitigation_gate.py:405`/`:410`, 3 `_prove` at `:417`/`:425`/`:436` |
| `pytest tests/test_phase23_prereg.py tests/test_phase23_budget.py -q` | 55 passed |
| **full suite** `pytest tests/ -q` | **`1589 passed, 1 skipped`** against the `1578 passed, 1 skipped` baseline — delta **+11**, exactly the tests added. Zero failures, zero new skips. |
| `make lint` | clean, 245 files |
| gate provenance | `never-taught`, 5 distinct seeds, keys `arm, device, git_sha, git_sha_per_seed, governs, k, questions, record, record_sha256, reduction, seeds, torch_version` — a superset of BOTH `EXTRACTION_FLOOR_PROVENANCE_KEYS` and `FLOOR_PROVENANCE_KEYS` |
| X-not-published key walk (both conjuncts) | `[]` |
| `git diff --exit-code -- results/phase23_never_taught.json` after the refusal cases | clean — degradations are made on COPIES |
| `git diff --exit-code -- results/phase23_never_taught_training.json` | clean — **no adapter was retrained**, and each live sha256 matches the training record's |
| AST import census over `scripts/phase23_run.py` | includes `phase18_extraction` — the predicate is imported, not grepped for |
| `git ls-files 'results/phase23_noised_*'` | **1**, unchanged from 23-11 — this plan writes no sweep point and the log is outside that glob |
| `git log --format=%H -- scripts/phase23_matched_prereg.py \| wc -l` | **1** |
| frozen pins vs this plan's start commit `920dbe3` | `git diff --exit-code` on `mitigation_gate.py`, `mitigation_accountant.py`, `phase23_prereg.py`, `phase23_matched_prereg.py`, `phase23_resume_prereg.py`, `mitigation_budget.py`, `phase18_extraction.py`, `pyproject.toml` — **all clean** |

### Task 4's narrow guards

| Guard | Result |
|-------|--------|
| `grep -c "^- \[x\] \*\*CTRL-03\*\*"` | **1** (MEASURED 0 at HEAD before) |
| every changed line names CTRL-03 (`^[<>]` on swapped indicators) | **0 violations** over **4** changed lines — the filter is not vacuous |
| no already-closed row re-ticked (`CAL-0[1235]\|DPSGD-06`) | **0** |
| all six of `ROADMAP.md:562` | `{'CAL-01': True, 'CAL-02': True, 'CAL-03': True, 'CAL-05': True, 'DPSGD-06': True, 'CTRL-03': True}` |
| `git diff --exit-code -- scripts/ tests/ results/ ROADMAP.md STATE.md pyproject.toml` at Task 4 | clean — the task edited ONE file |

**Zero `gsd-sdk` mutation handlers were called.** `.planning/REQUIREMENTS.md`, `.planning/STATE.md`
and `.planning/ROADMAP.md` were all hand-edited with `Edit` and diffed, per the standing hazard that
seven `state.*` / `roadmap.*` verbs corrupt planning frontmatter and that
`roadmap.update-plan-progress` keys on SUMMARY existence.

## What CTRL-03's Tick Rests On

CTRL-03 asks for *"a never-taught fresh adapter at identical budget and seed, serving double duty as
frontier floor and relearning reference; depends on nothing, scheduled early."* Every clause is
discharged by measurement, not by assertion:

- **fresh adapter, identical budget** — 23-08 trained five with ZERO persona facts, every budget
  constant an *imported symbol* (`tp.LR`, `tp.MAX_STEPS`, `tp.BATCH_SIZE`, `tp.WEIGHT_DECAY`,
  `tp.LORA_CFG`, …), so "identical" is literally the same symbol as the taught arms.
- **and seed** — the ladder `(1337, 2024, 1338, 2025, 1339)`, five distinct values against the
  frozen `EXTRACTION_FLOOR_MIN_SEEDS = 2`, imported and never retyped. The gate's reason for that
  minimum was watched firing on a single-seed degradation of this very record.
- **double duty** — `consumers` matches the training record's list exactly, seed lists are identical
  in both, the scored record cites the training record by path and live digest, every scored
  adapter matches the scheduling's export digest, and 23-08's AST census proves exactly one
  `train_never_taught` definition and one call site exist under `scripts/`. *Scheduled once,
  consumed twice* is a checked property.
- **the frontier floor is now MEASURED and committed** — and accepted by the frozen
  `extraction_ceiling`'s real code path.

The one thing the tick does **not** claim: that the floor is a rich estimate of run-to-run variance.
It is `0.0` over five identical readings. That is recorded in the requirement's own note.

## Known Stubs

None. No hardcoded empty value, placeholder or unwired data source was introduced. The one value
that *looks* like a placeholder — `extraction_noise_floor: 0.0` — is a measured reduction over five
committed readings and re-derives under exact `==` on every suite run.

## Threat Flags

None. This plan introduces no network endpoint, no auth path, no new file-access pattern and no
schema change at a trust boundary. It writes one committed JSON artifact and one log, both under
`results/phase23_*`, and reads three frozen modules without editing any of them.

## Retained but Uncommitted

`data/phase23_never_taught_seed{1337,2024,1338,2025,1339}_draws.json` — ~1 MB each of raw generated
text, in gitignored `data/`. **Every measurement taken off them is committed**, and their sha256
digests are pinned in `results/phase23_never_taught.json`'s `evidence[].raw_draws_sha256`, so the
retained files are identifiable. They are model output, not measurement; the record's
`evidence[].per_question` rows and `per_seed[].per_cell[].per_fact` counts are the committed
evidence, and the assembly proved the published counts re-derive from those raw draws.

## Self-Check: PASSED

- `results/phase23_never_taught.json` — FOUND (1,109,573 bytes, committed at `956238b`)
- `results/phase23_never_taught_run.log` — FOUND (352 lines, 6 `SESSION` lines)
- `scripts/phase23_run.py` — FOUND (modified, `never-taught` in `_TABLE` and `USAGE`)
- `tests/test_phase23_ctrl.py` — FOUND (18 tests)
- `.planning/REQUIREMENTS.md` — FOUND (`- [x] **CTRL-03**` present exactly once)
- commits `92b48a9`, `ec90611`, `6e17446`, `8a2942f`, `959dbb8`, `2bb6327`, `1274273`, `77e273d`,
  `956238b`, `22db5b6`, `87f6f2e` — all FOUND in `git log`
