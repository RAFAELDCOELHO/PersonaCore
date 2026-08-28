---
phase: 23
plan: 11
subsystem: cost-calibration
tags: [CAL-01, CAL-05, DPSGD-06, D-04, dp_n64, throughput, cost-record]
requires:
  - results/phase23_matched_verdict.json (23-19) — the gate's verdict conjunct
  - .planning/STATE.md @ 746ecf6 (the user, 2026-08-28) — the gate's human-act conjunct
  - results/phase23_matched_control.json (23-20) — training.non_dp
  - results/phase23_control_floor.json (23-08) — training.non_dp_superseded_protocol
  - results/phase23_sigma_zero.json (23-10) — training.dp_n8 and the T cross-check
  - results/phase18_preflight_report.md (18-13) — the throughput cross-validation target
provides:
  - results/phase23_noised_dp_n64_sigma0p500000.json — the milestone's FIRST noised sweep point
  - results/phase23_cost.json — four training legs, the floor/ceiling bracket, four ratios, the K sizing table
  - results/phase23_cost_run.log — the detachment evidence for both GPU legs
  - scripts/phase23_run.py::{noised,throughput,cost-record} + the ONE D-04 gate predicate
affects:
  - 23-12 (quotes the eleven pre-registered figure paths verbatim)
  - 23-13 (selects a K rung from the committed sizing table)
tech-stack:
  added: []
  patterns:
    - "one gate object, imported production -> test, never a second copy"
    - "a published figure is a scalar leaf written by json.dump from a computed float"
    - "a committed guard is WIDENED additively; the original assertion survives byte-identical"
key-files:
  created:
    - results/phase23_noised_dp_n64_sigma0p500000.json
    - results/phase23_cost.json
    - results/phase23_cost_run.log
    - results/phase23_sweep1_dp_n64/run.csv
  modified:
    - scripts/phase23_run.py
    - tests/test_phase23_matched.py
    - tests/test_phase23_cost.py
    - tests/test_phase23_resume.py
    - data/phase23_run_state.json
decisions:
  - "sigma = 0.5 — this phase's own committed CAL-03 value; the RETRACTED 'sigma >= 0.42' figure is not cited"
  - "C = 1.0 BINDS, because at sigma>0 C is the noise scale (std = sigma*C) and 1e6 would destroy the adapter"
  - "training.non_dp comes from results/phase23_matched_control.json; the superseded control is recorded BESIDE it"
  - "the run prefix is phase23_sweep1, NOT the plan's phase23_noised, so no run.csv lands inside NOISED_RECORD_GLOB"
  - "CAL-01/CAL-05 measured but NOT ticked: .planning/REQUIREMENTS.md stays byte-unchanged because 23-12 owns that row"
metrics:
  duration: ~85 min (2 detached GPU legs: 23.1 min training + ~7 min throughput; the rest CPU)
  completed: 2026-08-28
---

# Phase 23 Plan 11: CAL-01 dp_n64 Timing and CAL-05's Floor-to-Ceiling Throughput Bracket Summary

The milestone's first noised sweep point ran at `dp_n64` / σ=0.5 behind a two-conjunct D-04 gate,
priced the DP training leg at `1383.276182374917` s and the per-point evaluation leg as a measured
`5.72 → 9.01` h bracket whose **floor already exceeds** the committed 4.77 h/point figure.

---

## BINDS-OR-NOT, established BEFORE anything was edited (Task 1a)

The plan required this to be settled first. The answer is **YES, `test_no_noised_point_exists`
binds on this plan**, and it is measurable three ways — all three re-measured at HEAD:

1. **Task 2 emits under the glob, by construction.** The record path is produced by
   `phase23_prereg.noised_record_path("dp_n64", 0.5)`, which returns
   `results/phase23_noised_dp_n64_sigma0p500000.json` — measured `fnmatch(..., NOISED_RECORD_GLOB)`
   → `True`. Committing it takes `git ls-files 'results/phase23_noised_*'` from **0 to 1**, which
   is exactly the condition the unmodified guard asserts against.
