---
phase: 15-figures-writeup
plan: "08"
subsystem: doc-integrity tests / D-15, D-16, D-17 made structural
tags: [DOC-02, VIZ-02, VIZ-03, D-15, D-16, D-17, D-02, D-04, D-18, SC3, CR-02, R1, R2]
requires:
  - "docs/REPORT.md (15-05 @ b8db4ae) — the nine Limitations blockquotes, the pinned headings, the figures disclosure"
  - "README.md (15-06 @ ff5ca2a) — the three headline bullets and the Limitations anchor"
  - "demo_v2.ipynb (15-07 @ 25eaa54) — the second linking file"
  - "results/phase13_ab_report.md (Phase 13 + the 15-04 addendum @ 0e8b890) — the D-17 append"
  - "results/phase15_norms.json (15-02 @ f68450a) — vmax_driver, nonpositive_cells, blocks.fisher.variant"
  - "15-05-PLAN.md <verbatim_normalization> — the pinned normalize_quote helper, copied verbatim"
provides:
  - "tests/test_phase15_docs.py — 4 permanent CPU-only tests converting D-15/D-16/D-17 from prose policy into structure"
  - "the terminal wave-5 gate result: 407 passed / 1 skipped / 0 failed"
affects:
  - "nothing downstream — Phase 15 is terminal for the v2.0 milestone"
tech-stack:
  added: []
  patterns:
    - "committed-prose-under-test: the first tests in this repo asserting markdown wording against its cited source"
    - "both-sides normalization — a normalized quote is never compared against a raw source"
    - "self-citation handled by excising the citing section, not by shelling out to `git show`"
    - "section-anchored reads in the scripts/_verdict.py::VERDICT_SECTION shape, never last-occurrence substring"
key-files:
  created:
    - "tests/test_phase15_docs.py (544 lines, 4 tests)"
  modified: []
decisions:
  - "L8's source is docs/REPORT.md itself, so it is compared against the report MINUS the anchored Limitations section — the same guarantee 15-05 got from `git show HEAD:docs/REPORT.md`, but without importing subprocess, which the plan's own acceptance criterion forbids"
  - "The vmax assertion pins the COMPOSED phrase `layer N's \\`proj\\`` plus the artifact's full float value, not the projection name alone: `q_proj` and the digit `1` both appear all over the section, so the loose form would pass on a disclosure that had drifted"
  - "The forbidden `split(\"## Verdict\")` literal is spelled out NOWHERE in the file, not even in the prose explaining why it is forbidden, so the plan's `grep -c` acceptance check stays a usable future guard rather than being permanently pinned at 1"
metrics:
  duration: 34min
  tasks: 2
  files: 1
  completed: 2026-08-02
---

# Phase 15 Plan 08: Doc-Integrity Tests Summary

Converted D-15, D-16 and D-17 from prose policy into four permanent CPU-only tests: every
Limitations quote must reproduce its cited source's exact wording, every README headline number
must match its source and keep its qualifier, and the Phase 15 verdict append must stay dated,
marked and last — so softening the narrative is now a test failure, not a proofreading miss.

## What Was Built

| Task | Commit | What landed |
|------|--------|-------------|
| 1 | `e8f4beb` | `tests/test_phase15_docs.py` — `normalize_quote`, the nine-quote fixture, `test_limitations_quotes_are_verbatim`, `test_headline_numbers_match_sources` |
| 2 | `1ce2142` | `test_verdict_section_is_dated_and_separated`, `test_report_names_the_artifact_vmax_driver`, docstring inventory extended to four |

544 lines, 4 tests, zero files modified outside `tests/`.

## THE GATE — final counts

