---
phase: 25-frontier-sweep-and-the-existence-gate-verdict
verified: 2026-09-09T21:40:00Z
head: 795edb3
status: human_needed
score: 7/7 must-haves verified (5 ROADMAP Success Criteria + ADVT-01 + RPT-02)
overrides_applied: 0
requirements_accounted: 8/8 (CTRL-01, CTRL-02, FRONT-01, FRONT-02, FRONT-03, FRONT-04, ADVT-01, RPT-02)
verifier_ran:
  - "38/38 route-reachable point verdicts re-derived LIVE through the imported frozen route — 0 mismatches on (verdict, reasons, arm)"
  - "12/12 adversarial adapters re-hashed from bytes against their records — 0 mismatch"
  - "44/44 recall readings re-checked against the frontier's adapter_sha256 — 0 mismatch"
  - "gate/budget module sha256 in the artifact recomputed from live bytes — both match"
  - "tuple(point_keys) == ORDERED_POINT_KEYS() — hard equality holds on the committed bytes"
  - "801 passed, 3 skipped across 12 phase-25 CPU test files; 45 passed across the phase-20/24 ancestry+provenance guards"
  - "machine state read live: pmset sleep 1 / disksleep 10 / powernap 1; launchctl has no personacore job; KeepAlive False in all 5 committed plists"
  - "both published figures opened and read visually"
human_verification:
  - test: "Push `main` and confirm the GitHub Actions run on ubuntu-latest is green, then replace the DERIVED ubuntu skip pin (62/62) in tests/test_phase25_venue.py with the measured number if it differs."
    expected: "A green CI run whose HEAD contains this phase's wave-10..13 files."
    why_human: "`main` is 95 commits ahead of `origin/main`; the newest origin/main commit is 2026-09-02, so NO CI run has ever executed any Phase-25 wave-10..13 code. The ubuntu literal is self-declared DERIVED, NOT MEASURED at tests/test_phase25_venue.py:238. Only a push can close it, and the in-flight 25-REVIEW CR-01 fix (tests/, scripts/phase25_promotion.py, scripts/phase25_recall.py) must land first."
  - test: "Decide how `mechanism_pin_disclosure.governs` in results/phase25_frontier.json is corrected: a sanctioned delete-in-its-own-commit re-assembly, or a recorded discrepancy in results/phase25_operational_note.md."
    expected: "Either the artifact is re-assembled with the per-arm wording, or the discrepancy is written down where a reader of the artifact will meet it."
    why_human: "Confirmed independently (25-REVIEW WR-03): the published sentence says the lot is re-derived `for all 44 points` as `batch_size x max(1, grad_accum_steps)`, but the code applies that only on the adversarial arm — on `dp_n8_sigma0p000000` that formula gives 8 x 8 = 64 while `records_per_lot` is 8 (n_facts). `lot_rule_by_arm` beside it IS correct, so the artifact contradicts itself in FRONT-03's single source of truth. No verdict, count, epsilon or Success Criterion is affected. The artifact is write-once and downstream-pinned, so the repair route is a decision, not a code fix — and the review's own interim prescription (record it in the note) has not been executed and has no deferred-items entry."
  - test: "Decide whether a replay-bearing adversarial re-run is in v4.0 scope before Phase 28 publishes, and give it an owning phase if it is."
    expected: "Either a named phase owns the re-run, or Phase 28's report is explicitly scoped to publish the adversarial arm as recipe-confounded."
    why_human: "The adversarial arm trains with NO replay (verdicts.adversarial_no_replay, note 12.5c), so condition (c) fails on all 12 adversarial points for the recipe rather than the ratio, and at n=64 the arm's own ratio-0 control scored held-out 0/648 — which is what the route refused on. deferred-items D-25-18-ADV64-REFUSED hands this to 'a later phase' but names none, and Phase 26 (canary), 27 (relearning) and 28 (report) carry no goal or success criterion covering it. Scope/GPU-budget call, not a verifier call."
