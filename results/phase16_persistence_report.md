# Phase 16 — Weight vs Prompt Persistence, Four Arms (PERS-02 / PERS-03 / PERS-04 / STAT-01 / STAT-02 / STAT-06)

## Run Provenance

One block per condition process. D-01 splits this run into FOUR fresh processes, so four distinct pids below are what EVIDENCE the split rather than assert it.

### Condition `adapter-only` — its own process

- seed: 1337 (seed_everything before the load; every draw re-derivable from it)
- driver git_sha: dc9d6c1207a4f676f8e49a6a1e76974e9286a798
- pid: 16115 (PROCESS BOUNDARY — teaching ran in a different invocation)
- wall clock (UTC): 2026-08-14T01:21:10Z
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
- condition: adapter-only (ONE per process — D-01)
- condition wall clock: 10.6 min

### Condition `base-neither` — its own process

- seed: 1337 (seed_everything before the load; every draw re-derivable from it)
- driver git_sha: dc9d6c1207a4f676f8e49a6a1e76974e9286a798
- pid: 23448 (PROCESS BOUNDARY — teaching ran in a different invocation)
- wall clock (UTC): 2026-08-14T01:35:18Z
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
- condition: base-neither (ONE per process — D-01)
- condition wall clock: 13.8 min

### Condition `embedding-cosine` — its own process

- seed: 1337 (seed_everything before the load; every draw re-derivable from it)
- driver git_sha: dc9d6c1207a4f676f8e49a6a1e76974e9286a798
- pid: 26135 (PROCESS BOUNDARY — teaching ran in a different invocation)
- wall clock (UTC): 2026-08-14T01:35:29Z
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
- condition: embedding-cosine (ONE per process — D-01)
- condition wall clock: 0.2 min

### Condition `prompt-stuffed` — its own process

- seed: 1337 (seed_everything before the load; every draw re-derivable from it)
- driver git_sha: dc9d6c1207a4f676f8e49a6a1e76974e9286a798
- pid: 26193 (PROCESS BOUNDARY — teaching ran in a different invocation)
- wall clock (UTC): 2026-08-14T03:28:06Z
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
- condition: prompt-stuffed (ONE per process — D-01)
- condition wall clock: 112.6 min

### Report assembly (this process)

- report assembled from 4 arm records at /Users/juliorcoelho/PersonaCore/results
- arm git SHA (identical across all four): dc9d6c1207a4f676f8e49a6a1e76974e9286a798
- arm pids: [16115, 23448, 26135, 26193]

## What This Report Is

**What this report is.** The four-arm weight-versus-prompt comparison this phase exists to run, plus its descriptive interval, its one inferential gate and its pre-registered qualifiers. Every framing string below is a module-level constant in `scripts/phase16_persistence.py`, committed to git BEFORE the run that filled it; every number is interpolated from the run or formatted by a committed helper. A report whose text is written after the numbers is a report written to fit them.

**What it may not claim.** The headline is the CAPABILITY LADDER's own output, cited in `## Verdict` below, and this report may not claim more than that ladder licensed. **'Not demonstrable at n = 8' is a legitimate, pre-registered outcome recorded as-written**, exactly as Phase 12 recorded its own null. If the gate does not clear, that is the result — not a prompt to re-run, soften, or add an unplanned analysis.

Citable four-arm wall clock: **~39 min (realistically 35-44 min)**. The tighter single figure the intra-run interval would support is deliberately NOT quoted: arm A measured twice independently over the same 30 questions gave means 2.654 and 2.380 s per question, 11.5% apart, which exceeds that interval's own +-4% width. An interval that cannot contain a repeat of its own measurement understates real uncertainty and must never be quoted alone. The PERS-03 sweep's clock is reported separately and is much larger: 7 cells x 270 questions, ~100 min FLOOR to ~3 h, because there is no KV cache (D-04) and per-question cost grows with prompt length.

## Run Design

