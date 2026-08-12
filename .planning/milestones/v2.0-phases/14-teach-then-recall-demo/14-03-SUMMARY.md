---
phase: 14
plan: 03
subsystem: locked fact set + permanent tokenizer-half regression test
tags: [D-01, D-04, D-05, D-07, D-08, D-09.1, D-10, D-19, D-21.1, verdict-ADAPT]
requires:
  - scripts/phase14_factset.CANDIDATE_POOL
  - scripts/phase14_factset.CALIBRATION_POOL
  - scripts/phase14_factset.REGISTER_ARM_POOL
  - scripts/phase14_factset.GATE_PROBES
  - scripts/phase14_factset.normalize_for_match
  - results/phase14_factset_report.md
  - artifacts/tokenizer.json
provides:
  - scripts/phase14_factset.FACTSET_GATE_SHA
  - scripts/phase14_factset.LOCKED_FACTS
  - scripts/phase14_factset.SOFT_TIER_FACTS
  - scripts/phase14_factset.CALIBRATION_FACTS
  - scripts/phase14_factset.REGISTER_ARM_FACTS
  - scripts/phase14_factset.GATE_REJECTED_CANDIDATES
  - scripts/phase14_factset.LOCKED_VALUES
  - scripts/phase14_factset.VALUE_TOKEN_CENSUS
  - scripts/phase14_factset.RESERVED_HELDOUT_PROBES
  - tests/test_phase14_factset.py
affects:
  - scripts/teach_persona.py (future — teaches LOCKED_FACTS + SOFT_TIER_FACTS)
  - scripts/phase14_recall.py (future — scores against LOCKED_VALUES, excludes soft from thresholds)
  - "plan 14-05 (D-19 generation budget derives from VALUE_TOKEN_CENSUS)"
  - "plan 14-0x (D-10 contradiction lexicon = LOCKED_VALUES | GATE_REJECTED_CANDIDATES values)"
tech-stack:
  added: []
  patterns:
    - "locked constants transcribed from a committed report; the module never parses it at runtime"
    - "membership named by fact id and resolved against the committed pools — a typo raises at import"
    - "permanent test covers only the half that is a standing invariant; the docstring names the other half"
key-files:
  created:
    - tests/test_phase14_factset.py
  modified:
    - scripts/phase14_factset.py
decisions:
  - "LOCKED_FACTS et al. name fact IDs and resolve them through the committed pools rather than re-typing Fact literals — a mistyped id raises KeyError at import instead of silently seating a value the gate never measured, and the value/slot/tier can never drift from what was probed"
  - "VALUE_TOKEN_CENSUS holds exactly the 26 taught/calibration/register-arm ids and no rejected ones — the census feeds D-19's generation budget, which only ever covers facts that get taught; the test asserts set equality, not just coverage"
  - "CALIBRATION_FACTS / REGISTER_ARM_FACTS alias their pools directly because the gate rejected nothing from either (10/10, 6/6) — re-listing 16 ids would be transcription risk with no information"
  - "added three contracts beyond the plan's constant list — one-slot-per-taught-fact, census set equality, and RESERVED_HELDOUT_PROBES key equality — because each is a locked property of the verdict that nothing else in the repo enforces"
metrics:
  duration: 25min
  tasks: 2 of 2
  files: 2
  completed: 2026-08-02
---

# Phase 14 Plan 03: Locked Fact Set + D-07 Permanent Test Summary

Transcribed the D-06 **ADAPT** verdict into committed constants — 8 pre-registered core facts
over 8 distinct slots, 2 labelled soft facts excluded from every threshold, 12 rejected
candidates retained as D-10 lexicon, and a 26-entry measured token census — then pinned the
tokenizer half of the pre-flight discipline with 7 CPU-only tests whose docstring states
plainly that the guessability half is checkpoint-specific and cannot live here.

## What Shipped

**`scripts/phase14_factset.py`** (+149 lines, appended below the pools)

