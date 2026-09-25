# Phase 30: Replay-Bearing Adversarial Recipe and Its Own Control - Research

**Researched:** 2026-09-25 (HEAD 6e97013, `.venv` Python 3.11.15)
**Domain:** In-repo wiring: the `teach_persona.train_arm` replay seam, the D-05 mask-fraction calibration, the v5.0 own-control driver, and the schedule
**Confidence:** HIGH. Every premise below was measured at HEAD by reading the code or running it. No external library is involved.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Seam split & arm identity (ARECIPE-01)
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

#### ARECIPE-02 calibration meaning
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

#### Own-control plumbing (ACTRL-01, WR-05)
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

#### Schedule order (ACTRL-02)
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

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ARECIPE-01 | The adversarial arm receives replay through the train seam (the `is_dp` gate split); DP arms and the golden trajectory stay byte-unchanged | Findings F1–F4, F9, F10. `train()` accepts replay on the flat masked path with no `loop.py` change (measured). The split must keep ONE `dp_kwargs` dict and ONE splat, or two tests of the frozen `phase23_matched_prereg` census go red (F2). `on_draw` separates replay from teaching draws by `bin_path` (measured: 32 per step). |
| ARECIPE-02 | The `MIN_REFUSAL_SCORED_TOKENS` mask-fraction calibration is re-derived at the replay-bearing recipe and committed before any scored point | F5 and F6. All four D-05 inputs re-derive live from `build_bins` in 0.14 s on CPU: 176 / 7,581 / 2,719 / 336 episodes / 26,054 tokens, giving L = 15. The `advr_n8` bin is byte-identical to the `adv_n8` bin, which is the structural reason to record. |
| ACTRL-01 | The arm's own ratio-0 replay-bearing control is the sole source of recall floors, `control_gap` and relearning Z (WR-05) | F7 and F8. `control_key_for` is only one of five WR-05 carriers in `phase25_points` / `phase25_promotion`. A relabelled `dp_*` record is still distinguishable by `axis`, `q` and `clip_norm` (measured on the real v4.0 records). |
| ACTRL-02 | The control runs first in the schedule at both capacities | F7. `SWEEP_SCHEDULE()` is derived from `POINT_KEYS()` (12 keys, 6 per leg) plus `control_key(leg)`. The D-19 guard reads TRACKED records only, the v4.0 `control_reading` precedent. |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Python 3.11 venv at `.venv` only; never validate against the system 3.14. All commands below use `.venv/bin/python`.
- CPU-only tests, GPU/MPS-free; `pytest` must not need a GPU. Tests must not need gitignored `data/` or `checkpoints/`, or they skip on ubuntu CI (see Pitfall 8).
- PyTorch only; no HF/PEFT model code; no new dependencies (this phase needs none).
- Offline: no network, no wandb.
- GSD workflow: work goes through `/gsd-execute-phase`. Do not use `gsd-sdk` mutation handlers on STATE/ROADMAP/REQUIREMENTS; edit by hand with snapshot and diff (user memory).
- Stage explicit paths only; run `git status` before each commit (concurrent-agent memory).
- `make lint` = `ruff check . && ruff format --check .`.

## Summary

The replay seam already works for a flat, non-DP arm. `train()`'s replay validation (`loop.py:493-516`) is an all-or-none check over the three `replay_*` kwargs. It is independent of the `fact_bin`/`n_facts` group (`:520`) and of `dp_fn`. `replay_fn` (`:690-714`) runs after the mask-branch accumulation whatever branch `batch_fn` took. I ran `train_arm("adv_n8", ...)` through the `_e2e_env` fixture with `replay_*` injected, `fact_bin`/`n_facts`/`dp_fn=None`, and an `on_draw` counter. It completed in 1.9 s and counted exactly `MAX_STEPS × 32` replay windows and `MAX_STEPS × BATCH_SIZE` teaching windows. **So `loop.py` needs no change, and the golden trajectory is untouched by construction.**

The hard constraint is not in `loop.py`. It is in a frozen v4.0 pre-registration. `scripts/phase23_matched_prereg.py` (EDIT-ONCE) reads `train_arm` by AST and requires three things: a single `dp_kwargs = dict(...)` whose keyword set is exactly `{dp_fn, fact_bin, n_facts, replay_bin, replay_mask_bin, replay_windows}`, exactly one splat in the production `train(...)` call, and a 21-name keyword union. `tests/test_phase23_matched_prereg.py::test_the_dp_wiring_keys_match_the_live_caller` and `::test_the_train_call_keys_match_the_live_caller` enforce this against the live file. The natural reading of D-02 is "two dicts, two splats", and that shape reddens both. The shape that honours D-02's two predicates and passes both censuses is below. It was verified against the live census functions: keys unchanged, union 21, `grad_accum_steps` textual count still 14. It keeps ONE dict, gated on `gets_replay`, with the fact/DP entries individually gated on `is_dp`.

D-13's "import `phase25_points` and override only what differs" holds only in a narrow form. `point_plan`, `prefix_for`, `exact_axis_value` and `n_facts_for` all route through `phase25_record.parse_point_key` / `ORDERED_ARMS`, and these refuse every `advr_*` key by design (Phase 29). `record_kwargs` → `control_reading` → `control_key_for` is a second, indirect WR-05 path. So the v5.0 driver must own `point_plan`, `prefix`, control resolution and the control reading. It can reuse `train_stage`, `measure_stage` (with `is_control=True` on the ratio-0 key), `taught_mapping`, `seed_spread`, `attack_corpus` and `scoring_values` unchanged. The AST guard must forbid the transitive carriers, not only the `control_key_for` name.

**Primary recommendation:** Wave 0 captures the pre-split `train()` kwargs fixture. Wave 1 does the single-dict `gets_replay` split plus the `advr_*` arms and CLI refusal. Wave 2 adds the calibration emitter (live `build_bins`, imported constants, refuse-if-≠-15, write-once, `refuse_if_dirty`) and a stop before the operator commits. Wave 3 adds `scripts/phase30_points.py`: `SWEEP_SCHEDULE`, v5.0 `point_plan`, the own-control reader with key, path, provenance and recipe checks, the D-19 guard, and the AST guard over `scripts/phase3[0-4]_*.py`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Replay reaches `advr_*` training | `scripts/teach_persona.py::train_arm` (production caller) | `src/personacore/training/loop.py::train` (unchanged) | The seam exists in `train()`. Only the caller's gate decides who gets it. |
| Arm identity (`advr_n8`/`advr_n64`) | `teach_persona.ARMS` / `REPLAY_ARMS` / `arm_spec` | `phase29_prereg.ADVR_ARMS` (source of truth for names) | `arm_outputs` scopes paths by arm name. The prereg owns the key names. |
| Mask-fraction calibration | new `scripts/phase30_calibration.py` (emitter, lazy torch) | `teach_persona.build_bins`, `phase24_adversarial` constants | Bin-level derivation; replay never enters the bin. |
| Recipe identity + recipe-match refusal | new v5.0 driver module (torch-free) | `phase29_prereg._RECIPE_FIELDS`, `replay_windows` | D-09: the extra fields live in Phase 30 because the prereg is closed. |
| Own-control resolution / reading (WR-05) | new v5.0 driver module | `phase29_prereg.control_key`, `point_record_path`, `control_is_unlearnable`, `refused_record` | D-14 single source. |
| Execution order | new v5.0 driver `SWEEP_SCHEDULE()` | `phase29_prereg.POINT_KEYS()` | D-18: canonical vs. execution order kept separate. |
| Persistence | `results/phase30_calibration.json` (write-once, operator commit) | `phase25_run.atomic_write_json` | `os.replace` census (Pitfall 6). |

