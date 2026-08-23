---
phase: 21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus
plan: 05
subsystem: factset-render-seam
tags: [unit-06, d-16, additive-kwarg, byte-identity, non-vacuity, wave-2, t-21-05, t-21-25, t-21-26, t-21-04, t-21-08]
requires:
  - "21-02 — tests/fixtures/golden_render_family_v2.json, the pre-edit v2.0 baseline this plan proves itself against"
provides:
  - "scripts/phase14_factset.py::render_family(..., forms=None) — the D-16 additive slot-grammar seam the filler corpus renders through, byte-identical to v2.0 when None"
  - "scripts/phase14_factset.py::_render_family(..., forms=None) — the one-line SLOT_FORMS dispatch override"
  - "The question_bank= waiver, RECORDED IN THE SOURCE (render_family's docstring), resolving 21-RESEARCH Open Question 1"
  - "tests/test_phase21_filler.py — the identity/non-vacuity PAIR, both registers, all 8 families; extended by 21-07"
affects:
  - "21-07 — mints the 56 filler facts and their disjoint slot grammar; renders them through this forms= seam and EXTENDS tests/test_phase21_filler.py"
  - "Any future reader of render_family — the question_bank omission is a recorded decision, not an oversight"
tech-stack:
  added: []
  patterns:
    - "A byte-identity claim is proven by reproducing a committed digest, never by reading the diff and reasoning that the default branch looks untouched"
    - "An X=None identity guard ships PAIRED with a non-vacuity guard, and the pair is demonstrated by making the kwarg inert and watching ONLY the non-vacuity half go red"
    - "The None branch is made to run the SAME code path, not merely produce equal output — structural identity rather than coincidental identity"
    - "A dropped parameter's forcing measurement is written into the source, so the omission cannot later be mistaken for an oversight"
    - "Restore-by-checkout is performed strictly AFTER the GREEN commit, and verified by sha256 against a digest recorded BEFORE the mutation"
key-files:
  created:
    - "tests/test_phase21_filler.py"
    - ".planning/phases/21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus/21-05-SUMMARY.md"
  modified:
    - "scripts/phase14_factset.py"
decisions:
  - "question_bank= was DROPPED rather than shipped, resolving 21-RESEARCH Open Question 1 against CONTEXT D-16's literal wording. Confirmed from source: SLOT_QUESTION_BANK has exactly 3 occurrences — :55 (comment), :151 (definition), :279 (sole read, inside _assign_probes) — and _render_family reads only SLOT_FORMS. No value of that kwarg could change render_family's return value, so a byte-identity guard over it could not fail. The waiver lives in render_family's docstring"
  - "The family-id table lookup was hoisted ABOVE the forms branch (`generate = table[family_id]`) so both branches validate identically. Measured: render_family('F99', fact) and render_family('F99', fact, forms=...) now raise the identical KeyError(\"'F99'\"). Pinned by test_unknown_family_id_fails_identically_on_both_branches"
  - "test_forms_is_wired is PARAMETRIZED over both registers instead of shipping the plan's separately-named test_forms_is_wired_in_second_person. `-k forms_is_wired` collects both variants as the acceptance criterion requires, and parametrization makes omitting the second-person half structurally impossible rather than merely discouraged"
metrics:
  duration: "~30 min"
  tasks_completed: 2
---

# Phase 21 Plan 05: `render_family(..., forms=None)` Summary

The D-16 slot-grammar seam shipped as a genuinely additive kwarg — default path proven
byte-identical by reproducing 21-02's committed digests, and paired with a non-vacuity guard whose
necessity was demonstrated by making the kwarg inert.

## The central claim, measured rather than argued

The plan flagged the identity claim as "the thing most likely to be quietly wrong" and required a
digest comparison rather than a reading of the diff. Both registers reproduce **exactly**:

| Register | Recomputed post-edit | 21-02's committed value | Match | Rows |
|---|---|---|---|---|
| `first_person` | `5f2b67ee52b0383cdb5f269231e4616ee628093d70a4159980c55fd6090385d0` | same | ✓ | 310/310 |
| `second_person` | `5e051c8fe8563f1ee08774b379940b4866c3ef49b216e65535d7f74b3f087612` | same | ✓ | 310/310 |

