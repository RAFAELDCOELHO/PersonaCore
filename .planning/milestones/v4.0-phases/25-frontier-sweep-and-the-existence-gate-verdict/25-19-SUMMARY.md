---
phase: 25
plan: 19
subsystem: frontier-artifact
tags: [D-28, D-29, D-30, D-31, D-33, D-36, D-45, D-46, D-49, D-50, FRONT-02, FRONT-03, FRONT-04, write-once, epsilon]
requires:
  - results/phase25_point_*.json (44)
  - results/phase25_recall.json
  - results/phase25_promotion.json
  - results/phase23_never_taught.json
  - results/phase21_multiplicity.json
  - scripts/mitigation_gate.py (frozen), scripts/mitigation_budget.py (frozen)
provides:
  - results/phase25_frontier.json
  - results/phase25_frontier_dp.png
  - results/phase25_frontier_adversarial.png
  - scripts/phase25_record.py (assembly section)
  - tests/test_phase25_frontier.py
affects: [25-20, phase-close, Phase 26, Phase 28]
tech-stack:
  added: []
  patterns:
    - "an aggregate is asserted to re-derive exactly from the rows beside it at the single write, and the same function is re-run over the committed bytes and over a perturbed copy"
    - "a record carried verbatim keeps its own `governs`; the assembly's note takes a distinct name rather than overwriting"
decisions:
  - "The assembly needed TWO commits, not one: the emitter must be committed before the write because refuse_if_dirty watches scripts/ — the natural order the plan's own guard imposes."
  - "Area-7 fields are carried where the records put them (`condition_c.*`), never hoisted to the point's top level; the plan's AC8/AC9 name top-level fields and are re-run against the real names."
  - "Recall on 42 points is fed from results/phase25_recall.json pinned to adapter_sha256, with the two inline controls asserted equal to that artifact's copies; every point says which source it came from."
  - "FRONT-02 and FRONT-03 ticked here (this plan publishes them); FRONT-01 and FRONT-04 stay with the close plan as 25-18 recorded."
metrics:
  duration: "~4 h on CPU (assembly 1.27 s; full suite 21:24)"
  completed: 2026-09-09
---

# Phase 25 Plan 19: The Frontier Artifact, Its Ordering Proof and Its Figures Summary

**`results/phase25_frontier.json` exists, was written once against a clean tree, and every bound
in it re-derives from its own rows.** 44 points inline (22,311,714 bytes), `point_keys` equal to
`ORDERED_POINT_KEYS()` under hard equality proved at the single write, the verdicts carried verbatim
(32 FAIL, 6 INCONCLUSIVE, 6 REFUSED, 0 PASS), the curve total 2387.299119573244 by basic composition
over the 30 published noised DP points, both multiplicities named with the frozen pin's
`RECORDED, NOT RESOLVED` status intact, and `held_out_generalization` (A2, 756/4576) asserted to
re-derive from the per-point counts beside it. Figures were drawn by the unmodified plotter. Suite:
**`2717 passed, 4 skipped, 83 warnings in 1284.30s (0:21:24)`**, exit 0.

## Task 1 — the write-once assembly (`578a1ac` emitter, `4030d0e` artifact)

**Two commits, by the guard's own order.** `_write` runs `refuse_existing_artifacts` then
`refuse_if_dirty(pathspec=(scripts, src, results, artifacts, :(exclude)results/phase25_frontier.json))`
then the bytes, so the emitter change had to be committed (`578a1ac`) before the write could run;
the artifact's `provenance.git_sha` is `578a1ac9a59525e5b7f68d33bd339c0113f1491e`, the commit that
contains the code that produced it. `git status --porcelain scripts/ src/ results/ artifacts/` was
empty at the write. The write took 1.27 s on CPU with no torch in `sys.modules`.

