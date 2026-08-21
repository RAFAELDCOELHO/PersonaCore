---
phase: 20-pre-registration-the-three-condition-gate
plan: 16
subsystem: gate-correction
tags: [pre-registration, gate-02, gate-06, gap-closure-wave-2, watched-red, d-24, d-38, d-40, d-41]
requires:
  - "20-14 (the Y-leg value guards and the count-by-type guard this plan publishes)"
  - "20-15 (the magnitude bound, the D-41 harness rewire and the aliased-import census)"
  - "20-VERIFICATION.md:69 / :115 — the one-ULP measurement that falsified REQUIREMENTS.md:303"
provides:
  - "A top-level `value_guards` block and five new `defects` keys (GC-01, GC-02, GC-03, GC-04, GC-06) in results/phase20_gate_coverage_correction.json, every number computed by calling the modules"
  - "test_correction_payload_is_additive_across_the_second_correction — the pre-write revision derived from git log (the newest blob with no `value_guards` key), asserting every published value EQUAL"
  - "A SECOND dated continuation appended to results/phase20_gate_coverage_correction.md by scripts/_addendum.py::append_addendum in the idempotent-pointer form, 152 additions / 0 deletions"
  - "Two ordering assertions on the second heading inside the pre-existing addendum-additivity guard, watched RED with the failure confirmed to name the ORDERING assertion"
  - "REQUIREMENTS.md GATE-02 with its falsified 'by the number' claim corrected in place and its stale refusal count re-measured; GATE-06 with a dated D-40 amendment"
  - "Three watched-RED breaks with byte-identical restores, for 20-SECURITY.md's Watched-RED table"
affects:
  - "20-17 — T-20-79 and T-20-80 are discharged here against WATCHED guards; the re-close to threats_open: 0 may point at this evidence rather than at this plan"
  - "GC-05, GC-07, GC-08..GC-12 remain OPEN and are named as open in both halves of the artifact"
tech-stack:
  added: []
  patterns:
    - "An input a module was HANDED is not derivable from that module; publish it, source it from a constant where one exists, and declare the exemption instead of leaking it"
    - "Hoist an existing literal to module scope rather than declaring a second copy beside it — the payload and the case that demonstrates it then cannot drift"
    - "A guard whose claim is line-level when the artifact only supports value-level should say so in its own docstring rather than assert something weaker silently"
    - "Break a guard on a leaf NO other guard reads, to prove it is independently load-bearing rather than merely co-firing"
key-files:
  created:
    - ".planning/phases/20-pre-registration-the-three-condition-gate/20-16-SUMMARY.md"
  modified:
    - "results/phase20_gate_coverage_correction.json"
    - "results/phase20_gate_coverage_correction.md"
    - "tests/test_phase20_correction.py"
    - ".planning/REQUIREMENTS.md"
decisions:
  - "The second correction's measurements go in a NEW top-level `value_guards` key, not into `evidence`: `evidence` is the CR-01/WR-09 reproduction record with a fixed shape the re-derivation guard iterates key by key, and a differently-shaped record inside it would break that iteration contract"
  - "Nothing moved out of `recorded_not_corrected` — GC-01..GC-12 postdate this artifact, so none was ever recorded there as accepted — and the artifact says so in `value_guards.nothing_moved_out_of_recorded_not_corrected`"
  - "The plan's `0 deletions` acceptance criterion is STRUCTURALLY UNSATISFIABLE for this write and the guard says so rather than asserting it: `value_guards` sorts after every published key, so the previous last key necessarily gains a trailing comma. Semantic additivity is asserted on the PARSED payload instead"
  - "The falsified GATE-02 clause is corrected IN PLACE, not amended beside: D-36's additive register exists so a superseded NUMBER stays visible, not so a falsified CLAIM stays standing"
  - "A third break (1b) was added on a leaf no re-derivation reads, because BREAK 1 on `evidence` co-fired two guards and could not distinguish 'the additivity guard bites' from 'the re-derivation guard bites'"
metrics:
  duration: "~50 min"
  tasks_completed: 4
  commits: 3
  completed: 2026-08-21
---

# Phase 20 Plan 16: The Second Correction, Its Additivity Guard, and the Claim That Was Measured False Summary

