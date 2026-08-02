---
phase: 15-figures-writeup
plan: "04"
subsystem: statistics / recorded verdict
tags: [VIZ-03, D-09, D-10, D-11, D-12, D-17, CR-02, spearman, gate-pass]
requires:
  - "scripts/phase15_stats.py @ 0e1af98 (the pre-registered rule, seed, sign, gate, renderer)"
  - "results/phase15_norms.json @ d1e9eee21062976c398474324a513269ea78846e (the D-05 artifact)"
  - "results/phase13_ab_report.md (committed Phase 13 evidence — appended to, never amended)"
provides:
  - "the Fisher/Δ Spearman ρ, its bootstrap CI and its permutation p — the numbers exist for the first time in commit 0e8b890"
  - "the recorded GATE PASSES verdict, adjacent to the Phase 13 data it is computed from (D-17)"
  - "the CR-02 section-anchoring constraint for Plan 15-08's D-17 test"
affects:
  - "Plan 15-05 (REPORT.md) — cites the verdict in D-16/D-04 terse form; must NOT restate the pre-registration table"
  - "Plan 15-07 (ROADMAP/README) — SC2 stands, bounded to the sign; the magnitude is descriptive"
  - "Plan 15-08 — its D-17 test MUST anchor on scripts/_verdict.py::VERDICT_SECTION, never a heading substring"
tech-stack:
  added: []
  patterns:
    - "renderer committed before the number, output appended verbatim — the presentation cannot be tuned to the result"
    - "append-only into a prior phase's committed evidence, proven by `git diff --numstat` showing 0 deletions"
    - "byte-identical re-render as the D-12 reproducibility proof (stronger than comparing reported digits)"
key-files:
  created:
    - ".planning/phases/15-figures-writeup/15-04-SUMMARY.md"
  modified:
    - "results/phase13_ab_report.md (+57 lines, 0 deletions)"
    - ".planning/phases/15-figures-writeup/deferred-items.md (DEF-15-01 update, +6 lines)"
decisions:
  - "GATE PASSES: ρ = 0.801544, 95% CI [0.597984, 0.920291] excludes zero, permutation p = 0.000010 — SC2's wording is SUPPORTED at the level the gate tests (the sign) and no further; the magnitude stays descriptive at n = 36"
  - "The plan's own Task-1 verify literal ('does not reopen or amend') is split across a line break by the pre-registered renderer — the VERIFY command was corrected (whitespace-normalized), never the renderer, which must stay byte-unchanged since 0e1af98"
  - "Two fresh processes plus one in-process recomputation produced byte-identical output; the committed section is `rep.endswith(fresh_render)` True"
metrics:
  duration: 14min
  tasks: 2
  files: 2
  completed: 2026-08-02
---

# Phase 15 Plan 04: Fisher/Δ Correlation Verdict Summary

Ran the rule that was committed before the artifact existed, and recorded what it returned:
**the gate PASSES** — EWC's Δ-reduction tracks Fisher magnitude across all 36 cells with
ρ = 0.801544 and a 95% bootstrap CI that clears zero by a wide margin.

## RECORD VERBATIM — the numbers Plans 15-05 and 15-07 consume

| Quantity | Value |
|----------|-------|
| Spearman ρ | **`0.801544`** (raw `0.8015444015444017`, `average_rank_pearson_fp64`, n = 36) |
| 95% CI | **`[0.597984, 0.920291]`** (raw lo `0.5979835246758984`, hi `0.9202912618381133`; `percentile_bootstrap`, 10000 resamples, seed 1337) |
| Permutation p | **`0.000010`** (raw `9.99990000099999e-06`; 100000 shuffles, seed 1337) — **descriptive only** |
| Degenerate resamples dropped | **`0`** of 10000 |
| Verdict | **`GATE PASSES`** |
| Source artifact | `results/phase15_norms.json` @ git_sha `d1e9eee21062976c398474324a513269ea78846e`, built `2026-08-02` |
| Pre-registration | `scripts/phase15_stats.py` @ `0e1af98` |
| Recorded | `2026-08-02` |

