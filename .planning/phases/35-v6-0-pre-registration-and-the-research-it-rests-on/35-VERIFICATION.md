---
phase: 35-v6-0-pre-registration-and-the-research-it-rests-on
verified: 2026-10-01T00:00:00Z
status: passed
score: 5/5 roadmap success criteria verified (plus 41/41 plan must-haves, 9 of them judged against the rulings that superseded them)
overrides_applied: 0
---

# Phase 35: v6.0 Pre-Registration and the Research It Rests On — Verification Report

**Phase goal:** Every v6.0 front's rule, record paths and thresholds are committed and
ancestry-guarded before any v6.0 result record exists. Every threshold carries its written
derivation and its source. No E3/E4 threshold is locked without the research it rests on.

**Verified at:** HEAD `f7d258a`. The last commit touching code is `bbcec95`.
`git diff --name-only bbcec95 HEAD` lists only `35-05-SUMMARY.md` and `35-VALIDATION.md`.

**Status:** passed

**Re-verification:** No. This is the initial verification; no earlier `35-VERIFICATION.md` exists.

## Goal Achievement

### Observable Truths (ROADMAP Phase 35 SC1..SC5)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1 / PREREG-05: one ancestry-guarded v6.0 prereg holds the core, a registry of deferred slots, closed pins imported by reference, and one `seed_list`. A test reddens on an undeclared slot, on a fill outside the owner, on a different rule, and on a violation of the per-fill-file ordering (hand-note 7275ba1). | ✓ VERIFIED | See "SC1 evidence" below. |
| 2 | SC2 / PREREG-06: every threshold has a written derivation committed before measurement. Preferences are labelled. | ✓ VERIFIED | See "SC2 evidence" below. |
| 3 | SC3 / PREREG-07: no entry carries a proposer field. The phrase "selected by THE USER, verbatim" is absent. | ✓ VERIFIED | See "SC3 evidence" below. |
| 4 | SC4 / PREREG-08: every rule module has a CPU test. MPS-only tests are skipped in CI with an attributed count. | ✓ VERIFIED | See "SC4 evidence" below. |
| 5 | SC5 / PREREG-09: research on (a) the Steinke–Nasr–Jagielski one-run bound and (b) E3 selection accounting is on record before any E3/E4 threshold. | ✓ VERIFIED | See "SC5 evidence" below. |

**Score:** 5/5

#### SC1 evidence

The module is `scripts/phase35_prereg.py`, 1923 lines.

**Ancestry guard.** `test_phase35_prereg_is_frozen_before_every_v6_result` calls
`_assert_frozen_before`, which runs `merge-base --is-ancestor` on every prereg commit against the
first add of every tracked `results/phase36_*` … `results/phase45_*` file. It fails on a shallow
clone. I watched it go RED in a scratch clone: commit `results/phase36_probe_x.json`, then edit
the prereg, and the test raises `CalledProcessError` on `merge-base --is-ancestor`.

**Record paths.** `V6_RESULT_PATHS` is a single tuple. `ARTIFACT_PATHSPECS` is derived from it
and is asserted to equal `results/phase36_*` … `results/phase45_*`.

**Core values, as I ran them:**
- `seed_list()` returns `(1337, 2024, 1338, 2025, 1339)` by identity.
- `e1_targets()` returns `('pet_name', 'cat_name', 'street', 'sibling_name')`.
- `audit02_cut()` returns 3.7965357228934966. `e4_runs(cut)` is False and `e4_runs(cut+1e-9)` is True, so the comparison is strict.
- `e1_condition_b_margin()` returns 0.2962962962962963.
- `r1a_rederive()` gives k = 78 and destroyed = 77.6370113463966.

**Registry.** `SLOTS` holds 17 slots with owners in 36..43. My scratch-clone experiments:
- `fill("e2_S")` from `scripts/phase36_wrong_prereg.py` is RED: "outside its owner".
- `fill("e7_x")` is RED: "undeclared slot".
- `E2_S = 3` in `scripts/phase40_x_prereg.py` is RED: "different rule".
- A `phase38` minting record committed before a `phase38` fill file for `e5_minting_rule` is RED on leg (a).
- `results/phase36_budget.json` tracked while `v6_budget_and_stop_line` is unfilled is RED on leg (c).

#### SC2 evidence

- There are 22 `ENTRIES`. `_prove_entry` runs at import and requires a non-empty `derivation` and `source`.
- `F_Y` (0.7) and `F_C` (0.5) are `preference`. So are `delta`, `seed_list`, `e3_sigmas`, `mps_ceiling_hours`, `e5_max_set_size` and `e4_beta`.
- A measured slot is refused unless its four-field derivation names every input it consumed (`_consume_inputs`).
- "Never changes after" is enforced by the ancestry guard from SC1.