warnings:
  - "25-REVIEW CR-01 (tests/test_phase25_recall.py host-only dependencies) is known-and-being-fixed by a parallel agent; HEAD 795edb3 already carries the first half. Not counted as a gap per the verification brief."
  - "25-REVIEW WR-01: phase25_promotion.build() / phase25_recall.emit() overwrite committed, frontier-pinned artifacts in place with no refusal and no dirty-tree check — unlike phase25_record.py, which refuses. Being touched by the in-flight fixer."
  - "25-REVIEW WR-02: curve_pass catches every SystemExit from curve_verdicts, so a structural bug would be recorded as six REFUSED verdicts. Today's six refusals are the genuine route refusal (I reproduced it live), but the catch is too wide to distinguish the two."
  - "25-REVIEW WR-04: literals retyped into published prose in results/phase25_promotion.json with no write-time assertion against the values beside them. They match today (tests assert them)."
  - "D-25-19-PLOT-ANNOTATIONS: the two figures do not draw the capacity branch or the arm existentials. I read both PNGs; they are honest, artifact-sourced and carry the D-19/D-23 caption. No ROADMAP criterion requires those annotations, and no later phase owns the plotter change."
  - "deferred-items D1: tests/test_phase23_resume.py::test_production_resume_epsilon_bit_identical is flaky under full-suite load (1 red in 4). Pre-existing, not caused by this phase, not re-run here."
deferred:
  - truth: "The milestone report carrying the published null, the two arm existentials and both limitations"
    addressed_in: "Phase 28"
    evidence: "phase25_prereg.PUBLICATION_OBLIGATION pins the seven fields Phase 28 must carry; Phase 28 SC1 'The milestone report publishes the measured outcome including the DP null at both capacities'."
  - truth: "An empirical epsilon lower bound for the audit target dp_n8_sigma0p000000"
    addressed_in: "Phase 26"
    evidence: "CANARY_RESERVATIONS.audit_target_rule resolved to dp_n8_sigma0p000000 at close; Phase 26 SC1 'One-run canary auditing produces an empirical lower bound on epsilon for a published DP point'."
---

# Phase 25: Frontier Sweep and the Existence-Gate Verdict — Verification Report

**Phase Goal:** Both mitigation arms on one measured-privacy × measured-utility plane at both
capacities, judged by importing the rule Phase 20 committed — with the pre-registered null a named
verdict.
**Verified:** 2026-09-09T21:40:00Z at HEAD `795edb3`
**Status:** human_needed — 7/7 must-haves verified; three items need a developer decision or a CI run
**Re-verification:** No — initial verification

## Goal Achievement

The goal is achieved. The empty frontier is a *reached* branch, not a missing result: I re-derived
every route-reachable verdict myself, live, through the imported frozen gate, and got the committed
strings back exactly. What holds this report at `human_needed` is not a hole in the phase — it is
three things a verifier is not entitled to settle: a CI run that has never happened, a self-
contradicting sentence inside a write-once artifact, and an unowned scientific follow-up.

### Observable Truths

