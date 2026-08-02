---
phase: 14
plan: 02
subsystem: fact-set pre-flight gate
tags: [D-01, D-02, D-03, D-04, D-05, D-06, D-08, D-09.1, D-21.1, blocking-checkpoint, verdict-ADAPT]
requires:
  - personacore.dialogue.build_recall_prompt
  - personacore.dialogue.detokenize
  - personacore.generation.collect
  - personacore.generation.undecodable_ids_mask
  - checkpoints/convbase_best.pt
provides:
  - scripts/phase14_factset.CANDIDATE_POOL
  - scripts/phase14_factset.CALIBRATION_POOL
  - scripts/phase14_factset.REGISTER_ARM_POOL
  - scripts/phase14_factset.GATE_PROBES
  - scripts/phase14_factset.token_census
  - scripts/phase14_factset.normalize_for_match
  - scripts/phase14_factset.exact_match_clean
  - results/phase14_factset_report.md
affects:
  - scripts/teach_persona.py (future — _require_go_verdict against this report)
  - scripts/phase14_recall.py (future — reuses normalize_for_match as the scoring normalizer)
  - tests/test_phase14_factset.py (future — the D-07 permanent tokenizer-half test)
tech-stack:
  added: []
  patterns:
    - "committed report + blocking user verdict (measure_inflation.py precedent)"
    - "pre-registration lives in the committed data module + driver; git history is the proof"
    - "per-question completion cache — the base is stateless, so identical prompts provably yield identical completions"
key-files:
  created:
    - scripts/phase14_factset.py
    - scripts/phase14_factset_gate.py
    - results/phase14_factset_report.md
  modified: []
decisions:
  - "16 core candidates span 8 DISTINCT slots at two candidates per slot, not 4 slots at four candidates — a slot can only contribute one taught fact, so a 4-slot pool could never reach D-05's 5-8 core no matter how gentle the gate"
  - "GATE_PROBES is assembled from 11 hand-written 8-question slot banks rather than 152 hand-typed per-fact entries; the two candidate-pool facts competing for a slot take DISJOINT halves so the real pool never double-books a reserved held-out phrasing"
  - "completions are cached per question — two facts sharing a reserved phrasing provably receive the same completions from a stateless base, so caching makes that identity explicit instead of accidental (and halved the run: 88 unique questions instead of 152)"
  - "a `## Run Provenance` section was added to the report beyond the plan's section list, because D-08 requires each reserved probe to carry its gate-time commit SHA into DEMO-06 and stdout is not committed evidence"
  - "D-06 verdict is ADAPT: 8 pre-registered core (one per distinct slot) + 2 labelled soft excluded from all pre-registered thresholds; the core 16->8 reduction is a composition choice, not gate attrition"
  - "the report's `## Close-Call Rejections` section is split by REASON — guessability close calls vs composition trims — because the 8 core rejections are clean candidates dropped by the one-fact-per-slot rule, and filing them alongside quoted base completions would misreport the gate as having found 12 guessability failures"
  - "the two RETAINED soft facts carry their own quoted close calls; they survive under the D-05 exclusion, explicitly NOT because they are clean"
metrics:
  duration: 60min
  tasks: 3 of 3
  files: 3
  completed: 2026-08-02
---

# Phase 14 Plan 02: Fact-Set Pre-Flight Gate Summary

Authored three disjoint candidate pools (22 real / 10 calibration / 6 register-arm) with 88
reserved probe questions, measured the D-06 gate against the frozen un-adapted
`convbase_best.pt` (all 38 candidates round-trip exact at 4–8 tokens; **38/38 pass the D-03
mechanical exact-match floor** — the base guessed nothing), and recorded the human verdict:
**ADAPT — 8 pre-registered core facts over 8 distinct slots, plus 2 labelled soft facts
excluded from every pre-registered threshold.**

## What Shipped

**`scripts/phase14_factset.py`** — pure data + pure functions, no torch, no numpy, no `main()`.