#### SC3 evidence

- No entry has a `proposer` or `adopted_by` key; checked at runtime, and the result printed False.
- `_prove_entry` refuses both keys and the forbidden phrase.
- The test `-k no_proposer` passes.
- In the module, the phrase appears only in the `FORBIDDEN_PHRASE` constant and the docstring that describes it. It does not appear in the research note.

#### SC4 evidence

- `test_every_rule_has_a_cpu_test` is an AST census: every module-level def of the prereg is called by a test, and `_rule_*` functions count through `fill()`. I watched it go RED on a planted untested def.
- `test_no_skips_in_this_file` asserts 0 skip markers.
- The final suite at `bbcec95` was 3487 passed / 4 skipped / 0 failed (`phase35_suite2.log`, `EXIT=0`). The 4 skips equal the last green run's count.
- `tests/test_phase25_venue.py` (the attributed skip pin) has 0 commits since 4d49ba5.

#### SC5 evidence

- `.planning/research/V6-PREREG-09.md` was first added at `8fba327` (18:25:25). The first prereg commit is `ce659f4` (18:28:02).
- `test_research_note_precedes_every_prereg_commit` passes, and its planted-repo RED passes too.
- My run of the port: `eps_lower_one_run(1000,100,75,1e-4,0.05)` = 0.6729846633970737 against a published 0.673, and `(100000,1510,1439,1e-5,0.05)` = 2.6758510060608387 against 2.675. `one_run_reproduction_holds()` is True.
- `_rule_e4_parameters` refuses unless the reproduction holds.
- E3 uses basic composition by reference: `SELECTION_ACCOUNTED` is False, and `curve_total([1.5,2.25,0.25])` = `(4.0, 3.0000000000000004e-05)`.
- The note records why the Papernot–Steinke hypotheses 1, 2 and 4 fail for E3.

### Plan must-haves superseded by ruling (judged against the ruling, not counted as gaps)

| Plan-time must-have | Superseding ruling | Verified against the ruling |
|---|---|---|
| 35-03: `fill('e2_S', s=6, ...)` raises the D-06 SystemExit before any input is read; S is caller-typed in `[e2_min_seeds, len(seed_list())]` | CONTEXT "Addendum to D-15" (WR-04, Rafael: "decisão (a)… S é escolhido na Fase 36… e a Fase 40 só lê") | `_rule_e2_S` reads `e2_seed_count` from `results/phase36_budget.json` through `_budget_record`, which re-applies `_prove_budget`. A typed S that differs is refused. I ran `_prove_budget(fronts, 50, 6)` and it raises "S > len(seed_list()): STOP and ask Rafael (D-06); the seed list is never extended". S = 1 is refused by `e2_min_seeds`. |
| 35-03: the e2_S row "Owner Phase 40" chooses S | Same addendum | The owner is still 40 (`SLOTS['e2_S']['owner_phase'] == 40`) and the slot is filled as a read. The choice moved to owner 36 (`v6_budget_and_stop_line`). |
| 35-03 (and the D-02 row): `e1_condition_a_floors` takes written floor entries | Round 1 (Rafael): "O piso não é digitado. A regra calcula cada piso com phase19_erasure.lock_erasure_floor…" | `_rule_e1_condition_a_floors` computes `lock_erasure_floor(rate)` and `floor_branch(rate)` from the cell's calibration draws through `per_fact_rows` (the defect-B route). A supplied floor that differs is refused (`:1404-1410`). `_calibration_rate` is never referenced (test `never_reference_the_defect_b_rate`). |
| Calibration keyed per target / per ordering | Round 2: "Calibração por (ordem, semente), não por alvo" | `cal_key = (ordering[, seed])`. A record carrying `target` is refused, and so is a duplicate (ordering, seed). One record serves all four targets (`:1335-1363`). |
| Calibration corpus implicit | Round 2 item 1: the corpus is a declared input | `SLOTS['e1_condition_a_floors']['input_records']` includes `results/phase19_calibration_corpus.json`. A record's `corpus` must be a consumed input, and an unnamed consumed corpus is refused. |
| 35-03: E4 beta free (any beta in (0,1)) | Round 1 item 2: `e4_beta = 0.05`, preference; other beta refused | `ENTRIES['e4_beta']` is 0.05, kind `preference`, with its source citing `erasure_gate.py:90` and both pins. `_rule_e4_parameters` refuses `beta != ENTRIES['e4_beta']`. |
| 35-03: `e1_checkpoint_grid` with no defined outcome when nothing confirms | Round 1 item 3: `NOT_REACHED` | The `NOT_REACHED` constant is proved distinct from every verdict string at import. `e1_stop` returns `{"stop": NOT_REACHED, "judged": False}`, covered by test `e1_stop_not_reached_is_neither_pass_nor_fail`. |
| 35-03: the (c) band takes caller-typed `control_gap` / `gap_noise_floor` | Review CR-01 ("Opção 2") | Both values are now read from `results/phase41_band_inputs_*.json` and `results/phase40_noise_floor.json`. Supplied values that differ are refused (`:1700-1770`). |
| 35-03 ENTRIES count 21 / 35-05 "full suite at 7275ba1" | Round 1 (`e4_beta`), then the code-review fixes | There are 22 entries. The gate was re-run on `bbcec95`: 3487/4/0 (log, `EXIT=0`). VALIDATION was re-signed on `bbcec95`. |

