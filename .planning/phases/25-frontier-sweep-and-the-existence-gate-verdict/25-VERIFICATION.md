---
phase: 25-frontier-sweep-and-the-existence-gate-verdict
verified: 2026-09-09T21:40:00Z
head: 795edb3
status: passed
score: 7/7 must-haves verified (5 ROADMAP Success Criteria + ADVT-01 + RPT-02)
human_items_closed: 3/3 (re-checked 2026-09-09T22:15:00Z at HEAD 5b4159b)
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
  - "RE-CHECK: the two epsilon platform twins measured at exactly 4 ULP (rel 8.3e-16); epsilon_agrees accepts pin and twin, rejects a 1e-9 perturbation; published epsilons and the write-once artifact unchanged"
  - "RE-CHECK: MECHANISM_PIN_DISCLOSURE_GOVERNS_AS_PUBLISHED is byte-equal to the artifact; the corrected constant names both arms' rules; record_module_sha256 verified against the blob at provenance.git_sha and confirmed to differ from live, so the digest test is not vacuous"
  - "RE-CHECK: 38/38 verdicts re-derived live AGAIN after the WR-01/WR-02/WR-03 edits to phase25_promotion.py and phase25_record.py — still 0 mismatches; 640 passed, 3 skipped across the six touched test files"
human_verification_resolved:  # all three closed 2026-09-09; re-checked by this verifier, not accepted on report
  - item: "CI has never run any of this phase's code"
    closed_by: "Actions 34403612853 (first run ever on waves 10-13) -> ce2a151 -> Actions 34406246073 green"
    verified: "gh run list confirms failure on 52e736c then success on ce2a151; the log lines read `8 failed, 2682 passed, 62 skipped` and `2691 passed, 62 skipped, 9 warnings in 1245.48s`. main == origin/main, 0 ahead. The DERIVED ubuntu pin of 62 was exactly right and its literals are unchanged; the comment is now a MEASURED dated continuation carrying both run ids (5b4159b)."
    residual: "The green run is on ce2a151. HEAD 5b4159b changes only comment prose in tests/test_phase25_venue.py (I diffed it: the four pinned literals are untouched) plus one UAT line; its run 34408344901 was in_progress at re-check time. No executable difference between the green tree and HEAD."
  - item: "mechanism_pin_disclosure.governs contradicts the code"
    closed_by: "75b86a6 + 52e736c — operator decision: record it, do not re-emit"
    verified: "MECHANISM_PIN_DISCLOSURE_GOVERNS_AS_PUBLISHED == the artifact's bytes (True); MECHANISM_PIN_DISCLOSURE_GOVERNS now names n_facts on DP and batch_size x max(1, grad_accum_steps) on adversarial and points at lot_rule_by_arm; the refusal message prints LOT_RULE_BY_ARM[rule] (scripts/phase25_record.py:1610); note 13.8 records the discrepancy; deferred-items D-25-REVIEW-WR03 marked resolved-by-decision. The consequence was handled honestly: all four recorded digests are asserted against the blob at provenance.git_sha (578a1ac) and the three ancestry-guarded modules are still asserted byte-identical LIVE. I confirmed the emitter digest matches the blob at the write and differs from the working tree, so the test is non-vacuous and nothing was weakened for the frozen modules."
    residual: "The 22.3 MB artifact still carries the as-published sentence; the correction reaches a reader through note 13.8 and the deferred entry until a future sanctioned re-assembly. That is the decision, executed."
  - item: "the adversarial no-replay recipe has no owning phase"
    closed_by: "875118f — operator decision: both"
    verified: "ROADMAP Phase 28 now carries Success Criterion 4 publishing the arm as explicitly recipe-confounded, naming the no-replay cause, the `7,581 teaching + 0 replay` log line, the six n=64 refusals and the 0/648 control, quoted from note 12.5c and the artifact rather than re-derived. A v5.0 candidate milestone (ROADMAP.md:9) opens the replay-bearing re-run of the 12 points. The debt now has both a publisher and a measurer."
warnings:
  - "25-REVIEW CR-01 (tests/test_phase25_recall.py host-only dependencies): FIXED at 795edb3 and proved by the green ubuntu run — the 7 host-only tests skip rather than fail, which is exactly the +7 the ubuntu pin predicted."
  - "25-REVIEW WR-01 / WR-02: FIXED at cb96d8c (the two CPU artifacts are write-once behind --force; only the coverage route's floor refusal is recorded as a refusal). Superseding my initial reading of both as open."
  - "The eight CI failures are a finding, not a regression: seven were EPSILON_LADDER's two glibc twins reaching comparison sites that had never run off the publication host — which would also have killed the documented Kaggle P100 fallback — and one was a LaunchAgent plist's absolute path. Repaired by recording the twins under exact ==, following the precedent tests/test_phase25_grid.py set in an earlier phase, rather than by the relative tolerance first proposed."
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
**Verified:** 2026-09-09T21:40:00Z at HEAD `795edb3`; human items re-checked 2026-09-09T22:15:00Z at HEAD `5b4159b`
**Status:** passed — 7/7 must-haves verified; all three human items closed and re-checked against the repo
**Re-verification:** No — initial verification, plus a targeted re-check of the three human items