Published the five newly-closed defects and their measured value-guard evidence into the correction's
JSON additively — with a guard that derives the pre-write revision from history and asserts every
published value unchanged — appended a second dated continuation through `append_addendum` in its own
commit, and corrected the one sentence in `REQUIREMENTS.md` that the verification measured FALSE,
watching all three artifact guards fail before trusting any of them.

## What Was Built

**Task 1 — JSON + guard** (`001138d`, +151/-1 on the JSON, +141 on the test file). One commit,
two files, because the guard and the write it guards cannot be split without leaving the suite red
in between.

- `results/phase20_gate_coverage_correction.json`: five new `defects` keys (`GC-01`, `GC-02`,
  `GC-03`, `GC-04`, `GC-06`) in the shape the existing four use, and one new top-level
  `value_guards` object carrying `y_leg_differential`, `count_type_guard`,
  `retention_magnitude_bound`, `census`, `second_continuation` and
  `nothing_moved_out_of_recorded_not_corrected`. Generated by a throwaway script that imports the
  three modules and calls them; the script lives in the session scratchpad and is **not committed**
  (`git status --porcelain` shows no new `scripts/*.py`).
- `tests/test_phase20_correction.py`: the new
  `test_correction_payload_is_additive_across_the_second_correction`, plus every number in
  `value_guards` re-derived inside `test_every_published_number_re_derives_from_the_modules`.

**Task 2 — the second continuation** (`69be030`, **+152 / -0** on the `.md`). Written by
`scripts/_addendum.py::append_addendum(path, addendum, pending=RECORDED, recorded=RECORDED)` — the
idempotent-pointer form — in a commit **separate from the JSON**, so a pre-append revision exists in
history. `ADDENDUM_HEADING_SECOND` was extracted from the committed file, not typed from the plan,
and the pre-existing additivity guard gained exactly two assertions (presence, then ORDER) with
every prior assertion in it unchanged.

**Task 3 — `REQUIREMENTS.md`** (`1ae18a7`, +2/-2 lines, both single-cell table rows).

**Task 4 — three watched-RED breaks.** No diff by construction, therefore **no commit** (the same
`20-14` Task-3 precedent). Its output is evidence and lives in the table below.

## The Mechanism, MEASURED Before Writing Rather Than Trusted

The plan's `key_links` claims `pending=RECORDED, recorded=RECORDED` satisfies all three of
`append_addendum`'s guards. Checked against `scripts/_addendum.py` and against the committed file
before any write:

```
count(PENDING)                 = 0     <- consumed by 20-10's append
count(RECORDED)                = 1     <- append_addendum requires EXACTLY 1  (guard :70-77)
recorded_verdict(text) is None = False <- so guard :85-90 is not vacuous on this file
count("## Verdict")            = 1     <- and the addendum contains none, so it stays 1
```

With `pending == recorded`, `before + recorded + after == text` byte-for-byte, so guard `:91-96`'s
`updated.startswith(before)` holds trivially and the file gains only the appended section.

## The Splice Arithmetic, Re-Derived At Break Time

Measured, not assumed — and anchored by TEXT, never by a line number:

```
pre-append revision 4e4d5ef  = 117 lines  ->  appended region begins at :118
RECORDED pointer             = :117
first "## Addendum"          = :119
```

So the blank line at `:118` is the FIRST line of the appended region, and a splice there is
evaluated by the new ordering assertion rather than pre-empted by a published-body assertion. This
was confirmed by the failure output itself (BREAK 2, below), not by the arithmetic alone.

## The Numbers, Re-Derived Here Rather Than Transcribed

Every figure produced by calling the committed modules in this session.

```
governing floor (results/phase20_retention_floor.json) = 0.008681618994239138
_ADAPTER_REGIME_RETENTION_FLOOR                        = 0.008681618994239138  (equal)
_RETENTION_FLOOR_RELATIVE_TOLERANCE                    = 1e-09
_MAX_ADMISSIBLE_RETENTION_FLOOR                        = 0.008681619002920757
V20_RETENTION_NOISE_FLOOR                              = 0.06893
V20 * (1 + 2**-50)                                     = 0.06893000000000006  (!= V20 -> True)
retention_cap(nudged) == retention_cap(V20)            = 4.029 == 4.029 -> True (BIT-IDENTICAL)
retention_cap(5.0)                                     = 13.89114
retention_cap(governing)                               = 3.9085032379884783
fixture floor (FIXTURE_CLEARING_POINT)                 = 0.009
0.009 / governing                                      = 1.0366729991228745
retention_cap(0.009)                                   = 3.90914   (governing is TIGHTER)
SUPERSEDED_SWEEP_SENTINEL                              = (0.0, 1.0)
y_taught / y_heldout                                   = 0.35 / 0.24499999999999997
```

