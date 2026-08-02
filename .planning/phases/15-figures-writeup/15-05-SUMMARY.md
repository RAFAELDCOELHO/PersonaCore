---
phase: 15-figures-writeup
plan: "05"
subsystem: narrative / docs/REPORT.md v2.0 extension (DOC-02)
tags: [DOC-02, D-13, D-14, D-15, D-01, D-02, D-03, D-04, D-17, D-18, R1, R2, R3, SC3]
requires:
  - "docs/REPORT.md @ 39a59a7 — the v1.0 report; its first 421 lines are immutable (D-13)"
  - "results/phase15_norms.json (15-02 @ f68450a) — vmax_driver, nonpositive_cells, comparison_basis, blocks.fisher.variant"
  - "results/phase13_ab_report.md (Phase 13 + the 15-04 addendum @ 0e8b890) — the A/B numbers and the correlation verdict"
  - "results/phase14_recall_report.md / phase14_calibration_report.md / finetune_smoke_report.md / inflation_report.md — the nine quote sources"
provides:
  - "docs/REPORT.md — dated M1/M2 boundary marker, 7 new `## Decision:` sections, the results narrative, the nine-limitation section"
  - "the exact heading strings and the nine normalized quote strings Plan 15-08's tests assert against"
  - "the L8 tokenizer-corpus correction (closes the tracked tech-debt item routed to this phase)"
affects:
  - "Plan 15-08 — test_limitations_quotes_are_verbatim, test_report_names_the_artifact_vmax_driver (section-anchored on `### The Two Signature Figures`), and the SC3 Fisher-variant assertion"
  - "Plan 15-07 (README/ROADMAP) — README's v2.0 rewrite must state the corrected tokenizer-corpus attribution directly; REPORT.md's L8 note says it does"
  - "Plan 15-06 (notebook) — cites the pinned headings, not this SUMMARY"
tech-stack:
  added: []
  patterns:
    - "insert-a-dated-boundary-marker instead of editing stale text — 206/169/174 insertions, 0 deletions across three commits"
    - "verbatim quote comparison under whitespace+blockquote-marker-only normalization, with `…`-delimited fragments matched in order via an advancing find index"
    - "L8 verified against `git show HEAD:docs/REPORT.md` rather than the working file, so quoting a file into itself cannot self-satisfy the check"
    - "stable quote labels (L1..L9) rendered out of numeric order, with an explicit in-document note saying why"
key-files:
  created: []
  modified:
    - "docs/REPORT.md (456 -> 1005 lines; +549 insertions, 0 deletions)"
decisions:
  - "The v2.0 block opens with `## Milestone 2 Begins Here — Weight-Based Memory` (a `## ` heading, not `# `) so `## Where to Go Next` stays a bounded, byte-identical section — a level-1 heading would have swallowed it into the appended block under any `^## `-anchored section reader"
  - "Two extra `### ` headings (`### The Fisher/Δ Correlation, Cited Terse`, `### What Remains Uncertain`) close `### The Two Signature Figures`, which would otherwise have run to EOF and made Plan 15-08's section-anchored read trivially satisfied"
  - "The stable L1..L9 labels are kept over renumbering to sequential order; renumbering would have silently redefined L3/L8/L9 for every downstream reference"
metrics:
  duration: 41min
  tasks: 3
  files: 1
  completed: 2026-08-02
---

# Phase 15 Plan 05: docs/REPORT.md v2.0 Extension Summary

Extended the v1.0 report into a single front-to-back v2.0 document — a dated Milestone 1 boundary
marker, seven new `## Decision:` sections, a results narrative, and nine honest negatives each
reproduced in its source's exact wording — without editing one byte of the v1.0 text.

## What Was Built

| Task | Commit | What landed |
|------|--------|-------------|
| 1 | `37b8c97` | Boundary marker before the stale future-tense roadmap + 7 v2.0 `## Decision:` sections (+206/−0) |
| 2 | `7cf5f74` | The results narrative, `### The Two Signature Figures`, the terse correlation citation (+169/−0) |
| 3 | `b8db4ae` | `## Milestone 2 Limitations — Nine Honest Negatives, Quoted` (+174/−0) |

`git diff --numstat` across all three: **549 insertions, 0 deletions.**

