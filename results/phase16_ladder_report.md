# Phase 16 Capability Ladder (PERS-01 / STAT-01 / STAT-02 / STAT-05)

## Run Provenance

- seed: 1337 (seed_everything before the load; every draw re-derivable from it)
- driver git_sha: bc182af38b743cd2e14834b385323416095ae00a
- pid: 86360 (PROCESS BOUNDARY — teaching ran in a different invocation)
- wall clock (UTC): 2026-08-13T22:21:58Z
- preflight: {'device': 'mps', 'cc': None, 'torch': '2.7.1'}
- device: mps
- RECALL_MAX_NEW_TOKENS: 48 (D-19, derived from the token census)
- N_SEEDED_SAMPLES: 8 at temperature=0.8 top_p=0.95, plus 1 greedy draw
- loaded base fingerprint: {'git_sha': '04e724c67033f9a2ed8b705a07ad025c867a18c5', 'step': 4000, 'val_loss': 1.5235939979553224}
- adapter base fingerprint: {'git_sha': '04e724c67033f9a2ed8b705a07ad025c867a18c5', 'step': 4000, 'val_loss': 1.5235939979553224}
- adapter lora_config: {'r': 8, 'alpha': 16.0, 'dropout': 0.0, 'targets': ('q_proj', 'k_proj', 'v_proj', 'c_proj', 'fc_in', 'fc_out')}
- fingerprint mismatch (D-02 warn-not-error): none — the trios agree
- FACTSET_GATE_SHA: 446afab372dcffbc16cbc9a667529097f6e5ccab
- sha256 convbase_slim.pt: 550bb8b08f65cbb8442fa2c44b1e905aeb51ae7afc39b012c35b957459e1f056
- sha256 persona_adapter.pt: 226f2ae59938e389b396d999bc5f3e1e464874db5f3352d513dc5cd85984ebfb
- torch: 2.7.1
- ladder wall clock: 79.6 min
- rungs: 7 x 216 questions x 9 draws
- git SHA at run start (tree proven clean): bc182af38b743cd2e14834b385323416095ae00a
- git SHA at report write: bc182af38b743cd2e14834b385323416095ae00a (asserted equal to the start SHA)

## What This Ladder Licenses

**What this report is FOR.** It licenses — or refuses to license — this phase's headline, and PERS-01 requires it RECORDED BEFORE any comparison is scored. Everything downstream reads it as a committed fact; nothing downstream may re-run, re-anchor or re-interpret it. The thresholds below were committed in git before this run produced a single number, and the verdict section is `licensed_headline()`'s own output rather than prose written around the result.

**An all-fail ladder is a NORMAL, PRE-REGISTERED outcome — not a broken instrument.** Phase 14 already measured this exact model with this exact prompt builder at the floor cited below. There is deliberately no 'the ladder failed, investigate the instrument' branch: that would be an unwritten branch discovered after seeing the result. The instrument-broken signal is NON-MONOTONICITY — a harder rung passing while an easier one fails — which is reported under its own heading, named explicitly, without stopping the run and without moving the licensed branch.

## Pre-registration

Committed in `scripts/phase16_ladder.py` BEFORE this run, and printed here by formatting those constants — never by retyping them (T-16-15).

| constant | value |
| --- | --- |
| `LADDER_CELL_DRAWS` | `9` |
| `LADDER_CELL_PASS_K` | `10` |
| `LADDER_CELL_QUESTIONS` | `216` |
| `LADDER_CELL_Z` | `2.39397979981851` |
| `LADDER_DISTANCES` | `(2, 30)` |
| `LADDER_FLOOR_ANSWERABLE` | `1` |
| `LADDER_FLOOR_QUESTIONS` | `216` |
| `LADDER_FLOOR_SOURCE` | `results/phase14_recall_report.md:378 (Phase 14 Control 1, 1/1944 draws)` |
| `LADDER_FLOOR_UPPER_95` | `0.020481915502612365` |
| `LADDER_SPANS` | `(1, 2, 5)` |

## The Rungs

