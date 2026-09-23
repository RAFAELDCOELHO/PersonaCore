---
phase: 28-report-the-published-null-and-milestone-close
plan: 03
subsystem: milestone-close
tags: [ledger, dispositions, named-limitations, phase-27-carry, rpt-03]
requires: ["28-01", "28-02"]
provides:
  - results/phase28_ledger.json — the one disposition ledger (69 rows, closed six-value domain, `close: {"ci_run": null}`)
  - tests/test_phase28_ledger.py — schema / closed-domain / FIXED-has-test / record-bound-reason / stamp+artifact regression tests (15 tests)
affects: ["28-04 (register + ship block are filters over this file)", "28-06 (flips TD-XC-README-GLANCE to FIXED, then pins the rows digest)", "28-07 (fills close.ci_run)"]
tech-stack:
  added: []
  patterns: [byte-stable json dump (indent=2, sort_keys, ensure_ascii=False, trailing newline), collect-all-then-assert-once, planted-RED probes on a tmp_path copy]
key-files:
  created:
    - results/phase28_ledger.json
    - tests/test_phase28_ledger.py
  modified:
    - .planning/todos/completed/phase28-carry-phase27-latent-review-findings.md (git mv from pending/, status: resolved)
decisions:
  - "TD-16-R1 is RE-DEFERRED (v5.0), not ACCEPTED: the close is behavioural (read the D-28 note from 16-CONTEXT.md at runtime), not prose"
  - "TD-17-SUMMARY-FRONTMATTER is RE-DEFERRED: frontmatter.validate flags the archived SUMMARY invalid, but on duration/completed — fields unrelated to the audit's requirements cross-reference"
  - "IN-01..IN-06 are FORBIDDEN-BY-GUARD (record pins phase27_relearn.py + data.py; phase27_prereg.py is ancestry-guarded); IN-07 RE-DEFERRED (test-file edit, v5.0); IN-08 ACCEPTED (design choice, review says none required)"
  - "TD-XC-README-GLANCE stays RE-DEFERRED until 28-06 Task 1 flips it to FIXED with the 28-04 renderer commit + node id — a FIXED row must cite a collectable test"
  - "Planted-RED probes use Path.write_text on a tmp_path copy, not atomic_write_json: scratch file, no atomicity needed, and the census forbids os.replace in this test file"
metrics:
  duration: "2 sessions (Tasks 1-2 in one executor, Task 3 checkpoint + SUMMARY in a continuation)"
  completed: "2026-09-21"
---

# Phase 28 Plan 03: The Disposition Ledger Summary

One data file, `results/phase28_ledger.json`, replaces "16 + 6 items closed, re-deferred or recorded" with one row per open item across v3.0 and v4.0, a closed six-value disposition domain, and a test that refuses `FIXED` without a resolvable commit and a collectable test node id. The Phase 27 review findings, the human-UAT obligations and every carried limitation are rows in this file; 28-04's named-limitation register is `[r for r in rows if r["disposition"] == "NAMED-LIMITATION"]`.

## Commits

| Task | Commit | Content |
|------|--------|---------|
| 1 + 2 | `841e7df` | `results/phase28_ledger.json`, `tests/test_phase28_ledger.py`, todo moved to `.planning/todos/completed/` with `status: resolved` |
| 3 | none | developer review — "approved", no row changed |

## Measured counts (from `.venv/bin/python`, never typed)

- `len(rows)` = **69**; re-dump with `json.dumps(L, indent=2, sort_keys=True, ensure_ascii=False) + "\n"` is byte-identical to the file (`redump_identical True`).
- `close == {"ci_run": null}` (to be filled by 28-07).
- By milestone: `{'v3.0': 27, 'v4.0': 42}`.
- By category: `{'tech-debt': 16, 'stale-stamp': 12, 'found-by-measurement': 5, 'requirement': 5, 'review-finding': 16, 'inherited-obligation': 6, 'limitation': 3, 'refusal': 1, 'warning': 2, 'premise': 3}`.
- By disposition: `{'NAMED-LIMITATION': 23, 'ACCEPTED': 18, 'FORBIDDEN-BY-GUARD': 10, 'FIXED': 8, 'RE-DEFERRED': 6, 'CLOSED-EARLIER': 4}`.
- SC3's "16 + 6": v3.0 `tech-debt` filter = 16 (equals the parsed `tech_debt:` block of `v3.0-MILESTONE-AUDIT.md`); v3.0 `stale-stamp` filter = 6 (equals the body rows of STATE.md's "6 items acknowledged and deferred" table) — both asserted in `test_v3_counts_derive_from_the_sources`.
- `gsd-sdk query audit-open` after the todo move: `{"debug_sessions":0,"quick_tasks":0,"threads":0,"todos":0,"seeds":0,"uat_gaps":0,"verification_gaps":2,"context_questions":0,"total":2}` — the two remaining `verification_gaps` are the 23/27 `human_needed` rulings carried as rows `VER-23-HUMAN-NEEDED` / `VER-27-HUMAN-NEEDED` (ACCEPTED, D-35).