## RECORD VERBATIM — the three PINNED headings (Plans 15-06/15-07/15-08 cite the PLAN, not this file)

These are pinned in `15-05-PLAN.md` `<pinned_headings>`; reproduced here as written into the file,
byte-identical to the pinned spelling:

1. `## Milestone 2 Results: What Three Experiments Showed`
2. `### The Two Signature Figures`
3. `## Milestone 2 Limitations — Nine Honest Negatives, Quoted`

## RECORD VERBATIM — every OTHER new heading

```
## Milestone 1 Ends Here — Everything Below This Line Is As Written on 2026-06-10
## Milestone 2 Begins Here — Weight-Based Memory
## Decision: Two Mechanisms in Two Stages, Not One Combined Run
## Decision: The Tokenizer Stays Frozen for v2.0, and the Inflation Tax Is Measured Rather Than Assumed
## Decision: Pre-Registration Lives in Committed Code, Before Any Number Exists
## Decision: Gate Only the Part of a Claim the Sample Size Supports
## Decision: Honest Negatives Stand Unamended; Discretionary Continuations Are Logged Separately and Dated After
## Decision: Structural Enforcement Replaces Declared Invariants
## Decision: Extract Once, Then Plot From the Committed Artifact Only
### The Fisher/Δ Correlation, Cited Terse
### What Remains Uncertain
### Bounding "EWC mitigates forgetting"
### Bounding "memory lives in the weights"
### Bounding "…without damaging the base"
### Bounding "13.9M-parameter from-scratch base"
```

Decision-section count: **14 pre-existing + 7 new = 21**.

## RECORD VERBATIM — the Fisher variant string as written (ROADMAP SC3)

```
empirical_diag_fisher/groundtruth_targets/mean_normalized
```

Copied from `results/phase15_norms.json` → `blocks.fisher.variant`, never retyped from memory. It
sits **inside** `### The Two Signature Figures`, together with `n_examples` = 2000 and seed 1234.

## RECORD VERBATIM — the nine quote strings as written (for Plan 15-08)

Each string below is `normalize_quote(<the blockquote as rendered>)` — i.e. `> ` markers stripped
and whitespace runs collapsed, exactly the form Plan 15-08's `test_limitations_quotes_are_verbatim`
compares against `normalize_quote(<source file text>)`. Rendered order is L1, L7, L4, L2, L6, L5,
L3, L9, L8.

| Label | Source | Fragments |
|-------|--------|-----------|
| L1 | `results/finetune_smoke_report.md:159` | 1 |
| L7 | `results/phase13_ab_report.md:209-214` + `220-223` | 2 (`…`) |
| L4 | `results/phase14_recall_report.md:378` | 1 |
| L2 | `results/phase14_recall_report.md:566-571` | 1 |
| L6 | `results/phase14_recall_report.md:555-558` | 1 |
| L5 | `results/phase14_recall_report.md:562-564` | 1 |
| L3 | `results/phase14_calibration_report.md:322` | 1 + trailing `…` |
| L9 | `results/phase14_recall_report.md:585` | 1 + trailing `…` |
| L8 | `docs/REPORT.md:61-67` + `373-375` | 2 (`…`) |

