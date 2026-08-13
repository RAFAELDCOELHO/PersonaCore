# Phase 16: Weight-vs-Prompt Persistence Control - Context

**Gathered:** 2026-08-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Measure what memory-in-weights buys over prompting as a paired number with a bound — four arms on
the same committed 270-question fixture, with the shared instrument's pairing defect fixed first
and the headline licensed by a capability ladder that runs *before* anything is scored.

Fixed by `ROADMAP.md` §Phase 16 (SC1-SC5, as amended 2026-08-12). Discussion clarified
implementation inside that boundary; it did not move it.

**Two ROADMAP amendments were applied during this discussion** (single isolated commit, dated
notes in place):

- **SC2**: `"in one process"` → `"four fresh processes, one per condition"`
- **SC5**: `"on both context-bearing arms"` → `"the prompt-stuffed arm alone"`

</domain>

<decisions>
## Implementation Decisions

### Run architecture & condition order

- **D-01:** **Four fresh processes, one per condition.** Questions run sequentially within a
  process inside a condition. Not one process for all arms; not one process per question (that
  would be 1,080 loads).
- **D-02:** The formal justification for sequential questions **must cite BOTH sources
  explicitly**, never implicitly: (1) `tests/test_lora_toggle.py:77`
  `test_toggle_round_trip_bit_identity`, `:105` `test_adapter_disabled_preserves_prior_state`,
  `:95` `test_adapter_disabled_exception_safe`; **and** (2) Phase 14 D-11.3
  `run_bit_identity_control`, max |diff| 0.0 on the real 13.9M convbase + real persona adapter.
  Both are required because the Phase 9 tests run on a **fixture** model
  (`scripts/phase14_recall.py:1341-1344`) — citing only Phase 9 would inherit a fixture-scope
  guarantee as a real-weights one.
