---
phase: 15-figures-writeup
plan: "06"
subsystem: narrative / README.md v2.0 front door (DOC-02)
tags: [DOC-02, D-16, D-04, D-03, R1, VIZ-02, VIZ-03]
requires:
  - "results/phase15_adapter_delta.png + results/phase15_fisher_ewc.png (15-03 @ committed) — the two embedded figures"
  - "results/phase13_ab_report.md (Phase 13 + the 15-04 addendum) — retention numbers and the correlation verdict"
  - "results/phase14_recall_report.md — the recall rates, thresholds and closed-book control"
  - "results/inflation_report.md — the Phase 11 tokenizer-inflation tax and its same-run baseline"
  - "docs/REPORT.md § `## Milestone 2 Limitations — Nine Honest Negatives, Quoted` (15-05) — the full-form target of README's two Limitations links"
provides:
  - "README.md v2.0 — Milestone 2 framed as delivered, three headline numbers each qualified inline, both signature figures on the front page"
  - "the corrected tokenizer-corpus attribution stated directly (closes the obligation docs/REPORT.md's L8 note records on README's behalf)"
  - "the three (label, number_string, source_path) triples Plan 15-08's test_headline_numbers_match_sources consumes"
affects:
  - "Plan 15-08 — test_headline_numbers_match_sources reads the triples recorded below, the qualifier keyphrases, and the derived Limitations anchor"
tech-stack:
  added: []
  patterns:
    - "headline number and its qualifier in one bullet; the docs/REPORT.md link is additive, never the caveat itself"
    - "one-line italic figure captions carrying only the comparability statement (D-04 terse form)"
key-files:
  created: []
  modified:
    - "README.md (111 -> 187 lines; two commits, zero deletions of a still-true v1.0 claim)"
decisions:
  - "The three M2 headline numbers lead `## Results at a glance`, above the v1.0 foundation numbers — they carry the thesis; the M1 numbers are preserved verbatim below them rather than displaced"
  - "The Fisher/Δ correlation is stated on the front page (rho = 0.801544 with its CI) because the VIZ-03 figure otherwise implies an unmeasured claim — written as a rank correlation, not an effect size, and naming the 2 of 36 cells that moved further under EWC"
  - "`(~70 s)` was dropped from the `make test` block rather than re-asserted: the suite now measures 115 s, and a stale timing is the same class of error as a stale milestone framing"
metrics:
  duration: 17min
  tasks: 2
  files: 1
  completed: 2026-08-02
---

# Phase 15 Plan 06: README v2.0 Front Door Summary

Rewrote `README.md` as the v2.0 front door: Milestone 2 reads as shipped rather than upcoming,
both signature figures sit where a reader meets the thesis, and the three headline numbers each
carry their qualifier inside the same bullet at 547-live-ids density.

## What Was Built

| Task | Commit | What landed |
|------|--------|-------------|
| 1 | `b2dc9a8` | Framing rewrite — thesis-demonstrated opening, both v2.0 figures with terse captions, LoRA/EWC/two-demo bullets, `## Roadmap — Milestone 2 (upcoming)` replaced by `## Milestone 2 — what shipped` + honest next steps |
| 2 | `ff5ca2a` | The three headline numbers with inline qualifiers, the corrected tokenizer-corpus attribution, and the correlation stated as a rank correlation |

## RECORD VERBATIM — the three headline triples for Plan 15-08

`test_headline_numbers_match_sources` defines `(label, number_string, source_path)`. Every string
below was confirmed present in **both** `README.md` and its source file by a script run at Task 2
verification, not by eye.

| Label | Number string | Source path | Source line |
|-------|---------------|-------------|-------------|
| recall (held-out) | `0.3483` | `results/phase14_recall_report.md` | 59 (result table), 578 (verdict) |
| retention (naive arm) | `8.52417066884246` | `results/phase13_ab_report.md` | 56 (2×2 table), 114/119 (gate arithmetic) |
| inflation (dialogue) | `3.229` | `results/inflation_report.md` | 15 (D-08 metric 1), 31 (ratio) |

Every other value in those three bullets was cross-checked against the same sources in the same
run and is present verbatim:

- `results/phase14_recall_report.md` — `0.4921`, `0.2486`, `0.2000`, `326/936`, `496/1008`, `0/2430`
- `results/phase13_ab_report.md` — `3.8911400839446597`, `2.107553076833866`, `+6.416618`,
  `+1.783587`, `33.61`, `0.380556`, `0.801544`, `0.597984`, `0.920291`