```
L1	**EWC not demonstrable at this budget** (no λ satisfies both the within-margin rule and the retention demonstrability guard) — surfaced, never massaged (pre-registered §8 all-fail outcome: λ\* = None, demonstrable = False).
L7	**Named limitation (D-05 obligation 2):** that floor was **NOT re-verified at the 4000-step production budget**, and **NOT re-verified inside collapse dynamics** — it was measured in a stable regime, on the masked arm, at a shorter budget, while both Phase-13 arms are unmasked and one of them drifts by +6.42 PPL. **Seed-to-seed variance could plausibly scale with drift magnitude**, and a floor measured in a stable regime would not capture that. Nothing here rules that out. … That is corroboration from a free check, not a re-measurement — the honest re-measurement (a 1337/2024 seed pair at 4000 unmasked steps, ~75 min) was not run.
L4	**Measured.** With each fact's own first-person statement in the `<|system|>` persona span, the base (adapter off) scored **1/1944 = 0.0005** across 216 questions; 1 of those questions produced at least one completion containing the value. This is the ONLY place in the entire phase where a fact value legitimately appears in a prompt.
L2	See `## Control 1 — Question Fairness (D-11.1)`, part (a). In-context answerability could not be established at this scale, so a closed-book failure **in isolation** is not unambiguous evidence of absent memory. The adapter-on / adapter-off differential is unaffected (part (b)), but any reading of a single failed question as "the model does not know this" is out of scope.
L6	**Consequence for what a clean held-out result may claim:** it demonstrates generalization **within that scope** — across held-out template families in the taught direction — and **not** immunity to every documented fine-tuning limitation. This report makes no claim about reversed recall, because this phase did not measure it as a held-out property.
L5	See `## Soft Tier — Excluded From The Gate (D-05)`. Two of the taught facts contribute nothing to either threshold, so the headline number describes the proper-noun core only — a narrower set than "everything the adapter was taught."
L3	**What the paired arm shows replay actually BUYS, and what it costs.** Replay at ratio 1.0 moves the collapse from +224.81% to +29.39% — a large mitigation — while taught recall falls from 0.6825 to 0.4143, a fall of 0.2683. **The replay arm ITSELF still trips the trigger.** Replay at this ratio reduces the collateral collapse but does not eliminate it, so 'replay required' should not be read as 'replay solves it'. …
L9	(1) No-collateral-collapse (D-11 control 2): the taught persona measurably raises off-topic dialogue cost (+27.16%) relative to the pre-adapter conversational base, but does not eliminate the collapse signature entirely. The adapter reduces, rather than removes, deviation from general conversational behavior on unrelated prompts. …
L8	**What actually trained.** Training learned 283 of the 7,928 requested merges before the bounded TinyStories corpus exhausted its mergeable pairs — the trainer itself warns "corpus exhausted: learned 283 of 7928 requested merges; vocab_size=8192 has 7645 dead ids". The *effective* vocabulary is therefore 547 live ids (256 bytes + 283 learned merges + 8 specials); the locked 8192-row table is reserved capacity. The trade-off is stated plainly: shape stability for every downstream checkpoint, in exchange for 7645 dead rows the model carries in its embedding table. … Of the headline count, 2,935,680 parameters (7645 dead rows × 384 dims, ~21%) are embedding rows for ids that can never occur in the training data or be decoded — counted in the headline because they are part of the shipped tensor.
```

**Two things Plan 15-08 must not get wrong about these strings.**

1. **`grep -qF` is unrunnable for L7, L2, L5, L6 and L8** — those five span multiple source lines,
   so a line-oriented check reports a false failure. Use the pinned `normalize_quote` on **both**
   sides. Confirmed empirically: `grep -F 'the bounded TinyStories corpus' docs/REPORT.md` matches
   nothing in the *source* passage, because the phrase spans `docs/REPORT.md:61-62`.
2. **L8's source is `docs/REPORT.md` itself.** Comparing the quote against the *working* file is
   self-satisfying and proves nothing. The hand-check here compared it against
   `git show HEAD:docs/REPORT.md` (the pre-Task-3 blob); 15-08 should do the same, or anchor
   outside the Limitations section.

## The three things Plan 15-04 warned about — how each was honored

| Warning | Where it landed |
|---------|-----------------|
| ρ = 0.80 is a rank correlation, not an effect size | *"ρ = 0.80 is a rank correlation, not an effect size, and does not license a statement about what fraction of high-Fisher movement EWC avoids."* |
| Do not say EWC reduced movement everywhere | Its own paragraph: **34 of 36**, with layer 0/`q_proj` (−0.015185) and layer 1/`q_proj` (−0.006607) naming the two cells that moved further, and *"none of the 36 signed values was filtered out."* |
| Do not import the "suggestive but not statistically demonstrated at n = 36" register | `grep -c 'suggestive'` in `docs/REPORT.md` = **0**. The gate passed; the miss register was not used. |

The pre-registered percentile-bootstrap small-n bias note travels **with** the CI, in the same
sentence block, explicitly flagged as written before the coefficient existed.

## Verification Results

| Check | Result |
|-------|--------|
| Task 1 automated verify (marker precedes stale roadmap; ≥21 Decision sections) | `True True` (21) |
| First 421 lines vs `git show HEAD:docs/REPORT.md` (all three tasks) | `cmp` clean each time |
| `## Limitations and the Milestone 2 Roadmap` section vs HEAD | byte-identical |
| `## Where to Go Next` section vs HEAD | identical modulo one trailing blank separator line (see Deviation 1) |
| `git diff --numstat docs/REPORT.md` per task | `206 0` / `169 0` / `174 0` — **zero deletions throughout** |
| Boundary marker carries `2026-06-10` and `m1-demo-v1` | `True True` |
| Every NEW heading matches `^## Decision: [A-Z]` | 7/7 (the one pre-existing violator, `## Decision: fp32 …`, is v1.0 text and untouched) |
| Task 2 automated verify (13 literals + adapter vmax projection + Fisher variant + recall verdict) | `True True True True` |
| vmax drivers / `nonpositive_cells` / Fisher variant **inside** `### The Two Signature Figures` | all present, section-anchored (5705 chars) |
| `331,776` and `13,891,584` present; *"parameter budget, not a quality comparison"* present | `True True` |
| `units` argument present inside the figures subsection | `True` |
| No second copy of the pre-registration row set (`N_PERM` / `N_BOOT` / resample counts) | none found |
| Task 3 automated verify (6 conjuncts, section-anchored, normalized both sides) | six × `True` |
| **All nine quotes verbatim under `normalize_quote`**, fragments in order | **9/9 OK** |
| `grep -qiE 'nine (honest )?negatives'` | PASS |
| L3 carries `+224.81%`, `+224.5330%` and the `289-307` WR-01 line range | PASS |
| L8 correction names `scripts/train_tokenizer.py:31`, `tiny_corpus.txt`, `11,469` | PASS |
| `11,469` and `5,648` byte counts re-confirmed against the files | `wc -c` — 11469 / 5648 |
| `.venv/bin/pytest -q` | **403 passed, 1 skipped** — exactly the entry baseline |
| Lint, pinned `.venv/bin/ruff` | `All checks passed!` / `138 files already formatted` |
| Post-commit deletion check (`git diff --diff-filter=D`) | none, all three commits |

