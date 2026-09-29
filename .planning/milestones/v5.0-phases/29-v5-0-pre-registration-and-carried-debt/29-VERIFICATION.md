---
phase: 29-v5-0-pre-registration-and-carried-debt
verified: 2026-09-24T23:59:00Z
status: passed
score: 26/26 must-haves verified (1 option-1-only truth N/A under the D-15 option-2 ruling); 6/6 review fixes verified (CR-01, WR-01..04, IN-01)
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: 26/26 (plus 2 human decision items)
  previous_commit: 5bf969b
  gaps_closed:
    - "Human item 1 (CR-01 admission hardening): developer ruled 'Fix all now'; fixed in 744165b and verified"
    - "Human item 2 (WR-01..04, IN-01 disposition): fixed in 0f0336f, 9179cd7, 79cd4c6, a37e9a4 and 49a4e9f, all verified; IN-02..04 skipped by the ruling's scope"
  gaps_remaining: []
  regressions: []
---

# Phase 29: v5.0 Pre-Registration and Carried Debt Verification Report

**Phase goal:** Commit the v5.0 point keys, record paths, replay recipe, unlearnable-control refusal and conditional relearning scope rule, and ancestry-guard them, before any v5.0 number exists. Close the four debt items that v5.0 owns.
**Verified:** 2026-09-24 (re-verification after the review-fix pass, HEAD 1328ec0)
**Status:** passed
**Re-verification:** Yes. The previous pass (5bf969b) was `human_needed` with two decision items. The developer ruled "Fix all now". This pass verifies each fix, checks it against CONTEXT D-06..D-14 and the D-15 option-2 ruling, and checks for regressions.

## Re-verification (2026-09-24, after the review-fix pass)

### Scope of the change since 5bf969b

`git diff 5bf969b..HEAD --stat` shows 3 files changed: `scripts/phase29_prereg.py` (+90/-15), `tests/test_phase29_prereg.py` (+163/-3) and `29-REVIEW.md`. No frozen module is touched: `phase27_prereg`, `phase25_promotion`, `mitigation_gate`, `phase20_gate_coverage` and `phase25_record` are absent from the diff, and so is everything under `src/` and `results/`. `git ls-files 'results/phase3*'` returns 0 and `find results -name 'phase3*'` returns 0, so the legal edit window was still open for all 7 commits and the ancestry guard stays honest-green.

### Findings: original probe re-run against HEAD

The probe script (session scratchpad, `reprobe.py`) imports `tests/test_phase29_prereg._v5_frontier/_forge/_RECIPE` and calls the committed module.

| Finding | Original probe | Result at 5bf969b | Result at HEAD | Status |
|---|---|---|---|---|
| CR-01 | unlearnable n64 control (taught 1/1008, held-out 0/648), all 12 FAIL | MOOT | INCONCLUSIVE ("advr_n64_ratio0p000000 reads FAIL but advr_n64's own control … is unlearnable: D-11/D-12 REFUSE the whole leg") | FIXED |
| CR-01 | same control, one n64 PASS | ADMITTED | INCONCLUSIVE | FIXED |
| CR-01 | a PASS whose `control_taught_recall` is 900/1008 (graded against another control) | ADMITTED | INCONCLUSIVE ("… is not advr_n64's own control reading … (WR-05)") | FIXED |
| CR-01 | learnable control, n64 all REFUSED | MOOT | MOOT (unchanged, by the chosen reading; ruled below) | CORRECT |
| WR-01 | `frontier["verdicts"] = ["x"]` | AttributeError raised | INCONCLUSIVE "verdicts is absent or not a dict" | FIXED |
| WR-02 | `recipe={replay_windows:999, n_facts:8, seed:"x", max_steps:-1}` on an n64 key | accepted | SystemExit (seed is not an int) | FIXED |
| WR-02 | n8 recipe (32/8) on an n64 key | accepted | SystemExit "recipe n_facts 8 != leg n64's 64" | FIXED |
| WR-02 | `seed=True`, `max_steps=0` | accepted | SystemExit on each | FIXED |
| WR-02 | the correct n64 recipe (256/64) | — | returns the 6 D-13 fields | CORRECT |
| WR-03 | ADMITTED with a v4.0 key `adv_n64_ratio0p250000` | accepted | SystemExit "not distinct v5.0 keys" | FIXED |
| WR-03 | ADMITTED with `[]`; ADMITTED with a duplicated key; MOOT with a key; a bare string | accepted | SystemExit on each | FIXED |
| WR-04 | no ancestry guard on `phase25_record.py` / `phase20_gate_coverage.py` | absent | `test_call_time_sources_are_frozen_before_every_v5_result` (2 params) passes against the derived `ARTIFACT_PATHSPECS`, with a natural-RED non-vacuity leg: the same helper raises `CalledProcessError` for each source against the v4.0 artifact it post-dates | FIXED |
| IN-01 | mutate `r["v4_adv_n64_reading"]["heldout"]` | pin corrupted, `is` True | `is` False; pin still `(0, 648)` | FIXED |