| # | Truth | Status | Evidence (verified by me, not read from SUMMARY) |
|---|-------|--------|---------------------------------------------------|
| 1 | **SC1 / CTRL-01+02** — the retrained unmitigated control runs first, as a sweep point differing from every DP point by exactly the two DP parameters, with its non-bit-identity recorded in advance | VERIFIED | `git log --diff-filter=A` on the 44 records: `dp_n8_sigma0p000000` (`359a6fc`) and `dp_n64_sigma0p000000` (`e444a95`) are commits 1 and 2 of 44. The record's `reproduction_gate` = `{expected [790,1008], observed [790,1008], passed true, comparison "hard == on integer counts"}`. `clip_norm 1000000.0`, `sigma 0.0`, `clip_bind_count 0`, `epsilon null`. Taught 790/1008 (rate 0.7837301587301587 = the Phase 23 matched control exactly), held-out 346/648. Non-bit-identity pre-recorded as a bound, not discovered: `results/phase25_probe2_tensors.json` `agreement_bound` 0.182184 (n=8) / 0.034454 (n=64) under `agreement_bound_governs` "BOUNDED DISAGREEMENT, NEVER EQUALITY". D-04's tripwire is real: `tests/test_phase25_prereg.py::test_the_bit_identity_tripwire_fires_on_a_planted_violation` passes. |
| 2 | **SC2 / FRONT-01** — both arms carry a full curve at both capacities, reconnecting to the control at σ→0 and reaching the floor, with the extremes run first | VERIFIED | `arms` = `[dp_n8, dp_n64, adv_n8, adv_n64]`; 44 points = 2×16 + 2×6; `axis_for_arm` = sigma/sigma/ratio/ratio. Commit order is controls → the eight extremes (`dp_n8_sigma80`, `adv_n8_ratio0`, `dp_n64_sigma80`, `adv_n64_ratio0`, both `ratio1p909091`) → the 36 interior, so an empty frontier was reachable in two runs as designed. σ=80 lands on the floor at both capacities (extraction 0/416, taught 0/1008); σ=0 is the control (790/1008, 87/1008). The adversarial arm terminates at the pool ceiling 1.9090909090909092 with `axis_terminus.statement` naming D-19 — the scope continuation the ROADMAP wrote *before* the run, not after. |
| 3 | **SC3 / FRONT-02** — every ε at both granularities with unit, sampler and multiplicity in one sentence; no bare ε outside the helper | VERIFIED | `phase25_epsilon.report_epsilon(*, point_epsilon, curve_total_epsilon, selection_accounted)` — keyword-only, no defaults; omitting two raises `TypeError: missing 2 required keyword-only arguments`; three positionals raise `takes 0 positional arguments`. `epsilon_report.dual_granularity` names FACT-LEVEL as governing and EXAMPLE-LEVEL as the counterfactual in the same sentence with `q = 1.0` and per-step multiplicity 1. `multiplicities` carries both figures (262.9437465865647 pin / 207.0180229382851 artifact rule) with the frozen record's status `RECORDED, NOT RESOLVED` verbatim. 32 rendered strings, each re-rendered by a live call in `tests/test_phase25_frontier.py`. Curve total 2387.299119573244 over 30 summands at `total_delta` 30×1e-5, `selection_accounted: false` with its reason. |
| 4 | **SC4 / FRONT-03** — the frontier artifact is the single source of truth: counts not rates, per-question successes, ordered keys proved on write, `accounting: null` on the adversarial arm, module sha256s travelling; every figure drawn only from it | VERIFIED (1 warning) | `results/phase25_frontier.json`, 22,311,714 B, ONE commit (`4030d0e`), `git diff --exit-code` clean. `tuple(point_keys) == tuple(phase25_record.ORDERED_POINT_KEYS())` → True on the committed bytes. All 12 `adv_*` points carry `accounting is None`; DP points carry the accounting dict. `gate_module_sha256` `86db4798…` and `budget_module_sha256` `1b35aa88…` both equal sha256 of the live `scripts/mitigation_gate.py` / `mitigation_budget.py`. Every recall block carries `numerator`/`denominator`/`questions` beside its `rate`. `scripts/plot_phase25.py` declares `ALLOWED_READS = (FRONTIER_RECORD,)` and `tests/test_phase25_plots.py` fires that clause on a planted second read (12 passed). **Warning:** `mechanism_pin_disclosure.governs` misstates the lot rule for the 32 DP points — see human item 2. |
| 5 | **SC5 / FRONT-04** — the verdict is computed by importing the gate module's constants, and the null is a named pre-registered verdict | VERIFIED | **I re-derived all 38 route-reachable verdicts myself** by calling `phase20_gate_coverage.corrected_point_verdict` with each record's own 21 pin kwargs + its `whole_curve_inputs`: `live re-derived: 38, mismatches: 0` on `(verdict, reasons, arm)`. The 6 `adv_n64` refusals fire live from the same route (`Y_heldout=0.0`, its own control 0/648). `tallies` = `{PASS 0, FAIL 32, INCONCLUSIVE 6, REFUSED 6}`; `capacity_branch` = `null-at-both-capacities`, a member of `mitigation_gate.CAPACITY_BRANCHES`; existentials carry denominators verbatim ("0 of 32", "0 of 6") with `arm_existential_counts.adversarial` = examined 6 / in arm 12; `empty_frontier_reached: true`, `candidates: []`, `tail_cost_hours: 0`. Nothing retyped: no threshold literal, and the promotion rule commit `a6ded2e` is proved an ancestor of every record's add-commit. |
| 6 | **ADVT-01** — the adapter TRAINED against the Phase 18 attack suite, intensity as the sweep axis (the half Phase 24 correctly refused to tick) | VERIFIED | 12 adversarial adapters exist on disk and **I recomputed all 12 sha256 from bytes: 12 verified, 0 bad** against `points[k].adapter_sha256`. 10 are at non-zero ratios across the pinned six-point `ADVERSARIAL_RATIO_GRID`. `tests/test_phase25_extremes.py` asserts the trained families are present and the mask-fraction band holds on the real adapters. This closes the item Phase 24's own VERIFICATION deferred to Phase 25. |
| 7 | **RPT-02** — the normalizing prose helper is USED for correction sweeps (the second half of the conjunction) | VERIFIED | `tests/test_phase25_correction.py` matches every claim through `scripts/_prose.normalized` and searches each marker from the claim's own index (9 sentinel pairs, every original asserted to survive beside its continuation); `tests/test_phase25_close.py` reads the note through `normalized` too. Both green. The register is stated as four instances in three guard files and the traceability row says so without variation. |

