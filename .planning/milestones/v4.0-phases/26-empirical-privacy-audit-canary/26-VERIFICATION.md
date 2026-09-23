---
phase: 26-empirical-privacy-audit-canary
verified: 2026-09-13T22:30:00Z
head: 0e013c8
status: passed
score: 3/3 ROADMAP Success Criteria verified; 24/24 PLAN must-have truths verified
overrides_applied: 0
requirements_accounted: 2/2 (CANARY-01, CANARY-02) — no orphaned IDs
re_verification: false
verifier_ran:
  - "env -u PERSONACORE_SWEEP_ACTIVE .venv/bin/pytest -q tests/test_phase26_prereg.py tests/test_phase26_canary.py tests/test_phase25_close.py -x -> 69 passed in 3.58s (0 skipped)"
  - "the same two phase-26 files under -v: 43/43 PASSED by name, including test_the_live_path_is_wired_end_to_end, test_emit_refuses_a_partial_audit (both sub-cases ran on this host), test_the_power_gate_goes_red_on_a_forged_pass, test_the_sibling_is_pinned_to_the_frontier_both_ways, test_every_point_carries_its_reasons_and_the_ceiling_disclosure, test_the_control_reproduced_the_published_reading, and the two ancestry guards"
  - "sha256(results/phase25_frontier.json on disk) == artifact.frontier_sha256 (True); 16/16 points[k].adapter_sha256 == frontier's (0 mismatches); 16/16 sidecar adapter_sha256 == artifact's; OFF sidecar base_sha256 == artifact base_sha256 (checkpoints/convbase_slim.pt)"
  - "sha256(scripts/phase26_prereg.py on disk) == artifact.prereg_module_sha256 (True)"
  - "every fact_unit reading (epsilon_lower, direction_1, direction_2, tpr_lb, fpr_ub, degenerate) re-derived LIVE via phase26_prereg.epsilon_lower from the artifact's own counts -> 0 mismatches over 16 points; all 15 noised verdicts re-derived via phase26_prereg.point_verdict -> 0 mismatches"
  - "member flags re-derived from the raw sidecars: member == (answered_questions > 0) holds for every fact in every tier of all 16 sidecars (0 inconsistencies); OFF sidecar answered 0 in all four tiers, so exclusions 0/56 and 0/8 are the raw truth, not a default"
  - "control sidecar in_taught k/n = 790/1008 (matches the log line and the frontier); reproduction_gate {expected [790,1008], observed [790,1008], passed True} in both the sidecar and the artifact"
  - "auditor_ceiling recomputed = 2.7858978325772576 (==); power threshold recomputed = 0.6339783761989397 == frontier dp_n8_sigma80p000000.epsilon == accountant.epsilon_for(80.0, 200, mitigation_unit.DELTA)"
  - "power_gate.sentence == phase26_prereg.POWER_SENTENCE (True); VERDICTS == ('BROKEN','CONSISTENT','INCONCLUSIVE'); point_verdict on a forged epsilon_lower=5.0 vs 0.634 returns BROKEN; with power.passed=False returns INCONCLUSIVE"
  - "git: results/phase26_canary.json has exactly one commit, 8652c15, author Rafael <rafael.d.cooelho@gmail.com>, 1 file changed (the artifact alone); working tree bytes == HEAD bytes; results/phase25_frontier.json exactly one commit (4030d0e); scripts/phase26_prereg.py exactly one commit (e6a8851, 2026-09-10); git ls-tree e6a8851 results/ shows 0 phase26 files; merge-base --is-ancestor e6a8851 -> 4c01c43 (note first-add) OK and -> 8652c15 OK; git diff 4030d0e..HEAD -- scripts/phase25_prereg.py empty"
  - "data/phase26_canary_*.json: 17 files (OFF + 16), git ls-files data/ | grep phase26 -> 0, .gitignore:17 'data/' covers them"
  - "launchctl list | grep -i phase26 -> empty (exit 1); no phase26_canary process; no caffeinate -dims (only the unrelated pid 15665 -s -i -w 7584 and the harness's -i -t 300); heartbeat last line stage 'done' at 2026-09-12T23:07:28Z; logs/phase26_canary.out tail is the sigma=80 point"
  - "results/phase26_operational_note.md: 958 lines, headings ## 1..## 8 present, '## 8. The close — 2026-09-13' with 8.1-8.9; _NOTE_REQUIRED_BLOCKS has 7 entries incl. '## 8. The close'"
  - "artifacts/com.personacore.phase26.canary.plist: plutil -lint OK; KeepAlive false, RunAtLoad false, caffeinate -dims, PERSONACORE_SWEEP_ACTIVE=1"
  - "scripts/phase26_canary.py: no top-level torch import, no torch.load, the only 'git' token is in a docstring saying the driver builds no git argv"
