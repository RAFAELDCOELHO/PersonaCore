---
phase: quick-260819-r1u
plan: 01
subsystem: published-docs
tags: [audit-remediation, dated-continuation, append-only, STAT-02]
requires: [results/phase19_erasure_report.md, scripts/_addendum.py, scripts/phase18_extraction.py]
provides:
  - "results/phase18_extraction_report.md carries Phase 19's retroactive scope limit (B1 closed)"
  - "README.md carries the measured v3.0 result and Phase 19's FAILURE / DO NOT SHIP (W1 closed)"
affects: [README.md, results/phase18_extraction_report.md]
tech-stack:
  added: []
  patterns: ["append-only dated continuation via scripts/_addendum.append_addendum with an identity marker pair"]
key-files:
  created: []
  modified:
    - results/phase18_extraction_report.md
    - README.md
decisions:
  - "The identity marker pair (EXTRACTION_SHIP_RECORDED_LINE passed as BOTH pending and recorded) is the only legal append_addendum call against this report, because PENDING is already consumed at 0 occurrences and the writer requires the pending line to occur exactly once"
  - "Published 77.6370113463966% (the value results/phase19_erasure_report.md:146 and STATE.md:55 actually carry) rather than the plan's typed 77.63701134639661%, which has one digit too many"
  - "README states both 88.5% and the exact rate 0.884615, so the front page cannot be read as disagreeing with the report's own 88.46% rendering"
metrics:
  duration: ~25 min
  completed: 2026-08-19
  tasks: 2
  commits: 2
---

# Quick 260819-r1u: Close B1 + README v3.0 Catch-Up Summary

Two published files each grew by one dated continuation, appended and never edited: the Phase 18
report now carries Phase 19's retroactive scope limit on its rank/exposure readings, and README
carries the measured 92/104 extraction result, the re-scoped LoRA caveat, and Phase 19's FAILURE /
DO NOT SHIP.

## What Landed

| Task | Name | Commit | File |
| --- | --- | --- | --- |
| A | Close B1 — Phase 19's scope limit into the Phase 18 report | `7af6006` | `results/phase18_extraction_report.md` |
| B | Close W1 — v3.0 catch-up section into README | `24d49ad` | `README.md` |

Base commit: `28b3c6e`. Head: `24d49ad`. No branch created; executed on `main` per instruction.

## Append-Only Evidence

### Line counts and sha256, before and after

| file | lines before | lines after | sha256 before | sha256 after |
| --- | --- | --- | --- | --- |
| `results/phase18_extraction_report.md` | 338 | 405 | `e205732daa2f8354bd7918343183d471793846039e0b2d19d5f09af657bbf274` | `559afbe3ee46ad2932734a71438532a6208999031b659121957404516fbc93ba` |
| `README.md` | 218 | 257 | `964faf38d26b90a5748efa1c623dcb301b52a8e7228dd0364356ec9581c7d1fd` | `7ad07ca93b89a2512ad0a83a1409ecf85bde1d161c679f480c5e6e8aed279b52` |

### numstat — insertions / deletions

Measured against the pre-execution base `28b3c6e`, so the pair covers both commits together:

```
39	0	README.md
67	0	results/phase18_extraction_report.md
```

**Deletions are 0 on both files.** Each per-task commit also reported `0` in its own numstat
(`67 0` for Task A, `39 0` for Task B).

### Strict byte-prefix proofs

Both pre-edit blobs are strict byte prefixes of their post-edit files — i.e. the diffs are pure
insertions at the end, not merely deletion-free:

- `results/phase18_extraction_report.md` — `prefix OK, +4918 bytes`
- `README.md` — `prefix OK, +2858 bytes`

`README.md:212-218` (the anticipatory Phase 18 paragraph) diffs empty against its pre-edit form.

### Marker invariants (Task A)

`EXTRACTION_SHIP_PENDING_LINE` occurs **0** times and `EXTRACTION_SHIP_RECORDED_LINE` occurs
exactly **1** time, unchanged across the append. Both constants were imported from
`scripts/phase18_extraction.py`, never retyped. The driver asserted both counts *before* calling
`append_addendum`, so the identity call is provably the legal one rather than a coincidence, and it
additionally asserted the addendum body carries neither marker (which would have moved the counts).

## The Three Flipped Grep Counts

| evidence command | before | after |
| --- | --- | --- |
| `grep -ci "retroactive weight on phase 18" results/phase18_extraction_report.md` | 0 | **1** |
| `grep -cin "phase 19" README.md` | 0 | **1** |
| `grep -c "DO NOT SHIP" README.md` | 0 | **2** |

## STAT-02

`grep -cE '\b0(\.0+)?%'` on each touched file: **0 before, 0 after**, on both files. Every zero in
the new text carries its denominator — `0/104`, `0/27`, `0 per-question mismatches`.

## Verification Gates