- `results/inflation_report.md` — `2.860`, `1.129`, `4,800,385`, `1,486,754`, `0.9996`

> **One spelling trap for 15-08:** the inflation ratio is `1.129x` (ASCII `x`) in
> `results/inflation_report.md:31` and `1.129×` (U+00D7) in README. Pin **`1.129`** without the
> unit character, or the source-side assertion fails on a character README is right to render
> typographically.

## RECORD VERBATIM — the qualifier keyphrases now in each bullet

`test_headline_numbers_match_sources` asserts the qualifier shares the bullet with the number.
These are the literals present, verified by splitting README on `\n(?=- )` and asserting exactly
one bullet contains each number:

| Number | Keyphrases in the SAME bullet |
|--------|-------------------------------|
| `0.3483` | `proper-noun core` · `reversed phrasings` (both present) |
| `8.52417066884246` | `teacher-forced` · `noise floor` (both present) |
| `3.229` | `same-run baseline` |

`'see Limitations' in README` → **False**. No headline number's only caveat is a pointer; both
`docs/REPORT.md` links are appended **after** an already-complete inline qualifier.

## RECORD VERBATIM — the Limitations anchor as written

```
docs/REPORT.md#milestone-2-limitations--nine-honest-negatives-quoted
```

Derived programmatically from the heading **as actually written in `docs/REPORT.md`** (lowercase,
spaces → hyphens, drop characters that are neither alphanumeric nor hyphen), not retyped — the em
dash collapses to the empty string, leaving the double hyphen in `limitations--nine`. It appears
twice in README (the recall bullet and the retention bullet) plus once in the closing next-steps
list. Verified to resolve against the finished `docs/REPORT.md`, which Plan 15-05 had already
committed by the time this plan ran.

## The R1 obligation — discharged

`docs/REPORT.md`'s L8 correction note states on the record that *"README.md carried the same
misattribution and … its v2.0 rewrite states the corrected attribution directly rather than by
note."* That is now true. The tokenizer bullet reads:

> the frozen production tokenizer `artifacts/tokenizer.json`, 5,648 bytes, was trained on the
> 11,469-byte fixture `tests/fixtures/tiny_corpus.txt` — `scripts/train_tokenizer.py:31` — and
> not on the full TinyStories corpus, which is why only 283 of the 7,928 requested merges were
> learned and the remaining 7,645 rows are reserved capacity

Both byte counts were re-confirmed with `wc -c` **before** being written (11469 / 5648), per the
plan's independent-confirmation requirement. `'bounded TinyStories corpus' in README` → **False**.
The 283-merge / 547-live-id / 7,645-dead-row arithmetic and the tiktoken-oracle clause are
unchanged — only the corpus identity was under-disclosed, and only that changed.

## The prior-wave warnings — how each was honored

| Warning | Where it landed |
|---------|-----------------|
| ρ = 0.80 is a rank correlation, not an effect size | README writes *"a **rank** correlation, not an effect size"* in the same sentence as the coefficient; no fraction-of-movement claim appears anywhere |
| Do not write that EWC reduced movement everywhere | Same sentence: *"EWC in fact moved **further** than naive in 2 of the 36 cells"* |
| naive+ewc share a scale, Fisher does not, adapter is not comparable | Two one-line captions: the VIZ-03 caption states the shared scale and the units reason for Fisher's own scale; the VIZ-02 caption states independence and names the confounds (parameter counts, training budgets) |
| Every headline number carries its qualifier in the same breath | Verified structurally, bullet-by-bullet — see the keyphrase table above |

## Verification Results

| Check | Result |
|-------|--------|
| Task 1 automated verify (6 conjuncts) | six × `True` |
| `grep -n -i upcoming README.md` | no hits at all (exit 1) |
| `2.1066` still shares its bullet with `12,636,922` and `scripts/evaluate.py` | preserved byte-identical from v1.0 |
| Both figure paths resolve on disk | `results/phase15_adapter_delta.png` (65,304 B), `results/phase15_fisher_ewc.png` (107,413 B) |
| Task 2 automated verify (12 literals + wrong-attribution absence) | `True True`, `missing: []` |
| One bullet per headline number, qualifier keyphrases in that bullet | 3/3, exactly one matching bullet each |
| `'see Limitations' in README` | `False` |
| Every README number present in its cited source | 3/3 source files `OK`, zero missing |
| Limitations anchor derived from `docs/REPORT.md` resolves in README | `True` |
| `.venv/bin/pytest -q` | **403 passed, 1 skipped** — exactly the entry baseline |
| Lint, pinned `.venv/bin/ruff` | `All checks passed!` / `138 files already formatted` |
| Post-commit deletion check (`git diff --diff-filter=D`) | none, both commits |