| Check | Result |
|-------|--------|
| `.venv/bin/pytest -q tests/test_phase15_docs.py` | **4 passed** |
| `.venv/bin/pytest -q` (full suite, all six checkpoints present) | **407 passed, 1 skipped, 0 failed** in 116.81 s |
| Skip identity (`-rs`) | `tests/test_train_loop.py:81: fp16 AMP smoke needs a CUDA GPU` — the one pre-existing skip, exactly as the plan's `<verification>` predicts |
| Regression against the entry baseline | **none** — 403 + 4 = 407, and the skip count did not move |
| Lint, pinned `.venv/bin/ruff` (the `ruff~=0.15` pin CI installs) | `All checks passed!` / `140 files already formatted` |
| `make lint` (bare `ruff`) | **FAILS on the stale global 0.1.15** — DEF-15-01, see Deviation 1 |
| `grep -c 'import torch' tests/test_phase15_docs.py` | `0` |
| `grep -c 'split("## Verdict")' tests/test_phase15_docs.py` | `0` |
| AST check: no `subprocess` import | `True` |
| `git status --porcelain` — Phase 15 deliverables | both PNGs, `results/phase15_norms.json`, `demo_v2.ipynb` and all three `test_phase15_*.py` tracked and committed |
| Post-commit deletion check, both commits | `git diff --diff-filter=D` empty |

**The plan's text says "392-test baseline"; the real entry baseline was 403 passed / 1 skipped**
(Plans 15-02/15-03/15-04 had already landed their tests by the time this plan ran, and 15-04
through 15-07 each recorded 403/1). 407 is therefore exactly baseline + this plan's 4, and the
plan's `≥ 407 passed, exactly 1 skipped` criterion is met on the nose. **No third skip appeared.**

## RED / GREEN observations — every guard seen to fail, and seen to stay green under a legal edit

The plan requires four observations. All four were made against the real committed files, each
backed up to the scratchpad first and byte-restored after (`git status --short` clean each time).

### RED 1 — one word altered inside a Limitations blockquote

Changed L5's closing clause in `docs/REPORT.md` from `than "everything the adapter was taught."`
to `than "most of what the adapter was taught."` — one softening word, the exact drift vector
D-15 exists to close.

```
AssertionError: L5: this quote is no longer in docs/REPORT.md's Limitations section
as written — a word, digit, punctuation mark or emphasis marker changed
```

**It named the limitation**, which is what makes the failure actionable rather than a diff hunt.

### GREEN under a legal re-wrap — the scope proven right in the OTHER direction

Re-wrapped that same L5 blockquote from 3 lines to 4 at a 62-column width, asserting first that
the word sequence was byte-identical and only the line breaks moved. **`4 passed`.** This is the
observation the plan calls out as the one that stops the rule being weakened later: a guard nobody
has seen stay green under a *legitimate* edit is a guard someone will eventually relax. The
normalization is neither too tight (a rewrap does not fail) nor too loose (a single word does).

### RED 2 — a README headline number changed

Changed README's held-out recall from `0.3483` to `0.4483`:

```
AssertionError: recall (held-out): 0.3483 is no longer on the front page
```

### RED 3 — the Phase 15 addendum repositioned

Moved the whole `## Phase 15 Addendum` section above `## Evidence Index` in
`results/phase13_ab_report.md` — the "blended into Phase 13's recorded content" failure:

