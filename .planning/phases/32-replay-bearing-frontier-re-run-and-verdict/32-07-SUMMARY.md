---
phase: 32-replay-bearing-frontier-re-run-and-verdict
plan: 07
subsystem: v5.0 write-once frontier (verdicts by import, (c)-with-replay vs v4.0) and the phase gate
tags: [frontier, write-once, d-16, d-18, afront-02, afront-03, prereg-03, admission]
requires: ["32-06"]
provides:
  - "results/phase32_frontier.json: the v5.0 replay-bearing frontier, committed alone at 645641b (sha256 4a4bcb60f9b8bd9a1a63d9525c1d80fee9baec121ac15358a972dd625dc97be9, 56857 bytes)"
affects: [33, 34]
tech-stack:
  added: []
  patterns: [write-once emit held at a blocking developer review, derived (not typed) statement wording, single-path data commit]
key-files:
  created:
    - results/phase32_frontier.json
  modified:
    - scripts/phase32_frontier.py
    - tests/test_phase32_frontier.py
    - tests/test_phase32_live.py
    - .planning/phases/32-replay-bearing-frontier-re-run-and-verdict/32-VALIDATION.md
decisions:
  - "D-16/D-18 precision ruling (developer, 2026-09-28): the statement must name, per side, which recall violates 0 < F_Y × recall <= 1, derived from control_is_unlearnable per side, with no text typed after the result. Fixed in 8d47635 (test) + fd76e0d (fix); frontier deleted and re-emitted once; re-emit approved"
  - "Final verdicts: advr_n8 6 INCONCLUSIVE; advr_n64 6 REFUSED (PREREG-03); admission MOOT"
requirements-completed: []
# AFRONT-02 and AFRONT-03 are evidenced here. AFRONT-01..03 ticks are left to the orchestrator at phase close (after the full suite). ACTRL-01 stays unticked (ruling 2026-09-25).
metrics:
  duration: Task 3 ~25 min (plus the D-16 precision loop before it)
  completed: 2026-09-28
  tasks: 3
  files: 5
---

# Phase 32 Plan 07: v5.0 frontier emit, D-16 review and commit Summary

The v5.0 frontier is committed alone at `645641b`. It was built from the 12 committed point records through the frozen route. At advr_n8, (c) with replay passes at 0 of 5 non-control ratios and all 6 points read INCONCLUSIVE. The advr_n64 leg is REFUSED under PREREG-03 because its own control is unlearnable, so it was not re-tuned. Admission reads **MOOT**. The v4.0 records are byte-unchanged.

## Tasks

| Task | Name | Commit | Result |
| ---- | ---- | ------ | ------ |
| 1 | Emit frontier (untracked), print D-16 review block | none (untracked by design) | First emit 8b96eb1f…e5da rejected at Task 2; re-emitted once after the fix |
| 2 | D-16 developer review (blocking) | none | Precision ruling on the first emit, then "approved" on the re-emit |
| 3 | Commit the frontier alone and run the phase gate | 645641b (frontier), ef2d1d2 (validation) | Gates green; the orchestrator runs the full suite |

## D-16 precision correction (before any frontier commit)

1. **First emit rejected.** The first emit was sha256 `8b96eb1f80935de55a6bcafc5a6ff64c306d01f01fd9c334e243aa3890c7e5da`, 56685 bytes. The developer rejected it **only** on the precision of the D-18 statement. No count, verdict or admission was in question. The ruling was that the statement must name, **per side**, which recall violates `0 < F_Y × recall <= 1`. That must be derived from `control_is_unlearnable` on each side, with **no text typed after the result**.
2. **Fix, test first.**
   - `8d47635` test(32-07) makes the statement name the failing recall per side. v5 n64: taught 0/1008 violates, held-out 1/648 satisfies. v4 n64 is the reverse. Swapped counts swap the words, and `recall_floors` agrees with `phase29_prereg.control_is_unlearnable`.
   - `fd76e0d` fix(32-07) adds `recall_floors()`, which is proven consistent with `control_is_unlearnable`. It also adds `_floor_words()` and `statement_fields()`. The PREREG-03 v5 clause and the not_evaluated v4 clause bind the derived floor words, violating recall first, replacing "outside (0,1]".
3. **Re-emit.** The untracked file was deleted and re-emitted **once** at HEAD `fd76e0d`, giving sha256 `4a4bcb60f9b8bd9a1a63d9525c1d80fee9baec121ac15358a972dd625dc97be9` (56857 bytes).
4. **Scope of the difference.** A field-by-field JSON walk of the rejected emit (kept in the session scratchpad) against the re-emit shows only 5 differing paths:
   - `/verdicts/condition_c_vs_v4/statement`
   - `/provenance/module_sha256/scripts/phase32_frontier.py`
   - `/provenance/git_sha`
   - `/provenance/head_at_write`
   - `/provenance/written_utc`

   **No count, verdict, tally, control reading, leg refusal or admission changed.**