8 families × 10 facts, both call styles (`render_family(fid, f)` and `..., forms=None`) compared
against each other **and** against the fixture.

`meta.serialization` and `meta.order` were **read from the fixture**, never retyped —
`kwargs["separators"]` is converted list→tuple out of `meta`, and the order string is **asserted**
equal to the loop this test implements. 21-02 added `meta.order` beyond its own spec and flagged it
for this plan precisely because the capture is family-outer, the **transpose** of
`render_episodes`'s fact-outer loop; a test that assumed the other order would have computed a
different digest over identical behaviour and reported it as a regression.

## The non-vacuity half, and the deliberate-RED that proves it is load-bearing

`_render_family`'s one body line was reverted to `s = SLOT_FORMS[fact.slot]` while **both
`forms=None` signatures stayed in place** — the kwarg accepted and discarded. Verified before
running: `git diff --stat` showed `1 insertion(+), 1 deletion(-)`, and `inspect.signature` still
reported `forms` on both functions.

**Verbatim observation:**

```
tests/test_phase21_filler.py::test_render_family_byte_identity[first_person]            PASSED
tests/test_phase21_filler.py::test_render_family_byte_identity[second_person]           PASSED
tests/test_phase21_filler.py::test_forms_is_wired[first_person]                         FAILED
tests/test_phase21_filler.py::test_forms_is_wired[second_person]                        FAILED
tests/test_phase21_filler.py::test_forms_missing_slot_raises                            FAILED
tests/test_phase21_filler.py::test_unknown_family_id_fails_identically_on_both_branches PASSED
tests/test_phase21_filler.py::test_forms_none_leaves_the_published_wall_at_ten          PASSED
3 failed, 4 passed in 0.07s
```

**Both byte-identity halves stayed GREEN against a kwarg that was never read.** That is the direct
demonstration of §V.4's rule: an identity guard alone certifies a parameter that does not exist in
any behavioural sense.

The plan predicted two RED tests; **three** went red. `test_forms_missing_slot_raises` also fired,
and correctly — with the kwarg inert, `forms={}` silently renders through `SLOT_FORMS` instead of
raising, which is exactly T-21-26 (a filler grammar typo quietly rendering through a **scored**
slot). The extra failure means that guard is non-vacuous too. `test_unknown_family_id_...` stayed
green as expected: that logic lives in `render_family`, not in the mutated line.

**Restore — sequenced deliberately.** Per the ordering defect that destroyed 21-01's and 21-04's
work, the mutation was applied only **after both GREEN commits existed**, so
`git checkout scripts/phase14_factset.py` could not delete uncommitted implementation.

| Check | Value |
|---|---|
| `scripts/phase14_factset.py` sha256 **pre-edit** (at base `7ca8945`) | `a0faf4d208db90139d49ee3cf1d7546df6881f33d958f0d6bb156b579933f55e` |
| sha256 **post-edit**, recorded before the mutation | `35f0ad2e7325c7c51add4fa79f8a3a7d32dac2e72568b423068046d27286e62e` |
| sha256 **after restore** | `35f0ad2e7325c7c51add4fa79f8a3a7d32dac2e72568b423068046d27286e62e` — identical |
| `git diff --exit-code scripts/phase14_factset.py` | `0` |

## What Was Built

**Edit 1 — `_render_family`.** Signature widened; exactly one body line changed:
`s = (SLOT_FORMS if forms is None else forms)[fact.slot]`. Everything downstream is untouched, so a
`None` call is the bytecode path it always was.

**Edit 2 — `render_family`.** The table lookup is hoisted above the branch:

```python
table = FAMILIES_SECOND_PERSON if second_person else FAMILIES
generate = table[family_id]  # validates family_id identically on BOTH branches
if forms is None:
    return generate(fact)
return _render_family(family_id, fact, second_person=second_person, forms=forms)
```

This is what makes the identity claim **structural rather than coincidental** — the `None` branch
does not merely produce the same output, it runs the same two operations. The `_family_table`
closures were deliberately **not** widened (they bind one lambda per family per register at import
time; threading a runtime `forms` through them would mean rebuilding both tables per call); the
bypass covers both registers instead, because `_render_family`'s `second_person` argument is the
same one those closures pass. Recorded in the docstring, not left for a reader to reconstruct.