```
AssertionError: the Phase 15 addendum is no longer the last `## ` heading
(last is '## Evidence Index') — an append that sits among Phase 13's sections
reads as amending them
```

## How each prior-wave warning was honored

| Warning | Where it landed |
|---------|-----------------|
| **15-04:** never `split("## Verdict")[-1]`; anchor on `## Phase 15 Addendum` | `_anchored_section()` is the ONE anchored read (`^heading\b … (?=^stop\|\Z)`), used by all three section-scoped tests; the D-17 test anchors on `## Phase 15 Addendum` and its docstring cites CR-02 and records that `VERDICT_SECTION` matches nothing in this file |
| **15-05:** L1–L9 render out of numeric order | No numeric-order assertion anywhere. The ordering pinned is the **claim-bound** one — the four `### Bounding "…"` headings' positions must be increasing |
| **15-05:** keep `### The Two Signature Figures` bounded | The figures test anchors `^### The Two Signature Figures` → next `^#{2,3} `, and its meta-guard asserts the section is non-empty *before* any content assertion; a comment records that 15-05 had to add two following `###` headings for this to mean anything |
| **15-05:** verify L8 against its SOURCE, not against `docs/REPORT.md` itself | L8's source text is `report.replace(section, "")` — the report **minus** its Limitations section — with a guard asserting the excision actually shortened the text. No `subprocess`, so the plan's no-shell-out criterion holds too |
| **15-06:** pin `1.129` without the unit char | `1.129` is **not** in the fixture at all: the three pinned numbers are `0.3483` / `8.52417066884246` / `3.229`, exactly the triples 15-06 recorded |
| **15-06:** split README on `\n(?=- )`, not on lines | That is the literal split, with an assertion that the split produced more bullets than there are headline numbers |
| **15-06:** the anchor is `#milestone-2-limitations--nine-honest-negatives-quoted` | Never typed. Derived by `_github_anchor()` from the heading **as read out of `docs/REPORT.md`**, then asserted present in both README and `demo_v2.ipynb` |
| **15-07:** demo_v2's `checkpoints/` gate is code-cells-only | Not re-litigated here — this file makes no `checkpoints/` assertion about `demo_v2.ipynb`; it only checks the outbound link, which is a whole-file question |
| **15-07:** `demo.ipynb` cell indices shifted | No test in this file indexes a notebook cell |
| **The verdict:** gate PASSED; the miss phrase is absent by design | `("GATE PASSES" in body) != ("GATE MISSES" in body)`, and the `suggestive but not statistically demonstrated at n = 36` register is asserted **only inside the `GATE MISSES` branch** — dormant, with a comment saying so, so a future re-drive that misses cannot record it in softer language than the one locked in advance |
| **SC3 variant string** | Read from `blocks.fisher.variant`, never hardcoded a second time, and asserted inside the anchored figures section |

## Deviations from Plan

### 1. `make lint` fails on the stale global ruff — DEF-15-01, seventh consecutive plan, still out of scope

- **Found during:** Task 2's terminal gate.
- **Issue:** `Makefile:16` calls bare `ruff` → pyenv shim → **ruff 0.1.15**, which "would reformat"
  three files: `tests/test_gpt_lora_seam.py` (Phase 04), `tests/test_phase15_plots.py`
  (Plans 15-02/15-03) and `tests/test_phase15_docs.py` (this plan). The pinned `.venv/bin/ruff`
  (0.15.x — the `ruff~=0.15` that `pyproject.toml [dev]` declares and CI installs) reports
  `All checks passed!` and `140 files already formatted`.
- **Why it is not this plan's doing:** two of the three flagged files predate this plan entirely.
  A 0.1.15-vs-0.15 formatting disagreement is a binary-version artifact, not a defect in any file.
- **NEW information worth recording — the deferred item's stated one-line fix is WRONG.**
  DEF-15-01 has been logged five times as "point `Makefile:16` at `.venv/bin/ruff`". Checked this
  run: `.github/workflows/ci.yml:25` runs `ruff check . && ruff format --check .` **bare**, in an
  environment where `pip install .[cpu,dev]` put ruff 0.15 on `PATH` with no `.venv/` present.
  Hardcoding `.venv/bin/ruff` in the Makefile would therefore **break CI**. The correct fix is
  `python -m ruff` (or a `RUFF ?= ruff` variable), not a hardcoded venv path. Recorded in
  `deferred-items.md` rather than applied: changing the lint entry point is a build-config change
  that alters CI behaviour, outside a plan whose only artifact is a test file.
- **Files modified:** none.

### 2. The forbidden `split("## Verdict")` literal is described, never spelled

- **Found during:** Task 2 acceptance checking.
- **Issue:** the D-17 test's docstring originally quoted `text.split("## Verdict")[-1]` as the
  thing it must not do. That made the plan's own acceptance check —
  `grep -c 'split("## Verdict")' tests/test_phase15_docs.py` returns 0 — return **1**, and worse,
  it would have permanently blunted that grep as a future guard by pinning its floor above zero.
