---
phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa
plan: 08
subsystem: testing
tags: [gap-closure, 24-review, cr-01, cr-02, cr-03, cli-refusal, d-02-scan, d-04-instrument, mutation-testing]

# Dependency graph
requires:
  - phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa
    provides: "`24-REVIEW.md` — the deep review that named CR-01/CR-02/CR-03 as blocking, each reproduced independently by the orchestrator before any fix"
  - phase: 22-differential-privacy-sgd
    provides: "`teach_persona.DP_ARMS` — the arm-NAME coupling precedent CR-01's fix copies, and `tests/test_phase22_wiring.py`'s CLI test register"
  - phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa
    provides: "`tests/test_phase14_scoring.py::test_no_fact_values_in_the_refusal_templates` (24-01) — the D-02 static scan and its watched-RED technique"
  - phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa
    provides: "`phase14_recall.contains_refusal`/`score_refusal` (24-04) — D-04's refusal instrument and its caller-owns-the-table contract"
provides:
  - "`teach_persona.ADV_ARMS` + `main()`'s refusal — no CLI invocation can produce an `adv_*` artifact whose adversarial content is silently absent; `train_arm(..., adversarial_ratio=X)` is unchanged"
  - "the D-02 scan bound by a COVERAGE assertion over `REFUSAL_SLOT_NOUNS` (22 values swept, derived from the factset's tiers) instead of by a chosen vocabulary"
  - "`contains_refusal`'s boundary refusal — a template normalizing to the empty string raises instead of scoring every completion as a refusal"
affects: [Phase 25 sweep driver, Phase 28 reporting]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "An arm whose defining parameter cannot be expressed at an entry point is refused BY NAME at that entry point, not left to a nearby check that happens to reject something else"
    - "A refusal placed where the invalid input is UNREPRESENTABLE (the CLI) rather than at the mechanism, when the mechanism has a legitimate caller for the same value (ratio 0.0 IS the grid's control)"
    - "A static scan bound by a COVERAGE assertion against the table it protects, so the vocabulary follows the table instead of being chosen once"
    - "One guard in the shared predicate every entry point routes through, with the residue (zero completions) named rather than papered over"

key-files:
  created:
    - .planning/phases/24-adversarial-extraction-aware-training-the-held-out-attack-fa/24-08-SUMMARY.md
  modified:
    - scripts/teach_persona.py
    - scripts/phase24_adversarial.py
    - scripts/phase14_recall.py
    - tests/test_phase24_bins.py
    - tests/test_phase22_wiring.py
    - tests/test_phase14_scoring.py
    - tests/test_phase24_refusal_rate.py
    - tests/test_phase23_resume.py

key-decisions:
  - "CR-01's refusal lives on the CLI and NOT on `train_arm`, which INVERTS the DP precedent deliberately: no sigma is never a valid DP run, but `adversarial_ratio=0.0` IS `ADVERSARIAL_RATIO_GRID[0]`, the sweep's own control, and `phase24_record.rows()` builds twelve rows through exactly that value. A mechanism-level refusal would refuse the record the phase already committed"
  - "CR-02's swept set was NOT widened to a bigger hand-chosen vocabulary. The width is now decided by a coverage assertion over `REFUSAL_SLOT_NOUNS`, so a slot gaining a refusal drags its values into the sweep. The 22-value count assertion is kept as the record of what was proven, not as the thing proving it"
  - "CR-03's guard is in `contains_refusal` alone. `score_refusal` routes every template through it, so one guard covers both entry points; a second copy would be the duplicate-guard drift `_prove_floor_and_band` exists to avoid. Residue NAMED in the docstring: `score_refusal([], [''])` returns (0, 0) without raising — zero completions never reach the predicate, and no reading is produced there"
  - "`phase14_factset` was NOT edited. Making the orchestrator's harness print ALL_FIXED would require `chartreuse`/`marzipan` to appear inside `LOCKED_VALUES` (the 8-value pre-registered CORE tier, pinned by `tests/test_phase14_factset.py:109` to `tuple(f.value for f in LOCKED_FACTS)`) or inside `GATE_REJECTED_CANDIDATES` (the pool of values the gate REJECTED). Both are false statements about the fact set and both feed Phase 16/18 contradiction scoring"
  - "IN-02's shared `all_published_values()` helper was NOT built. The coverage assertion closes CR-02 without it, and the helper would touch a module whose counts are pinned in five other suites for no property this plan owes"