- **D-03:** `CONDITION_ORDER` is **locked as a module-level constant, pre-registered before the
  run**: (1) adapter-only, (2) base-neither, (3) embedding-cosine, (4) prompt-stuffed. Recorded
  rationale is exactly two reasons — pre-registering the order prevents choosing it after seeing
  numbers, and "adapter-only first" means the most critical result is already in hand under
  interruption. Plus this sentence, **verbatim and required**:

  > "sob o split de quatro processos frescos, o resultado é invariante à ordem — a ordem é
  > pré-registro puro, sem efeito físico sobre o resultado."

  The originally-drafted rationale for prompt-stuffed-last ("isolates residual context-window
  risk") was **deleted, not annotated**: it defended against a mechanism the process split already
  eliminates, and a false rationale left in an artifact is inherited downstream as true.
- **D-04 [informational]:** **No KV cache exists.** `grep` for `cache|past_key|kv` across
  `src/personacore/generation/` and `src/personacore/model/` returns zero hits — the model
  recomputes the full forward each step, so cross-question and cross-condition cache residue is
  structurally impossible. This is *why* the process split is defence-in-depth rather than
  necessity.
- **D-05 [informational]:** The run is **not cost-constrained**. See Measured Facts below for the
  number and its honest precision.

### Per-fact denominator, tier, ties, and the Holm family

- **D-06:** **Per-fact statistic = `k/n` over that fact's questions × 9 draws.** This is *resolved
  by arithmetic, not chosen*: the fixture is perfectly balanced (every core fact has exactly 14
  `core_taught` + 13 `core_held_out` questions, 4 reserved, 9 draws each → 126 / 117 draws), so
  `sum(k)/sum(n)` equals `mean(k_i/9)` digit for digit. The choice affects only the **interval**,
  and STAT-01 already mandates resampling *questions*.
  Report the denominator both ways (questions for the interval, draws for the raw count).
  Descriptive interval = cluster bootstrap resampling questions within the fact; Wilson alongside,
  **labelled as the independence-assuming width**; `3/n` wherever successes are zero.
  Implementation: change the grouping key at `scripts/phase14_recall.py:838-843` from
  `record["split"]` to `fact_id` — the fixture already carries `fact_id` per question.
- **D-07:** **The gated tier is `core_held_out`, and it is the single formal verdict.** `taught`
  runs in parallel under the same protocol and is reported as a pre-registered replication,
  **explicitly outside the Holm family**. Pre-registration text, locked before any real run,
  **verbatim and not paraphrasable**:

  > "o resultado do tier taught nunca altera, reforça formalmente, nem substitui o veredito do
  > tier held-out — é evidência corroborante reportada, não gate."

  Why exactly one tier can be gated: D-10 forbids pooling taught with held-out, so each fact
  yields two numbers. Gating both takes the Holm family from 6 to 12, alpha drops to
  `0.05/12 = 0.0041667`, and 8/8 unanimity (`p = 0.0078125`) **fails** — the gate becomes
  unclearable at *any* outcome, including perfect unanimity in both tiers.
  Why held-out and not taught: `results/phase14_recall_report.md:54` — taught measures recall on
  template families the adapter trained on, where success is compatible with surface memorization;
  held-out is the tier that distinguishes an internalized fact from a memorized phrasing.
- **D-08:** **Ties count AGAINST the alternative; `n` is fixed at 8, always, pre-registered.**
  Never inflates significance, and the denominator is locked at pre-registration time (STAT-02).
  Discarding ties (the textbook rule) is rejected: one tie gives `n=7` where unanimity is
  `p = 0.015625 > 0.0083333` (unclearable), and — decisively — the prompt-stuffed × base-neither
  pair is expected to tie on nearly all 8 facts given Phase 14's committed `1/1944`, which would
  drop that pair to `n≈0` where the test is **undefined**, not merely unclearable, and the Holm
  family becomes ill-formed. Under "ties against", that pair becomes 0/8.

  > **CORRECTION 2026-08-12 (post-plan-check).** The original last sentence of D-08 claimed that
  > 0/8 gives `p = 1.0`. **That was wrong under a pure two-sided test**, where 0/8 is exactly as
  > extreme as 8/8: both give `p = 0.0078125`. As written, a pair on which *all eight facts tied*
  > would have entered the Holm family as a significant result — a false positive in the
  > over-claiming direction, which is the failure mode this milestone exists to prevent. Caught by
  > `gsd-plan-checker`, not by the discussion. Resolved by D-29 below; the numeric claims in D-09
  > and SC4 are unaffected.

- **D-29:** **The sign test is two-sided in MAGNITUDE and directional in ALTERNATIVE — and the
  direction is a pre-registered literal.** `sign_test_exact` returns the two-sided p when
  `positives > SIGN_TEST_N / 2`, and `1.0` otherwise. A module-level `SIGN_TEST_ALTERNATIVE`
  literal declares the expected direction of each of the 6 `HOLM_FAMILY_PAIRS` entries **before
  any run** — same blind pre-registration discipline that governs every other rule in this
  milestone. Without it the direction could be fixed after seeing the signs, which is precisely
  what STAT-05 exists to prevent, in the one phase whose entire product is a pre-registration.
  Consequences, all verified by enumeration over the 256 sign partitions:

  | outcome | value | effect |
  |---|---|---|
  | 8/8 in the declared direction | `0.0078125` | clears at `0.05/6 = 0.0083333` — **SC4 and D-09's 6.7% margin unchanged** |
  | 7/8 | `0.0703125` | fails, as before |
  | 0/8 (all tied, or all against) | `1.0` | fails — the hole this decision closes |

  No ROADMAP amendment is required: SC4's pinned `p = 0.007812` is the value this construction
  still produces. Tests must pin **both** failing directions — `[0]*8 → 1.0` and `[-1]*8 → 1.0` —
  so the direction filter cannot silently invert.
- **D-09:** **The Holm family is closed at exactly the 6 pairs**, `C(4,2)`, as SC4 already writes.
  Alpha at the first step is `0.05/6 = 0.0083333`; 8/8 unanimity on the exact two-sided sign test
  over all `2^8 = 256` sign partitions gives `p = 0.0078125`; margin `0.0005208`, **6.7%
  relative**. The margin is load-bearing: `m=7` gives `alpha = 0.0071429 < 0.0078125` and kills
  the headline. **Therefore nothing else in Phase 16 may be gated** — PERS-03 and the taught
  replication included, both descriptive by construction. This is STAT-06 with arithmetic behind
  it, not just principle.
  Verified by enumeration: `n=8 pos=8 → 0.0078125`; `n=8 pos=7 → 0.0703125`;
  `n=7 pos=7 → 0.0156250`. **Exactly one outcome clears: 8/8 with zero ties.** "Not demonstrable
  at n=8" remains a legitimate pre-registered outcome recorded as-written, exactly as Phase 12
  recorded `λ*=None`.
- **D-10 [informational]:** `DEGEN-2` — cited in an earlier verification note as a downstream dependency of the
  denominator decision — **does not exist in this repository.** Repo-wide `grep` (excluding
  `.git`/`.venv`) returns a single hit: that note itself. It is not in `REQUIREMENTS.md`, not in
  `ROADMAP.md`, not in code or tests. Recorded here so the dangling reference cannot resurface as
  a fact; **do not propagate it.**

### In-context capability ladder (PERS-01)

- **D-11:** **2-D grid: span length × distance.** Spans of 1 / 2 / 5 tokens × distances of ~2 /
  ~30 tokens to the `<|assistant|>` trigger = 6 cells, with the **natural-question framing held
  constant** in every cell.
  Why 2-D and not distance-only: the real values are 4-8 tokens over a 547-id near-character
  vocabulary, so span length is the primary suspect for where capability dies; a distance-only
  ladder would fail at every distance without distinguishing "cannot copy 5 tokens" from "cannot
  use context", and those license different headlines.
  Why the framing is fixed and natural: an instructed-copy rung ("repeat this: X") is out of
  distribution for a TinyStories+PersonaChat model, so its failure cannot separate incapacity from
  instruction-following failure — and therefore licenses nothing.
- **D-12:** **Synthetic strings in the new rungs**, token-length-matched to the real values and
  filtered through the already-validated guessability gate. **Mandatory guard:** a synthetic string
  that happens to be a word the base already knows would *inflate* the ladder and license a
  stronger headline than the data supports. This is the only risk the synthetic choice introduces,
  and the existing gate closes it.
- **D-13:** **The ladder's top rung is the fairness control, re-run POST-FIX** (~12 min, noise
  against the ~39 min run), with the delta against the committed number reported as a
  **measurement of PERS-05's impact** rather than a silent assertion that it did not matter.
  This *revises* the earlier decision to reuse Phase 14's number as-is; the revision is recorded,
  not overwritten. The two pieces of evidence that forced it are D-19 and the unit problem below.
  It remains pre-comparison, so PERS-01 is satisfied. **The top rung can never be arm B** — PERS-01
  requires the ladder recorded before any comparison is scored, so a top rung taken from the
  comparison would be circular.