2. **The `CAL03_WIRING_RECORD` precedent does NOT exempt it.** That exemption's stated criterion is
   three substantive legs plus one declarative: *exports no adapter, scores no question, runs a toy
   `ModelConfig` under `max_steps_override` — and its own record declares `sweep_point: false`.*
   This run **exports** an adapter (`checkpoints/phase23_sweep1_dp_n64_adapter.pt`, 1.35 MB, sha256
   recorded), **scores** 768 real draws on the real attack shapes in Task 3, and runs the
   **unmonkeypatched** production budget (`MAX_STEPS = 200`). It fails all three substantive legs
   and cannot honestly declare the exemption; its record declares `sweep_point: true`.
3. **`tests/test_phase23_prereg.py` leaves no third door.**
   `_prove_noised_record_is_under_the_glob` refuses a σ>0 record that neither lives under the glob
   nor declares `sweep_point: false` — silence is a refusal, not an exemption. (This rule then
   *fired for real* on `results/phase23_cost.json`; see Deviations.)

**Route chosen: WIDEN.** `tests/test_phase23_matched.py` is a normal test file — measured **4
commits** at the time, and no pin registry or ancestry guard names it (`_assert_ordering_holds`
binds `scripts/phase23_*prereg.py` against the `results/phase2{0,1,3}_*` globs). So 23-20's
edit-once hazard does not apply, and the applicable precedent is 23-20's own on a non-pin test:
*"One pre-existing test was widened, not deleted."*

---

## Task 1 — the guard, widened; the gate, built once

`git diff --numstat` on Task 1's own commit (`38f8e52`): **305 insertions, 0 deletions.**
There is **no deleted line to account for**, by construction: the dated block was inserted *inside*
the existing docstring above its closing `"""`, and the new branch was inserted *between* the
untouched `git ls-files` call and the untouched final assertion. The retained assertion and its
message are byte-identical to their committed form.

| acceptance check | result |
|---|---|
| `pytest -k "noised or unblock"` | 4 passed |
| tripwire collects **3** cases | `absent-sentinel` / `wrong-sha` / `code-in-act`, all pass |
| sha PINNED (AST over top-level `Assign`) | `['746ecf699904e7c97bf73614e1c617a646da30ad']` |
| act shape `[ "$(git show --name-only --format= 746ecf6 \| grep -c -E '^(scripts\|src)/')" = 0 ]` | exit 0 |
| `tracked == []` survives **by identity** (AST `Compare`) | `True` |
| assert count inside the function (secondary) | **6** (1 retained + 5 new) |
| no `skip`/`skipif`/`xfail` decorator added | `[]` |

The four paths `746ecf6` touched, quoted: `.planning/ROADMAP.md`, `.planning/STATE.md`,
`.planning/phases/22-.../deferred-items.md`, `.planning/phases/23-.../deferred-items.md` — **zero
under `scripts/` or `src/`**.

**W17 disclosure — the `-S` set size.** `git log -S<sentinel> --format=%H -- .planning/STATE.md`
returns **1** sha today. Membership (`sha in shas`), never a positional read, is what is asserted,
and the size travels in both the failure message and the record's `unblock_sentinel_shas_n` field
so a set that grows is visible rather than absorbed. **This plan's own STATE.md edit deliberately
does not repeat the sentinel verbatim, so the set is still 1 after this commit** — verified by
counting occurrences in the working tree (1) before committing.

**The gate is written once.** Task 2 moved `UNBLOCK_SENTINEL`, `UNBLOCK_COMMIT` and
`unblock_act_is_committed` into `scripts/phase23_run.py`, and the test now binds
`_unblock_act_is_committed is phase23_run.unblock_act_is_committed` via
`test_the_unblock_gate_has_one_source`. Direction is production → test, never the reverse — a
production driver importing from `tests/` would make running this phase depend on the test tree
being importable, which `_count_composed_steps`' docstring already records. The test's two restated
literals follow `_MEASURED_DP_PRE_CLIP_MAX`'s established register: a literal asserted equal to its
production source is not a second source.

---

## Task 2 — the first noised sweep point

**Both verdicts, read and printed before any GPU second** (log lines 2–4):