### CR-01: ruling on the chosen reading

**Ruling: the reading honours D-06, D-11 and D-12. Accepted.**

- **INCONCLUSIVE, not REFUSED, for a record that contradicts its own control.** D-06 says admission "reads stored verdicts" and that "nothing about admission is decided after the v5.0 frontier exists", and it gives INCONCLUSIVE to "counts that do not re-derive". D-07 keeps INCONCLUSIVE "narrow": malformed or non-re-deriving. A FAIL or PASS beside an unlearnable control is a record whose verdicts do not re-derive from its own counts, because under D-11 the route could not have produced them. Relabelling those points as REFUSED would be admission deciding a verdict after the record exists, which D-06 forbids. INCONCLUSIVE also routes Phase 33 to a halt (`relearning_scope` raises on INCONCLUSIVE), which is the fail-closed outcome.
- **A learnable leg may carry REFUSED points.** D-11 says an unlearnable control implies the whole leg is REFUSED. It does not say the converse. The route has refusals that D-11 does not own: `phase20_gate_coverage.corrected_point_verdict` proves `0.0 < ceiling < 1.0` on the extraction ceiling and proves the retention-floor provenance (source lines ~604-640). The v4.0 driver `phase25_promotion.py:295-316` turns any route SystemExit into `verdict=None` + `early_return_reason="REFUSED by the sanctioned route …"`. Requiring INCONCLUSIVE here would turn an honest ceiling refusal into "malformed". A learnable leg that is fully route-REFUSED reads MOOT naming the leg (D-08) or, with the other leg also refused, REFUSED (D-07), which is what those decisions prescribe for a refused leg.
- **D-12 short-circuit records are admissible.** Probe A6 stores six real `refused_record(...)` outputs (with `verdict=None`, `early_return_reason`) as the n64 entries beside an unlearnable n64 control, with n8 all FAIL. It returns MOOT, not a false INCONCLUSIVE. `control_recall_counts` round-trips as lists, so the `carried != readings[leg]` comparison matches.
- **Precedence** is unchanged for (1a)-(1c). (1d) runs after the tally re-derivation and before ADMITTED, so nothing downstream can bypass it. (1d) cannot raise: `readings` is validated by `_is_count_pair` (int, non-bool, `0 <= k <= n`, `n > 0`) before `recall_threshold` and the `h[0]/h[1]` division, and `points[k]["verdict"]` is a dict after (1a).

**Can an unlearnable or foreign control still reach ADMITTED, CANDIDATE-UNREPLICATED or MOOT?** Adversarial frontiers of my own (beyond the 8 cases in `test_admission_reads_only_the_legs_own_control`):

| # | Forged frontier | Result | Ruling |
|---|---|---|---|
| A2 | n8 control taught 0/1008 (unlearnable), all n8 REFUSED; n64 learnable with one PASS | ADMITTED `[advr_n64_ratio1p500000]` | Correct. The admitted point is on the learnable leg. D-08's mixed-leg logic applied to PASS. |
| A3 | a replication-pending INCONCLUSIVE (would-be CANDIDATE) on the unlearnable n64 leg | INCONCLUSIVE | Correct. An unlearnable leg never reaches CANDIDATE. Control: the same point on a learnable leg gives CANDIDATE-UNREPLICATED. |
| A4 | unlearnable n64 leg correctly all REFUSED, but one REFUSED entry carries a learnable `control_taught_recall` (40/1008) | INCONCLUSIVE | Correct. The fields a REFUSED entry carries are checked. |
| A5 | a PASS whose `control_taught_recall` is `True`, `NaN`, `"0.0396"` or `None` | INCONCLUSIVE × 4 | Correct. |
| A7 | a REFUSED entry whose `control_recall_counts` disagree with the readings | INCONCLUSIVE | Correct. |
| A8 | both controls unlearnable, all 12 REFUSED | REFUSED | Correct (D-07). |
| A9 | control unlearnable only on held-out (taught 500/1008, held-out 0/648), with an n8 PASS | INCONCLUSIVE | Correct. Both sides of the route's precondition are enforced. |
| A10 | `control_readings` holds only `dp_n8`/`dp_n64` | INCONCLUSIVE | Correct. A dp reading never sources the threshold. |
| A1 | learnable n8; the n8 control **point** is REFUSED with every `point_*`/`control_*` field stripped; the readings are set to 900/1008 and 500/648 (numbers not tied to any measured point); an n8 point PASS graded consistently against them | ADMITTED | **Residual, not a gap (Info).** When the control point itself is REFUSED and carries no fields, nothing in the record anchors the readings to a measured advr point. This is a special case of the unclosable class: a fully self-consistent forgery (readings, the control point's `point_*_recall` and every point's `control_*_recall` all set to foreign numbers) also admits, because admission is a pure function of the record. Provenance of the readings is owned upstream: Phase 30 ACTRL-01 ("a test that feeds a DP-sourced reading is refused") and Phase 32 AFRONT-03. CR-01's claim is to reject records that contradict their own control, and it does. An honest route REFUSED entry carries its kwargs (the v4.0 driver writes `pin_kwargs_for(...)` on every entry, refused or not), so the stripped shape does not arise from the driver. |