The run splits into FOUR fresh processes, one per condition, and questions run sequentially within a process. Not one process for all four arms: a single process would carry whatever the previous arm left in it across the arm boundary, which is the one boundary this comparison is about. And not one process per question, which would be 1,080 model loads for an isolation nothing needs — see NO_KV_CACHE_NOTE (there is no per-step state to survive a question) and SEQUENTIAL_QUESTIONS_JUSTIFICATION (the adapter toggle leaves no residue, proven at fixture scope AND on the real weights). The split is defence-in-depth at the arm boundary, not a repair for a leak anyone measured.

Questions run sequentially inside a condition's process because the adapter toggle leaves no residue, and that claim rests on TWO citations, not one. (1) FIXTURE scope: tests/test_lora_toggle.py:77 test_toggle_round_trip_bit_identity, :105 test_adapter_disabled_preserves_prior_state, :95 test_adapter_disabled_exception_safe — these run against a fixture model (scripts/phase14_recall.py:1341-1344 records the same scope limit), so on their own they prove the toggle's semantics and not the real model's behaviour. (2) REAL WEIGHTS: Phase 14 D-11.3, scripts/phase14_recall.py:1336 run_bit_identity_control, max |diff| 0.0 measured on the real 13.9M convbase with the real persona adapter. Both are required: the first establishes the mechanism, the second establishes that it holds on the weights this comparison actually runs.

No KV cache exists in this codebase. grep for cache|past_key|kv across src/personacore/generation/ and src/personacore/model/ returns zero hits, so the model recomputes the full forward at every decode step and there is no per-step state that could survive a question, let alone a condition. Cross-question and cross-condition cache residue is therefore structurally impossible rather than merely unobserved — which is why the four-process split is defence-in-depth and not the thing that makes the run valid.

**Condition order (D-03), pre-registered:** `('adapter-only', 'base-neither', 'embedding-cosine', 'prompt-stuffed')`.

Two reasons are recorded for this order, and exactly two. (1) Pre-registering the order prevents choosing it after seeing numbers. (2) 'adapter-only first' means the most critical result is already in hand under interruption. A third rationale was drafted for the last position and DELETED rather than annotated: it defended against a mechanism the four-process split already eliminates, and a false rationale left in an artifact is inherited downstream as true. It is not restorable from anything in this repository, which is deliberate. sob o split de quatro processos frescos, o resultado é invariante à ordem — a ordem é pré-registro puro, sem efeito físico sobre o resultado.

## Arm Parity (SC2 / PERS-02)

The four scalar columns are read off ONE `SHARED_ARM_CONFIG` object by identity, not compared as four literals that agree today; `assert_arm_parity` asserts that identity AND the equality of every column below before this report is assembled. `forbid_ids` is recorded by sha256 CONTENT hash because `undecodable_ids_mask` needs a loaded tokenizer and returns a device-resident tensor, so it can be neither an import-time constant nor meaningfully compared by identity across the four fresh processes D-01 requires.

| arm | `max_new_tokens` | `forbid_ids` (masked / sha256) | `stop_ids` | `context_length` | `n_draws` |
| --- | --- | --- | --- | --- | --- |
| `adapter-only` | 48 | 7645 of 8192 / `79b55770f4dcfa94…` | [8184, 8185] | 256 | 9 |
| `base-neither` | 48 | 7645 of 8192 / `79b55770f4dcfa94…` | [8184, 8185] | 256 | 9 |
| `embedding-cosine` | 48 | 7645 of 8192 / `79b55770f4dcfa94…` | [8184, 8185] | 256 | 9 (shared budget; this arm REALIZES 1 deterministic draw per question — D-22: manufacturing 9 draws by softmax-sampling the similarities would produce an interval measuring the chosen temperature rather than any real uncertainty) |
| `prompt-stuffed` | 48 | 7645 of 8192 / `79b55770f4dcfa94…` | [8184, 8185] | 256 | 9 |

## Per-Fact Results — the gated tier (`held-out`)

One row per fact per arm. Every rate carries BOTH denominators — questions (the STAT-01 unit) and draws (the raw count) — and a bound; a fact scoring nothing carries the rule-of-three ceiling as well, because a bare zero percentage states a certainty this sample does not have.

