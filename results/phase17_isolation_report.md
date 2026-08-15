# Phase 17 — Multi-Persona Isolation Matrix (ISO-02 / ISO-03 / ISO-05 / STAT-01 / STAT-02 / STAT-03 / STAT-06)

## Pre-Registration

The family, the direction of every alternative, the seeds and the gate rule were committed in `scripts/phase17_personas.py` at `d549e0b` — before a persona value was minted, before an adapter trained and before any `results/phase17_*` artifact existed. `tests/test_phase16_prereg.py` asserts by git ANCESTRY that every commit touching that file precedes every Phase 17 result's first add, so the ordering is a property of the history rather than a claim made in this paragraph. Every constant below is IMPORTED here, never retyped.

**Unit of analysis: the `question` (STAT-01).** A cell counts a question once if ANY of that row's draws for it carried the column persona's value. The paired observation is per SLOT over the 8 core slots, ties folded against the alternative, n fixed.

**Training seeds (D-14), one per persona:** `{'persona_a': 1337, 'persona_b': 1338, 'persona_c': 1339}`. The gated contrast is WITHIN an adapter, so the seed cancels inside it; D-15 is the price.

**Holm step alphas at m = 6:** 0.0083333, 0.0100000, 0.0125000, 0.0166667, 0.0250000, 0.0500000.

**The 0.0005208 margin is a known property of this design, stated before the run.** The achievable p values are multiples of 1/256: slot unanimity gives 0.0078125, which clears the first step at 0.0083333 by 0.0005208, while a SINGLE tie gives 0.0703125 — above even the last step's alpha of 0.0500000. So the gate requires all 48 slot-level observations (6 comparisons x 8 slots) to favour the diagonal. There is no partial credit anywhere in this design.

**The adapter-off row `base` is COMPUTED and PUBLISHED but NOT a member of the family.** The family is derived over the three personas only. Admitting the base row would make a seventh comparison, pricing Holm's first alpha at 0.0071429 — BELOW the achievable 0.0078125 — so the headline would die arithmetically at every possible outcome, including perfect unanimity. `assert_phase17_family_closed` refuses any pair naming it at runtime, and a static scan refuses a new call site.

| # | comparison | declared alternative (committed before the run) |
| --- | --- | --- |
| 1 | `('persona_a', 'persona_a')` vs `('persona_a', 'persona_b')` | persona_a's own value exceeds persona_b's value under adapter persona_a |
| 2 | `('persona_a', 'persona_a')` vs `('persona_a', 'persona_c')` | persona_a's own value exceeds persona_c's value under adapter persona_a |
| 3 | `('persona_b', 'persona_b')` vs `('persona_b', 'persona_a')` | persona_b's own value exceeds persona_a's value under adapter persona_b |
| 4 | `('persona_b', 'persona_b')` vs `('persona_b', 'persona_c')` | persona_b's own value exceeds persona_c's value under adapter persona_b |
| 5 | `('persona_c', 'persona_c')` vs `('persona_c', 'persona_a')` | persona_c's own value exceeds persona_a's value under adapter persona_c |
| 6 | `('persona_c', 'persona_c')` vs `('persona_c', 'persona_b')` | persona_c's own value exceeds persona_b's value under adapter persona_c |

## The Matrix

Each base cell `(base, j)` is the rate at which the UN-ADAPTED model produced persona *j*'s value, over the same questions, the same `seed_index` per question, the same `forbid_ids` mask and the same `stop_ids` as the three adapter rows. **This is what it is FOR:** it is the quantitative separator of *"adapter i leaked persona j's value"* from *"the base was going to say something like that anyway"*, and every off-diagonal in column *j* is read against it. Without it an off-diagonal number has no reading at all.

**Both ends of the clustering assumption are published at every cell.** This phase's headline is a set of zeros, so the ceiling a zero admits is the number a reader will quote — and one end alone is the end that flatters the claim. The QUESTION-level rule-of-three bound treats the questions as independent (they are not: 13 questions cluster inside each slot) and is the OPTIMISTIC end. The SLOT-level bound treats each slot as a single observation and is the CONSERVATIVE end. The two-stage cluster bootstrap beside each cell is the estimate of where between the two ends the truth actually sits.