warnings:
  - "INFO: the run took 30 h 43 min against the note's ~25 h budget (sigma=50 at 7402 s, sigma=80 at 19390 s, outside the 3.4-4.3 s/question band). Recorded in note 8.2 with 'cause not measured, not claimed'. No criterion bounds the wall-clock; the sidecars carry the measured scoring_seconds."
  - "INFO: note 8.8(b) reports four idle Phase-25 LaunchAgents (sweep, recall, rehearsal, n64floor) loaded with runs = 0 — re-loaded by something outside this phase, inert by their committed plists (RunAtLoad/KeepAlive false). Not a Phase-26 obligation; named for the operator, not booted out. Nothing phase26 is loaded (verified live)."
  - "INFO: scripts/phase26_prereg.py:347 contains the word 'placeholder' inside a comment explaining that the Phase-25 note does NOT carry a pending placeholder — not a stub marker."
  - "INFO (SC1 wording): the ROADMAP SC1 says 'questions as the unit of analysis rather than draws'. CONTEXT D-10 fixes the FACT as the deciding unit (the privacy unit) with the question unit REPORTED beside it, and draws never a unit. The artifact carries both fact_unit (decides) and question_unit (reported) per point. Verified as the CONTEXT resolved it."
---

# Phase 26: Empirical Privacy Audit (Canary) — Verification Report

**Phase Goal:** Test the guarantee rather than the code — the strongest available answer to "how do
you know your from-scratch DP-SGD is correct?": an empirical lower bound on epsilon against the
accountant's claimed upper bound, under a rule committed before the audit ran, published whichever
way it came out, travelling with the frontier.
**Verified:** 2026-09-13T22:30:00Z at HEAD `0e013c8` (branch main)
**Status:** passed — 3/3 Success Criteria, 24/24 plan truths, 2/2 requirements
**Re-verification:** No — initial verification

Starting hypothesis was "tasks completed, goal missed". Every SUMMARY claim was re-measured against
the repository, the raw gitignored sidecars, git history and the live machine; none was accepted on
report. The hypothesis was falsified on every truth.

## Goal Achievement

