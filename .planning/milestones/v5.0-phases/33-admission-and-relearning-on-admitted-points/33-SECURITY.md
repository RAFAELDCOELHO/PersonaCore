---
phase: 33
slug: admission-and-relearning-on-admitted-points
status: verified
threats_open: 0
asvs_level: 1
block_on: high
created: 2026-09-28
---

# Phase 33 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> Register: T-33-01..T-33-13, written at plan time in the `<threat_model>` blocks of 33-01..33-03-PLAN.md.
> Method: each `mitigate` row was checked against code, tests and git at HEAD (3f9ba26), not against SUMMARY claims.
> Targeted tests: `tests/test_phase33_admission.py tests/test_phase27_prereg.py tests/test_phase29_prereg.py`, 148 passed. The full suite (3261 passed / 4 skipped / EXIT=0 at f48b738) was not re-run.
> Residuals: the code review (33-REVIEW.md, 0cf308f) reproduced WR-01 and WR-02, and both weaken a mitigation outside the one sanctioned run. The developer accepted them as AR-33-01/02 below.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| CLI argv → driver | `--out` / `--record` paths come from the operator | file paths |
| results/*.json on disk → leg guard | A record file may be forged or untracked | admission verdict (evidence integrity) |
| frontier bytes → admission() | Input to the frozen gate | frontier JSON (evidence integrity) |
| developer review → commit | The human "approved" is the only gate between the write and the commit | the write-once record |
| working tree → record | A concurrent session could dirty scripts/src/results mid-run | tree state |
| planning files → frozen Phase 28 renderer | REQUIREMENTS/ROADMAP/STATE are read live by guarded tests | requirement state |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-33-01 | Tampering | admit (re-run to fish for a different verdict) | mitigate | The parser has no `--force` (`admit --help` shows none; the two `--force` hits in the driver are prose at :6 and :158). The overwrite refusal comes first (:151-158). A record committed at HEAD but absent refuses via `git rev-parse --verify -q HEAD:<rel>` (:107-113, :161), including a staged `git rm`. Tests: `test_admit_refuses_to_overwrite_before_anything_else`, `test_admit_refuses_a_tracked_but_absent_record_before_the_dirty_check`. Observed live: the second admit exited 1 with "exists" (33-02-SUMMARY). Residual: WR-02 (AR-33-01) | closed |
| T-33-02 | Spoofing | refuse_leg (forged ADMITTED record) | mitigate | An unconditional `SystemExit` fires after every conjunct (:236). Tests: `test_each_leg_refuses_unless_admitted_even_on_a_forged_admitted_record`, plus 20 parametrized refusal cases | closed |
| T-33-03 | Repudiation | record written from a dirty tree | mitigate | `refuse_if_dirty(pathspec=DIRTY_PATHSPEC, cwd=_GIT_ROOT)` runs before any digest (:165). `git_sha`, `head_at_write` and the 7-module `module_sha256` are recorded. Tests: `test_admit_refuses_a_dirty_tree_before_any_digest`, `test_dirty_pathspec_excludes_only_the_untracked_record`, `test_provenance_digests_match_live_bytes`. The committed record carries git_sha 92fe48b (the parent of f48b738). Residual: WR-01 (AR-33-02) | closed |
| T-33-04 | Tampering | reuse of phase32_points with CR-01/WR-01/WR-05 open | mitigate | An AST census cites AR-32-02 and has a natural RED (`test_no_phase33_module_imports_phase32_points`); a sys.modules probe (`test_phase33_imports_neither_phase32_points_nor_torch`) backs it up | closed |
| T-33-05 | Spoofing | a relative --record path stepping around the tracked check | mitigate | The path is resolved against `_GIT_ROOT` before the tracked conjunct (:123). Test: `test_a_leg_refuses_unless_admitted_on_an_untracked_record_in_a_scratch_repo` | closed |
| T-33-06 | Tampering | JSON parsing of the record/frontier | accept | Parsing is `json.loads` only (:177, :219), never pickle. A malformed frontier makes admission() return INCONCLUSIVE, and relearning_scope refuses. A malformed record makes the leg raise KeyError and exit 1 (review IN-01, reproduced), so the leg still runs nothing | closed |
| T-33-07 | Repudiation | record commit | mitigate | Committed alone after "approved": `f48b738`, and `git show --name-only` lists only the record. Test: `test_the_record_was_committed_exactly_once_alone` | closed |
| T-33-08 | Tampering | concurrent edits mid-run | mitigate | `git status --porcelain` ran before admit and before the commit (33-02-SUMMARY), with explicit-path `git add`, and admit runs its own refuse_if_dirty | closed |
| T-33-09 | Tampering | admission re-run after review | mitigate | The second-admit refusal was observed live in 33-02 Task 1, and there is no `--force` | closed |
| T-33-10 | Information disclosure | push to remote | accept | Claude never pushes: `f48b738` is still in `git log origin/main..HEAD`. The developer pushes at Phase 34 close | closed |
| T-33-11 | Tampering | gsd-sdk handlers corrupting planning frontmatter | mitigate | Zero mutation handlers were called. REQUIREMENTS/ROADMAP/STATE were snapshotted and diffed and keep their line counts. `phase28_report.py check` exits 0 and the planning guard set gives 220 passed | closed |
| T-33-12 | Repudiation | a ledger figure without evidence | mitigate | The IN-03 evidence was re-measured and pasted raw into 33-03-SUMMARY (census count 8, one distinct value 4339f2b) | closed |
| T-33-13 | Information disclosure | secrets in planning notes | accept | No secrets are involved. The rows cite commits and paths only, and a grep of the 33 SUMMARYs for token/secret/password/api_key finds 0 hits | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-33-01 | T-33-01 | WR-02 (33-REVIEW.md): the write-once checks look only at the target path, and `_committed()` returns False outside `_GIT_ROOT`. So `admit --out <other path>` writes a fresh, authentic-looking record, reproduced by the reviewer in a scratch repo. It cannot change the committed record: the canonical path refuses, the record has one commit (f48b738), and `test_the_record_is_pinned_to_the_frontier_both_ways` binds it to the frontier. **Condition:** before any reuse of `phase33_admission`, remove `--out` or refuse any path other than `_GIT_ROOT/RECORD_PATH`, with a dated pin continuation (the driver is pinned in the record's `module_sha256`). Staged for the Phase 34 ledger | Developer ruling (AskUserQuestion: "Accept, Phase 34 ledger") | 2026-09-28 |
| AR-33-02 | T-33-03 | WR-01 (33-REVIEW.md): `git_sha()` (:44, :191) runs in the process cwd, not in `_GIT_ROOT`. Reproduced: importing the driver from `/tmp` gives `INSTRUMENT_GIT_SHA == 'unknown'`. The one real call ran from the repo root, and the committed record carries git_sha = head_at_write = 92fe48b. **Condition:** before any reuse, pass `cwd=_GIT_ROOT` (the root fix is a `cwd` parameter in `personacore.provenance.git_sha`), with a dated pin continuation. Staged for the Phase 34 ledger | Developer ruling (AskUserQuestion: "Accept, Phase 34 ledger") | 2026-09-28 |

*Accepted risks do not come back in future audit runs.* AR-33-01/02 cover only the committed record `results/phase33_admission.json`; they do not carry over to any reuse of `phase33_admission`.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-28 | 13 | 13 | 0 | orchestrator (inline; mitigations checked against code/tests/git at 3f9ba26) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-09-28