## Deviations from Plan

### 1. [Rule 1 — Bug] The test-count claim was stale by ~270 tests

- **Found during:** Task 1
- **Issue:** the v1.0 pytest bullet claimed *"(~130 CPU-only tests)"*. The suite is now
  403 passed / 1 skipped. The plan says to preserve v1.0 claims *that are still true*; this one
  is not.
- **Fix:** `~400 CPU-only tests`, and the bullet gained the adapter and Fisher invariants it now
  actually covers.
- **Files modified:** `README.md`
- **Commit:** `b2dc9a8`

### 2. [Rule 1 — Bug] The `make test` block asserted a wall-clock time that no longer holds

- **Found during:** Task 1
- **Issue:** `make test    # full CPU-only suite (~70 s)`. Measured this run: **115.18 s**.
- **Fix:** the timing was **deleted rather than updated** — a per-machine wall clock is not a
  claim README can keep true, and the same-standard reasoning is Plan 15-05's Deviation 4 (do not
  assert a number the document cannot check). The comment now reads
  `# full CPU-only suite — no GPU required`.
- **Files modified:** `README.md`
- **Commit:** `b2dc9a8`

### 3. [Rule 2] The front page states the Fisher/Δ correlation, which the plan left optional

- **Found during:** Task 2
- **Issue:** the plan's read-list mentions the correlation *"in case the front page mentions
  it"*. Embedding VIZ-03 without it leaves the figure implying the "EWC dodges high-Fisher
  coordinates" claim **visually and unmeasured** — precisely the declared-vs-measured gap D-09
  exists to close. Silence here would have been the less honest option, not the safer one.
- **Fix:** one sentence under the caption carrying the coefficient, its 95% CI, the
  pre-registered-before-the-number provenance, the rank-not-effect-size qualifier, and the 2-of-36
  counter-cells — the same inline-qualifier discipline as the three headline bullets.
- **Files modified:** `README.md`
- **Commit:** `ff5ca2a`

### 4. `make lint` still resolves the stale global ruff (DEF-15-01, unchanged, out of scope)

Fifth consecutive plan. `Makefile:16` calls bare `ruff` → pyenv shim → 0.1.15. **This plan
modified zero Python files.** The pinned `.venv/bin/ruff` is clean across all 138 files. No new
entry; DEF-15-01 already carries the one-line fix.

## Known Stubs

None. Every number on the front page is read from a committed report and machine-verified against
it; both figures exist on disk; both `docs/REPORT.md` links resolve to a heading that exists.

## Threat Flags

None. This plan wrote markdown only — no endpoint, no auth path, no file-access pattern, no
schema. Its own `<threat_model>` is covered: **T-15-18** (a number without its qualifier) by the
per-bullet keyphrase assertion plus `'see Limitations'` absence; **T-15-19** (a number drifting
from its source) by the three-source cross-check, zero missing; **T-15-16** (repeating the wrong
tokenizer attribution) by `wc -c` re-confirmation before writing and the `bounded TinyStories
corpus` absence check. **T-15-SC:** zero packages installed.

## What Plan 15-08 Must Carry

- Pin `1.129` **without** the `×`/`x` unit character (README and the source render it
  differently); the three primary triples are in the table above.
- The qualifier keyphrases actually present are `proper-noun core` / `reversed phrasings`,
  `teacher-forced` / `noise floor`, and `same-run baseline` — asserting any other spelling will
  go red against a correct README.
- Split README into bullets on `\n(?=- )`, not on lines: every headline bullet is multi-line, as
  the 547-live-ids density target itself always was.
- The Limitations anchor README uses is
  `#milestone-2-limitations--nine-honest-negatives-quoted` — **two** hyphens where the em dash
  was.

## Self-Check: PASSED

- `README.md` — FOUND (187 lines)
- `results/phase15_adapter_delta.png` — FOUND
- `results/phase15_fisher_ewc.png` — FOUND
- `docs/REPORT.md` § `## Milestone 2 Limitations — Nine Honest Negatives, Quoted` — FOUND, anchor resolves
- Commit `b2dc9a8` — FOUND in `git log`
- Commit `ff5ca2a` — FOUND in `git log`
