---
phase: 25-frontier-sweep-and-the-existence-gate-verdict
plan: 07
subsystem: planning-doc corrections and their guard
tags: [rpt-02, correction-sweep, sentinel-continuation, additive-doctrine, prose-normalized]
requires:
  - "scripts/_prose.py::normalized (plan 20-03)"
  - "tests/test_phase23_cost.py (23-12 correction sweep)"
  - "tests/test_phase24_correction.py (24-03 correction sweep)"
  - "results/phase23_matched_control.json, results/phase23_matched_verdict.json, results/phase23_control_floor.json"
  - "scripts/mitigation_budget.py::ADVERSARIAL_RATIO_GRID, ::MATCHED_CONTROL_NOISE_FLOOR"
  - "src/personacore/privacy/dpsgd.py::DPSGD.__init__ (PRE-PASS 1)"
provides:
  - "eight sentinel-bounded dated continuations across three planning documents"
  - "RPT-02 on ROADMAP Phase 25's Requirements line (D-38)"
  - "tests/test_phase25_correction.py — the register's third guard file"
  - "the inherited 25-D48-CONTINUATION pair, guarded for the first time"
affects:
  - ".planning/ROADMAP.md"
  - ".planning/REQUIREMENTS.md"
  - ".planning/phases/25-frontier-sweep-and-the-existence-gate-verdict/25-CONTEXT.md"
tech-stack:
  added: []
  patterns:
    - "retract-in-place via sentinel-bounded dated blocks, guarded through _prose.normalized"
    - "deletion budget asserted as a LITERAL against a pre-edit snapshot, never as a blanket zero"
    - "span-scoped absence checks with the pre-existing whole-document count held unchanged"
key-files:
  created:
    - tests/test_phase25_correction.py
  modified:
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md
    - .planning/phases/25-frontier-sweep-and-the-existence-gate-verdict/25-CONTEXT.md
decisions:
  - "D-02: SC1's binding comparator moves to the Phase 23 matched control; v2.0's 0.4921 / 0.3483 retained as a disclosed historical reference"
  - "D-19: FRONT-01's never-taught-floor clause is a DP-arm property; the adversarial axis terminates at its pool ceiling 1.9090909090909092"
  - "D-31: results/phase2X_frontier.json was a placeholder; the artifact is results/phase25_frontier.json"
  - "D-38: RPT-02 becomes a two-phase requirement; its DEFERRED traceability row is superseded, not rewritten"
  - "D-51: D-35's epsilon-scoping claim stands; only its closing 'Nothing to fix' is superseded"
  - "CTRL-02's clip_norm=inf is refused by the code; C = infinity is a finite 1e6 proven not to bind"
metrics:
  duration: ~55 min
  completed: 2026-08-31
  tasks: 3
  commits: 3
  files_changed: 4
---

# Phase 25 Plan 07: Dated Continuations and RPT-02's Discharge — Summary

Eight sentinel-bounded dated continuations across three planning documents, RPT-02 onto Phase 25's
Requirements line with its stale DEFERRED row superseded in place, and a third register guard file
that also picks up the one continuation pair in this phase that had shipped unguarded.

## What shipped

| Task | Tag / artifact | Document | Commit |
|------|----------------|----------|--------|
| 1 | `SC1-COMPARATOR` (D-02) | `.planning/ROADMAP.md` | `807ea2f` |
| 1 | `SC4-ARTIFACT-PATH` (D-31) | `.planning/ROADMAP.md` | `807ea2f` |
| 1 | `FRONT01-SCOPE` (D-19) | `.planning/REQUIREMENTS.md` | `807ea2f` |
| 1 | `CTRL02-CLIP-DOMAIN` | `.planning/REQUIREMENTS.md` | `807ea2f` |
| 1 | `D35-CONDITION-C` (D-51) | `25-CONTEXT.md` | `807ea2f` |
| 2 | `RPT02-SPAN` (D-38) + `, RPT-02` on the Requirements line | `.planning/ROADMAP.md` | `9a6d449` |
| 2 | `RPT02-ROW` (D-38) | `.planning/REQUIREMENTS.md` | `9a6d449` |
| 2 | `RPT02-DUPLICATE-COUNT` (D-38) | `.planning/REQUIREMENTS.md` | `9a6d449` |
| 3 | `tests/test_phase25_correction.py` | — | `d8dc010` |