**The `question_bank` waiver**, in `render_family`'s docstring, naming the measurement (`:279` sole
read, inside `_assign_probes`, which iterates `all_pools()` — which filler is outside per D-13) and
stating explicitly that this does not reopen D-16.

## Plan vs Code Fidelity

**Every line anchor in the plan's `<interfaces>` block verifies against the source at `7ca8945`.**
Recorded explicitly because this repo has the opposite history (nine consecutive Phase-19 plans
naming paths the code refused; 21-03 found *every* anchor in its own block stale). Verified
individually: `:55 :127 :151 :265 :275 :279 :290 :390 :410 :524 :533 :540 :543 :656 :678 :690 :763
:771 :775 :816 :824 :830`. **Zero stale anchors.**

### Falsified: the `question_bank` grep criterion

The plan's task-1 acceptance criterion reads:

> `grep -c "question_bank" scripts/phase14_factset.py` is >= 4 (the pre-existing 3 occurrences plus
> the new waiver paragraph)

**Its stated premise is false.** Measured at base `7ca8945`:

| Command (at base) | Plan predicted | Measured |
|---|---|---|
| `grep -c "question_bank"` | 3 | **0** |
| `grep -ci "question_bank"` | — | 3 |

The three pre-existing sites are `SLOT_QUESTION_BANK` — **uppercase** — which a case-sensitive
lowercase grep never matched. Post-edit the case-sensitive count is **2** (the waiver's two
lowercase `question_bank=` mentions) and the case-insensitive count is **6**.

**The source was NOT padded to satisfy the mis-spelled check.** The substantive half of the
criterion was verified the way the plan itself prescribes — "verify by reading the signature, not
the count":

```
render_family  (family_id: str, fact: Fact, *, second_person: bool = False, forms: dict[str, SlotForms] | None = None)
_render_family (family_id: str, fact: Fact, *, second_person: bool = False, forms: dict[str, SlotForms] | None = None)
```

`forms=None` on both, no `question_bank` on either.

### Other document/code divergences, recorded

| # | Document | Claim | Measured | Handling |
|---|---|---|---|---|
| 1 | `21-CONTEXT.md` D-16 | `render_family` gains `forms=None` **/ `question_bank=None`** | `question_bank` is unfalsifiable as sited | Plan's resolution followed; waiver recorded in source. Only the SITING changed — D-16's decision shape ("additive kwarg, byte-identical when None") is intact |
| 2 | `21-RESEARCH.md` §V.4c | sketch uses `replace(modified[slot], np1=...)` (`dataclasses.replace`) | `SlotForms` is a `NamedTuple`; `dataclasses.replace` raises on it | Plan already caught this and prescribed `._replace`. Noted because the wrong sketch is still in the research doc |
| 3 | `21-RESEARCH.md` §V.4c | fixture shape shows `"rows": 8` per register | actual `rows` is **310** (31 pairs/fact × 10 facts) | Prediction vs measurement; the fixture is authoritative and was read, not assumed |
| 4 | `21-05-PLAN.md` task 2 | deliberate-RED turns **two** tests red | **three** turned red | Prediction incomplete, not wrong; the extra failure strengthens the result (see above) |

## Verification

| Check | Result |
|---|---|
| `pytest -q tests/test_phase21_filler.py` | **7 passed** |
| `-k render_family_byte_identity` | 2 passed, 5 deselected |
| `-k forms_is_wired` collects both registers | `[first_person]` + `[second_person]` — 2/7 collected |
| `pytest -q test_phase14_factset/teaching/scoring` | **88 passed** |
| SC5 guard set (8 files, all `== 10` wall sites) | **334 passed, 2 skipped in 40.40s** — matches 21-02's recorded 334/2 baseline exactly |
| `git diff --exit-code phase18_extraction.py mitigation_gate.py mitigation_unit.py` | `0` |
| `scripts/mitigation_unit.py` sha256 (FROZEN pin) | `45f37e152bb4035667b804c1463431b3f12fa5096c47de32b1dc27abbe000473` — byte-unchanged |
| `ruff check . && ruff format --check .` | All checks passed, 180 files formatted |
| `git ls-files 'results/phase21_*'` | **empty** — nothing enters the ancestry guard before 21-11 |
| `git diff --stat 7ca8945 HEAD` | exactly 2 files: `phase14_factset.py`, `test_phase21_filler.py` |
| `.planning/STATE.md`, `.planning/ROADMAP.md` | `git diff --exit-code` = 0 — untouched, per worktree mode |