| record | `verdict` | role |
|---|---|---|
| `results/phase23_sigma_zero.json` | `HALT` | read and printed; **never** the gate |
| `results/phase23_matched_verdict.json` | `proceed` | **the gate's first conjunct** |

**The human unblock act, by full sha:** `746ecf699904e7c97bf73614e1c617a646da30ad`, asserted
`== UNBLOCK_COMMIT`, dated `Fri Aug 28 10:32:54 2026 -0300`, four planning paths, **0** under
`scripts/` or `src/`. `sigma_zero_record_file_sha256` in the verdict record
(`dd34e51398b87d54c4e83dcfd192a0e7abead7c73d143aeb28b11cfa07e85d36`) **matches** the live digest of
`results/phase23_sigma_zero.json`, and both gate records were asserted committed via `git ls-files`.

**Detachment probe, quoted verbatim, printed BEFORE any GPU second:**

```
DETACHED OK — pid 55784 is its own session leader; caffeinate holding
SESSION pid=55784 pgid=55784 sid=55784
```

`head -1 results/phase23_cost_run.log` → `SESSION pid=55784 pgid=55784 sid=55784` — all three equal.
The pid came from the log's first line, never from `$!`; the probe is `os.getsid(pid)` from a second
interpreter, never `ps -o sid`. The second leg (Task 3) appended its own
`SESSION pid=62745 pgid=62745 sid=62745` and was probed the same way.

**CAL-01, measured on the DP path with the seam active, per CAPACITY:**

| figure | value | denominator |
|---|---:|---|
| `seconds_total` | `1383.276182374917` s | the whole `train_arm` call |
| `seconds_per_optimizer_step` | `6.916380911874585` s | ÷ **200** timed iterations |
| `grad_accum_steps` | **64** | `= n_facts`, proven against the seam's own `_records` |
| `replay_micro_batches_per_step` | **32** | `= ceil(4·64/8)`, proven against `replay_window_budget(64)//BLOCK_SIZE` |
| `clip_bind_count` | **12800** | `= 200 × 64` — C=1.0 bound on **every** record |
| `records_per_lot` | **64** | the seam's last lot |
| ε | `519.6981942303134` | `epsilon_for(0.5, 200, 1e-05)` |

**Against research's projection, stated in both directions.** Research projects `dp_n64` at ~30 min
(1800 s). Measured `1383.276182374917` s = **0.768 of that projection — 23.2% BELOW it.** The
projection is **not** a bound in either direction: 23-10 measured the same projection method
over-stating the `dp_n8` figure by at least 10.8% and `RETRACTED IN PLACE` its lower-bound status
(`23-RESEARCH.md:665-685`). The delta is reported as a measurement against an unreliable estimate,
not as a pass against a bound.

**The T cross-check, and what it does not claim.** `t_n8 = 200 == t_n64 = 200`, both from
`_count_composed_steps` (real `DPSGD.finalize` invocations, never a checkpoint field). The record
carries `epsilon_comparison_made: false` with its reason: the two runs are at **different σ**
(0.0 and 0.5) and D-05 requires a fixed σ, so this leg tests **T only**.
`results/phase23_cal03_wiring.json` remains the record CAL-03's verdict is read from.

**Artifact hygiene, measured after the commit:**

- `git ls-files 'results/phase23_cost_run.log' | wc -l` → **1**
- `git ls-files 'results/phase23_noised_*' | wc -l` → **1** (only the record; the log is **not** in
  the glob, and neither is the run CSV — see Deviations)
- Derived path verified by **calling** `noised_record_path("dp_n64", 0.5)` and comparing to disk:
  `results/phase23_noised_dp_n64_sigma0p500000.json`, exists → `True`
- Ordering: σ=0 first added at `2d06989` (Thu Aug 27 03:53:56) — the noised record at `ab9d246`
  (Fri Aug 28 15:00:35). **Strictly earlier.**

---

## Task 3 — CAL-05's bracket, and the cost record

### Part A — per shape, per condition (768 timed draws total)

Every shape: 8 strided prompts × 8 draws = **64 timed draws per condition**, after **4 warm-up
draws discarded**.