The remaining plan must-haves from 35-01 to 35-05 hold as written. The quick suite (below) covers
them through its selectors. The ROADMAP hand-note `7275ba1` adds 7 lines and changes none. I ran
`phase28_report.py check` and `phase34_report.py check`, and both exit 0.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `.planning/research/V6-PREREG-09.md` | PREREG-09 note with verified citations | ✓ VERIFIED | 238 lines. Cites 2305.08846v1 (Alg. 1 p. 3, Thm 5.2 p. 14, Cor 5.4 pp. 15-16, Lemma 4.7, App. D pp. 45-46, §7 p. 28 with the verbatim PDF lines) and 2110.03620v2 (§3.3, Thm 2, Cor 3-4, Thm 6). 0 occurrences of "não verificado". |
| `scripts/phase35_prereg.py` | Core, entries, 17 slots, `fill`, one-run port | ✓ VERIFIED | Substantive. It is torch-free at import (subprocess probe test), and every rule refuses through `_prove`. |
| `tests/test_phase35_prereg.py` | CPU guard suite | ✓ VERIFIED | 2839 lines. 88 tests collected, 0 skip markers. |
| `.planning/ROADMAP.md` SC1 hand-note | Per-fill-file reading, dated, approved | ✓ VERIFIED | Present under Phase 35 SC1 (commit `7275ba1`, +7 lines). |
| `35-VALIDATION.md` | Signed off | ✓ VERIFIED | `status: complete`, `nyquist_compliant: true`, `wave_0_complete: true`. Re-signed on `bbcec95`. |

### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| `phase35_prereg.CURVE_TOTAL` | `phase25_epsilon.curve_total` | attribute binding (`:199`), `is` test | ✓ WIRED |
| `seed_list()` | `phase23_run.SEED_LADDER` | lazy import, identity; AST check of the tuple at first add `5303819` | ✓ WIRED |
| `audit02_cut()` | `results/phase26_canary.json` | `phase26_canary.RECORD` read at call | ✓ WIRED (returns 3.7965357228934966) |
| `fill` | `SLOTS[slot]["rule"]` | single dispatch; `_dispatch_failures` test | ✓ WIRED |
| `_rule_e4_parameters` | `one_run_reproduction_holds()` | first statement refusal | ✓ WIRED |
| `_rule_e3_recall_threshold` | `phase29_prereg.control_is_unlearnable` / `REFUSED` | per-recipe control | ✓ WIRED |
| `p22_onset_sigma` | `accountant.delta_quadrature/delta_closed/epsilon_for` | `_p22_breached` | ✓ WIRED (my run gives 0.07890181429684162; P22 printed 0.078902) |
| `_v4_control` | `results/phase25_point_dp_n8_sigma0p000000.json` at tag v5.0 | sha256 of working-tree bytes vs `git show v5.0:` | ✓ WIRED |
| tests | `ARTIFACT_PATHSPECS` | `git ls-files` → `_assert_frozen_before` | ✓ WIRED (natural RED observed) |

### Data-Flow Trace (Level 4)

Not applicable: the phase renders no UI. The rules' data sources are committed records, and I read
them live:

- `phase26_canary.json` gives the cut.
- `phase19_noise_floors.json` gives the margin.
- `phase19_arm_erased.json` gives k and destroyed.
- `TARGET_RANKING` gives the targets.