| gate | result |
| --- | --- |
| `git diff --numstat` deletions, both files | `0` |
| strict byte-prefix, both files | pass (+4918 / +2858 bytes) |
| `README.md:212-218` byte-intact | pass (empty diff) |
| new README heading lands last | pass — `220:## v3.0 audit results (recorded 2026-08-19)` |
| `pytest -q tests/test_phase18_docs.py` | 10 passed |
| `pytest -q` (full suite) | **845 passed, 1 skipped**, exit 0 |
| `ruff check .` + `ruff format --check .` | All checks passed; 170 files already formatted |
| frozen pins touched | **none** — `git diff --name-only 28b3c6e HEAD -- scripts/` returns 0 files |

The full suite was run twice — once after Task A and once after Task B — and returned
845 passed / 1 skipped both times, matching the pre-execution baseline exactly.

## Prohibitions Honored

- `render_report` was **not** called on the Phase 18 report.
- No frozen pin was edited (`scripts/phase18_extraction.py`, `scripts/phase19_erasure.py`,
  `scripts/erasure_gate.py`, `scripts/phase19_floor.py`, `scripts/phase17_isolation.py` — the
  diff against `28b3c6e` touches zero files under `scripts/`), so
  `tests/test_phase16_prereg.py`'s ancestry result is undisturbed.
- `README.md:212-218` was not edited.
- Marker string literals were imported, never retyped.
- `pyproject.toml` and `requirements.txt` are byte-identical (untouched; `tests/test_package.py`
  green).
- The driver was a throwaway in the scratchpad; no new file was added under `scripts/`.

## Deviations from Plan

### 1. [Rule 1 — Bug] The plan's destruction percentage had one digit too many

- **Found during:** Task A drafting
- **Issue:** The plan (`must_haves` and Task A action) specifies
  `77.63701134639661%`. The value published at `results/phase19_erasure_report.md:146` and
  restated at `.planning/STATE.md:55` is `77.6370113463966%`. Recomputing from the two committed
  gap values — `(1.2420966625043919 - 0.2777699357026435) / 1.2420966625043919 * 100` — returns
  exactly `77.6370113463966`, so the plan's literal is wrong, not the report's.
- **Fix:** Wrote the measured/published value in both new sections. Writing the plan's literal
  would have put a figure into a published audit artifact that disagrees with the artifact it
  cites.
- **Files:** `results/phase18_extraction_report.md`, `README.md`
- **Commits:** `7af6006`, `24d49ad`

### 2. [Instructed skip] The `.planning/STATE.md` activity line was NOT written

Task B's action ends by asking for one hand-written activity line appended to `.planning/STATE.md`.
The executor prompt's constraints state that the orchestrator owns that update and that this agent
must not edit or commit `.planning/STATE.md`. **The constraint wins; that sub-step was skipped.**
`.planning/STATE.md` is byte-untouched by this execution. Everything else in Task B was completed.

**The orchestrator still owes STATE.md its activity line.** Suggested content:

> 2026-08-19 -- quick 260819-r1u: audit finding B1 and warning W1 both closed as dated
> continuations. `results/phase18_extraction_report.md` (+67 lines, 0 deletions) now carries Phase
> 19's retroactive scope limit with the 73 zero-cells at `:236` named as inside it; `README.md`
> (+39 lines, 0 deletions) now carries 92/104 = 88.5% (lower bound 0.8231) against 0/104, the
> re-scoped LoRA caveat, and Phase 19 FAILURE / DO NOT SHIP. Suite 845 passed / 1 skipped.

### 3. [Judgement] README states the rate at two precisions

The plan asks for `88.5%`. The Phase 18 report's own generated conclusion renders the same rate as
`88.46%`. Both are honest roundings of `92/104 = 0.884615…`, but a reader comparing the front page
against the report would see two different strings and have no way to tell whether they describe the
same measurement. README therefore carries **`88.5%` (rate 0.884615)** — the plan's figure, with the
exact rate beside it so the two surfaces are visibly the same number.

### 4. [Scope addition] One paragraph on the threat model was added to the README section

The plan lists three required contents. A fourth short paragraph was added stating that black-box
prompt access makes 88.5% a **floor on leakage, never a ceiling on privacy**. Rationale: this
README's own D-16 discipline (`tests/test_phase15_docs.py::test_headline_numbers_match_sources`)
forbids outsourcing a headline number's caveat to a link, and the qualifier makes the published
number *worse* rather than more comfortable, so its omission would have been the self-serving
choice. No test required it.

## Not Done (by instruction)

- `.planning/STATE.md` — not edited, not committed (see Deviation 2).
- `.planning/ROADMAP.md` — not updated.
- `.planning/` docs artifacts (this SUMMARY, the PLAN) — not committed; the orchestrator commits
  them.
- No `gsd-sdk query state.*` / `roadmap.*` / `requirements.*` handler was run, for the same reason.

## Known Stubs

None. Both sections are complete published prose; nothing is placeholdered or deferred.

## Threat Flags

None. This execution touched two Markdown documents and introduced no endpoint, auth path, file
access pattern or schema change.

## Self-Check: PASSED

- `README.md` — FOUND
- `results/phase18_extraction_report.md` — FOUND
- commit `7af6006` — FOUND
- commit `24d49ad` — FOUND
- cumulative diff vs `28b3c6e`: `39 0 README.md`, `67 0 results/phase18_extraction_report.md` —
  zero deletions on both