## Full id list with dispositions

**v3.0 tech-debt (16):** TD-16-I1 FORBIDDEN-BY-GUARD · TD-16-I2 FORBIDDEN-BY-GUARD · TD-16-R1 RE-DEFERRED · TD-16-R2 ACCEPTED · TD-16-R3 ACCEPTED · TD-17-DEF-17-01 CLOSED-EARLIER · TD-17-SUMMARY-FRONTMATTER RE-DEFERRED · TD-18-W1-RESIDUAL FORBIDDEN-BY-GUARD · TD-18-ALLOWLIST-PARENTHETICAL FIXED · TD-19-W1-ARTIFACT-NAMES FIXED · TD-19-PERPLEXITY-DOCSTRING FIXED · TD-19-13-STRAY-TAGS ACCEPTED · TD-XC-ERASE-CHECKBOXES ACCEPTED · TD-XC-REQCOMPLETED-STRING ACCEPTED · TD-XC-17-DIGIT ACCEPTED · TD-XC-README-GLANCE RE-DEFERRED

**v3.0 stale-stamp (6):** SS-DEBUG-DRAW-ALL FIXED · SS-QUICK-260819-R1U FIXED · SS-QUICK-260819-SGH FIXED · SS-17-VERIFICATION ACCEPTED · SS-18-VERIFICATION ACCEPTED · SS-19-VERIFICATION ACCEPTED

**v3.0 found-by-measurement (5):** FM-QUICK-260902-DLO FIXED · FM-19-16-CASE FIXED · FM-17-VALIDATION-PLANNED ACCEPTED · FM-18-VALIDATION-DRAFT ACCEPTED · FM-19-VALIDATION-DRAFT ACCEPTED

**v4.0 requirement (5):** RELRN-02 · RELRN-03 · RELRN-04 · RELRN-05 · FRONT-04-WEAKER-FORM — all NAMED-LIMITATION

**v4.0 review-finding (16):** CR-01, CR-02, WR-01, WR-02, WR-03, WR-04, WR-05, WR-06 NAMED-LIMITATION · IN-01..IN-06 FORBIDDEN-BY-GUARD · IN-07 RE-DEFERRED · IN-08 ACCEPTED

**v4.0 inherited-obligation (6):** OBLIG-A..OBLIG-F — all NAMED-LIMITATION

**v4.0 limitation (3):** D40-LIMITATION-1 · D40-LIMITATION-2 · CANARY-COULD-NOT-HAVE-FAILED — all NAMED-LIMITATION

**v4.0 refusal (1):** ADV-N64-REFUSED NAMED-LIMITATION

**v4.0 warning (2):** P22-WARNING-4 · P22-WARNING-5 — RE-DEFERRED (v5.0)

**v4.0 premise (3):** P23-17-UNTICKED ACCEPTED · P18-THROUGHPUT-COMMENT FORBIDDEN-BY-GUARD · SC3-SHA256-CLAUSE ACCEPTED

**v4.0 stale-stamp (6):** UAT-25-STAMP CLOSED-EARLIER · UAT-24-ITEM-2 CLOSED-EARLIER · UAT-24-ITEM-3 CLOSED-EARLIER · UAT-24-STAMP ACCEPTED · VER-23-HUMAN-NEEDED ACCEPTED · VER-27-HUMAN-NEEDED ACCEPTED

## Seven judgement calls (flagged for the Task 3 review; all stood)