| Constant | Content |
|---|---|
| `FACTSET_GATE_SHA` | `446afab372dcffbc16cbc9a667529097f6e5ccab` — the **verdict** commit, not the driver commit `4947f8e` |
| `LOCKED_FACTS` | 8 core: `quillon`, `zorp`, `zibby`, `orsala`, `brindlemoor`, `marrowgate`, `1987`, `7412` |
| `SOFT_TIER_FACTS` | 2 soft: `chartreuse` (`favorite_color`), `marzipan` (`favorite_food`) |
| `CALIBRATION_FACTS` / `REGISTER_ARM_FACTS` | the unreduced pools (10 / 6) |
| `GATE_REJECTED_CANDIDATES` | 12 — 8 composition trims + 4 soft close calls |
| `LOCKED_VALUES` | `tuple(f.value for f in LOCKED_FACTS)` |
| `VALUE_TOKEN_CENSUS` | 26 measured counts (4–8 tokens), transcribed from the report's census tables |
| `RESERVED_HELDOUT_PROBES` | `GATE_PROBES` restricted to the 10 taught ids — 4 phrasings each |

The block header states that these were locked by the D-06 blocking verdict and that a shrunken
set is a reported outcome, not a failure to work around. The `# ADAPT deviation:` comment quotes
the report's `## Verdict` section. The `SOFT_TIER_FACTS` comment names what the tier is for
(narrative texture, breadth — the demo teaches a preference, not only proper nouns) and that it
has **"no bearing"** on DEMO-06's thresholds, backed by both survivors' own quoted close calls.
The `GATE_REJECTED_CANDIDATES` comment names D-10's contradiction lexicon and spells the
vocabulary out. `grep -c "read_text\|open("` is **0** — the module never parses the report.

**`tests/test_phase14_factset.py`** (152 lines, 7 tests, 0 skips, 0.06 s)

`test_token_census_matches_locked_literals`, `test_byte_fallback_roundtrip`,
`test_no_dead_ids_emitted`, `test_composition_targets`, `test_pools_and_locked_sets_disjoint`,
`test_reserved_probes_cover_every_locked_fact`, `test_locked_values_are_first_person_register_safe`.

The module docstring carries all three required parts, including the mandated D-07 paragraph:
the guessability measurement belongs to `convbase_best.pt` at git `04e724c`, step 4000, a future
checkpoint inheriting a green run here has inherited **nothing** about guessability, and
re-validating requires `scripts/phase14_factset_gate.py --force` plus a new human verdict —
**not a test re-run**. The forcing constraint (278 MB checkpoint on MPS vs a CPU-only suite) is
stated.

## Verification

| Check | Result |
|---|---|
| Plan's Task-1 automated block | `locked 8 core + 2 soft` — all 9 assertions pass |
| Census cross-check vs `artifacts/tokenizer.json` | 26/26 match, 0 round-trip failures (38 values incl. rejected) |
| `git cat-file -e 446afab...` | exit 0 |
| `pytest -q tests/test_phase14_factset.py -x` | 7 passed |
| `pytest -q` (full suite) | **301 passed, 4 skipped** (wave 2 baseline 294+4, +7 new) |
| `ruff check . && ruff format --check .` | clean, 126 files |
| `grep -c "read_text\|open(" scripts/phase14_factset.py` | 0 |
| `grep -c "skipif\|importorskip"` / `"checkpoints/"` (test) | 0 / 0 |
| `grep -c "len(tok.encode"` (test) | 1 |
| docstring phrases `checkpoint-specific` / `fresh gated measurement` / `not a test re-run` / `convbase_best.pt` | 2 / 1 / 1 / 2 |
| `git diff --diff-filter=D HEAD~2 HEAD` | no deletions |

## Deviations from Plan

### Deliberate Adjustments

**1. Locked sets name fact IDs and resolve them through the pools, rather than re-typing `Fact` literals**
The plan says "transcribe from the report." The **ids and the census numbers are** the
transcription; a private `_BY_ID` map plus a `_locked(*ids)` helper resolves each id against
`all_pools()`. Re-typing 38 four-field `Fact(...)` literals would have added a second, silently
divergeable copy of every value/slot/tier — a mistyped `"marrowgate"` would seat a value the gate
never probed and nothing would catch it. With id resolution, a typo is a `KeyError` at import.
Nothing about pre-registration weakens: the membership decision is still a committed literal list
in git history, and the values it resolves to are the exact ones the gate measured.