| fact | arm | answerable / questions | draws | bound |
| --- | --- | --- | --- | --- |
| `cand_cat_zibby` | `adapter-only` | 13 / 13 | 69 of 117 | Wilson upper 1.000000; rate 1.000000 |
| `cand_cat_zibby` | `base-neither` | 0 / 13 | 0 of 117 | Wilson upper 0.172267; rule of three 0.230769 |
| `cand_cat_zibby` | `embedding-cosine` | 0 / 13 | 0 of 13 | Wilson upper 0.172267; rule of three 0.230769 |
| `cand_cat_zibby` | `prompt-stuffed` | 0 / 13 | 0 of 117 | Wilson upper 0.172267; rule of three 0.230769 |
| `cand_dog_zorp` | `adapter-only` | 13 / 13 | 59 of 117 | Wilson upper 1.000000; rate 1.000000 |
| `cand_dog_zorp` | `base-neither` | 0 / 13 | 0 of 117 | Wilson upper 0.172267; rule of three 0.230769 |
| `cand_dog_zorp` | `embedding-cosine` | 0 / 13 | 0 of 13 | Wilson upper 0.172267; rule of three 0.230769 |
| `cand_dog_zorp` | `prompt-stuffed` | 0 / 13 | 0 of 117 | Wilson upper 0.172267; rule of three 0.230769 |
| `cand_house_7412` | `adapter-only` | 6 / 13 | 6 of 117 | Wilson upper 0.675180; rate 0.461538 |
| `cand_house_7412` | `base-neither` | 0 / 13 | 0 of 117 | Wilson upper 0.172267; rule of three 0.230769 |
| `cand_house_7412` | `embedding-cosine` | 0 / 13 | 0 of 13 | Wilson upper 0.172267; rule of three 0.230769 |
| `cand_house_7412` | `prompt-stuffed` | 0 / 13 | 0 of 117 | Wilson upper 0.172267; rule of three 0.230769 |
| `cand_person_quillon` | `adapter-only` | 10 / 13 | 23 of 117 | Wilson upper 0.903768; rate 0.769231 |
| `cand_person_quillon` | `base-neither` | 0 / 13 | 0 of 117 | Wilson upper 0.172267; rule of three 0.230769 |
| `cand_person_quillon` | `embedding-cosine` | 0 / 13 | 0 of 13 | Wilson upper 0.172267; rule of three 0.230769 |
| `cand_person_quillon` | `prompt-stuffed` | 0 / 13 | 0 of 117 | Wilson upper 0.172267; rule of three 0.230769 |
| `cand_sister_orsala` | `adapter-only` | 13 / 13 | 72 of 117 | Wilson upper 1.000000; rate 1.000000 |
| `cand_sister_orsala` | `base-neither` | 0 / 13 | 0 of 117 | Wilson upper 0.172267; rule of three 0.230769 |
| `cand_sister_orsala` | `embedding-cosine` | 0 / 13 | 0 of 13 | Wilson upper 0.172267; rule of three 0.230769 |
| `cand_sister_orsala` | `prompt-stuffed` | 0 / 13 | 0 of 117 | Wilson upper 0.172267; rule of three 0.230769 |
| `cand_street_marrowgate` | `adapter-only` | 12 / 13 | 37 of 117 | Wilson upper 0.982648; rate 0.923077 |
| `cand_street_marrowgate` | `base-neither` | 0 / 13 | 0 of 117 | Wilson upper 0.172267; rule of three 0.230769 |
| `cand_street_marrowgate` | `embedding-cosine` | 0 / 13 | 0 of 13 | Wilson upper 0.172267; rule of three 0.230769 |
| `cand_street_marrowgate` | `prompt-stuffed` | 0 / 13 | 0 of 117 | Wilson upper 0.172267; rule of three 0.230769 |
| `cand_town_brindlemoor` | `adapter-only` | 12 / 13 | 45 of 117 | Wilson upper 0.982648; rate 0.923077 |
| `cand_town_brindlemoor` | `base-neither` | 0 / 13 | 0 of 117 | Wilson upper 0.172267; rule of three 0.230769 |
| `cand_town_brindlemoor` | `embedding-cosine` | 0 / 13 | 0 of 13 | Wilson upper 0.172267; rule of three 0.230769 |
| `cand_town_brindlemoor` | `prompt-stuffed` | 0 / 13 | 0 of 117 | Wilson upper 0.172267; rule of three 0.230769 |
| `cand_year_1987` | `adapter-only` | 11 / 13 | 15 of 117 | Wilson upper 0.947710; rate 0.846154 |
| `cand_year_1987` | `base-neither` | 0 / 13 | 0 of 117 | Wilson upper 0.172267; rule of three 0.230769 |
| `cand_year_1987` | `embedding-cosine` | 0 / 13 | 0 of 13 | Wilson upper 0.172267; rule of three 0.230769 |
| `cand_year_1987` | `prompt-stuffed` | 0 / 13 | 0 of 117 | Wilson upper 0.172267; rule of three 0.230769 |