Eight continuations, as planned. No count was silently changed.

## Additivity: insertions-only, quoted

Snapshots taken **before any edit in this plan** (`/tmp/25-07-roadmap.pre`,
`/tmp/25-07-requirements.pre`, `/tmp/25-07-context.pre`), so a prior task's insertions cannot
contaminate the reading. Final `git diff --no-index --numstat` against those snapshots:

```
57	1	/tmp/25-07-roadmap.pre => .planning/ROADMAP.md
74	0	/tmp/25-07-requirements.pre => .planning/REQUIREMENTS.md
36	0	/tmp/25-07-context.pre => .planning/phases/25-frontier-sweep-and-the-existence-gate-verdict/25-CONTEXT.md
```

`.planning/REQUIREMENTS.md` and `25-CONTEXT.md` are **insertions-only, deletion count 0**.
`.planning/ROADMAP.md`'s deletion count is **exactly 1**, and the single deleted line is proved
identical to the pre-edit `**Requirements**` line rather than merely counted:

```
$ git diff --no-index -U0 -- /tmp/25-07-roadmap.pre .planning/ROADMAP.md | grep '^-[^-]'
-**Requirements**: CTRL-01, CTRL-02, FRONT-01, FRONT-02, FRONT-03, FRONT-04, ADVT-01

exactly 1 deleted line and it IS the pre-edit Requirements line:
**Requirements**: CTRL-01, CTRL-02, FRONT-01, FRONT-02, FRONT-03, FRONT-04, ADVT-01
```

Per-task numstat against HEAD at the time of each commit: Task 1 `ROADMAP 42/0`,
`REQUIREMENTS 59/0`, `25-CONTEXT 36/0` (137 insertions, 0 deletions). Task 2 `30 insertions,
1 deletion`. No original claim was deleted, reworded, reflowed or moved.

**Zero `gsd-sdk` mutation handlers were called.** No `state.*`, `roadmap.*`, `phase.*` or
`requirements.*` verb was invoked at any point. Every planning-doc edit was made by hand through an
exact unique-anchor insertion script, with the anchor count asserted `== 1` before each replacement.

**`.planning/STATE.md` is byte-unchanged.** md5 `4542061054527300c89f121a29083a34` before the first
edit and after the last; its most recent commit is still `4492428`, which predates this plan.

## Verification

| Check | Result |
|-------|--------|
| Task 1 `<verify>` (assertive, self-contained) | `5 sentinel pairs unique and ordered; 5 measured values inside their own spans; 5 originals still standing` |
| Sentinel counts by `str.count` | `[('SC1-COMPARATOR', 1, 1), ('SC4-ARTIFACT-PATH', 1, 1)]`, `[('FRONT01-SCOPE', 1, 1), ('CTRL02-CLIP-DOMAIN', 1, 1)]`, `[1, 1]`, `[('RPT02-SPAN', 1, 1)]`, `[('RPT02-ROW', 1), ('RPT02-DUPLICATE-COUNT', 1)]` |
| `append_addendum` span scope | `0 of 5 Task-1 spans mention append_addendum; 2 pre-existing whole-document occurrence(s), out of scope` |
| Phase 25 Requirements line | `**Requirements**: CTRL-01, CTRL-02, FRONT-01, FRONT-02, FRONT-03, FRONT-04, ADVT-01, RPT-02` |
| Superseded originals survive | `both superseded originals survive` (`DEFERRED to Phase 25`, `0 orphans, 0 duplicates`) |
| `pytest tests/test_phase25_correction.py -v` | **23 passed, 0 skipped** |
| `-k sentinel` | **9 passed**, 14 deselected — the nine stems |
| `-k originals` | **8 passed**, 15 deselected — the eight superseded claims |
| `-k measured_values` | 1 passed, 22 deselected |
| `-k rpt02` | 7 passed, 16 deselected |
| `pytest tests/test_phase23_cost.py tests/test_phase24_correction.py -q` | 65 passed — the two earlier sweeps untouched |
| `grep -c` AST gate over the new file | `grep -c appears only in prose, never in executable code` |
| `git diff --exit-code` on the four frozen modules + `pyproject.toml` | exit 0 — byte-unchanged |
| `make lint` | `All checks passed!` / `238 files already formatted` |
| **Full suite** | **`1723 passed, 1 skipped`** |