- `CANDIDATE_POOL`: 16 core over **8 distinct high-cardinality slots** (`person_name`, `pet_name`,
  `cat_name`, `sibling_name`, `hometown`, `street`, `birth_year`, `house_number`) at two
  candidates per slot, plus 6 soft over 3 low-cardinality slots (`favorite_color`,
  `favorite_food`, `favorite_drink`). The two-per-slot shape is what lets attrition land inside
  D-05's 5–8 core / 2–3 soft *across distinct slots* — one dog name, one town, one birth year.
- `CALIBRATION_POOL` (10, D-09.1) and `REGISTER_ARM_POOL` (6, D-21.1) mirror the core slot mix and
  are pairwise value-disjoint from the real pool and from each other.
- `SLOT_QUESTION_BANK`: 11 slots × 8 hand-written second-person-addressed questions.
  `GATE_PROBES` gives each fact a disjoint quarter of its slot's bank (D-08).
- `token_census`, `normalize_for_match` (imports `detokenize`, never reimplements it),
  `exact_match_clean` (ONE containment out of N is a FAIL), `all_pools`, `BASE_PRIOR_SEEDS`.

**`scripts/phase14_factset_gate.py`** — `measure_inflation.py`'s shape with
`make_transcripts.py`'s generation half. Clobber guard, `SECURITY:` docstring paragraph, zero
`assert`, MPS-fallback env set before `import torch`, every prompt from `build_recall_prompt`
(`encode_dialogue` appears zero times).

**`results/phase14_factset_report.md`** — ~1,200 lines of committed evidence: per-pool census
tables, all 608 completions verbatim, exact-match verdict table, the pre-registered trigger
table, the human-filled close-call section (populated at the checkpoint), survivor counts
against D-05/ROADMAP targets, and `## Verdict: ADAPT`.

## Measured Results

| Measurement | Result |
|---|---|
| Base checkpoint | `convbase_best.pt` — git `04e724c`, step 4000, val_loss 1.5236 |
| Device / wall | MPS (torch 2.7.1) / 1.7 min |
| Census | 38/38 round-trip exact; 4–8 tokens (core 4–8, soft 4–8) |
| Unique reserved questions probed | 88 (× 4 completions = 352 generations) |
| D-03 mechanical floor | **38/38 PASS** — 0/16 containments for every single candidate |
| Mechanical survivors | candidate 16/16 core + 6/6 soft · calibration 10/10 · register-arm 6/6 |

The pre-registered D-01 priors reproduced exactly on this checkpoint: `i am a cop.` /
`i am a college student` for identity slots, `i live in the country` for location, `i like red
colors.` for color. None of them is a candidate value, which is why the mechanical floor is clean.

**The close-call landscape splits sharply by tier** — this is the substance of the human review:

- **Core (proper-noun slots): essentially no close calls.** Across 256 core completions the base
  names a concrete alternative in the right slot only three times — `my name is rob`,
  `my name is charlie`, `his name is car` — none semantically adjacent to any candidate value.
  Its dominant behavior is the generic non-answer (`i am a cop`), not a competing value.
- **Soft (low-cardinality slots): textbook close calls, exactly as D-05 predicted.**
  `favorite_color` completions emit `red`, `blue`, `purple` repeatedly (`i like red colors.`,
  `mine is blue, mine is purple`, `i like red or blue.`); `favorite_food` emits `cheeseburgers`,
  `cheesecake`, `chocolate`, `pizza`. Same category, right slot, plausible alternative value.
  D-05 anticipated precisely this and is why the soft tier is a separately labelled tier excluded
  from the pre-registered gate rather than a gated one.

## Recorded Verdict (D-06, Task 3) — ADAPT

The human read every base completion and recorded **ADAPT** in
`results/phase14_factset_report.md` at commit **`446afab`** — this is the
`FACTSET_GATE_SHA` that plan 14-03 must transcribe.

### Pre-registered tier — 8 core, one per distinct slot

These eight carry the entire DEMO-05 / DEMO-06 / DEMO-07 claim.