## Measured Premises (the "VERIFY at HEAD" list)

### F1. The `is_dp` gate: location and everything it controls [VERIFIED: read teach_persona.py at HEAD]
`is_dp = arm in DP_ARMS` is at **`teach_persona.py:1752`**, as CONTEXT says. It controls seven things, not four:

| Line | What `is_dp` gates | After split |
|------|--------------------|-------------|
| 1753 | refusal if `dp_sigma`/`dp_clip_norm` is None | `is_dp` |
| 1801 | `_refuse_cross_device_resume` | `is_dp` |
| **1815** | **refusal if `DIALOG_TRAIN_BIN`/`DIALOG_TRAIN_MASK` is missing (replay source)** | **must move to `gets_replay`.** CONTEXT does not list this one. Otherwise an `advr_*` run with no replay data writes bins first and dies inside `replay_fn`, which is the exact failure this guard's comment describes. |
| 1914-1926 | `dp_fn = DPSGD(...) if is_dp else None` | `is_dp` |
| 1949 | `dp_accum = dict(grad_accum_steps=stats["n_facts"]) if is_dp else {}` | `is_dp` (the census needs `dp_accum` keys == `{grad_accum_steps}`) |
| 1950-1974 | `dp_kwargs = dict(fact_bin, n_facts, replay_bin, replay_mask_bin, replay_windows, dp_fn) if is_dp else {}` | see F2 |
| 2025 | DP provenance print (reads `dp_kwargs['replay_windows']`) | `is_dp` |

Also `build_arm_bins`: `aligned = arm in DP_ARMS` (`:1349`) and `arm_bin_targets` (`:405`). Both are keyed on `DP_ARMS` by name, so `advr_*` packs FLAT with 2 bin targets automatically. Correct, and nothing to change.

**`stats["n_facts"]` does NOT exist on a flat build** (measured: the flat `build_bins` stats have no `n_facts` key). The `advr_*` replay expression must use the fact count another way: `len(facts)` (8 / 64 from `arm_spec`). The DP arms must keep `stats["n_facts"]`.

### F2. The frozen census that constrains the split's SHAPE [VERIFIED: read scripts/phase23_matched_prereg.py:343-533; ran prove_dp_wiring_keys / prove_train_call_keys on a patched copy]
- `dp_wiring_key_census` walks every `Assign` to a Name `dp_kwargs` / `dp_accum` and reads the keywords of the `dict(...)` Call (or of `IfExp.body`). It requires `dp_kwargs` keys == `DP_KWARGS_KEYS` (6 names incl. the 3 replay ones).
- `prove_train_call_keys` requires **exactly one splat** in the `train(...)` call inside `FunctionDef train_arm`. The splat must be `dp_kwargs` or `dp_accum`, and the union must be the 21 `TRAIN_CALL_KEYS`.
- The module is EDIT-ONCE and ancestry-guarded, so the census cannot be edited. A separate `replay_kwargs` dict plus a second `**replay_kwargs` splat fails `len(splats) == 1`. Moving replay out of `dp_kwargs` fails the key-set equality.

**Shape that passes (verified: census returns the same 6 keys, union 21, `grad_accum_steps` count 14):**
```python
is_dp = arm in DP_ARMS
gets_replay = arm in DP_ARMS + REPLAY_ARMS
...
dp_kwargs = (
    dict(
        fact_bin=fact_bin_path(paths["bin"]) if is_dp else None,
        n_facts=stats["n_facts"] if is_dp else None,
        replay_bin=DIALOG_TRAIN_BIN,
        replay_mask_bin=DIALOG_TRAIN_MASK,
        replay_windows=replay_window_budget(stats["n_facts"] if is_dp else len(facts)) // BLOCK_SIZE,
        dp_fn=dp_fn,  # None unless is_dp
    )
    if gets_replay
    else {}
)
```
DP arms: every value is identical, so `train()` receives equal kwargs. `adv_*`/cal/real: `{}` as before. `advr_*`: `fact_bin=None, n_facts=None, dp_fn=None`, which are `train()`'s own defaults, plus the three replay kwargs. The alternative of keeping the DP `dict(...)` verbatim with a nested `IfExp` orelse for advr also passes the census, but it duplicates the replay expression. The shape above is recommended because D-02 asks for one expression.

### F3. `train()` accepts replay on the flat masked path without `fact_bin`/`dp_fn` [VERIFIED: read loop.py:465-714; ran a prototype]
- The replay validation (`:493-516`) checks only all-or-none over the three `replay_*` kwargs and a positive non-bool int `replay_windows`. The fact group (`:520`) triggers only if `fact_bin` or `n_facts` is not None. There is no coupling to `dp_fn`.
- With `fact_bin=None` and `train_mask_bin` set, `batch_fn` is the Phase-12 mask branch (`:651-661`). `replay_fn` is built from `replay_windows` alone (`:692`) and runs once per optimizer step inside `_optimizer_step` (`:217`).
- **Minimal `loop.py` change: none.** The golden trajectory (`tests/fixtures/golden_trajectory_v1.json`, a `BigramLanguageModel` recipe replayed through `train()`) cannot move, because no line of `loop.py` changes.
- Prototype (scratchpad, not committed): `_e2e_env` + `train_arm("adv_n8", adversarial_ratio=0.0)` with the replay kwargs and `on_draw` injected through a `tp.train` spy. Result: `{'replay': 64, 'teach': 2}` at `MAX_STEPS=2`, `BATCH_SIZE=1`, so 32 replay windows per step = `phase29_prereg.replay_windows(8)`. 1 passed in 1.90 s.

### F4. `on_draw` as the D-04 instrument [VERIFIED: data.py:93-123, loop.py:469-476, 661, 706]
- Signature: `on_draw(bin_path, ix)`, called after the offsets are drawn. `ix` is an array of window start offsets, so count `len(ix)`, not calls: `replay_fn` draws in micro-batches of `min(batch_size, remaining)`.
- It is threaded to BOTH training draws: the mask-branch `batch_fn` (`:661`) and every `replay_fn` micro-batch (`:706`). It is NOT threaded to the fact-aligned loader or to `estimate_loss`.
- **Replay vs teaching is distinguished by `bin_path`**: replay draws pass `replay_bin` (= `tp.DIALOG_TRAIN_BIN`); teaching draws pass `paths["bin"]`. Compare with `pathlib.Path(bin_path) == pathlib.Path(tp.DIALOG_TRAIN_BIN)`. `_e2e_env` monkeypatches `tp.DIALOG_TRAIN_BIN`, so read it AFTER the env is set up.
- `train_arm` does NOT pass `on_draw`, so the test injects it through a spy on `tp.train` (`monkeypatch.setattr(tp, "train", spy)`), the `test_phase22_wiring` pattern. No production change is needed for D-04.

