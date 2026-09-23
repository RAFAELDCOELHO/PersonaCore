---
phase: 28-report-the-published-null-and-milestone-close
plan: 02
subsystem: planning-artifacts
tags: [rpt-03, audit-open, verify-artifacts, d-31, d-35, d-36, d-37, d-39, uat-24-stamp]
requires: []
provides:
  - "gsd-sdk query audit-open: debug_sessions 0, quick_tasks 0, uat_gaps 0 (total 3: 1 todo + 2 D-35 verification gaps)"
  - "Five Phase-19 PLAN artifact paths resolved to the names the code actually writes (verify.artifacts green on every tracked results/ path)"
  - "25-HUMAN-UAT.md and 24-HUMAN-UAT.md status: complete, each by developer ruling"
  - "UAT-24-STAMP ruling text for 28-03's ledger"
affects: [28-03 ledger (UAT-24-STAMP row, measured phase24_adversarial.py lines, residual key-link mismatches), 28-VALIDATION]
tech-stack:
  added: []
  patterns: ["stamp edits only where a GSD tool reports an active error; every stamp cites the commit that proves the work (D-39); artifact names resolved from module constants, not from the PLAN prose"]
key-files:
  created: []
  modified:
    - .planning/quick/260819-r1u-close-b1-readme-v3-catchup/SUMMARY.md
    - .planning/quick/260819-sgh-close-w2-b1a-b1b/SUMMARY.md
    - .planning/quick/260902-dlo-pin-model-slim-pt-release-sha256-in-fetc/SUMMARY.md
    - .planning/debug/draw-all-utf8-decode-crash.md
    - .planning/milestones/v3.0-phases/19-selective-memory-erasure/19-08-PLAN.md
    - .planning/milestones/v3.0-phases/19-selective-memory-erasure/19-09-PLAN.md
    - .planning/milestones/v3.0-phases/19-selective-memory-erasure/19-12-PLAN.md
    - .planning/milestones/v3.0-phases/19-selective-memory-erasure/19-13-PLAN.md
    - .planning/milestones/v3.0-phases/19-selective-memory-erasure/19-16-PLAN.md
    - .planning/phases/25-frontier-sweep-and-the-existence-gate-verdict/25-HUMAN-UAT.md
    - .planning/phases/24-adversarial-extraction-aware-training-the-held-out-attack-fa/24-HUMAN-UAT.md
decisions:
  - "UAT-24-STAMP: 24-HUMAN-UAT status partial -> complete by developer ruling 2026-09-21 (field records pending state per D-36, not a verifier verdict; item 2 closed by ruling stays visible in its traceability note)"
  - "Stale artifact names in PLAN prose, files_modified, task <files> and recorded <automated> commands are NOT rewritten (D-31 / T-28-11); only the paths a tool reads were corrected"
  - "23-VERIFICATION.md and 27-VERIFICATION.md left at status: human_needed (D-35)"
metrics:
  duration: "~2 sessions (checkpoint at Task 3)"
  completed: "2026-09-21"
---

# Phase 28 Plan 02: Repair active tool errors in planning artifacts Summary

Every artifact that made a GSD tool report an active error is repaired with commit-cited evidence — three quick-task stamps, one debug stamp, five Phase-19 artifact names plus one casing pattern, and both open UATs closed by developer ruling — while everything D-31/D-35/D-39 fence off (archived VERIFICATION stamps, 19-13 tags, PLAN prose) is deliberately untouched; `audit-open` goes from total 9 to total 3, the residue being exactly the two D-35 gaps and one todo.

## Commits

