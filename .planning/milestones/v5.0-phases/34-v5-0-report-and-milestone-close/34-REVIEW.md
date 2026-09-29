---
phase: 34-v5-0-report-and-milestone-close
reviewed: 2026-09-29T12:33:47Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - scripts/phase34_report.py
  - scripts/phase34_report.md.tmpl
  - scripts/phase34_glance.md.tmpl
  - tests/test_phase34_report.py
  - tests/test_phase34_ledger.py
  - tests/test_package.py
  - tests/test_phase28_report.py
  - tests/test_phase31_probe.py
  - tests/test_phase32_points.py
findings:
  critical: 0
  warning: 3
  info: 5
  total: 8
status: issues_found
---

# Phase 34: Code Review Report

**Reviewed:** 2026-09-29T12:33:47Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Diff range b622b3c..HEAD, source files only. I checked the published artifacts (`results/phase34_ledger.json`, `docs/REPORT.md`, `README.md`) only for consistency with the code. This review proposes no edit to any PHASE28 or PHASE34 block. Any correction there is a dated continuation through `scripts/_addendum.py`.

Baseline checks, all read-only:
- `python scripts/phase34_report.py check` returned 0.
- `python scripts/phase28_report.py check` returned 0.
- `pytest tests/test_phase34_report.py tests/test_phase34_ledger.py tests/test_package.py`: 54 passed.
- The ledger's `close.ci_run.head_sha` (`dcc91f6…`) resolves to a commit in this repo.
- The ledger counts (61 rows: 7 NAMED-LIMITATION, 56 v5.0, 5 carried by reference) match the rendered register.
- The glance anchor matches `_github_anchor` of the rendered heading.

There are no blockers. The published blocks match the committed records byte for byte.

There are three warnings:
1. The pre-publish `write` path can leave a half-installed state that it then refuses to repair.
2. The templates still hand-type category and state claims (PASS, INCONCLUSIVE, REFUSED, "unlearnable") that the bound data could contradict. Only the byte-identity check catches this.
3. The per-leg comparison table renders `k5`/`k6` = `0` for the leg the report calls NOT MEASURED. It also drops the v4.0 per-leg counts that `COVERED_BY` claims it covers.

## Warnings

### WR-01: `write` is not atomic: a README anchor failure leaves REPORT.md installed and makes every retry refuse

**File:** `scripts/phase34_report.py:450-459`
**Issue:**
- `main(["write"])` pre-checks only that neither file has PHASE34 sentinels yet.
- It then calls `p28.install(REPORT_PATH, …)` (which writes REPORT.md) before `install_glance(README_PATH, …)`.
- `install_glance` only checks that the phase28 glance anchor occurs exactly once (line 411) after REPORT.md has already been written.

Failure scenario: the README has zero or two `PHASE28-GLANCE-BEGIN` markers. In that case REPORT.md gets the PHASE34 block, README.md does not, and every rerun refuses with "PHASE34-REPORT already present (carried D-20)". The operator's only way out is to hand-edit the report, which is exactly what D-20 exists to prevent.

**Reproduced:** yes. I copied the stripped pre-publish REPORT.md, plus a README with the anchor removed, into the scratchpad and ran `main(["write"])` twice:
- First run: exited "PHASE28-GLANCE-BEGIN must occur exactly once", and afterwards the report contained `PHASE34-REPORT`.
- Second run: exited "write refused: PHASE34-REPORT already present".

Impact today is nil, because both blocks are installed and `write` is pre-publish only. The engine is still carried forward, though. Phase 35+ will copy this shape.

**Fix:** Validate everything before writing anything, e.g. hoist the anchor check into the pre-check loop:
```python
readme = README_PATH.read_text(encoding="utf-8")
_prove(readme.count(ANCHOR_BEGIN) == 1, f"{README_PATH}: {ANCHOR_BEGIN} must occur exactly once")
```
Alternatively, compute both new texts first and write both only after both have been produced.

### WR-02: The templates hand-type verdict categories and states that the bound values can contradict

**File:** `scripts/phase34_glance.md.tmpl:1-7`, `scripts/phase34_report.md.tmpl:11-21`
**Issue:** The engine claims "rendered from the data, so this list cannot drift from the records". The templates, however, fix the shape of the outcome in prose and bind only the numbers:
- **Glance:** it binds only `tallies_by_leg.advr_n8.PASS` and `.INCONCLUSIVE`, and `advr_n64.REFUSED`. Any other non-zero category (FAIL) is silently dropped. The report's lead uses `_outcome()`, which lists every non-zero category, so the two blocks can disagree.
- **Report:** it types "This leg was refused, not measured" and "control is recorded unlearnable (`${…unlearnable}`)", with only the boolean bound.

**Reproduced:** yes, with planted in-memory records (no file written):
- Setting `advr_n8` to `INCONCLUSIVE=4, FAIL=2` renders the glance as "0 of 6 PASS, 4 of 6 INCONCLUSIVE", with no FAIL. The report lead says "PASS 0 of 6, FAIL 2 of 6, INCONCLUSIVE 4 of 6".
- Setting `control_readings.advr_n64.unlearnable = False` renders "The `advr n64` control is recorded unlearnable (`false`)".