The permutation p of `1.0e-5` is the **add-one floor** at `N_PERM = 100000`: **zero** of 100,000
shuffles produced a |ρ| at or above the observed one. Report it as `p = 0.000010`, not as
"p < 0.00001" and never as "p = 0" — the add-one correction exists precisely so the p is never
reported as exactly zero.

## SC2 wording — NOT narrowed (the miss branch was not taken)

ROADMAP SC2's *"showing EWC visibly dodging high-Fisher coordinates"* **stands**, and the
renderer's own committed sentence is the exact bound Plans 15-05 and 15-07 must carry:

> ROADMAP SC2's "showing EWC visibly dodging high-Fisher coordinates" wording is supported at the
> level the gate tests — the sign — and no further.

Two things follow, and both must survive into REPORT.md and ROADMAP:

1. **The sign is what passed.** ρ = 0.80 is a strong number, but D-11 pre-registered the magnitude
   as descriptive with **no gate**. "Strongly correlated" is reportable; "EWC dodges 80% of the
   high-Fisher movement" is not — that reads a rank correlation as an effect size.
2. **n = 36 still bounds it.** The pre-registered `_BOOTSTRAP_BIAS_NOTE` — percentile bootstrap is
   biased and anti-conservative at small n — travels **with** the CI into the report. It was
   written before the number and does not get dropped because the number came out favorable. That
   is the same asymmetry the miss branch would have faced.

The `"suggestive but not statistically demonstrated at n = 36"` register was **not** used, because
the gate cleared. It is not in the file, and Plans 15-05/15-07 must not import it.

## CR-02 — the constraint Plan 15-08's D-17 test inherits

`results/phase13_ab_report.md` now contains the literals `## Pre-Registration`, `## Gate Verdict`
and `## Verdict` **twice**: once as real Phase 13 headings, and once quoted inside the addendum's
own HTML separation comment. Additionally the addendum's `### Verdict` sub-heading is a
`## Verdict` **prefix match** for anything doing substring searching.

**Any guard or test reading a section of this report MUST anchor on the SECTION via
`scripts/_verdict.py::VERDICT_SECTION`, never on `text.split("## Verdict")[-1]`.** The naive tail
lands inside this addendum's prose. That is verbatim the CR-02 failure recorded at
`scripts/phase14_recall.py:1627-1635` — the failure that made `--force` mandatory on every
legitimate re-drive and thereby armed the guard to destroy the hand-written evidence it existed to
protect. Plan 15-08's `test_verdict_section_is_dated_and_separated` must be written
section-anchored **from the start**, not retrofitted.