**Ordering proof, at the write.** `load_point_records` finds the records by the pre-registered
glob, keys each by the `point_key` INSIDE the file (refusing a duplicate key or a file filed under a
name its own key does not produce), and asserts set equality against the pin with both sets in the
message — `44 records found against 44 pinned keys; missing []; extra []` — then builds `points` in
the pin's order, so the file's own insertion order is the pin's. Acceptance:
`tuple(b['point_keys'])==tuple(r.ORDERED_POINT_KEYS())` → `ordered hard equality holds`.

**What was assembled, and from where.**

| block | source | assertion at the write |
|---|---|---|
| `points[k]` (44) | the record whole, incl. 416 gated + 448 reported `per_question` rows, `per_family_counts` with A2, `refusal`, `adapter_sha256`, `canary_population`, `accounting: null` on the 12 adversarial points | key set == pin; `accounting is None` on every `adv_*` |
| `points[k].taught_recall` etc. (6 fields) | 2 controls inline; 42 from `results/phase25_recall.json` (D-25-18-RECALL) | `recall.adapter_sha256 == record.adapter_sha256` on all 44; the controls' inline copies `==` the artifact's; `recall_provenance.source` names which (`{'point_record': 2, 'results/phase25_recall.json (D-25-18-RECALL)': 42}`) |
| `points[k].verdict`, `.promotion` | `results/phase25_promotion.json::point_verdicts / promotion`, verbatim | `verdict.leg == arm`; no key collision |
| `verdicts` | the promotion record's whole top level verbatim (its own `governs` kept; the assembly's note is `assembly_governs`) + `tallies`, `tallies_by_leg`, `refused`, `capacity_branches` | `capacity_branch in mitigation_gate.CAPACITY_BRANCHES`; `refused == promotion.refused_points`; tallies sum to 44 |
| `held_out_generalization` | computed FROM `points[k].per_family_counts["A2"]` | `prove_held_out_generalization` — successes/questions/draws, total, per arm, per point |
| `epsilon_report` | `phase25_epsilon.curve_total` over the noised DP points; every rendering via `report_epsilon` | each summand `== point_epsilon_for_sigma(sigma, steps, delta)`; every summand a `CURVE_K` reading; 2 controls at sigma 0.0 excluded by name |
| `never_taught_floor` | `results/phase23_never_taught.json::pooled` verbatim + record sha256 | — |
| `retention_leg_binds_at_anchor`, `retention_floor_disclosure`, `dialogue_floor_recipe_mismatch`, `dialogue_floor_sensitivity` | `phase25_condition_c` constants | every record's copy `==` the module's |
| `mechanism_pin_disclosure` | D-25-17-ADV-PIN, lot re-derived per arm from each record's `training.train_config` | `records_per_lot == lot` on all 44 |
| `provenance` | git sha, python 3.11.15, torch 2.7.1 (read from distribution metadata, torch never imported), four module sha256s, sha256 of every input record, `CANARY_RESERVATIONS`, `PUBLICATION_OBLIGATION`, `GIT_SURFACE_EXCEPTION`, the pathspec, the re-run route | — |

**D-36 — `held_out_generalization`, from the artifact:** family `A2` (read through
`phase25_gate05._committed_literal("phase24_adversarial", "HELD_OUT_FAMILY")`, never spelled),
tier `core_held_out`, **756 successes / 4576 questions / 73,216 draws over 44 points**; by arm:
dp_n8 **96/1664**, dp_n64 **15/1664**, adv_n8 **557/624**, adv_n64 **88/624**. Acceptance
`tot==h['successes']` → `aggregate re-derives from its own rows`. The DP A2 successes are all at the
two sigma=0 controls (every noised DP point is 0/416 on the gated tier); the adversarial arm, which
never trained on A2, leaks it at 557 of 624 at n=8.

**The dual ε report (D-28/D-29/D-30), from the artifact:**