### F5. The D-05 derivation: exact inputs, live re-derivation, cost [VERIFIED: phase24_adversarial.py:83-113; ran build_bins at both n=8 corners]
- The rule is `frac(L) = (S + P·L) / (T + P·L)`. S = clean scored tokens, P = attack-pool episodes, T = clean tokens + pool prompt tokens. The target is `lo + MASK_FRACTION_MARGIN`, where `lo = tp.MASK_FRACTION_BAND[0] = 0.15` and `MASK_FRACTION_MARGIN = 0.05` (`0.15 + 0.05 == 0.2` exactly in float, measured).
- Measured live at HEAD, `adv_n8` facts (identical to `advr_n8` by D-01), `align_facts=None`, `seed=tp.SEED`:
  - ratio `grid[0]` = 0.0: `episodes 176`, `tokens 7581`, `mask_fraction 0.35865980741327`, so clean scored = mask sum = **2,719**
  - ratio `grid[-1]` = 1.9090909090909092: `clean_episodes 176`, `adversarial_episodes 336`, `adversarial_tokens 33152`, `adversarial_scored_tokens 7098`, so prompt tokens = 33152 − 7098 = **26,054**; T = 7,581 + 26,054 = 33,635
  - First L with frac ≥ 0.20: 268.8·L ≥ 4008 gives **L = 15** (frac(15) = 0.2006, frac(14) = 0.1936, not borderline). First L ≥ 0.15 is 9. Both reproduce the committed comment.