### Observable Truths — ROADMAP Success Criteria

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| SC1 | One-run canary auditing produces an empirical lower bound on epsilon for a published DP point, built additively on the existing fixture / scorer / Wilson bound / draw budget — no new instrument; questions (never draws) as a unit | VERIFIED | `results/phase26_canary.json` carries `fact_unit.epsilon_lower` and `question_unit.epsilon_lower` for all 16 points, computed from `phase20_gate_coverage.wilson_lower_bound` and `erasure_gate.wilson_upper_bound` (imported, `scripts/phase26_prereg.py:245-246`) at `delta = mitigation_unit.DELTA`, `z = erasure_gate._Z_ONE_SIDED_95`. Instrument string = `phase14_recall.complete_question + phase14_recall.score_question`; `pr.complete_question(..., index=index)` at `scripts/phase26_canary.py:175`; IN items equal `calibration_items` exactly (`test_in_items_equal_calibration_items_exactly` PASSED); OUT rendered through the filler grammar at 784/504 questions (`test_out_items_render_through_the_filler_grammar` PASSED); 9 draws per question, 1008 IN taught draws per point (sidecar `n = 1008`). Every reading re-derived live through `phase26_prereg.epsilon_lower` from the counts: 0 mismatches. Control reads eps_lower 2.7859 (8/8 members, 0/56 nonmembers); every noised point reads -0.0472 with `direction 1 undefined` NAMED, not clipped. |
| SC2 | The rule "eps_lower > eps_upper => provably broken" is committed before the audit runs, no room for a favourable reading afterward, and the comparison is executed and published whichever way it comes out | VERIFIED | `scripts/phase26_prereg.py` has exactly ONE commit `e6a8851` (2026-09-10); `git ls-tree e6a8851 results/` holds 0 phase26 files; both tracked `results/phase26_*` first-adds (`4c01c43` note, `8652c15` artifact) are strict descendants (`merge-base --is-ancestor` OK both; the guard also refuses same-commit). `RULE` is `phase25_prereg.CANARY_RESERVATIONS["audit_target_rule"]` by identity (`is`), and `scripts/phase25_prereg.py` is byte-identical since the frontier (`git diff 4030d0e..HEAD` empty). `VERDICTS == ('BROKEN','CONSISTENT','INCONCLUSIVE')`; live probe: forged eps_lower 5.0 vs 0.634 -> BROKEN; power failed -> INCONCLUSIVE. Published: `summary {BROKEN 0, CONSISTENT 15, INCONCLUSIVE 0}`, `reachable_claims 4/15`, 11 points carry `epsilon_upper >= auditor_ceiling: this comparison could not have failed` in `reasons`, the 4 reachable (sigma 24/32/50/80) do not; every CONSISTENT reason says `this test can only accuse; CONSISTENT is not 'verified correct'`. All 15 verdicts re-derived live through `point_verdict`: 0 mismatches. |
| SC3 | The verdict travels WITH the frontier artifact; if the audit is ever cut, that is a named limitation under D-16, not silence | VERIFIED | Sibling in the same directory: `results/phase26_canary.json` beside `results/phase25_frontier.json`. `frontier_sha256` == sha256 of the frontier bytes on disk (True, 22,311,714 bytes); 16/16 `adapter_sha256` equal the frontier's; frontier still at ONE commit (`4030d0e`), never re-emitted (WR-03). `test_the_sibling_is_pinned_to_the_frontier_both_ways` PASSED in its present state. Cut-audit path is real: `emit()` refuses without the OFF sidecar or with any of the 16 point sidecars missing, naming `results/phase26_operational_note.md` (`scripts/phase26_canary.py` emit, `test_emit_refuses_a_partial_audit` PASSED — both the empty and the 15-of-16 sub-cases ran on this host); `PUBLICATION_OBLIGATION_CONTINUATION[-1]` binds Phase 28 to say "audit not executed / partial" beside every epsilon if the artifact is absent. Branch A was taken so no D-19 entry was needed; note 7 says so explicitly rather than staying silent. |

**Score:** 3/3 Success Criteria verified

### Observable Truths — PLAN frontmatter must-haves (merged, deduplicated against the SCs)