5. **Statement diff.** The advr_n8 sentence is identical. The n64 sentence changed as follows:
   - OLD: `…its own control read taught 0/1008 and held-out 1/648, which puts the recall floors outside (0,1], and it was not re-tuned, so (c) with replay was not evaluated; in v4.0, (c) was measured but not evaluated at any of 6 ratios at adv_n64: the route refused on the control's recall floors (taught 1/1008, held-out 0/648).`
   - NEW: `…its own control read taught 0/1008 and held-out 1/648; the taught recall 0/1008 violates and the held-out recall 1/648 satisfies 0 < F_Y × recall <= 1 (F_Y = 0.7), and it was not re-tuned, so (c) with replay was not evaluated; in v4.0, (c) was measured but not evaluated at any of 6 ratios at adv_n64: the route refused on the control's recall floors (taught 1/1008, held-out 0/648): the held-out recall 0/648 violates and the taught recall 1/1008 satisfies 0 < F_Y × recall <= 1.`
6. **Approval.** At the D-16 re-review of the re-emit, the developer typed, verbatim: **"approved"**. The file was still untracked when approved, and it was committed as emitted.

## Committed statement (verbatim)

> At advr_n8, with replay, (c) passes at 0 of 5 non-control ratios, and at 1 of 6 counting the ratio-0 control, whose dialogue half passes by self-reference (the control_gap is its own gap); in v4.0, without replay, (c) passed at 0 of 6 at adv_n8. At advr_n64, the v5.0 leg is REFUSED under PREREG-03: its own control read taught 0/1008 and held-out 1/648; the taught recall 0/1008 violates and the held-out recall 1/648 satisfies 0 < F_Y × recall <= 1 (F_Y = 0.7), and it was not re-tuned, so (c) with replay was not evaluated; in v4.0, (c) was measured but not evaluated at any of 6 ratios at adv_n64: the route refused on the control's recall floors (taught 1/1008, held-out 0/648): the held-out recall 0/648 violates and the taught recall 1/1008 satisfies 0 < F_Y × recall <= 1.

## Final verdicts

| Leg | Tally | k5 / k6 | v5 state | v4 state | Own control (taught / held-out) |
| --- | ----- | ------- | -------- | -------- | ------------------------------- |
| advr_n8 | 6 INCONCLUSIVE | 0 / 1 | measured | evaluated | 777/1008, 334/648, learnable |
| advr_n64 | 6 REFUSED (PREREG-03) | 0 / 0 | refused_prereg03 | not_evaluated | 0/1008, 1/648, unlearnable |

- Overall tallies: PASS 0, FAIL 0, INCONCLUSIVE 6, REFUSED 6.
- `phase29_prereg.admission(frontier)` reads **MOOT**, which is not INCONCLUSIVE.
- `v4_source` is `results/phase25_frontier.json`, sha256 `1f182b40c9d7c316e57ecd69acd62c7f6407514b9c675bdf8ec677d3f0cb97d5`.
- No promotion field exists (Phase 29 D-15 option 2). "promotion" appears only as the provenance module hash key `scripts/phase25_promotion.py`.
- ACTRL-01 evidence for Phase 33 / the developer: each leg's `control_readings` are sourced from its own advr control record (`results/phase32_point_advr_n{8,64}_ratio0p000000.json`), and admission is re-derived from the committed record. ACTRL-01 stays unticked.

## Phase gate (Task 3)

| Check | Result |
| ----- | ------ |
| Pre-commit: sha256 = 4a4bcb60…97be9 and `git status --porcelain scripts src results tests` shows only the frontier | OK |
| Frontier commit `645641b` touches exactly `results/phase32_frontier.json` | OK (verify one-liner: SINGLE_PATH_OK) |
| `git diff --quiet v4.0 HEAD -- results ':(exclude)results/phase24_token_budget.json' ':(exclude)results/phase3*'` | exit 0 |
| `.venv/bin/python scripts/phase28_report.py check` | exit 0 |
| Flipped guards + phase32: `test_phase32_{frontier,points,live}`, `test_phase31_budget`, `test_phase29_prereg`, `test_phase30_{points,calibration}` | 237 passed (159.7 s); recompute and ancestry take their tracked branches |
| Census gate (10 tests, 32-RESEARCH § Validation Architecture) | 10 passed |
| D-19 tripwire `test_the_phase30_points_pin_continuation_is_a_tripwire` | 1 passed |
| Planning-doc guards: `test_phase28_ledger`, `test_phase28_prereg`, `test_phase25_close`, `test_phase29_debt` | 61 passed |
| `glob\|rglob` census: the 49 other `tests/*.py` matching the pattern (the other 5 matching files, 54 in all, ran in the guards row) | 1291 passed (387 s) |
| Full suite | **Not run by the executor** (~35 min exceeds the tool cap). The orchestrator runs it on the committed tree. |

## Deviations from Plan

- **D-16 ruling loop.** Task 2 returned a precision ruling rather than "approved". Per the resume-signal, the ruling authorized a code fix (`8d47635`, `fd76e0d`) and a single re-emit. The write-once record was never hand-edited. See the correction section above.
- **Full suite deferred to the orchestrator** because of the executor tool cap. `nyquist_compliant` stays `false` in 32-VALIDATION.md until the orchestrator reports EXIT=0.
- **No STATE/ROADMAP/REQUIREMENTS edits.** This follows the orchestrator's instruction and overrides the plan's hand-apply step for this continuation.

## Self-Check: PASSED

- results/phase32_frontier.json is tracked, at 645641b.
- Commits 8d47635, fd76e0d, 645641b and ef2d1d2 are present on main.