| shape | `n_draws` | `draws_per_min_floor` | `draws_per_min_ceiling` | `stop_floor` | `stop_ceiling` | `mean_tokens_floor` | `mean_tokens_ceiling` |
|---|---:|---:|---:|---:|---:|---:|---:|
| A1-mild | 64 | `146.17565608657875` | `76.33674733338722` | 62/64 | **0/64** | `25.234375` | `48.0` |
| A1-aggressive | 64 | `109.29468131023829` | `79.39714731528025` | 57/64 | **0/64** | `32.84375` | `48.0` |
| A2 | 64 | `153.44193383538487` | `79.90676177963012` | 57/64 | **0/64** | `25.390625` | `48.0` |
| A3 | 64 | `103.43725441713096` | `78.8667075237667` | 56/64 | **0/64** | `33.203125` | `48.0` |

The ceiling condition is confirmed by its own arithmetic: **0/64 stop-terminated and mean exactly
`48.0` tokens on every shape** — every draw ran the full `RECALL_MAX_NEW_TOKENS`.

**The bracket:**

- `h_per_point_floor` = **`5.7223403197590965`** h (stop ids ACTIVE)
- `h_per_point_ceiling` = **`9.013691285839306`** h (stop set EMPTIED)
- pooled `wall_multiplier` = **`1.5816071135660466`** vs research's pre-sizing **1.536×** →
  **+2.97%**, i.e. slightly worse than research's bracket predicted
- pooled `token_multiplier` = **`1.6456408196062675`** vs research's **1.751×** → **−6.0%**, i.e.
  the noised adapter emits *fewer* extra tokens than research bracketed

**The finding: the committed 4.77 h/point sits BELOW the measured FLOOR.** It was measured on the
un-adapted base, where 45–56 of 64 draws terminated early; the noised `dp_n64` adapter is slower at
both ends. `h_per_point` is composed by Phase 18's own method — per-shape minutes summed, with
family zero priced at the slowest measured rate — so the two figures are comparable.

### The un-adapted-base cross-validation

| shape | measured (base, floor) | committed | agreement | stop-terminated |
|---|---:|---:|---:|---:|
| A1-mild | `154.18168689919418` | `145.01` | **106.32%** | 56/64 |
| A1-aggressive | `127.88914995037322` | `134.54` | **95.06%** | 45/64 |
| A2 | `176.20528463152064` | `183.2` | **96.18%** | 56/64 |
| A3 | `136.2241779118406` | `140.85` | **96.72%** | 51/64 |

The committed rates were **parsed from `results/phase18_preflight_report.md`**, never retyped. The
stop-terminated counts reproduce the committed table **exactly** — 56 / 45 / 56 / 51 of 64. Neither
the hardware nor the stack has moved under the committed cost artifact.

### Part B — the `training.non_dp` provenance decision, stated explicitly

Three non-DP figures exist and they disagree materially:

| source | protocol | training |
|---|---|---:|
| `23-RESEARCH.md:637-641` | accum=1, loop-only **PROJECTION**, never a real run | 20.4 s — *research's own rounding of a projection* |
| `results/phase23_control_floor.json` | OLD control: 8-window lots, teaching weight 0.4342, `grad_clip` binding | `79.14336965046823` s mean / 5 seeds |
| `results/phase23_matched_control.json` | PROTOCOL-MATCHED: accum=8, 32 replay windows/step, weight 1.0, `dp_seam_active=False` | `161.12400419991462` s mean / 5 seeds |

**Both measured means were COMPUTED in code** from `training_seconds_per_seed` (a dict —
`.values()`) and `per_seed[i].training_seconds`, not retyped from this table.

**Decision: `training.non_dp` comes from `results/phase23_matched_control.json`.** The three-point
argument, written into the record's `provenance_argument`:

1. **It is a REFERENCE quantity, by use.** Its only consumers are the `ratios` block and 23-12's
   retraction, both of which compare non-DP against DP. A ratio is meaningless unless numerator and
   denominator describe the same experiment.
