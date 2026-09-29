---
phase: 32-replay-bearing-frontier-re-run-and-verdict
verified: 2026-09-28T18:00:00Z
status: passed
score: 3/3 roadmap success criteria verified; 50/50 plan must-have truths verified (by direct check or targeted/full-suite tests on the committed tree)
overrides_applied: 0
carried_warnings:
  - id: CR-01
    note: "D-08 does not include the import-time sha and module_sha256 is hashed from disk at write time. Latent for the committed records: git diff ae0ed837..e35654c touches only the 12 point records, all 7 trained records share one module_sha256 block and git_sha ae0ed837. Must be fixed (with a dated pin continuation) before phase32_points is reused in Phase 33 or a re-run."
  - id: WR-01
    note: "PINNED_MODULES omits stage-relevant modules. Latent for the same reason (no code changed during the sweep window)."
  - id: WR-02
    note: "The frontier's provenance.module_sha256 omits mitigation_gate/erasure_gate/phase25_condition_c/phase25_gate05/phase25_record/phase30_points. The block is incomplete, but provenance.git_sha fd76e0d pins the full tree, no scripts/src file changed between fd76e0d and HEAD, and the committed-recompute test passes. No verdict or number is affected. Phase 34 should state that git_sha is the authoritative pin."
  - id: WR-03..05, IN-01..07
    note: "All latent for the committed records. The review's latency claims were re-measured here."
---

# Phase 32: Replay-Bearing Frontier Re-run and Verdict Verification Report

**Phase Goal:** The 12 adversarial points are re-measured with replay and judged by the frozen v4.0 gate, so that condition (c) is tested against the ratio rather than the recipe.
**Verified:** 2026-09-28
**Status:** passed
**Re-verification:** No. This is the initial verification.

## Goal Achievement

### Roadmap Success Criteria

| # | Truth | Status | Evidence (measured by the verifier) |
|---|-------|--------|-------------------------------------|
| 1 | All 12 points, controls first, trained/scored unattended on MPS inside the committed budget; each record is written once under its PREREG-01 key, and a second write refuses (AFRONT-01) | VERIFIED | **Tracking and commits.** All 12 `results/phase32_point_*.json` are tracked. Each has exactly 1 commit, and `git show --name-only` on it lists only that path. The add commits are e5ba659 (n8 control) and d37b1e7 (n64 control), followed by the 10 others. **Trained records.** The 7 trained records have device `mps`, `replay.per_step` of length 200 equal to [32] (n8) or [256] (n64) matching `recipe.replay_windows`, all 5 stage timings, and their own taught/held-out recall. **PREREG-03.** The 5 n64 non-controls are PREREG-03 records with `control_recall_counts` taught [0,1008], held-out [1,648]. **Budget.** `cumulative_seconds` is 39903.5 s against `stop_line_seconds` 135989.5 s. **Second-write probe.** A live `write_point_record('advr_n8_ratio0p000000', ...)` on the real repo raised SystemExit "exists — REFUSING to overwrite"; the bytes are unchanged and the tree is clean. **Plist.** RunAtLoad and KeepAlive are false, and `--past-stop-line` appears only in a comment. |
| 2 | A new v5.0 frontier record is assembled write-once; its verdicts are computed by importing the frozen v4.0 gate, and every v4.0 record re-hashes byte-unchanged (AFRONT-02) | VERIFIED | **Commit.** `results/phase32_frontier.json` (sha256 4a4bcb60…97be9) was added by 645641b, which touches only that path; its parent fd76e0d equals `provenance.git_sha`. **Import of the gate.** `scripts/phase32_frontier.py:182` calls `phase25_verdict.curve_verdicts(`, and the file has no local `corrected_point_verdict`, `cleared_abc` or `mitigation_point_verdict`. **Sources.** All 14 `sources` sha256 re-hash equal to `git show HEAD:<path>`. **Second emit.** A live `emit()` refuses ("exists — REFUSING"). **v4.0 byte guard.** `git diff --quiet v4.0 HEAD -- results ':(exclude)results/phase24_token_budget.json' ':(exclude)results/phase3*'` exits 0. At v4.0 there are no `results/phase3*` files, so that exclusion hides no v4 record. `phase24_token_budget.json` was changed only by ef5800a (Phase 30, before this phase). `git diff 59ce590 HEAD -- results` shows no non-phase3 change during Phase 32. **Admission.** Recomputed `phase29_prereg.admission(frontier)` = MOOT (not INCONCLUSIVE). |
| 3 | The verdict states explicitly whether (c) now passes with replay, against v4.0's recipe-confounded reading; a PREREG-03-refused leg is reported with its reading and not re-tuned (AFRONT-03) | VERIFIED | **Rows.** `verdicts.condition_c_vs_v4` has 12 rows, `by_leg` and a statement. `v4_source` sha256 1f182b40… equals the current `results/phase25_frontier.json`. **k counts.** I recomputed `cleared_abc` on the n8 entries: (c) is True only at ratio 0 (self-referential, and that row carries `control_self_referential_dialogue: true`). That gives k5 = 0 and k6 = 1, matching `by_leg.n8`; v4 is 0 of 6 evaluated. **n64 leg.** It reads `refused_prereg03` against v4 `not_evaluated`. Its entries carry verdict None, early_return_reason "own control unlearnable (PREREG-03)" and `control_recall_counts` 0/1008 and 1/648. The n64 control entry is REFUSED by the route with the floor-marker message in `leg_refusals`. **Statement.** It leads with "0 of 5 non-control ratios", gives "1 of 6" beside it, names the self-reference, and names the failing recall on each side. |