### Pooled per arm, with the phase's DESCRIPTIVE interval

`two_stage_cluster_percentile_bootstrap`, 10,000 resamples, seed 1337, alpha 0.05. Two stages: the 8 FACTS are resampled first, then that resampled fact's own QUESTIONS. A question-only bootstrap would be conditional on these exact 8 facts and therefore NARROWER than the fact-level sign test standing beside it — an interval claiming more than the gate it accompanies. The percentile method is biased and anti-conservative at small n, and n here is 8 facts; that is NAMED in the pre-registration rather than upgraded after the numbers landed.

| arm | pooled rate | two-stage cluster bootstrap 95% | Wilson upper (see label below) |
| --- | --- | --- | --- |
| `adapter-only` | 90/104 questions (rate 0.865385; 95% Wilson upper bound 0.911252; 936 draws) | (0.721154, 0.971154) | 0.911252 |
| `base-neither` | 0/104 questions (95% Wilson upper bound 0.025355; rule-of-three upper bound 0.028846; 936 draws) | (0.000000, 0.000000) | 0.025355 |
| `embedding-cosine` | 0/104 questions (95% Wilson upper bound 0.025355; rule-of-three upper bound 0.028846; 104 draws) | (0.000000, 0.000000) | 0.025355 |
| `prompt-stuffed` | 0/104 questions (95% Wilson upper bound 0.025355; rule-of-three upper bound 0.028846; 936 draws) | (0.000000, 0.000000) | 0.025355 |

**Wilson label (T-16-41).** one-sided 95% Wilson upper bound computed as if the questions were INDEPENDENT. They are not — questions cluster inside facts — so this width UNDERSTATES the real uncertainty. The DESCRIPTIVE interval for this phase is the two-stage cluster bootstrap (`cluster_bootstrap`); Wilson is reported alongside it, labelled, for comparability with every other rate in this milestone, and never as the phase's own width.

**The soft tier is not reported per fact here, and arm D could not be reported for it at all.** The soft tier feeds neither gated number (`phase14_recall.SOFT_TIER` names it excluded from the pre-registered gate) and it is outside the Holm family by construction. Arm D additionally CANNOT score it: the 20-value candidate pool contains no soft-tier values, so arm D returns nothing on that tier BY CONSTRUCTION — a property of the pool, not a measurement of the model. Passing that structural absence through `report_proportion` would dress it in a rule-of-three ceiling and it would read as a measured zero, so no arm-D soft-tier bound is printed anywhere in this report.

## The Inferential Gate (STAT-06 / D-09)

The exact paired sign test over all 2**8 = 256 sign partitions, Holm-corrected across EXACTLY the six pairs D-09 closes the family at. Ties count AGAINST the alternative and n stays 8 (D-08); the alternative's direction per pair was committed before the run (D-29). **Only 8/8 unanimity clears**: the achievable p at unanimity is 0.0078125 against a first-step alpha of 0.05/6, a margin of 6.7% relative — and a SEVENTH gated comparison would price that step at 0.0071429 and kill the headline arithmetically at every possible outcome, including perfect unanimity. That is why the taught replication and the PERS-03 sweep are descriptive by construction and enter nothing (STAT-06).