2. **The three invalidating mechanisms are wall-clock mechanisms too, and the effect is MEASURED.**
   `training.non_dp.wall_clock_gap_vs_superseded` = **`2.035849685343305`**, computed at write time
   from the two `training_seconds_mean` fields. **This measurement is NOT 8.125, so it REFUTES the
   naive per-step-work equality** an earlier draft asserted ("8.125× the lot volume is 8.125× the
   work per step; the measurement confirms it") — it does not confirm it. The conclusion needs only
   the measured gap and survives without the equality: the two protocols do not time the same work,
   so they cannot share a ratio denominator.
3. **The consequence is the finding, not a rounding.** Both DP/non-DP multiples are computable from
   the record's own fields and are named that way; no rounded numeral is written for either.

**Scope, stated honestly and not overstated:** `deferred-items.md`'s **CONTROL PROVENANCE** rule
governs the formal gate's three UTILITY fields — `control_taught_recall`, `control_heldout_recall`,
`control_gap` — and requires them to come from the matched record. **Timing is not one of those
three.** This decision is made and argued here on its own merits; it is **not** inherited from that
rule, and the record says so.

The old protocol's figure is **recorded beside it**, never deleted, as
`training.non_dp_superseded_protocol` with its protocol named and its own `source_record` +
`source_record_sha256`.

### W6 — where every required key of the two ASSEMBLED blocks came from

`validate_record` was run against **named mappings**: the four `training.*` blocks at
`kind="training"` and the `generation` block at `kind="generation"`. `ratios` and `sizing` are
derived and covered by the re-derivation test instead. Command output: `OK ['dp_n64', 'dp_n8',
'non_dp', 'non_dp_superseded_protocol']`.

**The aggregate convention was COPIED from `results/phase23_never_taught_training.json`**, not
invented: `seed` is a **LIST**, `seconds_total` the **SUM** across seeds, `timed_iterations` the
**SUM** of timed steps, `seconds_per_optimizer_step` their quotient, `warmup_iterations_discarded`
**0**. The per-seed list, mean, min and max ride beside the required keys as extra fields.

**`training.non_dp`** (all thirteen keys were missing at top level of its source):

- from `per_seed[i]`: `arm`, `capacity_n_facts` (`n_facts`=8), `grad_accum_steps` (8),
  `replay_micro_batches_per_step` (4), `max_steps` (200), `batch_size` (8), `block_size` (256),
  `dp_seam_active` (`False`)
- from the **top level**: `device`, `torch_version`, `python_version`, `git_sha`, `n_seeds` (5),
  `training_seconds_per_seed`
- **computed**: `seconds_total`, `timed_iterations`, `seconds_per_optimizer_step`,
  `warmup_iterations_discarded`, `seed`

**`training.non_dp_superseded_protocol`** (thinner still — and the gap is a finding, not a default):

- from `per_seed[i]`: `arm`, `capacity_n_facts` (8), `training_seconds`
- from `recipe.budget_constants`: `max_steps` (200), `batch_size` (8), `block_size` (256)
- from the **top level**: `device`, `torch_version`, `python_version`, `git_sha`, `n_seeds`
- **from the record's OWN PROSE, cited by `residual_differences` index** — sourcing, not inventing,
  and every citation travels in the record under `prose_sourced_keys`:
  - `grad_accum_steps = 1` — `residual_differences[1].difference`: *"grad_accum_steps is 1 here and
    `n_facts` on the DP path"*
  - `replay_micro_batches_per_step = 0` — `residual_differences[0].difference`: *"replay lives IN
    the teaching bin here; it is drawn at TRAIN time on the DP path"* (no separate replay pass, so
    the per-optimizer-step count is zero)
  - `dp_seam_active = False` — `residual_differences[3].why_not_eliminable`: *"`DPSGD` is
    constructed only when `is_dp`"*, and this arm is the non-DP control
- **computed**: the same five aggregate fields

**No key was unsourceable, so no escalation was required.**

### The eleven pre-registered figure paths — all resolve, at full stored precision