| Task | Commit | Files |
|------|--------|-------|
| 1 — Stale stamps: three quick tasks + debug session | `64e7162` | quick/260819-r1u, 260819-sgh, 260902-dlo `SUMMARY.md` (renamed); debug/draw-all-utf8-decode-crash.md |
| 2 — Phase-19 artifact names, 19-16 casing, 25-UAT stamp, 24-UAT items 2-3 | `64e7162` | 19-08/09/12/13/16-PLAN.md, 25-HUMAN-UAT.md, 24-HUMAN-UAT.md |
| 3 — 24-HUMAN-UAT status stamp per developer ruling | `4b00c80` | 24-HUMAN-UAT.md (frontmatter only: `status: complete`, `updated: 2026-09-21T00:00:00Z`) |

Tasks 1 and 2 were committed together by the prior executor as `64e7162`.

## audit-open counts

| Point | debug_sessions | quick_tasks | todos | uat_gaps | verification_gaps | total |
|-------|---------------|-------------|-------|----------|-------------------|-------|
| Start | 1 | 3 | 1 | 2 | 2 | 9 |
| After Task 1 | 0 | 0 | 1 | 2 | 2 | 5 |
| After Task 2 (64e7162) | 0 | 0 | 1 | 1 | 2 | 4 |
| After Task 3 (4b00c80) | 0 | 0 | 1 | 0 | 2 | 3 |

Final (2026-09-21T18:36Z), verbatim: `"counts": {"debug_sessions": 0, "quick_tasks": 0, "threads": 0, "todos": 1, "seeds": 0, "uat_gaps": 0, "verification_gaps": 2, "context_questions": 0, "total": 3}`. The remaining items are `todos/phase28-carry-phase27-latent-review-findings.md` (owned by later 28-xx plans) and the two D-35 gaps (23-VERIFICATION.md, 27-VERIFICATION.md, both `human_needed`).

## Task 1 — evidence per stamp (D-39)

| Artifact | Evidence commit(s) | Note |
|----------|--------------------|------|
| quick/260819-r1u (close B1 README v3 catchup) | `7af6006`, `24d49ad` (2026-08-19) | renamed `260819-r1u-SUMMARY.md` -> `SUMMARY.md`, `status: complete` |
| quick/260819-sgh (close W2 B1a/B1b) | `4012a61`, `c90d0c8`, `98d0a60` (2026-08-19) | renamed, `status: complete` |
| quick/260902-dlo (pin model_slim.pt release sha256) | already `status: complete` | only the filename rule fired (`audit-open.js:78`); rename only |
| debug/draw-all-utf8-decode-crash.md | `c71bade` (2026-08-16) | `grep -n decode-crash results/phase18_extraction_report.md` -> line 320; `status: resolved` |

Nothing was RE-DEFERRED.

## Task 2 — name resolution (Phase-19 PLAN artifacts)

| Plan | PLAN said | Code writes | Source of truth |
|------|-----------|-------------|-----------------|
| 19-08 | `results/phase19_cal_corpus.json` | `results/phase19_calibration_corpus.json` | `CALIBRATION_CORPUS_PATH` (scripts/phase19_*.py:3093) |
| 19-09 | `results/phase19_calibration_arm.json` | `results/phase19_arm_cal-erased.json` | `arm_record_path("cal-erased")` |
| 19-12 | `results/phase19_arm_m1.json` | `results/phase19_arm_erased.json` | M1 = `arm_record_path("erased")` |
| 19-13 | `results/phase19_arm_m2.json` | `results/phase19_arm_retrain.json` | `arm_record_path("retrain")` |
| 19-16 | casing pattern | corrected to the casing the artifact carries | verify.artifacts 1/1 |

`contains:` patterns replaced where stale: 19-08 `corpus_sha256` -> `sha256`; 19-12 and 19-13 `zero_results_have_nll` -> `retention_ppl`.

verify.artifacts after edits: 19-08 `results/phase19_calibration_corpus.json` passed, `checkpoints/phase19_cal_adapter.pt` not found (gitignored — recorded, not renamed, D-31); 19-09 2/2; 19-12 2/2; 19-13 `results/phase19_arm_retrain.json` passed, `checkpoints/phase19_m2_retrain_adapter.pt` gitignored (recorded); 19-16 1/1. Every tracked `results/` path now exists.