Family size m = 6; first-step alpha = 0.05 / 6 = 0.0083333.

| pair | declared alternative (D-29) | per-fact signs | exact p | alpha at step | rejected |
| --- | --- | --- | --- | --- | --- |
| `adapter-only` x `base-neither` | adapter-only exceeds base-neither | +1 +1 +1 +1 +1 +1 +1 +1 | 0.0078125 | 0.0083333 | YES |
| `adapter-only` x `embedding-cosine` | adapter-only exceeds embedding-cosine | +1 +1 +1 +1 +1 +1 +1 +1 | 0.0078125 | 0.0100000 | YES |
| `adapter-only` x `prompt-stuffed` | adapter-only exceeds prompt-stuffed | +1 +1 +1 +1 +1 +1 +1 +1 | 0.0078125 | 0.0125000 | YES |
| `base-neither` x `embedding-cosine` | base-neither exceeds embedding-cosine | +0 +0 +0 +0 +0 +0 +0 +0 | 1.0000000 | 0.0166667 | no |
| `base-neither` x `prompt-stuffed` | base-neither exceeds prompt-stuffed | +0 +0 +0 +0 +0 +0 +0 +0 | 1.0000000 | 0.0250000 | no |
| `embedding-cosine` x `prompt-stuffed` | embedding-cosine exceeds prompt-stuffed | +0 +0 +0 +0 +0 +0 +0 +0 | 1.0000000 | 0.0500000 | no |

## Taught Replication — OUTSIDE the Holm family (D-07)

> o resultado do tier taught nunca altera, reforça formalmente, nem substitui o veredito do tier held-out — é evidência corroborante reportada, não gate.

The same protocol on the taught tier, reported with NO alpha and NO rejection flags, because there is nothing here that may be read as a verdict. Gating both tiers would take the family from 6 to 12, alpha to 0.05/12, and 8/8 unanimity would then FAIL — the gate would be unclearable at every possible outcome.

| pair | per-fact signs | exact p (descriptive) |
| --- | --- | --- |
| `adapter-only` x `base-neither` | +1 +1 +1 +1 +1 +1 +1 +1 | 0.0078125 |
| `adapter-only` x `embedding-cosine` | +1 +1 +1 +1 +1 +1 +1 +1 | 0.0078125 |
| `adapter-only` x `prompt-stuffed` | +1 +1 +1 +1 +1 +1 +1 +1 | 0.0078125 |
| `base-neither` x `embedding-cosine` | +0 +0 +0 +0 +0 +0 +0 +0 | 1.0000000 |
| `base-neither` x `prompt-stuffed` | +0 +0 +0 +0 +0 +0 +0 +0 | 1.0000000 |
| `embedding-cosine` x `prompt-stuffed` | +0 +0 +0 +0 +0 +0 +0 +0 | 1.0000000 |

## The Arm-D Structural Floor (D-25) — pre-registered qualifier, verbatim

> os três pares envolvendo o braço D (cosine-proxy) operam sobre recuperação em conjunto fechado (8 candidatos, piso de acaso 0.125) contra geração de vocabulário aberto nos braços A/B/C (piso ~0.005 e ~0). Qualquer resultado onde D "vence" ou empata favoravelmente precisa ser lido à luz desse piso estrutural — não é evidência de capacidade equivalente, é consequência da tarefa ser mais fácil por construção. Isso NÃO invalida os pares com D nem os remove da família de Holm (margem intacta, 0.0078125 < 0.0083333) — só qualifica a interpretação de qualquer resultado favorável a D no relatório final.