| # | Plan | Truth | Status | Evidence |
|---|------|-------|--------|----------|
| 1 | 26-01 | Committed rule resolves to `dp_n8_sigma0p000000`; extension names all 15 noised dp_n8 in `point_keys` order | VERIFIED | `resolved_target` in artifact == CONTROL_KEY; `audited_point_keys` (16, control first) == `phase26_prereg.audited_point_keys(frontier)` (True); tests `test_the_committed_rule_resolves_to_the_control`, `test_the_extension_is_all_fifteen_in_point_keys_order` PASSED |
| 2 | 26-01 | `epsilon_lower` reproduces the six hand-computed rows from the two IMPORTED Wilson bounds; degenerate cases named | VERIFIED | six parametrizations of `test_epsilon_lower_matches_the_hand_computed_table` PASSED; `test_zero_members_names_direction_one_undefined`, `test_all_nonmembers_names_direction_two_undefined` PASSED; artifact's noised points carry `degenerate: ['TPR_lb <= delta: direction 1 undefined']` |
| 3 | 26-01 | Each noised point compared to its OWN epsilon at delta 1e-5; curve total beside it, never the comparator | VERIFIED | `points[k].epsilon_upper == frontier points[k].epsilon` for all 16 (0 mismatches); `curve_total_epsilon` + `curve_total_is_context_only` at the top level; `epsilon_sentence` per point asserted equal to the frontier's `epsilon_report.rendered[k]` at emit |
| 4 | 26-01 | Power threshold derived from the artifact = sigma 80 record = `epsilon_for(80.0, 200, DELTA)` | VERIFIED | all three equal 0.6339783761989397 (recomputed live) |
| 5 | 26-01 | Verdict domain exactly three-valued, one-sided, reasons with numbers and the D-13 ceiling clause | VERIFIED | see SC2; `test_verdict_domain_is_three_valued_and_one_sided` PASSED |
| 6 | 26-01 | Deciding tier, exclusion scope, membership rule, waiver continuation are module constants with rationale | VERIFIED | `DECIDING_TIER='taught'`, `EXCLUSION_SCOPE='either'`, `MEMBERSHIP_RULE` (D-14 text), `WAIVER_CONTINUATION` (supersedes `phase21_filler.GUESSABILITY_WAIVER`, dated 2026-09-10), all travel in the artifact; `test_the_continuations_are_data` PASSED |
| 7 | 26-01 | Every prereg commit precedes every tracked phase26 result first-add; phase25_prereg byte-identical since the frontier | VERIFIED | see SC2; ancestry arithmetic checked 2 == 1 prereg commit x 2 tracked artifacts |
| 8 | 26-02 | One instrument scores IN (8) and OUT (56) with imported `complete_question`/`score_question`, same enumerate index | VERIFIED | sidecar per_fact sizes 8/8/56/56 in all four tiers of all 17 sidecars; `pr.complete_question(..., index=index)` line 175; `score_question` real (not stubbed) in the wiring test |
| 9 | 26-02 | OFF arm measured ONCE on the sha256-pinned base; every sidecar pinned to the frontier's adapter hash and reused only on match | VERIFIED | one `data/phase26_canary_off.json` with `base_sha256` == artifact's; emit re-hashes the base on disk (T-26-07); `test_a_matching_sidecar_is_reused`, `test_a_sidecar_for_a_different_adapter_is_refused` PASSED |
| 10 | 26-02 | At the control the IN-taught sum is routed through `prove_reproduction` before the sidecar is written | VERIFIED | `phase25_prereg.prove_reproduction(k, n)` at `scripts/phase26_canary.py:369`; control sidecar `reproduction_gate.observed == [790, 1008]`; `test_the_control_routes_its_in_taught_sum_through_prove_reproduction` PASSED |
| 11 | 26-02 | `emit()` refuses unless OFF + 16 sidecars exist; exclusions, ceiling, power gate computed BEFORE any verdict; write-once; names the note when refusing | VERIFIED | read the emit body: order is write-once guard -> OFF present + base re-hash -> missing keys (names the note) -> per-sidecar hash -> `_exclusions` (4) -> `auditor_ceiling` (5) -> readings (6) -> `power_gate` (7) -> verdicts (8-9); `test_emit_refuses_to_overwrite_the_committed_artifact` PASSED against the real committed artifact |
| 12 | 26-02 | Driver builds no git argv; plist mirrors the recall agent | VERIFIED | `test_the_driver_never_commits`, `test_the_canary_agent_mirrors_the_recall_agent`, `test_the_canary_agent_plist_lints` PASSED; plist read: caffeinate -dims, KeepAlive false, RunAtLoad false, `PERSONACORE_SWEEP_ACTIVE=1` |
| 13 | 26-03 | Items builder equals `calibration_items` on LOCKED_FACTS; OUT through the filler grammar at 784/504 | VERIFIED | tests PASSED (row 8) |
| 14 | 26-03 | Dry-run and reuse paths never import torch; no top-level torch import; no `torch.load` | VERIFIED | grep: none; `test_the_driver_imports_no_torch_touching_module_at_top_level`, `test_the_driver_never_calls_torch_load_directly`, `test_the_dry_run_walks_off_and_sixteen_and_never_imports_torch` PASSED |
| 15 | 26-03 | Sidecar reuse only on hash match; partial set refuses naming the note; forged power-gate pass goes RED on a copy | VERIFIED | `test_the_power_gate_goes_red_on_a_forged_pass` PASSED plus rows 9, 11 |
| 16 | 26-03 | LIVE path wired: `main(argv)` -> `score_off_once` -> `score_point` -> `emit` on stubbed draws, real producer records accepted by the consumer, control sum reaches `prove_reproduction` | VERIFIED | read the test body: `canary.main([--points control sigma80 --heartbeat ...])` with only `load_adapted_model`/`complete_question` stubbed; asserts 8/112, 8/72, 56/784, 56/504 shapes on OFF/control/producer sidecars, `recorded == [(0, 1008)]`, then `canary.emit()` on 16 records. PASSED, not skipped |
| 17 | 26-03 | Sibling artifact pinned both ways; frontier at one commit | VERIFIED | SC3 |
| 18 | 26-04 | Note's first-add descends from every prereg commit; 0 tracked phase26 results at the prereg commit | VERIFIED | `4c01c43` descends from `e6a8851`; ls-tree at `e6a8851` -> 0 |
| 19 | 26-04 | Launch posture recorded before any MPS second (owners, pmset, ~25 h budget, wiring proof on host, plist installed, sweep flag) | VERIFIED | note 1-5 present with quoted outputs; `## 5. The launch record — 2026-09-11`; `~/Library/LaunchAgents/com.personacore.phase26.canary.plist` present (installed copy, untracked by design) |
| 20 | 26-04 | Run started by `launchctl kickstart`; early-run gate (OFF sidecar, refusal on real records naming 15 missing keys, control 790/1008) observed and operator-approved | VERIFIED (outcome) | the checkpoint itself was the operator's, consumed inside the phase (approved 2026-09-11T18:34:58Z per SUMMARY/note 6). Its OUTCOMES are observable now: OFF sidecar dated 11 set 14:39, control sidecar 15:32 with the reproduction gate passed, note 6 quoting the refusal, heartbeat trail ending `done` |
| 21 | 26-05 | Artifact assembled ONLY with OFF + 16 sidecars; else a dated D-19 entry and no artifact | VERIFIED | 17 sidecars on disk; `emitted_utc 2026-09-13T17:39:11Z` after the `done` beat 2026-09-12T23:07:28Z; refusal path proven by test (row 11) |
| 22 | 26-05 | Artifact carries frontier sha, 16 adapter hashes, ceiling, reachable k/15, power gate with sentence, exclusions n/56, three-valued verdict with reasons per noised point | VERIFIED | all fields present and re-derived (SC1-SC3 rows) |
| 23 | 26-05 | Artifact committed by the OPERATOR by hand; driver never commits; frontier at one commit | VERIFIED | `8652c15` author Rafael, `1 file changed, 1 insertion(+)` — the artifact alone; `emitted_git_sha c4a5511` (the tree at emit) differs from the commit that added it, consistent with a hand commit after emit; frontier one commit |
| 24 | 26-05 | Machine put back: agent booted out, `launchctl list` empty of phase26, assertion owners quoted | VERIFIED (live) | `launchctl list \| grep -i phase26` empty; no driver process; no `-dims` caffeinate; note 8.8 quotes bootout, pmset by pid and the caffeinate ps |

