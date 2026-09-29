# Phase 30: Replay-Bearing Adversarial Recipe and Its Own Control - Context

**Gathered:** 2026-09-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire the adversarial arm to the train-time replay seam under new `advr_n8`/`advr_n64` arms, commit
the ARECIPE-02 mask-fraction calibration at that recipe, and make the arm's OWN ratio-0
replay-bearing control the sole source of recall floors, `control_gap` and relearning Z — with a
committed execution schedule that runs both controls first. Requirements: ARECIPE-01, ARECIPE-02,
ACTRL-01, ACTRL-02.

This phase trains NO scored point. The first replay-bearing point runs in Phase 31 (probe, own
probe path) and the sweep in Phase 32. The DP arms, the golden trajectory and the v4.0 `adv_*`
arms stay byte-unchanged.

</domain>

<decisions>
## Implementation Decisions

### Seam split & arm identity (ARECIPE-01)
- **D-01:** Replay reaches the adversarial arm through NEW arms `advr_n8` / `advr_n64` in
  `scripts/teach_persona.py` (`ARMS`, `arm_spec`, a new `REPLAY_ARMS` tuple). They mirror
  `adv_n8`/`adv_n64` (same facts, `replay_ratio = 0.0` in the bin — replay stays OUTSIDE the bin
  per D-10) and differ only in receiving the train-time seam. `adv_*` is untouched, so v4.0 stays
  reproducible and the arm name matches the Phase 29 D-01 point keys. No `--replay` flag.
- **D-02:** The `is_dp` gate at `teach_persona.py:1752` splits into TWO predicates:
  `is_dp = arm in DP_ARMS` keeps DPSGD, `grad_accum_steps = n_facts` and fact-aligned routing
  (`fact_bin`, `n_facts`); a separate `gets_replay = arm in DP_ARMS + REPLAY_ARMS` gates ONLY
  `replay_bin` / `replay_mask_bin` / `replay_windows`. The DP arms' `train()` kwargs are identical
  before and after the split. `replay_windows` for `advr_*` is the same expression the DP arms use
  (`replay_window_budget(n) // BLOCK_SIZE` = `REPLAY_WINDOWS_PER_FACT`·n), and must equal
  `phase29_prereg.replay_windows(n)`.
- **D-03:** "Byte-unchanged" is proven by (a) the existing golden-trajectory tests staying green
  UNMODIFIED, and (b) a new CPU test that captures the `train()` / `TrainConfig` kwargs for
  `dp_n8`, `dp_n64`, `adv_n8`, `adv_n64` and asserts them equal to the pre-split values (adv_*
  included, not only DP). No slow few-step checkpoint diff.
- **D-04:** SC1's "logs a non-zero replay count equal to the PREREG-04 recipe" is MEASURED from
  actual draws: a short CPU run of `advr_n8` counts replay windows drawn through `train()`'s
  `on_draw` hook and asserts per-step draws == `phase29_prereg.replay_windows(8)` (32) and > 0.
  Not a check of the configured kwarg.

### ARECIPE-02 calibration meaning
- **D-05 (premise measured in discussion):** The D-05 (Phase 24) derivation of
  `MIN_REFUSAL_SCORED_TOKENS = 15` is over the TEACHING BIN's mask fraction
  (`_prove_floor_and_band`, `teach_persona.py:701`). Train-time replay is a separate loss pass in
  `train()` (one full replay mean per optimizer step, `loop.py` replay_fn) and never enters the
  bin. The `teach_persona.py:1252` warning (0.359 → 0.403) is about a BIN-level replay ratio, which
  this recipe does not use.
- **D-06:** The calibration re-measures all four D-05 inputs LIVE at HEAD from `build_bins` on
  `advr_n8` at the worst grid corner (n=8, max adversarial ratio), recomputes `frac(L)` and the
  first L clearing `0.15 + MASK_FRACTION_MARGIN`, and commits `results/phase30_calibration.json`
  (path already pinned in `phase29_prereg`). It very likely reproduces 15; the record says so
  honestly WITH the structural reason (replay is outside the bin). The constant is IMPORTED from
  `phase24_adversarial`, never retyped.
- **D-07:** The same record carries the per-step teaching:replay token mix at BOTH capacities
  (8 teaching windows vs. 32 replay at n=8 and 256 at n=64; loss weighted 1:1 by `train()`) as a
  DESCRIPTIVE field — never gating, never read by a verdict — so Phase 34 can report the window
  asymmetry that the bin-level number alone would hide.