**Score: 7/7 truths verified.**

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `results/phase25_frontier.json` | write-once single source of truth, 44 points inline | VERIFIED | 1 commit, clean, 22.3 MB, ordered keys hard-equal to the pin |
| `results/phase25_point_*.json` (44) | one record per pinned point, one add-commit and one path each | VERIFIED | `git ls-files` = 44; scanned all 44 — none has ≠ 1 add commit |
| `results/phase25_promotion.json` | the verdict pass, 21 kwargs per point | VERIFIED | 38 verdicts re-derived live, 6 refusals reproduced live |
| `results/phase25_recall.json` | condition (b) for all 44, pinned to adapter digests | VERIFIED | 44 entries, 0 digest mismatches vs the frontier; 2 `point_record` + 42 sidecars |
| `results/phase25_interior_log.json` / `phase25_extremes_log.json` | the run as the records show it | VERIFIED | 538 + tests green; completeness 44 == 44, missing [] extra [] |
| `results/phase25_frontier_dp.png` / `_adversarial.png` | figures drawn only from the artifact | VERIFIED | Read both. DP: 15 noised points flat at 0 recall across the ε ladder at both capacities, σ=0 control line, never-taught floor. Adversarial: the ratio curve falling to the pool-ceiling terminus, n=64 panel topping out at 0.04, D-19/D-23 caption present. |
| `scripts/phase25_{record,promotion,recall,verdict,epsilon,prereg}.py` | the machinery | VERIFIED | all present, imported by the tests that assert the artifacts |
| `artifacts/com.personacore.phase25.*.plist` (5) | `KeepAlive` false, `RunAtLoad` false | VERIFIED | read with `plistlib`: all five False/False |
| Frozen modules | byte-unchanged | VERIFIED | `git diff --exit-code` clean on `mitigation_gate.py`, `mitigation_budget.py`, `phase20_gate_coverage.py`, `_prose.py`, `pyproject.toml` |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `phase25_promotion` | frozen `mitigation_gate` | `phase20_gate_coverage.corrected_point_verdict` | WIRED | 38/38 live re-derivations match byte-for-byte, including reason strings |
| frontier artifact | frozen module bytes | `gate_module_sha256` / `budget_module_sha256` | WIRED | recomputed from live files, both match |
| `plot_phase25` | frontier artifact | `ALLOWED_READS` allow-list | WIRED | single-file allow-list, planted-second-read test fires |
| recall artifact | the swept adapters | `adapter_sha256` pin | WIRED | 44/44 pinned to the same digests the records carry |
| adversarial adapters | their records | sha256 from bytes | WIRED | 12/12 recomputed, 0 mismatch |
| pre-registration | the data | `git merge-base --is-ancestor` | WIRED | promotion rule commit precedes all 44 record commits |

### Data-Flow Trace (Level 4)