- Cost: both builds together took **0.14 s** on CPU. The calibration is cheap enough to re-run inside a test.
- Read the clean scored count as `int(np.fromfile(mask_path, np.uint8).sum())`, not `round(mask_fraction*tokens)`.
- NOTE: the committed D-05 comment says the clean inputs came off `dp_n8`. The FLAT build of the same 8 facts gives the same 176/7,581/2,719, so that is still true. Use the flat `advr_n8` build as D-06 says.
- **Honest structural evidence to record:** at the same ratio and seed, the `advr_n8` teaching bin should be byte-identical to the `adv_n8` one, because `arm_spec` returns the same facts and `replay_ratio=0.0` and the packer never sees replay. Recording both sha256 values and their equality measures "replay is outside the bin" instead of asserting it. [ASSUMED until the planner's task runs it. It follows from `build_bins` taking no arm argument: verified that `tp.build_bins(tok, episodes, bin, mask, ...)` has no arm parameter.]

### F6. Constants for D-10 [VERIFIED: ran imports]
- `mitigation_budget.STEP_BUDGET = 200` (`mitigation_budget.py:508`). `teach_persona.MAX_STEPS = 200`. `train_arm` trains `tp.MAX_STEPS`, not `STEP_BUDGET`, so the calibration should PROVE `tp.MAX_STEPS == STEP_BUDGET` and record `max_steps` from `STEP_BUDGET`.
- `phase25_points.SWEEP_SEED = phase25_prereg.REPRODUCTION_PROVENANCE["seed"] = 1337` (`phase25_points.py:69`). `tp.SEED = 1337`. Prove they are equal.
- Importing `phase25_points` is torch-free (measured: `'torch' in sys.modules` is False after import, 0.28 s). It transitively loads `phase25_epsilon`; the DEBT-04 census tolerates that (F11).

### F7. `phase29_prereg` public API as it actually exists [VERIFIED: read scripts/phase29_prereg.py; ran POINT_KEYS]
| Name | Kind | Notes |
|------|------|-------|
| `ADVR_ARMS = ("advr_n8", "advr_n64")` | tuple | Docstring: "Phase 30 imports it from here. It must NEVER be appended to `teach_persona.ADV_ARMS`." |
| `LEGS = ("n8", "n64")` | tuple | |
| `RATIO_GRID` | `mitigation_budget.ADVERSARIAL_RATIO_GRID` (6 values) | |
| `point_key(arm, ratio)` | fn | wraps `phase25_record.point_key` via the v4.0 twin |
| `POINT_KEYS()` | fn → 12-tuple | arm-major, control first per leg: `advr_n8_ratio0p000000 … advr_n8_ratio1p909091, advr_n64_ratio0p000000 …` |
| `control_key(leg)` | fn | `advr_n8_ratio0p000000` / `advr_n64_ratio0p000000` |
| `leg_keys(leg)` | fn → 6-tuple | D-12 short-circuit set |
| `POINT_RECORD_PREFIX = "results/phase32_point_"`, `point_record_path(key)` | str / fn | refuses non-keys |
| `V5_RESULT_PATHS` | tuple | `[0] == "results/phase30_calibration.json"` (resolve by membership, never retype) |
| `ARTIFACT_PATHSPECS` | derived | `results/phase30_*` … `results/phase34_*` |
| `REPLAY_SOURCE` | `("teach_persona.DIALOG_TRAIN_BIN", "teach_persona.DIALOG_TRAIN_MASK")` | NAMES, not paths |
| `replay_windows(n_facts)` | fn, lazy `teach_persona` import | 32 / 256 |
| `control_is_unlearnable(tk, tn, hk, hn)` | fn | the route's (0,1] inequality on counts |
| `REFUSED_RECORD_FIELDS`, `_RECIPE_FIELDS = frozenset({"replay_windows","n_facts","seed","max_steps"})` | | |
| `refused_record(key, *, taught, heldout, recipe)` | fn | builds only; refuses a learnable reading; checks `n_facts == leg n`, `replay_windows == replay_windows(n)`, `seed >= 0`, `max_steps > 0` |
| `CONTROL_BASELINE_SOURCE`, `control_baseline_source(leg)` | | relearning Z's control = `results/phase32_point_<control_key>.json::adapter_sha256` |
| `recall_threshold(frontier, leg, arm)` | fn | refuses `arm != "advr"` |
| `_prove(cond, msg)` | private | the SystemExit register |

The REFUSED-record helper writes nothing. Phase 32 writes it, write-once.

### F8. `phase25_points.control_key_for` and every WR-05 carrier [VERIFIED: read phase25_points.py, phase25_promotion.py, phase25_verdict.py]
- `control_key_for(arm)` (`:160`) returns `phase25_record.point_key(f"dp_n{n_facts_for(arm)}", 0.0)`. Call sites are `point_plan` (`:262`) and `control_reading` (`:315`). `record_kwargs` (`:731`) calls `control_reading(arm, tracked)` for every non-control point, so **`record_kwargs` is an indirect WR-05 carrier.**
- Lookup is by module global at call time, so monkeypatching `phase25_points.control_key_for` would "work". That mutates a frozen module process-wide and would silently re-route any v4.0 code in the same process. **Do not override by assignment; re-implement in the v5.0 module.**
- **The keys block reuse more than CONTEXT assumes:** `n_facts_for` requires `arm in phase25_record.ORDERED_ARMS`, and `prefix_for`, `point_plan` and `exact_axis_value` call `phase25_record.parse_point_key`/`point_key` with the arm. All of these refuse `advr_*` (Phase 29 `test_keys_are_refused_by_every_v4_parser`). `build_point_record` (`phase25_record.py:826`) also calls `parse_point_key`, which matters in Phase 32.
- Safely reusable unchanged (they take a `plan` dict and never parse the key): `train_stage(plan)` (uses `tp.arm_spec`, `tp.arm_outputs`, `tp.train_arm`; `prove_mechanism_matches_pin` uses the key only in messages), `measure_stage(plan, training)` (scores recall iff `plan["is_control"]`; the `arm == "dp_n8"` reproduction gate is inert for `advr`), `taught_mapping`, `seed_spread`, `attack_corpus`, `scoring_values`, `_family_counts`, `_refusal`.
- NOT reusable for `advr`: `_adversarial_extras` filters `results/phase24_token_budget.json` rows by `row["arm"] == plan["arm"]`, which gives 0 rows for `advr_*` and refuses. `record_kwargs` has the WR-05 path.
- Other WR-05 carriers a v5.0 module must not call: `phase25_promotion.control_readings` (dialogue pair from the DP σ=0 control, `:160-166`). Also `phase25_verdict.curve_verdicts`: its leg lookup goes through `ARM_LEGS["adversarial"] = ADV_ARMS` (committed literal `("adv_n8","adv_n64")`), so an advr leg would have to be keyed `adv_n{cap}`. Phase 32 should call `phase29_prereg.GATE_ROUTE` directly. That is a Phase 32 decision, flagged here.
- Relabelled-DP detection, measured on the real records: `results/phase25_point_dp_n8_sigma0p000000.json` has `axis "sigma"`, `q 1.0`, `clip_norm 1000000.0`, `sigma 0.0`, `train_config.grad_accum_steps 8`. `results/phase25_point_adv_n8_ratio0p000000.json` has `axis "ratio"`, `q None`, `clip_norm None`, `grad_accum_steps 1`. The DP n8 recipe has the SAME `_RECIPE_FIELDS` values as advr n8 (8 / 32 / 1337 / 200). So a recipe check alone cannot refuse a relabelled DP record. **The provenance check must include `axis == "ratio"`, `q is None` and `clip_norm is None`** (plus key, path, arm, and the D-09 `min_refusal_scored_tokens` / `replay_source`, which DP records do not carry).

### F9. The golden-trajectory tests [VERIFIED: grep + ran them]
- `tests/test_loop_penalty_fn.py::test_golden_trajectory_bit_identity` and `tests/test_phase22_dpsgd.py`'s golden half: `train()`-level, platform-gated replay of `golden_trajectory_v1.json`. Untouched, because `loop.py` does not change.
- `tests/test_masked_train_seam.py`: the masked seam's golden recipe, `train()`-level.
- `tests/test_phase21_aligned_bins.py::test_build_bins_byte_identity_default_matches_the_v2_golden` (`golden_build_bins_v2.json`) and `tests/test_phase24_bins.py`: bin-level. `build_bins` does not change.
- `tests/test_phase22_wiring.py`: the end-to-end `train_arm` DP run (asserts `replay_windows == replay_window_budget(n)//BLOCK_SIZE`) and the non-DP control asserting NONE of the 5 wiring keys reach `train()` for `cal_first_person`. The `if gets_replay` gate keeps that true.
- Targeted guard run at HEAD: **225 passed in 35.6 s** (`test_phase22_wiring`, `test_loop_penalty_fn`, `test_phase21_aligned_bins`, `test_phase24_bins`, `test_phase24_band`, `test_phase24_refusal`, `test_phase23_matched_prereg`, `test_phase29_prereg`, `test_phase14_teaching`, `test_phase23_resume::test_resume_from_none_is_inert`, `test_phase25_points`).

### F10. Tests that WILL change or need registering (not golden) [VERIFIED: read each]
1. **`tests/test_phase22_wiring.py::test_non_dp_arm_cli_is_unchanged`**: `non_dp = [arm for arm in tp.ARMS if arm not in DP_ARMS and arm not in ADV_ARMS]` then `tp.main([arm])` must NOT raise. Adding `advr_*` to `ARMS` (D-01) while refusing them on the CLI (required: same CR-01 class as `adv_*`) reddens it. The fix follows the 24-REVIEW precedent in that same docstring: narrow the population to also exclude `REPLAY_ARMS`, with a dated note. The file is not on CONTEXT's "unmodified" list; only its golden/e2e tests are.
2. **`tests/test_phase23_resume.py::test_resume_from_none_is_inert`**: every raw `grep -rn "train_arm("` hit in `scripts/` and `tests/`, **prose and docstrings included**, must be in `_TRAIN_ARM_CALL_SITES`. The count of non-this-file calls is pinned as the literal `8 + 1 + 1 + 1 + 1 + 2 + 1 + 1`, and the per-file AST call count must match. D-04's test calls `tp.train_arm(...)`, so it adds one `call` entry and needs the literal bumped `+ 1` with its reason. Any new prose containing `train_arm(` (in `teach_persona.py`, the driver, or test docstrings) is also a hit. `_RESUME_PASSERS`: the new test must not pass `resume_from`.
3. `tests/test_phase24_bins.py::test_the_cli_refuses_the_adversarial_arms`: selects `arm.startswith("adv_")`, and `"advr_n8".startswith("adv_")` is False. **Stays green** as long as `ADV_ARMS` is not touched. Phase 29's docstring forbids appending to `ADV_ARMS`, because `phase25_verdict.ADV_ARMS` reads that committed literal.
4. `tests/test_phase14_teaching.py::test_arm_outputs_scoped` / `test_arm_outputs_prefix_is_additive` / `test_real_arm_adapter_is_the_shippable_path` iterate `tp.ARMS`. `advr_*` gets disjoint paths by name, so they stay green and extend coverage.
5. `tests/test_phase22_wiring.py::test_the_prose_vs_code_measurement_is_still_true` pins `source.count("grad_accum_steps") == 14` in `teach_persona.py`. **Do not write that word in any new comment.**

### F11. Existing guard patterns to reuse [VERIFIED]
- Ancestry: `tests/test_phase29_prereg.py::_assert_frozen_before(prereg_artifact, tracked)`. Import it; cross-test imports are precedent: `test_phase23_resume` imports `_e2e_env` from `test_phase22_wiring`, and `test_phase23_matched_prereg` imports `_git` / `_ordering_guard`. Honest-green with zero tracked.
- AST helpers in `tests/test_phase29_prereg.py`: `_numeric_constants`, `_replay_literal_failures(source, value)`, `_planted(tmp_path, source, planted, name)` (planted-RED on a tmp copy, asserts the real file unchanged), `_accountant_failures`.
- DEBT-04 census `test_no_v5_module_uses_the_accountant` already globs `scripts/phase29_*.py … phase34_*.py`, so any `scripts/phase30_*.py` is automatically covered. It flags a direct `import phase25_epsilon`/`personacore.privacy*` and the names `epsilon_for`, `sigma_for`, `delta_closed`, `delta_quadrature`. Importing `phase25_points` does not trip it (not an AST hit in the v5.0 file).
- Emitter register: `phase27_relearn.admit` (`:360-410`). Order: overwrite refusal, then `refuse_if_dirty(who=, detail=, pathspec=("scripts","src","results", ":(exclude)<out>"), cwd=_ROOT)`, then build, then provenance (`git_sha`, `head_at_write`, module sha256s), then `phase25_run.atomic_write_json`. The operator commits by hand.
- Write target: resolve from `phase29_prereg.V5_RESULT_PATHS`, never retype `"results/phase30_calibration.json"`.
- `teach_persona.refuse_if_exists` imports torch. The torch-free emitters restate it as `_prove(not out.exists(), ...)` (phase27 precedent).

## Standard Stack

No external packages. Everything is in-repo.

| Component | Where | Use |
|-----------|-------|-----|
| `train()` replay seam | `src/personacore/training/loop.py` | unchanged |
| `on_draw` | `personacore.training.data.get_batch_memmap_masked` | D-04 instrument (test-injected) |
| `build_bins`, `arm_spec`, `render_episodes`, `MASK_FRACTION_BAND`, `SEED`, `MAX_STEPS`, `BATCH_SIZE`, `BLOCK_SIZE`, `DIALOG_TRAIN_BIN` | `scripts/teach_persona.py` (torch at import, so lazy-import from the driver) | calibration + seam |
| `MIN_REFUSAL_SCORED_TOKENS`, `MASK_FRACTION_MARGIN` | `scripts/phase24_adversarial.py` | imported, never retyped |
| `STEP_BUDGET`, `ADVERSARIAL_RATIO_GRID` | `scripts/mitigation_budget.py` | imported |
| `SWEEP_SEED`, `train_stage`, `measure_stage` | `scripts/phase25_points.py` | imported |
| key/path/control/refusal API | `scripts/phase29_prereg.py` | imported (closed) |
| `refuse_if_dirty`, `git_sha` | `personacore.provenance` | emitter |
| `atomic_write_json` | `scripts/phase25_run.py` | the only sanctioned writer |
| pytest 8.x | `.venv` | tests |

## Package Legitimacy Audit

Not applicable. This phase installs no external package. slopcheck was not run because there is nothing to check.

## Architecture Patterns

### System Architecture Diagram

```
                ┌───────────────────────── Phase 30 (no scored point) ─────────────────────────┐
 phase29_prereg ─┬─ POINT_KEYS() ──► SWEEP_SCHEDULE() = [ctrl n8, ctrl n64, 10 others]  (ACTRL-02)
  (closed)       ├─ control_key(leg) ─► own-control reader ──► WR-05 refusal:
                 │                        key == control_key(leg)?  path == point_record_path?
                 │                        arm == advr_<leg>?  axis=="ratio", q/clip_norm None?
                 │                        recipe == point recipe == calibration recipe?  (D-15/16)
                 ├─ replay_windows(n) ─► recipe_identity(leg) = _RECIPE_FIELDS + floor + replay src
                 └─ V5_RESULT_PATHS ─► results/phase30_calibration.json
                                          ▲
 build_bins(advr_n8 facts, ratio=grid[0] and grid[-1]) ─► 4 inputs ─► frac(L) ─► L==15? ─no─► SystemExit (D-08 checkpoint)
                                                                                    │yes
                                            + descriptive teaching:replay mix ──────┘─► write-once, operator commit
 teach_persona.train_arm(advr_*) ─ gets_replay ─► train(replay_bin, replay_mask_bin, replay_windows=4n)
                                   is_dp=False ─► no DPSGD, no fact_bin, accum 1, flat bins
 D-19 guard: key not a control and its leg's control record not TRACKED ─► refuse;
             control REFUSED ─► leg_keys(leg) get refused_record(...) (Phase 32 writes)
```

### Recommended layout
```
scripts/
├── teach_persona.py          # +REPLAY_ARMS, +advr_* in ARMS/arm_spec, gets_replay split, CLI refusal
├── phase30_points.py         # v5.0 driver: recipe_identity, SWEEP_SCHEDULE, point_plan, control reader, D-19 guard (torch-free at import)
└── phase30_calibration.py    # ARECIPE-02 emitter (lazy teach_persona import), writes results/phase30_calibration.json
tests/
├── fixtures/phase30_train_kwargs_presplit.json   # Wave 0 capture, BEFORE the split commit
├── test_phase30_seam.py        # ARECIPE-01
├── test_phase30_calibration.py # ARECIPE-02 (+ D-11 ancestry)
└── test_phase30_points.py      # ACTRL-01/02 (+ AST guard)
```
The names are the planner's to choose (Claude's discretion). Two scripts keep the driver torch-free at import while the emitter needs `build_bins`.