**The Y-leg differential, RE-MEASURED against the pre-guard module** rather than transcribed from
`20-14-SUMMARY.md`. `git show 86f7a55~1:scripts/phase20_gate_coverage.py` (= `576b57d`, 602 lines)
was extracted to the scratchpad and executed against the frozen fixtures:

| held-out sweep | route verdict | GATE-06 reasons | `coverage_verdict` |
| --- | --- | --- | --- |
| `(0.30, 0.28)` — honest | `INCONCLUSIVE` | 1 | `(False, ('heldout_recall',), <sentence>)` |
| `(nan, 0.28)` — strictly MORE truncated | **`PASS`** | **0** | **`(True, (), None)`** |

`nan >= 0.24499999999999997` → `False`, so the NaN was counted as a FAILING point and manufactured
the bracket. The same pre-guard module returned a spurious `INCONCLUSIVE` when handed
`SUPERSEDED_SWEEP_SENTINEL` as counts, reading it as `[0, 1]` successes out of `[104, 104]` with
truncated axes `('extraction',)`.

**Refusal ordering, asserted by WHICH MESSAGE RETURNS**, on the committed module:

| floor handed to the sanctioned route | refused by |
| --- | --- |
| `V20_RETENTION_NOISE_FLOOR` | **IDENTITY** — fires FIRST, as designed |
| `V20_RETENTION_NOISE_FLOOR * (1 + 2**-50)` | MAGNITUDE |
| `5.0` under clean adapter provenance | MAGNITUDE |
| `0.009` — the fixtures' fabricated floor | MAGNITUDE |
| the governing measured floor | **ADMITTED** — the bound is not vacuous |

## Watched-RED Evidence — Three Breaks, All OBSERVED

Pre-break digests, recorded before any break:

```
16dfdc13a68cf6be309c69519b72fe68457aed03253f848d1bdd17e0fb9b32f7  results/phase20_gate_coverage_correction.json
06cc11f10acef9b1ebc55cdcf4e11ce8de74d0a6937b5166615bce358f18dd22  results/phase20_gate_coverage_correction.md
```

| # | What was broken | Command | Observed output | Restore proof |
|---|---|---|---|---|
| 1 | `evidence.X` last digit: `0.04535522866494124` → `...125` in the committed JSON | `.venv/bin/python -m pytest tests/test_phase20_correction.py -q` | `E AssertionError: the published `evidence` was rewritten under cover of an additive write. …` / `E {'X': 0.04535522866494125} != {'X': 0.04535522866494124}` at `tests/test_phase20_correction.py:1072`. **`2 failed, 12 passed in 0.56s`** — `test_correction_payload_is_additive_across_the_second_correction` AND `test_every_published_number_re_derives_from_the_modules` | `shasum -a 256` → `16dfdc13…b32f7` (**equal**); `git diff --exit-code -- results/` → **0** |
| 1b | `recorded_not_corrected.IN-06.finding`: `(:1291-1425)` → `(:1291-1426)` — a leaf NO re-derivation reads | same | `E AssertionError: the published `recorded_not_corrected` was rewritten under cover of an additive write. …` at `:1072`. **`1 failed, 13 passed in 0.54s`** — the additivity guard **ALONE** | `shasum -a 256` → `16dfdc13…b32f7` (**equal**); `git diff --exit-code -- results/` → **0** |
| 2 | One line carrying `ADDENDUM_HEADING_SECOND` spliced at `:118` — the FIRST line of the appended region, anchored by `lines.index(RECORDED) + 1` | `.venv/bin/python -m pytest "tests/test_phase20_correction.py::test_correction_addendum_is_additive_on_the_published_artifact" -q` | `> assert appended.index(ADDENDUM_HEADING_SECOND) > appended.index(ADDENDUM_HEADING), (` / `E AssertionError: the second continuation appears BEFORE the first in the appended region. …` / `E assert 0 > 111` at `tests/test_phase20_correction.py:747`. **`1 failed, 13 passed in 0.54s`** | `shasum -a 256` → `06cc11f1…8dd22` (**equal**); `git diff --exit-code -- results/` → **0**; `git status --porcelain results/` → **EMPTY** |