```
training.non_dp.training_seconds_mean                        161.12400419991462
training.non_dp_superseded_protocol.training_seconds_mean     79.14336965046823
training.non_dp.wall_clock_gap_vs_superseded                   2.035849685343305
training.dp_n8.seconds_total                                 205.44225783273578
training.dp_n64.seconds_total                               1383.276182374917
generation.h_per_point_floor                                   5.7223403197590965
generation.h_per_point_ceiling                                 9.013691285839306
ratios.non_dp.eval_over_training_ceiling                     201.39326098648866
ratios.non_dp_superseded_protocol.eval_over_training_ceiling 410.006407009605
ratios.dp_n8.eval_over_training_ceiling                      157.94846187604026
ratios.dp_n64.eval_over_training_ceiling                      23.458286235587472
GAP RE-DERIVES
```

The three MEASURED-known values reproduce exactly: `2.035849685343305`, `161.12400419991462`,
`79.14336965046823`. None is a shorter rounding, so none was typed.

### All four `eval ÷ training` ratios, at the record's own precision — and the "~1,010×" claim

| block | protocol | s/point (source field) | `eval_over_training_ceiling` | `eval_over_training_floor` |
|---|---|---:|---:|---:|
| `non_dp` | protocol-matched non-DP comparator | `161.12400419991462` (`training_seconds_mean`) | `201.39326098648866` | `127.85447614355938` |
| `non_dp_superseded_protocol` | old unmitigated control (superseded) | `79.14336965046823` (`training_seconds_mean`) | `410.006407009605` | `260.2924950265985` |
| `dp_n8` | dp_n8, seam active, σ=0 | `205.44225783273578` (`seconds_total`) | `157.94846187604026` | `100.27355310661025` |
| `dp_n64` | dp_n64, seam active, σ>0 | `1383.276182374917` (`seconds_total`) | `23.458286235587472` | `14.892488870707165` |

**Which arm, at which protocol, is the "~1,010×" sentence true of? NONE of the four.** The largest
measured ratio is `410.006407009605`, on the arm the record itself argues is the **wrong**
comparator; the matched comparator gives `201.39326098648866`, the σ=0 DP arm
`157.94846187604026`, and the expensive DP capacity `23.458286235587472` — **a factor of ~43 below
the claim.** The 843×/~1,010× family came from the 20.4 s loop-only projection whose lower-bound
status 23-10 already retracted, and **no measured `train_arm` run in this repository reproduces
it.** The correction of the claim itself is 23-12's; `.planning/REQUIREMENTS.md` is byte-unchanged
here (`git diff --exit-code` → 0).

### The K-rung sizing table (16 sweep points), pricing the never-taught floor at N=5

| K | draws/point | projected (ceiling) | floor-derived | never-taught floor (N=5) | total |
|---:|---:|---:|---:|---:|---:|
| 48 | 42480 | `144.2190605734289` h | `91.55744511614554` h | `45.06845642919653` h | `189.2875170026254` h |
| 24 | 21744 | `73.82060388673818` h | `46.864997330637216` h | `23.068938714605682` h | `96.88954260134386` h |
| 16 | 14832 | `50.354451657841274` h | `31.967514735467766` h | `15.735766143075399` h | `66.09021780091668` h |
| 8 | 7920 | `26.88829942894437` h | `17.070032140298323` h | `8.402593571545117` h | `35.29089300048949` h |

N=5 is **read** from `results/phase23_never_taught_training.json`'s `n_seeds`, never assumed. Every
rung is sized against the ceiling, because the K ratchet has no cheap direction.

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The plan's `prefix="phase23_noised"` would have filed a run CSV INSIDE `NOISED_RECORD_GLOB`**

- **Found during:** Task 2, before launching
- **Issue:** `arm_outputs(arm, prefix=)` renders `results/{prefix}_{arm}/run.csv`, and run.csv files
  **are committed** in this phase (`results/phase23_sigma0_dp_n8/run.csv` and nine others are
  tracked). `prefix="phase23_noised"` therefore produces `results/phase23_noised_dp_n64/run.csv`,
  which **matches** `results/phase23_noised_*` — measured `True`. This is the same defect the plan's
  own environment note raises against the run LOG, one artifact over: the glob every ordering guard
  binds on would gain a non-record member, Task 1's derivation conjunct would try to `json.loads` a
  CSV, and the plan's own acceptance criterion (`git ls-files 'results/phase23_noised_*'` = **1**)
  would be violated. The plan also lists a literal placeholder path
  `results/phase23_noised_dp_n64_sigma<σ>.json` in its frontmatter, which was never created.