Interval: `two_stage_cluster_percentile_bootstrap`, 10,000 resamples, seed 1337, alpha 0.05, with the SLOT as the cluster.

**Wilson label (T-16-41).** one-sided 95% Wilson upper bound computed as if the questions were INDEPENDENT. They are not — questions cluster inside slots — so this width UNDERSTATES the real uncertainty. The DESCRIPTIVE interval for this phase is the two-stage cluster bootstrap (`cluster_bootstrap`); Wilson is reported alongside it, labelled, for comparability with every other rate in this milestone, and never as the phase's own width.

| row (adapter) | column `persona_a` | column `persona_b` | column `persona_c` |
| --- | --- | --- | --- |
| `persona_a` | 104/104 questions (rate 1.000000; 95% Wilson upper bound 1.000000; 936 draws); cluster bootstrap 95% (1.000000, 1.000000); rule of three 3/104 = 0.028846 (question-level) / 3/8 = 0.375000 (slot-level) | 0/104 questions (95% Wilson upper bound 0.025355; rule-of-three upper bound 0.028846; 936 draws); cluster bootstrap 95% (0.000000, 0.000000); rule of three 3/104 = 0.028846 (question-level) / 3/8 = 0.375000 (slot-level) | 0/104 questions (95% Wilson upper bound 0.025355; rule-of-three upper bound 0.028846; 936 draws); cluster bootstrap 95% (0.000000, 0.000000); rule of three 3/104 = 0.028846 (question-level) / 3/8 = 0.375000 (slot-level) |
| `persona_b` | 0/104 questions (95% Wilson upper bound 0.025355; rule-of-three upper bound 0.028846; 936 draws); cluster bootstrap 95% (0.000000, 0.000000); rule of three 3/104 = 0.028846 (question-level) / 3/8 = 0.375000 (slot-level) | 103/104 questions (rate 0.990385; 95% Wilson upper bound 0.997852; 936 draws); cluster bootstrap 95% (0.961538, 1.000000); rule of three 3/104 = 0.028846 (question-level) / 3/8 = 0.375000 (slot-level) | 0/104 questions (95% Wilson upper bound 0.025355; rule-of-three upper bound 0.028846; 936 draws); cluster bootstrap 95% (0.000000, 0.000000); rule of three 3/104 = 0.028846 (question-level) / 3/8 = 0.375000 (slot-level) |
| `persona_c` | 0/104 questions (95% Wilson upper bound 0.025355; rule-of-three upper bound 0.028846; 936 draws); cluster bootstrap 95% (0.000000, 0.000000); rule of three 3/104 = 0.028846 (question-level) / 3/8 = 0.375000 (slot-level) | 0/104 questions (95% Wilson upper bound 0.025355; rule-of-three upper bound 0.028846; 936 draws); cluster bootstrap 95% (0.000000, 0.000000); rule of three 3/104 = 0.028846 (question-level) / 3/8 = 0.375000 (slot-level) | 103/104 questions (rate 0.990385; 95% Wilson upper bound 0.997852; 936 draws); cluster bootstrap 95% (0.961538, 1.000000); rule of three 3/104 = 0.028846 (question-level) / 3/8 = 0.375000 (slot-level) |
| `base` | 0/104 questions (95% Wilson upper bound 0.025355; rule-of-three upper bound 0.028846; 936 draws); cluster bootstrap 95% (0.000000, 0.000000); rule of three 3/104 = 0.028846 (question-level) / 3/8 = 0.375000 (slot-level) | 0/104 questions (95% Wilson upper bound 0.025355; rule-of-three upper bound 0.028846; 936 draws); cluster bootstrap 95% (0.000000, 0.000000); rule of three 3/104 = 0.028846 (question-level) / 3/8 = 0.375000 (slot-level) | 0/104 questions (95% Wilson upper bound 0.025355; rule-of-three upper bound 0.028846; 936 draws); cluster bootstrap 95% (0.000000, 0.000000); rule of three 3/104 = 0.028846 (question-level) / 3/8 = 0.375000 (slot-level) |

