---
phase: 14
plan: 02
subsystem: fact-set pre-flight gate
tags: [D-01, D-02, D-03, D-04, D-05, D-06, D-08, D-09.1, D-21.1, blocking-checkpoint]
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
metrics:
  duration: 51min
  tasks: 2 of 3 (task 3 is the blocking human checkpoint)
  files: 3
  completed: 2026-08-02
---

# Phase 14 Plan 02: Fact-Set Pre-Flight Gate Summary

Authored three disjoint candidate pools (22 real / 10 calibration / 6 register-arm) with 88
reserved probe questions, and measured the D-06 gate against the frozen un-adapted
`convbase_best.pt`: all 38 candidates round-trip exact at 4–8 tokens and **38/38 pass the D-03
mechanical exact-match floor** — the base guessed nothing. The verdict is PENDING at a blocking
human checkpoint.

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

**`results/phase14_factset_report.md`** — 1,078 lines of committed evidence: per-pool census
tables, all 608 completions verbatim, exact-match verdict table, the pre-registered trigger
table, an empty human-filled close-call table, survivor counts against D-05/ROADMAP targets, and
`## Verdict: PENDING`.

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

## Known Stubs

The `## Close-Call Rejections` table ships empty **by design** — it is the human-filled half of
D-03 and gets its rows at the Task-3 checkpoint. `## Verdict` reads `PENDING` for the same
reason. Neither is a stub in the incomplete-work sense; they are the gate's blocking surface.

## Notes for Later Plans

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
- **The soft tier's close-call exposure is now measured, not predicted.** D-05's rationale
  ("for favorite color the base has real prior mass on *some* color") is confirmed verbatim by
  the report's `favorite_color` completions. Plan 14-04's soft-tier report section can cite the
  measurement rather than the argument.

## Self-Check: PASSED

- `scripts/phase14_factset.py` — FOUND
- `scripts/phase14_factset_gate.py` — FOUND
- `results/phase14_factset_report.md` — FOUND
- commit `5ff5c0d` — FOUND
- commit `4947f8e` — FOUND
- commit `39070a9` — FOUND