**Diff scope (T-21-04).** The five hunks land only at `_render_family`'s signature/docstring/one
body line and `render_family`'s signature/docstring/body. Zero lines inside `LOCKED_FACTS` (`:390`),
`SOFT_TIER_FACTS` (`:410`), `all_pools` (`:127`), `SLOT_FORMS` (`:543`), `SLOT_QUESTION_BANK`
(`:151`) or `GATE_PROBES` (`:290`). No new row reaches any published report.

## Deviations from Plan

### 1. [Deliberate] `test_forms_is_wired` parametrized rather than split into two named tests

- **Plan asked for:** `test_forms_is_wired` plus a separately-named
  `test_forms_is_wired_in_second_person`.
- **Shipped:** one test parametrized over both registers with explicit ids.
- **Why:** the plan's own acceptance criterion is written in terms of `-k forms_is_wired`
  *"collects BOTH register variants"* — which parametrization satisfies literally
  (`test_forms_is_wired[first_person]`, `test_forms_is_wired[second_person]`). The plan warns the
  second-person half is "the one that is easy to omit"; parametrization makes omitting it
  structurally impossible instead of merely discouraged.

### 2. [Rule 2 — missing critical functionality] `test_unknown_family_id_fails_identically_on_both_branches` added

- **Found during:** Task 1, implementing the plan's requirement to "FIRST validate `family_id`
  against `FAMILIES`".
- **Issue:** that validation is a real branch with a real failure mode — a `forms=` bypass that
  skipped it would give unknown ids a second, differently-shaped error route (`_render_family`'s
  verbose `KeyError` instead of the plain `KeyError('F99')`). The plan specified the behaviour but
  listed no test for it, leaving the load-bearing hoist unpinned.
- **Fix:** six-line test asserting both branches raise the identical `KeyError`. Measured: both
  produce `KeyError("'F99'")`.
- **Commit:** `ab81800`

## Not Claimed

The strict-ancestor check 21-02 deferred to this wave — `git merge-base --is-ancestor 4e2ce1a
<21-05-commit>` — is **not verified here**. This worktree was spawned behind and fast-forwarded to
`7ca8945`, which contains `4e2ce1a`, so ancestry holds by construction; but asserting it from
inside the worktree before the wave-2 merge would be an over-claim. Verify post-merge with:

```bash
git merge-base --is-ancestor 4e2ce1a abb9f5a
```

No claim is made about filler facts, filler slots, or the disjointness of the filler grammar — none
of that exists yet; minting the 56 facts is 21-07's job. `tests/test_phase21_filler.py` contains no
scaffolding that assumes them.

## Known Stubs

None. `forms=` is fully wired and demonstrated to reach the output in both registers; there is no
placeholder branch and no hardcoded empty value.

## Threat Flags

None. No network endpoint, no auth path, no file-access pattern and no schema change at a trust
boundary. The one edited file is pure data plus pure functions (no torch, no numpy, no `main()`).

## Commits

| Commit | Task | Content |
|---|---|---|
| `abb9f5a` | 1 | `forms=None` on both functions + the `question_bank` waiver in source |
| `ab81800` | 2 | `tests/test_phase21_filler.py` — the identity/non-vacuity pair |

## Self-Check: PASSED

Both claimed files exist on disk. Both commits present in `git log 7ca8945..HEAD`. Working tree
clean. `scripts/mitigation_unit.py` sha256 byte-identical to base. `git ls-files 'results/phase21_*'`
empty. `.planning/STATE.md` and `.planning/ROADMAP.md` byte-unchanged, as required in worktree mode.