### WR-02: seed and max_steps are only type- and range-checked

**Ruling: acceptable.** D-13 requires the REFUSED record to carry the recipe identity. The values that Phase 29 owns are pinned exactly: `n_facts == n` of the key's leg, and `replay_windows == replay_windows(n)` (the D-04 expression, lazy `teach_persona` import, so the module stays torch-free at import). Seed and max_steps are Phase 30's calibration outputs. ROADMAP line 1224 (Phase 30, ARECIPE-02) refuses "a point whose recipe differs from the calibration's", and CONTEXT D-14 names ARECIPE-02 as the enforcement point. Pinning values now would pre-empt a calibration that has not run, and would force a `_addendum.py` continuation once it does. The type and range proofs (int, non-bool, `seed >= 0`, `max_steps > 0`) are the right Phase-29 share.

### Regression checks

| Check | Command / evidence | Result |
|---|---|---|
| Targeted suite | `.venv/bin/python -m pytest tests/test_phase29_prereg.py tests/test_phase29_debt.py tests/test_phase16_driver.py -q` | **169 passed** in 5.21s (was 142; +27 new cases) |
| Plan 01 AST guards (no literal 4, no grid retype, no gate retype) | `test_ast_replay_literal_guard`, `test_ast_grid_retype_guard`, `test_ast_gate_retype_guard` | PASSED. The added lines contain no grid, F_Y, 4 or count literal (grep over `+` lines: only the docstring's "(4)" list marker). |
| D-09 attribute-reference pins | `test_d09_pins_are_attribute_references`, `test_d09_never_taught_baselines_and_advr_control_source`, `test_recovery_fixture_is_pinned_by_reference` | PASSED |
| Constants by reference (D-05) | `test_constants_are_by_reference` | PASSED |
| Ancestry guard (SC1) | `test_phase29_prereg_is_frozen_before_every_v5_result` plus the new WR-04 guard | PASSED. 0 `results/phase3*` tracked or on disk. |
| No `== 10` in tests | grep over the two test files and the added test lines | none |
| No frozen-module edits | `git diff 5bf969b..HEAD --name-only` | only `29-REVIEW.md`, `scripts/phase29_prereg.py`, `tests/test_phase29_prereg.py` |
| D-14 no retry/alternate surface | `test_no_retry_or_alternate_key_is_exposed` (in the 169) | PASSED. The new surface (`_own_control_mismatch`, `_is_rate`) is private and exposes no key. |
| DEBT-04 accountant census | `test_no_v5_module_uses_the_accountant` (in the 169) | PASSED. `math` is the only new import. |
| Lint | `ruff check` + `ruff format --check` on both files | clean |
| Full suite | not run by this verifier (the orchestrator runs it concurrently, as instructed) | deferred to the orchestrator |

All 4 roadmap success criteria and all 22 applicable plan truths from the prior pass hold on HEAD; the rows below the "Prior verification" heading remain accurate, except that the CR-01/WR-01..04/IN-01 caveats are now closed. The D-15 option-2 ruling is untouched: there is still no promotion field, and `CANDIDATE_UNREPLICATED` is still reached only through the frozen `mitigation_gate.promote_to_full_fidelity` (probe A3b), now additionally behind (1d).

### Anti-patterns (new lines)

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| `scripts/phase29_prereg.py`, `tests/test_phase29_prereg.py` (added lines) | — | TBD/FIXME/XXX/TODO/HACK | none found | — |
| `scripts/phase29_prereg.py` | `_own_control_mismatch` | A REFUSED control point with stripped fields leaves the readings unanchored (probe A1) | Info | The same class as any self-consistent forgery. Provenance is owned by ACTRL-01 / AFRONT-03. |
| `tests/test_phase29_prereg.py` | `_v5_frontier` | REFUSED fixture entries carry the full `control_*_recall` kwargs | Info | Matches the v4.0 driver shape. A6 in this pass covers the D-12 `refused_record` shape. |

IN-02..IN-04 were skipped by the developer's scope ruling. They were Info-level and affect no must-have.

### Human verification

None. Both prior decision items were resolved by the developer ruling and the fixes are verified.

### Gaps summary

No gaps. Every fix produces the correct outcome on the original probe, the CR-01 reading is consistent with D-06/D-07/D-08/D-11/D-12, and no path takes an unlearnable control, or a point graded against a control other than the leg's own stored one, to ADMITTED, CANDIDATE-UNREPLICATED or MOOT. WR-02's type-only check on seed and max_steps is correct scope (ARECIPE-02, Phase 30). No regression: 169 targeted tests pass, the guards hold, no frozen module moved, and 0 v5.0 results exist.

---

## Prior verification (5bf969b)

The initial verification is kept below as history. Its status was `human_needed`, with 26/26 must-haves verified and two developer-decision items (CR-01; WR-01..04/IN-01), both resolved above.

## Phase 29: v5.0 Pre-Registration and Carried Debt Verification Report

**Phase goal:** Commit the v5.0 point keys, record paths, replay recipe, unlearnable-control refusal and conditional relearning scope rule, and ancestry-guard them, before any v5.0 number exists. Close the four debt items that v5.0 owns.
**Verified:** 2026-09-24
**Status:** human_needed. The goal is achieved in code, and every must-have is verified. The review findings are all confirmed as behaviour, but none breaks a must-have. Whether to fix them before the edit window closes is a developer decision.
**Re-verification:** No. This is the initial verification.

### Goal Achievement

#### Roadmap Success Criteria

| # | Success criterion | Status | Evidence |
|---|---|---|---|
| SC1 | A pre-registration module exists and a CPU-only ancestry test proves it precedes every v5.0 results artifact. It has 12 keys over the frozen grid and write-once paths distinct from v4.0, and it imports the gate and `REPLAY_WINDOWS_PER_FACT` rather than copying them. An AST guard catches re-typing. | VERIFIED | The module `scripts/phase29_prereg.py` (587 lines) was first added in f517c58, with its only other edit in e44f045. `test_phase29_prereg_is_frozen_before_every_v5_result` runs over `ARTIFACT_PATHSPECS`, derived from `V5_RESULT_PATHS` as `results/phase30_*`..`phase34_*`. `git ls-files 'results/phase3*'` returns 0 and `find results -name 'phase3*'` returns 0, so the guard is honest-green. `RATIO_GRID`, `F_Y` and `GATE_ROUTE` are bound by reference and checked with `is`. `replay_windows` uses a lazy `teach_persona` import. The AST guards `test_ast_replay_literal_guard`, `_grid_retype_guard` and `_gate_retype_guard` go red on tmp copies. Keys are pinned as first `advr_n8_ratio0p000000` and last `advr_n64_ratio1p909091`. |
| SC2 | The same module states the conditional scope rule and the unlearnable own-control rule as code. | VERIFIED | `SCOPE_RULE` and `relearning_scope` cover ADMITTED, MOOT, REFUSED, CANDIDATE-UNREPLICATED and INCONCLUSIVE (the INCONCLUSIVE case exits with SystemExit). `control_is_unlearnable` is the route's `0 < F_Y*recall <= 1` inequality applied to counts, with a differential test against `corrected_point_verdict` on both sides of the boundary. `refused_record` refuses a learnable reading. `leg_keys` is the D-12 short-circuit set. Admission reads REFUSED, never MOOT, when all 12 points are refused. D-14: `test_no_retry_or_alternate_key_is_exposed`. |
| SC3 | DEBT-01: scratch `relearn._ROOT`. DEBT-02: D-28 is read verbatim at runtime and an amended note turns a test red. DEBT-03: Phase-17 frontmatter validates. | VERIFIED | DEBT-01: the test monkeypatches `relearn._ROOT` to a scratch `git init` repo and asserts the digests of the tracked `results/phase27_*` files are unchanged, with no stray files and a clean `git status` (1 passed). DEBT-02: `d28_note()` goes through the shared `_blockquote_after`. The tests pin its sha256, check parity with the test-side parser, and flip one byte to confirm the amended note fails (`test_d28_amended_note_reddens`). DEBT-03: `gsd-sdk query frontmatter.validate --schema summary` reports `valid: true` for all 11 files `17-*-SUMMARY.md` (run by this verifier). |
| SC4 | P22-WARNING-4/5 is re-recorded as a named limitation with zero code change. | VERIFIED | `NAMED_LIMITATIONS["P22-WARNING-4/5"]` carries the reason, source, ledger rows and the fact of the transitive load. The accountant census `test_no_v5_module_uses_the_accountant` passes. The diff over the phase's commits (820e365..HEAD) touches only `phase16_persistence.py`, `phase29_prereg.py`, 4 test files and planning docs. `src/personacore/privacy/*` and `results/phase28_ledger.json` are untouched. |

#### Plan must-have truths

| Plan | Truth | Status | Evidence |
|---|---|---|---|
| 29-01 | D-01: 12 `advr_*` keys that wrap `point_key`, refused by every v4.0 parser | VERIFIED | `point_key` wraps `phase25_record.point_key(twin, …)`. Checked by `test_keys_are_refused_by_every_v4_parser`. |
| 29-01 | D-02/D-03: one `V5_RESULT_PATHS` tuple with pathspecs derived from it, and no probe path parses as a key | VERIFIED | Source lines 128-143. Two tests cover it. |
| 29-01 | PREREG-01 ancestry test | VERIFIED | See SC1. |
| 29-01 | D-04: `replay_windows(8)==32` and `(64)==256`, the module is torch-free at import, and there is no literal 4 | VERIFIED | `test_replay_windows_equal_the_dp_expression`, `test_the_prereg_imports_without_torch`, and the AST guard. |
| 29-01 | D-05: route, `F_Y` and grid bound by reference, with an AST guard | VERIFIED | `test_constants_are_by_reference` and the two retype guards. |
| 29-01 | D-11/D-13: the predicate agrees with the route, and the REFUSED record carries counts, recipe and the v4.0 reading re-read from the frontier | VERIFIED | `test_unlearnable_predicate_agrees_with_the_route`, `test_v4_adv_n64_reading_re_reads_from_the_frontier` and `test_refused_record_shape`. See WR-02 for the recipe values. |
| 29-01 | D-14: no retry or alternate surface | VERIFIED | Covered by a test. |
| 29-01 | D-12: `leg_keys` is derived, puts the control first and has length `len(RATIO_GRID)` | VERIFIED | Covered by a test. |
| 29-01 | D-19: the named limitation and the accountant census | VERIFIED | See SC4. |
| 29-02 | D-16: scratch-repo probe | VERIFIED | See SC3. |
| 29-02 | D-18 (amended): top-level `duration`/`completed` copied from `metrics:`, and every file validates | VERIFIED | 2 lines added per file (the diffstat shows 11 × `+2`). The validator returns true. |
| 29-02 | D-18: test checks top level == nested == first-add date | VERIFIED | `tests/test_phase29_debt.py` (11 parametrized cases, passing). |
| 29-03 | D-17: `d28_note()` reads through the shared parser, and the output of `arm_d_qualifier` is byte-identical | VERIFIED | `test_d28_arm_d_qualifier_unchanged_by_the_refactor` passes. |
| 29-03 | D-17: pinned digest and parity | VERIFIED | `_D28_SHA256` pin plus the parity assertion. |
| 29-03 | D-17: kernel absent from the report ⇔ `TD-16-R1-REPORT` is in `NAMED_LIMITATIONS` | VERIFIED | `test_d28_report_absence_is_a_named_limitation`. The report is not in the phase diff. |
| 29-04 | D-15: ruling recorded before any line that depends on it | VERIFIED | 2969994 (20:17:43, SUMMARY + RESEARCH only) precedes e44f045 (20:21:01). `git log -- scripts/phase29_prereg.py` shows only f517c58 before it. |
| 29-04 | D-06: pure admission, `EXPECTED_POINTS==12`, INCONCLUSIVE takes precedence, ADMITTED names the PASS keys in order | VERIFIED | Tests `test_admission_*`, including 12 parametrized INCONCLUSIVE cases. |
| 29-04 | D-06/WR-05: `recall_threshold(…, arm)` reads the advr control and refuses dp | VERIFIED | `test_threshold_reads_the_advr_control_and_refuses_dp`. The function has no caller in phase 29. That matches the v4.0 precedent (`phase27_prereg.recall_threshold` is called by `phase27_relearn`, never by admission) and ROADMAP Phase 33 SC1. |
| 29-04 | D-07 all REFUSED ⇒ REFUSED; D-08 mixed ⇒ MOOT naming the refused leg | VERIFIED | `test_admission_all_refused_does_not_raise` and `_mixed_refused_does_not_raise`. |
| 29-04 | D-10 scope rule, including the D-15 reading | VERIFIED | `test_scope_rule_covers_every_verdict`. See WR-03 for input validation. |
| 29-04 | D-09: pins bound by reference through an AST guard, 5 never-taught baselines, and the control and fixture referenced by their source | VERIFIED | `test_d09_pins_are_attribute_references`, `test_d09_never_taught_baselines_and_advr_control_source` and `test_recovery_fixture_is_pinned_by_reference`. |
| 29-04 | Option 1 only: promotion path | N/A | D-15 was ruled option-2. There is no promotion field in `FRONTIER_SCHEMA`, and ROADMAP is not in the phase diff, which is correct because the ROADMAP note was option-1 only. |
| 29-04 | Every Phase-29 test and the full suite pass on a committed tree | VERIFIED (targeted) and ACCEPTED (full suite) | This verifier's targeted run gave 142 passed for `test_phase29_prereg.py`, `test_phase29_debt.py` and `test_phase16_driver.py`, plus 1 passed for `test_phase27_relearn -k untracked_record`. The full suite was not re-run, as instructed. VALIDATION.md:87 records 2988/4/0 on 345b9b3, and the only commits since then are docs. |

**Score:** 26/26 applicable must-haves verified.

#### D-15 ruling honoured (option-2; (b)/(c)/(d) accepted)

- `CANDIDATE_UNREPLICATED` is a distinct verdict that is never MOOT. It is reached only for INCONCLUSIVE points that pass the frozen `mitigation_gate.promote_to_full_fidelity`, with the REFUSED guard in place (`test_admission_candidate_unreplicated_is_never_moot`).
- No promotion namespace or field exists: `grep promotion` over the module finds only the import of `COVERAGE_FLOOR_REFUSAL_MARKERS` and the ruling prose. `NAMED_LIMITATIONS["GATE-08-NO-PROMOTION"]` is recorded.
- (b): `NEVER_TAUGHT_BASELINES` has 5 entries, and `CONTROL_BASELINE_SOURCE` points to the Phase-32 record. (c): the filenames are unchanged. (d): the `ADVR_ARMS` seam stays in this module and `teach_persona.ADV_ARMS` is not modified.
- The frozen modules (`phase27_prereg`, `phase25_promotion`, `mitigation_gate`, `phase20_gate_coverage`, `phase25_record`) do not appear in the phase diff.

#### Code-review findings: rulings (each reproduced with a one-command probe)

The probe script lives in the session scratchpad. It imports `tests/test_phase29_prereg._v5_frontier` and runs against the committed module.

| Finding | Experiment result | Ruling | Reason |
|---|---|---|---|
| **CR-01**: `admission()` never checks control readings against the verdicts | Confirmed. With an unlearnable n64 control (taught 1/1008, held-out 0/648): all points FAIL gives `MOOT`; one n64 PASS gives `ADMITTED`; with a learnable control but n64 all REFUSED it gives `MOOT`. `recall_threshold(` has no caller in the module. | **Confirmed but out of scope. Not a must-have gap. Escalated as a human decision.** | The 29-04 plan spec (PLAN:148) freezes precedence (1a) shape → (1b) domain → (1c) tallies → ADMITTED → … and names no control/verdict consistency check. The executor implemented it faithfully. D-06's "counts that do not re-derive" means the tallies, as in the v4.0 precedent `relearning_is_worth_attempting`, which also never checks controls. D-11 places the refusal in the route's own precondition (`corrected_point_verdict` refuses when the floors fall outside (0,1]), so a record where the route produced a FAIL cannot carry an unlearnable control. The source of each floor is pinned upstream: ROADMAP Phase 30 SC3 / ACTRL-01 ("a test that feeds a DP-sourced reading is refused") and Phase 32 AFRONT-03. `recall_threshold` being uncalled matches the v4.0 design (it is the relearning clear threshold, consumed by the RELRN legs in Phase 33 per ADMIT-01). The finding is still real defense-in-depth for a contract that is about to be frozen, and the fix is legal until the first `results/phase3*` commit (0 exist today). Hence the decision item. |
| **WR-01**: a non-dict `verdicts` raises | Confirmed: `AttributeError: 'list' object has no attribute 'get'`. | Confirmed. Warning, not a gap. | It fails closed: Phase 33 halts and nothing is admitted. The plan's enumerated (1a) cases are all returned, not raised, and tested. The docstring's "never raised (T-29-14)" is broader than the implementation, so it is a contract-wording defect. It is a one-line fix in the edit window. |
| **WR-02**: `refused_record` accepts any recipe values, and the fixture puts the n8 recipe on an n64 key | Confirmed: `recipe={"replay_windows":999,"n_facts":8,"seed":"x","max_steps":-1}` on `advr_n64_ratio0p250000` is accepted. | Confirmed. Warning, not a gap. | The D-13 must-have is that the record carries the recipe identity, and it does. Checking the values is hardening. The test fixture enshrining the n8 recipe on an n64 key is a real test-quality defect. |
| **WR-03**: `relearning_scope` accepts foreign or empty ADMITTED keys | Confirmed: `adv_n64_ratio0p250000` gives `relearn_point_keys=('adv_n64_ratio0p250000',)`, and empty ADMITTED is accepted. | Confirmed. Warning, not a gap. | D-10 maps an `admission()` result, and `admission()` can only emit keys in `POINT_KEYS()` with ADMITTED ⇔ non-empty. It is exploitable only by a hand-forged dict, so this is hardening. |
| **WR-04**: the ancestry guard covers only `phase29_prereg.py`, and the key renderer and route resolve at call time | Confirmed: no `_assert_frozen_before` covers `phase25_record.py` or `phase20_gate_coverage.py`. `phase25_record.py` was last edited 2026-09-09 (52e736c). Partial mitigation: `test_keys_are_twelve_and_wrap_the_v4_renderer` pins the first and last key literally. | Confirmed. Warning, not a gap. | SC1 asks that "its first-add commit … precedes every v5.0 results artifact", meaning the module itself, and that holds. The route's frozen-ness belongs to the v4.0 guards and to CONTEXT's "never edit" rule. Extending the guard is cheap and recommended. |
| IN-01..IN-04 | IN-01 confirmed (`r["v4_adv_n64_reading"] is V4_ADV_N64_READING` is True). The others were read and are as described. | Info | They affect no must-have. |

#### Required Artifacts

| Artifact | Status | Details |
|---|---|---|
| `scripts/phase29_prereg.py` | VERIFIED | 587 lines. Contains `ADVR_ARMS` and `def admission`. Imported by `tests/test_phase29_prereg.py` and `tests/test_phase16_driver.py`. |
| `tests/test_phase29_prereg.py` | VERIFIED | 925 lines, 36 test functions, passing. |
| `tests/test_phase29_debt.py` | VERIFIED | 56 lines. 11-file parametrization plus a coverage test. |
| `tests/test_phase27_relearn.py` | VERIFIED | Contains `monkeypatch.setattr(relearn, "_ROOT", scratch)`. |
| `scripts/phase16_persistence.py` | VERIFIED | Contains `_blockquote_after`, `D28_NOTE_ANCHOR` and `d28_note`. |
| `tests/test_phase16_driver.py` | VERIFIED | 4 d28 tests. |
| 11 × `17-*-SUMMARY.md` | VERIFIED | Top-level `duration`/`completed` present, and the validator returns true. |

#### Key Link Verification

| From | To | Status |
|---|---|---|
| `phase29_prereg.point_key` | `phase25_record.point_key` | WIRED (line 104) |
| `replay_windows` | `teach_persona.replay_window_budget` (lazy) | WIRED (line 158) |
| ancestry test | `ARTIFACT_PATHSPECS` | WIRED (test line 108-116) |
| DEBT-01 test | `relearn._require_admitted` via `_ROOT` | WIRED |
| DEBT-03 test | `git log --follow --diff-filter=A` | WIRED |
| `d28_note` | 16-CONTEXT.md `- **D-28:**` | WIRED (read at call time) |
| `test_phase16_driver` | `phase29_prereg.NAMED_LIMITATIONS` | WIRED |
| `admission` | `phase27_prereg.point_verdict_string` (by reference) | WIRED |
| `recall_threshold` | `control_readings["advr_<leg>"]` | WIRED as a function. Its consumer is Phase 33 (ADMIT-01), by design. |

#### Data-Flow Trace (Level 4)

Not applicable. No artifact renders dynamic data, and no v5.0 data exists yet by design.

#### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Phase-29 targeted tests | `.venv/bin/python -m pytest -q tests/test_phase29_prereg.py tests/test_phase29_debt.py tests/test_phase16_driver.py` | 142 passed in 5.25s | PASS |
| DEBT-01 probe | `pytest tests/test_phase27_relearn.py -k untracked_record` | 1 passed | PASS |
| DEBT-03 validator | `gsd-sdk query frontmatter.validate <f> --schema summary` × 11 | `valid: true` × 11 | PASS |
| No v5.0 result exists | `git ls-files 'results/phase3*'`; `find results -name 'phase3*'` | 0 / 0 | PASS |
| Review probes | scratchpad `probe.py` | All 5 findings reproduce (see the rulings table) | recorded |

#### Probe Execution

No `scripts/*/tests/probe-*.sh` is declared or used by this phase. Skipped.

#### Requirements Coverage

| Requirement | Plan | Status | Closure |
|---|---|---|---|
| PREREG-01 | 29-01 | SATISFIED | **Fully satisfied by this phase.** Module, ancestry guard, keys, paths, and gate imported by reference. |
| PREREG-02 | 29-04 | SATISFIED | **Fully satisfied as a pre-registration.** The scope rule is committed before any point. Its execution is Phase 33 (ADMIT-02, RELRN-06..09), which consumes it. |
| PREREG-03 | 29-01, 29-04 | SATISFIED (with WR-02 and CR-01 caveats) | **Fully satisfied as a pre-registration** (predicate, REFUSED record, short-circuit set, REFUSED admission reading). Applying it to real controls is Phase 32 (AFRONT-03). |
| PREREG-04 | 29-01 | SATISFIED | **Fully satisfied as a pin.** Phase 30 (ARECIPE-01) consumes it in the train seam. |
| DEBT-01 | 29-02 | SATISFIED | Fully satisfied. |
| DEBT-02 | 29-03 | SATISFIED | Fully satisfied. The absence from the published report is recorded as the named limitation `TD-16-R1-REPORT`, per D-17. |
| DEBT-03 | 29-02 | SATISFIED | Fully satisfied. |
| DEBT-04 | 29-01 | SATISFIED | Fully satisfied, with zero code change. |

No orphaned IDs: REQUIREMENTS.md maps exactly these 8 IDs to Phase 29, and all 8 are claimed by plans. The summaries leave `requirements-completed: []` on purpose. The orchestrator may mark all 8 complete in REQUIREMENTS.md; none of the 8 depends on later-phase work for its own wording.

#### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| (phase diff, scripts/ and tests/) | — | TBD/FIXME/XXX/TODO/HACK | none found | — |
| `tests/test_phase29_prereg.py` | 48, 335-345 | n8 recipe used on an n64 REFUSED key (WR-02) | Warning | The test locks in a wrong record shape. |
| `scripts/phase29_prereg.py` | 252 | Module constant returned by reference (IN-01) | Info | A downstream mutation would corrupt the pin within the process. |

#### Human Verification Required

##### 1. Admission hardening decision (CR-01), before Phase 30's first results commit

**Test:** Choose (a) add the control/verdict consistency check to `admission()` now, or (b) accept that enforcement lives upstream (D-11 route precondition, ACTRL-01, AFRONT-03) and record that acceptance.
**Expected:** A recorded decision before Phase 30 begins. For (a), rerun the Phase-29 tests. The ancestry guard stays green because 0 `results/phase3*` files exist.
**Why human:** The finding is confirmed but outside the frozen plan and CONTEXT spec. The edit window is one-shot; afterwards a fix needs a `_addendum.py` continuation.

##### 2. WR-01..WR-04 / IN-01 disposition

**Test:** Fold them into the same edit, or accept each one with its reason.
**Expected:** Each finding has a recorded disposition.
**Why human:** Same one-shot edit window. None breaks a must-have.

#### Gaps Summary

No must-have gaps. Every roadmap success criterion and every applicable plan truth is verified in the code, with the tests passing in this verifier's own process. The D-15 option-2 ruling is honoured and was recorded before the dependent code. All five review findings (CR-01, WR-01..04) reproduce exactly as reported. All five are ruled confirmed but outside what CONTEXT D-06..D-12 and PLAN 29-04:148 required, because control refusal is pinned to the route precondition (D-11) and to Phases 30 and 32. They share one root cause: the admission, scope and record builders trust their inputs beyond the enumerated shape checks. Because the module becomes ancestry-frozen at Phase 30's first results commit, the developer should decide, before Phase 30, whether to land a single hardening edit covering CR-01, WR-01, WR-02, WR-03 and IN-01 (and extend the guard per WR-04).

---

_Verified: 2026-09-24_
_Verifier: Claude (gsd-verifier)_