**Numeric reconciliation, flagged rather than silent.** The verbatim qualifier above was written citing an EIGHT-candidate pool. The pool decision taken in the same round chose the committed 20-value lexicon `find_contradictions` already consumes (D-23), whose chance floor is **0.05** — and **0.05 is the number this report uses**, everywhere, in every computation. The qualifier holds in full at the chosen pool's floor: 0.05 is still an order of magnitude above arm B (~0.005) and arm C (~0), so a result where arm D wins or ties favourably remains a consequence of its task being easier by construction rather than evidence of equivalent capability. This does NOT invalidate the three pairs involving arm D and does NOT remove them from the Holm family — the margin is intact, 0.0078125 < 0.0083333 — it qualifies the INTERPRETATION of any arm-D-favourable result and nothing else.

Operative chance floor: **0.05** = 1 / 20, `_prove`d against the committed lexicon at every call of `candidate_pool()`.

## Context Pressure (PERS-03)

| arm | treatment | reason |
| --- | --- | --- |
| `adapter-only` | **proof** | PROOF, cited and not re-measured: `scripts/phase14_recall.py:1336 run_bit_identity_control` measured a max ABSOLUTE DIFFERENCE of exactly 0.0 between the adapter-off logits and the un-adapted base on the real 13.9M convbase with the real persona adapter. The weight arm's memory is not in the context window at all, so context pressure cannot reach it; an invariance PROOF is stronger evidence of that than any statistic, and re-measuring it under pressure would replace a proof with an estimate. |
| `base-neither` | **not_applicable** | NOT APPLICABLE: the fact is nowhere — not in the weights, not in the context window — so there is no context-borne memory for dilution, truncation or overwriting to act on. A swept cell here would report a rate that measured nothing while still looking measured. |
| `embedding-cosine` | **not_applicable** | NOT APPLICABLE: the fact lives in the closed candidate pool this arm retrieves over, and the pool is not the context window. Pressuring the prompt would leave the retrieval set untouched, so the cell would vary the one thing this arm does not read. |
| `prompt-stuffed` | **measured** | MEASURED: the only arm carrying the fact in the context window, which is the surface every SC5 pressure acts on. All six dilution cells and the overwrite cell run here and nowhere else (D-26). |

### The arm-B cells

ONE ordered dilution axis. Truncation is DERIVED from crossing `block_size` (256) and is never an independent knob (D-27): the recall prompt is 33 tokens bare and 46 with a 13-token persona span, so truncation cannot fire until dilution has already pushed the context past the window. A separately-built truncation cell would be the largest dilution cell under a second name, and this report would state one effect twice. The seventh row is the adversarial overwrite on its OWN axis at nominal length — six on-axis cells plus one off-axis cell, which is why the log shows seven runs.

Prompt lengths are printed as DISTRIBUTIONS, never as their target: the fixture's own questions run 14 / 28 / 63 tokens bare (min / median / max), so a cell's achieved length varies by question even at a fixed persona span.

| target | pressure | measured prompt tokens (min / median / max) | over `block_size` | statement head offset | statement cropped out of view | rate |
| --- | --- | --- | --- | --- | --- | --- |
| 46 | dilution | 26 / 43 / 88 | 0 of 270 | 1 | 0 of 270 | 0/270 questions (95% Wilson upper bound 0.009921; rule-of-three upper bound 0.011111; 2430 draws) |
| 96 | dilution | 77 / 90.5 / 124 | 0 of 270 | 1 | 0 of 270 | 0/270 questions (95% Wilson upper bound 0.009921; rule-of-three upper bound 0.011111; 2430 draws) |
| 160 | dilution | 141 / 155 / 192 | 0 of 270 | 1 | 0 of 270 | 0/270 questions (95% Wilson upper bound 0.009921; rule-of-three upper bound 0.011111; 2430 draws) |
| 224 | dilution | 203 / 219 / 256 | 0 of 270 | 1 | 0 of 270 | 0/270 questions (95% Wilson upper bound 0.009921; rule-of-three upper bound 0.011111; 2430 draws) |
| 320 | dilution + truncation | 300 / 314 / 349 | 270 of 270 | 1 | 270 of 270 | 0/270 questions (95% Wilson upper bound 0.009921; rule-of-three upper bound 0.011111; 2430 draws) |
| 448 | dilution + truncation | 426 / 443 / 480 | 270 of 270 | 1 | 270 of 270 | 0/270 questions (95% Wilson upper bound 0.009921; rule-of-three upper bound 0.011111; 2430 draws) |
| 46 | adversarial overwrite (own axis, nominal length) | 42 / 60 / 104 | 0 of 270 | 1 | 0 of 270 | 0/270 questions (95% Wilson upper bound 0.009921; rule-of-three upper bound 0.011111; 2430 draws) |