## Goal Achievement

The goal is achieved. The empty frontier is a *reached* branch, not a missing result: I re-derived
every route-reachable verdict myself, live, through the imported frozen gate, and got the committed
strings back exactly — and re-derived them a second time after the WR-01/WR-02/WR-03 edits landed,
still 0 mismatches.

This report was held at `human_needed` for three things a verifier is not entitled to settle: a CI
run that had never happened, a self-contradicting sentence inside a write-once artifact, and an
unowned scientific follow-up. **All three are now closed, and I re-checked each against the repo
rather than accepting the closure report.** The first one paid for itself: the first CI run ever to
execute this code found eight real defects that were invisible on the publication host, including
two epsilon rungs that would have refused to resolve on x86 and taken the documented Kaggle P100
fallback with them. The derived ubuntu skip pin of 62 turned out to be right to the unit.

### Observable Truths

| # | Truth | Status | Evidence (verified by me, not read from SUMMARY) |
|---|-------|--------|---------------------------------------------------|
| 1 | **SC1 / CTRL-01+02** — the retrained unmitigated control runs first, as a sweep point differing from every DP point by exactly the two DP parameters, with its non-bit-identity recorded in advance | VERIFIED | `git log --diff-filter=A` on the 44 records: `dp_n8_sigma0p000000` (`359a6fc`) and `dp_n64_sigma0p000000` (`e444a95`) are commits 1 and 2 of 44. The record's `reproduction_gate` = `{expected [790,1008], observed [790,1008], passed true, comparison "hard == on integer counts"}`. `clip_norm 1000000.0`, `sigma 0.0`, `clip_bind_count 0`, `epsilon null`. Taught 790/1008 (rate 0.7837301587301587 = the Phase 23 matched control exactly), held-out 346/648. Non-bit-identity pre-recorded as a bound, not discovered: `results/phase25_probe2_tensors.json` `agreement_bound` 0.182184 (n=8) / 0.034454 (n=64) under `agreement_bound_governs` "BOUNDED DISAGREEMENT, NEVER EQUALITY". D-04's tripwire is real: `tests/test_phase25_prereg.py::test_the_bit_identity_tripwire_fires_on_a_planted_violation` passes. |
| 2 | **SC2 / FRONT-01** — both arms carry a full curve at both capacities, reconnecting to the control at σ→0 and reaching the floor, with the extremes run first | VERIFIED | `arms` = `[dp_n8, dp_n64, adv_n8, adv_n64]`; 44 points = 2×16 + 2×6; `axis_for_arm` = sigma/sigma/ratio/ratio. Commit order is controls → the eight extremes (`dp_n8_sigma80`, `adv_n8_ratio0`, `dp_n64_sigma80`, `adv_n64_ratio0`, both `ratio1p909091`) → the 36 interior, so an empty frontier was reachable in two runs as designed. σ=80 lands on the floor at both capacities (extraction 0/416, taught 0/1008); σ=0 is the control (790/1008, 87/1008). The adversarial arm terminates at the pool ceiling 1.9090909090909092 with `axis_terminus.statement` naming D-19 — the scope continuation the ROADMAP wrote *before* the run, not after. |
| 3 | **SC3 / FRONT-02** — every ε at both granularities with unit, sampler and multiplicity in one sentence; no bare ε outside the helper | VERIFIED | `phase25_epsilon.report_epsilon(*, point_epsilon, curve_total_epsilon, selection_accounted)` — keyword-only, no defaults; omitting two raises `TypeError: missing 2 required keyword-only arguments`; three positionals raise `takes 0 positional arguments`. `epsilon_report.dual_granularity` names FACT-LEVEL as governing and EXAMPLE-LEVEL as the counterfactual in the same sentence with `q = 1.0` and per-step multiplicity 1. `multiplicities` carries both figures (262.9437465865647 pin / 207.0180229382851 artifact rule) with the frozen record's status `RECORDED, NOT RESOLVED` verbatim. 32 rendered strings, each re-rendered by a live call in `tests/test_phase25_frontier.py`. Curve total 2387.299119573244 over 30 summands at `total_delta` 30×1e-5, `selection_accounted: false` with its reason. |
| 4 | **SC4 / FRONT-03** — the frontier artifact is the single source of truth: counts not rates, per-question successes, ordered keys proved on write, `accounting: null` on the adversarial arm, module sha256s travelling; every figure drawn only from it | VERIFIED (1 warning) | `results/phase25_frontier.json`, 22,311,714 B, ONE commit (`4030d0e`), `git diff --exit-code` clean. `tuple(point_keys) == tuple(phase25_record.ORDERED_POINT_KEYS())` → True on the committed bytes. All 12 `adv_*` points carry `accounting is None`; DP points carry the accounting dict. `gate_module_sha256` `86db4798…` and `budget_module_sha256` `1b35aa88…` both equal sha256 of the live `scripts/mitigation_gate.py` / `mitigation_budget.py`. Every recall block carries `numerator`/`denominator`/`questions` beside its `rate`. `scripts/plot_phase25.py` declares `ALLOWED_READS = (FRONTIER_RECORD,)` and `tests/test_phase25_plots.py` fires that clause on a planted second read (12 passed). **Warning, now resolved by decision:** `mechanism_pin_disclosure.governs` misstates the lot rule for the 32 DP points. Recorded in note 13.8 and corrected in the emitter (`75b86a6`), the artifact deliberately not re-emitted. |
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
| `results/phase25_frontier.json` | `mechanism_pin_disclosure.governs` | a published sentence contradicting the code it describes | RESOLVED BY DECISION | WR-03, independently confirmed by me, then recorded in note 13.8 + the emitter corrected (`75b86a6`) rather than re-emitting 22.3 MB of write-once bytes |
| `scripts/phase25_promotion.py` | `curve_pass` | `except SystemExit` catching everything | FIXED | WR-02, closed at `cb96d8c`: only the coverage route's floor refusal is recorded as a refusal. Today's six were genuine anyway (reproduced live). |

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