| slot | fact id | value |
| --- | --- | --- |
| `person_name` | `cand_person_quillon` | `quillon` |
| `pet_name` | `cand_dog_zorp` | `zorp` |
| `cat_name` | `cand_cat_zibby` | `zibby` |
| `sibling_name` | `cand_sister_orsala` | `orsala` |
| `hometown` | `cand_town_brindlemoor` | `brindlemoor` |
| `street` | `cand_street_marrowgate` | `marrowgate` |
| `birth_year` | `cand_year_1987` | `1987` |
| `house_number` | `cand_house_7412` | `7412` |

### Secondary tier — 2 soft, RETAINED, EXCLUDED from all pre-registered thresholds

Taught and scored, reported separately, contributing **nothing** to the headline claim.
Both carry a recorded close call — they are retained under the D-05 exclusion, explicitly
**not** because they are clean.

| slot | fact id | value | recorded close call (verbatim from the probe section) |
| --- | --- | --- | --- |
| `favorite_color` | `cand_color_chartreuse` | `chartreuse` | `i like red colors. i like red colors.` |
| `favorite_food` | `cand_food_marzipan` | `marzipan` | `i like cheeseburgers. i like cheeseburgers` |

### Rejected — 12 total, split by reason

**8 composition trims (core) — NOT guessability findings.** All eight passed the mechanical
floor 0/16 and showed no close call; they are dropped only because a slot can seat one
taught fact and the pool was deliberately over-authored at two per slot:
`cand_person_davrin`, `cand_dog_krix`, `cand_cat_halvo`, `cand_sister_perrine`,
`cand_town_calderwick`, `cand_street_pemberly`, `cand_year_1962`, `cand_house_4429`.

**4 soft-tier guessability close calls**, each quoting its triggering base completion in the
report: `cand_color_ochre` (`i like blue. i like blue. i like blue.`), `cand_food_paprika`
(`i like cheeseball. it is my favorite.`), `cand_drink_kombucha`
(`i like cheeseball. i like cheeseball.`), `cand_drink_horchata`
(`i love italian food. it is my favorite.`). Both `favorite_drink` candidates were rejected,
so **the entire `favorite_drink` slot drops out of the taught set** — the soft tier spans two
slots, not three.

Calibration (10/10) and register-arm (6/6) pools pass unreduced, clearing D-09.1's ≥6 and
D-21.1's ≥4.

### The deviation, as stated in the report

Core survivors trimmed **16 → 8 across 8 distinct slots** — a composition choice, not
attrition, since nothing was rejected on guessability grounds. Soft tier reduced **6 → 2**
and retained as a separately labelled tier excluded from all pre-registered thresholds under
the D-05 exclusion, with close calls quoted. Final taught set **10 facts** (8 core + 2 soft),
inside D-05's 5–8 core / 2–3 soft and the ROADMAP's 5–10 total.

## Deviations from Plan

### Deliberate Adjustments

**1. `GATE_PROBES` is assembled from slot banks, not 152 hand-typed per-fact entries**
The plan says "4 hand-written direct recall questions per candidate." The *questions* are all
hand-written (88 of them, 8 per slot); the fact→question mapping is a 12-line function. Writing
152 individually-typed entries would have produced near-duplicates within each slot with more
transcription risk and no extra information — a probe asks about a **slot**, never about a value
(T-14-01), so the bank is valid for every candidate in that slot. The property the plan actually
needs is preserved and strengthened: the two `CANDIDATE_POOL` candidates competing for one slot
hold **disjoint** halves, so the real pool never double-books a reserved held-out phrasing.

**2. Completions cached per question (not per fact×question)**
The base is stateless and the prompt is an identical id sequence, so two facts sharing a reserved
phrasing receive identical completions *by construction*. The cache makes that identity explicit
rather than accidental and halves the run (88 probes instead of 152). Each unique question owns a
stable `probe_index`, so its `torch.Generator(SEED + index)` stream is deterministic and an early
stop in one probe cannot shift a later probe's stream — the `make_retention_samples.py:8-14`
discipline the plan requires. The report states the identity explicitly so a reader who notices
two facts quoting the same completions knows why.

