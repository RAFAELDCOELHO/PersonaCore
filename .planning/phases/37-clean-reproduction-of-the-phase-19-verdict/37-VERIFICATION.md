---
phase: 37-clean-reproduction-of-the-phase-19-verdict
verified: 2026-10-04T00:35:30Z
status: passed
score: 4/4 roadmap success criteria verified (plan must-haves 01-07 all verified; the 37-07 post-commit full suite is the orchestrator's, pending)
overrides_applied: 0
---

# Phase 37: Clean Reproduction of the Phase 19 Verdict — Verification Report

**Phase Goal:** An outsider can re-derive the Phase 19 verdict exactly with one CPU command, and an MPS replica of k = 78 is published beside the verdict under a tolerance fixed before it ran.
**Verified:** 2026-10-04T00:35:30Z at HEAD 8a289fc
**Status:** passed. One open condition: the orchestrator's full suite at 8a289fc (37-07 truth 5) must come back green.
**Re-verification:** No. This is the initial verification.

All evidence below comes from commands the verifier ran at 8a289fc. None of it is taken from a SUMMARY. The full suite was running in the background, so the verifier did not run it and did not touch MPS. Nothing was written under scripts/, src/, tests/, results/, ledger/ or data/. `git status --porcelain` showed only the pre-existing ` D .claude/scheduled_tasks.lock` before and after every probe.

## Goal Achievement

### Observable Truths (ROADMAP success criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| SC1 | REPRO-01: one CPU command re-derives k=78, target 0/27, 7/7 non-targets beyond 0.2962962962962963 and 77.6370113463966% destroyed, and halts on divergence | ✓ VERIFIED | See SC1 below. |
| SC2 | REPRO-02: each of defects A-E is routed by a named function, and removing any route turns a test red (natural red) | ✓ VERIFIED | See SC2 below. |
| SC3 | REPRO-03: the tolerance and the definition of "replicated" were pre-registered before the replica ran; the replica is published beside the verdict, never over it | ✓ VERIFIED | See SC3 below. |
| SC4 | No record exists before the prereg module and its ancestry test are committed; records are write-once and committed only after Rafael's "approved" | ✓ VERIFIED | See SC4 below. |

**Score:** 4/4

**SC1 evidence (REPRO-01)**
- `.venv/bin/python scripts/phase37_r1a.py` printed `R1a REPRODUCED (record verified)` with k 78, [0, 27], [7, 7], destroyed_pct 77.6370113463966, margin 0.2962962962962963, b_floor 0.14814814814814814 and verdict FAILURE. It exited 0 in 1.6 s.
- `derive()` compares every value against `phase35_prereg.R1A_ASSERTIONS` and raises `SystemExit` with "STOP … never adjust (D-10)" when one differs.
- All 7 `INPUT_RECORDS` are tracked results files (`git ls-files --error-unmatch` passed). It needs no checkpoint, no gitignored data and no GPU.
- Tests that cover the halt: `test_a_nudged_dialogue_ppl_halts_naming_destroyed_pct`, `test_a_dropped_component_halts_naming_k` and `test_a_dropped_reason_halts`.

**SC2 evidence (REPRO-02)**
- The named routes are `route_a`, `route_b`, `route_c`, `route_d` and `select_target_prefix` (E), all in `scripts/phase37_routes.py`.
- The verifier removed each route in-process with a scratchpad probe, putting back the pin's own unrouted path from `test_phase37_routes.UNROUTED`. No committed file was touched:
  - A: R1a halts with STOP INCONCLUSIVE.
  - B: R1a halts because the reasons read "floor 0.2000".
  - C: the pin's PROOF FAILED fires (13 questions vs 27).
  - D: `TypeError`.
  - E: the twin passes |R| = 6 against the curve's 8.
- The shipped test `test_rederive_reproduces_…` went RED for each of A-D.

**SC3 evidence (REPRO-03)**
- The prereg `be311f0` (2026-10-03 10:14 -0300) fills `r1b_tolerance_and_replicated` with tolerances k 0, target 0, nontargets 0 and destroyed_pct 0.8396203493271365 (`kind` derived). The verifier recomputed the derived tolerance and got bit-equal 2×0.005214448168350039/1.2420966625043919×100.
- The prereg was committed 10 h before the ledger start at 2026-10-03T23:16:49Z.
- `results/phase37_r1b.json` reads verdict REPLICATED. Every row of `comparison.per_key` has `within` True with abs_diff 0.
- The verifier recomputed the verdict independently: `prereg.replicated(routes.rederive(results/phase37_r1b_arm.json))` returned `REPLICATED`.
- The record is published beside the verdict, not over it. `git log 8f87f6c..HEAD -- 'results/phase19_*' README.md scripts/phase19_erasure.py scripts/erasure_gate.py` is empty.

**SC4 evidence (ordering and write-once)**
- `be311f0` (prereg) and `9425fe5` (test) are both ancestors of `fe715c5`, the first `results/phase37_*` record. The prereg has no later commit.
- The R1b chain runs ledger `3f87acf` → arm `57dcd4b` → record `8a289fc` (each pair checked with `merge-base --is-ancestor`). Each of the four record commits touches a single path.
- The ledger diff in 3f87acf is +2 lines with 0 removed.
- File SHA-256 values equal the ones in the SUMMARYs: r1a `bcae9145…1f02`, r1b `a37c5356…6ed6c`, arm `f6539c05…91ecbc`.
- "approved" appears in every record commit subject. The approvals themselves are the orchestrator's attestation; see the note under Human Verification.

### Plan must-haves (merged; none reduces roadmap scope)

| Plan | Must-have cluster | Status | Evidence |
|------|-------------------|--------|----------|
| 37-01 | D-01 to D-07, D-11 to D-16; SC4 ancestry test | ✓ | `R1B_TOLERANCE_AND_REPLICATED` is a mappingproxy with the tolerance and replicated_definition (kind preference). `replicated()` has signature `(rederived)` and never takes the draw identity. Cost: 1.2590560358100467 h ≤ cap 1.6622708975519829 h. `_assert_frozen_before(PREREG, _phase37_records())` is at tests/test_phase37_prereg.py:284 and `RECORDS_AT_COMMIT == 0` at :304. |
| 37-02 | routes A-E, single-route swaps, ERASE-08 wrapper, pin/gate byte-unchanged, AST gates | ✓ | `test_swapping_one_route_for_the_pins_own_path_diverges` is parametrized over A-D. E is covered by `test_defect_e_twin_is_smaller_and_the_resweep_moves_k`, `test_select_target_prefix_passes_target_ablates_call_shape` (asserts `len(references) == curve reference_set_size`) and the twin-refusing recorder fixture. `test_pin_and_gate_are_byte_unchanged` holds. `report()` is never called. |
| 37-03 | R1a derive/write/check/main, D-13 b-floor, reasons EQUAL to the recorded report, cross-check with r1a_rederive | ✓ | Code read. `derive()` cross-checks k, destroyed_pct and margin against `phase35_prereg.r1a_rederive()`. The writer proves the path matches `RECORD_GLOB` and writes only through `phase25_run.atomic_write_json`. |
| 37-04 | R1b driver: preflight before ledger start, sweep through `select_target_prefix`, `prefix_decision`, `run_erasure_arm(record_path=)`, emit, plist | ✓ | Wiring checked by grep: `require_launch(FRONT` at :203, then `append("start"` at :237, then `routes.select_target_prefix(` at :254, then `record_path=root / prereg.R1B_ARM_RECORD` at :299, then the end line at :331. Emit calls `prereg.replicated(routes.rederive(replica))` at :368-369. |
| 37-05 | R1a record committed alone after approved; carries D-13 and input_sha256 | ✓ | `fe715c5` touches a single path. The record verifies on re-run. |
| 37-06 | the one attempt: start and end lines, provenance mps, arm present iff run_arm | ✓ | Ledger lines 11 and 12 hold one start and one end for `v6/37/R1b/replica`, and the end names `results/phase37_r1b.json`. Provenance shows device mps, torch 2.7.1, git_sha_at_launch = git_sha_at_end = 7831ea9, head_moved_during_run false and modules_changed_since_launch []. decision.run_arm is True and the arm record exists. |
| 37-07 | records committed ledger, then arm, then record, after approved; replica beside the verdict; D-03 verdict from `prereg.replicated`; post-commit full suite green | ✓ (suite PENDING) | Ordering and contents are verified above. The post-commit full suite is running now and the orchestrator adds its result. |

### Required Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| `scripts/phase37_prereg.py` | ✓ VERIFIED | It fills the slot, derives the tolerance at import and holds the rule functions. Single commit `be311f0`, frozen since. |
| `scripts/phase37_routes.py` | ✓ VERIFIED | Wired: R1a and R1b both call `rederive`, and R1b calls `select_target_prefix`. |
| `scripts/phase37_r1a.py` | ✓ VERIFIED | Runs and exits 0 (verify mode). |
| `scripts/phase37_r1b.py` | ✓ VERIFIED | It produced the committed R1b records. |
| `artifacts/com.personacore.phase37.r1b.plist` | ✓ VERIFIED | Covered by the plist mirror test, which passes. |
| `tests/test_phase37_{prereg,routes,r1a,r1b}.py` | ✓ VERIFIED | `pytest -q tests/test_phase37_*.py`: 146 passed in 13.05 s. |
| `results/phase37_r1a.json` | ✓ VERIFIED | Write-once and committed alone. |
| `results/phase37_r1b_arm.json` | ✓ VERIFIED | k 78, ablated set equal to the committed set, draws `==` committed `phase19_arm_erased.json` draws. |
| `results/phase37_r1b.json` | ✓ VERIFIED | REPLICATED. Its sweep, decision, draw_identity (criterion false), nontarget_context (criterion false), re_measured and inherited fields are all present. |
| `ledger/v6_mps_ledger.jsonl` | ✓ VERIFIED | +2 lines for the one attempt. |

### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| phase37_prereg | phase35_prereg | `fill("r1b_tolerance_and_replicated", …)` | WIRED |
| phase37_routes | phase19_erasure (pin) | `pin.render_verdict(`, `pin.select_ablation_prefix(` | WIRED |
| phase37_routes | phase19_run | `p19run._pooled_rows(` (C), `p19run._order_normalised(` (A); `report()` never called | WIRED |
| phase37_r1a | phase37_routes | `routes.rederive(`, `routes.b_floor_from_replicate()` | WIRED |
| phase37_r1a | results/phase37_r1a.json | `phase25_run.atomic_write_json(` after the RECORD_GLOB proof | WIRED |
| phase37_r1b | phase36_ledger | `require_launch(FRONT` before `append("start"` | WIRED |
| phase37_r1b | phase37_prereg | `prereg.replicated(` | WIRED |
| ledger end line | results/phase37_r1b.json | `record` field | WIRED |

### Data-Flow Trace (Level 4)

| Artifact | Data | Source | Real data | Status |
|----------|------|--------|-----------|--------|
| results/phase37_r1b.json verdict | `comparison` | `prereg.replicated(routes.rederive(<MPS arm record>))` | yes: recomputed by the verifier from the committed arm | ✓ FLOWING |
| results/phase37_r1a.json | assertions | `routes.rederive(results/phase19_arm_erased.json)` | yes: re-derived on every run of verify mode | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|----------|
| One CPU command re-derives the verdict | `.venv/bin/python scripts/phase37_r1a.py` | prints REPRODUCED (record verified) and the four numbers; EXIT=0 | ✓ PASS |
| Phase 37 tests | `.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_phase37_*.py` | 146 passed | ✓ PASS |
| The R1b verdict re-derives from the arm | `prereg.replicated(routes.rederive(arm))` | REPLICATED | ✓ PASS |
| Natural red per route A-E | scratchpad in-process un-routing probe | A, B, C and D all STOP R1a and turn the rederive test red; E gives \|R\| 6 ≠ 8 | ✓ PASS |
| The tolerance is derived, not typed | `prereg.DESTROYED_PCT_TOLERANCE` vs the arithmetic | 0.8396203493271365 on both sides | ✓ PASS |

### Probe Execution

Step 7c: no `scripts/*/tests/probe-*.sh` is declared by the Phase 37 plans or summaries. The repo's clean-tree probes run inside the full suite, which the orchestrator is running.

### Requirements Coverage

| Requirement | Source Plan | Status | Evidence |
|-------------|-------------|--------|----------|
| REPRO-01 | 37-03, 37-05 | ✓ SATISFIED | SC1 |
| REPRO-02 | 37-02 | ✓ SATISFIED | SC2 |
| REPRO-03 | 37-01, 37-04, 37-06, 37-07 | ✓ SATISFIED | SC3 and SC4 |

There are no orphaned requirements: REQUIREMENTS.md:807-809 maps exactly REPRO-01..03 to Phase 37. All three are still unticked, and the orchestrator ticks them by hand.

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| scripts/phase37_*.py, tests/test_phase37_*.py, the plist | TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER | none found | — |
| 37-REVIEW.md | WR-01..05 | ✓ fixed | Each fix commit (9abab12, 5896ae3, 9069c5c, 2781bd6, 6dbad06) touches its script and test. The fixes are present in the code: `git_sha_at_launch`, the write-once sweep before the arm, the missing-input refusal before the start line, EQUAL reasons in R1a, and `os.chdir(_ROOT)`. All five predate fe715c5. The six Info findings are left open by design. |
| phase directory | no 37-07-SUMMARY.md | ℹ️ Info | The 37-07 commits exist (3f87acf, 57dcd4b, 8a289fc), but no SUMMARY records them. The orchestrator should write it alongside the suite result. |

### Human Verification Required

None that blocks. The "approved" provenance for fe715c5, for the R1b launch and for the R1b records is attested by the orchestrator, by the commit subjects and by the 37-05 and 37-06 SUMMARYs. The verifier cannot re-observe a session message, and the task brief establishes these approvals.

### Gaps Summary

No gaps found. Both halves of the goal hold in the committed tree:
- The outsider command re-derives the verdict exactly and refuses any divergence.
- The MPS replica re-measured k = 78 with the identical address set. It reproduced the committed draws bit for bit and is published as REPLICATED under the tolerance pre-registered 10 h before launch.
- Every Phase 19 file and the README are unchanged.

The phase closes only once the orchestrator's full suite at 8a289fc comes back green with zero new skips.

---

_Verified: 2026-10-04T00:35:30Z_
_Verifier: Claude (gsd-verifier)_

## Orchestrator addendum (2026-10-04): the open condition is met

The full suite at 8a289fc (all Phase 37 records tracked) printed `3928 passed, 4 skipped, 83 warnings in 2574.46s (0:42:54)` and `EXIT=0`. That is zero new skips; the same 4 skips appeared at 7e6432c and fe715c5. 37-07 truth 5 holds, so status `passed` stands unconditionally. 37-07-SUMMARY.md is written alongside this addendum.