### Pattern 1: `REPLAY_ARMS` as a literal, proven equal to the prereg
`teach_persona` cannot import `phase29_prereg` at module scope: it would pull `mitigation_gate`, `phase20_gate_coverage`, `phase25_promotion` and more into `teach_persona`'s import graph, which `tests/test_phase14_scoring.py`'s clean-room check and many consumers rely on. Define the literal `REPLAY_ARMS = ("advr_n8", "advr_n64")` next to `ADV_ARMS`, add both names to `ARMS`, and have a test assert `tp.REPLAY_ARMS == phase29_prereg.ADVR_ARMS`. `arm_spec`: `if arm in REPLAY_ARMS: return arm_spec({"advr_n8": "adv_n8", "advr_n64": "adv_n64"}[arm])` (or the twin by string). One line of logic, and it inherits the lazy `phase21_filler` import.

### Pattern 2: CLI refusal for `advr_*`
`main()`: `elif arm in ADV_ARMS or arm in REPLAY_ARMS: raise SystemExit(...)`. Reusing the existing message adds no new `train_arm(` text. If the message is specialised, keep the registered `train_arm(` hit count unchanged or register the new one. Update `USAGE`'s programmatic-only line to list `REPLAY_ARMS` too; it is a registered prose hit, so keep exactly one `train_arm(` in it.

### Pattern 3: Own-control reader (single entry point for floors, `control_gap`, relearning Z)
```python
def own_control(key, tracked, *, point_recipe):
    leg = _leg_of(key)                      # via phase29_prereg.leg_keys, never string-slicing a dp name
    ckey = phase29_prereg.control_key(leg)  # D-14: the ONLY control source
    rel = phase29_prereg.point_record_path(ckey)
    _prove(rel in set(tracked), ...)        # D-19 / v4.0 control_reading precedent: TRACKED only
    record = json.loads((_ROOT / rel).read_text())
    _prove(record["point_key"] == ckey and record["arm"] == f"advr_{leg}", ...)
    _prove(record["axis"] == "ratio" and record["q"] is None and record["clip_norm"] is None, ...)  # relabelled dp_*
    _prove(record["recipe"] == point_recipe == recipe_identity(leg), ...)                            # D-16 at read time
    return record   # floors = taught/heldout counts; control_gap = condition_c pair; Z baseline = adapter_sha256
```
The `recipe` field does not exist in v4.0 records. Phase 32's record assembly must put it into `extra` (`build_point_record` merges `extra`), and Phase 30 pins the field name and shape in `recipe_identity`. Floors come from the record's taught/heldout counts and go to `phase29_prereg.control_is_unlearnable` / the REFUSED branch. `control_gap` goes through `phase25_condition_c.control_gap_for_capacity(own_record["condition_c"] pair)`. The relearning-Z control baseline goes through `phase29_prereg.control_baseline_source(leg)` plus the verified `adapter_sha256`.

### Pattern 4: `SWEEP_SCHEDULE()` derived, never typed
```python
def SWEEP_SCHEDULE():
    controls = tuple(phase29_prereg.control_key(leg) for leg in phase29_prereg.LEGS)
    return controls + tuple(k for k in phase29_prereg.POINT_KEYS() if k not in controls)
```

### Pattern 5: v5.0 `point_plan(key)` (re-implemented, feeds the reused `train_stage`/`measure_stage`)
Same dict keys as `phase25_points.point_plan`, with these values: `is_dp=False`, `is_control = key == control_key(leg)` (NOTE: v4.0 set `is_control` only for dp σ=0, so ratio-0 adv points were never recall-scored), `n_facts` from `phase29_prereg` leg, `seed=phase25_points.SWEEP_SEED`, `adversarial_ratio` = the exact grid member (index-match over `RATIO_GRID` via `phase29_prereg.point_key`), `pinned_mechanism = phase25_points.pinned_mechanism("adv_n8", ratio)` (the twin; `is_dp("adv_*")` is False, so no parse), `point_epsilon=None`, `accounting=None`, `control_key=phase29_prereg.control_key(leg)`, `prefix` a v5.0 label (e.g. `"phase32_" + key minus arm`) that does not start with `phase25_points.CALIBRATION_PREFIX_LITERAL`.