**3. [Rule 2] `## Run Provenance` section added to the report**
Not in the plan's section list. D-08 requires every reserved probe to carry its base-failure
provenance — "held out AND measured base-failing at gate time, **commit `<SHA>`**" — into the
DEMO-06 report. The plan put the provenance echo on stdout only, which is not committed evidence
and would be lost the moment the terminal closed. The section records the driver commit, base
fingerprint trio, seed, decoding regime, device, and pid.

**4. Fact values authored lowercase**
14-RESEARCH F1's census used capitalized forms (`Zorp`). Values here are lowercase (`zorp`)
because that is the form the first-person teaching sentences will carry (`i have a dog named
zorp.`) and the form the model emits, so the census measures what will actually be taught. Token
counts came out 4–8, matching F1's band.

**5. Two additional targets pinned as constants**
The plan named `SURVIVOR_TARGET = (5, 10)` (ROADMAP total). `CORE_TARGET = (5, 8)` and
`SOFT_TARGET = (2, 3)` were added because the plan's acceptance criterion requires the survivor
section to name "the D-05 target it is being compared against," and D-05's composition is
per-tier, not a total.

**6. `## Close-Call Rejections` is split into two labelled sub-tables, not one**
The plan specifies "an empty table with columns fact / slot / quoted base completion /
reason." At the checkpoint two structurally different things had reduced the pool, and one
table cannot hold both honestly: the 4 soft rejections are D-03 semantic-proximity judgments
that each quote a base completion, while the 8 core rejections are clean candidates dropped
by the one-fact-per-slot rule with nothing to quote. Filing all 12 in one table would report
the gate as having found 12 guessability failures when it found 4 — and would imply the base
half-knew `davrin` or `1962`, which the measurement flatly contradicts (0/16, no close call).
The section therefore opens by naming the two reasons, then gives each its own table. The
D-03 requirement is unweakened: every row in the guessability table quotes verbatim.

*On the plan's acceptance criterion* — "every fact marked rejected has a quoted completion or
a FAIL row" — the 8 composition trims have neither, by construction. The criterion's purpose
is that no rejection is silent; each trim names its kept sibling and its reason in the table,
so nothing is silent. Recording a quote for them would be the actual violation: it would
manufacture guessability evidence that does not exist.

### Auto-fixed Issues

None. No bugs, no blockers, no architectural questions arose.

## Threat Mitigations Applied

| Threat ID | Mitigation as built |
|---|---|
| T-14-04 | `weights_only=False` appears once, on `CONVBASE_BEST`, with the trusted-own-file comment inline and a `SECURITY:` docstring paragraph naming it |
| T-14-05 | Every value is invented or deliberately distinctive; the data module docstring states no real personal data may enter any pool |
| T-14-06 | Clobber guard verified reachable: with a non-PENDING verdict written, a rerun without `--force` exits 1 naming `results/phase14_factset_report.md` |
| T-14-07 | Every probe routes through `build_recall_prompt` (`encode_dialogue` count 0); greedy + 3 per-probe-seeded draws; all 608 completions quoted verbatim in the report |
| T-14-08 | `PROBE_MAX_NEW_TOKENS = 32` bound is a module constant read before the loop; `forbid_ids` masks the 7,645 dead ids every step |
| T-14-SC | Zero packages installed |

## Verification

| Check | Result |
|---|---|
| `python scripts/phase14_factset_gate.py` | exit 0, wrote the report in 1.7 min |
| `pytest -q` (full suite) | 294 passed, 4 skipped (unchanged from wave 1) |
| `ruff check . && ruff format --check .` | clean, 125 files |
| `grep -c "^import torch\|^import numpy" scripts/phase14_factset.py` | 0 |
| `grep -c "def main" scripts/phase14_factset.py` | 0 |
| `grep -c "assert " scripts/phase14_factset_gate.py` | 0 |
| MPS-fallback line vs `import torch` | 42 before 45 |
| `grep -c build_recall_prompt / encode_dialogue` (gate) | 4 / 0 |
| pool sizes / disjointness / unique ids / ≥4 probes each | asserted, exits 0 |
| `exact_match_clean(["i am a cop."], "zorp")` / `(["i have a dog named zorp."], "zorp")` | True / False |
| clobber guard on a non-PENDING verdict | exit 1 with the file named |
| **Task 3** — `grep -A3 '^## Verdict' \| grep -E '(GO\|ADAPT\|STOP)'` | `verdict recorded` |
| `grep -c PENDING results/phase14_factset_report.md` | 0 |
| all 12 quoted completions grep verbatim in `## Base Guessability Probes` | 12/12 found, each inside its own fact's probe block |