- **Fix:** the docstring now names the forbidden call in prose (a `str.split` on the
  `## Verdict` heading literal taking `[-1]`) and states explicitly that the exact call is spelled
  nowhere in the file so the grep stays usable. The explanation and the CR-02 citation are intact.
- **Files modified:** `tests/test_phase15_docs.py` (Task 2, pre-commit).

### 3. `positions`-in-f-string rewritten for Python 3.11

- **Found during:** Task 1, first run — a `SyntaxError` at import.
- **Issue:** the claim-ordering assertion's message used a multi-line expression inside an
  f-string. That is **PEP 701, Python 3.12+**; this project pins **3.11** (`CLAUDE.md`, CI,
  `.venv`). A 3.12-only construct would have been a collection error on every supported runtime.
- **Fix:** the comprehension was hoisted to an `absent` local before the assert.
- **Files modified:** `tests/test_phase15_docs.py` (Task 1, pre-commit).

## Known Stubs

None. All four tests assert against real committed files, every assertion was observed to be
capable of failing (three RED proofs plus the count/meta-guards), and no assertion is a
placeholder. The one deliberately dormant branch — the `GATE MISSES` register check — is dormant
because the gate *passed*, is guarded by an XOR that would fail if both or neither verdict string
were present, and carries a comment saying why it exists.

## Threat Flags

None. This plan added one pytest module that reads four markdown files, one JSON artifact and one
notebook from disk. No endpoint, no auth path, no new file-access pattern, no schema at a trust
boundary, no network, no torch, no `subprocess`. Its own `<threat_model>` is covered and
**verified by observation**, not asserted:

- **T-15-05** (a Limitations quote paraphrased/softened/reordered) — mitigated; RED 1 proves it
  fires on a one-word softening and names the limitation, and the re-wrap proves it does not fire
  on presentation.
- **T-15-26** (the verbatim rule weakened at wave 5 to make the blockquote register satisfiable) —
  mitigated by construction: `normalize_quote` was **copied**, not re-derived, and is two
  `re.sub` calls plus `.strip()`. No case fold, no punctuation substitution, no ellipsis handling,
  no smart-quote folding. Its docstring names adding any of those a D-15 **violation**.
- **T-15-19** (a README number drifting or losing its qualifier) — mitigated; RED 2 proves the
  drift half, and the per-bullet keyphrase assertion covers the qualifier half.
- **T-15-13** (the addendum blending into or displacing Phase 13) — mitigated; RED 3 proves the
  positioning half, and the six-heading survival check covers the displacement half.
- **T-15-14** (a guard fooled by a heading quoted in prose — the CR-02 failure) — mitigated; one
  anchored reader, `grep -c 'split("## Verdict")'` = 0, CR-02 cited in the docstring.
- **T-15-24** (figure and report disagreeing about the vmax driver; SC3's variant unnamed) —
  mitigated; every driver phrase, driver value, `nonpositive_cells` count and the variant string
  are read **from the artifact** and asserted inside the anchored figures section.
- **T-15-25** (a dangling cross-document anchor) — mitigated; the anchor is derived from the
  heading as written and asserted in both README and `demo_v2.ipynb`.
- **T-15-SC** — zero packages installed. Standard library only (`json`, `re`, `pathlib`).

## Self-Check: PASSED

- `tests/test_phase15_docs.py` — FOUND (544 lines, 4 tests, `4 passed`)
- `docs/REPORT.md` / `README.md` / `results/phase13_ab_report.md` — FOUND and byte-restored after
  every RED proof (`git status --short` clean)
- `results/phase15_norms.json`, `results/phase15_adapter_delta.png`,
  `results/phase15_fisher_ewc.png`, `demo_v2.ipynb` — all FOUND and tracked by git
- Commit `e8f4beb` — FOUND in `git log`
- Commit `1ce2142` — FOUND in `git log`
