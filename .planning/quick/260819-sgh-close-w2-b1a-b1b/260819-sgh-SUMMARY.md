---
phase: quick-260819-sgh
plan: 01
subsystem: docs
tags: [dated-continuation, append-only, audit-closure, stat-02, stat-06]

requires:
  - phase: 19
    provides: "the canonical A-E defect labels at results/phase19_erasure_report.md:564-574, and the 2026-08-19 retroactive scope limit at results/phase18_extraction_report.md:340-405"
provides:
  - "README's dated A-E labelling section, retiring the four-defect undercount republished at :253-255"
  - "docs/REPORT.md's dated deep-link redirect, scoping the rank-only Phase 18 exposure table the pointer at :1140-1141 sends readers to"
  - "the Phase 18 report's dated mechanism continuation, reconciling item (4) sitting inside the scope limit with the verdict being exempt"
affects: [v3.0 milestone audit, any future correction to published dated evidence]

tech-stack:
  added: []
  patterns:
    - "identity marker pair (pending=recorded) turns scripts/_addendum.append_addendum into a provable pure-append writer for a file whose PENDING marker is already consumed"

key-files:
  created: []
  modified:
    - README.md
    - docs/REPORT.md
    - results/phase18_extraction_report.md

key-decisions:
  - "B1-a shipped as an appended section rather than the audit's suggested in-place pointer edit: docs/REPORT.md:1145 asserts no line above its heading is altered, so editing the pointer at :1140-1141 would falsify a published claim two lines below it"
  - "All three writes are pure insertions at EOF; no published dated text was edited in place anywhere"
  - "Task 3 was driven by a throwaway scratchpad script, not a new committed file under scripts/ — matching the precedent at 7af6006"

patterns-established:
  - "Undercounts on a high-traffic surface are corrected by a dated continuation that names the earlier phrasing and leaves it standing, never by an in-place edit"

requirements-completed: [ATK-04, ERASE-01, STAT-02, STAT-06]

duration: 27min
completed: 2026-08-19
---

# Quick 260819-sgh: Close W2, B1-a and B1-b Summary

**Three published statements their own sources had superseded — README's four-defect undercount, the deep link that lands 190 lines above the limit scoping what it points at, and B1's asserted-but-unshown exemption — closed as dated continuations, with zero deletions across all three files.**

## Performance

- **Duration:** ~27 min
- **Tasks:** 3/3
- **Files modified:** 3 (47 + 47 + 59 insertions, **0 deletions**)

## Accomplishments