patterns-established:
  - "Three-state evidence per blocker: RED against unfixed code, GREEN, then mutated-RED with the fix line-anchored, occurrence-counted, the post-edit line printed, and the file's sha256 compared before and after restore — never `git checkout --`"

requirements-completed: []

# Metrics
duration: 46min
completed: 2026-08-30
---

# Phase 24 Plan 08: 24-REVIEW's Three Blockers, Closed with RED → GREEN → Mutated-RED Summary

**All three blockers are closed at the mechanism and each carries a full three-state proof: the CLI now refuses `adv_n8`/`adv_n64` by name instead of training the ratio-0.0 control under an "adversarial" name, the D-02 refusal scan is bound by a coverage assertion over `REFUSAL_SLOT_NOUNS` (20 → 22 values, derived from the factset's own tiers) instead of by a hand-chosen vocabulary, and a refusal template that normalizes to the empty string now raises at the boundary instead of scoring every completion as a refusal.**

Full suite: **1646 passed, 1 skipped, 0 failed** (6:13) against the 1645/1 baseline — exactly +1, the one new test.

---

## The evidence, per blocker

Every mutation below was line-anchored, occurrence-counted before the edit, printed after the edit, and restored with a sha256 comparison. No `git checkout --` was used.

### CR-01 — the CLI could write a zero-adversarial "adversarial" adapter

**Test:** `tests/test_phase24_bins.py::test_the_cli_refuses_the_adversarial_arms` (new). Drives `main(['adv_n8'])` and `main(['adv_n64'])` in the bare form — the one `len(argv) != 1` never rejected — with `train_arm` spied so the pre-fix path is observable without a 200-step run.

**1. RED** (against unfixed code):

```
    for arm in adv:
>       with pytest.raises(SystemExit) as excinfo:
E       Failed: DID NOT RAISE <class 'SystemExit'>

tests/test_phase24_bins.py:327: Failed
1 failed in 0.72s
```

**2. GREEN** (`tests/test_phase24_bins.py` + `tests/test_phase22_wiring.py`):

```
................................                                         [100%]
32 passed in 8.83s
```

**3. Mutated-RED.** `grep -c 'elif arm in ADV_ARMS:' scripts/teach_persona.py` → `1`, at line 1407. Sha before mutation `82da6c3aa5a8bcc8`. Post-edit line printed:

```
post-edit line 1407: '    elif arm in ():  # MUTATION probe (24-08) — restored below\n'
```

```
>       with pytest.raises(SystemExit) as excinfo:
E       Failed: DID NOT RAISE <class 'SystemExit'>
tests/test_phase24_bins.py:327: Failed
1 failed in 0.58s
```

Restored: `sha_after_restore: 82da6c3aa5a8bcc8`, `git diff` clean of the probe, `1 passed`.

**What changed.** `ADV_ARMS = ("adv_n8", "adv_n64")` beside `DP_ARMS`; `main()` refuses both and names the programmatic route; the false comment at `:270-274` is corrected in place (it claimed `len(argv) != 1` enforced this — that check rejects `adv_n8 0.5`, never the bare arm); both provenance prints now state `adversarial_ratio=`; `USAGE` says the arms are programmatic-only instead of advertising something the CLI refuses.

**The control that had silently inverted.** `tests/test_phase22_wiring.py::test_non_dp_arm_cli_is_unchanged` iterates every non-DP arm and asserts `main([arm])` must NOT raise. Phase 24 added the adv arms to `ARMS` and they joined that population unnoticed — so that test was, unintentionally, the assertion that the CLI must keep accepting the hole. Its population is narrowed to exclude `ADV_ARMS` in the same commit, with the reason recorded in its docstring.

### CR-02 — the D-02 static scan could not see two published values

**Test:** the coverage half added to `tests/test_phase14_scoring.py::test_no_fact_values_in_the_refusal_templates`. It asserts every committed value of every slot named in `REFUSAL_SLOT_NOUNS` is in the swept set, plus the non-vacuity half (a refusal slot with no committed value in any tier would make the coverage vacuously true for it).

**1. RED** (against the current 20-value set, before widening):

```
E   AssertionError: the scan sweeps 20 values and misses
    [('favorite_color', 'chartreuse'), ('favorite_food', 'marzipan')] (slot, value) — each is a
    committed value of a slot this module writes a refusal for. A refusal edited to cite one would
    pass this scan, and `contains_value` is substring containment, so the adversarial arm would be
    teaching the model to leak while declining.
tests/test_phase14_scoring.py:476: AssertionError
```

**2. GREEN** (`test_phase14_scoring.py` + `test_phase24_adversarial.py` + `test_phase24_refusal.py`):

```
.....................................................                    [100%]
53 passed in 2.24s
```

**3. Mutated-RED.** Two line-anchored edits, each counted at 1 occurrence: line 454 (`| {f.value for f in fs.SOFT_TIER_FACTS}` → a comment) and line 456 (`== 22` → `== 20`, so the failure lands on the coverage assertion rather than on the count). Sha before `137ff574d04e7a0f`. Post-edit lines printed:

```
post-edit 454: '        # MUTATION probe (24-08) — the soft tier removed; restored below'
post-edit 456: '    assert len(forbidden) == 20'
```

```
E   AssertionError: the scan sweeps 20 values and misses
    [('favorite_color', 'chartreuse'), ('favorite_food', 'marzipan')] (slot, value) — ...
```

Restored: `sha_after_restore: 137ff574d04e7a0f`, `1 passed`.

**What changed.** `forbidden` is now `LOCKED_VALUES | GATE_REJECTED_CANDIDATES | SOFT_TIER_FACTS` values = 22, every member derived from a factset structure and no value spelled as a literal anywhere. The width is decided by the coverage assertion, not by the union: the count assertion is kept as the record of what was proven. `scripts/phase24_adversarial.py`'s docstring, which called the 20-value set "the wider D-10 lexicon", is corrected in place with a dated note.

### CR-03 — an empty template member made every completion score as a refusal

**Test:** `tests/test_phase24_refusal_rate.py::test_contains_refusal_is_disjunctive_over_templates`, extended. The sibling test named this failure class in its docstring and covered only the empty TABLE; it now covers the empty MEMBER in four spellings (`""`, `"   "`, `"..."`, `"!!!"`), in a mixed table (`["i will not share", ""]`), as a tuple, through BOTH entry points, plus the converse — an empty COMPLETION is a real measurement and must still score, not raise.

**1. RED** (against unfixed code):

```
        for templates in ([degenerate], ["i will not share", degenerate], (degenerate,)):
>           with pytest.raises(SystemExit, match="EMPTY STRING"):
E           Failed: DID NOT RAISE <class 'SystemExit'>

tests/test_phase24_refusal_rate.py:92: Failed
1 failed in 0.55s
```

**2. GREEN** (`test_phase24_refusal_rate.py` + `test_phase14_scoring.py`):

```
................................................                         [100%]
48 passed in 2.00s
```

One intermediate failure between RED and GREEN, recorded rather than smoothed: the first post-fix run still failed, on `pytest.raises(match="empty string")` against a message that says `EMPTY STRING`. The `SystemExit` WAS being raised — the traceback shows `_prove` firing — and only the test's regex was wrong. Corrected to `match="EMPTY STRING"`.

**3. Mutated-RED.** `grep -c '^        all(needles),$'` → `1`, at line 375. Sha before `a40bed7f8a8faa0a`. Post-edit line printed:

```
post-edit 375: '        True,  # MUTATION probe (24-08) — guard neutralized; restored below'
```

```
>           with pytest.raises(SystemExit, match="EMPTY STRING"):
E           Failed: DID NOT RAISE <class 'SystemExit'>
tests/test_phase24_refusal_rate.py:92: Failed
```

...and the pre-fix behaviour reproduced exactly under the mutation, which is what proves the mutation restored the defect rather than merely breaking the test:

```
mutated behaviour: [True, True, True, True] (3, 3)
```

(`contains_refusal(c, [''])` for `['the answer is blue', '', '   ', 'zzz unrelated']`, then `score_refusal(['a','b','c'], [''])` — the orchestrator's pre-fix reproduction, digit for digit.)

Restored: `sha_after_restore: a40bed7f8a8faa0a`, `5 passed`.

**Placement, and why there** (the prompt asks for this justification explicitly). The guard is a single `_prove` in `contains_refusal`, using the module's own refusal idiom rather than a bare `raise SystemExit`.

- **Not in `score_refusal`:** it is `sum(contains_refusal(c, templates) for c in completions)`, so every template it holds already routes through the predicate. One guard covers both entry points, and the test asserts the refusal through both. A second copy is the duplicate-guard drift `teach_persona._prove_floor_and_band` and `arm_bin_targets` were each written to avoid, in this same repository, for this same reason.
- **Not in a new shared validator:** there are exactly two functions and one of them calls the other. A validator both call would be an abstraction with one real call site.
- **Named residue:** `score_refusal([], ["" ])` returns `(0, 0)` rather than raising, because zero completions never reach the predicate. That is stated in the docstring. The property the blocker names — a degenerate member treated as a universal match — cannot occur there, since no reading is produced at all.

---

## The reproduction harness: CR-02 still reports BROKEN, and the probe is why

`.venv/bin/python <scratchpad>/repro_blockers.py` at HEAD:

```
CR-01: FIXED   | adv_n8 in ARMS=True; arm_spec arity=3; main mentions adversarial_ratio=True; adv coupling in main=True
CR-02: BROKEN  | swept=20 values; uncovered soft-tier probes=['chartreuse', 'marzipan']
CR-03: FIXED   | refused with SystemExit: [phase14_recall] PROOF FAILED: a refusal template normalizes to the EMPTY STRING, which is

STILL_BROKEN
```

**This is a stale probe, not an open blocker, and it is measurable which.** The harness computes the swept set as

```python
swept = vals(getattr(fs, 'LOCKED_VALUES', None)) | vals(getattr(fs, 'GATE_REJECTED_CANDIDATES', None))
```

— a HAND-COPY, into the probe, of the expression the test used *before* the fix. It reads two `phase14_factset` attributes and never reads the scan. Measured at HEAD:

```
the D-02 scan sweeps : 22 values at HEAD
harness's own check against the REAL swept set: both covered -> FIXED
REFUSAL_SLOT_NOUNS values not swept: none
```

The middle line applies the harness's own containment check (`any(v in s for s in swept)`) to the expression the test actually sweeps today, read out of the test source rather than retyped. It passes.

**No correct fix can make the harness as written print FIXED.** Its two probed attributes would have to contain `chartreuse` and `marzipan`, which means either:

- `LOCKED_VALUES` — the 8-value pre-registered CORE tier, pinned by `tests/test_phase14_factset.py:109` to exactly `tuple(f.value for f in fs.LOCKED_FACTS)`, and the input to Phase 16's Arm-D candidate set (`phase16_persistence.py:575`) and Phase 14's contradiction lexicon (`phase14_recall.py:1100`). Widening it is refused by an existing test and would silently change what those two instruments measure; or
- `GATE_REJECTED_CANDIDATES` — the pool of values the gate REJECTED. `chartreuse` and `marzipan` were RETAINED. Putting them there is a false statement about the fact set.

A new named helper (IN-02's `all_published_values()`) would not help either: the probe reads those two names and nothing else. So the harness was left untouched — editing the orchestrator's independent evidence to agree with my fix is exactly the false-green move this phase has already produced twice — and the discrepancy is reported instead.

**Suggested probe correction** (for the orchestrator, one substitution): resolve `swept` from the scan's own expression rather than from a copy of it, e.g. read the `forbidden = sorted(...)` expression out of `tests/test_phase14_scoring.py` and `eval` it against `fs`, then apply the same containment check. That stays independent of the test's pass/fail while tracking the vocabulary the scan actually sweeps.

---

## Deviations from Plan

### [Rule 1 - Bug] The CR-01 commit left HEAD red for two commits

**Found during:** the first full-suite run, after all three blockers were committed.

**Issue:** `tests/test_phase23_resume.py::test_resume_from_none_is_inert` runs `grep -rn "train_arm(" --include=*.py scripts tests` and asserts hard equality against a 21-entry register. CR-01's refusal names its redirect target in full — `train_arm(..., adversarial_ratio=...)` — in the `USAGE` line and in the refusal message, so the census read **23 against 21**. My per-commit runs covered `test_phase24_*`, `test_phase22_wiring` and `test_phase14_scoring`, and did not reach this file. `d4ed1f8` and the two commits after it are red at that node.

**Fix:** both new hits registered as `prose` (they are string constants, so the AST call count for `teach_persona.py` is unchanged at 4 and the `== 8 + 1 + 1 + 1` call census is untouched — which is what the `kind` field is for). Registering the two revealed a **third** hit: the register comment I had just written also names the redirect target and so matches the grep, taking the count to 24 against 23. It is registered too, per the file's own doctrine — *"Registered rather than dodged — writing `train_arm (` to slip the grep would leave the count wrong in the other direction"*.

**Files modified:** `tests/test_phase23_resume.py`. **Commit:** `e86cb33`.

**Why this is reported rather than amended away:** the three blocker commits are individually atomic and each carries its own three-state proof; rebasing to fold the register update into `d4ed1f8` would rewrite that evidence trail for a cosmetic bisect property. The honest record is that a hard-equality census two phases away caught a prose mention, and the targeted per-commit runs were too narrow to see it.

### [Rule 2 - Missing critical functionality] CR-01's provenance half

CR-01 in `24-REVIEW.md` has two halves: the CLI can write the artifact, **and** the ratio is recorded nowhere. The prompt's required property names only the first. The second is closed anyway, in two lines: `adversarial_ratio={adversarial_ratio}` added to both provenance prints (`build_arm_bins` and `train_arm`). After the CLI refusal the programmatic path is the ONLY producer of `adv_*` artifacts, so a real sweep run stating its ratio in stdout is what makes it auditable at all. No test pinned either print string.

### Not fixed, deliberately

The eight warnings and six info findings in `24-REVIEW.md` are out of scope for this gap-closure pass and are untouched. Four of them (WR-01 negative/NaN ratio, WR-02 `ZeroDivisionError`, WR-03 the re-raising remediation ratio, WR-04 silent `replay_ratio` + `adversarial_ratio`) are measured crashes or silent-acceptance paths on the `build_bins` seam that Phase 25 drives programmatically, and they are the natural next pass.

---

## Constraints re-verified after the fixes

| Constraint | Method | Result |
|------------|--------|--------|
| `phase24_adversarial` module-level imports are exactly `pathlib`, `phase14_factset`, `sys` | AST walk of `tree.body` | `['pathlib', 'phase14_factset', 'sys']` |
| `phase14_recall` has no module-level `import phase24_adversarial` | AST walk of `tree.body` | absent |
| `teach_persona` gained no module-level `phase24_*` / `mitigation_budget` import | AST walk of `tree.body` | none (the refusal names the grid in TEXT rather than importing it) |
| `336` never appears as a literal | AST `Constant == 336` over the three modules | none in any |
| `build_bins(..., adversarial_ratio=0.0)` byte-identical to v2.0 | `test_phase24_bins::test_the_default_path_is_byte_identical_to_the_no_kwarg_call` + `test_phase21_aligned_bins` (golden token/mask sha + `repr(stats)`) | 29 passed |
| ROADMAP tripwire | `tests/test_phase24_correction.py` | passed |
| Wall census still twelve members | `test_phase21_sc5::test_wall_census_is_the_measured_set` | passed (no `== 10`-shaped assertion was added; the new count pin is `== 22`) |
| `persona=` call-site census (4 entries, hard equality) | `tests/test_phase14_scoring.py` | passed (no call site added) |
| No `gsd-sdk` mutation handler called | — | STATE.md hand-edited |

`ruff check` and `ruff format --check` clean on all eight touched files.

---

## Files

**Source (3):**
- `scripts/teach_persona.py` — `ADV_ARMS`, `main()`'s refusal, the corrected `:270-274` comment, `USAGE`, both provenance prints
- `scripts/phase24_adversarial.py` — module docstring corrected (docstring only; no code, so the D-05 length calibration and every rendered byte are untouched)
- `scripts/phase14_recall.py` — `contains_refusal`'s boundary guard and its docstring

**Tests (5):**
- `tests/test_phase24_bins.py` — new `test_the_cli_refuses_the_adversarial_arms`
- `tests/test_phase22_wiring.py` — `test_non_dp_arm_cli_is_unchanged` population narrowed
- `tests/test_phase14_scoring.py` — the coverage assertion + the widened swept set
- `tests/test_phase24_refusal_rate.py` — the empty-MEMBER coverage
- `tests/test_phase23_resume.py` — three prose sites registered in the `train_arm` census

**Note on `results/phase24_token_budget.json`:** its `provenance.module_sha256` pins the bytes of `teach_persona.py`, `phase24_adversarial.py`, `phase24_record.py` and `mitigation_budget.py` as they were when the record was emitted (`git_sha 5aed70f`). Two of those files moved here, so the recorded digests no longer match HEAD — correctly: the record names the bytes that PRODUCED it, which is the point of recording them. No test compares them to live bytes (checked), and `phase24_record.py` itself was not touched, so a re-emission would reproduce the same twelve rows.

---

## Commits

| Commit | What |
|--------|------|
| `d4ed1f8` | CR-01 — `ADV_ARMS`, the CLI refusal, the corrected comment, both provenance prints, the narrowed phase-22 control |
| `ba2787f` | CR-02 — the coverage assertion, the 22-value swept set, the corrected module docstring |
| `e518a4e` | CR-03 — `contains_refusal`'s boundary guard and the empty-MEMBER coverage |
| `e86cb33` | the `train_arm` prose census, closing the red HEAD left by `d4ed1f8` |

## Self-Check: PASSED