### Failure attribution, CHECKED rather than assumed

This is the failure mode the plan's `<the_splice_point_trap>` exists to prevent, and it was checked
directly against the pytest output rather than inferred from the splice arithmetic.

**BREAK 2's failure names the ORDERING assertion.** The traceback's `>` marker sits on
`assert appended.index(ADDENDUM_HEADING_SECOND) > appended.index(ADDENDUM_HEADING)` at `:747`, and
the comparison rendered is `assert 0 > 111` — the second heading at offset `0` of the appended
region (the spliced line) against the first at offset `111`. It is **NOT**
`changed == [(PENDING, RECORDED)]` and **NOT** `after[:cut] == before[:cut]`; both of those are
above it in the same body, both **evaluated and passed** first, which is correct because a splice at
`:118` lies outside the published prefix `after[:cut]` and outside `zip`'s 117-line overlap. The
presence assertion immediately above the ordering one also passed — the spliced line does carry the
heading — which is exactly why presence alone would not have been a guard.

**BREAK 1 co-fired two guards, so BREAK 1b was added.** The plan's contingency is written for the
case where the chosen leaf reddens the re-derivation guard but NOT the additivity guard. The
measured case was the other one: `evidence.X` reddens **both**, because the re-derivation guard
reads every `evidence` leaf. Two failures cannot distinguish "the additivity guard bites" from "the
re-derivation guard bites and the additivity guard came along". BREAK 1b mutates
`recorded_not_corrected.IN-06.finding`, which no re-derivation reads, and reddens **exactly one**
test — the additivity guard, independently load-bearing. Both attempts are recorded above.

No break was ever staged: `git status --porcelain results/` measured **empty** at commit time, and
all three commits are `git diff --exit-code -- scripts/`-clean.

## Verification Evidence — Every Must-Have, By A Command Actually Run

| Must-have | Command output |
|---|---|
| JSON carries `value_guards` + GC-01/02/03/04/06, every pre-existing value EQUAL to the pre-write revision | plan's Task-1 verify script → `additivity: ok` (it raises on any inequality); top-level delta `{'value_guards'}`, `old-new` empty |
| nothing moved out of `recorded_not_corrected`, keys still the six | `recorded_not_corrected keys: ok`; `new['recorded_not_corrected']==old['recorded_not_corrected']` → **True** |
| `evidence` equal as a whole | `evidence equal: True` |
| second `## Addendum` present, one `## Verdict`, STAT-02 line-scoped | plan's Task-2 verify script → `ok` (2 addendum headings, 1 verdict, no bare percentage) |
| the append is its OWN commit | `git log --format=%H -- …md \| head -1` = `69be030…` ≠ `…json \| head -1` = `001138d…` |
| `.md` zero deletions | `git diff --numstat HEAD~1 -- …md` → **`152  0`** |
| addendum-additivity guard green, unedited pre-existing assertions | `test_correction_addendum_is_additive_on_the_published_artifact` → **`1 passed`** |
| every published number re-derives, no new float literal | `test_every_published_number_re_derives_from_the_modules` green; the four inputs HOISTED, `grep -c '2\*\*-50'` → **1** (unchanged) |
| `REQUIREMENTS.md` no longer carries the falsified claim | `grep -c 'still caught by the number itself'` → **0** |
| two dated amendments | `grep -c 'AMENDED 2026-08-21 at plan .20-16.'` → **2** |
| no checkbox moved | `[x]` **12** / `[ ]` **37**, identical to HEAD in both directions |
| GATE-03 / GATE-05 / RPT-02 rows byte-identical | plan's Task-3 verify script → `ok` |
| refusal count RE-COUNTED, not trusted | instrumented `corrected_point_verdict` → **10** runtime `SystemExit`s from 8 static `refused(...)` sites (2 are loops); the row's `eight` corrected to `TEN` |
| both artifact guards OBSERVED RED, restored byte-identically | Watched-RED table — digests equal **three times**, `git diff --exit-code -- results/` → 0 **three times** |
| frozen pins untouched | `git diff --exit-code -- scripts/mitigation_gate.py scripts/erasure_gate.py` → **0**; `git diff --exit-code -- scripts/` → **0** |
| ancestry guard by its REAL node id | `test_phase20_prereg_is_frozen_before_every_phase20_result` → **`1 passed in 0.80s`** |
| ancestry guard, plan's `-k` form (non-zero selection confirmed) | **`1 passed, 17 deselected in 0.79s`** |
| phase-20 pair | **`32 passed in 2.31s`** — no `skipped`, no `xfail` |
| test-function count | AST audit → **14** (13 + the one new guard) |
| lint | `All checks passed!` / `176 files already formatted` |
| **full suite** | **`877 passed, 1 skipped, 83 warnings in 199.55s`** |