### Anti-Patterns to Avoid
- **Two dicts / two splats in `train_arm`.** Breaks the frozen `phase23_matched_prereg` census (F2).
- **Appending `advr_*` to `ADV_ARMS`.** `phase25_verdict.curve_verdicts` would match two legs and refuse (phase29 docstring).
- **Monkeypatching `phase25_points.control_key_for` from the v5.0 module.** Process-wide mutation of a frozen module.
- **Calling `phase25_points.point_plan` / `record_kwargs` / `control_reading` / `_adversarial_extras`, or `phase25_promotion.control_readings`, from v5.0.** These are indirect DP control reads or `parse_point_key` refusals.
- **A grep acceptance criterion for "dp_" / "control_key_for" in a v5.0 file whose docstrings discuss WR-05.** It measures prose (user memory). Use an AST gate that exempts docstrings and matches only whole key-shaped constants (see Pitfall 4).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Replay window count | `4 * n` | `phase29_prereg.replay_windows(n)` / `tp.replay_window_budget(n) // tp.BLOCK_SIZE` | AST guard vs literal `4`; one site computes it |
| Mask-fraction inputs | copying 176/7581/2719/336/26054 | live `tp.build_bins` at `grid[0]` and `grid[-1]` | D-06 "re-measured live" |
| Floor / margin / band | `15`, `0.05`, `0.15` | `pa.MIN_REFUSAL_SCORED_TOKENS`, `pa.MASK_FRACTION_MARGIN`, `tp.MASK_FRACTION_BAND[0]` | never retyped |
| Keys, control key, record path | f-strings | `phase29_prereg.POINT_KEYS/control_key/point_record_path` | D-14 |
| Unlearnable check / REFUSED record | own inequality | `phase29_prereg.control_is_unlearnable` / `refused_record` | route-equivalent, tested |
| Atomic JSON write | `os.replace` | `phase25_run.atomic_write_json` | repo census (Pitfall 6) |
| Dirty-tree refusal | `git status` parsing | `personacore.provenance.refuse_if_dirty` | |
| Ancestry test | new git walker | `test_phase29_prereg._assert_frozen_before` | |
| e2e CPU env | new fixture | `test_phase22_wiring._e2e_env` | registered pattern (`test_phase23_resume`) |

## Runtime State Inventory

Not a rename/migration phase, but new arm names create on-disk state:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None: `git ls-files 'results/phase3*'` = 0, `find results -name 'phase3*'` = 0 (measured) | none |
| Live service config | None | none |
| OS-registered state | None in Phase 30 (launchd plists belong to Phase 31/32 runs) | none |
| Secrets/env vars | None | none |
| Build artifacts | `advr_*` runs will write gitignored `data/persona_advr_*_train*.bin`, `checkpoints/<prefix>_advr_*`, and `data/phase25_<key>_*.json` sidecars if `train_stage` is reused (its sidecar prefix is hard-coded `phase25_`). The D-04 test writes only under `tmp_path` via `_e2e_env`. | Planner: the calibration must build into a tempdir, never through `build_arm_bins` into real `data/` (that would plant `refuse_if_exists` targets for Phase 31). |

## Common Pitfalls

### Pitfall 1: The split reddens the frozen matched-comparator census
**What goes wrong:** `test_the_dp_wiring_keys_match_the_live_caller` / `test_the_train_call_keys_match_the_live_caller` go red, and `phase23_matched_prereg.py` cannot be edited (EDIT-ONCE, ancestry-guarded).
**How to avoid:** the single-dict shape in F2. Run `tests/test_phase23_matched_prereg.py` in the task's verify step.

### Pitfall 2: The replay-source guard stays on `is_dp`
**What goes wrong:** on a machine without `data/dialog_train.bin`, an `advr_*` run writes bins (now recorded evidence), then dies in `replay_fn`.
**How to avoid:** move the `:1815` guard to `gets_replay`. Test: `_e2e_env` then delete the replay pair, and `train_arm("advr_n8")` raises SystemExit before any bin exists.

### Pitfall 3: `stats["n_facts"]` on a flat build
**What goes wrong:** KeyError for `advr_*`, because flat stats carry no `n_facts`.
**How to avoid:** `stats["n_facts"] if is_dp else len(facts)`. Assert `== phase29_prereg.replay_windows(n)` in the test.

### Pitfall 4: The AST guard measures prose, or misses the transitive carriers
**What goes wrong:** WR-05 docstrings mention "dp_*", and a string-constant scan goes false-RED. Meanwhile a call to `phase25_points.record_kwargs` reaches `control_key_for` and goes false-GREEN.
**How to avoid:** skip docstring `Expr` constants. Flag a string constant only if it fully matches `^dp_n\d+(_sigma\d+p\d+)?$`, or an f-string whose literal head is `dp_n`. Flag a Name/Attribute in `{control_key_for, control_reading, record_kwargs, point_plan (as phase25_points attr), control_readings, _adversarial_extras}`. Prove non-vacuity with `_planted` copies (one plant per class), and cover `scripts/phase3[0-4]_*.py` so Phases 31-34 inherit it. Precedent for the approach: the DEBT-04 census glob.