**Score:** 3/3

### Plan must-haves (7 plans, 50 truths)

| Plan | Key checks performed |
|------|----------------------|
| 32-01 | `own_control` per_step equality at `scripts/phase30_points.py:266-268`; IN-04 teach_persona module check at :88-92. The D-17 continuation exists in `tests/test_phase30_points.py`, and the D-19 `_SUPERSEDED_PINS` continuation in `tests/test_phase30_calibration.py`. The tripwire is green (targeted run). |
| 32-02 | Write-once order (exists → dirty → D-08 → atomic write) read in `write_point_record`. The clock and stop-line are read from committed blobs and gave the values above. `scripts/phase25_points.py` and `scripts/teach_persona.py` are unchanged since 59ce590. |
| 32-03 | The frozen route is imported and admission is self-checked (`phase32_frontier.py:182, 255`). There is no promotion field and `replicated_at_second_seed` is False. Tallies are {PASS 0, FAIL 0, INCONCLUSIVE 6, REFUSED 6}, and `tallies_by_leg` matches. |
| 32-04 | Plist argv and flags checked. Schedule, stop-line and refused-leg behaviour are covered by `tests/test_phase32_points.py` (green). |
| 32-05 | `tests/test_phase32_live.py` is 474 lines and green in the orchestrator's full suite. |
| 32-06 | The 12 single-path commits, controls first, the MPS device and the replay per_step were re-measured (SC1). |
| 32-07 | Frontier committed alone, v4.0 byte guard, `scripts/phase28_report.py check` exit 0 (re-run here). The full suite is 3221/4/0 at fd47e6b (orchestrator log). |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Phase 32 unit and frontier tests plus the pin tripwire | `pytest tests/test_phase32_frontier.py tests/test_phase32_points.py tests/test_phase30_calibration.py` | 89 passed, EXIT=0 | PASS |
| Record write-once | live `write_point_record` on an existing key | SystemExit refusal, bytes unchanged | PASS |
| Frontier write-once | live `emit()` | SystemExit refusal | PASS |
| Admission re-derived | `phase29_prereg.admission(frontier)` | MOOT | PASS |
| Report guard | `scripts/phase28_report.py check` | exit 0 | PASS |
| v4.0 byte guard | `git diff --quiet v4.0 HEAD -- results …` | exit 0 | PASS |

### Requirements Coverage

| Requirement | Source Plans | Status | Evidence |
|-------------|-------------|--------|----------|
| AFRONT-01 | 32-01, 02, 04, 05, 06 | SATISFIED | SC1 |
| AFRONT-02 | 32-01, 03, 05, 07 | SATISFIED | SC2 |
| AFRONT-03 | 32-03, 05, 07 | SATISFIED | SC3 |

No orphaned IDs: REQUIREMENTS.md maps exactly AFRONT-01..03 to Phase 32. They are still unticked (Pending), and the orchestrator ticks them at close. ACTRL-01 stays unticked by the 2026-09-25 ruling. That is out of scope here, and 32-07 records the evidence for it.

### Code review (32-REVIEW.md) against the success criteria

No finding undermines a success criterion. I re-measured the review's latency claims:
- `git diff --name-only ae0ed837 e35654c` lists only the point records.
- The 7 trained records have 1 distinct `module_sha256` block, and their `provenance.git_sha` is ae0ed837.
- No scripts/src file changed between fd76e0d (the frontier's git_sha) and HEAD.

On that basis:
- **CR-01 and WR-01** would allow a mis-pinned record only if code changed mid-sweep, which did not happen.
- **WR-02** leaves the frontier's provenance hash block incomplete, but no verdict is affected, and `git_sha` plus the recompute test pin it.
- **WR-04** (a non-positive gap crashes the frontier) was not reached: the n8 control gap is +0.134.
- **WR-05** (the pending-commit path) never fired.

These are carried warnings for any reuse of `phase32_points`/`phase32_frontier` in Phase 33. They are not Phase 32 gaps.

### Anti-Patterns

There are no TBD/FIXME/XXX markers in `scripts/phase32_points.py`, `scripts/phase32_frontier.py` or `tests/test_phase32_*.py`.

Info: the PREREG-03 entries' `reasons[0]` still read "outside (0,1]". That text comes from the frozen `refused_record` shape; the D-18 precision fix changed only the statement. This is informational and does not contradict the counts.

### Human Verification Required

None outstanding. The D-16 developer review ("approved" on the re-emit) is recorded in 32-07-SUMMARY, and the committed bytes equal the approved sha256 4a4bcb60….

### Gaps Summary

There are no gaps. The phase goal is met: the 12 points were re-measured with replay on MPS, the frozen v4.0 route judged them, and the verdict states that (c) with replay passes at 0 of 5 non-control ratios at n8 (1 of 6 counting the self-referential control), against v4.0's 0 of 6. The n64 leg is reported REFUSED under PREREG-03 with its control's reading (0/1008, 1/648) and was not re-tuned.

---

_Verified: 2026-09-28_
_Verifier: Claude (gsd-verifier)_