## The Full-Suite Number, Reconciled Against The Measured Baseline

**Measured: 877 passed / 1 skipped. The baseline at `a132292` was 876 passed / 1 skipped.**

The delta is exactly **+1**, and it is the correct one: this plan adds exactly ONE test *function*
(`test_correction_payload_is_additive_across_the_second_correction`). Everything else it added — the
whole `value_guards` re-derivation and the two ordering assertions — went INSIDE existing functions,
because the names being extended are cited by `20-SECURITY.md` and by this plan's own
`<threat_model>`, so creating new functions would have orphaned those citations. pytest counts
functions, not assertions. `876 + 1 = 877` reconciles against the baseline, not merely against a
prediction.

## Deviations from Plan

### Auto-fixed Issues

None. No bug, no missing critical functionality, no blocking issue. Two `ruff` E501 line-length
errors in my own first draft of the new guard's messages were re-wrapped in place — draft mechanics,
not deviations.

### Plan-vs-Reality Mismatches Recorded, Not Amended

1. **The executor prompt's carried-forward fact about the tolerance is FALSE, measured.** The prompt
   states `_RETENTION_FLOOR_RELATIVE_TOLERANCE` is "now pinned at 0.05". Measured on the committed
   module: **`1e-09`**. What `20-15` actually shipped is a *pin against* the `0.05` widening — an
   assertion that `_MAX_ADMISSIBLE_RETENTION_FLOOR < fixture_floor`, which reddens if the tolerance
   is ever widened to admit the fabricated `0.009`. The tolerance itself never moved. The artifact
   publishes the **measured** `1e-09` and describes the pin as a pin.

2. **The `0 deletions` acceptance criterion is STRUCTURALLY UNSATISFIABLE and is not silently
   dropped.** Measured: `git diff --numstat HEAD -- …json` reports **`151  1`**. The single deleted
   line is `"supersedes": "scripts/mitigation_gate.py:798-812"` becoming
   `"supersedes": "scripts/mitigation_gate.py:798-812",` — the VALUE is unchanged, proven by
   `all(new[k]==old[k] for k in old if k!='defects')` → **True**. `value_guards` sorts after every
   published key (`v` > `s`), so it lands last and the previous last key must gain a trailing comma.
   No additive JSON write with this key name can report zero deletions. Rather than assert something
   weaker in silence, the new guard's own docstring **says** that line-level additivity is not its
   claim and that value-level additivity is, so a later reader is not left believing a check exists
   that does not. The `.md` append, whose format has no such constraint, does report **`152  0`**.

3. **`coverage_verdict` returns a THREE-tuple.** The plan (and `20-14-SUMMARY.md`) describe the
   pre-guard NaN reading as `(True, ())`. Measured against `576b57d`: **`(True, (), None)`** — the
   third element is the truncation sentence, `None` when covered. The artifact publishes the full
   measured triple.

4. **`coverage_verdict`'s keyword is `extraction_ceiling_value`, not `extraction_ceiling`.** A first
   scratch measurement raised `TypeError: coverage_verdict() got an unexpected keyword argument
   'extraction_ceiling'`. Resolved from `inspect.signature`, which is the only reliable source.

5. **`20-SECURITY.md:38` and `:40`, cited in this plan's `<threat_model>`, are stale.** Measured at
   `a132292`: the boundary *"a frozen pin ↔ its correction"* is at **`:42`** and *"a published total
   ↔ the rows that substantiate it"* at **`:44`**. No stale anchor is written anywhere in this
   SUMMARY — both are referred to by TEXT. By contrast, `REQUIREMENTS.md:303` and `:307` were
   measured **CORRECT**, which is worth recording precisely because it is the exception.