Note also: `scripts/_verdict.py::VERDICT_SECTION` (`^## Verdict\b`) currently matches **nothing**
in this file — Phase 13's heading is `## Gate Verdict` and the addendum's is `### Verdict`. A test
that anchors on `## Phase 15 Addendum` (as this plan's own verify does) is the correct pattern
here; `recorded_verdict()` returning `None` on this file is expected, not a bug.

## What Was Built

| Task | Commit | What landed |
|------|--------|-------------|
| 1 | `0e8b890` | The renderer's verbatim output appended to `results/phase13_ab_report.md` — 57 insertions, **0 deletions** |
| 2 | `4fcf314` | Reproducibility check (no artifact change) + the DEF-15-01 update |

## Reproduction — the D-12 requirement, three independent computations

| Run | How | ρ | p | CI lo | CI hi | degenerate |
|-----|-----|---|---|-------|-------|------------|
| 1 | fresh process, `.venv/bin/python scripts/phase15_stats.py` | `0.801544` | `0.000010` | `0.597984` | `0.920291` | `0` |
| 2 | fresh process, same command | `0.801544` | `0.000010` | `0.597984` | `0.920291` | `0` |
| 3 | in-process `importlib` load, `permutation_p` + `bootstrap_ci` called directly | `0.8015444015444017` | `9.99990000099999e-06` | `0.5979835246758984` | `0.9202912618381133` | `0` |

**They matched.** `diff run1 run2` is empty — the two renders are **byte-identical**, including
the `**Recorded:**` line (both ran the same UTC day, so the one field permitted to differ did
not). Run 3 reproduces the same values at full float precision through a different entry point.

Stronger still: `results/phase13_ab_report.md`**`.endswith(fresh_render)` is `True`** — the
committed section is not merely numerically equal to a re-render, it is byte-for-byte the same
text. D-12's *"reproducible byte-for-byte from the committed artifact, not dependent on whatever
shuffle order a given run happens to draw"* is satisfied literally.

`git diff --stat scripts/phase15_stats.py` and `git status --short scripts/phase15_stats.py` are
both **empty**: no pre-registered constant, no gate, no renderer line moved after the number
appeared. The T-15-09 mitigation held, and git history is its audit trail.

## Verification Results

| Check | Result |
|-------|--------|
| `git diff --numstat results/phase13_ab_report.md` | **`57  0`** — zero deletions, purely additive |
| Append point | after the closing `## Evidence Index` table row; the diff hunk starts at line 371 |
| `## Phase 15 Addendum` is the LAST `## ` heading | `True` |
| Section carries `Recorded:` + a `GATE PASSES`/`GATE MISSES` line | `True` / `True` |
| Section states it does not reopen or amend Phase 13 | `True` (whitespace-normalized — see Deviation 1) |
| `grep -qF "Recorded: $(date -u +%Y-%m-%d)"` | PASS (`2026-08-02`) |
| `grep -qF 'phase15_stats.py'` / `'phase15_norms.json'` | PASS / PASS |
| Section carries `### Pre-Registration` / `### Result` / `### Verdict` / `### Evidence Index Addendum` | all present |
| Recomputed ρ and CI lo appear in the committed section | `True True` |
| `ewc_dodges_high_fisher(rho, lo, hi)` matches the recorded line | `True` = `GATE PASSES` |
| Two fresh runs byte-identical (`diff`) | IDENTICAL |
| Committed tail byte-identical to a fresh render | `True` |
| `git diff --stat scripts/phase15_stats.py` | empty — unchanged since `0e1af98` |
| `.venv/bin/pytest -q` full suite | **403 passed, 1 skipped** — exactly the entry baseline, no regression |
| Lint, pinned `.venv/bin/ruff` (the `pyproject.toml` pin CI installs) | `All checks passed!` / `138 files already formatted` |
| No code path reads this report (`grep -rn phase13_ab_report scripts tests src`) | 3 hits, all docstrings — no guard to break |

## Deviations from Plan

### 1. [Rule 1 — Bug] The plan's Task-1 verify literal is broken by the renderer's line wrap

- **Found during:** Task 1 (running the `<automated>` verification command)
- **Issue:** The command tests `'does not reopen or amend' in section`, which returned **`False`**.
  The pre-registered renderer emits that phrase across a hard line break —
  `...it does not reopen\nor amend Phase 13's pre-registered content...` — so the unwrapped
  literal does not appear in the file. Every other conjunct in the command was `True`.
- **Fix:** the **verification command** was corrected (whitespace-normalize the section before the
  substring test: `'does not reopen or amend' in ' '.join(body.split())` → `True`). The **file was
  not touched** and `scripts/phase15_stats.py` was **not** touched.
- **Why the fix went to the verifier and not the renderer:** rewrapping that comment would edit a
  file committed at `0e1af98` *before the number existed*, which is exactly the T-15-09 tampering
  this plan's own acceptance criteria forbid (`git diff --stat scripts/phase15_stats.py` must show
  no change). A cosmetic reflow to satisfy a grep would have destroyed the pre-registration
  property to fix a test string. The plan's `must_haves` truth — that the section is explicitly
  marked as Phase 15 material that does not reopen or amend Phase 13 — is satisfied in substance
  and is what Plan 15-08 should assert (whitespace-normalized, or anchored on the shorter
  unwrapped fragment `does not reopen`).