**Score:** 24/24 plan truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/phase26_prereg.py` | dated continuation, >= 200 lines, 20 named exports | VERIFIED | 395 lines, one commit `e6a8851`; every export in the plan list imported and exercised by the driver and tests; sha256 pinned into the artifact and matches disk |
| `tests/test_phase26_prereg.py` | ancestry guards, resolution, extension, threshold, formula table, degenerate cases, verdict domain, continuation data; >= 150 lines | VERIFIED | 259 lines, 17 tests PASSED |
| `scripts/phase26_canary.py` | driver with `_items`, `_score_list`, `score_off_once`, `score_point`, `emit`, `build_parser`, `main`; >= 250 lines | VERIFIED | 653 lines; wired end-to-end (row 16); produced the 17 real sidecars and the committed artifact |
| `artifacts/com.personacore.phase26.canary.plist` | LaunchAgent, contains label | VERIFIED | `plutil -lint` OK; label present; mirrors the recall agent |
| `tests/test_phase26_canary.py` | CPU tests incl. wiring proof, plist, link, power-gate RED; >= 250 lines | VERIFIED | 675 lines, 26 tests PASSED (incl. 7 note-heading parametrizations) |
| `results/phase26_operational_note.md` | contains `## 5. The launch record` and `## 8.` | VERIFIED | 958 lines; 1-8 present; 7 "Nothing pending"; 8.1-8.9 quoted outputs |
| `results/phase26_canary.json` | sibling verdict artifact, contains `frontier_sha256` | VERIFIED | 165,830 bytes, tracked at one commit by the operator, all fields re-derived |
| `data/phase26_canary_*.json` (17) | gitignored sidecars | VERIFIED | 17 present, 0 tracked, `.gitignore:17 data/` |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `phase26_prereg.py` | `phase25_prereg.py` | `RULE = CANARY_RESERVATIONS["audit_target_rule"]` by reference | WIRED | line 79; test asserts identity with `is` |
| `phase26_prereg.py` | `erasure_gate` / `phase20_gate_coverage` | Wilson bounds imported | WIRED | lines 245-246 |
| `tests/test_phase26_prereg.py` | git history | `merge-base --is-ancestor`, earliest add, strictly-after | WIRED | read the guard body; refuses same-commit and shallow clones |
| `phase26_canary.py` | `phase26_prereg.py` | `audited_point_keys` / `auditor_ceiling` / `power_gate` / `point_verdict` | WIRED | lines 112, 449, 503, 520, 563 |
| `phase26_canary.py` | `phase14_recall` | `pr.complete_question(..., index=index)` lazily | WIRED | line 175 |
| `phase26_canary.py` | `phase25_run` | `atomic_write_json` / `beat` / `start_heartbeat` / `device` CALLED | WIRED | lines 269-377 |
| `phase26_canary.py` | `phase25_prereg` | `prove_reproduction` at the control; `point_record_path` charset | WIRED | lines 95, 369 |
| `tests/test_phase26_canary.py` | `phase26_canary.main` | live `main([...])` with monkeypatched loader/completer | WIRED | row 16 |
| `results/phase26_canary.json` | `results/phase25_frontier.json` | `frontier_sha256`, 16 `adapter_sha256` | WIRED | verified by hash on disk, both directions |
| `results/phase26_operational_note.md` | `tests/test_phase26_canary.py` | `_NOTE_REQUIRED_BLOCKS` | WIRED | 7 headings pinned, 7 PASSED |
| `launchctl` | `phase26_canary.py` | kickstart -> caffeinate -dims -> driver | WIRED (consumed) | ran 2026-09-11T16:23:57Z to 2026-09-12T23:07:28Z; booted out; nothing loaded now |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `results/phase26_canary.json` | `points[k].fact_unit` / `question_unit` | `_readings` over `data/phase26_canary_<k>.json` `per_fact` | Yes — raw per-fact/per-question counts from 16 real MPS runs (control 790/1008; log lines match sidecar k/n) | FLOWING |
| `results/phase26_canary.json` | `exclusions` | `_exclusions` over the OFF sidecar | Yes — OFF answered 0 in all tiers, so 0/56 is measured, not defaulted | FLOWING |
| `results/phase26_canary.json` | `power_gate` | control `fact_unit.epsilon_lower` vs `power_threshold(frontier)` | Yes — 2.7859 vs 0.6340 | FLOWING |
| `results/phase26_canary.json` | `verdict` x15 | `point_verdict(reading, epsilon_upper, power, ceiling)` | Yes — re-derived 15/15 | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Quick phase gate | `env -u PERSONACORE_SWEEP_ACTIVE .venv/bin/pytest -q tests/test_phase26_prereg.py tests/test_phase26_canary.py tests/test_phase25_close.py -x` | 69 passed in 3.58s | PASS |
| Verdict domain can accuse | `point_verdict({...epsilon_lower: 5.0}, 0.634, power=passed, ceiling)` | BROKEN | PASS |
| Power gate failure propagates | `point_verdict(reading, 0.634, power={passed: False}, ceiling)` | INCONCLUSIVE | PASS |
| Write-once refusal on the real artifact | `test_emit_refuses_to_overwrite_the_committed_artifact` | PASSED; bytes unchanged | PASS |
| `--emit` re-run | not run (write-once, committed) | n/a | SKIP by instruction |
| `make test` | not re-run (22 min; green at 8652c15: 2792/4/0; later commits touch only docs/planning — confirmed by `git show --stat 5477519 0e013c8`) | n/a | SKIP by instruction |