- **D-14:** **`licensed_headline()` branches on the highest passed rung**, with a module-level
  literal threshold per cell committed before the run it judges (STAT-05), and the verdict computed
  by *importing* those constants, never retyping them in prose. Verbatim:

  > "licensed_headline() ramifica no degrau mais alto aprovado, com threshold literal módulo-level
  > commitado por célula antes da corrida (STAT-05). Ramo "nenhum degrau aprovado" licencia só o
  > enunciado de déficit de capacidade do SC1. Violação de monotonicidade registrada como anomalia
  > de instrumento no relatório, sem parar a corrida — mas nomeada explicitamente, não silenciada."

- **D-15:** **Free proxy-validity check, derived not chosen.** The `(span 5 tokens, distance ~30)`
  cell is the same configuration as the fairness control at the top of the ladder — same prompt
  position, same median span length — differing *only* in material: synthetic vs real taught value.
  Comparing them directly tests whether the synthetic substitution is a fair proxy. If they diverge
  badly, every low rung of the ladder is suspect. Cost: zero, both measurements already exist in
  the approved design.
- **D-16:** **Engineering note for the planner:** `scripts/phase14_factset_gate.py` exists but
  exposes only `main()` and private helpers (`_probe:87`, `_complete:73`, `_quote:111`,
  `assert_report_not_clobbered:116`). It has **no public API taking an arbitrary string**. ISO-01
  sets the precedent of *importing* this instrument rather than copying it; applying that precedent
  here requires widening the file's public surface — deliberately and visibly, in the same register
  as the PERS-06 guard widening. **Never copy the logic into a new script.**

### Instrument surgery (PERS-05 / PERS-06)