### Human Verification — All Three Items Closed

Closed 2026-09-09 and **re-checked against the repo by this verifier**, not accepted on report.
`main == origin/main`, working tree clean, HEAD `5b4159b`.

**1. CI — CLOSED, and it earned its keep.**
`main` was pushed. Actions **34403612853**, the first CI run ever to execute waves 10-13, reported
`8 failed, 2682 passed, 62 skipped`; after `ce2a151`, Actions **34406246073** reported
`2691 passed, 62 skipped, 9 warnings in 1245.48s`, green. I pulled both log lines from `gh` rather
than reading them from the commit message. **The DERIVED ubuntu pin of 62 was exactly right** — 62
derived, 62 measured — and the literals are unchanged; `5b4159b` turns the comment into a MEASURED
dated continuation carrying both run ids.

The eight failures are a finding in their own right, recorded in
`results/phase25_operational_note.md` §13.9:

- **Seven had one cause.** `EPSILON_LADDER` was transcribed on Apple Silicon; on glibc two of its
  fifteen noised rungs return a value 4 ULPs away. I measured both myself: sigma 8.0 pin
  `8.595865790470416` vs twin `…423`, sigma 50.0 pin `1.060789755417757` vs twin `…756` — **exactly
  4 ULP each, relative 8.3e-16**, the other thirteen bit-identical. Because the comparison is exact
  by design, `phase25_points.point_epsilon_and_accounting` refused to resolve the 44 plans on x86 at
  all, which would also have killed the documented Kaggle P100 fallback. The repair follows the
  precedent `tests/test_phase25_grid.py` set in an earlier phase rather than the relative tolerance
  first proposed — an approximate comparison would accept exactly the hand-edited digit these
  assertions exist to refuse. `LADDER_PLATFORM_TWINS` is now a single source in
  `scripts/phase25_epsilon.py` (I checked: no second copy of either literal anywhere in
  `scripts/` or `tests/`), and `epsilon_agrees` returns `pinned == live or TWINS.get(sigma) == live`
  — exact on both branches. I confirmed it accepts the pin and the twin and **rejects a 1e-9
  relative perturbation**, and that an off-ladder rung rejects even 1e-15.
  **No published epsilon changed:** the artifact's sigma-8 and sigma-50 values are still the pinned
  ones, the curve total is still `2387.299119573244`, and `results/phase25_frontier.json` is still
  one commit and `git diff` clean.
- **The eighth** was a LaunchAgent plist's absolute `WorkingDirectory` asserted against this
  checkout's root, split into the half that travels and the half that is host-bound.