- **Fix:** `NOISED_RUN_PREFIX = "phase23_sweep1"`, retaining the load-bearing `phase23_` head
  (anything outside it falls outside the Phase-23 ancestry guards entirely). Measured after the
  change: every one of the five `arm_outputs` paths returns `False` against the glob.
- **Files modified:** `scripts/phase23_run.py`
- **Commit:** `52fd49d`

**2. [Rule 1 - Bug] The noised record carried no top-level `arm`, and the widened guard raised `KeyError`**

- **Found during:** Task 2, immediately after the first artifact commit
- **Issue:** Task 1's derivation conjunct calls
  `phase23_prereg.noised_record_path(payload["arm"], payload["sigma"])` on every tracked member of
  the glob. The record carried `arm` only under `training` and `recipe`, so it could not prove its
  own path. Watched RED (`KeyError: 'arm'`) on the freshly committed record.
- **Fix:** the record now carries `arm` at top level. **No measurement was re-taken** —
  `_already_trained` verified the exported adapter's sha256 against the working state and reused it;
  every figure is byte-identical (`seconds_total 1383.276182374917`, `seconds/step
  6.916380911874585`, `clip_bind_count 12800`). The only other diff lines are the provenance
  timestamp and `git_sha`, because the record was re-emitted by the fixing commit's code.
- **Files modified:** `scripts/phase23_run.py`, `results/phase23_noised_dp_n64_sigma0p500000.json`
- **Commit:** `bcdfb71`

**3. [Rule 1 - Bug] `results/phase23_cost.json` carried a positive top-level `sigma` and no `sweep_point` declaration**

- **Found during:** Task 3, after the Part B commit
- **Issue:** `tests/test_phase23_prereg.py::_prove_noised_record_is_under_the_glob` reddened: the
  cost record names σ=0.5 (to say **which** sweep point's adapter the bracket was measured on) and
  the committed rule leaves exactly two doors for a σ>0 record — live under the glob, or declare
  `sweep_point: false` and say why. Silence is a refusal, not a third door. This is the rule
  working as designed.
- **Fix:** the record takes the second door **honestly**: it trains nothing, scores nothing and
  exports no adapter, and it now carries `sweep_point: false`, a `sweep_point_false_reason`, and a
  `sweep_point_record` pointing at the run that IS under the glob and declares `sweep_point: true`.
  **No guard was weakened and the rule was not edited.** Regenerated from the same committed inputs;
  all eleven figure paths byte-identical and the gap still re-derives.
- **Files modified:** `scripts/phase23_run.py`, `results/phase23_cost.json`
- **Commit:** `c6e8673`

**4. [Rule 1 - Bug] `tests/test_phase23_resume.py`'s `train_arm` call-site census reddened on the new site**

- **Found during:** Task 3, on the full-suite run
- **Issue:** three separate teeth fired in sequence, each correctly: the total grep count (21 hits
  vs a 20-entry register), the per-file `_RESUME_PASSERS` count for `scripts/phase23_run.py`
  (`train_noised` also passes `resume_from`), and the pinned literal `8 + 1 + 1`.
- **Fix:** the register was **EXTENDED, never weakened** — a 21st entry naming `train_noised` with
  its reason, `_RESUME_PASSERS["scripts/phase23_run.py"]` 1 → 2, and the literal
  `8 + 1 + 1` → `8 + 1 + 1 + 1` with its reason spelled in the comment ledger exactly as that
  register's own discipline requires ("BUMPED with its reason rather than derived from the
  register"). Each tooth was watched RED, then GREEN.
- **Files modified:** `tests/test_phase23_resume.py`
- **Commit:** `8876b8c`

### Deliberate departures from the plan text

**A. C = 1.0, not the σ=0 arm's non-binding `1e6`.** The plan names `dp_clip_norm=<C>` without
pinning a value and requires the reasoning to be recorded. At σ=0 the only thing C could do was
clip, so `1e6` was chosen to be non-binding. At σ>0, `dpsgd._draw_noise` uses `std = σ · C` on the
summed accumulator before the divide by N, so **C is also the noise scale**: `1e6` would draw noise
at std 500,000 against gradient norms measured in `[0.3359, 2.2901]`, destroying the adapter by six
orders of magnitude and making its stop behaviour **pathological rather than representative** —
which is precisely what CAL-05's bracket must not be. `1.0` is the `grad_clip` the old unmitigated
control ran at and it **binds** on the DP path's measured pre-clip norms (1.54–2.28 over 25 sampled
steps), which is what a real sweep point does. Measured `clip_bind_count = 12800 = 200 × 64`.