- **D-17:** **PERS-05, confirmed by reading:** `scripts/phase14_recall.py:1184` does
  `for index, item in enumerate(questions)` and passes that positional `index` straight into
  `draw_all(..., index)` at `:1193`. Fix: `item.seed_index`.
- **D-18:** **PERS-06's twin already exists inline, unnamed.** `phase14_recall.py:1188-1192`
  already runs `_prove(contains_value(tok.decode(prompt_ids), item.fact.value), ...)` inside
  `run_fairness_control`. The surgery is to **extract it as a named twin of
  `assert_no_value_in_prompt` (`:398`)**, which already has the target shape: takes `values` as a
  **parameter**, never a module-level constant (LAZY-IMPORT RULE), and checks at both levels
  (normalized string and contiguous id run). This is naming and symmetry, not a new assertion.
- **D-19:** **The fix changes which seeds are drawn**, so the number that code produced in Phase 14
  does not reproduce bit-for-bit afterwards. That is the definition of the defect, not a
  regression. Phase 14 never compared that arm against anything (PERS-05's own text says so), so
  pairing was not in play there; Phase 16 does compare, which is why the fix is a prerequisite and
  not polish.
- **D-20:** **Surgery placement is hybrid.** PERS-05 and the `assert_value_in_prompt` extraction
  land in `scripts/phase14_recall.py` — the **shared instrument** — because Phases 17 and 18 consume
  the same file and a fix that does not live there is a fix they do not inherit, which is literally
  the failure mode PERS-05 exists to prevent. The Phase 16 driver goes in its own file.
- **D-21:** **The AST guard widens in SCOPE, not just in list.** Verbatim:

  > "guarda AST varre scripts/*.py e src/ completos, allowlist explícita nomeada por
  > arquivo+função. Qualquer call site com persona= fora da allowlist falha a suíte imediatamente
  > — sem exceção por conveniência de arquivo novo."

  Current state: `tests/test_phase14_scoring.py::test_persona_argument_is_scoped_to_the_fairness_control`
  parses exactly one file (hard-coded in `_build_recall_prompt_call_sites`) and asserts hard
  equality `with_persona == ["run_fairness_control"]`. If it kept walking one file, a new Phase 17
  file with `persona=` would simply not be scanned and would pass in silence — leaving the guard
  technically green and substantively blind. **Widening is deliberate and visible; deletion is
  forbidden** (PERS-06, literal).

### Four-arm parity and the cosine arm (PERS-02 / PERS-04)

- **D-22:** **Arm D emits the argmax-cosine value AS TEXT**, scored by the **same
  `contains_value`** as the other three arms. The phase then has exactly one scorer, so silent
  divergence between arm scorers is structurally impossible rather than merely unlikely.
  Resolution: **1 deterministic draw per question, not 9** — per-fact rate becomes
  `hits/13 held-out questions` against `hits/117 draws` for A/B/C. Compatible with D-06 without
  adjustment: the sign test uses only the **ordering** between arms, never the magnitude of the
  denominator. Rejected: manufacturing 9 draws by softmax-sampling the similarities, whose interval
  would measure the chosen temperature rather than any real uncertainty.
- **D-23:** **Candidate pool = `LOCKED_VALUES ∪ {f.value for f in GATE_REJECTED_CANDIDATES}` = 20
  distinct values, chance floor 0.05.** Direct reuse of the lexicon `find_contradictions` already
  uses, with zero new editorial judgment — the codebase already makes this exact argument at
  `phase14_recall.py:325-338`: a competing value the detector must spot is precisely a plausible
  same-slot alternative, which is what every rejected candidate already is.
  (For contrast: 8 candidates → 0.125; 10 → 0.10.)
- **D-24:** **Embedding = final hidden state of the BASE model, adapter OFF, mean-pooled over the
  sequence.** One forward pass per question; the 20 candidate embeddings are computed once for the
  whole run. Verbatim: *"Adapter OFF é invariante estrutural, não opção — o braço D existe para ser
  o referencial sem memória-em-pesos."* Zero new dependencies (STAT-04).
- **D-25:** **Pre-registered qualifier on the three pairs involving arm D — must appear before any
  run.** User instruction, verbatim:

  > "os três pares envolvendo o braço D (cosine-proxy) operam sobre recuperação em conjunto
  > fechado (8 candidatos, piso de acaso 0.125) contra geração de vocabulário aberto nos braços
  > A/B/C (piso ~0.005 e ~0). Qualquer resultado onde D "vence" ou empata favoravelmente precisa
  > ser lido à luz desse piso estrutural — não é evidência de capacidade equivalente, é
  > consequência da tarefa ser mais fácil por construção. Isso NÃO invalida os pares com D nem os
  > remove da família de Holm (margem intacta, 0.0078125 < 0.0083333) — só qualifica a
  > interpretação de qualquer resultado favorável a D no relatório final."

  **Numeric reconciliation, flagged not silent:** that text cites 8 candidates / floor 0.125, but
  the pool decision taken in the same round chose the 20-value lexicon, whose floor is **0.05**.
  The qualifier holds in full with the floor of the pool actually chosen — still an order of
  magnitude above arm B (~0.005) and arm C (~0). **The number to use in the report is 0.05.**

### Context-pressure sweep (PERS-03)

- **D-26:** **The sweep runs on arm B only.** Arm A receives the invariance **proof**
  (`run_bit_identity_control`, max |diff| 0.0) — cited, not re-measured. Arms C and D are declared
  **not applicable in the report, with each one's reason stated** (C: the fact is nowhere; D: the
  fact lives in the candidate pool, which is not the context window), so the absence reads as a
  decision rather than an oversight.