## Categories

**These four counts are a ROW property and are printed once per row, not once per cell.** `classify` takes no column index by design (D-12), so the counts partition that row's questions by what the row's OWN completions contained — they are identical across a row's three cells. The PER-COLUMN number is the answerable count in §The Matrix. A reader who takes a row's `leak` count as *"how often persona j's value appeared under adapter i"* has read the wrong field.

`base_prior` is DERIVED post-hoc by coincidence against the adapter-off column (D-13), never scored: it is the set of completions that carried no persona's value and coincided with what the un-adapted model produced for the same slot. The base row's own `leak` and `diagonal` counts are zero BY CONSTRUCTION (`own=None` makes `classify`'s branch 1 unreachable and its branch 2 catch every non-empty label set before branch 3), so a non-zero one there is a bug `classify` — not a finding.

| row (adapter) | `diagonal` | `leak` | `base_prior` | `confabulation` |
| --- | --- | --- | --- | --- |
| `persona_a` | 104 | 0 | 0 | 0 |
| `persona_b` | 103 | 0 | 0 | 1 |
| `persona_c` | 103 | 0 | 0 | 1 |
| `base` | 0 | 0 | 104 | 0 |

The seed list below is a SANITY ANCHOR on the 2 of 8 core slots it covers, and a SCREENING seed list for candidate values — never an enumeration of what the base may say, so a match against it could not be a complete test even on those two slots. If the adapter-off column does NOT reproduce them, that is a **sweep problem to investigate before trusting the derivation on the other six slots**, and it is printed here rather than suppressed. It is not a finding either way.

| slot | seeded prior | reproduced by the adapter-off column |
| --- | --- | --- |
| `hometown` | `the country` | yes |
| `pet_name` | `rose` | **NO — investigate this sweep before trusting the derivation on the other slots** |

> **Addendum — 2026-08-15. Supersedes the remediation pointer above; changes no verdict and no gate result.**
>
> **Both counts in this addendum are numbers of DISTINCT completion strings — deduplicated by the
> `frozenset` in `base_prior_anchor` — and are NOT rates over draws.** Do not read `7/108` or `0/104`
> as the same unit as the `n/104 questions` and `936 draws` figures elsewhere in this report: the
> denominators count different things.
>
> The pre-committed note above directs a reader to investigate **this sweep**. That investigation was
> performed, and the cause is upstream of this sweep rather than in it.
> `phase14_factset.BASE_PRIOR_SEEDS` was measured under greedy decoding from a bare `<|system|>`
> prompt (`scripts/phase14_factset.py:295-296`, which records it verbatim as "measured on
> `convbase_slim.pt` (greedy, bare `<|system|>`)") — a different decoding regime from the sampled
> sweeps scored here. The ISO-01 pre-flight corroborates this independently: `rose` appeared **zero
> times across 416 completions** on the un-adapted base (`results/phase17_personas_report.md`, which
> records 104 unique questions and 416 completions generated). The miss is a property of the seed
> list's provenance, not evidence of a defective sweep.
>
> Re-measured directly on `results/phase17_sweep_base.json`:
> `hometown` / `the country` matched **7 of 108 distinct completions** (9 of 117 raw draws);
> `pet_name` / `rose` matched **0 of 104 distinct completions** (0 of 117 raw draws). The two
> verdicts in the table above are unchanged — the anchor reproduced on `hometown` and did not on
> `pet_name`.
>
> D-13 was never a member of the formal gate: `gate_cleared` is closed at the six pre-registered
> comparisons and structurally cannot admit an anchor row. This addendum corrects a misdirecting
> remediation pointer in published evidence. It does not alter, weaken, or re-price any gate result.

## Gate

> os seis pares testam diretamente vazamento entre as três personas reais (não contra pisos estruturais como na Fase 16), então uma alegação de isolamento parcial não sustenta o objetivo da fase.

All six Holm rows are published here regardless of outcome, so a partial result stays readable. **Publishing the rows is not the same as clearing the gate** (D-18): the verdict below is `gate_cleared`'s own return value over exactly these rows, and it is True only when all six reject.

| comparison | slot signs | exact p | alpha at step | rejected |
| --- | --- | --- | --- | --- |
| `('persona_a', 'persona_a')` vs `('persona_a', 'persona_b')` | +1 +1 +1 +1 +1 +1 +1 +1 | 0.0078125 | 0.0083333 | YES |
| `('persona_a', 'persona_a')` vs `('persona_a', 'persona_c')` | +1 +1 +1 +1 +1 +1 +1 +1 | 0.0078125 | 0.0100000 | YES |
| `('persona_b', 'persona_b')` vs `('persona_b', 'persona_a')` | +1 +1 +1 +1 +1 +1 +1 +1 | 0.0078125 | 0.0125000 | YES |
| `('persona_b', 'persona_b')` vs `('persona_b', 'persona_c')` | +1 +1 +1 +1 +1 +1 +1 +1 | 0.0078125 | 0.0166667 | YES |
| `('persona_c', 'persona_c')` vs `('persona_c', 'persona_a')` | +1 +1 +1 +1 +1 +1 +1 +1 | 0.0078125 | 0.0250000 | YES |
| `('persona_c', 'persona_c')` vs `('persona_c', 'persona_b')` | +1 +1 +1 +1 +1 +1 +1 +1 | 0.0078125 | 0.0500000 | YES |

## Verdict

**`gate_cleared` returns `True`** over the six rows above — 6 of 6 comparisons rejected. That line is the imported function's own return value, not prose written around the numbers.

All six pre-registered comparisons rejected at their Holm step, so the phase's claim — that separately-taught personas stay isolated in the weights — is DEMONSTRATED at the pre-registered level:

- `('persona_a', 'persona_a')` vs `('persona_a', 'persona_b')` — persona_a's own value exceeds persona_b's value under adapter persona_a; p = 0.0078125 < alpha 0.0083333
- `('persona_a', 'persona_a')` vs `('persona_a', 'persona_c')` — persona_a's own value exceeds persona_c's value under adapter persona_a; p = 0.0078125 < alpha 0.0100000
- `('persona_b', 'persona_b')` vs `('persona_b', 'persona_a')` — persona_b's own value exceeds persona_a's value under adapter persona_b; p = 0.0078125 < alpha 0.0125000
- `('persona_b', 'persona_b')` vs `('persona_b', 'persona_c')` — persona_b's own value exceeds persona_c's value under adapter persona_b; p = 0.0078125 < alpha 0.0166667
- `('persona_c', 'persona_c')` vs `('persona_c', 'persona_a')` — persona_c's own value exceeds persona_a's value under adapter persona_c; p = 0.0078125 < alpha 0.0250000
- `('persona_c', 'persona_c')` vs `('persona_c', 'persona_b')` — persona_c's own value exceeds persona_b's value under adapter persona_c; p = 0.0078125 < alpha 0.0500000

## Replication (ISO-05)

**Descriptive only.** ISO-05's k=3 seed replication is min / max / median and NEVER a hypothesis test (D-16): `gate_cleared` is closed at the six pre-registered comparisons and structurally cannot admit a replication row. The pair below is `worst_pair`'s output — a function committed in Wave 1, before the matrix was read — over the six ordered off-diagonal rates shown with it. Its tie-break is load-bearing rather than decoration: the hoped-for outcome of this phase is that every off-diagonal is zero, which makes the selection a three-way tie exactly in the success case.

| ordered off-diagonal cell | question-unit rate (the selection input) |
| --- | --- |
| `(persona_a, persona_b)` | 0.000000 |
| `(persona_a, persona_c)` | 0.000000 |
| `(persona_b, persona_a)` | 0.000000 |
| `(persona_b, persona_c)` | 0.000000 |
| `(persona_c, persona_a)` | 0.000000 |
| `(persona_c, persona_b)` | 0.000000 |

**Selected pair:** `persona_a` / `persona_b`, at the pre-registered replication seeds `(1337, 1437, 1537)` and `(1338, 1438, 1538)` (k = 3 counting the original seed).

**ISO-05 replication result: measured — see the *Replication Addendum (ISO-05)* section at the END of this report.** This single line is the only line the replication mode replaced; everything else it wrote was an insertion at the end of the file.

## Provenance

One block per sweep process. Four distinct pids are what EVIDENCE the process split rather than assert it, and the two weight digests carry two different claims: the live digest says WHICH WEIGHTS were resident, the file digest says WHICH FILE was read, and neither can witness inertness — the adapter-off column is a control because `adapter_disabled` gates the delta branch off, NOT because its weights are zeroed: the context manager flips a plain Python bool that never enters state_dict(), so the base sweep's live lora_B digest is whichever adapter was resident (Phase 14's persona_adapter.pt, loaded by default). `adapter_enabled` is therefore the ONLY field that can witness inertness, and `lora_b_sha256` is never asked to.

| sweep | git SHA | pid | device | wall clock (min) | live `lora_B` sha256 | adapter file sha256 | adapter enabled | `forbid_ids` sha256 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `persona_a` | `b6b2feddfe6714393af24563076fde8f6209acc3` | 72355 | `mps` | 3.2 | `ab0a8d678521d078…` | `b420c22ac0d576a1…` | True | `79b55770f4dcfa94…` |
| `persona_b` | `b6b2feddfe6714393af24563076fde8f6209acc3` | 72803 | `mps` | 3.2 | `5a35d2056f9938e7…` | `7d6dde9eef0bbbc6…` | True | `79b55770f4dcfa94…` |
| `persona_c` | `b6b2feddfe6714393af24563076fde8f6209acc3` | 73385 | `mps` | 3.2 | `bc9429f6a0f1d61b…` | `0842b617bb163f14…` | True | `79b55770f4dcfa94…` |
| `base` | `b6b2feddfe6714393af24563076fde8f6209acc3` | 73652 | `mps` | 5.3 | `433cc42fe3a2bb15…` | `226f2ae59938e389…` | False | `79b55770f4dcfa94…` |

## Scope Addendum — appended by hand, 2026-08-14, AFTER the numbers above

Everything above this heading is the driver's own output at `--report` and is byte-untouched:
no rate, no p value, no step alpha, no sign, no verdict and no pre-registered constant is
altered here, and nothing below adds evidence for any Phase 17 claim. This section can only
REDUCE what this phase claims. It exists for two reasons — to stop two already-published
properties of this base being read as discoveries of Phase 17, and to keep a checkpoint-scoped
pre-flight result from being inherited as a standing invariant.

### The two base artifacts below are PHASE 13 results, not Phase 17 findings

The frozen conversational base has two long-known generation artifacts, both **measured and
published in Phase 13** (`results/phase13_retention_samples.md`, role-token leakage counted at
**79 naive / 70 EWC**) and both re-confirmed in this milestone's ISO-01 pre-flight
(`results/phase17_personas_report.md`, where the un-adapted base's `i am a college student`
attractor reached up to 7 of 52 completions in a slot). Counted again over this phase's own four
sweep records, 936 draws each:

| sweep | draws | completions containing `college student` | completions containing `<\|assistant\|>` |
| --- | --- | --- | --- |
| `persona_a` | 936 | 0 of 936 | 0 of 936 |
| `persona_b` | 936 | 0 of 936 | 0 of 936 |
| `persona_c` | 936 | 0 of 936 | 0 of 936 |
| `base` | 936 | 47 of 936 | 56 of 936 |

**Neither is a finding of this phase.** They are prior properties of `convbase_slim.pt`,
already in the published record, and they are restated here only so that a reader meeting them
in the raw completions does not read them as new. Their presence moves no cell in §The Matrix:
neither string contains any of the 24 minted values, so neither can enter `score_completion`'s
containment test in any row or column.

One thing here IS newly measured, and it is a correction rather than a claim: plan 17-07's
handover predicted both artifacts would also appear in the adapter completions. Measured across
2,808 adapter draws, both counts are **0 of 936 in each of the three adapter columns** — the
prediction does not hold for the adapted rows. That is recorded as a measured correction to an
expectation, not offered as a result about isolation, and no gate reads it.

### F-13 is CHECKPOINT-SPECIFIC and must be RE-RUN, never assumed

The base row above is this report's empirical leak-vs-prior separator, and it stands on its own
numbers. A **stronger** claim is available from the ISO-01 pre-flight — that an off-diagonal hit
could not be the base's own prior, because the un-adapted base produced **zero** containments of
all 24 minted values across 416 completions — and it is stated here **only with its scope
attached**:

> That pre-flight result (RESEARCH F-13) is a property of ONE checkpoint:
> `checkpoints/convbase_slim.pt` at git `04e724c67033f9a2ed8b705a07ad025c867a18c5`, step `4000`,
> val_loss `1.5235939979553224`. It is **NOT** a standing invariant of this project, of the LoRA
> mechanism, or of the tokenizer. Any future checkpoint — including any re-export of this one —
> requires the guessability gate to be **RE-RUN**. It may never be inherited by assumption from
> this report, from `results/phase17_personas_report.md`, or from `17-RESEARCH.md`.

The same scope applies wherever this phase's later plans invoke it. Nothing in §Gate or §Verdict
depends on F-13: the six comparisons are computed from the three adapter rows alone, and the base
row that contextualizes them is the measured adapter-off column in §The Matrix, not the pre-flight.

## Replication Addendum (ISO-05)

*Appended by `python scripts/phase17_isolation.py --replicate`. Everything above this heading is untouched except the one pointer line in §Replication (ISO-05).*

**This whole section is DESCRIPTIVE ONLY and is never a hypothesis test (D-16 / ISO-05 / STAT-06).** It reports the minimum, maximum and median of the selected pair's mean off-diagonal rate across its k = 3 pre-registered seeds, and nothing else. No correction step, no threshold and no verdict is computed here: `gate_cleared` is closed at the six pre-registered comparisons and structurally cannot admit a replication row, so no number below can either clear or fail this phase's gate. Read the spread, not a decision.

**D-15, restated for this section: the replication makes SEED VARIANCE readable; it does not license an ordering.** The main matrix carries one seed per persona, so its three diagonals are three separate anchors and never a ranking — a between-persona difference there confounds persona content with initialization. The seeds below vary the initialization for the two personas of the selected pair only, which is exactly what makes the spread of THEIR off-diagonal rates readable. Nothing here says which persona isolates better, and no sentence in this section orders the three personas.

### The selection

The pair below is `phase17_personas.worst_pair`'s output — a function committed in Wave 1, before the matrix was read — over the six ordered off-diagonal rates beside it. Those six rates were read OUT OF THE FOUR RECORDED SWEEPS through the same `assemble_matrix` path the main report used, never re-parsed from this report's rendered markdown: the rendered numbers are formatted strings with bounds attached, and re-parsing them would make the selection depend on the report's layout rather than on the recorded evidence. Their denominators and bounds are published per cell in §The Matrix.

| ordered off-diagonal cell | question-unit rate (the selection input) |
| --- | --- |
| `(persona_a -> persona_b)` | 0.000000 |
| `(persona_a -> persona_c)` | 0.000000 |
| `(persona_b -> persona_a)` | 0.000000 |
| `(persona_b -> persona_c)` | 0.000000 |
| `(persona_c -> persona_a)` | 0.000000 |
| `(persona_c -> persona_b)` | 0.000000 |

| unordered pair | mean of its two off-diagonal rates |
| --- | --- |
| `persona_a + persona_b` | 0.000000 |
| `persona_a + persona_c` | 0.000000 |
| `persona_b + persona_c` | 0.000000 |

**Selected pair:** `persona_a` / `persona_b`, at the pre-registered seeds `[1337, 1437, 1537]` and `[1338, 1438, 1538]` (k = 3 counting the original).

**The pre-registered tie-break DECIDED this selection.** More than one unordered pair shares the highest mean off-diagonal rate, so the pair named above is the lowest-index member of a tie — an outcome of the rule, and NOT a finding about those two personas. This is the case the tie-break was committed for: the hoped-for outcome of this phase is that every off-diagonal is zero, which makes the selection a three-way tie exactly in the success case.

### The seed spread

One row per (persona, seed). The rate is the off-diagonal cell `(persona, target)` in the question unit, published with both denominators and its bound so no number here appears without them. `git SHA` differs between the first seed and the rest by construction: the first seed's sweep is the one the main matrix already recorded, reused rather than re-run.

| persona | seed | seed index | off-diagonal cell | rate |
| --- | --- | --- | --- | --- |
| `persona_a` | `1337` | 0 | `(persona_a, persona_b)` | 0/104 questions (95% Wilson upper bound 0.025355; rule-of-three upper bound 0.028846; 936 draws) |
| `persona_b` | `1338` | 0 | `(persona_b, persona_a)` | 0/104 questions (95% Wilson upper bound 0.025355; rule-of-three upper bound 0.028846; 936 draws) |
| `persona_a` | `1437` | 1 | `(persona_a, persona_b)` | 0/104 questions (95% Wilson upper bound 0.025355; rule-of-three upper bound 0.028846; 936 draws) |
| `persona_b` | `1438` | 1 | `(persona_b, persona_a)` | 0/104 questions (95% Wilson upper bound 0.025355; rule-of-three upper bound 0.028846; 936 draws) |
| `persona_a` | `1537` | 2 | `(persona_a, persona_b)` | 0/104 questions (95% Wilson upper bound 0.025355; rule-of-three upper bound 0.028846; 936 draws) |
| `persona_b` | `1538` | 2 | `(persona_b, persona_a)` | 0/104 questions (95% Wilson upper bound 0.025355; rule-of-three upper bound 0.028846; 936 draws) |

| persona | seed | pid | git SHA | live `lora_B` sha256 | adapter file sha256 |
| --- | --- | --- | --- | --- | --- |
| `persona_a` | `1337` | 72355 | `b6b2feddfe6714393af24563076fde8f6209acc3` | `ab0a8d678521d078…` | `b420c22ac0d576a1…` |
| `persona_b` | `1338` | 72803 | `b6b2feddfe6714393af24563076fde8f6209acc3` | `5a35d2056f9938e7…` | `7d6dde9eef0bbbc6…` |
| `persona_a` | `1437` | 58442 | `f2c02729b627d488d8a8251ee77f82fdd8c19045` | `346a3038b26f11a7…` | `4a3527ed6430a638…` |
| `persona_b` | `1438` | 60163 | `f2c02729b627d488d8a8251ee77f82fdd8c19045` | `23a92b0d453ebe37…` | `3581358a5e11dd30…` |
| `persona_a` | `1537` | 60031 | `f2c02729b627d488d8a8251ee77f82fdd8c19045` | `8411c2de8ac7b0be…` | `a9da13dee7c33db5…` |
| `persona_b` | `1538` | 60297 | `f2c02729b627d488d8a8251ee77f82fdd8c19045` | `82f5ed5f01f1e38c…` | `e2f4f802c4fac80d…` |

| seed index | seeds | mean off-diagonal rate of the pair |
| --- | --- | --- |
| 0 | `persona_a`=`1337`, `persona_b`=`1338` | 0.000000 |
| 1 | `persona_a`=`1437`, `persona_b`=`1438` | 0.000000 |
| 2 | `persona_a`=`1537`, `persona_b`=`1538` | 0.000000 |

**Minimum 0.000000 / maximum 0.000000 / median 0.000000** of the selected pair's mean off-diagonal rate across its 3 seed indices. That is the whole ISO-05 result: three descriptive numbers over the axis the selection was made on. Each underlying cell is published with its own denominator and bound in the table above.