**All seven cells scored 0/270, and that is UNINFORMATIVE about context-pressure degradation specifically because there was no baseline signal to degrade.** The capability floor already established by the committed ladder means dilution and adversarial pressure had nothing to erode: the arm entered the sweep at zero and stayed there. This result does NOT support 'context pressure had no effect' — it supports only 'no measurable effect was observable given zero baseline recall.' The two readings are not interchangeable, and only the second one is what was measured. A sweep that could speak to PERS-03's question would need an arm that recovers the fact at the least-diluted cell, which this arm does not.

CAVEAT — `assert_value_in_prompt` PASSES on the truncated cells, and that pass must never be read as 'the value was in view'. `phase14_recall.run_fairness_control` asserts over the full `prompt_ids` it built, while `personacore/generation/core.py:65` feeds the model `idx[:, -bs:]` — the LAST `block_size` ids. On a cell whose prompt exceeds `block_size` the assertion is therefore checking a region the model never sees. That is not a defect in the assertion: it proves the value was PLACED, which is what the cell is built to do. The entire point of the crossing cells is that the placed value is then cropped away, and every such cell in the table above reports the statement's own token offset, so the crop is shown rather than assumed.

**All dilution is INSIDE the persona span, and there is no turns axis.** `build_recall_prompt` (`src/personacore/dialogue/serialize.py:92`) passes exactly ONE turn to `encode_dialogue`, and `PERSONA_CAP` is enforced only by `cap_persona` (`:115`), which `build_recall_prompt` never calls — so the cap does not bite on this route and the persona span reaches the largest cell's length directly. SC5 and PERS-03 were amended at `79fa01a` from 'dilution across turns' to 'dilution within the persona span' for exactly this reason; there is no turns axis for this run to be missing.

SC5's third pressure, on its OWN axis at nominal length — NOT a point on the dilution axis. A contradicting same-slot value is folded into the taught statement, AFTER the taught value, inside that same string. It is a STATEMENT, not a prompt: `phase14_recall.run_fairness_control` builds its own prompt from the `statements` map (`phase14_recall.py:1262-1264`) and accepts no prebuilt prompt, so a prompt builder for this cell would be dead code on this route. The competitor is drawn from the committed 20-value lexicon (`candidate_pool`, D-23) by a fixed rotation, never hand-picked. SLOT MATCHING IS NOT ATTEMPTED and that is recorded rather than repaired: the committed lexicon carries no slot partition, and inventing one would be exactly the editorial judgment D-23 chose that lexicon to avoid. The competitor is therefore a plausible same-lexicon alternative, which is the property `find_contradictions` already relies on, and not necessarily a same-slot one.

### Arm A — a PROOF, cited and not re-measured

PROOF, cited and not re-measured: `scripts/phase14_recall.py:1336 run_bit_identity_control` measured a max ABSOLUTE DIFFERENCE of exactly 0.0 between the adapter-off logits and the un-adapted base on the real 13.9M convbase with the real persona adapter. The weight arm's memory is not in the context window at all, so context pressure cannot reach it; an invariance PROOF is stronger evidence of that than any statistic, and re-measuring it under pressure would replace a proof with an estimate.

### Monotone degradation (D-28)

D-28's condition is met at the branch level: the committed ladder branch is `span_2`, so at least one rung passed and the prompt arm was not at the floor everywhere. **That is the whole of what is licensed, and the branch statement in `## Verdict` bounds it.** A monotone reading of the cells above describes the degradation of a capability the ladder LOCATED at that rung — not of this arm's ability to carry the real taught values, which are longer than the passing rung's span and on which every longer-span rung failed. Read the two together or neither.

## The Floor in Both Units (STAT-01 / T-16-26)