- **D-08:** If the re-derived floor ≠ 15, the calibration REFUSES to commit and the plan STOPS at a
  checkpoint for the developer's ruling. `MIN_REFUSAL_SCORED_TOKENS` is a frozen v4.0 input that
  shapes the adversarial corpus; it is never silently re-pinned.
- **D-09:** Recipe identity = `phase29_prereg._RECIPE_FIELDS` (n_facts, replay_windows, seed,
  max_steps — IMPORTED) + `MIN_REFUSAL_SCORED_TOKENS` + the replay source path
  (`data/dialog_train.bin`). The calibration records it; scoring refuses any point whose recipe
  differs from the calibration's (SC2). The extra two fields live in the Phase 30 module —
  `phase29_prereg` is a closed pre-registration and is NOT edited (pin corrections are dated
  continuations only).
- **D-10:** Seed and step budget are IMPORTED from v4.0 (`mitigation_budget.STEP_BUDGET`; the
  v4.0 sweep seed, `phase25_points.SWEEP_SEED` = `phase25_prereg.REPRODUCTION_PROVENANCE["seed"]`)
  so v5.0 differs from v4.0 only in replay and the control source.
- **D-11:** The calibration record's first-add commit must precede every scored point and every
  Phase 31 probe record — an ancestry test, not prose.

### Own-control plumbing (ACTRL-01, WR-05)
- **D-12 (defect located):** `phase25_points.control_key_for(arm)` (`:160`) returns the
  `dp_n{n}` σ=0 control for EVERY arm, adversarial included; it feeds `point_plan` (`:262`) and the
  control load (`:315`). This is the WR-05 root.
- **D-13:** A NEW v5.0 driver module IMPORTS `phase25_points` and overrides only what differs:
  control resolution, prefix/paths (v5.0 `results/phase32_point_<key>.json`), and the arm set
  (`advr_*`, keys from `phase29_prereg.POINT_KEYS()`). `phase25_points.py` stays byte-untouched.
- **D-14:** The single source of "this point's control" is `phase29_prereg.control_key(leg)`.
  Floors, `control_gap` and relearning Z all read through it. An AST guard reddens if any v5.0
  module calls `control_key_for` or constructs a `dp_*` control key.
- **D-15:** The WR-05 refusal checks KEY + RECORD PROVENANCE: the control key must equal
  `phase29_prereg.control_key(leg)`, AND the control record must sit at the v5.0 `advr` path with
  `arm == advr_<leg>` and the same recipe identity (D-09). A test feeds a DP-sourced reading —
  including a `dp_*` record with its fields relabelled — and asserts refusal.
- **D-16:** "Identical budget and seed" is CHECKED AT READ TIME, per point: when floors /
  `control_gap` are produced for a point, the driver compares the control record's recipe identity
  to the point's and refuses any divergence. Not "by construction".

### Schedule order (ACTRL-02)
- **D-17:** Execution order: `advr_n8` control → `advr_n64` control → the 10 remaining points. Both
  D-12 (Phase 29) branches — leg refused vs. measured — are known before any non-control point
  trains, and an unlearnable n64 control is not hidden behind five n8 points.
- **D-18:** A new `SWEEP_SCHEDULE()` in the v5.0 driver, DERIVED programmatically from
  `phase29_prereg.POINT_KEYS()` and `control_key()` — never hand-typed keys. A test proves it is an
  exact permutation of the 12 keys and reddens if any non-control point precedes either control.
  `POINT_KEYS()` remains the CANONICAL key order; `SWEEP_SCHEDULE()` is the EXECUTION order. The
  two roles stay separate, never merged because an ordering would make them coincide.
- **D-19:** Runtime guard: the driver refuses to train a non-control point whose leg's control
  record does not exist. If the control record is REFUSED (outside (0,1]), the Phase 29 D-12
  short-circuit writes the leg's write-once REFUSED records instead of training. This is where a
  manual out-of-order run (resume, single key) is stopped.

### Claude's Discretion
- v5.0 driver module name (e.g. `scripts/phase30_points.py`), the Phase 30 recipe/calibration
  module layout, test file names, and exact AST-guard mechanics — follow the phase25/29 register.
- How the calibration script re-uses the Phase 24 derivation code (import vs. thin re-run),
  provided every constant is imported and every input is re-measured live.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap / requirements