1. **TD-16-R1 → RE-DEFERRED, not ACCEPTED.** The item is behavioural, not prose: closing it means reading the D-28 note from `16-CONTEXT.md` at runtime so an amended D-28 surfaces as a test failure. `scripts/phase16_persistence.py` is not ancestry-guarded and no record `module_sha256` names it (28-01 re-measurement), so an edit is *possible* — but no v4.0 number depends on it and Phase 28 edits no runtime behaviour. Target v5.0.
2. **TD-17-SUMMARY-FRONTMATTER → RE-DEFERRED, tool error on different fields.** `gsd-sdk query frontmatter.validate ...17-01-SUMMARY.md --schema summary` returns `{"valid":false,"missing":["duration","completed"],...}`. The tool does flag the archived file, but for `duration`/`completed`; the `summary` schema consumes no `requirements` field at all, so the audit's cross-reference gap is not a tool error, and the fields the tool does flag belong to an archived phase (D-31). Target: v5.0 audit-tooling pass.
3. **IN-01..IN-06 → FORBIDDEN-BY-GUARD, each naming its guard.** IN-01, IN-04, IN-06 edit `scripts/phase27_relearn.py` (pinned by `results/phase27_admission.json::provenance.module_sha256`, guarded by `tests/test_phase27_relearn.py::test_provenance_digests_match_live_bytes`); IN-02, IN-03 edit `scripts/phase27_prereg.py` (ancestry-guarded by `tests/test_phase27_prereg.py` — any commit touching it after the record reddens the guard permanently); IN-05 edits `src/personacore/training/data.py`, one of the seven `PINNED_MODULES`. All six are latent on the committed record (each reason says why). **IN-07 → RE-DEFERRED** (a test-file edit is allowed but Phase 28 touches no Phase-27 test; v5.0, monkeypatch `relearn._ROOT`). **IN-08 → ACCEPTED** (design choice consistent with the 24-09 guard; the review's own fix is "none required"; recorded so the maintenance cost behind the six FORBIDDEN rows is visible).
4. **UAT-24-ITEM-2 → CLOSED-EARLIER with measured lines.** D-37 cited `scripts/phase24_adversarial.py:289-292; :300`; the file is unchanged since `ba2787f` and the filter measures at `:296-301` (condition `:300`), with the belt-and-braces `SystemExit` at `:309`. The ledger cites the measured lines; the ADVT-02 traceability note names both.
5. **TD-XC-REQCOMPLETED-STRING → ACCEPTED (valid).** `frontmatter.validate ...16-04-SUMMARY.md --schema summary` returns `{"valid":true,"missing":[],...}` and 28-02 measured no tool error on this field either; no active cost (D-31), archived frontmatter recorded, not edited.
6. **FM-17-VALIDATION-PLANNED / FM-18-VALIDATION-DRAFT / FM-19-VALIDATION-DRAFT → ACCEPTED.** Three archived VALIDATION stamps (`status: planned` / `draft` / `draft` at line 4) that no tool scans; the v3.0 audit's nyquist row already records each phase as partial; no number, gate or requirement status depends on them. Rows exist so REQUIREMENTS.md:470-472's "3 PARTIAL VALIDATION files" has a disposition each.
7. **`Path.write_text` instead of `atomic_write_json` in the planted-RED probes.** `test_a_lowercase_disposition_is_red` and `test_a_missing_test_node_id_is_red` write a mutated copy of the ledger to `tmp_path`; it is a scratch file read once by the same test, so atomicity buys nothing, and the file's census forbids the `os.replace` token that `atomic_write_json` relies on. The real ledger is never written by a test.

## Task 3: developer review

**"approved" — 2026-09-21.** The developer read all 69 rows (printed in full via the plan's step-1 command) and the seven judgement calls above; rows stand as written, no changes, no review commit. Verified after the ruling: `.venv/bin/pytest tests/test_phase28_ledger.py -q` → `15 passed in 3.41s`; `git status --short results/phase28_ledger.json` empty.

## Verification

- `tests/test_phase28_ledger.py`: 15 passed (12 checks + 2 planted-RED probes + byte-stable re-dump). Census clean: no `== 10`, `train_arm(`, `os.replace`.
- Ledger tracked at `841e7df`; `.planning/todos/pending/` empty; todo in `completed/` with `status: resolved`; no `todos/resolved/` directory.
- **Full suite NOT run by this executor.** The continuation only re-ran the ledger test; the orchestrator runs `make test` on the committed tree after the wave (the ~23-min suite is outside a task-scoped `timeout`).

## Deviations from Plan

None in the continuation — plan executed exactly as written for Task 3. (Tasks 1-2 deviations, if any, are in the wave-1 executor's report; the seven judgement calls above are dispositions the plan left to measurement, not deviations.)

## Note for 28-06

`TD-XC-README-GLANCE` is the only row the plan expects to change before publish: 28-06 Task 1 flips it `RE-DEFERRED → FIXED` with evidence `<28-04 renderer sha>; tests/test_phase28_report.py::test_glance_block_is_byte_identical`, *before* the publishing commit pins the rows digest. After publish, any row change is a dated continuation (D-20).

## Self-Check: PASSED

- `results/phase28_ledger.json` FOUND · `tests/test_phase28_ledger.py` FOUND · `.planning/todos/completed/phase28-carry-phase27-latent-review-findings.md` FOUND
- commit `841e7df` FOUND on `main`