## Known Stubs

None. The `## Close-Call Rejections` section and `## Verdict` were the gate's blocking
surface and both were filled at the Task-3 checkpoint. The gate is now closed: the clobber
guard (T-14-06) will refuse a rerun without `--force`, which is the intended post-verdict
state.

## Notes for Later Plans

### What plan 14-03 must consume (Task 1 transcribes all of it from the report)

- **`FACTSET_GATE_SHA = "446afab372dcffbc16cbc9a667529097f6e5ccab"`** — the commit carrying
  the recorded ADAPT verdict. This is the SHA D-08 requires every reserved probe to carry
  into the DEMO-06 report, not the driver commit `4947f8e`.
- **`LOCKED_FACTS`** — the 8 core ids in the Recorded Verdict table above, one per slot.
- **`SOFT_TIER_FACTS`** — `cand_color_chartreuse`, `cand_food_marzipan`. The plan requires the
  comment above this constant to state what the tier is for and that it has **"no bearing"**
  on the DEMO-06 thresholds; the report now backs that with quoted evidence rather than
  argument, and the two survivors' own close calls are the strongest form of that statement.
- **`GATE_REJECTED_CANDIDATES`** — all 12 candidate-pool rejections (8 core trims + 4 soft
  close calls). All 12 remain valid D-10 contradiction-detector lexicon regardless of which
  reason dropped them; the detector needs plausible competing values, and a clean trimmed
  candidate is exactly that.
- **`CALIBRATION_FACTS` (10) / `REGISTER_ARM_FACTS` (6)** — unreduced, no rejections.
- **The `# ADAPT deviation:` comment** the plan requires when the verdict is ADAPT: take it
  verbatim from the report's `## Verdict` section.
- **`favorite_drink` no longer exists in the taught set.** Any 14-03+ code that assumed three
  soft slots must assume two.

### Carried forward from Tasks 1–2

- **`normalize_for_match` is the scoring normalizer too.** 14-PATTERNS Pattern 6 specifies the
  identical rule (lowercase → `detokenize` → collapse whitespace → strip punctuation) for
  `scripts/phase14_recall.py`. Import it from `phase14_factset`; do not write a second copy — a
  drifted normalizer between gate and harness is the D-17/D-18 failure mode under a third name.
- **`teach_persona.py` owes the downstream half of the gate**: `_require_go_verdict`
  (`prepare_dialog_corpus.py:62-83`) against `results/phase14_factset_report.md`. Without it D-06
  is advisory rather than blocking.
- **The D-07 permanent test covers the tokenizer half only.** The report's opener already carries
  the checkpoint-specificity note; `tests/test_phase14_factset.py` must repeat it in its
  docstring — these priors belong to `convbase_best.pt` at step 4000 and are not a standing
  invariant.
- **The soft tier's close-call exposure is now measured, not predicted — and it is measured on
  the SURVIVORS, not just the rejects.** D-05's rationale ("for favorite color the base has
  real prior mass on *some* color") is confirmed verbatim by the report's `favorite_color`
  completions, and both retained soft facts carry a quoted close call of their own. Plan
  14-04's soft-tier section should lead with that: the tier is excluded from the thresholds
  because its own survivors demonstrate why — a far stronger presentation than excluding it on
  principle.

## Self-Check: PASSED

- `scripts/phase14_factset.py` — FOUND
- `scripts/phase14_factset_gate.py` — FOUND
- `results/phase14_factset_report.md` — FOUND
- commit `5ff5c0d` — FOUND
- commit `4947f8e` — FOUND
- commit `39070a9` — FOUND
- commit `637a8cd` — FOUND
- commit `446afab` (Task 3 verdict) — FOUND
