# Phase 37: Clean Reproduction of the Phase 19 Verdict - Research

**Researched:** 2026-10-03
**Domain:** Reproducing a closed pre-registered verdict from committed records (CPU), routing five published pin defects through named functions, and pre-registering then running one MPS replica under the v6.0 slot, ledger and approval machinery
**Confidence:** HIGH. Every number below was measured in this session in the 3.11 venv at `.venv`, with the tree clean before and after (`git status` showed only the pre-existing ` D .claude/scheduled_tasks.lock`).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Ordering and the slot (REPRO-03)
- **D-01:** Phase 37's own ancestry-guarded pre-registration module fills
  `phase35_prereg.fill("r1b_tolerance_and_replicated", ...)`. It is committed before ANY Phase 37
  record, including R1a's. There are two records, R1a's and R1b's, both under
  `results/phase37_*`, which is the path Phase 35 reserved.

#### Tolerance and the definition of "replicated" (REPRO-03)
- **D-02:** The tolerances, one per key of `R1A_ASSERTIONS`:
  - `k`: **0**.
  - `target_correct` (0/27): **0**.
  - `nontargets_beyond_margin` (7/7): **0**.
  - `destroyed_pct`: **derived, not chosen**. It is
    MARGIN_K × the published dialogue noise floor ÷ the pre-erasure on−off gap, × 100, in
    percentage points. The arithmetic, read from committed records and never typed:
    - `MARGIN_K` = 2 (`erasure_gate.py:86`, imported via `phase35_prereg.MARGIN_K`);
    - floor = `results/phase19_noise_floors.json::dialogue_ppl_noise_floor.value` =
      0.005214448168350039 (|ΔPPL|);
    - g0 = `phase19_arm_erased.json::pre_erasure.dialogue_ppl` adapter_on − adapter_off =
      5.815445876712191 − 4.573349214207799 = 1.2420966625043919;
    - tolerance = 2 × 0.005214448168350039 / 1.2420966625043919 × 100 ≈ **0.8396203493271365 pp**.

    The derivation is shown in the module. `kind = derived` for `destroyed_pct`. The three zeros
    are Rafael's ruling and get labelled honestly under PREREG-06 (see Claude's Discretion).
- **D-03:** **"Replicated"** means all four assertions fall within the D-02 tolerances.
  - Bit-identity of the draws against the committed `phase19_arm_erased.json` is reported beside
    the result, as yes or no plus the count of differing draws. It is description, never a
    criterion.
- **D-04:** **If the replica does not replicate:**
  - a write-once `NOT_REPLICATED` record is published beside the v3.0 verdict, and the verdict does
    not change;
  - the record carries the per-fact non-target deltas compared with the 0.14814814814814814 floor
    (`nontarget_noise_floor.value`) as context;
  - there is one attempt only. Any new run needs Rafael's "approved", and a root-cause
    investigation comes first.

#### What R1b runs (REPRO-03)
- **D-05:** R1b re-derives the prefix and then runs the erased arm at K = 48:
  - It redoes the selection sweep (ordering and stopping rule) through the defect-E routing (D-08),
    so that k = 78 is MEASURED, not assumed.
  - It then runs the erased arm at K = 48.
  - The record says, by assertion, what was re-measured and what came from the committed prefix.
- **D-06:** Cost, measured from the records:
  - erased arm 68.584 min (`phase19_arm_erased.json::config.wall_clock_min`) + sweep 6.959 min
    (`phase19_collateral_curve.json::wall_clock_min`) = **1.259 h**;
  - the R1b front is 1.108 h (`phase36_budget.json::front_hours.R1b`), and 1.5× that is 1.662 h;
  - 1.259 h < 1.662 h, so Rafael's conditional approval covers the sweep. If the plan's sum ever
    exceeds 1.662 h, it goes to Rafael BEFORE launch.

  One sweep costs 6.2–7.0 min. The 12.29 min in `phase19_reference_set_resweep.json` was TWO
  sweeps (|R| = 8 and |R| = 6). The retrain arm (46.6 min) and the replicate arm (45.3 min) stay
  out of scope.
- **D-07:** **If the re-measured prefix differs from the committed one:**
  - **k = 78 and the SET of the 78 ablated addresses equals the committed set:** the erased arm
    runs even if the internal order differs. The order difference (how many positions moved) is
    recorded as description.
    - Verified: `ablate_components` (`phase19_erasure.py:275-324`) zeros both factors of each
      address on clones and refuses duplicates.
    - So the same set gives bit-identical weights whatever the order.
  - **k ≠ 78 or the set differs:** the erased arm does NOT run.
    - A `NOT_REPLICATED` record is written with only the k and the set difference.
    - A root-cause investigation comes before anything else.
    - A new run needs only Rafael's "approved".

#### Defect E (REPRO-02, ERASE-08)
- **D-08:** Defect E is routed by ONE named function:
  - It imports the pin without editing it and selects `phase18_extraction.reference_set_for`
    (|R| = 8) instead of the pin's `reference_set_for_calibration` (|R| = 6) inside
    `_selected_components`' path.
  - It is proved on the committed records: the curve (`reference_set_size` 8, k = 78) and the
    published re-sweep (|R| = 8 gives k = 78 with a prefix identical to the committed one; |R| = 6
    gives k = 120).
  - It is the function R1b's re-derivation (D-05) uses.
  - It IS the ERASE-08 wrapper. Phase 41 imports this function and does not write another.
  - A test proves `scripts/phase19_erasure.py` byte-unchanged.
- **D-09:** Every one of A–E has a named routing function, and removing any routing turns a test
  red. The red must be natural, not planted:
  - A: on-disk `zero_results_have_nll` False vs order-normalised True;
  - B: the pin's `_calibration_rate()` gives 0.8846…, which yields the `ceiling` floor 0.2 instead
    of `TARGET_FLOOR`;
  - C: the committed `per_fact` reads 14, not the pooled 27;
  - D: `[ppl, n]` raises a `TypeError` in the gate;
  - E: without the routing, the reference set has 6 members, not 8.

#### R1a's output (REPRO-01)
- **D-10:** One command asserts and exits 0 or with an error. It ALSO writes a write-once record
  `results/phase37_*` holding:
  - the four re-derived numbers;
  - the SHA-256 of every input record;
  - the commit.

  The record is committed only after Rafael's "approved". A divergence in any number means STOP
  and report, never adjust to match.

### Claude's Discretion
- File and record names inside `results/phase37_*`, for example `phase37_r1a.json` and
  `phase37_r1b.json`.
- The module layout: the Phase 37 prereg module, the routing module and the drivers. Reuse
  `phase19_run.report()`'s existing A–D routing (`scripts/phase19_run.py:2771`) rather than
  re-implementing it, and never write a `results/phase19_*` path.
- Which list order the erased arm receives under D-07's set-equal case. The re-measured list is
  preferred, so the arm sits downstream of the measurement, and the weights are identical either
  way.
- The `kind` labels for D-02's three zero tolerances (`preference` per PREREG-06, unless the
  planner writes a derivation for them). They must be labelled honestly and surfaced in the plan.

### Deferred Ideas (OUT OF SCOPE)
- The Phase 19 retrain arm (46.6 min) and replicate arm (45.3 min) as part of the replica: not
  run without a new "approved" from Rafael.

Also out of scope (CONTEXT `<domain>`): any edit to `scripts/phase19_erasure.py` or
`scripts/erasure_gate.py`.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REPRO-01 | One CPU command re-derives the Phase 19 verdict from the committed draws, importing the pin and the gate, and asserts exactly k = 78, target 0/27, 7/7 non-targets beyond 0.2962962962962963, 77.6370113463966% destroyed; any divergence halts | Measured end to end on CPU in 1.3 s (§ "R1a, measured now"); `phase35_prereg.r1a_rederive()` already proves k and destroyed_pct; 0/27 and 7/7 come out of `phase19_run._pooled_rows`; the verdict comes out of `pin.render_verdict` and its three reason strings match the recorded `## Verdict` byte for byte |
| REPRO-02 | Each of A–E routed by a named function; removing any routing turns a test red, naturally | Every unrouted path measured on committed inputs (§ "Defects A–E: routed vs unrouted, measured"); `report()` cannot be called (it rewrites a `results/phase19_*` file), so B and D need thin named functions around its inline lines |
| REPRO-03 | MPS replica of k = 78 under a tolerance and a "replicated" definition pre-registered before it runs, published beside the verdict | The slot rule and its census and ordering tests were read and dry-called in memory (§ "The slot"); the ledger API (§ "Ledger and launch"); the D-08 sweep wrapper (§ "Defect E"); the replica's arm record path (§ "R1b design") |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Python 3.11 venv at `.venv` only. The box's 3.14 is not a target, and CI pins 3.11 (`.github/workflows/ci.yml:33`).
- Tests are CPU-only and GPU-free; `pytest` must run without MPS (`CLAUDE.md` "Run `pytest` here; tests must not require a GPU").
- MPS runs are fp32, with no AMP, no `GradScaler` and no `torch.compile` (primary path).
- Offline: no wandb or network. Records are JSON under `results/`, and logs go to the gitignored `logs/`.
- Reproducibility is seed + git SHA + config in the record. Records carry provenance (git_sha, head_at_write, module_sha256, run UTC).
- Never commit secrets. `checkpoints/`, `data/` and `logs/` are gitignored (`.gitignore`).
- GSD workflow: file changes happen only through `/gsd-execute-phase` plans.
- Rafael's rules (memory): measure every premise before stating it; use natural reds, never planted; prefer AST gates over grep; corrections to a closed pin are dated continuations; zero `gsd-sdk` mutation handlers on planning files.