The committed floor stated in BOTH units, computed by `phase16_ladder.floor_in_both_units()` from the shared bounds. The draw-unit bound is roughly NINE TIMES tighter than the question-unit one, and citing the draw unit alone makes the prompt arm look far more definitively at zero than STAT-01's unit supports. Both are printed side by side, with the draw unit labelled as the one STAT-01 FORBIDS for inference, so the tighter number cannot quietly become the one that gets quoted (T-16-26).

Source: `results/phase14_recall_report.md:378 (Phase 14 Control 1, 1/1944 draws)`.

| unit | count | rate | one-sided 95% Wilson upper |
| --- | --- | --- | --- |
| draws — the unit STAT-01 FORBIDS for inference | 1 of 1944 | 0.000514 | 0.002302 |
| questions — the STAT-01 unit | 1 of 216 | 0.004630 | 0.020482 |

Rule-of-three ceiling at 216 questions had the floor scored nothing at all: 0.013889.

## Verdict

**Ladder branch: `span_2`** — highest passed rung: `(2, 2)`. Read from `results/phase16_ladder_report.md`, committed at `5a17920` BEFORE any arm of this comparison was scored (PERS-01 / PREREG-02), and rendered here as `licensed_headline()`'s own output rather than as prose written around this run's numbers.

HIGHEST PASSED RUNG: SPAN 2. LICENSED: the base can sustain a TWO-TOKEN in-context copy at that rung's distance. NOT LICENSED: the multi-token claim the comparison needs. The real taught values are longer than this rung and the longer-span rungs failed, so the prompt-stuffed arm remains below the capability required by the material it is scored on. Scope is exactly span two: this branch reports where the copy dies, it does not license reading the four-arm comparison as a mechanism comparison.

**This report does not cite the ladder's D-15 `proxy_consistent` verdict as validation of anything.** That check compared two cells which BOTH scored zero answerable questions out of 216, so they agree trivially: a difference of zero is what two dead cells produce whether or not the synthetic substitution was fair. The check can only detect unfairness that MOVES the count, and at the floor there is no movement to detect. The ladder's own report records this caveat; it is repeated here because the branch cited above and that verdict sit in the same artifact, and a reader following one could pick up the other as evidence it is not.

**This comparison alone does not distinguish two mechanisms, and does not claim to.** An adapter-over-prompt result here is consistent with BOTH (1) personalization genuinely living in the weights, and (2) prompt-stuffing being structurally incapable of recovering a span as long as the material it is scored on. The committed capability ladder measured the second directly: the synthetic, guessability-gate-cleared span-5 cells `(5, 2)` and `(5, 30)` each scored 0 answerable questions of 216, and the top rung on the REAL taught values scored 0 of 216, against real value token lengths of [4,4,4,5,5,6,8,8] (median 5). Because the synthetic values are gate-cleared, the base provably had no prior knowledge of them, so that zero is not about which strings were chosen — it is span length. The prompt arm's floor is therefore explained by measured incapacity at the length of its own material, independently of what the adapter does. Separating the two would require comparing the arms on material INSIDE the proven ceiling (~2 tokens); no such condition exists here, because the adapter was trained on the real 4-8 token values and building a 2-token adapter is a separate training run. That was checked before this run and found unavailable — so this qualification is an explicit decision, not an omission. What the result licenses is precise: AT THIS SCALE, weight-based memory achieves what prompting cannot. Whether it would still win where prompting is capable is NOT tested here, and a headline omitting that is measuring a capability deficit and calling it a mechanism win.

### The pre-registered gate outcome, as-written

3 of 6 pairs cleared their Holm step:

- `adapter-only` x `base-neither` — adapter-only exceeds base-neither; p = 0.0078125 < alpha 0.0083333
- `adapter-only` x `embedding-cosine` — adapter-only exceeds embedding-cosine; p = 0.0078125 < alpha 0.0100000
- `adapter-only` x `prompt-stuffed` — adapter-only exceeds prompt-stuffed; p = 0.0078125 < alpha 0.0125000