**B. The gate predicate lives in `scripts/phase23_run.py`, not in the test file.** The plan says
"Import or re-use Task 1's predicate rather than writing a second copy". Task 1 wrote it in the test
file; Task 2 moved it to the driver and made the test import it, because a production driver
importing from `tests/` is refused by this repository's own register. The test's AST pin criterion
was re-verified green after the move.

**C. The two GPU legs are two detached launches, one log.** The plan says Task 3 Part A "is part of
the same detached run as Task 2". They cannot literally be one process: the plan itself mandates
committing the noised record and running `pytest` **between** them (Task 2e). Both were launched
detached with 23-20's recipe onto the same `results/phase23_cost_run.log`; because the log is
appended to, this launch's SESSION line is the **last** one rather than the first, so the probe
reads the last SESSION line. `head -1` still shows a valid `SESSION pid=N pgid=N sid=N` with all
three equal, which is what the acceptance criterion reads.

**D. `.planning/REQUIREMENTS.md` untouched — CAL-01 and CAL-05 are MEASURED but NOT ticked.** The
plan's frontmatter lists `requirements: [CAL-01, CAL-05]`, and its Task 3 acceptance criteria
require `git diff --exit-code -- .planning/REQUIREMENTS.md` to exit 0 because 23-12 owns the
retract-in-place of that row's falsified "~1,010×" claim. The criterion wins: no box was ticked and
the file is byte-unchanged. **This is a deliberate non-delivery of the frontmatter's requirement
ticks, recorded here rather than silently done either way.**

### Authentication gates

None.

---

## Frozen pins — all byte-identical, both one-commit pins still one commit

| check | result |
|---|---|
| `git diff --exit-code c7de5d4 HEAD -- scripts/phase23_prereg.py` | exit 0 |
| `git diff --exit-code c100388 HEAD -- scripts/phase23_matched_prereg.py` | exit 0 |
| `git log --format=%H -- scripts/phase23_matched_prereg.py \| wc -l` | **1** |
| `git log --format=%H -- scripts/phase23_resume_prereg.py \| wc -l` | **1** |
| `git diff --exit-code -- mitigation_{accountant,gate,budget}.py phase18_extraction.py phase14_recall.py REQUIREMENTS.md pyproject.toml` | exit 0 |

---

## Suite and lint

**`1559 passed, 1 skipped`** against a baseline of `1549 passed, 1 skipped`. The +10 are exactly the
guards this plan added: `tests/test_phase23_matched.py` +4 (the 3-case tripwire and
`test_the_unblock_gate_has_one_source`) and `tests/test_phase23_cost.py` +6
(`test_the_cost_record_is_committed`, `test_the_committed_cost_record_validates`,
`test_the_cost_record_ratios_re_derive`, `test_borrowed_figures_cite_a_record_and_a_digest`,
`test_every_timing_block_names_its_protocol`,
`test_the_sizing_table_prices_the_never_taught_floor`). `make lint` exits 0 over **245** files.

---

## Known Stubs

None. Every field in both emitted records is either measured in this plan, computed from measured
values, or read from a cited committed artifact with its sha256.

## Threat Flags

None. The plan's `<threat_model>` assigned `mitigate` to T-23-57, -57b, -57c, -57d, -58, -58b, -58c,
-59, -60, -61, -62, -63, -63b; each mitigation is implemented and named above. No new network
endpoint, auth path, file-access pattern or trust-boundary schema change was introduced — zero
package installs, `pyproject.toml` byte-unchanged (RPT-03).