- `curve_total_epsilon = 2387.299119573244`, **30 summands** (`summand_keys` = the 15 noised points
  of `dp_n8` then the 15 of `dp_n64`; the two ladders are identical, so the n=64 summands equal the
  n=8 ones: 519.6981942303134 at σ=0.5 down to 0.6339783761989397 at σ=80), `k = 30`,
  **`total_delta = 0.00030000000000000003`** (= `30 * 1e-05` in the same float arithmetic the
  acceptance uses; `e['total_delta']==len(e['summands'])*1e-05` → exits 0), `delta_source:
  mitigation_unit.DELTA`, `composition: BASIC (sequential): curve_total_epsilon = math.fsum(summands)`.
- `selection_accounted: false` with `SELECTION_ACCOUNTED_REASON`; `total_crosses_both_legs: true`
  with `TOTAL_CROSSES_BOTH_LEGS` and `legs_crossed: {dp_n8: 15, dp_n64: 15}`.
- `control_points_excluded: ["dp_n8_sigma0p000000", "dp_n64_sigma0p000000"]`,
  `no_joint_bound_over_all_published_artifacts: true`, `control_has_no_epsilon` verbatim.
- `dual_granularity` (rendered at the curve total) names `262.9437465865647` (the frozen pin's
  overlap rule) and `207.0180229382851` (first-token-owns-draw, the artifact rule) with the record's
  status `'RECORDED, NOT RESOLVED — the pin is frozen and is not edited'`; the structured
  `multiplicities` block carries both figures, both rule names, the reconciliation,
  `epsilon_computed: false` and the record's sha256. Acceptance AC4 printed `2387.299119573244`.
- `rendered`: 32 strings, one per DP point (controls with `point_epsilon = None`), each produced by
  `report_epsilon(point_epsilon=, curve_total_epsilon=, selection_accounted=)` and asserted equal to a
  live call in the tests. No bare ε.

**The verdicts (FRONT-04), from the artifact:** `tallies = {PASS: 0, FAIL: 32, INCONCLUSIVE: 6,
REFUSED: 6}`; per leg dp_n8 16 FAIL, dp_n64 16 FAIL, adv_n8 6 INCONCLUSIVE, adv_n64 6 REFUSED.
`capacity_branch = 'null-at-both-capacities'`, a member of `CAPACITY_BRANCHES = ('not-comparable',
'capacity-recovers', 'capacity-destroys', 'recovery-at-both-capacities', 'null-at-both-capacities')`.
Existentials verbatim: **`NO CLEARING POINT IN THE 'dp' ARM: 0 of 32 point(s) examined returned
PASS. ...`** and **`NO CLEARING POINT IN THE 'adversarial' ARM: 0 of 6 point(s) examined returned
PASS. ...`** with `arm_existential_counts.adversarial = {points_examined: 6, points_in_arm: 12}`.
The six refusals are inline on `adv_n64_ratio{0,0p25,0p5,1,1p5,1p909091}`: `verdict: null`,
`early_return_reason: "REFUSED by the sanctioned route before the pin was reached"`, `reasons` =
`["[phase20_gate_coverage] the recall floors came out Y_taught=0.0006944444444444444,
Y_heldout=0.0; both must lie in (0.0, 1.0]. ..."]`, and again under `verdicts.refused[k]` with
`route: phase20_gate_coverage.corrected_point_verdict` — never a null that reads as missing.
`adversarial_capacity_rule_absent`, `amended_criterion` and `adversarial_no_replay` (§12.5c) are in
`verdicts`; every adversarial point also carries `recipe_disclosure` naming the no-replay recipe.

**Area 7 (D-45/D-46/D-49/D-50).** All eleven `phase25_condition_c.CONDITION_C_FIELDS` plus
`zero_extraction_has_nll` (a plain `bool`, `True` on all 44) on every point under `condition_c`;
`retention_cap(retention_noise_floor=counterfactual_retention_floor) == counterfactual_retention_cap`
exactly on all 44; `retention_leg_binds_at_anchor` published top-level with borrowed headroom
**−0.1907598923364855** and governing headroom **−0.3112566543480071** (caps 4.029 / 3.9085032379884783,
floors 0.06893 / 0.008681618994239138, admit factors 2.383721836185154 / 18.926187186661135).