- **D-27:** **Truncation and dilution are not independent knobs.** Measured: the prompt is 33 tokens
  bare and 46 with a persona span, against `block_size=256`. Truncation at 256 **does not bite** on
  the nominal prompt — it only exists once dilution pushes the context past 256 tokens. SC5 lists
  the three pressures as if parallel. The planner must design the sweep with this dependency
  explicit, or the truncation cell measures exactly what the highest dilution cell measures and the
  report states one effect twice under two names.
- **D-28:** Monotone prompt-arm degradation is claimed **only if** the capability ladder got that
  arm off the floor (SC5, unchanged).

### Claude's Discretion

Nothing was delegated wholesale. The planner retains normal latitude on: exact bootstrap
resample count, report table layout and column order, the filler text used to build synthetic
spans, file/function naming in the new Phase 16 driver, and the dilution step sizes inside the
constraint D-27 imposes.

</decisions>

<specifics>
## Measured Facts (produced during this discussion — cite these, do not re-derive)

**Instrument, measured on the real `convbase_slim` + `persona_adapter`, `device=mps`, torch 2.7.1:**

| Fact | Value |
|---|---|
| Decodable token ids | **547 of 8192** (7,645 masked as `forbid_ids`) |
| Usable-vocab composition (bytes) | 1B=256, 2B=63, 3B=74, 4B=55, 5B=55, 6B=21, 7B=12, 8B=2, 9B=1 |
| Model | `n_layer=6`, `n_head=6`, `n_embd=384`, `block_size=256` |
| Locked value token lengths | `[4,4,4,5,5,6,8,8]` (median 5); soft `[6,6]` |
| Prompt length | bare 33 tokens; with a 13-token persona span 46 tokens |

Consequence: reproducing a value is **not** single-token copying — it is a 4-8 token sequence copy
over a near-character-level vocabulary in a 6-layer model. That is sustained induction, materially
harder than the "distance ~2" intuition suggests, and it is why span length entered the ladder.

**Wall-clock, n=30 per arm, one process, stride-9 deterministic sample (tiers 13/11/6):**

| Arm | median | min/max | spread | mean | sd |
|---|---|---|---|---|---|
| A adapter-only | 2.181 | 1.518/4.575 | 3.01× | 2.380 | 0.732 |
| B prompt-stuffed | 3.183 | 2.162/4.025 | 1.86× | 3.219 | 0.459 |
| C base-neither | 3.185 | 2.390/4.017 | 1.68× | 3.106 | 0.408 |
| D cosine (one forward pass) | 0.009 | 0.008/0.012 | 1.42× | 0.009 | 0.001 |

**Citable total: ~39 min, realistically 35-44 min.** Do **not** quote "39.2 min" — arm A measured
twice independently over the same 30 questions gave means 2.654 vs 2.380 (11.5% apart), which
exceeds the intra-run 95% CI (±4%), so the intra-run interval understates real uncertainty and must
never be quoted alone.