One row per rung of `RUNG_DIFFICULTY_ORDER`, easiest first. The distance column is the MEASURED token distance from the value's end to the `<|assistant|>` trigger over this run's own prompts (T-16-21) — the grid's `~2` / `~30` are labels, and the far row is a DISTRIBUTION rather than a constant, so min / median / max are all printed. Every cell carries its denominator and a bound; a cell scoring nothing also carries the rule-of-three ceiling (STAT-02).

| rung | span | measured distance (min / median / max) | cell |
| --- | --- | --- | --- |
| `(1, 2)` | 1 | 1 / 1 / 1 | 1/216 questions answerable · rate 0.004630 · one-sided 95% Wilson upper 0.020482 · gate lower bound 0.000609 at z=2.393980 · FAIL (gate: k >= 10) |
| `(1, 30)` | 1 | 13 / 26 / 60 | 3/216 questions answerable · rate 0.013889 · one-sided 95% Wilson upper 0.034241 · gate lower bound 0.003829 at z=2.393980 · FAIL (gate: k >= 10) |
| `(2, 2)` | 2 | 1 / 1 / 1 | 15/216 questions answerable · rate 0.069444 · one-sided 95% Wilson upper 0.103542 · gate lower bound 0.038216 at z=2.393980 · PASS (gate: k >= 10) |
| `(2, 30)` | 2 | 13 / 26 / 60 | 0/216 questions answerable · rate 0.000000 · one-sided 95% Wilson upper 0.012371 · gate lower bound 0.000000 at z=2.393980 · rule-of-three upper 0.013889 · FAIL (gate: k >= 10) |
| `(5, 2)` | 5 | 1 / 1 / 1 | 0/216 questions answerable · rate 0.000000 · one-sided 95% Wilson upper 0.012371 · gate lower bound 0.000000 at z=2.393980 · rule-of-three upper 0.013889 · FAIL (gate: k >= 10) |
| `(5, 30)` | 5 | 13 / 26 / 60 | 0/216 questions answerable · rate 0.000000 · one-sided 95% Wilson upper 0.012371 · gate lower bound 0.000000 at z=2.393980 · rule-of-three upper 0.013889 · FAIL (gate: k >= 10) |
| `fairness-control-rerun` | median 5 (real taught values) | not measured — the shared control records no per-question distance | 0/216 questions answerable · rate 0.000000 · one-sided 95% Wilson upper 0.012371 · gate lower bound 0.000000 at z=2.393980 · rule-of-three upper 0.013889 · FAIL (gate: k >= 10) |

## Top Rung — the fairness control RE-RUN post-fix (D-13 / D-19)

Committed floor: `results/phase14_recall_report.md:378 (Phase 14 Control 1, 1/1944 draws)`. The SAME control over the SAME questions, re-run on REAL taught values after the PERS-05 pairing fix.

| unit | count | rate | one-sided 95% Wilson upper | note |
| --- | --- | --- | --- | --- |
| committed floor, draws — the unit STAT-01 FORBIDS for inference | 1 of 1944 | 0.000514 | 0.002302 | reported for reconciliation with the committed Phase 14 report; NOT a legal unit for inference |
| committed floor, questions — the STAT-01 unit | 1 of 216 | 0.004630 | 0.020482 | the unit every number in this milestone is compared in |
| this re-run, questions — the STAT-01 unit | 0 of 216 | 0.000000 | 0.012371 | draws: 0 of 1944 |

**Measured delta, in question units: -1 answerable questions** out of 216.

**D-19 — this number is not expected to reproduce the committed one bit-for-bit.** The PERS-05 fix changes WHICH SEEDS ARE DRAWN: the control used to seed from its own loop position and now seeds from each question's stamped index, so different completions come back. That is the DEFINITION of the defect, not a regression — Phase 14 never compared this arm against anything, so pairing was not in play there; Phase 16 does compare, which is why the fix is a prerequisite rather than polish. `results/phase14_recall_report.md` is deliberately NOT amended: the published number stays exactly as published, and the delta above is a REPORTED MEASUREMENT of the fix's impact rather than a silent assertion that it did not matter. It never fed a threshold — the gate stays anchored to the committed number, because re-anchoring it to a number this phase measured would be setting the gate after seeing data.