**D-25-17-ADV-PIN, disclosed where the pin fields are reported.** `mechanism_pin_disclosure`
names `composed_lot_sizes` and `records_per_lot` as pinned := live on `adv_n8`/`adv_n64` and
re-derives the lot from each record's `train_config`. A first rule (`batch_size x grad_accum` on all
arms) went RED on `dp_n8_sigma0p000000` (`8 != 64`): on the DP arm the lot is the fact-aligned
capacity — `grad_accum_steps = n_facts` micro-steps per optimizer step (D-27) — so the rule is per
arm (`LOT_RULE_BY_ARM`), and the adversarial lot is 8 at BOTH capacities, as 25-17 measured.

**The plan's acceptance commands, quoted where the schema differs (orchestrator fact 6).**
AC8 as written — `need <= set(p)` over `CONDITION_C_FIELDS` at the point's top level — fails with
`AssertionError: (['control_gap', 'counterfactual_retention_cap', ... 'retention_total_tokens'],
['dp_n8_sigma0p000000', ...])` because the records nest the group under `condition_c` (the schema
`build_point_record` committed in 25-08 and the driver wrote 44 times). The same check against the
real names prints `12 Area-7 fields present on all 44 points (condition_c.* +
zero_extraction_has_nll), the flag a plain bool everywhere`. AC9 as written raises
`KeyError: 'counterfactual_retention_floor'`; against `p['condition_c'][...]` it prints `D-50
re-derives on all 44; D-49 pre-registration published inside the artifact -0.1907598923364855
-0.3112566543480071`. The group is not hoisted: a second copy at the top level would be a second
statement free to drift from the first. Every other acceptance command exits 0 as written
(AC1 `22311714 44`, AC5 `30`, AC6/AC7 as quoted, AC10 below, AC11 `FROZEN-CLEAN`).

**A second assembly, watched refused (AC10, exit 1):**

```
[phase25_record] REFUSING a second assembly. [teach_persona] /Users/juliorcoelho/PersonaCore/results/phase25_frontier.json already exists — this arm is recorded evidence. Delete /Users/juliorcoelho/PersonaCore/results/phase25_frontier.json to re-run.
THE SANCTIONED RE-RUN ROUTE: DELETE results/phase25_frontier.json IN ITS OWN COMMIT, then run `.venv/bin/python scripts/phase25_record.py` again against a clean tree — exactly as scripts/phase24_record.py documents for its record. Never overwrite in place and never write to a temporary path and copy the file into results/: the recorded git_sha must name the tree that produced the bytes.
```

**Size.** 22,311,714 bytes, not the plan's ≈ 9.7 MB: the estimate priced the 864 per-question rows
per point (≈ 180 KB), while each committed record also carries `per_fact` (18.5 KB), `gate05_gated`
+ `gate05_reported` (35 KB) and the refusal column with its denominator provenance (14 KB), ≈ 400–460
KB per record before the verdict entry and the 32 rendered ε sentences (~150 KB). Embedding the
records whole was the plan's instruction; the size is reported, not trimmed.

## Task 2 — the figures (`6af3fa0`)