## Summary

R1a can be built almost entirely from code that already exists, and it already works on CPU. Run read-only now, `phase35_prereg.r1a_rederive()` returned `k = 78`, `destroyed_pct = 77.6370113463966` and `margin = 0.2962962962962963`. `phase19_run._pooled_rows` over the committed draws gives target `0/27`. The seven pooled non-target deltas are all `> 0.2962962962962963` (7/7). `pin.render_verdict` returns `FAILURE` with exactly the three reason strings recorded in `results/phase19_erasure_report.md`. The whole computation takes about 1.3 s on CPU and needs no checkpoint.

**Do not reuse `phase19_run.report()` by calling it.** It unconditionally rewrites `results/phase19_erasure_report.md` (`scripts/phase19_run.py:3007`), with no clobber refusal. Its A–D routing is also inline, not named. Only C (`_pooled_rows`, :620) and A's helper (`_order_normalised`, :1290) are functions. B (reading the correction record and proving it through `lock_erasure_floor`) and D (`retention_ppl[0]`) are inline lines, so Phase 37 must wrap them in named functions that read the same values.

**The slot is thin.** `_rule_r1b_tolerance_and_replicated` takes a plain `tolerance` mapping of finite numbers ≥ 0, with keys drawn from `R1A_ASSERTIONS` and any non-empty subset accepted. It also takes one four-field `replicated_definition` entry. It has no `input_records` and no `derivation` parameter, and the tolerance mapping cannot carry a `kind`. So:

- the four per-tolerance kinds (three `preference`, one `derived`) must live as four-field entries in Phase 37's own prereg module;
- that module must assert that all four keys are present;
- the destroyed_pct tolerance must be computed in that module from the committed records, torch-free.

Phase 35's ordering test (leg (a)) then freezes every commit of `scripts/phase37_*prereg.py` before the first `results/phase37_*` record. Everything R1b needs from the prereg must therefore be in it before R1a's record is committed.

**Primary recommendation:** commit in this order:

1. `scripts/phase37_prereg.py` + `tests/test_phase37_prereg.py`, complete for both R1a and R1b;
2. `scripts/phase37_routes.py` (five named routes, `rederive(arm_record)`, and the D-08 wrapper `select_target_prefix`) + `scripts/phase37_r1a.py` and their tests;
3. the R1a record, after approved;
4. `scripts/phase37_r1b.py` + a LaunchAgent plist, tested on CPU by feeding the committed `phase19_arm_erased.json` through the replica comparison (it must read REPLICATED with 0 differing draws);
5. code review, Rafael's approved, `require_launch("R1b")`, the run, and the records after approved.

## Premise checks (CONTEXT.md, measured)