**Why both units are printed** (T-16-26). The draw-unit bound is roughly nine times tighter than the question-unit one. Citing the draw unit alone makes the prompt arm look far more definitively at zero than STAT-01's unit supports, and the ceiling if the floor had scored nothing at all would still be 0.013889 (rule of three at 216 questions).

## Proxy Validity (D-15)

The `(5, 30)` synthetic cell against the top rung: same prompt position, same span length, same denominator, same draw count — differing in MATERIAL (a gate-cleared synthetic string versus the real taught value). If they diverge badly, every low rung of this ladder is suspect and any reading built on those rungs must say so.

- synthetic `(5, 30)`: **0 of 216** answerable questions
- top rung (real values): **0 of 216** answerable questions
- difference: **+0** questions
- committed rule: DIVERGES when the two cells differ by at least 10 answerable questions out of 216 — the same integer LADDER_CELL_PASS_K sets for a cell to pass, so the synthetic substitution is called unfair exactly when it moves the count by as much as passing a rung does
- **VERDICT: `proxy_consistent`**

CAVEAT — these two cells also differ in FRAME, not only in material. `build_far_prompt`'s committed signature carries no fact id, so its persona line is ONE fact-agnostic sentence used for all eight facts, while the fairness control gives each fact its own first-person taught statement. For the name slot the two frames coincide; for the other seven the synthetic cell's persona names a different slot than the question asks about, which the control never does. The signature is locked, so this is reported as a limit on the comparison rather than repaired by changing it. It makes the two verdicts asymmetric: CONSISTENT is the stronger reading, because it holds despite the extra difference, while DIVERGES is ambiguous between the frame and the material and cannot separate them.

SECOND CAVEAT, added post-run at the human-verification checkpoint (additive commentary; no measured
number above was touched). **On THIS run the consistent verdict is DEGENERATE and carries almost no
information.** Both compared cells scored exactly `0 of 216`, so they agree trivially: a difference of
`+0` against a divergence threshold of 10 is what two dead cells produce whether or not the synthetic
substitution is fair. The check can only detect unfairness that MOVES the count, and at the floor
there is no movement available to detect — its power here is essentially nil. So `proxy_consistent`
above must NOT be read as evidence that the synthetic material is a validated stand-in for the real
taught values; it is the absence of evidence in either direction. A future reader — and plan 16-10's
report writer specifically — must not cite this verdict as validation of the low rungs. The check
would have been informative only if at least one of the two cells had scored off the floor.

## Monotonicity Anomalies

A harder rung passing while an easier one fails means the rungs are not ordered by the difficulty the grid claims, and every reading built on that order is suspect. Per D-14 an anomaly is NAMED here without stopping the run and without moving the licensed branch — this is the instrument-broken signal, and an all-fail ladder is not.

- **ANOMALY** — `(2, 2)` passed while the easier `(1, 2)` failed
- **ANOMALY** — `(2, 2)` passed while the easier `(1, 30)` failed

## Verdict

**Branch: `span_2`** — highest passed rung: `(2, 2)`.

HIGHEST PASSED RUNG: SPAN 2. LICENSED: the base can sustain a TWO-TOKEN in-context copy at that rung's distance. NOT LICENSED: the multi-token claim the comparison needs. The real taught values are longer than this rung and the longer-span rungs failed, so the prompt-stuffed arm remains below the capability required by the material it is scored on. Scope is exactly span two: this branch reports where the copy dies, it does not license reading the four-arm comparison as a mechanism comparison.

### The pre-registered licensing rule (D-14, verbatim)

> licensed_headline() ramifica no degrau mais alto aprovado, com threshold literal módulo-level commitado por célula antes da corrida (STAT-05). Ramo "nenhum degrau aprovado" licencia só o enunciado de déficit de capacidade do SC1. Violação de monotonicidade registrada como anomalia de instrumento no relatório, sem parar a corrida — mas nomeada explicitamente, não silenciada.