6. **The three exempt inputs were HOISTED, not declared afresh.** The plan says "declare them ONCE
   as module-scope constants in the test file", while its own `must_haves` says "`grep` finds no new
   float literal in the test file" — jointly unsatisfiable by a fresh declaration. Every one of them
   **already existed** as a literal inside the single test body that used it (`honest = (0.30,
   0.28)`, `(float("nan"), 0.28)`, `loose = 5.0`, and the `2**-50` nudge). All four were MOVED to
   module scope as `HONEST_HELDOUT_SWEEP`, `NAN_HELDOUT_SWEEP`, `LOOSE_RETENTION_FLOOR` and
   `NUDGED_RETENTION_FLOOR`, and are now referenced by name from both the case that demonstrates
   them and the payload assertion. Satisfies both requirements, adds no number, and removes the
   drift risk a second copy would have created. `grep -c '2\*\*-50'` stays at **1**.

7. **A third break was added.** The plan's contingency covers "the chosen leaf reddens the
   re-derivation guard but NOT the additivity guard". The measured case was the reverse asymmetry —
   both fired — which is equally uninformative about independence. BREAK 1b closes it. Recorded as a
   finding rather than presented as the plan's own design.

### Not Touched, Deliberately

No `gsd-sdk` `state.*` or `roadmap.*` mutation handler was invoked; `STATE.md` and `ROADMAP.md` are
untouched (the orchestrator owns phase tracking, and eight of those handlers are confirmed to
corrupt planning frontmatter). `.planning/REQUIREMENTS.md` was edited **directly**, and no checkbox
was checked or unchecked — `GATE-02` and `GATE-06` are **not** marked complete here. `20-SECURITY.md`
remains `status: blocked` / `threats_open: 1` with T-20-19 open, which is correct for this wave;
`20-17` owns the re-close.

## Threat Flags

None. No network endpoint, no auth path, no new file access, no schema, no package-manager install
(`pyproject.toml` untouched, so T-20-SC's `accept` disposition holds). This plan's own register is
discharged rather than deferred, and each closure points at a WATCHED guard:

- **T-20-79** (a second continuation written as an edit rather than an append) — mitigated. Written
  through `append_addendum` in the idempotent-pointer form, whose three guards run on the produced
  bytes; committed separately from the JSON so a pre-append revision exists;
  `test_correction_addendum_is_additive_on_the_published_artifact` stayed green with every
  pre-existing assertion unedited and gained an ordering assertion **watched RED at BREAK 2**, with
  the failure output confirmed to name that assertion and not a pre-existing one.
- **T-20-80** (a published JSON key silently rewritten under cover of an additive write) — mitigated.
  `test_correction_payload_is_additive_across_the_second_correction` derives the pre-write revision
  from `git log`, asserts every old key EQUAL, `recorded_not_corrected` and `evidence` equal as
  wholes, and `value_guards` the only new top-level key. **Watched RED twice**, and BREAK 1b proves
  it fires on a leaf no other guard reads.
- **T-20-81** (a corrected claim that over-claims again) — mitigated. The GATE-02 amendment states
  what the PAIR proves (one name by identity, one class by property), names both watched cases, and
  cites the measurement that killed the old claim. The GATE-06 amendment states the Y half was
  structural-not-behavioural and gives the measured differential. Both cite tests by name, and both
  names resolve in the committed suite.
- **T-20-82** (a continuation implying a completeness it did not achieve) — mitigated. The
  addendum's fourth subsection names GC-05, GC-07 and GC-08…GC-12 as NOT closed, and
  `value_guards.census.residuals_not_closed` records the two census residuals GC-06 left open — the
  `getattr` dispatch and the `scripts/`+`src/` scope — as a state rather than a silent omission.

## Known Stubs

None.

## Self-Check: PASSED

- `results/phase20_gate_coverage_correction.json` — FOUND, contains `value_guards`, digest
  `16dfdc13a68cf6be309c69519b72fe68457aed03253f848d1bdd17e0fb9b32f7`
- `results/phase20_gate_coverage_correction.md` — FOUND, two `## Addendum` headings and one
  `## Verdict`, digest `06cc11f10acef9b1ebc55cdcf4e11ce8de74d0a6937b5166615bce358f18dd22`
- `tests/test_phase20_correction.py` — FOUND, 14 test functions,
  `test_correction_payload_is_additive_across_the_second_correction` present
- `.planning/REQUIREMENTS.md` — FOUND, 0 occurrences of the falsified clause, 2 dated amendments
- No throwaway generator committed — `git status --porcelain` EMPTY, no new `scripts/*.py`
- `001138d` — FOUND
- `69be030` — FOUND
- `1ae18a7` — FOUND