## Deviations from Plan

### 1. [Rule 3] The v2.0 block opens with a `## ` heading, not a `# ` one

- **Found during:** Task 1 (running the acceptance check)
- **Issue:** The appended block originally opened with `# PersonaCore — Milestone 2: Weight-Based
  Memory`. A level-1 heading does not terminate a `^## `-anchored section read, so
  `## Where to Go Next` silently absorbed the entire v2.0 extension and failed its byte-identity
  check — the same class of anchoring bug Plan 15-04's CR-02 note warns about.
- **Fix:** changed to `## Milestone 2 Begins Here — Weight-Based Memory` and dropped the `---`
  rule that preceded it. `## Where to Go Next` is now bounded and identical to HEAD apart from the
  blank separator line any appended heading requires.
- **Files modified:** `docs/REPORT.md`
- **Commit:** `37b8c97`

### 2. [Rule 3] Two extra `### ` headings close the figures subsection

- **Found during:** Task 2
- **Issue:** `### The Two Signature Figures` was the last `###` in the file, so it ran to EOF and
  swallowed the correlation citation and the closing paragraph. Plan 15-08's
  `test_report_names_the_artifact_vmax_driver` reads that block anchored `^### ` → next
  `^#{2,3} `; with the section unbounded, the test would have passed on a whole-file read while
  proving nothing — exactly the failure the section-anchoring requirement exists to prevent.
- **Fix:** added `### The Fisher/Δ Correlation, Cited Terse` and `### What Remains Uncertain`.
  Both are narrative-level siblings that the plan's own action bullets already describe as
  separate items; only their heading level is new. The figures section is now 5,705 characters and
  properly terminated.
- **Files modified:** `docs/REPORT.md`
- **Commit:** `7cf5f74`

### 3. [Rule 1 — Bug] The D-03 third confound was first written with the wrong polarity

- **Found during:** Task 2 self-review
- **Issue:** The confound was drafted as *"does NOT imply more conservative or **more** effective
  learning"*. The artifact and the plan both say **less** effective. Inverting it turns a
  "do not read this as a quality verdict either way" caveat into something closer to a claim.