**A falsified prediction, recorded as an error rather than silently corrected:** arm C
(base-neither) was predicted *faster* than A because it skips the LoRA matmuls. It is **30%
slower** (3.106 vs 2.380). The cause is decode-step count, not per-step cost — the adapted model
hits `STOP_IDS` early because it answers and stops, while the base rambles to the 48-token cap.
**Run cost is governed by when each arm stops, not by how much compute each step does.**

**Phase 14 per-fact adapter rates, extracted from the committed report tables** (sums reproduce the
published 496/1008 taught and 326/936 held-out):

```
fact                     taught          held-out
cand_sister_orsala      102/126 0.810     72/117 0.615
cand_cat_zibby           94/126 0.746     69/117 0.590
cand_dog_zorp            81/126 0.643     59/117 0.504
cand_street_marrowgate   65/126 0.516     37/117 0.316
cand_person_quillon      64/126 0.508     23/117 0.197
cand_town_brindlemoor    57/126 0.452     45/117 0.385
cand_year_1987           18/126 0.143     15/117 0.128
cand_house_7412          15/126 0.119      6/117 0.051
zero-rate facts: NONE, in either tier
```

Consequence: for the headline pair (A adapter × B prompt) **zero ties are expected and 8/8 is the
predicted outcome**. Tie risk lives entirely in the floor pairs.

**The unit problem in the number Phase 16 inherits** (computed with the repo's own stdlib
`erasure_gate.wilson_upper_bound:139` / `rule_of_three:161`, zero new dependencies):

```
1/1944 = 0.000514   Wilson upper 95% = 0.002302   <- draws: the unit STAT-01 FORBIDS
1/216  = 0.004630   Wilson upper 95% = 0.020482   <- questions: the STAT-01 unit
rule_of_three(216) = 0.013889                     <- the ceiling if it were 0/216
```

**Nine times** the difference in the upper bound. Citing "1/1944" makes the prompt arm look far
more definitively at zero than the legal unit supports. `run_fairness_control` already computes the
correct numerator — `n_answerable` at `:1219`.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and requirements
- `.planning/ROADMAP.md` §Phase 16 — goal, SC1-SC5. **SC2 and SC5 were amended 2026-08-12**; read
  the amended text with its dated notes, not any cached version.
- `.planning/REQUIREMENTS.md` — STAT-01..06, PERS-01..06, PREREG-01/02, and the Out-of-Scope list
  (notably: PERS-04 is embedding + cosine only — no index, no re-ranking, no chunking).

### The binding fixture
- `results/phase16_recall_sample.json` — the **BINDING** 270-question fixture (112 core taught /
  104 core held-out / 54 soft; 8 core facts; 40 reserved D-08 probes). Every core fact carries
  exactly 14 taught + 13 held-out + 4 reserved. Phases 17 and 18 MUST consume it unchanged.
- `tests/test_phase16_fixture_regen.py` — pins the fixture against `build_question_sets` and the
  Phase 14 transcripts.

### The shared instrument
- `scripts/phase14_recall.py:1147` `run_fairness_control` — holds the PERS-05 defect at `:1184`
  and the unnamed `assert_value_in_prompt` at `:1188-1192`.
- `scripts/phase14_recall.py:398` `assert_no_value_in_prompt` — the shape the PERS-06 twin mirrors.
- `scripts/phase14_recall.py:315-322` `score_question`, `:838-850` tier aggregation — the grouping
  key D-06 changes.
- `scripts/phase14_recall.py:152,542` — `N_SEEDED_SAMPLES=8` + 1 greedy = 9 draws; per-draw
  `torch.Generator`, no module-level RNG.
- `scripts/phase14_recall.py:1336` `run_bit_identity_control` — the real-weights bit-identity
  proof, max |diff| 0.0.
- `scripts/phase14_recall.py:622-625` — Phase 14's decision *against* per-question subprocesses
  (argued about questions, never about arms).
- `src/personacore/dialogue/serialize.py:92` `build_recall_prompt` — single source of truth for the
  recall prompt (harness and demo both import it); `PERSONA_CAP = 140` at `:21`.