| # | CONTEXT premise | Measured | Verdict |
|---|---|---|---|
| P1 | Line refs `phase35_prereg.py` :453 / :463 / :434 / :1191 / :1798 / :1882 / :320 | `grep -n`: `R1A_ASSERTIONS` 453, `r1a_rederive` 463, `e1_condition_b_margin` 434, `_rule_r1b_tolerance_and_replicated` 1191, slot dict 1798, `fill` 1882, `"results/phase37_*"` 320 | TRUE, no drift |
| P2 | `phase19_erasure.py` :275 / :2443 / :3096 / :3558; `phase19_run.py` :2771 / :620 / :1290; `erasure_gate.py:86` | 275 `ablate_components`, 2443 `select_ablation_prefix`, 3096 `reference_set_for_calibration`, 3558 `_selected_components`; 2771 `report`, 620 `_pooled_rows`, 1290 `_order_normalised`; 86 `MARGIN_K = 2` | TRUE |
| P3 | README defect lines `:1562`/`:2948`/`:3850-3855`/`:2922`/`:3811`/`:3576` | `sed -n` shows the cited code at each line | TRUE |
| P4 | "Reuse `phase19_run.report()`'s existing A–D routing" | `report()` writes `pin.ERASURE_REPORT_PATH` (`results/phase19_erasure_report.md`) at `phase19_run.py:3007` with no `_refuse`; B and D are inline expressions, not functions | **PARTLY FALSE as a mechanism.** The routing can be reused only as its constituent functions (`_pooled_rows`, `_order_normalised`) plus thin named wrappers for B and D. Calling `report()` would overwrite a committed Phase 19 file |
| P5 | D-08: the wrapper "selects `reference_set_for` instead of `reference_set_for_calibration` inside `_selected_components`' path" | `_selected_components(adapter_path, fact)` (`:3558`) hard-codes `references=reference_set_for_calibration(fact.slot, fact)` (`:3576`), loads its own model and returns only the prefix; it has no parameter to override. `select_ablation_prefix` takes `references` as a keyword argument, and `phase19_run.target_ablate` (`:885`, the producer of the committed curve) already routes E by passing `extraction.reference_set_for(pin.TARGET_SLOT)` | TRUE in intent. Mechanism: the wrapper must call `pin.select_ablation_prefix(..., references=reference_set_for(slot), ...)` in `target_ablate`'s shape. It cannot route "inside" `_selected_components` without monkeypatching the pin, so do not monkeypatch |
| P6 | D-09 D: "`[ppl, n]` raises a `TypeError` in the gate" | `erasure_succeeded(..., retention_ppl=[3.6709177253236867, 1000285])` raises `TypeError: unsupported format string passed to list.__format__`. On these records `dialogue_ppl <= dialogue_cap` is False, so the `and` at `erasure_gate.py` short-circuits before `retention_ppl <= retention_cap`; the TypeError comes from the reason's `{retention_ppl:.6f}` format | TRUE (a TypeError in the gate). The README's "where the comparison raises `TypeError`" is imprecise on these records. **Tests must use `pytest.raises(TypeError)` with no message match** |
| P7 | D-09 B: "yields the `ceiling` floor 0.2 instead of TARGET_FLOOR" | `pin._calibration_rate()` = `0.8846153846153846`; `lock_erasure_floor` → `0.2`; `floor_branch` → `'ceiling'`; corrected rate `0.0` → `0.09107873950450847` = `TARGET_FLOOR`, branch `reachability-min` | TRUE. Note: on these records the unrouted-B **verdict is still FAILURE** ((b) and (c) fail anyway), so B's natural red must assert the floor value, never the verdict |
| P8 | D-06: "One sweep costs 6.2–7.0 min" | Sweeps on record: 6.959359816710154 (curve), 6.15522662003835 and 6.133444146315257 (resweep runs) min | Slightly off: the measured range is **6.13–6.96 min**. Harmless to the 1.259 h sum |
| P9 | D-06 arithmetic | (68.58400233189265 + 6.959359816710154)/60 = `1.2590560358100467` h; `front_hours.R1b` = `1.1081805983679887`; ×1.5 = `1.6622708975519829` | TRUE |
| P10 | D-02 tolerance 0.8396203493271365 | `MARGIN_K * floor / g0 * 100` → `0.8396203493271365`; `100 * MARGIN_K * floor / g0` and `MARGIN_K * floor * 100 / g0` → `0.8396203493271364` | TRUE **only in D-02's operation order**. The order is load-bearing for any repr-equality test |
| P11 | Re-sweep: |R|=8 → k=78 prefix identical, |R|=6 → k=120; curve `reference_set_size` 8 | `replication.prefix_identical_to_committed` True, `remeasured_k_under_reference_set_for` 78, `..._calibration_twin` 120, `ordering_is_reference_set_invariant` True; curve `reference_set_size` 8, `calibration_twin_reference_set_size` 6 | TRUE |
| P12 | `ablate_components` zeros both factors on clones, refuses duplicates | `phase19_erasure.py:275-324`: `detach().clone()` every tensor; `_prove(address not in seen, ...)` | TRUE: a set-equal prefix gives identical weights in any order |
| P13 | "R1b is an MPS replica" implies Phase 19 ran elsewhere | The committed curve, erased arm and re-sweep all ran on **`mps`, torch 2.7.1** (`device` fields). The k* arms (2026-09-29, MPS) reproduced the erased arm's `pre_erasure.dialogue_ppl` and `retention_ppl` **bit-identically**, at k = 8/16/32/64 | Not a premise error; it strengthens the prior. R1b is a same-device re-run seven weeks later on macOS 26.5.1 (M3 Pro), and the venv torch is still 2.7.1 |
| P14 | No `results/phase37_*` or `scripts/phase37_*` exists | `ls results \| grep phase37` → 0; `git ls-files results \| grep phase37` → none; `ls scripts \| grep phase37` → none. `grep -rl phase37` hits only `phase35_prereg.py`, `phase36_budget.py` and their tests (path reservations and the ledger's phase-37 handling) | TRUE: nothing of this phase is already built |
| P15 | Phase 36 budget text on the re-sweep | `phase36_budget.py:180-184`: "the M1 re-sweep (6.959 min) are NOT in R1b's hours: if Phase 37 wants them they need Rafael's approved (D-06: nothing reallocated)" | Consistent with D-06's conditional approval. The plan should quote Rafael's conditional approval from 37-DISCUSSION-LOG and still take his per-phase "approved" before launch (ROADMAP Approvals paragraph) |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Tolerances, "replicated", D-04/D-07 rules | Pre-registration module (torch-free, `scripts/phase37_prereg.py`) | `phase35_prereg.fill` (the only door to the slot) | PREREG-05..07; it must precede every `results/phase37_*` record in git |
| A–E routing + `rederive(arm_record)` | Routing module (`scripts/phase37_routes.py`, imports the pin, CPU) | `phase19_run._pooled_rows` / `_order_normalised`, `pin.render_verdict` | REPRO-02; shared by R1a (committed record) and R1b (replica record); Phase 41 imports the E wrapper |
| R1a assert + write-once record | CPU driver (`scripts/phase37_r1a.py`) | `phase25_run.atomic_write_json`, `personacore.provenance` | REPRO-01, D-10 |
| R1b sweep + erased arm | MPS driver (`scripts/phase37_r1b.py`) under a LaunchAgent | the pin's `select_ablation_prefix` / `run_erasure_arm(record_path=...)` | REPRO-03; MPS only, about 1.26 h |
| Budget gate, start/end, heartbeat | `phase36_ledger` (`require_launch`, `append`, `reconcile`) | `phase25_run.beat` / `start_heartbeat` | 36-CONTEXT D-11..D-13 |
| Record persistence and ordering | git (ancestry tests, ledger-first commits) | Rafael's "approved" checkpoints | SC4; Phase 35 slot ordering legs (a)/(c) |

## Standard Stack

No new dependency is installed by this phase. Everything is either the repo's own modules or what is already pinned.

### Core (already in the repo)
| Module | Role in Phase 37 | Verified |
|---|---|---|
| `scripts/phase35_prereg.py` | `fill`, `R1A_ASSERTIONS`, `r1a_rederive`, `e1_condition_b_margin`, `MARGIN_K`, `V6_RESULT_PATHS`, `ENTRY_FIELDS`/`KINDS`/`FORBIDDEN_PHRASE` | read and dry-called |
| `scripts/phase19_erasure.py` (CLOSED, 15 commits, sha256 `c407246d…6e303`) | `select_ablation_prefix`, `run_erasure_arm(record_path=)`, `render_verdict`, `zero_results_have_nll`, `lock_erasure_floor`, `nontarget_rows`/`nontarget_deltas`, `target_fact_id`, `reference_set_for_calibration` (unrouted E), `_calibration_rate` (unrouted B) | `shasum -a 256` |
| `scripts/erasure_gate.py` (sha256 `a79d317a…facde`) | `erasure_succeeded` (reached via `render_verdict`), `MARGIN_K` | read |
| `scripts/phase19_run.py` (UNPINNED driver, sha256 `b7bd0e7e…dffde`) | `_pooled_rows` (C), `_order_normalised` (A), `CALIBRATION_CORRECTION_PATH`, `TARGET_CURVE_PATH`, `RESWEEP_PATH` | imported read-only |
| `scripts/phase19_floor.py` (torch-free) | `TARGET_FLOOR`, `NONTARGET_NOISE_FLOOR`, `DIALOGUE_PPL_NOISE_FLOOR`, `EVIDENCE_ARTIFACT` | measured |
| `scripts/phase18_extraction.py` | `reference_set_for` (routed E), `CORE_SLOTS` | measured |
| `scripts/phase36_ledger.py` | `require_launch`, `append`, `run_id`, `reconcile`, `HEARTBEAT_PATH` | `require_launch("R1b")` called read-only |
| `scripts/phase25_run.py` | `beat`, `start_heartbeat`, `atomic_write_json`, `disk_precheck` | signatures read |
| `src/personacore/provenance.py` | `git_sha`, `refuse_if_dirty(who, detail, pathspec, cwd)` | read |
| torch | 2.7.1, MPS available (venv) | `python -c` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|---|---|---|
| Thin named wrappers for B and D | Calling `phase19_run.report()` | Rejected: it rewrites `results/phase19_erasure_report.md` |
| `select_ablation_prefix(references=reference_set_for(slot))` | Monkeypatching `pin.reference_set_for_calibration` around `_selected_components` | Rejected: it patches the closed pin at runtime, `_selected_components` also discards the curve, and the twin raises SystemExit on `street`/`house_number` (|R| = 5), which Phase 41 needs |
| Pin arm record committed under `results/phase37_*` | Gitignored `data/` (the Phase 36 probe pattern) | `data/` loses the draws an outsider needs to re-derive R1b. The record is 749 KB (like `phase19_arm_erased.json`), so commit it |

**Installation:** none.

## Package Legitimacy Audit

No external package is installed by this phase, so slopcheck was not needed.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---|---|---|---|---|---|---|
| (none) | — | — | — | — | — | — |

**Packages removed:** none. **Packages flagged:** none.

## R1a, measured now (read-only, CPU, 2026-10-03)

| Quantity | Path through code | repr |
|---|---|---|
| k | `phase35_prereg.r1a_rederive()["k"]` (= `len(config.ablated_components)`) | `78` |
| destroyed_pct | `r1a_rederive()["destroyed_pct"]` `(1 - g1/g0) * 100`; `report()`'s `100.0*(g0-g1)/g0` gives the same | `77.6370113463966` |
| margin | `e1_condition_b_margin()` = `2 * 0.14814814814814814` | `0.2962962962962963` |
| family / K / tiers | erased `config` | `A2`, `48`, `('core_held_out', 'core_taught')` |
| target (C routed) | `_pooled_rows(erased draws)[target_fact_id]` | `cand_dog_zorp 0 / 27` |
| non-target deltas (C routed) | `pin.nontarget_deltas(nontarget_rows(pre), nontarget_rows(post))`, slot order | `[0.7407407407407407, 1.0, 1.0, 0.9629629629629629, 0.7037037037037037, 0.37037037037037035, 0.7777777777777778]` |
| beyond margin | `sum(d > margin)` | `7 / 7` (min 0.37037037037037035) |
| (b) floor re-derived from replicate arm | `pin.nontarget_noise_floor(...)` via `_pooled_rows` on `phase19_arm_replicate.json` | `0.14814814814814814` (== `phase19_floor.NONTARGET_NOISE_FLOOR`) |
| dialogue floor | `pin.dialogue_floor_from_record()` | `0.005214448168350039` |
| verdict (A, B, C, D routed) | `pin.render_verdict(...)` | `FAILURE`; reasons `(a) target upper bound 0.0911 over 27 questions <= calibrated floor 0.0911` / `(b) worst non-target degradation 1.000000 > k=2 x 0.148148 = 0.296296` / `(c) dialogue PPL 4.8511 vs cap 4.5837; retention PPL 3.670918 vs cap 4.029000`, identical to the text in `_verdict.recorded_verdict(results/phase19_erasure_report.md)` |
| wilson_upper_bound(0, 27) | gate | `0.09107873950450847` (== `TARGET_FLOOR` exactly, so (a) holds at equality) |
| D-02 tolerance | `2 * 0.005214448168350039 / 1.2420966625043919 * 100` | `0.8396203493271365` |
| tree after run | `git status --porcelain --untracked-files=all` before == after | `True` |

Input records R1a reads, with their SHA-256 today (each committed once):
`results/phase19_arm_erased.json` `c10313a7…e505` (equal to the SHA in `phase36_budget_prereg.RULING`), `results/phase18_arm_adapter-on.json` `71fb0627…7c4c7c`, `results/phase19_noise_floors.json` `ad2c96dd…daba`, `results/phase19_calibration_correction.json` `833631cf…1858`, `results/phase19_dialogue_floor.json` `57d648d2…7934`, `results/phase19_arm_cal-erased.json` `3e80696c…15cb4` (unrouted-B description), `results/phase19_arm_replicate.json` `77474413…01ef` (optional (b) floor re-derivation), `results/phase19_collateral_curve.json` `e27d64ef…ea7`, `results/phase19_reference_set_resweep.json` `3fada88f…2309`. The record must compute these at write time, never type them.

## Defects A–E: routed vs unrouted, measured on committed inputs

| Defect | Named route (recommended) | What it does (reused code) | Unrouted path (the pin's own) | Unrouted value on committed input | Routed value |
|---|---|---|---|---|---|
| A | `route_a(arm_record)` | `pin.zero_results_have_nll(phase19_run._order_normalised(arm_record))` | `pin.zero_results_have_nll(arm_record)` | `False` → verdict `INCONCLUSIVE` | `True` → verdict `FAILURE` |
| B | `route_b()` | reads `phase19_run.CALIBRATION_CORRECTION_PATH`, proves `governs == "corrected_target_floor"` and `pin.lock_erasure_floor(rate) == phase19_floor.TARGET_FLOOR`, returns that floor | `pin.lock_erasure_floor(pin._calibration_rate())` | rate `0.8846153846153846` → floor `0.2`, branch `ceiling` (the verdict is still FAILURE) | `0.09107873950450847`, `reachability-min` |
| C | `route_c(draws, ...)` | `phase19_run._pooled_rows(draws, values, family, tiers)` | `arm_record["per_fact"]` | target `0/14`; `pin.nontarget_deltas(nontarget_rows(per_fact), ...)` → `SystemExit: ... carries 14 questions against the pooled per-core-fact count 27` | `0/27`, 7 deltas |
| D | `route_d(arm_record)` | `arm_record["retention_ppl"][0]` (scalar; `n` travels beside it) | `arm_record["retention_ppl"]` = `[3.6709177253236867, 1000285]` | `TypeError` inside `erasure_succeeded` (format of the reason, see P6) | `3.6709177253236867` |
| E | `select_target_prefix(model, tok, device, artifact, *, fact, dialogue_ppl)` (the D-08 / ERASE-08 wrapper) | `pin.select_ablation_prefix(..., references=phase18_extraction.reference_set_for(fact.slot), collateral={s: (taught[s], reference_set_for(s)) for s in CORE_SLOTS}, ...)` (`target_ablate`'s call shape) | `_selected_components` → `reference_set_for_calibration(slot, fact)` | `pet_name`: |R| = `6` (`krix snorrel nyxen fenmark grindlow zorp`) → committed re-sweep k = `120`; also `SystemExit` on `street` and `house_number` (|R| = 5) | |R| = `8` (`krix nubbin torvo snorrel nyxen fenmark grindlow zorp`) → k = `78`, prefix identical |

|R| for every locked fact (relevant to Phase 41's reuse of the E wrapper):

| slot | `reference_set_for` | `reference_set_for_calibration` |
|---|---|---|
| person_name | 8 | 6 |
| pet_name | 8 | 6 |
| cat_name | 7 | 6 |
| sibling_name | 7 | 6 |
| hometown | 7 | 6 |
| street | 6 | SystemExit (|R| = 5) |
| birth_year | 7 | 6 |
| house_number | 6 | SystemExit (|R| = 5) |

**How "removing the routing turns a test red, naturally" works (D-09).** The red state is the pin's own code path on the real committed records, so no inverse edit is involved. Recommended shape, two halves per defect:

1. **Tripwire, "the defect is still live":** the test calls the pin's unrouted path on the committed record and asserts the wrong value above. Examples: `pin.zero_results_have_nll(erased) is False`; `pin.lock_erasure_floor(pin._calibration_rate()) == 0.2`; `{r["n_questions"] for r in erased["per_fact"].values()} == {14}`; `pytest.raises(TypeError)` on the gate with the pair; `len(pin.reference_set_for_calibration("pet_name", target)) == 6`. The precedents are `tests/test_phase19_correction.py:264` (`test_defects_a_b_and_c_are_all_still_live_and_all_published`) and `tests/test_phase19_erasure.py:~3920` (the E guard).
2. **Routed:** R1a's assertions pass only through the route.

`rederive(arm_record, routes=ROUTES)` takes the routes as a mapping. A parametrized test swaps ONE letter for the pin's unrouted function (`UNROUTED = {"A": pin.zero_results_have_nll, "B": lambda: pin.lock_erasure_floor(pin._calibration_rate()), ...}`) and asserts the run diverges: A gives INCONCLUSIVE, B gives floor 0.2, C gives SystemExit or 0/14, D gives TypeError. The unrouted callables are the pin's real functions, not mutants. For E, the test monkeypatches `pin.select_ablation_prefix` with a recorder (no model) and asserts the wrapper passes `len(references) == curve["reference_set_size"] == 8`. With the unrouted reference choice it is 6, matching the re-sweep record's k = 120 ≠ 78.

**TDD order gives the natural red for free.** Write `tests/test_phase37_routes.py` against the committed records BEFORE `phase37_routes.py` has its routes. Record the measured red output in the SUMMARY, then add the routes. Never plant and revert.

## The slot, its census and ordering tests

**Rule** (`phase35_prereg.py:1191`): `_rule_r1b_tolerance_and_replicated(*, tolerance, replicated_definition)`.

What it validates:
- `tolerance` must be a non-empty Mapping with `set(tolerance) <= set(R1A_ASSERTIONS)`. A **subset is accepted**: `{"k": 0}` alone passes, measured;
- each value must be `int`/`float` (bool excluded), finite and ≥ 0;
- `replicated_definition` goes through `_frozen_entry` → `_prove_entry`, so it must have exactly `{value, derivation, kind, source}`, `kind ∈ {derived, preference}`, non-empty str `derivation` and `source`, and no `proposer`/`adopted_by` key or forbidden phrase.

It returns `MappingProxyType({"tolerance": ..., "replicated_definition": deep-frozen entry})`.

Dry call measured, in memory, torch-free: `fill("r1b_tolerance_and_replicated", tolerance={"k":0,"target_correct":0,"nontargets_beyond_margin":0,"destroyed_pct":0.8396203493271365}, replicated_definition={...})` is accepted. `{"k": True}`, `{"k": -1}`, `{"x": 0}`, `{}` and a `proposer` key are all refused with SystemExit.

Slot registry entry (`:1798`): `owner_phase 37`, `input_records ()`. With no input records, the rule takes no `input_records`/`derivation` (proved by `_prove_slots`), and nothing in the slot reads records. Phase 37 computes the destroyed_pct tolerance itself.

**Census constraints (`tests/test_phase35_prereg.py::_slot_census_failures`, run over `scripts/**/*.py` and `src/**/*.py`):**
- The fill must sit in a file matching `scripts/phase37_*prereg.py` (`owner_prereg_glob`). `scripts/phase37_prereg.py` matches.
- The fill must be `R1B_TOLERANCE_AND_REPLICATED = phase35_prereg.fill("r1b_tolerance_and_replicated", ...)`, a module-level single-target binding whose whole value is the call, with a constant slot string.
- After a plain `import phase35_prereg`: no alias, no `from phase35_prereg import fill`, no `SLOTS` import or write, no `SLOTS[...]["rule"]`.
- **No private access `phase35_prereg._anything`** (that includes `_prove_entry`, `_prove`, `_REPO_ROOT`) in ANY scripts file. Phase 36 copied `_prove_entry` (`phase36_prereg.py:62`). `phase36_prereg._prove_entry` is not banned by the census and is an identical validator, so either reuse it or copy it.
- The slot is filled exactly once anywhere.

**Ordering legs (`_slot_ordering_failures`, `test_slot_ordering_is_green_on_the_real_repo`):**
- (a) Because the r1b slot has no phase-37 input, **every commit** touching the fill file must strictly precede the first add of **every** `results/phase37_*` record. The prereg is therefore frozen at the first Phase 37 record, which is R1a's. Anything R1b needs from it (tolerances, kinds, D-04/D-07 rules, the bit-identity unit, record paths) must be in it before R1a's record commit. Later corrections are dated continuation modules, never edits.
- (c) Once any `results/phase37_*` is tracked, the slot must be filled. This is satisfied by committing the fill first.

Recommended Phase 37 prereg entries (four fields each, no proposer):

| entry | value | kind | derivation / source |
|---|---|---|---|
| `tolerance_k` | 0 | preference | Rafael's ruling (37-CONTEXT D-02); k is an integer count; the k* precedent measured MPS curve agreement at \|diff\| = 0.0 (`erasure_kstar_prereg.py:139`) — context, not a derivation |
| `tolerance_target_correct` | 0 | preference | numerator tolerance; the denominator (27) must be equal exactly — state it |
| `tolerance_nontargets_beyond_margin` | 0 | preference | count tolerance; denominator 7 exact |
| `tolerance_destroyed_pct` | computed `MARGIN_K * floor / g0 * 100` | derived | floor from `phase19_floor.EVIDENCE_ARTIFACT["DIALOGUE_PPL_NOISE_FLOOR"]` (`results/phase19_noise_floors.json`), `dialogue_ppl_noise_floor.value`; g0 from `results/phase19_arm_erased.json` `pre_erasure.dialogue_ppl`; g0 is the COMMITTED gap |
| `replicated_definition` (passed to fill) | all four keys; `abs(replica - committed) <= tolerance[key]` (inclusive, like the gate's `<=`); tuple keys compare numerators with exact denominators | preference | D-03 |
| `prefix_divergence_rule` | D-07 text | preference | D-07 |
| `not_replicated_rule` | D-04 text (write-once, one attempt, per-fact deltas vs 0.14814814814814814 as context) | preference | D-04 |
| `draw_identity_description` | unit: completions differing out of 216 × 48 = 10,368 (+ entries differing out of 216); description only | preference | D-03 |

Also add `COMMITTED`, `RECORDS_AT_COMMIT = 0`, and the record paths, derived (`fnmatch` against the `"results/phase37_*"` member of `phase35_prereg.V6_RESULT_PATHS`). The prereg must assert `set(R1B_TOLERANCE_AND_REPLICATED["tolerance"]) == set(phase35_prereg.R1A_ASSERTIONS)`, because the slot accepts a subset.

Torch-free import: read the two records with `json`, without importing `phase19_erasure` (that pulls in torch). Type the erased-arm path once as `"results/phase19_arm_erased.json"` and add a test proving it equals `pin.arm_record_path("erased")` relative to the repo, the same pattern as `phase35_prereg._CALIBRATION_CORPUS`. Measured: `fill` runs with `'torch' in sys.modules == False`.

## Ledger and launch (36-CONTEXT D-11..D-13)

Measured today: `phase36_ledger.require_launch("R1b")` → `{'front': 'R1b', 'spent_seconds': {'probes': 13176.153838, 'R1b': 0.0, ...}, 'total_seconds': 13176.153838, 'lifted': ()}`. It passes and writes nothing.

| Step | Call | Notes |
|---|---|---|
| before launch | `phase36_ledger.require_launch("R1b")` | refuses a cut front; pauses at stops (a) R1b spent > 1.5 × 1.1081805983679887 h, (b) total ≥ 90 h stop line, (c) projection > 90 h. Projection today 77.72 h; after R1b ≈ 77.72 − 1.108 + 1.259 ≈ 77.87 h |
| start | `rid = phase36_ledger.run_id(37, "R1b", "replica")` → `"v6/37/R1b/replica"`; `append("start", run_id=rid, phase=37, front="R1b")` | refuses if the run is still open |
| heartbeat | `phase25_run.beat(phase36_ledger.HEARTBEAT_PATH, point=rid, stage=..., shape=None, draw_index=None)` once at once, then `stop, thread = phase25_run.start_heartbeat(path, state)` | the `phase36_probe.run_front` pattern (`phase36_probe.py:355-417`) |
| end | `append("end", run_id=rid, phase=37, front="R1b", record="results/phase37_r1b.json")` | the record must match `V6_RESULT_PATHS`; when tracked, `_closed_row` reads **`provenance.run.started_utc` / `finished_utc`** from it, or `spent()` refuses |
| crash | `python scripts/phase36_ledger.py reconcile` writes a `lost` line counted to the last beat | whether a crash consumes D-04's "one attempt" is an open question |

**Launch on this box:** copy `artifacts/com.personacore.phase36.probe.plist` to `artifacts/com.personacore.phase37.r1b.plist`. Keep `/usr/bin/caffeinate -dims` + `.venv/bin/python` + driver; `KeepAlive` false; `RunAtLoad` false; `WorkingDirectory` the repo; `logs/phase37_r1b.{out,err}`; `EnvironmentVariables` `PERSONACORE_SWEEP_ACTIVE=1`, `PATH`, `PYTHONUNBUFFERED`. Rafael copies it to `~/Library/LaunchAgents`, then runs `launchctl bootstrap` / `kickstart` / `bootout`. Pin it with a test shaped like `tests/test_phase36_probe.py::test_plist_mirrors_the_phase31_probe_agent`, which uses suffix comparisons so it holds on CI. While the run is live, run no pytest and no other MPS work. Under launchd the caffeinate is the CHILD (`ppid == driver pid`).

**Commit order after the run (W9 precedent, 36-07):** the ledger first (`ledger/v6_mps_ledger.jsonl` with the end line), then `results/phase37_r1b_arm.json`, then `results/phase37_r1b.json`. That keeps `tests/test_phase36_ledger.py::test_every_tracked_v6_mps_record_has_a_launch_line` (it scans `results/phase3[7-9]_*` for `provenance.run.device == "mps"`) and `test_phase36_budget.py::later_records` green at every intermediate commit. Each commit happens only after Rafael's "approved" (SC4).

## R1b design (D-05, D-07, D-03, D-04)

Data flow:

```
Rafael "approved" ──► require_launch("R1b") ──► ledger start + heartbeat
        │
        ▼
load production adapter (sha256 must equal curve.adapter_in_sha256 = 226f2ae5…ebfb, verified today)
        │
        ▼
select_target_prefix (D-08 / defect E)  ── pin.select_ablation_prefix(references=reference_set_for("pet_name"))
        │            re-measures: 288-address ordering, stop k, intact_nll, curve rows (MPS)
        ▼
D-07 decision vs committed curve.ordered_prefix
   ├─ k != 78 or set differs ──► write results/phase37_r1b.json  NOT_REPLICATED {k, set difference}
   │                              ledger end; STOP (root cause first; new run needs approved)
   └─ k == 78 and set equal ──► record positions moved (description)
        │
        ▼
pin.run_erasure_arm("erased", device, components=<re-measured list>, record_path=results/phase37_r1b_arm.json)
        │   re-measures: pre_erasure dialogue/retention/exposure, 216 × 48 = 10,368 A2 draws, post block
        │   inherited by the pin's design: the pre-erasure per_fact block is Phase 18's committed record
        ▼
routes.rederive(replica arm record)  (A, B, C, D routes: the SAME function R1a runs on the committed record)
        │
        ▼
compare with R1A_ASSERTIONS under R1B_TOLERANCE_AND_REPLICATED  ──►  REPLICATED / NOT_REPLICATED
   + description: draws bit-identical? (#differing completions / 10,368; #entries / 216),
     positions moved, per-fact non-target deltas vs 0.14814814814814814 (NOT_REPLICATED context)
        │
        ▼
write results/phase37_r1b.json (write-once, provenance.run{device, started_utc, finished_utc, git_sha, torch})
ledger end ──► Rafael "approved" ──► commit ledger, then arm record, then summary
```

Key facts:
- **Never use the pin's default record path.** `run_erasure_arm` defaults to `arm_record_path(arm)` = `results/phase19_arm_erased.json`; its clobber refusal would stop it, but always pass `record_path=` explicitly (the `erasure_kstar_run.measure` precedent, `erasure_kstar_run.py:139`). Prove at runtime that the path matches `results/phase37_*`.
- The pin writes its arm record with `sort_keys=True` (`:2948`), so **defect A bites the replica record too**. `rederive` must route A on both records. This exercises the same code in R1a and R1b.
- `run_erasure_arm("erased", ...)` asserts Phase 18 parity before the first draw and reseeds with `seed_everything(recall.SEED)` at its own start, so the earlier sweep in the same process does not shift the draws' RNG.
- The sweep's model and the arm's model are separate loads. The arm loads the production adapter itself (`adapter_path=None`), and its pre-erasure block must be measured on the unerased adapter (`phase19_run.target_score` comment).
- Wall-clock basis: Phase 36 probe `unit_prices.a2_k48_high` = 3989.450154124759 s (= `front_hours.R1b` × 3600) plus a sweep of 6.13–6.96 min gives about 1.22–1.26 h, inside 1.662 h.

**CPU wiring proof before launch** (memory "dry-run tests hide an unwired driver"): feed the COMMITTED `results/phase19_arm_erased.json` through R1b's consumer (`rederive` → tolerance comparison → draw-identity count) as if it were the replica. It must read REPLICATED, 0 differing completions out of 10,368, and 0 positions moved (with the committed prefix as the "re-measured" one). Take the kwargs from `inspect.signature`, not from a fixture. Then monkeypatch only `pin.select_ablation_prefix` and `pin.run_erasure_arm`, with the latter copying the committed record to the given `record_path`. That drives `main()` end to end on CPU into `tmp_path`.

## Recommended Project Structure

```
scripts/
├── phase37_prereg.py        # torch-free: entries, the slot fill, record paths (frozen at first record)
├── phase37_routes.py        # route_a..route_d, select_target_prefix (E / ERASE-08), rederive(record)
├── phase37_r1a.py           # CPU: assert + write-once results/phase37_r1a.json
└── phase37_r1b.py           # MPS: ledger, sweep, D-07, arm, compare, write-once records
artifacts/com.personacore.phase37.r1b.plist
tests/
├── test_phase37_prereg.py   # ancestry, entries, fill, census, torch-free, every function tested, no skips
├── test_phase37_routes.py   # A–E natural reds, pin/gate byte-unchanged, AST call-site gates
├── test_phase37_r1a.py      # REPRO-01 on committed records; write-once to tmp; no phase19 write
└── test_phase37_r1b.py      # D-07/D-03/D-04 logic on CPU; consumer fed the committed record; plist
results/ (written by the drivers, committed after approved)
├── phase37_r1a.json
├── phase37_r1b_arm.json     # the pin's ARM_RECORD_KEYS record (draws), only if the arm runs
└── phase37_r1b.json         # REPLICATED / NOT_REPLICATED + provenance.run (ledger end names it)
```

## Code Examples

### The fill (census-conformant)
```python
# scripts/phase37_prereg.py — torch-free. Source pattern: scripts/phase36_budget_prereg.py
import json, pathlib, sys
_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))
import phase19_floor      # noqa: E402  torch-free
import phase35_prereg     # noqa: E402  plain import: no alias, no `from`, no `_` access

ERASED_RECORD = "results/phase19_arm_erased.json"  # test proves == pin.arm_record_path("erased")
_floor = json.loads((_ROOT / phase19_floor.EVIDENCE_ARTIFACT["DIALOGUE_PPL_NOISE_FLOOR"])
                    .read_text(encoding="utf-8"))["dialogue_ppl_noise_floor"]["value"]
_pre = json.loads((_ROOT / ERASED_RECORD).read_text(encoding="utf-8"))["pre_erasure"]["dialogue_ppl"]
_g0 = _pre["adapter_on"] - _pre["adapter_off"]
DESTROYED_PCT_TOLERANCE = phase35_prereg.MARGIN_K * _floor / _g0 * 100  # D-02 ORDER: ...365

R1B_TOLERANCE_AND_REPLICATED = phase35_prereg.fill(
    "r1b_tolerance_and_replicated",
    tolerance={k: ENTRIES[f"tolerance_{k}"]["value"] for k in phase35_prereg.R1A_ASSERTIONS},
    replicated_definition=ENTRIES["replicated_definition"],
)
```

### R1a's verdict call (routes A–D, the pin's single gate call site)
```python
# Source shape: scripts/phase19_run.py:2814-2878 (report), minus every write
verdict = pin.render_verdict(
    target_successes=t["n_answerable"], target_questions=t["n_questions"],
    target_floor=routes.route_b(),                       # B
    nontarget_deltas=deltas,                             # C via _pooled_rows
    nontarget_noise_floor=phase19_floor.NONTARGET_NOISE_FLOOR,
    dialogue_ppl=erased["dialogue_ppl"]["adapter_on"],
    dialogue_ppl_noise_floor=pin.dialogue_floor_from_record(),
    retention_ppl=routes.route_d(erased),                # D
    zero_results_have_nll=routes.route_a(erased),        # A
)
```

### The defect-E wrapper (ERASE-08)
```python
# Source shape: scripts/phase19_run.py:919-941 (target_ablate), the producer of the committed curve
def select_target_prefix(model, tok, device, artifact, *, fact, dialogue_ppl):
    """Defect E: the TARGET's stop is read on reference_set_for, never the calibration twin."""
    import phase14_factset as factset, phase18_extraction as extraction
    taught = {f.slot: f.value for f in factset.LOCKED_FACTS}
    return pin.select_ablation_prefix(
        model, tok, device, artifact, slot=fact.slot, value=fact.value,
        references=extraction.reference_set_for(fact.slot),
        collateral={s: (taught[s], extraction.reference_set_for(s)) for s in extraction.CORE_SLOTS},
        dialogue_ppl=dialogue_ppl,
    )
```

### Ancestry (SC4)
```python
# Source: tests/test_phase36_prereg.py:52-57 + tests/test_phase29_prereg.py:69 (_assert_frozen_before)
def test_phase37_prereg_is_frozen_before_every_phase37_record():
    tracked = sorted(_git("ls-files", "results/phase37_*").split())
    _assert_frozen_before("scripts/phase37_prereg.py", tracked)
    with pytest.raises(subprocess.CalledProcessError):   # natural RED: 35 was added before 37
        _assert_frozen_before("scripts/phase37_prereg.py", ["scripts/phase35_prereg.py"])
```
For "its ancestry test is committed before any record", check only the test file's FIRST add (`git log --diff-filter=A ... | tail -1`) against each record's first add. Do not use `_assert_frozen_before` on the test file: it requires EVERY commit to precede, and a later latent-red test fix (Phase 36 had two) would turn it red forever.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| Pooled 27-question rows | a per-tier sum loop | `phase19_run._pooled_rows` | the committed defect-C recovery; `erasure_kstar_run` already reuses it |
| Exposure key-order fix | your own reorder | `phase19_run._order_normalised` | it is what the published verdict used |
| The verdict | any (a)/(b)/(c) comparison | `pin.render_verdict` → `erasure_succeeded` | the 19-05 AST guard keeps the pin's single call site; a second evaluation is the failure this phase exists to rule out |
| The ablation sweep | an ordering or stop loop | `pin.select_ablation_prefix` | the closed rule; the ordering is reference-invariant |
| Arm drawing and scoring | a draw loop | `pin.run_erasure_arm(record_path=...)` | parity assertion, in-prompt guard, same-pass pre/post blocks |
| Budget, stops, lost hours | own bookkeeping | `phase36_ledger` | D-11..D-13; Phase 36 tests already anticipate phase-37 end lines |
| Atomic JSON write | `open().write` + `os.replace` | `phase25_run.atomic_write_json` | the `os.replace` census allows it only in `phase25_run.py`/`phase25_record.py` (`tests/test_phase25_driver.py:359`) |
| Dirty-tree refusal | `git status` parsing | `personacore.provenance.refuse_if_dirty` | untracked counts as dirty |
| Entry validation | new schema code | `phase36_prereg._prove_entry` (or a copy, as Phase 36 did) | `phase35_prereg._prove_entry` is banned by the census |

## Common Pitfalls

### Pitfall 1: Calling `phase19_run.report()` overwrites a committed Phase 19 file
**What goes wrong:** `report()` ends with `pin.ERASURE_REPORT_PATH.write_text(full)` (`:3007`) and has no refusal. **Avoid:** never call `report()`. Add an AST gate: no Call to the attribute `report` on the `phase19_run` binding in `scripts/phase37_*.py`. Also never call `run_erasure_arm` without `record_path=`, and never call a pin `_cmd_*`.

### Pitfall 2: The prereg is frozen at R1a's record
**What goes wrong:** Phase 35 leg (a) fails permanently if `scripts/phase37_prereg.py` gets a commit after any `results/phase37_*` first add. Deleting and re-adding cannot launder it (`adds[-1]`). **Avoid:** finish every R1b rule in the prereg before committing R1a's record. Any later correction is a dated continuation module, which must not call `fill` (the slot is filled once).

### Pitfall 3: The slot accepts a partial tolerance
**What goes wrong:** `set(tolerance) <= set(R1A_ASSERTIONS)`, so a missing key passes the fill. **Avoid:** assert equality of key sets in the prereg and in its test.

### Pitfall 4: Float operation order
**What goes wrong:** `100 * MARGIN_K * f / g0` → `0.8396203493271364`; D-02's order → `...365`. **Avoid:** compute in D-02's order. Tests compare against the same expression, never against a typed literal. An AST literal scan should refuse the float typed in source, using the phase35 `_literal_failures` pattern, `tests/test_phase35_prereg.py:749`.

### Pitfall 5: The ledger needs `provenance.run` on the record its end line names
**What goes wrong:** the pin's arm record has `config.device` but no `provenance`. If the end line names it, `_closed_row` refuses once it is tracked, and every later `spent()` and `require_launch` breaks. **Avoid:** the end line names `results/phase37_r1b.json`, which carries `provenance.run{git_sha, device, torch_version, started_utc, finished_utc}`. Commit the ledger first.

### Pitfall 6: Dirty-tree refusal blocks the summary write
**What goes wrong:** once the pin has written the untracked `results/phase37_r1b_arm.json`, `refuse_if_dirty(pathspec=("scripts","src","results"))` fails at summary time. **Avoid:** exclude the run's own records with `:(exclude)`, as `phase36_probe._emit_target` does. Refuse dirt on `scripts`/`src` at launch (the kstar `RULE_PATHSPEC` pattern).

### Pitfall 7: New skips break the pinned skip count
**What goes wrong:** `tests/test_phase25_venue.py` pins the M3 and ubuntu skip totals. A test that skips without `checkpoints/` (ubuntu) or without MPS changes them. **Avoid:** zero skips in `tests/test_phase37_*` (add the `_skip_failures` "no skips in this file" test). R1a needs only committed `results/`. R1b's logic is tested on CPU with monkeypatched device work.

### Pitfall 8: Repo-wide censuses a new `scripts/phase37_*.py` can trip
- the slot census (Phase 35), described above;
- `inject_lora` call sites (`tests/test_lora_inject.py`, hard-equality allowlist): use `phase14_recall.load_adapted_model`, never `inject_lora`;
- `retention_perplexity` call sites (`tests/test_phase19_erasure.py:1386`): never call it directly (`run_erasure_arm` does);
- `draw_all` / `build_recall_prompt` `persona=` censuses (`tests/test_phase14_scoring.py`);
- `os.replace` (`tests/test_phase25_driver.py:359`);
- `train_never_taught` / `train_arm(` registers;
- `== 10` literal count under `tests/` (`tests/test_phase21_sc5.py:266`): write no `== 10` in new tests, not even in comments;
- `mitigation_point_verdict` call sites (`tests/test_phase20_correction.py:1422`).

### Pitfall 9: Clean-tree probes and state-dependent tests
Eleven tests fail while `scripts/`, `tests/` or `results/` is dirty, which is expected before a commit. Tests asserting "untracked today" go red once records are committed (Phase 36 lesson). Run the full suite after each record commit. `tests/test_phase36_budget.py::test_emit_refuses_after_a_phase_37_record` and `later_records` already handle phase-37 end lines.

### Pitfall 10: The unrouted B and D reds are not verdict changes
Unrouted B still gives FAILURE, and unrouted D raises from the reason's format string. Assert the floor value and `TypeError`, never a verdict or message text.

### Pitfall 11: Bit identity can fail while replication holds
The OS has moved to macOS 26.5.1 since August; MPS kernels may differ. That is why D-03 makes bit identity description only. Count at the completion level (n = 10,368) and the entry level (n = 216), and never feed either into REPLICATED.

### Pitfall 12: A grep acceptance criterion over prose
Docstrings in these modules will discuss `reference_set_for_calibration`, `report()`, `_calibration_rate` and "TypeError". Use AST gates (Call nodes resolved through import aliases, docstrings excluded, non-empty meta-guard).

## State of the Art

| Old approach | Current approach | When changed | Impact |
|---|---|---|---|
| `_cmd_report` (pinned) renders the verdict | `phase19_run.report` routes A–D and calls `render_verdict` once | 19-15 | R1a reuses the pieces, never `report()` itself |
| `_selected_components` (twin, |R| = 6) | `target_ablate` passes `reference_set_for` (|R| = 8) | 19-12 | the E wrapper takes `target_ablate`'s call shape |
| Per-phase ad-hoc MPS accounting | the `phase36_ledger` milestone ledger | 2026-10-02 | R1b calls `require_launch` and start/end |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|---|---|---|
| A1 | `kind = preference` for the three zero tolerances is the honest label (no written derivation makes 0 follow from a measurement) | The slot | low; the planner surfaces it, as CONTEXT already asks |
| A2 | "count of differing draws" means completions out of 10,368 (and entries out of 216) | R1b design | low; description only, but the unit must be fixed in the prereg before the run |
| A3 | The D-04 "per-fact non-target deltas" means each non-target's replica pooled delta beside the committed delta, with \|replica − committed\| compared to 0.14814814814814814 as context | R1b design | medium; the record's context fields change. Confirm with Rafael |
| A4 | Committing the 749 KB pin arm record under `results/phase37_r1b_arm.json` is wanted (outsider re-derivation) | Structure | low |
| A5 | No markdown publication is needed in Phase 37 ("beside the verdict" = the `results/phase37_*` records); the v6.0 report (Phase 45) renders it | Summary | low–medium |

## Open Questions

1. **Does a crashed R1b attempt consume D-04's "one attempt"?** We know D-04 says one attempt, and that a new run needs approved and root cause. It is unclear whether this applies when no record exists (only a ledger `lost` line). Recommendation: treat any started attempt as the attempt, and require approved plus a reconcile before relaunch (the 36-07 W3 pattern). Ask Rafael at the plan checkpoint.
2. **The D-04 delta definition** (A3).
3. **Should R1a also re-derive the (b) floor from the replicate arm, as `report()` does?** Measured cheap (0.1 s) and equal. Recommendation: yes, as an extra assertion. It adds `phase19_arm_replicate.json` to the input SHA list.
4. **The sweep in the NOT_REPLICATED (D-07) case.** Recommendation: record the full re-measured `ordered[:k]` and curve rows in `phase37_r1b.json` in both branches, so the root-cause investigation has the data.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|---|---|---|---|---|
| Python 3.11 venv | everything | ✓ | 3.11.15 | — |
| torch + MPS | R1b | ✓ | 2.7.1, `mps.is_available()` True | — (R1b is MPS by design) |
| `checkpoints/persona_adapter.pt` | R1b | ✓ | sha256 `226f2ae5…ebfb` = curve `adapter_in_sha256` | — |
| `data/retention_val.bin`, `results/phase18_corpus.json` | R1b (pin) | ✓ | 2,000,572 B / 375,787 B | — |
| committed Phase 18/19 records | R1a, R1b comparator | ✓ | SHAs listed above | — |
| `phase36_budget.json` + ledger | R1b launch gate | ✓ | R1b 1.1081805983679887 h, stop 90 h, spent 13176.153838 s | — |
| launchd / caffeinate | R1b unattended | ✓ | macOS 26.5.1, Apple M3 Pro; phase25 agents listed as loaded but idle (`launchctl list`, pid `-`) | `nohup caffeinate -dims` (precedent) |
| Disk | R1b | ✓ | 471 GiB free | — |

No missing dependencies.

## Validation Architecture

### Test Framework
| Property | Value |
|---|---|
| Framework | pytest 8.x (venv), CPU-only |
| Config file | `pyproject.toml` / `tests/conftest.py` (`PERSONACORE_SWEEP_ACTIVE` skips MPS legs) |
| Quick run command | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase37_prereg.py tests/test_phase37_routes.py tests/test_phase37_r1a.py tests/test_phase37_r1b.py` |
| Targeted regression | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase35_prereg.py tests/test_phase36_prereg.py tests/test_phase36_ledger.py tests/test_phase36_budget.py tests/test_phase19_erasure.py tests/test_phase19_correction.py tests/test_phase16_prereg.py tests/test_erasure_kstar_run.py tests/test_lora_inject.py tests/test_phase25_driver.py tests/test_phase21_sc5.py`: measured 23.0 s + 26.8 s + 48.7 s today |
| Full suite command | `nohup sh -c ".venv/bin/pytest -q -p no:cacheprovider > $LOG 2>&1; echo EXIT=\$? >> $LOG" &` plus an `until grep -q '^EXIT='` waiter. It takes about **42–44 min** (STATE: 42:38 and 44:25; 3782 passed / 4 skipped at e72c17a), not 25 min. Bash caps at 600 s, so use about 5 waiter calls |

### Phase Requirements → Test Map
| Req / Decision | Behavior | Type | Automated Command | File Exists? |
|---|---|---|---|---|
| REPRO-01 | `phase37_r1a` asserts k 78, 0/27, 7/7 beyond `e1_condition_b_margin()`, 77.6370113463966, verdict FAILURE + reasons equal to the recorded `## Verdict`; exit 0 | unit (CPU, committed records) | `pytest tests/test_phase37_r1a.py -x` | ❌ Wave 0 |
| REPRO-01 | divergence halts: a monkeypatched record (one draw changed) gives SystemExit naming the key, and no file is written | unit | same | ❌ |
| REPRO-01 / D-10 | write-once into tmp: refuses overwrite, refuses dirty (recorded via monkeypatched `refuse_if_dirty`), carries the four numbers, input SHA-256s computed from bytes, git_sha; refuses unless `scripts/phase37_prereg.py` is tracked | unit | same | ❌ |
| REPRO-01 | AST: imports `phase19_erasure` and `erasure_gate`; `render_verdict` is the only verdict route; no `report` call; no `results/phase19_` write | AST | same | ❌ |
| REPRO-02 / D-09 A–D | tripwires: pin path on committed records gives False / 0.2 / {14} / TypeError | unit | `pytest tests/test_phase37_routes.py -x` | ❌ |
| REPRO-02 / D-09 A–D | swapping ONE route for the pin's unrouted function makes `rederive` diverge (parametrized over A–D) | unit | same | ❌ |
| REPRO-02 / D-08 E | wrapper passes |R| = 8 = curve `reference_set_size`; twin = 6; re-sweep record k(8) = 78, k(6) = 120, prefix identical | unit (recorder monkeypatch, no model) | same | ❌ |
| D-08 / ERASE-08 | `scripts/phase19_erasure.py` byte-unchanged: sha256 == `results/phase36_probe_e1.json` `provenance.module_sha256["scripts/phase19_erasure.py"]` (`c407246d…`), `git diff --quiet 3ba3e2c HEAD -- scripts/phase19_erasure.py` and a clean porcelain; `erasure_gate.py` is NOT in that record's module_sha256 (measured: None), so anchor it on its last commit `23a830c` (`git diff --quiet 23a830c HEAD -- scripts/erasure_gate.py`, sha256 `a79d317a…facde`) | unit | same | ❌ |
| REPRO-03 / D-01 | slot filled once in `scripts/phase37_prereg.py`; the census is green over `scripts/phase37_*.py` | unit | `pytest tests/test_phase37_prereg.py -x` | ❌ |
| REPRO-03 / D-02 | tolerance keys == `R1A_ASSERTIONS` keys; three zeros `preference`; destroyed_pct `derived` == `MARGIN_K*floor/g0*100` read from records; no float literal of it in source (AST) | unit + AST | same | ❌ |
| REPRO-03 / D-03, D-07, D-04 | entries exist with four fields, no proposer; prereg imports without torch | unit | same | ❌ |
| SC4 | prereg frozen before every `results/phase37_*` (`_assert_frozen_before` + natural-RED non-vacuity); the test file's first add precedes records; `RECORDS_AT_COMMIT` true at the first commit | git ancestry | same, plus `tests/test_phase35_prereg.py::test_slot_ordering_is_green_on_the_real_repo` | ❌ / ✅ |
| D-05 / D-07 | decision function: same set → run (positions moved counted); k ≠ 78 or a set difference → NOT_REPLICATED with only k and the difference; the arm is not called | unit (CPU) | `pytest tests/test_phase37_r1b.py -x` | ❌ |
| D-03 / D-04 | the committed record fed as the replica → REPLICATED, 0/10,368 differing; a perturbed copy → NOT_REPLICATED with per-fact context vs 0.14814814814814814 | unit (consumer fed a real producer record) | same | ❌ |
| D-11..D-13 | `main()` end to end with the pin monkeypatched: `require_launch` called before `append("start")`; the end names `results/phase37_r1b.json`; the record carries `provenance.run`; `run_erasure_arm` gets `record_path` under `results/phase37_*` | unit (tmp ledger/heartbeat) | same | ❌ |
| plist | mirrors the phase36 agent (caffeinate -dims, KeepAlive/RunAtLoad false, logs, env) | unit | same | ❌ |
| real tree | `tests/test_phase36_ledger.py::test_every_tracked_v6_mps_record_has_a_launch_line` stays green after the record commits | existing | `pytest tests/test_phase36_ledger.py` | ✅ |
| R1b on MPS | the replica itself | manual (LaunchAgent, about 1.26 h) | Rafael `launchctl kickstart`; `python scripts/phase36_ledger.py report` | manual-only: MPS, 1.26 h, needs approved |

### Sampling Rate
- **Per task commit:** the quick run (new files) + `tests/test_phase35_prereg.py`.
- **Per wave merge:** quick + targeted regression (about 100 s).
- **After each record commit and at the phase gate:** the full suite, uncapped in background.

### Wave 0 Gaps
- [ ] `tests/test_phase37_prereg.py`: ancestry, entries, fill, census, torch-free, no skips, every function called
- [ ] `tests/test_phase37_routes.py`: A–E tripwires + swaps, pin/gate byte-unchanged, AST gates
- [ ] `tests/test_phase37_r1a.py`: REPRO-01 assertions + write-once
- [ ] `tests/test_phase37_r1b.py`: D-07/D-03/D-04 logic, consumer fed the committed record, ledger wiring, plist
- No framework install needed.

## Security Domain

`security_enforcement` is absent from `.planning/config.json`, so it is treated as enabled. The phase has no network, auth or user input. Its trust boundaries are the committed records, the adapter file and git state.

| ASVS Category | Applies | Standard Control |
|---|---|---|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | `_prove`-style SystemExit on record shape; `phase35_prereg` entry validation; the adapter sha256 checked against the curve's `adapter_in_sha256` before the sweep |
| V6 Cryptography | yes (integrity only) | `hashlib.sha256` over record bytes; never hand-rolled |
| V10 Malicious code / integrity | yes | `load_adapted_model` uses `weights_only=True`; `refuse_if_dirty` before any record; module_sha256 provenance |

| Threat | STRIDE | Mitigation |
|---|---|---|
| A Phase 19 record overwritten by a reproduction | Tampering | never call `report()`/`_cmd_*`; explicit `record_path` under `results/phase37_*`; AST gate; the pin's own clobber refusals |
| A tolerance tuned after seeing the replica | Repudiation | ancestry (prereg before records) + Phase 35 leg (a) |
| A replica adjusted to match | Tampering | write-once, one attempt, NOT_REPLICATED published, records committed only after approved |
| Wrong adapter swept | Spoofing | sha256 equality with the curve's `adapter_in_sha256` before and after the run (the `target_ablate` pattern) |
| A lost MPS run hidden from the budget | Repudiation | ledger start/heartbeat/reconcile `lost` line |

## Sources

### Primary (HIGH confidence, read or run in this session)
- `scripts/phase35_prereg.py` (lines 1-200, 300-520, 840-960, 1120-1215, 1785-1923); `tests/test_phase35_prereg.py` (425-445, 2120-2560)
- `scripts/phase19_erasure.py` (275-324, 1633-1742, 1935-1967, 2443-2560, 2732-2830, 3096-3130, 3540-3700, 3850-3861)
- `scripts/phase19_run.py` (docstring 1-181, 885-1140, 1286-1495, 2771-3036); `scripts/erasure_gate.py` (180-291); `scripts/erasure_kstar_run.py`; `scripts/erasure_kstar_prereg.py:130-150`
- `scripts/phase36_ledger.py`, `scripts/phase36_prereg.py`, `scripts/phase36_budget_prereg.py`, `scripts/phase36_probe.py` (355-440, 1165-1260), `scripts/phase36_budget.py` (175-260, 840-862, 1056-1066)
- `tests/test_phase36_prereg.py`, `tests/test_phase36_ledger.py:700-760`, `tests/test_phase36_budget.py`, `tests/test_phase29_prereg.py:69-117`, `tests/test_phase19_erasure.py` (2100-2200, 3925-3975, 4274-4310), `tests/test_phase19_correction.py:264-320`, `tests/test_erasure_kstar_prereg.py:55-90`
- Records: `results/phase19_arm_erased.json`, `phase19_collateral_curve.json`, `phase19_reference_set_resweep.json`, `phase19_noise_floors.json`, `phase19_target_scores.json`, `phase19_calibration_correction.json`, `erasure_kstar_arm_k0{08,16,32,64}.json`, `erasure_kstar_summary.json`, `phase36_budget.json`, `ledger/v6_mps_ledger.jsonl`; `results/phase19_reference_set_correction.md`; `README.md:386-420`
- `.planning/phases/36-mps-cost-probes-and-budget-commitment/36-CONTEXT.md` (D-11..D-16), `36-07-PLAN.md`; `.planning/ROADMAP.md` (1450-1475, 1599-1620, 1712-1722); `.planning/REQUIREMENTS.md` (700-746)
- Scratch scripts run read-only (R1a arithmetic, defect C/E measurement, floor re-derivation, fill dry call, `require_launch("R1b")`), tree verified unchanged

### Secondary / Tertiary
- None. No web sources were needed: this is a repo-internal phase.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH. Repo modules only, all read and exercised.
- Architecture: HIGH. Every reused function was called on the real records; the ledger gate was called read-only.
- Pitfalls: HIGH. Each cites the measured line or test.

**Research date:** 2026-10-03
**Valid until:** the first commit touching `scripts/phase35_prereg.py`, `scripts/phase36_ledger.py`, `scripts/phase19_run.py` or any record listed above (stable otherwise; about 30 days).