- **Fix:** corrected to match `results/phase15_norms.json`'s `comparison_basis.note` wording
  before the task was committed.
- **Files modified:** `docs/REPORT.md`
- **Commit:** `7cf5f74`

### 4. The `~914 MB` checkpoint figure is attributed rather than asserted

- **Found during:** Task 1
- **Issue:** The plan's Decision-section bullet states the figures are regenerable "without the
  914 MB of gitignored checkpoints". Measured directly, the six checkpoints
  `scripts/extract_deltas.py` reads total **946,648,137 bytes** (902.8 MiB / 946.6 MB) — neither
  reading is 914 MB. The five checkpoints in D-08's list sum to 637.6 MiB.
- **Fix:** the report writes *"`scripts/extract_deltas.py` records them at ~914 MB"* — which is a
  verifiable statement about what the committed script says (`extract_deltas.py:10,33,274`) rather
  than an unverified claim about disk. Same standard as R1's correction note: do not assert a
  number this plan cannot check. Logged as `DEF-15-02` in the phase's `deferred-items.md`; the
  one-line fix belongs in the extraction script, not in the report.
- **Files modified:** `docs/REPORT.md` (wording only)
- **Commit:** `37b8c97`

### 5. `make lint` still resolves the stale global ruff (DEF-15-01, unchanged, out of scope)

Fourth consecutive plan. `Makefile:16` calls bare `ruff` → pyenv shim → 0.1.15. **This plan
modified zero Python files.** The pinned `.venv/bin/ruff` is clean across all 138 files. No new
entry; DEF-15-01 already carries the one-line fix.

## Known Stubs

None. Every heading this plan created carries its full content, every number in the narrative is
read from a committed artifact or a committed report, and all nine limitation quotes are present
and machine-verified against their sources.

## Threat Flags

None. This plan wrote markdown only — no endpoint, no auth path, no file-access pattern, no schema.
Its own `<threat_model>` is covered: **T-15-15** (a v1.0 section silently edited) is verified by
`cmp` on the first 421 lines after every task plus `0` deletions in all three `--numstat` reads;
**T-15-05 / T-15-26** (a limitation softened, or the verbatim rule weakened under pressure) by the
nine-quote check run through the plan's pinned `normalize_quote` with no substitution added —
whitespace and `> ` markers only, ellipsis fragments matched in order; **T-15-16** (the L8
correction asserted without evidence) by re-confirming 11,469 and 5,648 bytes with `wc -c` before
writing them; **T-15-17** (+224.81% quoted without WR-01) by an entry that carries the figure, the
correction block's line range, and the `+224.5330%` re-measurement. **T-15-SC:** zero packages
installed.

## What Plans 15-06 / 15-07 / 15-08 Must Carry

- **15-07 (README):** REPORT.md's L8 correction note states, on the record, that **README carried
  the same misattribution and its v2.0 rewrite states the corrected attribution directly.**
  `README.md:29-33` still reads *"the bounded TinyStories corpus exhausts its mergeable pairs"*.
  That sentence must change, or REPORT.md now contains a false statement about a sibling file.
- **15-07 (ROADMAP):** SC2 stands unnarrowed; SC3's named Fisher variant is in the report verbatim.
- **15-08:** use the pinned `normalize_quote` for the nine quotes and **never `grep -qF`**; anchor
  the figures test on `### The Two Signature Figures` (now properly bounded by
  `### The Fisher/Δ Correlation, Cited Terse`); compare L8 against a source that is not the
  working `docs/REPORT.md`.
- **All three:** the labels `L1`–`L9` are stable identifiers, not list positions. The rendered
  order is claim-bound: L1, L7 / L4, L2, L6, L5 / L3, L9 / L8.

## Self-Check: PASSED

- `docs/REPORT.md` — FOUND (1005 lines; first 421 byte-identical to `39a59a7`)
- `## Milestone 2 Results: What Three Experiments Showed` — FOUND, spelled as pinned
- `### The Two Signature Figures` — FOUND, spelled as pinned
- `## Milestone 2 Limitations — Nine Honest Negatives, Quoted` — FOUND, spelled as pinned
- Commit `37b8c97` — FOUND in `git log`
- Commit `7cf5f74` — FOUND in `git log`
- Commit `b8db4ae` — FOUND in `git log`