| Artifact | Data | Source | Real data? | Status |
|----------|------|--------|-----------|--------|
| `phase25_frontier.json::points` | 44 records inline | the committed per-point records, keyed by the `point_key` inside each file | Yes — 416 gated + 448 reported per-question rows per point | FLOWING |
| `phase25_frontier.json::verdicts` | verdicts/reasons | `phase25_promotion.json`, itself produced by the imported route | Yes — I reproduced 38/38 live | FLOWING |
| `points[k].taught_recall` (42) | recall counts | `phase25_recall.json`, sha-pinned per point | Yes — real MPS scoring, 15.77 h, denominators 1008/648 | FLOWING |
| both PNGs | plotted series | the frontier artifact only | Yes — visually confirmed the points, control line, floor, terminus | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| the verdict re-derives from the frozen rule | live call of `corrected_point_verdict` over all 38 reachable points | `live re-derived: 38 mismatches: 0` | PASS |
| the adv_n64 refusal is the route's, not a story | live call on `adv_n64_ratio0p000000` | `SystemExit` equal to the recorded reason, containing `Y_heldout=0.0` | PASS |
| the ε helper cannot be bypassed | `report_epsilon(point_epsilon=1.0)` / three positionals | `TypeError` both ways | PASS |
| ordered keys are a hard equality | `tuple(point_keys) == ORDERED_POINT_KEYS()` | `True` | PASS |
| adapters are the ones that were swept | sha256 of the 12 adversarial adapters | 12 verified, 0 bad | PASS |
| the machine was really put back | `pmset -g`, `launchctl list \| grep personacore` | `sleep 1 / disksleep 10 / powernap 1`; no personacore job | PASS |
| phase-25 CPU suites | 12 test files | `675 passed, 3 skipped` + `126 passed` = **801 passed, 3 skipped** | PASS |
| no regression in the pre-registration guards | `test_phase20_prereg.py`, `test_phase20_correction.py`, `test_phase24_record.py` | `45 passed` | PASS |

Full suite not re-run (2743 passed / 4 skipped at HEAD per 25-20, 25:43 — per the brief).

### Requirements Coverage

| Requirement | Source plans | Status | Evidence |
|-------------|--------------|--------|----------|
| CTRL-01 | 25-01, 25-13, 25-15, 25-20 | SATISFIED | control is commit 1 of 44; reproduction gate `passed: true` under hard `==` on 790/1008 |
| CTRL-02 | 25-01, 25-07, 25-12, 25-13, 25-15, 25-20 | SATISFIED | sweep point at `sigma 0.0`, `clip_norm 1000000.0`, `clip_bind_count 0`, `epsilon null`; the `inf` literal is superseded in place with the refusal `[dp-refusal:clip-domain]` and the ROADMAP/REQUIREMENTS continuations still standing beside the original |
| FRONT-01 | 25-05..25-08, 25-10..25-12, 25-14, 25-16..25-18, 25-21 | SATISFIED | 44 points, 4 legs, extremes first, σ=80 at the floor, adversarial at the pool ceiling under the pre-recorded D-19 scope |
| FRONT-02 | 25-03, 25-08, 25-19 | SATISFIED | three-required-kwarg helper, 32 live-reproduced renderings, both multiplicities named |
| FRONT-03 | 25-08, 25-09, 25-10, 25-14, 25-19, 25-20 | SATISFIED | write-once artifact, counts beside every rate, ordered keys, `accounting: null` ×12, live module digests, figures allow-listed |
| FRONT-04 | 25-02, 25-18, 25-19, 25-21, 25-22 | SATISFIED | 38/38 live re-derivation through the import route; the null named (`empty_frontier_reached`, `candidates: []`). Its row discloses the weaker existential form (0 of 32 + 0 of 6 with 6 refused, not 0 of 44) in its own words — the criterion's own sentence is about DP points and is answered in full at both capacities |
| ADVT-01 | 25-04, 25-11, 25-12, 25-16, 25-17, 25-20 | SATISFIED | 12 trained adversarial adapters, digests recomputed from bytes; closes Phase 24's deferred half |
| RPT-02 | 25-07, 25-20 | SATISFIED | correction sweeps routed through `_prose.normalized` in `tests/test_phase25_correction.py` and `tests/test_phase25_close.py` |

**Orphans:** none. Every ID on a 25-*-PLAN `requirements:` line is on the ROADMAP's Phase 25
Requirements line, and every one is ticked with a traceability row naming artifact fields and guard
tests. `RPT-03` is not in any Phase-25 plan and maps to Phase 28 in the traceability table — out of
scope here, and `pyproject.toml` is byte-unchanged anyway.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `tests/test_phase25_close.py` | 15 | the token `TBD` | INFO | Inside a docstring quoting an assertion-error message about an unfilled ROADMAP row template. Not a debt marker. |
| `results/phase25_frontier.json` | `mechanism_pin_disclosure.governs` | a published sentence contradicting the code it describes | WARNING | See human item 2 — WR-03, independently confirmed |
| `scripts/phase25_promotion.py` | `curve_pass` | `except SystemExit` catching everything | WARNING | WR-02: a structural bug would be recorded as six REFUSED verdicts. Today's six are genuine (reproduced live). |