### Probe Execution

No `scripts/*/tests/probe-*.sh` exist in this repository and no PLAN/SUMMARY names a probe script;
the phase's runnable checks are the pytest files run above.

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| CANARY-01 | 26-01..26-05 | One-run canary auditing produces an empirical lower bound on epsilon, built additively on the Phase 18 fixture, scorer, Wilson bound and draw precedent | SATISFIED | SC1 row; artifact `fact_unit`/`question_unit` per point; bounds imported; instrument = `phase14_recall` calls; readings re-derived 16/16 |
| CANARY-02 | 26-01..26-05 | A rule committed before the audit runs: eps_lower > eps_upper => provably broken, no favourable reading afterward | SATISFIED | SC2 row; one prereg commit strictly before both artifact first-adds; three-valued one-sided domain; published 15 CONSISTENT with the D-13 disclosure on the 11 unreachable |

Orphan check: `grep "Phase 26" .planning/REQUIREMENTS.md` returns only the CANARY-01 and CANARY-02
traceability rows (lines 572-573). No requirement is mapped to Phase 26 that the plans did not claim.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `scripts/phase26_prereg.py` | 347 | word "placeholder" in a comment | INFO | explains why no pending placeholder is required; not a stub |
| — | — | `TBD` / `FIXME` / `XXX` / `TODO` / `HACK` in the four phase files | none | debt-marker gate clear |

