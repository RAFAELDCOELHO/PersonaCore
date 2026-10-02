---
phase: 36-mps-cost-probes-and-budget-commitment
fixed_at: 2026-10-02T00:00:00Z
review_path: .planning/phases/36-mps-cost-probes-and-budget-commitment/36-REVIEW.md
iteration: 1
findings_in_scope: 6
fixed: 6
skipped: 0
status: all_fixed
---

# Phase 36: Code Review Fix Report

**Fixed at:** 2026-10-02
**Source review:** .planning/phases/36-mps-cost-probes-and-budget-commitment/36-REVIEW.md
**Iteration:** 1
**Base:** 38743e8

**Summary:**
- Findings in scope: 6 (CR-01, WR-01..WR-05). IN-01 and IN-02 were left for the verifier, as instructed.
- Fixed: 6. Each fix was first reproduced by a regression test that failed on the unfixed code.
- Skipped / not reproduced: 0.
- Final targeted run (`tests/test_phase36_{budget,caps,ledger,prereg,probe}.py`): **294 passed**.
  The baseline was 288. The fixes add 6 tests and rewrite 2 existing tests whose assertions
  encoded the defects.
- Census-bearing suites that name the phase36 modules (`tests/test_phase23_resume.py`,
  `tests/test_phase35_prereg.py`): **97 passed**.
- ruff check + format --check on the 6 touched files: clean. The `(==|!=)\s*10(?![0-9_])` census
  over `tests/test_phase36_*.py` finds no matches.
- Untouched: `scripts/phase36_prereg.py`, the pinned modules, and STATE/ROADMAP/REQUIREMENTS.

## Fixed Issues

### CR-01: A re-probe writes a second end line for the same record, and spent() then refuses forever

**Files modified:** `scripts/phase36_ledger.py`, `scripts/phase36_probe.py`, `tests/test_phase36_ledger.py`, `tests/test_phase36_probe.py`
**Commit:** 0d1b51a
**Reproduced:** yes. The RED test was `test_spent_counts_a_superseded_end_line_by_its_own_span`:
`SystemExit: [phase36_ledger] records named by two end lines (double count): ['results/phase36_probe_e1.json']`
**Applied fix:** two parts.

1. **spent() and report_rows() no longer refuse.**
   - The new `_superseded(attempts)` finds every end line that a later end line for the same
     record supersedes.
   - A superseded attempt is counted by its own ledger span (end utc − start utc), with
     `SUPERSEDED_FLAG`.
   - Only the last end line is counted by the record's `provenance.run`.
2. **run_front refuses a re-probe once the record exists.** If the ledger already has an end line
   for the front's record and that record exists (`_path_state != "absent"`: committed, modified
   or untracked-emitted), run_front refuses before it writes the start line. This keeps the last
   end line pointing at the attempt that wrote the record.

**Why this option:** counting only would let a re-probe after emit price the last attempt with
another attempt's record clock. Refusing only would not fix the reviewer's trigger, because the
WR-02 re-probes happen before any record exists. With both parts:

- re-probing before emit (WR-02's sanctioned recovery) works, and every attempt is counted
  exactly once;
- once the write-once record exists, a re-probe that it could never carry is refused.

**Old test rewritten:** `test_spent_refuses_a_record_named_twice` asserted the defect, so it was
replaced.

**GREEN:** 289 passed.

### WR-01: The exact-equality check against E6's A2-context copy makes an E1 re-probe after E6 permanently un-derivable

**Files modified:** `scripts/phase36_budget.py`, `tests/test_phase36_budget.py`
**Commit:** 021e194
**Reproduced:** yes. The RED test was `test_derive_prices_e1_and_surfaces_an_e6_record_beside_another_e1`:
`SystemExit: [phase36_budget] the E6 record's A2-context unit 2015.0 is not the E1 record's 2016.0: E6 was emitted beside a different E1 run`
**Applied fix:**

- `unit_prices` dropped the equality `_prove`. `a2_question_k48_high` comes from the E1 record,
  which is authoritative.
- `derive` returns a new field, `a2_context_mismatch`. It is `None` when the values match, and
  `{"e6_record": …, "e1_record": …}` when they differ.
- `dry` prints that field when it is set, so Rafael sees it.
- The D-16 emit-all order (ledger, e5, e6, e3, e2, e1) is unchanged.
- A missing E1 record still refuses: derive's "keyed by exactly PROBE_FRONTS" check, which the
  test asserts. `e6_a2_context_beside` also still refuses a missing E1 sidecar.

**Old test rewritten:** `test_derive_refuses_an_e6_record_beside_another_e1` asserted the defect,
so it was replaced.

**GREEN:** 289 passed.

### WR-02: A crashed attempt's session stays in the sessions sidecar, so WR-02 refuses a clean rerun

**Files modified:** `scripts/phase36_probe.py`, `tests/test_phase36_probe.py`
**Commit:** 6973b08
**Reproduced:** yes. The RED test was `test_a_crashed_attempts_session_never_poisons_a_clean_rerun`. The crashed attempt's session was at the pre-fix sha, and the clean rerun was at HEAD:
`SystemExit: [phase36_probe] pinned modules [...] changed between session commit c78f9ac… and HEAD (WR-02)`
**Applied fix:** run_front gets past its "sidecar exists → skip" branch only on a fresh attempt,
and stages never resume. So it now deletes the sessions sidecar
(`sessions_sidecar(front).unlink(missing_ok=True)`) before `record_session`.

- This deletion runs after the CR-01 refusal, so a refused re-probe deletes nothing.
- The crashed attempt's hours stay in the ledger through its lost line. Only its session sha,
  which owns none of the priced seconds, is dropped.

**GREEN:** 290 passed.

### WR-03: emit_all reconciles unconditionally, closing a live attempt

**Files modified:** `scripts/phase36_probe.py`, `tests/test_phase36_probe.py`
**Commit:** 78de575
**Reproduced:** yes. The RED test was `test_emit_all_never_closes_a_live_attempt`:
`Failed: DID NOT RAISE <class 'SystemExit'>`. The unfixed emit_all closed the live attempt with a
lost line and carried on.
**Applied fix:** before calling `reconcile()`, emit_all now checks every open run.

- **Liveness rule:** a run counts as alive if its last beat since its start
  (`phase36_ledger.last_beat_since`) falls inside `phase25_watch.STALL_THRESHOLD_MINUTES`. This is
  the watcher's existing stall rule; no new rule was invented.
- **Live run:** emit_all refuses with `run <id> is alive (last beat …)`, before anything is closed
  or committed.
- **Dead run:** a run silent past the window is reconciled as before, and the test asserts this.
- **reconcile itself is unchanged.** Its tests and the `phase36_ledger.py reconcile` CLI keep their
  semantics.
- **Import:** `phase25_watch` (stdlib only, torch-free) is now imported by phase36_probe.

**GREEN:** 291 passed.

### WR-04: The T-36-05 append-only proof is never called on any production path

**Files modified:** `scripts/phase36_ledger.py`, `tests/test_phase36_ledger.py`, `tests/test_phase36_probe.py`
**Commit:** 192ae6b
**Reproduced:** yes. The RED test was `test_every_reader_of_the_real_ledger_proves_it_append_only`.
In the working ledger the committed E5 lost line had been dropped:
`Failed: DID NOT RAISE <class 'SystemExit'>`. spent() read the rewritten ledger silently.

`test_emit_all_refuses_a_rewritten_committed_ledger` was added after the fix. It was confirmed RED
(`DID NOT RAISE`) against the HEAD blob of `phase36_ledger.py`. The blob was restored temporarily
from a scratch copy, and the fixed file was put back immediately afterwards.

**Applied fix:** `read_ledger` now calls `prove_append_only(path=path)` whenever the path resolves
to the real `_ROOT / LEDGER_PATH`.

- Every reader and writer of the real ledger goes through `read_ledger`: append, reconcile, spent,
  require_launch, rule, report_rows, emit-all (via its WR-03 check and reconcile), the probe's
  preflight and the budget's later_records. All of them now refuse a rewritten ledger.
- Tmp ledgers in tests are not the real path, so they are not checked. The same goes for the
  budget's scratch copy of the committed blob. Without that exemption, tests would break once the
  real ledger is committed.
- `prove_append_only` now treats a deleted working ledger as empty, so a tracked ledger missing
  from disk refuses with T-36-05 instead of raising `FileNotFoundError`.
- Both cases are tested on every path: the rewritten ledger and the deleted one.

**GREEN:** 293 passed.

### WR-05: dry() re-applies Rafael's cuts in the "E3 hours at recipes" loop

**Files modified:** `scripts/phase36_budget.py`, `tests/test_phase36_budget.py`
**Commit:** be3aaa6
**Reproduced:** yes. The RED test was `test_dry_applies_ruled_cuts_once_in_the_e3_recipes_loop`, with `cuts={"e2_seeds_to_3": 1}`:
`SystemExit: [phase36_budget] S is already 3`.
The `{"e6_anchor_adapters": 4}` case, run first on its own, was also RED:
`SystemExit: [phase36_budget] cut e6_anchor_adapters 4 leaves -1 adapters`.
**Applied fix:** the loop now builds `caps` from the pre-cut caps
(`kwargs.get("unit_caps") or proposed_unit_caps(probes)`) instead of `derived["unit_caps"]`, which
already had the cuts applied. Each ruled cut is therefore applied exactly once by `derive`.

The test checks both cut rulings. It asserts that each printed "E3 hours at recipes N" value
equals a direct `derive` with the same cuts at N recipes.

**GREEN:** 294 passed.

## Notes for the verifier

- **New production surfaces:**
  - `phase36_ledger._superseded` and `SUPERSEDED_FLAG`;
  - `derive()["a2_context_mismatch"]`;
  - the `phase25_watch` import in phase36_probe.
- **Function census:** `_superseded` is called as `phase36_ledger._superseded(...)` in its test.
- **Not changed:**
  - `budget_record` does not carry `a2_context_mismatch`. It is surfaced only through
    `derive`/`dry`.
  - `reconcile` itself still never refuses. The liveness refusal is only in `emit_all`, as the fix
    constraint specified.

---

_Fixed: 2026-10-02_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