- `src/personacore/generation/text.py:31` `undecodable_ids_mask` — the 547-of-8192 fact.
- `src/personacore/lora/inject.py:109` `set_adapter_enabled`, `:133` `adapter_disabled`.

### Instrument integrity
- `tests/test_phase14_scoring.py:425` — the `persona=` AST guard PERS-06 widens rather than deletes.
- `tests/test_lora_toggle.py:77,95,105` — the Phase 9 toggle no-residue proofs (**FIXTURE scope** —
  see D-02).
- `scripts/phase14_factset_gate.py` — the guessability + tokenizer-census instrument. Import, never
  copy (ISO-01 precedent); see D-16 on its missing public API.

### Pre-registration and prior numbers
- `scripts/erasure_gate.py` — PREREG-01 at `23a830c`; stdlib-only `wilson_upper_bound:139`,
  `rule_of_three:161`. **Reuse these; adding scipy is forbidden (STAT-04).**
- `results/phase14_recall_report.md:54` (why held-out is the discriminating tier), `:58-59`
  (496/1008 taught, 326/936 held-out), `:364-378` (Control 1 — the fairness control and 1/1944),
  and the per-question `k/N` tables at `:66-289`.
- `.planning/milestones/v2.0-phases/14-teach-then-recall-demo/14-CONTEXT.md` — D-16 clean-room
  process boundary, D-12 gate-miss policy, D-17/D-18 structural-enforcement register.

### Full decision provenance
- `.planning/phases/16-weight-vs-prompt-persistence-control/16-DISCUSS-CHECKPOINT.json` — 31
  decision entries across 6 areas, including every option that was presented and rejected, the
  retracted n=3 cost estimate, and the revision trail for D-13.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `erasure_gate.wilson_upper_bound` / `rule_of_three` — stdlib-only, already committed. Every bound
  STAT-02 requires can come from here; no new statistics dependency is needed or permitted.
- `find_contradictions`' lexicon (`LOCKED_VALUES | {f.value for f in GATE_REJECTED_CANDIDATES}`) —
  becomes arm D's candidate pool verbatim (D-23), with the reuse argument already written in the
  codebase.
- `adapter_disabled` context manager — carries the no-residue proofs D-02 cites; arms B, C and D
  all run inside it.
- The tier aggregation at `:838-850` — the per-fact statistic is the *same two lines* with a
  different grouping key.
- `run_fairness_control`'s `n_answerable` (`:1219`) — the STAT-01-legal numerator already exists.

### Established Patterns
- **LAZY-IMPORT RULE:** `import phase14_factset` belongs only inside functions. Locked fact strings
  must never reach module import time (`test_no_fact_strings_at_import` scans docstrings too).
- **Gates are module-level literals in a committed driver, pushed before the run they judge**
  (STAT-05); verdicts are computed by *importing* those constants, never retyping them in prose.
- **Structural enforcement over convention:** invariants get a test that parses the source, not a
  comment. The recurring defect this project names is "a declared invariant silently becomes false".
- **Zero new runtime dependencies:** `pyproject.toml` must be byte-identical at v3.0 close; scipy
  has been declined twice in committed code.

### Integration Points
- New Phase 16 driver imports `phase14_recall` (loader, `draw_all`, `score_question`,
  `contains_value`) and `serialize.build_recall_prompt`; it does not re-implement any of them.
- The widened AST guard in `tests/test_phase14_scoring.py` must scan the new driver file — that is
  the point of widening the scope rather than the allowlist (D-21).
- `preflight_device(strict=True)` then `RuntimeConfig().device` is the harness's own two-line device
  resolution (`phase14_recall.py:1049-1051`); `preflight_device` returns a summary dict, **not** a
  device.

</code_context>

<deferred>
## Deferred Ideas

- **Widening `phase14_factset_gate.py`'s public API** (D-16) is required by this phase but is a
  cross-phase instrument change; Phase 17's ISO-01 depends on the same import path. Plan it as a
  deliberate, visible widening here so Phase 17 inherits it.
- **DEMO-F2 (prompt-vs-weight recall parity)** stays deferred as Phase 14 declared. Phase 16
  measures the four-arm comparison under its own pre-registration; it is not DEMO-F2 arriving late.

</deferred>

---

*Phase: 16-weight-vs-prompt-persistence-control*
*Context gathered: 2026-08-12*