### Human Verification Required

None. The phase's two blocking human checkpoints (26-04 early-run gate approval; 26-05 operator
commit of the artifact) were exercised inside the phase and their outcomes are observable in the
repository and on the machine now (sidecar timestamps, `reproduction_gate` in the control sidecar,
commit `8652c15` by the operator, `launchctl` empty). No PLAN carries a `<human-check>` block
deferred to end-of-phase.

### Gaps Summary

No gaps. The phase goal is achieved in the codebase, not only in the summaries:

- The pre-registration is a single commit that every result descends from; the guard is
  non-vacuous (2 tracked artifacts x 1 prereg commit, checked pairwise, same-commit refused).
- The instrument is the existing recall scorer with the existing Wilson bounds; nothing new was
  built as an instrument.
- The 16 raw sidecars are real MPS output (per-question counts sum to the log lines; the control
  reproduced the frontier's 790/1008 through `prove_reproduction`), and every published reading and
  verdict re-derives from them through the frozen prereg functions with zero mismatches.
- The verdict is pinned to the frontier by digest in both directions; the frontier was not touched.
- The honest reading is stated in the artifact itself: at the fact unit the auditor's ceiling is
  2.7859, so only 4 of the 15 claims were reachable, and with 0/8 members answered at every noised
  point the instrument had nothing to accuse with. CONSISTENT means "not contradicted".

---

_Verified: 2026-09-13T22:30:00Z_
_Verifier: Claude (gsd-verifier)_