*Residual, stated rather than glossed:* the green run is on `ce2a151`. HEAD `5b4159b` changes only
comment prose in `tests/test_phase25_venue.py` — I diffed it, the four pinned literals are
untouched — plus one UAT line; its run `34408344901` was still in progress at re-check time. There
is no executable difference between the green tree and HEAD.

**2. WR-03 — CLOSED by decision: record it, do not re-emit.**
Landed in `75b86a6` + `52e736c`. Verified by me:

- `phase25_record.MECHANISM_PIN_DISCLOSURE_GOVERNS_AS_PUBLISHED` is **byte-equal** to
  `results/phase25_frontier.json::mechanism_pin_disclosure.governs`, so the published sentence is
  pinned as what it is rather than quietly replaced.
- `MECHANISM_PIN_DISCLOSURE_GOVERNS` now reads "BY THE ARM'S RULE — `canary_population.n_facts` on
  the DP arm, `batch_size x max(1, grad_accum_steps)` on the adversarial arm", pointing at
  `lot_rule_by_arm`.
- The per-arm refusal message now prints `LOT_RULE_BY_ARM[{rule!r}]`
  (`scripts/phase25_record.py:1610`) instead of one arm's formula for both.
- Note §13.8 records the discrepancy where a reader of the artifact meets it; `deferred-items.md`
  `D-25-REVIEW-WR03` is marked resolved-by-decision with the earlier "not fixed here" paragraph
  left standing beside it, per this project's retract-in-place doctrine.
- **The consequence was handled honestly, and I checked it rather than trusting it.** The artifact
  pins `provenance.record_module_sha256` — the emitter's own digest — so correcting the emitter made
  a live-match claim false for that one file. `test_both_module_digests_are_live` now asserts all
  four digests against the blob at `provenance.git_sha` (`578a1ac`) **and still asserts the three
  ancestry-guarded modules byte-identical live**. I recomputed: the recorded emitter digest matches
  the blob at the write (`e1b3b380…`) and differs from the working tree (`d9ab85d3…`), so the test
  is non-vacuous, and nothing was weakened for `mitigation_gate.py`, `mitigation_budget.py` or
  `mitigation_unit.py` — the half that would catch a frozen-module edit is intact.

*Residual, and it is the decision working as intended:* the 22.3 MB artifact still carries the
as-published sentence. The correction reaches a reader through note §13.8 and the deferred entry
until a future sanctioned re-assembly.

**3. The no-replay owner — CLOSED both ways.**
`875118f`. ROADMAP **Phase 28 Success Criterion 4** now requires the report to publish the
adversarial arm as explicitly recipe-confounded, naming the no-replay cause (`build_bins` refusing
`replay_ratio > 0` with `adversarial_ratio > 0`), the run's own `7,581 teaching + 0 replay` log
line against the DP arms' 32 replay windows per step, the six n=64 refusals and the **0/648**
control — quoted from note §12.5c and the artifact, never re-derived in prose — and to state that
no conclusion about adversarial ratio is available from v4.0. A **v5.0 candidate milestone**
(`ROADMAP.md:9`) opens the replay-bearing re-run of the 12 points so condition (c) is tested against
the ratio instead of the recipe. The debt now has a publisher and a measurer; it had neither when I
raised it.

**Re-run after all three landed:** `640 passed, 3 skipped` across the six touched test files
(`grid`, `points`, `epsilon`, `frontier`, `interior`, `promotion`), and the load-bearing check
repeated on the edited modules — **38/38 verdicts re-derived live, 0 mismatches**.

### Gaps Summary

**None.** No must-have failed, no artifact is missing or stubbed, no key link is unwired, and no
blocker anti-pattern exists. The phase goal — both arms on one plane at both capacities, judged by
importing Phase 20's rule, with the null named — is achieved in the codebase, and the parts most
likely to have been narrated rather than built (the verdict route, the adapter provenance, the
recall pins, the module digests, the machine revert, the figures) were re-derived or re-read from
bytes by this verifier rather than accepted from any SUMMARY.

The report was held at `human_needed` for three items only: a CI run this verifier could not
perform, a write-once artifact whose repair route was a developer's choice, and a scientific
follow-up with no owner. **All three are closed and re-checked**, so the status is `passed`. The CI
item was worth holding for — it found eight real defects invisible on the publication host, one of
which would have refused to resolve the sweep's own epsilon plan on any x86 machine, and the
project's answer was to record the two 4-ULP libm twins under exact `==` rather than to loosen a
comparison that exists to refuse a hand-edited digit.

---

_Verified: 2026-09-09T21:40:00Z_
_Verifier: Claude (gsd-verifier), goal-backward, FORCE stance_