## UAT stamps

**25-HUMAN-UAT.md (D-36):** `status: complete`, zero pending items (commit `64e7162`).

**24-HUMAN-UAT.md items 2-3 (D-37, commit `64e7162`):** item 2 carries a dated traceability note (filter in `scripts/phase24_adversarial.py`; see deviation 1 for the measured lines); item 3 `CLOSED-EARLIER` — `scripts/phase25_record.py:553` calls `phase14_recall.score_refusal`, `:574` `clean_frame_probe_populations`; all 44 frontier points carry `refusal.by_family` (four families, `refusal_n` 3456 each). Requirement prose untouched.

**24-HUMAN-UAT.md status stamp (Task 3, commit `4b00c80`) — tag `UAT-24-STAMP` for 28-03's ledger.** Developer ruling, 2026-09-21, verbatim:

> Confirma opção 1: status: partial → complete, updated: today. Mesmo raciocínio de Phase 25's UAT nesta mesma discussão — o campo registra estado de pendência (D-36), não veredito de verificador; com pending: 0, manter partial seria falso pela definição do próprio campo. A distinção real (item 2 fechado por ruling, não reteste) permanece visível e precisa na nota de rastreabilidade que ADVT-02 já decidiu escrever — não apagada, só não confundida com o campo errado.

Applied as: frontmatter `status: partial` -> `status: complete`, `updated: 2026-08-30T21:10:00Z` -> `2026-09-21T00:00:00Z`; no other line changed (`git show 4b00c80 --stat`: 1 file, 2 insertions, 2 deletions).

## D-35 by non-edit

`23-VERIFICATION.md:5` and `27-VERIFICATION.md:5` both still read `status: human_needed`. These are the two `verification_gaps` audit-open still lists, by design.

## Deviations from Plan

**1. [Rule 1 - Bug] Measured lines for the item-2 filter differ from the ones the UAT/D-37 cite.**
`scripts/phase24_adversarial.py` is unchanged since `ba2787f`, but the filter sits at `:296-301` (condition `:300`) and the `SystemExit` at `:309`, not `:289-292`/`:300` as the plan's must_have and D-37 state. The item-2 note names both the cited and the measured lines. 28-03's ledger should cite the measured lines. Commit `64e7162`.

**2. [Rule 2 - Missing] `verify.key-links` also reported the stale names.**
The `from:` entries (and 19-08's `to:`) in `key_links` carried the same stale artifact names; repaired with the same five real names. Residual key-link failures are dotted-symbol `to:` pattern mismatches — not artifact names — left for the ledger. Commit `64e7162`.

**3. [Scope, D-31] Stale names remain in each PLAN's `files_modified`, task `<files>`, prose and historical `<automated>` commands.**
No tool reads those fields, and rewriting recorded commands would falsify what actually ran (T-28-11). The plan's whole-file acceptance grep is therefore NOT satisfied by design; the verifier should rule on it.

**4. `contains:` patterns replaced where stale.** 19-08 `corpus_sha256` -> `sha256`; 19-12/19-13 `zero_results_have_nll` -> `retention_ppl` (the keys the artifacts actually carry). Commit `64e7162`.

**5. 24-UAT `updated:` was left at 2026-08-30 through Task 2**, pending the Task 3 ruling; now applied in `4b00c80`.

## Known Stubs

None — planning artifacts only.

## Threat Flags

None — no code or network surface touched.

## Self-Check: PASSED

- `64e7162`, `4b00c80` present in `git log`.
- `.planning/phases/24-adversarial-extraction-aware-training-the-held-out-attack-fa/24-HUMAN-UAT.md` line 2 `status: complete`, line 6 `updated: 2026-09-21T00:00:00Z`.
- `gsd-sdk query audit-open` counts: uat_gaps 0, total 3.
- STATE.md / ROADMAP.md not modified by this plan.