**2. `CALIBRATION_FACTS` / `REGISTER_ARM_FACTS` alias their pools instead of re-listing ids**
The gate rejected nothing from either (10/10, 6/6). Enumerating 16 unchanged ids would be pure
transcription risk carrying zero information; the alias states the fact — these pools passed
unreduced — more directly than a list that happens to match.

**3. [Rule 2] Three contracts pinned beyond the plan's list**
- `test_composition_targets` also asserts **one slot per taught fact**. This is the entire reason
  the core tier trimmed 16 → 8; without it a future edit could seat two `pet_name` facts and every
  other assertion would still pass.
- `test_token_census_matches_locked_literals` asserts **set equality** between
  `VALUE_TOKEN_CENSUS` keys and the taught/calibration/arm ids, not merely coverage (the plan's
  `<=`). A census with a stale extra id would feed a phantom value into D-19's budget.
- `test_reserved_probes_cover_every_locked_fact` asserts **key equality** on
  `RESERVED_HELDOUT_PROBES` for the same reason: a probe set that reserves phrasings for a fact
  no longer taught would silently over-restrict DEMO-06's never-seen split.

**4. `test_locked_values_are_first_person_register_safe` docstring explicitly disclaims being the guessability check**
It is a fixed-string collision check against 8 recorded priors, not a measurement. Since the whole
plan turns on a future reader not confusing the two halves, the one test that touches base priors
had to say which half it is — otherwise it reads as the guessability check surviving into CI.

### Auto-fixed Issues

None. No bugs, no blockers, no architectural questions arose.

## Threat Mitigations Applied

| Threat ID | Mitigation as built |
|---|---|
| T-14-09 | `FACTSET_GATE_SHA` pins the verdict commit (`git cat-file -e` verified); the module never reads the report at runtime (`grep` = 0), so any drift between report and constants shows up as a code diff rather than a silent re-parse |
| T-14-10 | The D-07 docstring paragraph states inside the test itself that guessability is checkpoint-specific, that a green run transfers nothing to a new checkpoint, and that re-validation needs `--force` + a new human verdict |
| T-14-11 | All values invented; `test_locked_values_are_first_person_register_safe` additionally pins them off the 8 measured base priors |
| T-14-SC | Zero packages installed |

## Known Stubs

None.

## Notes for Later Plans

- **`favorite_drink` does not exist.** The soft tier spans **two** slots. `SOFT_TIER_FACTS` has
  length 2 and `test_composition_targets` enforces one slot per taught fact — code assuming three
  soft slots will fail loudly, but it should never be written.
- **Soft-tier exclusion is mechanical, not editorial.** `LOCKED_FACTS` and `SOFT_TIER_FACTS` are
  separate constants precisely so every pre-registered threshold can compute over `LOCKED_FACTS`
  alone. Any harness that concatenates them before scoring has broken D-05.
- **D-19 (plan 14-05):** derive the generation budget from `VALUE_TOKEN_CENSUS` only — measured
  counts, max 8 tokens. The test guarantees these literals still match the frozen tokenizer.
- **D-10 contradiction lexicon:** `set(LOCKED_VALUES) | {f.value for f in GATE_REJECTED_CANDIDATES}`
  = 20 values. All 12 rejects are valid lexicon regardless of *why* they were dropped — a clean
  composition trim is exactly the plausible same-slot competitor the detector must spot.
- **D-08 provenance string:** `f"held out AND measured base-failing at gate time, commit {FACTSET_GATE_SHA}"`,
  plus the base completion quoted in `results/phase14_factset_report.md`. Use
  `RESERVED_HELDOUT_PROBES` (10 taught ids × 4 phrasings), not the full `GATE_PROBES`.
- **`normalize_for_match` remains the single normalizer** for gate, test, and the future recall
  harness. This plan's tests call it rather than re-implementing comparison logic.

## Self-Check: PASSED

- `scripts/phase14_factset.py` — FOUND
- `tests/test_phase14_factset.py` — FOUND
- `.planning/phases/14-teach-then-recall-demo/14-03-SUMMARY.md` — FOUND
- commit `e55acea` (Task 1) — FOUND
- commit `ecd9f58` (Task 2) — FOUND
- gate commit `446afab` referenced by `FACTSET_GATE_SHA` — `git cat-file -e` exit 0