- `.planning/ROADMAP.md` §"Phase 30: Replay-Bearing Adversarial Recipe and Its Own Control" — goal and 4 SC; §v5.0 ordering constraint
- `.planning/REQUIREMENTS.md` — ARECIPE-01, ARECIPE-02, ACTRL-01, ACTRL-02; WR-05 history
- `.planning/phases/29-v5-0-pre-registration-and-carried-debt/29-CONTEXT.md` — D-01..D-15 (keys, replay recipe, admission, own-control refusal, short-circuit, GATE-08 ruling)
- `.planning/phases/29-v5-0-pre-registration-and-carried-debt/29-VERIFICATION.md` — what Phase 29 actually shipped

### Code the phase touches or imports
- `scripts/phase29_prereg.py` — `POINT_KEYS`, `control_key`, `leg_keys`, `replay_windows`, `_RECIPE_FIELDS`, `V5_RESULT_PATHS` (incl. `results/phase30_calibration.json`), REFUSED record, admission contract. CLOSED pre-registration — import, never edit.
- `scripts/teach_persona.py` — `arm_spec` (:1240), `train_arm` `is_dp` gate (:1752) and the D-08 kwargs dicts (:1924-1973), `replay_window_budget` (:182), `_prove_floor_and_band` (:701), `REPLAY_WINDOWS_PER_FACT` (:179)
- `src/personacore/training/loop.py` — replay seam `replay_fn` (~:690), `on_draw` hook, replay kwargs validation (~:500)
- `scripts/phase24_adversarial.py` — `MIN_REFUSAL_SCORED_TOKENS` + D-05 derivation comment (:79-113), `MASK_FRACTION_MARGIN`
- `scripts/phase25_points.py` — `control_key_for` (:160, the WR-05 defect), `point_plan`, `SWEEP_SEED` (:69), v4.0 `SWEEP_SCHEDULE`
- `scripts/phase25_record.py` — `point_key`, `parse_point_key`, `DP_ARMS`/`ORDERED_ARMS`

### Tests that must stay green unmodified
- Golden-trajectory tests: `tests/test_phase22_wiring.py`, `tests/test_loop_penalty_fn.py`, `tests/test_phase21_aligned_bins.py`, `tests/test_phase24_bins.py`
- `tests/test_phase24_band.py`, `tests/test_phase24_refusal.py` — floor/band guards
- `tests/test_phase29_prereg.py` — ancestry and AST guards over the pre-registration

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `phase29_prereg.control_key(leg)` / `leg_keys(leg)` / `POINT_KEYS()`: the control and schedule sources already exist; Phase 30 only consumes them.
- `train()` replay seam: accepts `replay_bin`/`replay_mask_bin`/`replay_windows` and adds one replay mean per step; already validated in Phase 21/22. Researcher: confirm it runs on the flat masked path WITHOUT `fact_bin`/`dp_fn`.
- `on_draw` hook in `get_batch_memmap_masked`: the instrument for D-04's measured replay count.
- `phase25_points` driver: import, override control/paths/arms.

### Established Patterns
- Frozen v4.0 modules are imported, never edited; v5.0 wraps.
- Every constant imported, never retyped; AST guards enforce it.
- Write-once records, ancestry-guarded first-add commits, `provenance.refuse_if_dirty` on emitters.
- Lazy imports keep pre-registration modules torch-free.

### Integration Points
- `teach_persona.ARMS` / `arm_spec` / `train_arm` — new `advr_*` arms and `gets_replay` predicate.
- `results/phase30_calibration.json` — consumed by the v5.0 scoring path (recipe-identity refusal) and the ancestry test.
- v5.0 driver — consumed by Phase 31 (probe) and Phase 32 (sweep).

</code_context>

<specifics>
## Specific Ideas

- The calibration record is expected to reproduce 15 and must SAY why (replay outside the bin),
  not just report the number.
- The teaching:replay window asymmetry (8 vs. 32/256 per step) must be visible in the record for
  Phase 34 even though it gates nothing.
- `POINT_KEYS()`'s docstring cites ACTRL-02 for its arm-major order; that text is in a closed
  pre-registration and is not edited — `SWEEP_SCHEDULE()` is the ACTRL-02 artifact.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 30-replay-bearing-adversarial-recipe-and-its-own-control*
*Context gathered: 2026-09-25*