No test in `tests/test_phase34_report.py` checks glance category coverage or the unlearnable prose. Today only the byte-identity check (`check`, tests in section 8) stops this, because the records are frozen.

**Fix:** For future renderers, add `derived.outcome.<leg>` (wrapping `_outcome`) and use it in the glance instead of per-category bindings. Guard typed state prose with `_prove`, e.g. `_prove(control["unlearnable"] is True, …)` inside a `derived.not_measured_leg` binding. Alternatively, add a test that `_outcome(tallies[leg])` appears normalized in the glance for every leg.

### WR-03: The per-leg comparison table shows `k5`/`k6` = `0` for the NOT-MEASURED leg and drops the v4.0 per-leg counts

**File:** `scripts/phase34_report.py:239-255` (with `COVERED_BY` at line 345)
**Issue:**
- `_condition_c_by_leg` renders `b["k5"]`, `b["k6"]` directly. For `advr_n64` (`v5_state: refused_prereg03`) the record carries `k5: 0, k6: 0`, so the published row reads `| advr_n64 | … | refused_prereg03 | 0 | 0 |`. A reader scanning the table sees "zero points cleared (c)" for a leg the same block declares NOT MEASURED. The report's own convention (`_null_cell`, the "`null` marks a point that never reached the pin" sentence at template line 29) calls for `null` here.
- The table also omits the record's v4.0 per-leg fields (`v4_k`, `v4_tk`/`v4_tn`, `v4_hk`/`v4_hn`, `v4_n_evaluated`). The section is titled "v4.0 → v5.0" and `COVERED_BY` asserts that `table.condition_c_by_leg` covers `frontier.verdicts.condition_c_vs_v4.by_leg`, but only the v5.0 side and `v4_state` are shown. The contract test (`_uncovered`) works at path level, so it cannot see dropped fields.

**Reproduced:** yes, read directly from `docs/REPORT.md`, PHASE34 block, by-leg table row `advr_n64`.

**Fix:** Do not edit the frozen block. If you want this surfaced, add a dated continuation via `scripts/_addendum.py`. In the renderer, render `k5`/`k6` as `null` when `v5_state != "measured"`, and add `v4_k` and `v4_tk/v4_tn` columns. Also make the contract test enumerate record keys, e.g. assert that every key of `by_leg[*]` is either a column or listed in an explicit exclusion.

## Info

### IN-01: `install_glance`'s byte-identity proof is tautological

**File:** `scripts/phase34_report.py:413-416`
**Issue:** `updated` is built as `text[:i] + … + text[i:]`, so `updated[:i] == text[:i]` and `updated.endswith(text[i:])` hold by construction and can never fire. The docstring claim "proved byte-identical on the produced text" gives no protection.
**Fix:** Drop it, or prove something non-trivial, e.g. `updated.replace(begin + block + end + "\n", "", 1) == text`.

### IN-02: `_capacity` splits on the first `_n`

**File:** `scripts/phase34_report.py:100-101`
**Issue:** `int(leg.split("_n", 1)[1])` raises `ValueError` for any leg id with `_n` before the capacity suffix (e.g. `adv_noreplay_n8` → `int("oreplay_n8")`). This is fine for today's `advr_n8`/`advr_n64`.
**Fix:** `int(leg.rsplit("_n", 1)[1])`.

### IN-03: The "engine untouched" test compares only against HEAD

**File:** `tests/test_phase34_report.py:311-316`
**Issue:** `git diff --quiet HEAD -- scripts/phase28_report.py` catches only uncommitted edits. A committed edit to the engine passes, and D-01 says the engine is "imported, never edited". `phase28_report.check() == 0` still catches output-changing edits, so the gap is limited to edits that don't change output.
**Fix:** Pin the sha256 of `scripts/phase28_report.py`, or diff against the phase-28 publishing commit.

### IN-04: A stale docstring in an amended phase28 guard

**File:** `tests/test_phase28_report.py:579-582`
**Issue:** The docstring still says the v4.0 heading "is the last one in the file". The R-1 continuation (lines 576-578) made that false for the real file: the guard now checks the file with later blocks removed.
**Fix:** Leave the docstring alone (the frozen-guard convention). The continuation comment above it already records the change. Noted only so a later reader does not "fix" the assertion to match the docstring.

### IN-05: The plist heartbeat assertion no longer ties the absolute root to this checkout

**File:** `tests/test_phase31_probe.py:991-997`, `tests/test_phase32_points.py:1045-1051`
**Issue:** The R-2 port compares only the path suffix under `_ROOT`, so it can pass on CI. As a result, a plist whose `--heartbeat` points into a different clone or worktree (e.g. the memory-noted stale worktree roots) now passes locally too. The equality with the canary plist still holds, so both would have to be wrong together.
**Fix:** Optionally assert full equality with `str(phase25_run.HEARTBEAT_PATH)` when `not os.environ.get("CI")`, keeping the suffix check on CI.

---

_Reviewed: 2026-09-29T12:33:47Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