**Delta: +23 over the 1700/1 baseline** — exactly the 23 cases `tests/test_phase25_correction.py`
adds (9 sentinel + 8 originals + 6 non-parametrized). No pre-existing test changed status.

## Watched RED — mechanic (3)

Driven through the **real** guard function with `_ROOT` pointed at a doctored copy in a temp tree;
the committed files were never mutated. One `BEGIN` sentinel duplicated on a single line in
`.planning/REQUIREMENTS.md`:

```
line-based count (the WRONG tool): 1
str.count (the tool mechanic 3 mandates): 2

WATCHED RED (real guard, tmp copy): .planning/REQUIREMENTS.md:
<!-- 25-07-CONTINUATION-FRONT01-SCOPE-BEGIN --> occurs 2 time(s); exactly one is required.
A missing or duplicated sentinel makes the guard scan the wrong text, which is how a guard
passes vacuously
```

The line counter returns **1** and `str.count` returns **2** on the same file — mechanic (3)'s
defect reproduced rather than argued.

## The ninth guarded pair

`25-CONTEXT.md`'s `25-D48-CONTINUATION` pair was written during planning, by no plan, and shipped
**unguarded**. It is now covered by (a), (b) and (c): sentinels unique and ordered, span carrying
`0.068930` / `results/phase20_retention_floor.json` / `0.005214448168350039` / `SUPERSEDED IN
PLACE`, and D-49's `the floor can never be loosened after seeing results` proved still standing
above it. It is a **guarded case, not a register instance** — RPT-02's register stays at **four
instances in three guard files** (23-12, 24-03, and this plan's two sweeps), and every "eight" in
Tasks 1, 2 and 3(f) stays eight. The module docstring says so explicitly so the next reader does not
reconcile 8 and 9 by changing the wrong one.

## Deviations from Plan

### [Rule 3 - Blocking] Task 2's `RPT02-ROW` is an adjacent NEW table row, not an in-line append

**Found during:** Task 2.
**Issue:** The plan requires `.planning/REQUIREMENTS.md`'s deletion count to be a literal **0**, and
requires the `RPT02-ROW` continuation to be appended to the RPT-02 traceability row. Those two
constraints are jointly unsatisfiable for an in-cell append: a markdown table cell is one line, so
appending inside it is recorded by git as one deletion plus one insertion — the shape the plan
explicitly permits *only* for the ROADMAP `**Requirements**` line.
**Fix:** The `DEFERRED` row is left **byte-unchanged** and its continuation is a new adjacent table
row, `| RPT-02 *(continued)* | Phase 20 (builds) → **Phase 25 (discharges)** | <sentinel-bounded
block> |`. It renders as part of the same table, sits immediately below the row it supersedes, and
keeps the deletion count at 0. Every property the plan asked of the block is unchanged.
**Files modified:** `.planning/REQUIREMENTS.md`. **Commit:** `9a6d449`.

### [Rule 3 - Blocking] Task 2's `pytest tests/test_phase25_correction.py -k rpt02 -x` criterion is unrunnable in Task 2

**Found during:** Task 2.
**Issue:** Blocker NEW-3 was closed for Task 1 but the same shape survives in Task 2's acceptance
criteria: `tests/test_phase25_correction.py` does not exist until Task 3, so that command exits 4
(collection error) at Task 2.
**Fix:** Task 2 was verified against its other five criteria, all inline `python -c`, all green. The
`-k rpt02` criterion was discharged in Task 3, where the file exists: **7 passed, 16 deselected**.
No criterion was dropped, only re-ordered to where it can run.
**Commit:** `9a6d449` (Task 2), `d8dc010` (the discharge).

### [Rule 2 - Disclosure] `scripts/phase25_record.py` does not exist at HEAD

**Found during:** Task 1(b).
**Issue:** The plan's SC4 text names `scripts/phase25_record.py`'s module constant as the authority
for the artifact path. That module is created by plan **25-08** (Wave 2) and does not exist yet.
Writing prose that cites a non-existent module as a present-tense authority is the misnamed-artifact
defect this project has hit repeatedly.
**Fix:** The continuation names the constant by symbol (`FRONTIER_RECORD` in
`scripts/phase25_record.py`) and **discloses in the same sentence** that it is *"the write-once
emitter plan 25-08 creates"*, so the citation is honest at HEAD. No acceptance criterion asserts the
module's existence; the guard asserts only that the span carries `results/phase25_frontier.json`.
Verified against `25-08-PLAN.md`, which creates `scripts/phase25_record.py` with
`FRONTIER_RECORD.name == 'phase25_frontier.json'`.
**Files modified:** `.planning/ROADMAP.md`. **Commit:** `807ea2f`.

### [Rule 2 - Correctness] `0 orphans, 0 duplicates` deliberately not quoted verbatim inside `RPT02-ROW`

**Found during:** Task 2(b).
**Issue:** The plan's action text quotes the dated 2026-08-20 `48/48 mapped, 0 orphans, 0
duplicates` line as the thing never to edit. Reproducing that full phrase inside the continuation
would create a second occurrence in the file, and mechanic (2) — searching for the marker from the
claim's own index — depends on the original being locatable. `tests/test_phase24_correction.py`
asserts claim uniqueness for exactly this reason.
**Fix:** The row cites it as *"the dated 2026-08-20 `48/48 mapped` line"*. The full phrase stays
**unique** in the file (measured: count 1), and Task 2's own criterion
`normalized('0 orphans, 0 duplicates') in q` passes against the original. The behavioural
instruction — never edit that line, only supersede it in place — was followed exactly.
**Files modified:** `.planning/REQUIREMENTS.md`. **Commit:** `9a6d449`.

### [Rule 3 - Blocking] `-k originals` needed a selector the fixed function name does not carry

**Found during:** Task 3.
**Issue:** The plan pins the function name `test_every_original_claim_survives_beside_its_continuation`
and separately requires `pytest -k originals` to collect 8 cases. The name contains `original`, not
`originals`, so `-k originals` would collect **0**.
**Fix:** The parametrization carries the selector: `ids=[f"originals-{stem.lower()}" ...]`, giving
node ids like `...[originals-25-07-continuation-sc1-comparator]`. The function name is unchanged and
the criterion is satisfiable: **8 passed, 15 deselected**. The reason is recorded in a comment above
the ids so it is not "cleaned up" later.
**Files modified:** `tests/test_phase25_correction.py`. **Commit:** `d8dc010`.

### [Rule 1 - Lint] One over-length line and one formatter difference

**Found during:** Task 3. `ruff check` reported E501 at 106 > 100 on the `_SUPERSEDED` table, and
`ruff format --check` wanted the `@pytest.mark.parametrize` call on one line. Both fixed; `make
lint` exits 0.

## Known Stubs

None. Every span carries measured values read from committed artifacts and live code, not
placeholders.

## Threat Flags

None. This plan touches planning prose and one CPU-only test module; it introduces no network
endpoint, auth path, file-access pattern or schema change at a trust boundary.

## Notes for the verifier

- **`DEFERRED to Phase 25` occurs twice** in `.planning/REQUIREMENTS.md` — the original row and the
  quotation inside `RPT02-ROW`, which sits below it. Mechanic (2) anchors at the original's index,
  so this is correct rather than ambiguous. Six of the eight superseded claims are quoted back
  inside their own continuation for the same reason; that is what makes searching from byte 0 wrong.
- **`append_addendum` was never used** and is not called anywhere in the new guard (asserted by
  AST). Its whole-document count across the three documents is held at its pre-existing **2**, with
  both sites pinned by content — `.planning/ROADMAP.md`'s `20-16-PLAN.md` bullet and
  `25-CONTEXT.md`'s `### Canonical References` bullet — never by line number.
- **No line-number citation drifted.** Every `ROADMAP.md:NN` / `REQUIREMENTS.md:NN` reference held in
  `scripts/` and `tests/` points above this plan's insertion points, so none moved.

## Self-Check

- `tests/test_phase25_correction.py` — FOUND
- `.planning/phases/.../25-07-SUMMARY.md` — FOUND (this file)
- `807ea2f`, `9a6d449`, `d8dc010` — all FOUND in `git log`

## Self-Check: PASSED