- **Files modified:** none.
- **Commit:** n/a (verification-only correction).

### 2. One blank line inserted before the appended section

`printf '\n' >> results/phase13_ab_report.md` ran before the append, so the renderer's leading
`---` does not sit flush against the Evidence Index's last table row (where CommonMark could read
it as a setext underline rather than a thematic break). This is one added newline, still zero
deletions, and the rendered section itself is byte-verbatim from the script's stdout.

### 3. `make lint` still resolves the stale global ruff (DEF-15-01, unchanged, out of scope)

Third consecutive plan hitting this. `Makefile:16` calls bare `ruff` → pyenv shim →
**ruff 0.1.15**, which now flags **two** files: `tests/test_gpt_lora_seam.py` (Phase 04) and
`tests/test_phase15_plots.py` (Plans 15-02/15-03). **This plan modified zero Python files**, so
neither can be its doing. The pinned `.venv/bin/ruff` (0.15.16) is clean across all 138 files.
Logged as an update under the existing `DEF-15-01` rather than a new entry; the one-line fix
(point `Makefile:16` at `.venv/bin/ruff`) is unchanged.

## Known Stubs

None. This plan wrote no code — it ran already-committed code and recorded what it returned.

## Threat Flags

None. This plan introduced no network endpoint, no auth path, no file-access pattern and no schema
at a trust boundary. It ran one pure-numpy module over the project's own committed JSON and
appended text. T-15-09 (re-seeding after seeing the number) is mitigated and **verified**:
`scripts/phase15_stats.py` is byte-unchanged since `0e1af98`. T-15-13 (the append appearing to
amend Phase 13) is mitigated and **verified**: 0 deletions, dated section, explicit separation
comment, last heading in the file. T-15-SC: zero packages installed.

## What Plans 15-05 / 15-07 / 15-08 Must Carry

- **15-05 (REPORT.md):** terse form only — pass/fail plus ρ, linking to the full pre-registration
  table in `phase13_ab_report.md` (D-17/D-16/D-04). Do **not** restate the table. Carry the
  "supported at the level the gate tests — the sign — and no further" bound and the small-n
  bootstrap-bias note; both are pre-registered, not optional garnish.
- **15-05, load-bearing consistency check:** Plan 15-03 recorded that EWC moved **more** in two of
  the 36 cells (layer 0/`q_proj` −0.015185, layer 1/`q_proj` −0.006607). Those two negatives are
  **inside** this ρ — all 36 signed values were used, none filtered. A report sentence claiming
  EWC reduced movement everywhere would contradict both 15-03's grid and this correlation's own
  input.
- **15-07 (ROADMAP/README):** SC2 stands unnarrowed. Record ρ = 0.801544 with its CI in the same
  sentence, at 547-live-ids density (D-16) — never a bare coefficient.
- **15-08 (D-17 test):** anchor on the **section**, never a heading substring (see the CR-02
  section above). Assert the date line, the `GATE PASSES` line, the separation comment, and that
  `## Phase 15 Addendum` is the last `## ` heading.

## Self-Check: PASSED

- `results/phase13_ab_report.md` — FOUND (+57/−0, addendum is the last `## ` heading)
- `.planning/phases/15-figures-writeup/deferred-items.md` — FOUND (DEF-15-01 updated)
- `scripts/phase15_stats.py` — FOUND and **unchanged** since `0e1af98`
- `results/phase15_norms.json` — FOUND, cited by `git_sha d1e9eee2…`
- Commit `0e8b890` — FOUND in `git log`
- Commit `4fcf314` — FOUND in `git log`
- Pre-registration commit `0e1af98` — FOUND, and precedes the artifact commit `d1e9eee`