### Pitfall 5: Recipe identity alone does not refuse a relabelled DP record
**What goes wrong:** `dp_n8`'s `(8, 32, 1337, 200)` equals `advr_n8`'s.
**How to avoid:** add the provenance checks from F8 (`axis`, `q`, `clip_norm`, key, arm, path, plus D-09's two extra fields). Build the test's fixture from the REAL `results/phase25_point_dp_n8_sigma0p000000.json` with `point_key`/`arm` relabelled, which is a natural fixture rather than a hand-typed one.

### Pitfall 6: Repo-wide censuses a new file trips (user memory, measured in Phase 27)
- `os.replace` is allowed only in `phase25_run.py`/`phase25_record.py`. Use `atomic_write_json`.
- `== 10` literals under `tests/` are counted by `tests/test_phase21_sc5.py`, comments included.
- `train_arm(` text anywhere in `scripts/`/`tests/` must be registered (F10.2).
- `grad_accum_steps` textual count in `teach_persona.py` is pinned at 14 (F10.5).
- `mitigation_gate.ratchet_k` fixtures use K ∈ {8, 16}.

### Pitfall 7: The calibration record lands before its guards, or the prereg is edited after it
**What goes wrong:** the first `results/phase30_*` commit turns `test_phase29_prereg_is_frozen_before_every_v5_result` non-vacuous. Any later commit touching `scripts/phase29_prereg.py`, `phase25_record.py` or `phase20_gate_coverage.py` then reddens forever (user memory: pin corrections are dated continuations only).
**How to avoid:** land the D-11 ancestry test (honest-green) and all Phase 30 code BEFORE the operator commits the JSON. The emitter's `refuse_if_dirty` enforces a clean tree. The D-11 test must also be non-vacuous in the other direction: once any `results/phase31_*`/`phase32_*` is tracked, the calibration must be tracked.

### Pitfall 8: Host-gated skips drift the ubuntu skip pin
**What goes wrong:** `tests/test_phase25_venue.py` pins CI skip totals. A new test that `skipif`s on `data/`/`checkpoints/` presence changes the ubuntu count.
**How to avoid:** every Phase 30 test uses `_e2e_env`/tmp builds (the tokenizer and fact modules are committed) and never skips. The calibration test builds bins from committed inputs only.

### Pitfall 9: Clean-tree probes during execution
Eleven tests fail while `results/`, `tests/` or `scripts/` hold untracked files (user memory). Run the full suite only on a committed tree, with `nohup` plus a grep waiter (the suite takes ~25 min, and the Bash tool caps at 600 s).

## Code Examples

### D-04 measured replay count (the prototype that passed, cleaned up)
```python
# Source: verified in this session against HEAD (scratchpad prototype, 1 passed in 1.90 s)
from test_phase22_wiring import _e2e_env
def test_advr_n8_draws_the_prereg_replay_count(tmp_path, monkeypatch):
    _e2e_env(tmp_path, monkeypatch)
    drawn = {"replay": 0, "teach": 0}
    real = tp.train
    def spy(**kw):
        def on_draw(bin_path, ix):
            key = "replay" if pathlib.Path(bin_path) == pathlib.Path(tp.DIALOG_TRAIN_BIN) else "teach"
            drawn[key] += len(ix)
        return real(**kw, on_draw=on_draw)
    monkeypatch.setattr(tp, "train", spy)
    facts, sp, rr = tp.arm_spec("advr_n8")
    tp.train_arm("advr_n8", facts=facts, family_ids=fs.TAUGHT_FAMILY_IDS, second_person=sp,
                 replay_ratio=rr, adversarial_ratio=mb.ADVERSARIAL_RATIO_GRID[0], prefix="phase30_probe")
    per_step = drawn["replay"] / tp.MAX_STEPS
    assert per_step == phase29_prereg.replay_windows(len(facts)) > 0
    assert drawn["teach"] == tp.MAX_STEPS * tp.BATCH_SIZE
```
(The `tp.train_arm(` line must be registered in `tests/test_phase23_resume.py`, F10.2.)

### Calibration core (exact, cheap)
```python
# Source: phase24_adversarial.py:83-113 rule; inputs measured live (F5)
lo = tp.MASK_FRACTION_BAND[0]; target = lo + pa.MASK_FRACTION_MARGIN
S, T0 = clean_scored, clean_tokens                    # grid[0] build
P, prompt = s["adversarial_episodes"], s["adversarial_tokens"] - s["adversarial_scored_tokens"]  # grid[-1]
frac = lambda L: (S + P * L) / (T0 + prompt + P * L)
L = next(L for L in itertools.count(1) if frac(L) >= target)
_prove(L == pa.MIN_REFUSAL_SCORED_TOKENS, "... D-08: STOP for the developer's ruling")
```

## State of the Art

| Old Approach (v4.0) | Current Approach (v5.0) | Impact |
|--------------|------------------|--------|
| Adversarial arm trained with NO replay (`adv_*`) | `advr_*` gets train-time replay, `4·n` windows/step | the only recipe difference besides the control |
| `control_key_for` → `dp_n{n}` σ=0 control for adversarial points (WR-05) | `phase29_prereg.control_key(leg)` → `advr_n{n}` ratio-0 | floors, `control_gap`, Z all own-sourced |
| v4.0 schedule, `is_control` only on dp σ=0 | `SWEEP_SCHEDULE()` with both advr controls first; advr ratio-0 recall-scored | D-12 short-circuit decidable before any other point |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `advr_n8` and `adv_n8` teaching bins are byte-identical at equal ratio/seed | F5 | Low: `build_bins` has no arm input (verified). If it differs, the "structural reason" field must say so and the plan should investigate before emitting. |
| A2 | Narrowing `test_non_dp_arm_cli_is_unchanged` with a dated note is acceptable to the developer | F10.1 | Medium: if refused, the alternative is to leave `advr_*` out of `ARMS` (the CLI then rejects them via USAGE), which contradicts D-01's literal "ARMS". This needs a ruling only if the developer objects. |
| A3 | Phase 32 will carry a `recipe` dict in each v5.0 point record's `extra` | Pattern 3 | Medium: Phase 30 defines the reader, so Phase 32 must write what it reads. Pin the field name in the driver and test the round-trip on a forged record. |
| A4 | A v5.0 prefix like `phase32_<ratio>` for `arm_outputs` | Pattern 5 | Low: discretion. It must not start with `phase25_calibration`, and it scopes only gitignored paths. |

## Open Questions

1. **Should the Phase 30 modules themselves be ancestry-frozen before the first `results/phase31_*`/`phase32_*`?** (WR-04 precedent for call-time sources.) Phase 31's probe may legitimately fix the driver. Recommendation: freeze `scripts/phase30_calibration.py` before the calibration JSON (the emitter precedent) and leave the driver unfrozen, with the decision recorded.
2. **`curve_verdicts` leg lookup for `advr`** (F8): Phase 32's choice. Phase 30's AST guard should not forbid `GATE_ROUTE`.
3. **D-04 at n=64 too?** D-04 names `advr_n8` only. Parametrizing `advr_n64` costs ~256 tiny forwards per step, a few seconds. Recommendation: include it, since SC1 says "equal to the PREREG-04 recipe" and n=64 is where 256 is claimed.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `.venv` Python | all | ✓ | 3.11.15 | — |
| torch (CPU) | seam tests, calibration | ✓ | venv wheel (2.7.x per CLAUDE.md) | — |
| frozen tokenizer / fact modules | `build_bins` | ✓ committed | — | — |
| `data/dialog_train.bin` / `_mask.bin` | real `advr_*` training only (Phase 31+) | ✓ locally (10.5 MB / 5.3 MB); absent on CI | — | tests use `_e2e_env` fixtures |
| `checkpoints/convbase_best.pt` | real training only | ✓ locally | — | `_e2e_env` tiny GPT |
| git with full history | ancestry tests | ✓ (not shallow) | — | — |

No missing blocking dependency.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x in `.venv` |
| Config file | `pyproject.toml` (existing) |
| Quick run command | `.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_phase30_seam.py tests/test_phase30_calibration.py tests/test_phase30_points.py` (target < 30 s) |
| Guard set (per task commit) | `.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_phase22_wiring.py tests/test_phase23_matched_prereg.py "tests/test_phase23_resume.py::test_resume_from_none_is_inert" tests/test_loop_penalty_fn.py tests/test_phase21_aligned_bins.py tests/test_phase24_bins.py tests/test_phase24_band.py tests/test_phase24_refusal.py tests/test_phase14_teaching.py tests/test_phase29_prereg.py tests/test_phase22_dpsgd.py tests/test_masked_train_seam.py tests/test_phase25_points.py` (~40 s; 225 of these measured at 35.6 s) |
| Full suite command | `nohup sh -c ".venv/bin/pytest -q -p no:cacheprovider > $LOG 2>&1; echo EXIT=\$? >> $LOG" &` plus an `until grep -q '^EXIT=' $LOG` waiter (~25 min; committed tree only) |

### Phase Requirements → Test Map
| Req / SC | Behavior | Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ARECIPE-01 / SC1 | `advr_n8` (and n64) draws exactly `replay_windows(n)` replay windows per step, > 0, measured via `on_draw` | e2e CPU | `pytest tests/test_phase30_seam.py -k draws -x` | ❌ Wave 0 |
| ARECIPE-01 / SC1 (D-03) | `train()` + `TrainConfig` kwargs for `dp_n8`, `dp_n64`, `adv_n8`, `adv_n64` equal the pre-split fixture | e2e CPU (capture-and-stop spy) | `pytest tests/test_phase30_seam.py -k presplit` | ❌ Wave 0 (fixture captured BEFORE the split) |
| ARECIPE-01 / SC1 | golden trajectory + bins unchanged | existing, unmodified | `pytest tests/test_loop_penalty_fn.py tests/test_masked_train_seam.py tests/test_phase22_dpsgd.py tests/test_phase21_aligned_bins.py tests/test_phase24_bins.py` | ✅ |
| ARECIPE-01 | frozen matched census still passes | existing, unmodified | `pytest tests/test_phase23_matched_prereg.py` | ✅ |
| ARECIPE-01 | `REPLAY_ARMS == phase29_prereg.ADVR_ARMS`; `arm_spec(advr_x) == arm_spec(adv_x)`; CLI refuses `advr_*`; replay-source guard fires before bins on `advr_*` | unit | `pytest tests/test_phase30_seam.py -k "arms or cli or replay_source"` | ❌ |
| ARECIPE-02 / SC2 | live re-derivation gives L == imported floor; four inputs re-measured; advr/adv bin sha equality recorded | unit (0.2 s) | `pytest tests/test_phase30_calibration.py -k derivation` | ❌ |
| ARECIPE-02 (D-08) | a perturbed input (monkeypatched margin/band) → SystemExit, nothing written | unit | `pytest tests/test_phase30_calibration.py -k refuses_if_not_15` | ❌ |
| ARECIPE-02 / SC2 | scoring refuses a point whose recipe differs from the calibration's (each of the 6 fields perturbed) | unit | `pytest tests/test_phase30_calibration.py -k recipe_mismatch` | ❌ |
| ARECIPE-02 (D-11) | calibration first-add strictly precedes every tracked `results/phase31_*`/`phase32_*` first-add; honest-green now; red if a later file is tracked while the calibration is not | git ancestry | `pytest tests/test_phase30_calibration.py -k ancestry` | ❌ |
| ARECIPE-02 | write-once + dirty-tree refusal on the emitter | unit | `pytest tests/test_phase30_calibration.py -k "write_once or dirty"` | ❌ |
| ACTRL-01 / SC3 | own-control reader refuses: a `dp_*` key; the real dp_n8 σ=0 record relabelled to `advr_n8`; a record at a non-advr path; a recipe divergence (D-16); an untracked control | unit | `pytest tests/test_phase30_points.py -k wr05` | ❌ |
| ACTRL-01 (D-14) | AST guard over `scripts/phase3[0-4]_*.py`: no `control_key_for`/transitive carriers/dp key constants; planted RED per class; docstrings exempt | AST | `pytest tests/test_phase30_points.py -k ast_guard` | ❌ |
| ACTRL-01 | DEBT-04 accountant census still green with the new modules | existing | `pytest tests/test_phase29_prereg.py -k accountant` | ✅ |
| ACTRL-02 / SC4 | `SWEEP_SCHEDULE()` is a permutation of `POINT_KEYS()`; both controls precede every other key; a planted reorder reddens | unit | `pytest tests/test_phase30_points.py -k schedule` | ❌ |
| ACTRL-02 (D-19) | driver refuses a non-control key whose control record is untracked; an unlearnable control yields `refused_record` for all `leg_keys(leg)` and trains nothing | unit (fake `tracked`, fake train fn) | `pytest tests/test_phase30_points.py -k guard` | ❌ |

### Sampling Rate
- **Per task commit:** the quick run plus the guard set (~1 min).
- **Per wave merge:** the full suite, uncapped, committed tree.
- **Phase gate:** full suite green before `/gsd-verify-work`, and the calibration JSON committed by the operator after all code is committed.

### Wave 0 Gaps
- [ ] `tests/fixtures/phase30_train_kwargs_presplit.json`: captured at pre-split HEAD by the same helper the test uses. Normalise paths relative to `tmp_path`, `dp_fn` to `{sigma, C}`, and `TrainConfig` via `asdict`.
- [ ] `tests/test_phase30_seam.py`, `tests/test_phase30_calibration.py`, `tests/test_phase30_points.py`
- [ ] Register the new `train_arm(` call in `tests/test_phase23_resume.py::_TRAIN_ARM_CALL_SITES` and bump the `8 + 1 + … + 1` literal with its reason.
- [ ] Narrow `tests/test_phase22_wiring.py::test_non_dp_arm_cli_is_unchanged` to exclude `REPLAY_ARMS`, with a dated note (A2).

## Security Domain

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication / V3 Session / V4 Access Control | no | offline CLI/research code |
| V5 Input Validation | yes | `_prove` SystemExit checks on record fields; keys only via `phase29_prereg.point_record_path` (refuses non-keys, so no path traversal) |
| V6 Cryptography | yes (integrity only) | `hashlib.sha256` for bin/adapter/module digests; no secrets |
| Data integrity | yes | write-once + `refuse_if_dirty` + ancestry guards; JSON only (never `torch.load` of foreign files) |

| Threat | STRIDE | Mitigation |
|--------|--------|------------|
| DP reading relabelled as the advr control (WR-05) | Spoofing | key + path + arm + `axis`/`q`/`clip_norm` + recipe checks (F8) |
| Post-hoc re-tune of the floor after seeing data | Tampering | D-08 refusal; D-11 ancestry; constants imported |
| Out-of-order / single-key run skipping the control | Elevation (of an unvalidated point) | D-19 runtime guard on TRACKED control records |
| Record written from a dirty tree | Repudiation | `refuse_if_dirty` before write; `git_sha` in the record |
| Recipe drift between control and point | Tampering | D-16 read-time recipe equality |

## Sources

### Primary (HIGH confidence, read or run at HEAD 6e97013)
- `scripts/teach_persona.py` :170-310, :1195-1290, :1300-1440, :1500-1560, :1655-2080 (gate, arms, `build_arm_bins`, `train_arm`)
- `src/personacore/training/loop.py` :150-235, :465-730; `src/personacore/training/data.py` :93-130
- `scripts/phase23_matched_prereg.py` :343-533; `tests/test_phase23_matched_prereg.py`
- `scripts/phase29_prereg.py` (whole API); `tests/test_phase29_prereg.py` (ancestry, AST helpers, census)
- `scripts/phase25_points.py` (whole); `scripts/phase25_promotion.py` :140-300; `scripts/phase25_verdict.py` :100-200, :440-660
- `scripts/phase24_adversarial.py` :77-113; `tests/test_phase24_band.py`
- `tests/test_phase22_wiring.py` :340-430, :552-600, :690-960; `tests/test_phase23_resume.py` :40-360; `tests/test_phase24_bins.py` :300-355
- `scripts/phase27_relearn.py` :360-410 (emitter register); `src/personacore/provenance.py`
- `results/phase25_point_dp_n8_sigma0p000000.json`, `results/phase25_point_adv_n8_ratio0p000000.json` (field comparison)
- Live runs: build_bins at both n=8 corners (0.14 s); prototype replay-count e2e (1 passed, 1.90 s); census functions over the patched source; targeted guard set (225 passed, 35.6 s)

### Secondary
- User memory notes: execute-phase gates (censuses, suite runtime), plans misname artifacts, grep criteria measure prose, pin corrections are dated continuations.

## Metadata

**Confidence breakdown:**
- Seam split and census constraint: HIGH. Measured against the live census functions and a working prototype.
- Calibration: HIGH. Inputs and L re-derived live.
- Own-control driver design: HIGH on the constraints (key parsers refuse advr, the relabelled-DP distinguishers). MEDIUM on the Phase 32 record field shape (A3).
- Pitfalls: HIGH. Each tied to a named test that was read.

**Research date:** 2026-09-25
**Valid until:** the next commit touching `teach_persona.py`, `loop.py`, `phase25_points.py` or `phase29_prereg.py` (in-repo, so it goes stale on edit, not on time).
