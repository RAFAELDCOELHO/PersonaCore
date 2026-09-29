---
phase: 32
slug: replay-bearing-frontier-re-run-and-verdict
status: verified
threats_open: 0
asvs_level: 1
block_on: high
created: 2026-09-28
---

# Phase 32 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> Register: T-32-01..T-32-31, authored at plan time in the `<threat_model>` blocks of 32-01..32-07-PLAN.md.
> Method: every `mitigate` row was checked against code/tests at HEAD (eee9a95), not against SUMMARY claims.
> Targeted tests run: `tests/test_phase32_points.py tests/test_phase32_frontier.py tests/test_phase30_calibration.py tests/test_phase30_points.py`, 128 passed.
> The full suite was not run, by instruction.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| v4.0 DP control readings -> v5.0 modules | A DP reading passed off as the advr control would falsify ACTRL-01 | control readings (evidence integrity) |
| committed control record -> own_control | The record's declared recipe must match the recipe it trained with | recipe, replay per-step counts |
| unattended driver -> git main | The driver commits for about 23 h with no human in the loop | point records (write-once evidence) |
| stage sidecars (data/, gitignored) -> committed record | Working state becomes evidence at write time | training/replay/session sidecars |
| committed budget -> stop line | The pause threshold is read from another record | stop_line.seconds |
| committed point records -> frontier | The 12 records become the verdicts that Phase 33 admission reads | verdicts, tallies |
| v4.0 frontier -> comparison block | A frozen external record is quoted into a v5.0 claim | v4 verdicts, reasons |
| launchd agent -> repository main | An unattended process holds commit rights | commits |
| developer ruling text -> provenance | Free text ends up in committed records | ruling string |
| crash/restart -> resumed state | Half-finished working state could be promoted | checkpoints, pending records |
| test fixture -> real repository | Fixture writes could pollute data/, checkpoints/ or results/ | files |
| frontier -> Phase 33 admission | The committed verdicts decide admission | frontier |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation (evidence) | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-32-01 | Spoofing | `_wr05_failures` D-17 exemption | mitigate | **CLOSED 2026-09-28 by fix.** At audit time the Subscript half exempted *any* `X["control_readings"]`, and four module-namespace reads returned `[]` (review WR-03). RED: 325aaf0 plants the four forms in `test_ast_guard_planted_red_per_class` (`tests/test_phase30_points.py:739-751`: `wr03_vars`, `wr03_dunder_dict`, `wr03_vars_alias`, `wr03_sys_modules`); each returned `[]` and the test failed at `wr03_vars.py`. FIX: f7c1a83 adds `_json_root` (`:627-636`): a subscript is exempt only when its value is a chain of subscripts rooted at a plain Name that is not a v4.0 module binding nor `sys`, so any Call (`vars(...)`), Attribute (`.__dict__`, `sys.modules`) or module Name in the chain stays flagged. The D-17 dict-key/subscript GREEN cases, the natural cases (phase29_prereg / phase23_matched_prereg / phase25_promotion) and the v5 census over `phase3[0-4]_*.py` (incl. `phase32_frontier.py`, JSON keys only) stay green. Residual, documented in the code comment: a namespace first bound to a plain name (`d = vars(m); d["control_readings"]`) needs dataflow and is not caught; no v5 module uses `vars(`/`__dict__`/`sys.modules`/`importlib` (grep, 0 hits). | closed |
| T-32-02 | Tampering | own_control replay equality | mitigate | `scripts/phase30_points.py:265-272` requires `per_step == [replay_windows] * max_steps`. It is tested by the parametrized `tests/test_phase30_points.py:405` (`test_wr04_own_control_refuses_a_control_without_replay_counts`). | closed |
| T-32-03 | Repudiation | phase30_points pin continuation | mitigate | `tests/test_phase30_calibration.py:350-386` holds the dated `_SUPERSEDED_PINS` continuation. The tripwire checks both a synthetic extra and a missing sha. It is green. | closed |
| T-32-04 | Tampering | recipe_identity replay source (IN-04) | mitigate | `scripts/phase30_points.py:88-93` checks that each `REPLAY_SOURCE` name's module part is `teach_persona`. Tested at `tests/test_phase30_points.py:414`. | closed |
| T-32-05 | Elevation | commit_path | mitigate | `scripts/phase32_points.py:408-450` resolves the path under `results/`, requires branch == main, commits with `git commit -- <path>` and verifies the name-only result. `ALLOWED_GIT_ACTIONS`/`READ_ONLY_GIT_ACTIONS` are at `:103-104`. The AST surface and the no-`_git` rule are tested in `tests/test_phase32_points.py:467-483`, and the refusals at `:426-437`. | closed |
| T-32-06 | Repudiation | stage outputs from different code (WR-02 / D-08) | mitigate → accept (developer ruling) | **CLOSED 2026-09-28 as ACCEPTED RISK (AR-32-02), developer ruling, scoped to the committed Phase 32 data.** Audit finding kept: **PARTIAL.** The declared parts exist: the sessions sidecar (`scripts/phase32_points.py:340-349`), `prove_pinned_unchanged` (`:352-371`), the call before the write (`:397`) and `module_sha256` (`:617`). The threat is **not closed** for three reasons. (a) **CR-01:** `:397` diffs `[*session_shas, training.git_sha]` against HEAD but omits `INSTRUMENT_GIT_SHA` (`:62`), the commit the running process imported its code from. `record_session` (`:538`) reads the *current* HEAD at each point, so a pinned-module commit landing *between* points gives session sha = training sha = HEAD, and D-08 passes while old code runs. `module_sha256` (`:617`) is hashed from disk at write time, so it would pin bytes that never ran. No test binds `INSTRUMENT_GIT_SHA` into D-08; it appears only at `:618` and `tests/test_phase32_points.py:924`. (b) **WR-01:** `PINNED_MODULES` (`:66-94`) omits modules that the pinned stage modules import: `personacore.checkpoint`, `config`, `dialogue`, `evaluation`, `generation`, `tokenizer` and `seeding` (grep of the imports in teach_persona/phase14_recall/phase25_points/phase25_run/phase18_extraction/phase25_gate05). (c) **WR-05:** the pending-record path (`:698-708`) commits a record without re-running D-08 at commit time (see the unregistered flags). **Not reached:** see the evidence below. | closed |
| T-32-07 | Tampering | record overwrite | mitigate | `scripts/phase32_points.py:379-399` puts the overwrite refusal first, the dirty refusal second, D-08 third and `atomic_write_json` last. Tested at `tests/test_phase32_points.py:374-406`. The verifier probed it live on the real repo and it refused. The declared scope (overwrite) is closed. The WR-05 bypass does not overwrite anything; it is logged under the unregistered flags. | closed |
| T-32-08 | Tampering | stop line retyped or edited | mitigate | `scripts/phase32_points.py:317-326` reads the value through `phase30_points._tracked_json` (`scripts/phase30_points.py:190-203`, committed blob, working-tree edit refused). The AST check for no float literal equal to it is at `tests/test_phase32_points.py:286-298`. | closed |
| T-32-09 | Spoofing | DP reading used as control_gap | mitigate | `control_gap` comes from its own measurement or from `phase30_points.control_dialogue_pair` (`scripts/phase32_points.py:611-615`). The WR-05 AST guard is clean over `phase3[0-4]_*.py` (`tests/test_phase30_points.py:695-703`). The guard carries the T-32-01 weakness, but the property holds in the current code (0 bypass forms). | closed |
| T-32-10 | Tampering | local verdict computation | mitigate | `scripts/phase32_frontier.py:182` calls `phase25_verdict.curve_verdicts`. There is no local `corrected_point_verdict`/`cleared_abc`/`curve_verdicts` def and no F_Y literal (grep). `_gate_retype_failures == []` plus a planted RED are at `tests/test_phase32_frontier.py:283-313`. | closed |
| T-32-11 | Spoofing | DP reading laundered into control_readings_by_arm | mitigate | `by_twin` is built only from the advr control records (`scripts/phase32_frontier.py:136-138, 99-108`). `phase25_promotion.control_readings` is never referenced (the only occurrences are JSON-key positions at `:248, :381-382, :544`). The AST guard runs in `tests/test_phase32_frontier.py:299-304`. It has the T-32-01 weakness but is not reached. | closed |
| T-32-12 | Tampering | statement typed after results | mitigate | There is a fixed `TEMPLATES` table (`scripts/phase32_frontier.py:280-305`) selected by computed state (`:457-464`). The floor words are derived (`:420-443`). Tested at `tests/test_phase32_frontier.py:445-556`. | closed |
| T-32-13 | Tampering | v4.0 drift / wrong v4 source | mitigate | v4 is read from the committed blob and its sha256 recorded (`scripts/phase32_frontier.py:527-528, 410`). The `git diff --quiet v4.0 HEAD -- results` guard with a natural RED is at `tests/test_phase32_frontier.py:638-655` (green). | closed |
| T-32-14 | Repudiation | structural SystemExit misrecorded | mitigate | The floor-marker proof is at `scripts/phase32_frontier.py:185-193`, and any other exit propagates. Tested at `tests/test_phase32_frontier.py:230-236`. | closed |
| T-32-15 | Tampering | frontier re-emitted after review | mitigate | Write-once `emit` with the overwrite refusal first (`scripts/phase32_frontier.py:496-505`). The git surface is read-only with no add/commit (`tests/test_phase32_frontier.py:625-635`). The live second emit refuses (32-VERIFICATION). | closed |
| T-32-16 | Tampering | post-hoc re-tune of a refused leg | mitigate | The refuse branch calls `next_action`, which returns `refuse` (`scripts/phase30_points.py:298-320`). `write_refused_records` is write-once and byte-checked (`:323-345`), and no `run_point` runs on a refused leg (`scripts/phase32_points.py:747-752`). Tested at `tests/test_phase32_points.py:602-650`. | closed |
| T-32-17 | Tampering | resumed training with uncountable replay | mitigate | The half-trained refusals are at `scripts/phase32_points.py:525-536`. The replay sidecar is tied to `adapter_sha256` (`:562-566`), and `resumed_from_step == 0` is enforced (`:214-218`). Tested at `tests/test_phase32_points.py:777-850`. | closed |
| T-32-18 | DoS | runaway sweep past budget | mitigate | The clock uses committed stage seconds (`scripts/phase32_points.py:299-314`) and is checked before each point (`:731-745`). At the line it writes a `stop_line` beat and exits 0. Tested at `tests/test_phase32_points.py:667-690`. | closed |
| T-32-19 | Repudiation | continuing past the line without a trace | mitigate | `--past-stop-line` is refused unless the line is reached (`scripts/phase32_points.py:716-725`). The ruling goes into `stop_line.past_line_ruling` in the provenance of every later record (`:758-762, :620`). Tested at `tests/test_phase32_points.py:693-712`. Residuals, both not reached (every record has `past_line_ruling: None`): IN-01, an empty `""` ruling is accepted; IN-07, PREREG-03 records carry no ruling. | closed |
| T-32-20 | Tampering | ruling text as an injection vector | accept | See the Accepted Risks Log. Verified: `past_stop_line` never enters subprocess argv, f-string messages or eval. It is stored only as a dict value (`scripts/phase32_points.py:716-762`). | closed |
| T-32-21 | Elevation | plist relaunch loops | mitigate | `artifacts/com.personacore.phase32.sweep.plist` has `KeepAlive` false and `RunAtLoad` false, and a fixed argv without `--past-stop-line`. The plistlib test is at `tests/test_phase32_points.py:1034-1055`. | closed |
| T-32-22 | Tampering | fixture writes into the real tree | mitigate | `tests/test_phase32_live.py:77-125, 346-353` snapshots stray `Path.glob` output before and after, and patches every root to a scratch repo while leaving `_CODE_ROOT` untouched (`:91`). The real tree is clean now (`git status --porcelain`: only the pre-existing `.claude/scheduled_tasks.lock`). | closed |
| T-32-23 | Repudiation | dry-run-only proof | mitigate | `tests/test_phase32_live.py` enters through `main()`, reads committed blobs, and feeds them to `build_frontier` and `admission()` (`:420-474`). It was green in the orchestrator's full suite and was not re-run here. | closed |
| T-32-24 | Spoofing | forced n8 counts hide a recall defect | mitigate | Forcing matches the arm and the exact adapter file name (`tests/test_phase32_live.py:150-186`). The forced list is asserted to be exactly the n8 control's one entry (`:288-296`). | closed |
| T-32-25 | Tampering | code changed mid-sweep | mitigate → accept (developer ruling) | **CLOSED 2026-09-28 as ACCEPTED RISK (AR-32-03), developer ruling, scoped to the committed Phase 32 data.** Audit finding kept: **PARTIAL.** The pre-launch porcelain gate is present (`32-RUNBOOK.md:27`, and `run()`'s `refuse_if_dirty` at `scripts/phase32_points.py:684-692`). The runbook forbids scripts/src commits during the run (`32-RUNBOOK.md:100-104`). However, the declared code control "D-08 refuses the next write if PINNED_MODULES moved" is **false** for a commit that lands between points. That is CR-01 (the import-time sha is missing from `:397`, and `record_session` re-reads HEAD at `:538`). It is also false for any stage module outside `PINNED_MODULES` (WR-01). The runbook even overstates D-08 (`32-RUNBOOK.md:100-104`). The only effective control against a between-points commit was procedural (the runbook). **Not reached:** see the evidence below. | closed |
| T-32-26 | Elevation | Claude launching the agent | mitigate | 32-06-PLAN Task 2 is `checkpoint:human-action` (`32-06-PLAN.md:113-130`), and the runbook says "Claude never runs launchctl" (`32-RUNBOOK.md:9-10`). 32-06-SUMMARY:39 records that the developer launched the agent and reported completion. This is a procedural control and cannot be proven from code. | closed |
| T-32-27 | Tampering | re-tuning after an unlearnable n64 control | mitigate | PREREG-03 is a structural refusal (T-32-16 evidence). The runbook states it is pre-registered (`32-RUNBOOK.md:166-170`). The 5 n64 records are PREREG-03, with no retry commits in `ae0ed837..e35654c`. | closed |
| T-32-28 | Repudiation | unrun points marked REFUSED at the line | mitigate | The stop-line branch returns 0 before any write (`scripts/phase32_points.py:732-745`). Only `next_action == refuse` writes PREREG-03 records. The line was never reached (clock 39903.5 s against 135989.5 s). | closed |
| T-32-29 | Tampering | frontier edited after the verdict | mitigate | Write-once emitter (T-32-15). The blocking D-16 review is recorded ("approved", 32-07-SUMMARY:63). The recompute test binds the committed frontier (`tests/test_phase32_frontier.py:666-682`, green). The first emit was deleted and re-emitted once, under a developer ruling, before any commit; that is within the declared control. | closed |
| T-32-30 | Tampering | frontier committed with others / before a point | mitigate | The add commit 645641b names only `results/phase32_frontier.json` (re-measured now; the 32-07 Task 3 automated check). The ancestry check `_assert_frozen_before(point, [frontier])` is at `tests/test_phase32_frontier.py:685-693`. The single-path property is a one-time plan check, not a persistent test. | closed |
| T-32-31 | Tampering | v4.0 records altered | mitigate | `tests/test_phase32_frontier.py:638-655` (green) and the 32-07 Task 3 command. | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

### Committed-run exposure of the open threats (measured 2026-09-28)

- `git log --name-only ae0ed837..e35654c` has 12 commits, and **each** names exactly one `results/phase32_point_*.json`. I checked this per commit, not just as a net diff, so no scripts/src change was made and reverted inside the window. CR-01 and WR-01 therefore did not occur.
- All 7 trained records carry 1 distinct `module_sha256` block, and `provenance.git_sha` = ae0ed837 on all 7.
- Each record's single session sha equals its `head_at_write` and its `training.git_sha`. The session sha of point *i+1* equals the commit of point *i*, which is a continuous write→commit chain. The WR-05 pending path never fired.
- The only scripts/src change since launch is `scripts/phase32_frontier.py` (fd76e0d, the D-16 fix), which descends from e35654c, so it landed after the sweep. The frontier is not in `PINNED_MODULES`.
- No v5 module uses a WR-03 bypass form.

**Conclusion:** the 3 threats open at audit time (T-32-01 since fixed; T-32-06/25 since accepted) are real gaps in the declared mitigations. None of them was exploited or reached in the committed records or the frontier. They matter for any reuse of `phase32_points` (Phase 33 or a re-run) and of the AST guard.

### Unregistered Flags

Carried as warnings (not closed by this gate; UF-32-01 is WR-05 and is part of the AR-32-02/03 reuse condition). The SUMMARY `## Threat Flags` sections list none. These surfaced in 32-REVIEW and have no register row:

| Flag | Source | Category | Note |
|------|--------|----------|------|
| UF-32-01 | WR-05 | Tampering | `scripts/phase32_points.py:698-708` commits any untracked, non-PREREG-03 point record that parses. It skips the schema, point_key and D-08 checks. The run-start dirty check excludes these paths (`:672`), and `tests/test_phase32_points.py:653-664` commits a record reduced to `{point_key, stages}`. **Not reached.** |
| UF-32-02 | WR-02 | Repudiation | The frontier's `PROVENANCE_MODULES` (`scripts/phase32_frontier.py:64-73`) omits `mitigation_gate`, `erasure_gate`, `phase25_condition_c`, `phase25_gate05`, `phase25_record` and `phase30_points`. `provenance.git_sha` plus the recompute test pin the full tree, so no verdict is affected. |
| UF-32-03 | WR-04 | DoS (availability) | A control gap ≤ 0 would give a raw `ValueError` at `build_frontier`, not a named refusal. **Not reached:** the n8 gap is +0.134325. |

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-32-01 | T-32-20 | The `--past-stop-line` ruling text is stored as JSON data only. It is never executed and never put into argv, which is verified at `scripts/phase32_points.py:716-762`. The single local developer is its only author. No ruling was ever given (`past_line_ruling: None` on all 7 trained records). | Plan 32-04 threat register (plan-time disposition) | 2026-09-28 |

| AR-32-02 | T-32-06 | Stage-output provenance gaps (D-08 / WR-02) not reached in the committed sweep. Evidence (committed-run exposure above): `git log --name-only ae0ed837..e35654c` names only the 12 `results/phase32_point_*.json` records, one per commit, checked commit by commit; all 7 trained records carry one `module_sha256` block with `provenance.git_sha` ae0ed837; in every record the session sha = `head_at_write` = `training.git_sha`, so the WR-05 recovery path never ran. Gaps accepted, not fixed: CR-01 (`scripts/phase32_points.py:397` omits `INSTRUMENT_GIT_SHA` from `prove_pinned_unchanged`), WR-01 (`PINNED_MODULES` omits stage modules such as `personacore.checkpoint/config/dialogue/evaluation/generation/tokenizer/seeding`), WR-05 (the recovery commit at `:698-708` skips D-08). **Condition:** CR-01, WR-01 and WR-05 must be fixed, with dated pin continuations (`phase32_points.py` is pinned by the 7 trained records), BEFORE any Phase 33 reuse of `phase32_points` or any re-run. | Developer ruling (AskUserQuestion: "Fix WR-03, accept the HIGHs") | 2026-09-28 |
| AR-32-03 | T-32-25 | Code change mid-sweep: the effective control was procedural (runbook ban on scripts/src commits during the run; D-08 wording corrected in `32-RUNBOOK.md` the same day) and it held. Same evidence, gaps and condition as AR-32-02. | Developer ruling (AskUserQuestion: "Fix WR-03, accept the HIGHs") | 2026-09-28 |

*Accepted risks do not come back in future audit runs.* AR-32-02/03 cover only the committed Phase 32 records and frontier; they do not carry over to any reuse of `phase32_points`.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-28 | 31 | 28 | 3 (T-32-01, T-32-06, T-32-25) | gsd-security-auditor |
| 2026-09-28 | 31 | 31 | 0 (T-32-01 fixed: RED 325aaf0, fix f7c1a83; T-32-06/25 accepted as AR-32-02/03 by developer ruling; UF-32-01..03 carried as warnings) | gsd-executor (security gate close) |

Open-threat severity against `block_on: high`:
- **T-32-06 and T-32-25 are HIGH.** CR-01 is rated critical by the review, and the declared code control is ineffective for the between-points case.
- **T-32-01 is MEDIUM.** The gap is in a test-only guard that has no pin cost.

The possible resolutions were the developer's choice (ruling 2026-09-28: fix WR-03, accept the HIGHs):
- **Fix:** follow the CR-01, WR-01 and WR-05 fixes in 32-REVIEW.md with a dated pin continuation, and add the WR-03 planted-RED cases.
- **Accept:** record accepted-risk entries scoped to the committed Phase 32 data, carry the fixes as prerequisites for any reuse in Phase 33, and correct the D-08 wording in `32-RUNBOOK.md:100-104`.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-09-28 — 31/31 closed (T-32-01 fixed in f7c1a83; T-32-06/25 accepted as AR-32-02/03 by developer ruling, conditional on the CR-01/WR-01/WR-05 fixes before any Phase 33 reuse of `phase32_points`)