No `FIXME`/`XXX`, no stub returns, no placeholder rendering, no hardcoded-empty props anywhere in
the phase's scripts or tests.

### Findings the phase recorded honestly, which I checked and accept as NOT gaps

Each of these was decided by an operator, recorded before the affected result was seen or on a
pre-registered principle, and is guarded by a test that fires live:

1. **44/44 as pinned with 2 jetsam kills and 3 one-stage halts, all resumed as the same attempt.**
   Every one of the 44 records has exactly one add-commit and one path — I scanned all 44. D-10's
   one-attempt unit is the point, and no reading had landed at either kill.
2. **D-25-18-RECALL — condition (b) had no per-point producer; 42 adapters re-scored after the
   sweep.** Not a selection effect: the adapters are frozen and hash to their records (verified),
   ALL 42 were scored, never a subset, with the controls' own instrument, before any verdict was
   seen. 44/44 readings pin to the frontier's digests.
3. **D-25-18-ADV64-REFUSED — nothing borrowed.** The refusal comes from the imported route, not
   from a plan; I fired it live. Option B (borrowing the DP n=64 control) was rejected on
   pre-registered D-16/D-47. Condition (a) fails on all six regardless (3–66 of 416, every Wilson
   upper bound above X), so no feeding choice could have moved the existential.
4. **The frontier is empty as a REACHED branch.** `empty_frontier_reached: true`, tallies summing to
   44, existentials with denominators. This is the pre-registered null being named, which is exactly
   what the goal asks for.

### Human Verification Required

**1. CI has never run any of this phase's code.**
`main` is **95 commits ahead of `origin/main`**; the newest `origin/main` commit is `15dce85`
(2026-09-02). `tests/test_phase25_venue.py:238` pins the ubuntu skip count as `52 + 3 + 7 = 62`,
labelled **DERIVED, NOT MEASURED** in the file itself. Push and confirm green; replace the derived
literal with the measured one if they differ. The parallel CR-01 fix (currently editing
`tests/test_phase25_recall.py`, `tests/test_phase25_promotion.py`, `scripts/phase25_promotion.py`,
`scripts/phase25_recall.py`) must land first.

**2. `mechanism_pin_disclosure.governs` contradicts the code, inside the write-once artifact.**
The published sentence says the lot is re-derived "for all 44 points" as
`batch_size x max(1, grad_accum_steps)`. The code applies that formula only on the adversarial arm.
On `dp_n8_sigma0p000000` the sentence's formula gives `8 x 8 = 64`; `records_per_lot` is `8`
(`n_facts`). `lot_rule_by_arm` immediately beside it is correct for both arms, so the artifact
disagrees with itself. **No verdict, count, ε or Success Criterion is affected.** Because the
artifact is write-once and downstream-pinned, the repair is a decision: a sanctioned
delete-in-its-own-commit re-assembly, or the discrepancy recorded in
`results/phase25_operational_note.md`. Neither has been done and there is no deferred-items entry.

**3. The adversarial arm's no-replay recipe has no owning phase.**
Condition (c) fails on all 12 adversarial points for the recipe, not the ratio, and at n=64 the
arm's own ratio-0 control scored held-out **0/648** — which is what the route refused on.
`deferred-items.md` hands "a replay-bearing adversarial recipe" to "a later phase" and names none;
Phase 26 (canary), 27 (relearning) and 28 (report) carry no goal or success criterion covering it.
Decide before Phase 28 publishes: give it a phase, or scope the report to publish the adversarial
arm as explicitly recipe-confounded.

### Gaps Summary

**None.** No must-have failed, no artifact is missing or stubbed, no key link is unwired, and no
blocker anti-pattern exists. The phase goal — both arms on one plane at both capacities, judged by
importing Phase 20's rule, with the null named — is achieved in the codebase, and the parts most
likely to have been narrated rather than built (the verdict route, the adapter provenance, the
recall pins, the module digests, the machine revert, the figures) were re-derived or re-read from
bytes by this verifier rather than accepted from any SUMMARY.

The status is `human_needed`, not `passed`, only because of the three items above: a CI run this
verifier cannot perform, a write-once artifact whose repair route is a developer's choice, and a
scientific follow-up with no owner.

---

_Verified: 2026-09-09T21:40:00Z_
_Verifier: Claude (gsd-verifier), goal-backward, FORCE stance_
