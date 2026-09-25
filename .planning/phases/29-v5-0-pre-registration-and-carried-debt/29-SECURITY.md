---
phase: 29
slug: v5-0-pre-registration-and-carried-debt
status: verified
threats_open: 0
asvs_level: 1
created: 2026-09-25
---

# Phase 29 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> Audited at HEAD 72502a5 (review fixes 744165b..49a4e9f included). Every mitigation below was
> located in code and its test run: 97 passed in 4.17 s (`tests/test_phase29_prereg.py`,
> `tests/test_phase29_debt.py`, the four `test_d28_*` tests in `tests/test_phase16_driver.py`,
> `tests/test_phase27_relearn.py::test_a_leg_refuses_an_untracked_record_inside_the_repo`).

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| pre-registration → later phases | Phases 30-34 import keys/paths/recipe/admission from `scripts/phase29_prereg.py`; a post-hoc edit would re-tune after seeing data | frozen experimental contract (integrity-critical) |
| key string → filesystem path | `point_record_path(key)` builds a results path from a key | path component |
| test → real repository | a test writing into the real `results/` pollutes frozen artifacts or starts ancestry clocks | committed evidence files |
| archived planning files → validator | hand edits to milestone archives | frontmatter metadata |
| 16-CONTEXT.md → runtime reader | a silent amendment of a pre-registered note | pre-registered prose |
| v5.0 frontier record → admission | Phase 33 feeds a Phase-32 artifact into `admission()`; malformed/forged must not admit | untrusted JSON record |
| developer ruling → code | the D-15 choice must precede the code that depends on it | decision provenance |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-29-01 | Tampering | scripts/phase29_prereg.py after data exists | mitigate | `ARTIFACT_PATHSPECS` derived from `V5_RESULT_PATHS` (phase29_prereg.py:148-161); `test_phase29_prereg_is_frozen_before_every_v5_result` (test_phase29_prereg.py:109) runs `_assert_frozen_before` (:69-106: shallow-clone refusal, earliest-add, same-commit refusal, `merge-base --is-ancestor`, pair-count check). WR-04 extends it to call-time sources `phase25_record.py`/`phase20_gate_coverage.py` with a natural-RED non-vacuity leg (:130-143). `scripts/_addendum.py` exists. Today 0 tracked `results/phase3[0-4]_*` → honest-zero, guard armed for Phase 30. PASS. | closed |
| T-29-02 | Tampering | re-tune after a refused control (D-14) | mitigate | `POINT_KEYS()` 12 keys (phase29_prereg.py:112-117); `test_no_retry_or_alternate_key_is_exposed` (test:247) scans every public name for non-registered `advr_n*_ratio` strings and retry/alternate/rerun/retune names; `refused_record` proves `control_is_unlearnable` (phase29_prereg.py:238-241) plus WR-02 recipe-value checks against the key's leg (:247-259); `test_refused_record_refuses` (test:396, 14 cases incl. learnable control, n8 recipe on n64 key). Write-once enforcement at write time is Phase 32's (module builds, never writes). PASS. | closed |
| T-29-03 | Tampering | path traversal via key | mitigate | `point_key` refuses non-`advr` arms then delegates to `phase25_record.point_key` (non-finite/negative refusals) (phase29_prereg.py:105-109); `point_record_path` proves `key in POINT_KEYS()` (:144). Tests `test_point_record_path_is_proved_against_the_key_set` (test:180, includes `.../../x`) and `test_keys_refuse_foreign_arms_and_bad_ratios` (test:218, NaN/negative/foreign arm). PASS. | closed |
| T-29-04 | Spoofing | DP reading used as adversarial floor (WR-05) | mitigate | `control_key(leg)` returns `point_key(f"advr_{leg}", RATIO_GRID[0])` (phase29_prereg.py:120-123); `test_keys_are_refused_by_every_v4_parser` (test:206) asserts `phase25_record.parse_point_key` and `phase27_prereg.arm_of` raise on all 12 keys; `test_keys_put_each_legs_control_first` (test:223). PASS. | closed |
| T-29-05 | Tampering | re-typed gate/grid/replay constant | mitigate | By-reference bindings (phase29_prereg.py:90-93, 315-334); `test_constants_are_by_reference` (test:273, `is`); AST guards `test_ast_replay_literal_guard` (:526), `test_ast_grid_retype_guard` (:545), `test_ast_gate_retype_guard` (:561), each planting a tmp_path copy and asserting it fires, then asserting the real file bytes unchanged; D-09 pins `test_d09_pins_are_attribute_references` (:1021). PASS. | closed |
| T-29-06 | Information disclosure | accountant ε leaking into a v5.0 number | mitigate | `test_no_v5_module_uses_the_accountant` (test:581) AST-censuses every `scripts/phase29_*..phase34_*` for `phase25_epsilon` / `personacore.privacy` imports and `epsilon_for/sigma_for/delta_*` names, refuses an empty census, non-vacuity on `phase25_epsilon.py`; transitive load stated in `NAMED_LIMITATIONS["P22-WARNING-4/5"]["transitive_load"]` (phase29_prereg.py:285-289), tested at test:602. PASS. | closed |
| T-29-07 | Tampering | results/phase27_* frozen records during tests | mitigate | `test_a_leg_refuses_an_untracked_record_inside_the_repo` (test_phase27_relearn.py:182-211): scratch git repo, `monkeypatch.setattr(relearn, "_ROOT", scratch)`, sha256 of every tracked `results/phase27_*` before/after, `_real_tree_strays()` before/after, `git status --porcelain -- results/phase27_*` empty, probe path absent in real tree. PASS. | closed |
| T-29-08 | Repudiation | fabricated durations/dates in archived SUMMARYs | mitigate | `test_phase17_summary_frontmatter_validates` (test_phase29_debt.py:43-56) pins top-level `duration`/`completed` equal to nested `metrics:` values and `completed` equal to `git log --follow --diff-filter=A` first-add date; `test_all_eleven_phase17_summaries_are_covered` (:38) pins count 11. PASS (11/11). | closed |
| T-29-09 | Tampering | frontmatter corruption by gsd-sdk mutation handlers | mitigate | `git log --numstat` on commit 5523d50: exactly `2 0` on each of the 11 `17-*-SUMMARY.md` (no other Phase-29 commit touches them); read-only `gsd-sdk query frontmatter.validate --schema summary` re-run at audit: 11/11 `valid:true, missing:[]`. | closed |
| T-29-10 | Tampering | D-28 note in 16-CONTEXT.md | mitigate | `d28_note()` reads the note at runtime (scripts/phase16_persistence.py:2069-2077); `test_d28_note_is_read_verbatim_and_pinned` (test_phase16_driver.py:1845) pins sha256 `171725c6…4210`; `test_d28_amended_note_reddens` (:1868) amends one char on a tmp copy, asserts digest differs and real bytes unchanged. PASS. | closed |
| T-29-11 | Repudiation | published report re-rendered to "fix" history | mitigate | `results/phase16_persistence_report.md` last touched at 127d60d (Phase 16), none in Phase 29; `test_d28_report_absence_is_a_named_limitation` (test_phase16_driver.py:1858) asserts kernel-absent ⇔ `"TD-16-R1-REPORT" in NAMED_LIMITATIONS` and that it is absent; entry at phase29_prereg.py:291-298. PASS. | closed |
| T-29-12 | Tampering | admission decided after the frontier exists | mitigate | Full contract (`admission`, `SCOPE_RULE`, `relearning_scope`, `FRONTIER_SCHEMA`) lives in the ancestry-guarded module (phase29_prereg.py:361-662); same T-29-01 test covers every commit touching it (latest 49a4e9f); no v5.0 result exists yet. PASS. | closed |
| T-29-13 | Spoofing | DP reading sourcing the adversarial threshold | mitigate | `recall_threshold` `_prove(arm == "advr")` and reads only `control_readings[f"advr_{leg}"]` (phase29_prereg.py:388-399); CR-01 wires it into `admission()` via `_own_control_mismatch` (:454). `test_threshold_reads_the_advr_control_and_refuses_dp` (test:935) refuses `dp`/`adversarial`/`adv`, foreign leg, bool count. PASS. | closed |
| T-29-14 | Tampering | malformed/forged frontier admitting a point | mitigate | `admission()` steps 1a-1d (phase29_prereg.py:518-575): non-dict frontier/verdicts (WR-01, :519-522), key-set equality, per-point verdict dict, `_control_readings` count shape, closed verdict domain, reasons type, re-derived tallies, CR-01 own-control check (`_own_control_mismatch` :440-480) — all return INCONCLUSIVE, never raise. `test_admission_inconclusive_takes_precedence` (test:829, 14 forged mutations incl. `verdicts-not-dict`, `maybe-beats-pass`, `tally-beats-pass`) and `test_admission_reads_only_the_legs_own_control` (test:903, 8 CR-01 forgeries: unlearnable-all-fail, unlearnable-one-pass, unlearnable-candidate, PASS graded against dp, readings copied from dp, missing kwargs, bool kwarg, foreign control in REFUSED record). WR-03: `relearning_scope` refuses foreign/duplicate/empty-ADMITTED keys (:649-662), `test_scope_rule_refuses_foreign_or_empty_admitted_keys` (test:983). PASS. | closed |
| T-29-15 | Repudiation | all-refused frontier reported as "mitigation held" | mitigate | Step (4) REFUSED with "could not be measured (not 'the mitigation held')" and per-leg control lines (phase29_prereg.py:611-621); step (5) MOOT names each fully-REFUSED leg (:623-630); `SCOPE_RULE` strings fixed (:637-646). `test_admission_all_refused_does_not_raise` (test:705), `test_admission_mixed_refused_does_not_raise` (test:717), `test_scope_rule_covers_every_verdict` (test:950). PASS. | closed |
| T-29-16 | Elevation of privilege | D-15-dependent code landing before the ruling | mitigate | `git log`: ruling commit 2969994 (20:17:43, touches only 29-04-SUMMARY.md + 29-RESEARCH.md) precedes code commit e44f045 (20:21:01); `git merge-base --is-ancestor 2969994 e44f045` exits 0; no commit touches phase29_prereg.py between f517c58 and e44f045. | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

### Notes (informational, not open)

- T-29-01 / T-29-12 are currently honest-zero: 0 tracked or untracked `results/phase3[0-4]_*` files, so the pair loop checks 0 pairs by design; the guard becomes load-bearing at Phase 30's first results commit. The WR-04 call-time-source test proves the helper can fire (natural RED against v4.0 artifacts).
- T-29-02 write-once enforcement at write time belongs to Phase 32's writer; Phase 29 freezes the key set and the refused-record builder only.

### Unregistered Flags

None. No `## Threat Flags` section in 29-01..29-04-SUMMARY.md.

---

## Accepted Risks Log

No accepted risks.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-25 | 16 | 16 | 0 | gsd-security-auditor (HEAD 72502a5; targeted run 97 passed) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-09-25