No hardcoded value stands in for any of them. The AST census `no_seed_target_or_record_value_is_retyped`
passes.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Quick suite | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase35_prereg.py tests/test_phase29_prereg.py tests/test_phase25_prereg.py` | 188 passed in 38.05s | ✓ PASS |
| Phase 35 test count | `pytest --co tests/test_phase35_prereg.py` | 88 collected | ✓ PASS |
| One-run pins / reproduction gate | Python spot-check | 0.67298…, 2.67585…; holds True | ✓ PASS |
| D-06 STOP, COST-02 HALT | `_prove_budget(fronts, 50, 6)`, `(…, 95, 3)` | both SystemExit with the D-06 / COST-02 messages | ✓ PASS |
| Ancestry guard natural RED | Scratch clone: record commit, then prereg edit | `frozen_before` FAILS | ✓ PASS |
| Census RED ×3, ordering (a) and (c) RED | Scratch clone, planted owner files and records | each test FAILS with the expected message | ✓ PASS |
| No v6.0 record exists | `git ls-files 'results/phase3[5-9]_*' 'results/phase4[0-5]_*'`; `find results …` | empty | ✓ PASS |
| Frozen planning inputs | `phase28_report.py check`, `phase34_report.py check` | exit 0, exit 0 | ✓ PASS |
| Clean tree after checks | `git status --short` | only the pre-existing ` D .claude/scheduled_tasks.lock` | ✓ PASS |

All experiments ran in
`/private/tmp/claude-501/-Users-juliorcoelho-PersonaCore/f3aad491-2597-4043-b6cf-4351c5705769/scratchpad/verify35/repo`.
Nothing was written under the real `scripts/`, `tests/` or `results/`.

### Probe Execution

Step 7c: no `scripts/*/tests/probe-*.sh` is declared by the phase, and this is not a
migration/tooling phase. SKIPPED.

### Requirements Coverage

| Requirement | Source Plans | Status | Evidence |
|-------------|--------------|--------|----------|
| PREREG-05 | 35-02, 35-03, 35-04, 35-05 | ✓ SATISFIED | SC1 evidence above. |
| PREREG-06 | 35-01, 35-02, 35-03, 35-05 | ✓ SATISFIED | SC2 evidence above. |
| PREREG-07 | 35-01, 35-02, 35-05 | ✓ SATISFIED | SC3 evidence above. |
| PREREG-08 | 35-01, 35-04, 35-05 | ✓ SATISFIED | SC4 evidence above. |
| PREREG-09 | 35-01, 35-05 | ✓ SATISFIED | SC5 evidence above. |

REQUIREMENTS.md maps exactly PREREG-05..09 to Phase 35 (lines 802-806). There are no orphaned
IDs. All five are still `[ ]` / Pending; the orchestrator ticks them, not the verifier.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| prereg, test, note | — | TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER | — | none found (grep rc = 1) |
| `scripts/phase35_prereg.py` | 1579-1580 | `taught_recall` / `heldout_recall` sub-fields not shape-guarded (35-REVIEW-FIX N-02) | ℹ️ Info | Fails closed with a raw TypeError/KeyError instead of `_prove`. No value or verdict changes. |
| `scripts/phase35_prereg.py` | census | KL-01..KL-09 (35-REVIEW-FIX): bypasses through private names, forged grids, module-as-argument, iterating the registry, `__globals__` | ℹ️ Info | Accepted under Rafael's recorded stopping rule. Each needs a deliberate bypass of the public API. |

### Human Verification Required

None outstanding. Rafael reviewed every entry, every slot and the 19 planner readings at the 35-05
blocking checkpoint; his verbatim rulings are in `35-05-SUMMARY.md`. He also ruled on WR-04 and set
the review stopping rule.

### Informational notes (not gaps)

1. **PIN 2 is close to the tolerance.** PIN 2's distance is 8.5e-4, against a tolerance of 1e-3.
   The tolerance's derivation (one unit in the last printed digit, because the paper truncates
   2.67585 to 2.675) is written and committed. The port also reproduces four unpinned printed
   values within about 1e-3 (note table, rows p. 45 / p. 46 / Fig. 10), which corroborates the
   transcription.
2. **No recorded confirmation of the PDF lines.** Rafael asked for the verbatim PDF lines "para eu
   conferir no PDF". They are in the note (f13ad62), and his later replies raise no objection
   ("Aprovado" on round 3). No explicit "conferi" is on record.
3. **PREREG-08 for later rule modules.** "Every rule module has a CPU test" covers the only v6.0
   rule module that exists, `phase35_prereg`. Phases 36-43 add their own fill modules. No generic
   census forces those to have tests; it falls to each owner phase.

### Gaps Summary

None. The goal holds on the code at `f7d258a`:

- The core, the 17-slot registry and the PREREG-09 research exist and are wired.
- They are guarded against later v6.0 records by a git-ancestry test, which I watched go RED.
- Every threshold is a four-field entry with no proposer field.
- E4 cannot compute its ceiling without the reproduced one-run bound.
- E3 is pinned to basic composition with `SELECTION_ACCOUNTED` False.
- No v6.0 record exists, so the guard holds honestly.

---

_Verified: 2026-10-01_
_Verifier: Claude (gsd-verifier)_