- **W2 closed.** `README.md` now names all five published pin defects by the canonical letters **A**–**E** with their lines in the closed pin (`:1562`/`:2948`, `:3850-3855`, `:2922`, `:3811`, `:3576`), states the four-vs-five distinction (A–D block the pin's own `_cmd_report`; **E** sits in the `erase` subcommand, a path the render never called), and records that its own earlier "four published defects" phrasing at `:253-255` undercounts the phase when read as a complete enumeration — because README, unlike the erasure report, grants itself no in-file exemption.
- **B1-a closed.** `docs/REPORT.md` carries a dated section telling the deep-link reader that the exposure table at `results/phase18_extraction_report.md:145-154` (eight slots, every one rank 1, no generation number beside any of it) is a rank-only reading now scope-limited by the dated continuation at `:340-405` of that same file, and that item (4)'s 73 zero-cells at `:236` sit inside the limit rather than in its exemption. It states in so many words why the pointer at `:1140-1141` was deliberately left byte-intact.
- **B1-b closed.** `results/phase18_extraction_report.md` now states the mechanism the previous continuation was missing, from the code and by line: `scripts/phase18_extraction.py:1636` reads `exposure_rank` as a **presence check only** (`is None` is the sole operator applied to it anywhere in `null_result_is_admissible` — the identifier occurs exactly twice in the whole gate, once in the docstring at `:1567`), and `:1657`'s terminal ternary decides the verdict on `attack_successes`, i.e. on **generation**. Both facts were re-verified against the pin this session before being published.
- **Nothing retracted anywhere.** `FAILURE`, `DO NOT SHIP`, `LEAKAGE_DEMONSTRATED`, 92/104, the 0/104 control and every measurement stand exactly as published.

## Task Commits

1. **Task 1 — W2, README A–E labelling section** — `4012a61` (docs), 47 insertions / 0 deletions
2. **Task 2 — B1-a, docs/REPORT.md deep-link redirect** — `c90d0c8` (docs), 47 insertions / 0 deletions
3. **Task 3 — B1-b, Phase 18 report mechanism continuation** — `98d0a60` (docs), 59 insertions / 0 deletions

## Verification — actual output

**Flip gates, all three moved:**

| gate | before | after |
| --- | --- | --- |
| `grep -cE '\*\*E\*\*\|defect E' README.md` | 0 | **3** |
| `grep -c ':340' docs/REPORT.md` | 0 | **1** |
| `grep -ci 'null_result_is_admissible' results/phase18_extraction_report.md` | 3 | **5** |

**Purity gates — `git diff --numstat 07391cd HEAD`:**

```
47	0	README.md
47	0	docs/REPORT.md
59	0	results/phase18_extraction_report.md
```

Deletions column is `0` on every row.

**Byte-prefix gates vs `07391cd`:** `PREFIX OK` on all three files. `docs/REPORT.md` lines 1140, 1141 and 1145 compare byte-identical (`PINNED LINES 1140/1141/1145 OK`).

**Task 3 specifics:** written through `scripts/_addendum.append_addendum` under the identity pair `pending=recorded=EXTRACTION_SHIP_RECORDED_LINE` (both imported off the pin by `spec_from_file_location`, never retyped). Post-write markers unchanged: RECORDED **1**, PENDING **0**. `## Verdict` block byte-identical to `07391cd` with `LEAKAGE_DEMONSTRATED` intact; the entire pre-edit file is a byte-exact prefix of the new one (the identity replacement was a provable no-op).

**Suite:** `845 passed, 1 skipped` in 188.01s — exactly the stated baseline.
**Lint:** `ruff check` → `All checks passed!`; `ruff format --check` → `170 files already formatted`.
**STAT-02:** bare-zero-percentage count stays `0` on all three files.
**STAT-04:** `pyproject.toml` / `requirements.txt` untouched (empty `git diff --stat`).
**Frozen pins:** none in the diff — `git diff --name-only 07391cd HEAD | grep -E 'scripts/(phase18_extraction|phase19_erasure|erasure_gate|phase19_floor|phase17_isolation)\.py'` returns nothing.
**No file added under `scripts/`** — the Task 3 driver is a throwaway in the session scratchpad.

## Deviations from Plan

**None affecting content.** Two scope carve-outs applied per the executor's constraints, both stated here rather than silently:

1. **`.planning/STATE.md` was NOT edited or committed** — the orchestrator owns it. The plan's execution context folds a STATE.md update into the standard flow; that step was **skipped** deliberately.
2. **`.planning/ROADMAP.md` was NOT updated**, and no `.planning/` docs artifact (PLAN.md, this SUMMARY.md) was committed — the orchestrator commits those. The three task commits contain content files only.

One drafting judgement worth recording: the plan's Task 1 spec allowed "a markdown table or a bulleted list" for the A–E labels. A **table** was chosen so the appended section introduces no line beginning with `- `, which keeps `tests/test_phase15_docs.py::test_headline_numbers_match_sources`'s `\n(?=- )` bullet split untouched by the append. The three forbidden literals (`0.3483`, `8.52417066884246`, `3.229`) are absent from the appended region and each still occurs exactly once file-wide.

## Threat Flags

None. Documentation-only change, no new network surface, no auth path, no schema change, no dependency change.

## Known Stubs

None.

## Self-Check: PASSED

- Commits `4012a61`, `c90d0c8`, `98d0a60` — all `FOUND` in `git log --oneline --all`.
- `README.md`, `docs/REPORT.md`, `results/phase18_extraction_report.md` — all `FOUND` on disk.
- Working tree clean apart from the untracked `.planning/quick/260819-sgh-close-w2-b1a-b1b/` directory the orchestrator owns.