`.venv/bin/python scripts/plot_phase25.py` (no arguments; the path from the module's constant) exits 0:
`results/phase25_frontier_dp.png` **110,047 bytes**, `results/phase25_frontier_adversarial.png`
**161,979 bytes**. `git diff --exit-code -- scripts/plot_phase25.py` → clean (run, not edited).
`tests/test_phase25_plots.py` with the real artifact present: **`12 passed in 1.95s`**. Fresh
interpreter probe: `no torch in a fresh interpreter`.

Annotated values, each beside the JSON path it was read from:

| annotation | value on the figure | JSON path |
|---|---|---|
| never-taught floor | `0/416 on core_held_out` | `never_taught_floor.nontarget_successes` / `.nontarget_questions` / `.tier` |
| pool ceiling (adversarial axis terminus) | `1.9090909090909092` | `max(points[adv_*].ratio)`; equals `points[adv_*].axis_terminus.pool_ceiling_ratio`, with `this_point_is_the_ceiling: true` on `adv_n8_ratio1p909091` / `adv_n64_ratio1p909091` |
| σ=0 control lines | 790/1008 (n=8), 87/1008 (n=64) | `points[dp_n8_sigma0p000000].taught_recall.numerator/denominator`, likewise `dp_n64_sigma0p000000` |
| every plotted ε | 519.698 … 0.634 | `points[k].epsilon` (30 noised points; `null` on controls and the adversarial arm) |
| every plotted recall | 0/1008 on all 30 noised DP points; 879…268 / 1008 on adv_n8; 1…0 / 1008 on adv_n64 | `points[k].taught_recall.numerator/denominator` |
| marker legend `k=16 (mitigation_budget.CURVE_K)` | 16 | `points[k].draws_per_question` / `.draws_per_question_source` |
| adversarial caption (D-19/D-23) | "…the absence of a committed capacity rule for this arm is named here rather than left for a reader to trip over." | `points[adv_*].epsilon_omitted_reason` (`ADVERSARIAL_MAKES_NO_FORMAL_CLAIM`), sentence selected by `_sentence_about(reason, "capacity rule")` |

**The capacity branch and the arm existentials are NOT drawn.** The plan's Task 2 (b) and its
acceptance presume the figures annotate them; the committed plotter (25-09) has no such clause, and
this plan forbids editing it. They reach a reader from `verdicts.capacity_branch` and
`verdicts.arm_existentials` in the artifact. Recorded as `D-25-19-PLOT-ANNOTATIONS` in
`deferred-items.md`.

## Task 3 — `tests/test_phase25_frontier.py` (`36cb3f3`)

**`30 passed in 1.24s`** (`-v` last line; `-q`: `30 passed in 1.19s`), **0 skipped**, against the
60 s budget with the 22,311,714-byte artifact loaded once into a module fixture.

**D-36's natural RED, on a copy in `tmp_path`.** The artifact is written to `tmp_path/
phase25_frontier.json`, reloaded, one per-point A2 `successes` (on `dp_n8_sigma0p000000`)
incremented by one, and `prove_held_out_generalization` — the same function that ran at the write —
is called on the copy. Verbatim:

```
[phase25_record] held_out_generalization.successes = 756 does NOT re-derive from the per-point 'A2' rows beside it, which sum to 757 over 44 points. D-36: an aggregate that no longer describes its own data is refused at the write and over the committed bytes; one perturbed per-point count is enough
```

`git status --porcelain results/` was empty afterwards (asserted in the test).

**The counts-never-rates walk found two things the plan's rule would have mis-read.** A substring
match on `rate` flags `verdicts.extraction_ceiling.tolerated` — a COUNT (`0` of `n_questions: 416`)
whose name happens to contain `rated` — the false-RED class RPT-02 closes; the walker matches
`rate`/`rates` as whole `_`-separated tokens. And every verdict entry carries
`sweep_extraction_rates` / `sweep_taught_recalls` as `[0.0, 1.0]`: not readings but
`phase20_gate_coverage.SUPERSEDED_SWEEP_SENTINEL` recorded as the pin received them (D-34), with the
real leg-length COUNT sequences beside them under `whole_curve_inputs`. The test admits exactly that
shape and asserts all 88 values equal the sentinel. With those two, the walk over the whole artifact
returns `[]`.

Other selections: `test_every_epsilon_bearing_reading_carries_its_k_inline` finds exactly 45 dicts
keyed by an `EPSILON_NAMES` member (44 points + the report), all with `draws_per_question = 16` and
its source; `test_no_bare_epsilon_string_bypassed_the_helper` re-renders all 32 strings live and
asserts equality; `test_the_artifact_carries_the_pre_registered_commitments` compares the three
`phase25_prereg` values after a JSON round-trip and re-hashes all 44 input records;
`test_a_second_assembly_is_refused` watches `refuse_second_assembly()` and `main()` both raise
`SystemExit` naming `DELETE results/phase25_frontier.json IN ITS OWN COMMIT`.

## Deviations from Plan

1. **[Rule 3] The emitter is committed before the artifact** (`578a1ac` then `4030d0e`): the
   plan's Task 1 lists both files, but `refuse_if_dirty` over `scripts/` makes the emitter's own
   change a refusal until committed. The natural order, not a workaround.
2. **[Rule 1] `_prove` evaluates its message eagerly**: the duplicate-key guard's message indexed
   `loaded[key]` before the condition was checked and raised `KeyError` on the first record. Fixed
   with an explicit branch; the refusal text unchanged.
3. **[Rule 1] The lot re-derivation is per arm** (see D-25-17-ADV-PIN above); the first draft's
   single rule went RED on the DP control and was corrected from the record's own `train_config`.
4. **[Rule 1] `verdicts` keeps the promotion record's own `governs`**; the assembly's note was
   renamed `assembly_governs` after a collision refusal.
5. **The acceptance commands AC8/AC9 name top-level fields the schema nests** — both quoted above
   with the real-name forms (orchestrator fact 6). No field was hoisted.
6. **Task 2's capacity-branch / existential annotations do not exist in the plotter** — recorded as
   `D-25-19-PLOT-ANNOTATIONS`; the plotter was not edited (the plan forbids it).
7. **The suite line.** The plan's AC expects `0 failed and 1 skipped` against a `1647/1` plan-time
   baseline; the measured line is `2717 passed, 4 skipped` — the same four skips 25-18 recorded
   (three `test_phase25_promotion.py` empty-candidate skips and the CUDA AMP smoke), so
   `tests/test_phase25_venue.py`'s literals (39/4) are unchanged and were not continued. Delta:
   +30 over 25-18's 2687/4 (this file's 30 tests); +1070 / +3 over the plan-time 1647/1.
8. **Requirement ticks:** FRONT-02 and FRONT-03 ticked by hand in REQUIREMENTS.md (this plan
   publishes them); FRONT-01 and FRONT-04 left to the close plan as 25-18 recorded, although this
   plan's frontmatter lists FRONT-04. `roadmap.update-plan-progress 25` wiped the ROADMAP row's note
   and counted 20/22 (the SUMMARY did not exist yet); hand-repaired to 21/22 with the note. STATE.md
   updated by hand (frontmatter `stopped_at`/`last_updated`, Current Position, Session Continuity).

No auth gates. No package installs. `git diff --exit-code` on the five frozen modules,
`scripts/plot_phase25.py` and `pyproject.toml`: clean. `make lint`: `All checks passed!`, 274 files
already formatted.

## Verification

- Every Task 1 acceptance command: quoted above (AC8/AC9 in both forms).
- `.venv/bin/python -m pytest tests/test_phase25_plots.py -q` → `12 passed in 1.95s`.
- `.venv/bin/python -m pytest tests/test_phase25_frontier.py -v` → `30 passed in 1.24s`, 0 skipped.
- Full suite `.venv/bin/python -m pytest tests/ -q -rs` → **`2717 passed, 4 skipped, 83 warnings in 1284.30s (0:21:24)`**, exit 0.
- `make lint` → `All checks passed!`.

## Commits

`578a1ac` feat (assembly in `scripts/phase25_record.py`) · `4030d0e` feat (`results/phase25_frontier.json`) · `6af3fa0` feat (two figures) · `36cb3f3` test (`tests/test_phase25_frontier.py`) · this commit (SUMMARY, deferred-items, STATE/ROADMAP/REQUIREMENTS).

## Self-Check: PASSED

All five created files present (`results/phase25_frontier.json`, both PNGs, `tests/test_phase25_frontier.py`, this SUMMARY); all four task commits (`578a1ac` `4030d0e` `6af3fa0` `36cb3f3`) found in `git log`.
