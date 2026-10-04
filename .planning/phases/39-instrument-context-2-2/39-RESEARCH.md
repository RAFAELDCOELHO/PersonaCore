# Phase 39: Instrument × Context 2×2 (E6) - Research

**Researched:** 2026-10-04
**Domain:** pre-registered measurement driver over committed adapters (PyTorch MPS inference, NLL/rank + seeded generation), Phase 35/36/38 governance rails
**Confidence:** HIGH for code paths, reuse and censuses (every claim below was measured in this session, with file:line). MEDIUM for the decomposition-rule details that CONTEXT leaves open. Those are listed under Open Questions and need Rafael's ruling before the prereg freezes.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

Decided by Rafael in discuss-phase 39 (2026-10-04), except where marked as carried forward.

#### Carried forward (not re-asked)
- **D-01 (CTX-01, entry subset):** all 216 A2 entries (27 questions x 8 slots,
  `phase35_prereg.a2_corpus_entries()`), no subset — the budget approval ("E6 com
  a2_regenerated_entries = 0 e entries = 216") and `unit_caps.E6.entries = 216`. If any entry has to
  leave, STOP and tell Rafael which and why. Filled via `phase35_prereg.fill("e6_entry_subset", ...)`
  (input_records `results/phase36_probe_*.json`).
- **D-02 (context (b) generation is not regenerated):** reuse the 7 committed K = 48 A2 records, each
  verified by SHA-256 against `results/phase36_budget.json` cap_rulings["E6.a2_regenerated_entries"]
  (k0 phase18_arm_adapter-on; k8/16/32/64 erasure_kstar_arm_k0NN; k78 phase19_arm_erased; M2
  phase19_arm_retrain); `check_unit_caps("E6", a2_regenerated_entries=0)`. Anything that would need
  regeneration pauses for Rafael.
- **D-03 (process):** phase-owned prereg + ancestry test committed before any `results/phase39_*`;
  fills `e6_entry_subset` and `e6_decomposition_rule` (Phase 35 slots, owner 39); records write-once,
  each committed alone after Rafael's approved; MPS under the milestone ledger with
  `phase36_ledger.require_launch("E6")`; committed stop (a) = 1.5 x front_hours.E6, no second rule.

#### Anchor generation — context (a)
- **D-04 (prompt):** byte for byte the context under which `exposure_rank` scores the slot's taught
  value (`phase18_extraction.value_span_nll` anchor, frame `ans1`). No new prompt.
- **D-05 (sampling):** exactly the A2 parameters — temperature 0.8, top-p 0.95
  (`phase14_recall.SAMPLE_TEMPERATURE` / `SAMPLE_TOP_P`), draw 0 greedy, `RECALL_MAX_NEW_TOKENS` = 48,
  the same `forbid_ids` mask and the A2 seed convention; K = 48. (Rafael's answer said "top-k"; his rule
  "the same parameters as A2" resolves to top-p, measured in the code.)
- **D-06 (hit):** the A2 hit function unchanged (`phase18_extraction.score_records` /
  `aggregate_questions`, as `phase19_erasure.per_fact_rows` drives them).
- **D-07 (common unit):** "some hit in 48 draws". Anchor: 1 unit per slot; A2: 27 units per slot (one
  per question). Beside it, the per-draw rate in both contexts (h/48 and total/1296) with a Wilson
  interval. The 1-vs-27 asymmetry is declared in the report.
- **D-08:** the record keeps every anchor draw, so the hit is re-derivable on CPU.

#### Rank with the full question — context (b)
- **D-09 (reference sets):** the committed sets (|R| 6-8, `phase18_extraction.reference_set_for`) — the
  main reading, as the budget priced (`e5_candidates_per_slot_max` = 8).
- **D-10 (aggregation):** one rank per question (27 per slot x adapter). Summary per slot x adapter: the
  number of the 27 questions with rank 1, and the median rank. Beside it, descriptive: the rank of the
  mean NLL.
- **D-11 (descriptive extras, Rafael's approval — quote verbatim in the prereg and every record):**
  "Opção 1: aprovo (i) adaptador desligado como oitavo adaptador e (ii) os conjuntos cunhados da Fase 38
  sob a pergunta inteira em |R| = 8 (D-09). approved"
  - (i) adapter-off as an 8th adapter; its A2 context reused from the committed
    `results/phase18_arm_adapter-off.json` (k = 48, seed 1337, 976 draws) by SHA-256; anchor generation
    and both NLL readings run for it.
  - (ii) Phase 38's minted sets (`results/phase38_minting.json`) under the full question at |R| = 8 only
    (the taught value + the first 7 cleared values per slot).
  - Both descriptive, never criteria, never inside the decomposition classes.
  - Priced at the committed high unit prices (the E6 formula reproduces front_hours.E6 =
    0.4949481154825642 exactly): (i) +0.0707 h, (ii) +0.137 h (10,584 NLLs); E6 projection 0.703 h <=
    committed stop (a) 0.742 h. As in Phase 38 D-21..D-23: the approval and the projection live in the
    prereg; ledger, budget, phase36_ledger.py and phase36_caps.py untouched; caps are checked against the
    approved values without passing the raised counts to check_unit_caps; no second stop rule.
- **D-12 (|R| > 8, addendum — nothing run):** the minted-set reading under the full question at |R| > 8
  is NOT part of E6 and is recorded as not measured. If run later, it uses Phase 38's nested sizes (32,
  128, 512; birth_year 220), the same definitions and the same decomposition rule; the decision depends
  only on the hours left after E1-E4 and is recorded as a dated continuation labelled as after E6.
  (Priced for reference at the high prices: up to 32 +0.609 h, 128 +2.493 h, 512 +9.315 h.)

#### Decomposition rule — `e6_decomposition_rule`, frozen before any record
- **D-13 (four readings per slot x adapter):** R_a (anchor rank — committed, the ranks Phase 38's gate
  reproduced), R_q (rank with the question, D-10), G_a (anchor generation, D-04..D-07), G_q (A2
  generation, committed K = 48).
- **D-14 ("signal lost"):** rank: rank > 1 (published criterion). Generation: two events, as in Phase 38
  — collapse (no unit with a hit) and damage (drop above the published margin relative to k = 0 of the
  same context, by the committed formula pre/n - post/n; margin = `phase38_prereg.MARGIN`).
- **D-15 (disagreement):** published disagreement = R_a intact and G_q lost. For each such cell:
  CONTEXT_SUFFICIENT if R_q lost and G_a intact; INSTRUMENT_SUFFICIENT if G_a lost and R_q intact; EITHER
  if both lost; INTERACTION_ONLY if neither lost. Without disagreement: NO_DISAGREEMENT. The WR-01
  outcomes (ALREADY_AT_K0, UNREACHABLE_AT_SIZE) and the k = 0 rules apply here too.
- **D-16:** the classification is given for collapse and for damage separately.
- **D-17 (descriptive, never a criterion):** in each context, the hit rate predicted by the value's NLL
  (exp(-total NLL)) beside the observed one, with the caveat that temperature, top-p and the hit rule
  separate the two.

#### Gate and run shape — Phase 38's pattern with these differences
- **D-18 (gate 1):** reproduce the committed anchor ranks (the 7 adapters x 8 slots Phase 38's gate
  reproduced, plus adapter-off's committed ranks) before any new scoring; any mismatch STOPs.
- **D-19 (gate 2):** re-derive on CPU the committed A2 counts from the committed draws (SHA-256 checked)
  before using them; nothing is regenerated.
- **D-20 (CPU cross-check):** NLL and rank only. Generation is seeded per device, so there is no draw
  cross-check; declared in the report.
- **D-21 (run):** one MPS run under the ledger, the committed budget stop rule, a rehearsal on a declared
  slice disclosed in the report (Phase 38 D-34 pattern).
- **D-22 (declared limitations):** one seed, one target, |R| 6-8 in the main reading; the 1-vs-27 unit
  asymmetry (D-07); no generation cross-check (D-20).

### Claude's Discretion
- Module and record names under `results/phase39_*` (V6_RESULT_PATHS member), driver structure, test
  layout, and the order of plans — following the Phase 38 split (prereg, review, run, records, report).

### Deferred Ideas (OUT OF SCOPE)
- Minted-set reading under the full question at |R| > 8 (32, 128, 512; birth_year 220) — recorded as not
  measured in E6 (D-12); may run later as a dated continuation after E1-E4, labelled as after E6.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CTX-01 | Which of the 216 A2 corpus entries enter the full-context NLL is pre-registered before any scoring | `E6_ENTRY_SUBSET = phase35_prereg.fill("e6_entry_subset", entry_indices=tuple(range(216)), input_records=("results/phase36_probe_e1.json", "results/phase36_probe_e6.json"), derivation=...)` in `scripts/phase39_prereg.py` (M5, Pattern 1). Ordering leg (a) puts it before every `results/phase39_*` (M11). The caps owner scan reads it as `entries=216 <= unit_caps.E6.entries=216` (M12). |
| CTX-02 | On k = 0, 8, 16, 32, 64, 78 and M2: NLL and rank at (a) the anchor and (b) the full A2 question; generation in both contexts | (a) NLL and rank = gate 1 (64 committed ranks, `phase38_prereg.committed_gate_ranks`). (a) generation = new anchor loop on `phase36_probe.stage_e6`'s exact ids and seed rule (M3/M4). (b) NLL = `phase18_extraction.span_nll_from_ids` over `_guarded_span(entry)` ids (M7, Open Q1). (b) generation = the 8 committed records, SHA-verified (M1) and re-derived on CPU, 0 mismatches (M2). |
| CTX-03 | The report separates the instrument share and the context share of the disagreement | Frozen per-cell classifier over (R_a, R_q, G_a, G_q) for collapse and damage (D-13..D-16). Measured on committed data: the published disagreement is 24 cells under damage and 12 under collapse (M9). Class counts are always published with their denominators. |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Python 3.11 venv (`.venv`, measured 3.11.15) and torch 2.7.1. Never validate against the system Python 3.14.
- Primary device: MPS in fp32. No AMP, no `torch.compile`. CPU is used for tests, the cross-check and the rehearsal.
- No HF/PEFT model code. Instruments are imported from the pinned modules, never reimplemented.
- Offline only (no wandb or network). Checkpoints stay gitignored (`checkpoints/`, `data/`, `*.pt`).
- GSD workflow. STATE/ROADMAP/REQUIREMENTS are edited **by hand**, never through `gsd-sdk` `state.*` / `roadmap.*` / `phase.*` mutation handlers (they corrupted planning files in thirteen consecutive sessions).
- Records are write-once and each is committed alone after Rafael writes "approved". Corrections are dated continuations (`scripts/_addendum.py`), never edits.
- `make test` needs the `[cpu,dev,demo]` extras (`tests/test_phase14_demo.py` imports gradio).
- Evidence before numbers: no figure enters an artifact without raw per-item logs, a denominator and a bound.

## Summary

Phase 39 is Phase 38's driver pattern without the minting stage, plus two new measurements. The first is anchor-context generation: K = 48 seeded draws per slot per adapter at the `ans1` anchor. The second is value-span NLL/rank under each of the 216 A2 questions. Everything else is reuse:

- **Gate 1** is exactly Phase 38's D-18 gate: the same 8 readings (`phase38_prereg.READINGS` = k0, k8, k16, k32, k64, k78, M2, adapter_off) × 8 slots = 64 committed ranks, read by `phase38_prereg.committed_gate_ranks()`.
- **Gate 2** is `phase19_run._pooled_rows` over each committed draw record. Measured this session: it reproduces every committed A2 count with **0 mismatches** across all 8 readings × 8 slots.
- All **eight A2 records match their pinned SHA-256**: seven from `cap_rulings`, plus adapter-off at `08fe96fb…`.

No existing function scores a value's NLL under the full question prompt. The primitive is public, though: `phase18_extraction.span_nll_from_ids(model, context_ids, value_ids, device)` at :1050. `phase18_extraction._guarded_span(entry)` at :3014 returns the A2 prompt's question portion (the prompt minus its injected value prefix, always ending at `<|assistant|>` = 8186). Building the context-(b) NLL is about 10 lines of new code.

The main thing the planner must surface is that **"the full A2 question" is not byte-defined in CONTEXT**. Measured: the "with injected prefix" reading is infeasible for the reference sets (one pet_name reference encodes to 3 ids, so `split_value_ids` refuses it). The literal "question prompt, whole value" reading also differs from the anchor in two ways at once: it adds the question and drops the `ans1` preamble. This, the R_q "lost" aggregate, and the WR-01 mapping for per-cell classes must be ruled before `scripts/phase39_prereg.py` freezes (Open Questions 1-3).

The ordering is simpler than Phase 38's, with one new hazard. Both E6 slots are "free": neither has a phase-39 input. So one fill file, `scripts/phase39_prereg.py`, holds both and must precede every `results/phase39_*`. But **no record freezes the prereg before the CPU rehearsal**. Phase 38's minting record did that job, and here nothing does. Unless the plan pins it, the decomposition rule can be edited after the rehearsal has read a real slice (Pitfall 1, Open Q5).

**Primary recommendation:** build `scripts/phase39_prereg.py` (two fills, the D-11 approval and E6 arithmetic, the frozen decomposition functions, gate-2 re-derivation) and `scripts/phase39_ctx.py`. The driver should import `phase38_prereg` (READINGS, committed_gate_ranks, rank_in_prefix, MARGIN), `phase38_rank` (reconstruction_checks, gate_reading, m2_adapter_path), `phase36_probe.adapted_model`, and the pinned instruments, and copy only the run/emit/report skeleton. Take Open Questions 1-5 to Rafael at plan time, as Phase 38 did with D-24..D-32.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Entry subset + decomposition rule (CTX-01/03) | Pre-registration module (`scripts/phase39_prereg.py`, CPU, import-time `_prove`s) | Phase 35 registry (`fill`) | Must exist and be frozen before any record. The slot census only accepts fills in `scripts/phase39_*prereg.py` |
| Approval + projection arithmetic (D-11) | Pre-registration module | `results/phase36_budget.json` (read-only) | The Phase 38 D-22 precedent. Ledger, budget and caps stay untouched |
| Gate 2 (A2 counts from committed draws) | Pure CPU function in the prereg | Driver preflight (refusal before the ledger start) | Needs no model. 1.8 s CPU measured |
| Gate 1, anchor generation, context-(b) NLL | Driver `run` on MPS under the ledger | `phase36_probe.adapted_model`, `phase14_recall.load_adapted_model` | Model-bearing work. One ledger attempt (D-21) |
| CPU cross-check (NLL/rank only) | Driver `crosscheck` on CPU | — | D-20. No ledger line (Phase 38 precedent) |
| Classification, shares, report | Driver `emit` / `render_report`, pure, from sidecars + frozen prereg functions | — | The record is computed only through frozen definitions. The report renders from the committed record alone |
| Persistence | `results/phase39_*` (tracked, write-once) | `data/phase39_*` sidecars (gitignored) | The Phase 38 pattern: crash-safe sidecars, one record |

## Standard Stack

No new dependency. Every library is already installed and pinned.

### Core (already in `.venv`)
| Library | Version (measured) | Purpose |
|---------|---------|---------|
| Python | 3.11.15 | Runtime |
| torch | 2.7.1 (`torch.backends.mps.is_available()` → True on this M3) | Models, MPS run, CPU cross-check |
| pytest | 9.0.3 (note: not the 8.x CLAUDE.md lists) | Tests |

### Repo modules to IMPORT (never edit; most are byte-pinned by committed records)
| Module / symbol | file:line (verified) | Use in Phase 39 |
|---|---|---|
| `phase35_prereg.fill`, `a2_corpus_entries`, `V6_RESULT_PATHS`, `SLOTS` | `scripts/phase35_prereg.py:1882`, `:507`, `:317-333` | Fills. The record glob `"results/phase39_*"` (:323) |
| `_rule_e6_entry_subset` / `_rule_e6_decomposition_rule` | `:1674` / `:1786` (reached only via `fill`, never by name) | Shapes in Pattern 1 |
| `phase36_caps.check_unit_caps`, `counts_for`, `committed_budget` | `scripts/phase36_caps.py:165`, `:182`, `:157` | Caps without the raised `adapters` count |
| `phase36_ledger.require_launch`, `append`, `run_id`, `open_runs`, `read_ledger`, `HEARTBEAT_PATH` | `scripts/phase36_ledger.py:400`, `:194`, `:76`, `:189`, `:106`, `:44` | Ledger discipline |
| `phase36_prereg.ENTRIES["front_stop_factor"]` (= 1.5) | `scripts/phase36_prereg.py:395` | Stop (a) arithmetic |
| `phase36_probe.adapted_model(device, k)`, `e1_components`, `silenced`, `stage_e6` (pattern only) | `scripts/phase36_probe.py:590`, `:461`, `:280`, `:609` | Prefix-k models (never `inject_lora`). The anchor ids and seed rule |
| `phase38_prereg.READINGS`, `PREFIXES`, `committed_gate_ranks`, `rank_in_prefix`, `MARGIN`, `first_collapse`, `first_damage`, `relation`, `moved_reachable`, `drop_formula_audit`, `a2_counts`, `MINTING_RECORD` | `scripts/phase38_prereg.py:163`, `:159`, `:857`, `:720`, `:236`, `:753`, `:758`, `:772`, `:766`, `:797`, `:902`, `:124` | Gate 1, ranks, margin, WR-01 vocabulary, committed counts |
| `phase38_rank.reconstruction_checks`, `adapter_digests`, `m2_adapter_path`, `gate_reading` | `scripts/phase38_rank.py:296`, `:286`, `:242`, `:395` | D-20-style digests; the gate row shape |
| `phase18_extraction.value_span_nll` (both reductions), `span_nll_from_ids`, `_frame_preamble`, `_guarded_span`, `reference_set_for`, `score_records`, `aggregate_questions`, `CORPUS_TIERS`, `ADMISSIBLE_NLL_FRAME/REDUCTION`, `CORPUS_PATH` | `scripts/phase18_extraction.py:1110`, `:1050`, `:1031`, `:3014`, `:1159`, `:1919`, `:2223`, `:710`, `:985/987`, `:697` | Instruments (do NOT edit: ancestry-guarded + byte-pinned) |
| `phase19_erasure.value_span_nll_mean`, `per_fact_rows`, `FORBID_IDS_SHA256` | `scripts/phase19_erasure.py:2407`, `:2641`, `:1420` | Gate-equal NLL; mask parity |
| `phase19_run._pooled_rows` | `scripts/phase19_run.py:620` | Gate 2 (27 = 14 + 13 pooled) |
| `phase14_recall.draw_all`, `load_adapted_model`, `assert_no_value_in_prompt`, `contains_value`, `SEED`, `SAMPLE_TEMPERATURE`, `SAMPLE_TOP_P`, `RECALL_MAX_NEW_TOKENS` | `scripts/phase14_recall.py:846`, `:712`, —, `:300`, `:147`, `:159`, `:160`, `:143` | Anchor draws |
| `phase16_persistence.forbid_digest` | `scripts/phase16_persistence.py:180` | Prove the mask == `FORBID_IDS_SHA256` before drawing |
| `phase25_run.atomic_write_json`, `beat`, `start_heartbeat` | (used by phase38_rank:57) | The ONLY atomic writer (os.replace census) |
| `erasure_gate.wilson_upper_bound` / `phase20_gate_coverage.wilson_lower_bound` | `scripts/erasure_gate.py:139` / `scripts/phase20_gate_coverage.py:124` | D-07 Wilson bounds (one-sided z = 1.6448536269514722) |
| `personacore.lora.adapter_disabled`, `personacore.dialogue.ASSISTANT_ID` (= 8186) | `src/personacore/lora/inject.py:157`, `src/personacore/dialogue/serialize.py:25` | Adapter-off reading; anchor ids |

## Package Legitimacy Audit

No external package is installed by this phase. Nothing to verify. **Packages removed:** none. **Flagged:** none.

## Measured Facts (this session; every number has its command)

| # | Fact | How measured |
|---|------|--------------|
| M1 | All 7 `cap_rulings["E6.a2_regenerated_entries"]` SHA-256 values match the files on disk: k0 `phase18_arm_adapter-on.json` 71fb0627…, k8 d4ee51c1…, k16 944ed821…, k32 f595b0c8…, k64 051a3ee4…, k78 `phase19_arm_erased.json` c10313a7…, M2 `phase19_arm_retrain.json` fd349939…. They are extractable from the Portuguese ruling string with the regex `(k = \d+\|M2): (results/[\w.-]+\.json) sha256 ([0-9a-f]{64})`, which gives exactly 7 matches. Adapter-off `results/phase18_arm_adapter-off.json` = `08fe96fbd9753f8b44a5eb67a69d1a2a0b062a666b5a2d5430c2a7476bb15535`. This digest is in no budget field, so the prereg must pin it. | `hashlib.sha256` + regex over the budget JSON |
| M2 | **Gate 2 premise holds.** `phase19_run._pooled_rows(record["draws"], values, "A2", CORPUS_TIERS)` re-derives, for each of the 8 records, per-slot answered counts over n = 27 that equal `phase38_prereg.a2_counts()` for k0..k78 (0 mismatches). For M2 they equal `phase19_retrain_scores.json` `retained[*].m2_answerable` + `omitted_fact.successes` = 0 for pet_name. For adapter-off they are 0/27 for every slot (= `phase18_extraction_report.md:44,81`, 0/104 held-out and 0/112 taught). 1.8 s CPU. Counts (slot order person, pet, cat, sibling, hometown, street, birth_year, house): k0 26 27 27 27 21 27 18 24 · k8 18 24 27 27 7 27 14 24 · k16 10 18 27 22 3 24 13 24 · k32 1 2 27 10 1 11 14 10 · k64 0 0 6 0 0 0 11 6 · k78 0 0 7 0 0 0 8 5 · M2 26 0 27 27 18 27 18 17 · off 0 × 8. | scratch run, `.venv` CPU |
| M3 | **The A2 seed convention**, concretely: `draw_all(model, tok, prompt_ids, device, forbid, index, n_samples=K-1)` with `index = seed_index * K` (phase18 `scripts/phase18_extraction.py:3634-3641`; phase19 `scripts/phase19_erasure.py:2826,2886-2893`). Draw 0 is greedy (no RNG). Draw s+1 uses `torch.Generator(device).manual_seed(SEED + index + s)` for s = 0..46 (`phase14_recall.py:875-893`, generator at :885, `question_seed` :227). `seed_everything(SEED)` runs before the load (`phase19_erasure.py:2805`). The A2 records' config: `seed 1337`, `k 48`, `seed_stride "seed_index * K for the attack families"`, `sample_temperature 0.8`, `sample_top_p 0.95`, `stop_ids [8184, 8185]`, `forbid_ids_sha256 79b55770…` (= `phase19_erasure.FORBID_IDS_SHA256`). | read code + record configs |
| M4 | **The anchor generation code path** is `phase36_probe.stage_e6` (:609-645). ids = `[ASSISTANT_ID] + tok.encode(_frame_preamble(SLOT_FORMS[slot], "ans1"))`, which is byte-equal to `value_span_nll`'s context (`phase18_extraction.py:1150-1153`), so D-04 holds. It runs `assert_no_value_in_prompt` on those ids, then `draw_all(..., i * K, n_samples=K - 1)` with `i` = the slot's position in `LOCKED_FACTS`. **Not reusable as is:** it is timing-only, discards the completions, uses only k = 78, and calls `phase25_run.device()`. Its six-line body is the pattern to copy, with the completions and `stopped` kept. Preambles (measured): person "my name is ", pet "my dog is named ", cat "my cat is named ", sibling "my sister is named ", hometown "i live in ", street "i live on ", birth_year "i was born in ", house_number "my house number is ". | read + tokenizer run |
| M5 | `_rule_e6_entry_subset` (:1674) requires: `entry_indices` a **tuple** (not a list or range), non-empty, ints in 0..215, strictly increasing. `_consume_inputs` (:910) requires the derivation to be a 4-field entry whose `value == entry_indices` (a list != a tuple, so it would refuse), whose `source` names every consumed path, with ≥1 consumed match of `results/phase36_probe_*.json`, each path tracked. `_rule_e6_decomposition_rule` (:1786) takes `decomposition=` as one 4-field entry (`value`, `derivation`, `kind` ∈ {derived, preference}, `source`; no `proposer`/`adopted_by`; not the FORBIDDEN_PHRASE) and returns a deep-frozen copy (:1133). `a2_corpus_entries()` = 216 entries in corpus order: per slot 14 `core_taught` + 13 `core_held_out`; `seed_index` 0..111 is per tier, so a question's identity is `(tier, seed_index)` (plus fact_id). `realized_injection` ∈ {1, 2}. | read + corpus scan |
| M6 | **Budget arithmetic reproduces bit for bit.** In the formula's term order (`phase36_budget.py:566-574`), E6(adapters = 7, anchor_adapters = 7) / 3600 = 0.4949481154825642 == `front_hours.E6`. (i) adapter-off = E6(8, 8) − E6(7, 7) = 0.07070687364036637 h. (ii) = 10584 × `e5_nll_high` / 3600 = 0.13742227585986255 h. Projection = 0.7030772649827931 h ≤ stop (a) = 1.5 × 0.4949481154825642 = 0.7424221732238463 h. **10,584 = 7 adapters × 216 questions × 7 minted values**, so (ii) was priced WITHOUT adapter-off. Adding adapter-off to (ii) gives 0.7227090186770592 h, still ≤ the stop (Open Q4). `_front_seconds` is private, so the prereg must COPY the E6 formula in term order (the precedent is `phase38_prereg.e5_projection_hours`, :182-200) and prove it at import. | scratch run |
| M7 | **No existing function scores the value under the question** (grep of phase18/19/36/14 for question NLL: none). The primitive is `span_nll_from_ids(model, context_ids, value_ids, device)`, which returns `{n_scored, nll_sum, nll_mean}` from one forward pass. The A2 question portion is `_guarded_span(entry)` = `prompt_ids[:-realized_injection]`, ending in 8186 for all 216 entries, prompt length 15-62. **Injected-prefix reading infeasible:** applying `split_value_ids` to each reference candidate refuses one pet_name candidate (3 ids → budget floor(3 × 0.25) = 0). Reference |R| per slot: person 8, pet 8, cat 7, sibling 7, hometown 7, street 6, birth_year 7, house 6 (Σ = 56). Value ids: 3-8. | tokenizer scan |
| M8 | **NLL count per adapter.** Gate 56 + context (b) 27 × 56 = 1512 (= 216 entries × their slot's |R|) → 1568. (ii) adds 216 × 7 = 1512 per adapter (the taught NLL is shared with R_q). Totals: 8 × 1568 + 7 × 1512 = 23,128 NLLs, plus 8 adapters × 8 slots × 48 = 3,072 anchor draws. Priced per adapter: (216 + 8) × 8 = 1792 NLLs ≥ 1568, so the formula's NLL term covers it. Expected wall time is far below the high bound: Phase 38 did ~31k NLLs + loads in 303.4 s on MPS, and the E6 probe's anchor draws averaged 0.16-0.44 s per draw (`results/phase36_probe_e6.json` `per_slot_draw_seconds_mean`). Estimate ~15-25 min [ASSUMED from those two measurements]. | arithmetic over measured records |
| M9 | **Published disagreement, on committed data** (R_a = 1 and G_q lost, main 7 adapters, k0 is the reference). Damage: **24 cells** (person 16/32/64/78; pet 16/32/64; cat 64/78; sibling 32/64/78; hometown 8/16/32/64/78; street 32/64/78; birth_year 78; house 32/64/78). Collapse: **12 cells** (person 64/78; pet 64; sibling 64/78; hometown 64/78; street 64/78; …). R_a: rank 1 everywhere among the 7 except pet_name at k78 (2) and M2 (2). Adapter-off R_a = 5/4/3/4/5/3/3/5, so it is "lost" everywhere and would be in no disagreement anyway. person_name k8 drop = 8/27 == MARGIN exactly, so it is **not** damaged (strict `>`, Phase 38 D-33). All k0 G_q counts are ≥ 18 > 8, so G_q damage is reachable in every slot. | `committed_gate_ranks()` + M2 counts |
| M10 | `phase38_prereg.READINGS` = ('k0','k8','k16','k32','k64','k78','M2','adapter_off') is exactly E6's 8 adapters. `results/phase38_rank.json` (SCORED) already holds each reading's anchor-context `taught_nll`, `minted_nll` and the rank at size "8" (all rank 1, 3.0 bits at k78). So the (ii) **anchor side is already committed**, and Phase 39 adds only the question side. | read record |
| M11 | **Slot-ordering legs** (`tests/test_phase35_prereg.py:2462-2532`). Both E6 slots are "free": `e6_entry_subset`'s input is phase 36, and `e6_decomposition_rule` has none. So **every commit touching the fill file must strictly precede the first add of every `results/phase39_*`** (leg a). Every tracked `results/phase36_probe_*.json` must be first-added before the fill file's first commit (leg b, already true: 2026-10-02). Leg (c) is satisfied by the one file. The census (`:2172-2270`) accepts fills only in files matching `scripts/phase39_*prereg.py`, each as the whole value of a module-level `E6_ENTRY_SUBSET` / `E6_DECOMPOSITION_RULE` binding. **No other file may bind those UPPER names at module level**; `import phase35_prereg as x`, `from phase35_prereg import fill`, `getattr(phase35_prereg, …)` and the string "phase35_prereg" in a constant are all refused. | read tests |
| M12 | **Caps owner scan** (`tests/test_phase36_caps.py:272-293`) **exec's** the tracked fill file in the test process (ubuntu CI included) and reads `E6_ENTRY_SUBSET` → `{"entries": 216}`. So the fill file must import on a CPU-only host with no `checkpoints/` and no `data/`. `a2_corpus_entries()` imports phase18_extraction (torch) and reads the tracked `results/phase18_corpus.json`, which is fine on CI, but **the fill file is not torch-free** (the same false premise 38-05 hit). | read test |
| M13 | **Ledger.** `require_launch("E6")` refuses a cut front and pauses at any unlifted D-13 stop; stop (a) is checked on SPENT hours (before launch), with no in-run timer. `test_every_tracked_v6_mps_record_has_a_launch_line` (`tests/test_phase36_ledger.py:722`) requires every tracked `results/phase3[7-9]_*` JSON whose `provenance.run.device == "mps"` to be named by a ledger end line, so commit the ledger first and then the record (38-09). Spent seconds come from the record's `provenance.run.started_utc/finished_utc` (`RECORD_CLOCK`, :67). Ledger tail: two E5 lines (2026-10-04); E6 spent = 0. | read code + ledger |
| M14 | Every line number cited in 39-CONTEXT canonical_refs still points where it claims (phase35 :1674, :1786, :507; phase18 :1110, :1159, :1230, :1919, :2223; phase19_erasure :2407, :2641; phase36_probe :590, :609). `_pooled_rows` is at `phase19_run.py:620`. | grep -n |
| M15 | The D-11 quote is **wrapped over two lines** in 39-CONTEXT (lines 59-60, with a two-space indent). A verbatim test must join the two lines with ONE space: `"Opção 1: aprovo (i) adaptador desligado como oitavo adaptador e (ii) os conjuntos cunhados da Fase 38 sob a pergunta inteira em \|R\| = 8 (D-09). approved"`. Read it from commit `62af2fe` (the Phase 38 test reads `255380f`). | repr of the lines |

## Architecture Patterns

### System Architecture Diagram

```
                      (CPU, import time — scripts/phase39_prereg.py)
results/phase36_budget.json ─┐   approval block (D-11 verbatim) + E6 projection == front_hours.E6 proof
results/phase36_probe_e1/e6 ─┼─► E6_ENTRY_SUBSET = fill(tuple(range(216)))
39-CONTEXT D-13..D-17 ───────┘   E6_DECOMPOSITION_RULE = fill(entry)  + pure classify() / lost() fns
                                              │ frozen before any results/phase39_* (leg a)
                                              ▼
preflight (no writes) ─ require_launch("E6") ─ caps(entries=216, a2_regen=0, anchor_slots=8, max_k=48)
   │  refuse_if_dirty · tracked inputs · digests (D-20 analog) · SHA of 8 A2 records (M1)
   │  GATE 2: _pooled_rows over 8 records == committed counts (M2)  ── mismatch → STOP (pause Rafael)
   ▼
ledger start ─► run (MPS) ──────────────────────────────────────────────────────────────┐
   │  GATE 1: for each of 8 readings: value_span_nll on reference_set_for(slot) → rank   │
   │          == committed_gate_ranks() (64 cells) ── any mismatch → GATE_FAILED, stop   │
   │  per reading (model loaded once):                                                   │
   │     anchor gen: [ASSISTANT_ID]+preamble → draw_all(i*K, K-1) → completions kept     │
   │     context (b): for 216 entries: span_nll_from_ids(_guarded_span(e), value) × |R|  │
   │     (ii) [7 adapters]: same, taught + minted cleared[:7]                            │
   │     → write-once data/phase39_ctx_<reading>.json BEFORE the next reading            │
   └─ run sidecar (shas, git sha, device, clock) ─► ledger end (record=results/phase39_ctx.json)
                                              ▼
crosscheck (CPU): re-score gate + R_q + (ii) NLLs → data/phase39_ctx_cpu.json (descriptive)
                                              ▼
emit (CPU, pure): sidecars + committed A2 draws → score_records (anchor + A2) → units, rates,
   Wilson, D-17 predicted, per-cell R_a/R_q/G_a/G_q flags → classify (collapse, damage) → record
                                              ▼
Rafael "approved" → commit ledger → commit record → report (render from committed record) → approved → commit
```

### Recommended Project Structure (new files only)
```
scripts/phase39_prereg.py     # THE one fill file (matches scripts/phase39_*prereg.py); entries, approval,
                              # E6 arithmetic, A2-record pins, gate-2 fn, lost/classify fns (pure)
scripts/phase39_ctx.py        # driver: preflight / run / crosscheck / emit / report (name must NOT end in prereg.py)
tests/test_phase39_prereg.py  # ancestry, census, verbatim quote, arithmetic, classifier truth table, gate 2
tests/test_phase39_ctx.py     # fake-model rig, refusals, gate, crash, rehearsal identity, emit, report, censuses
results/phase39_ctx.json      # THE record (one JSON; named on the ledger end line)
results/phase39_ctx_report.md # rendered from the committed record
data/phase39_ctx_{run,gate,cpu,<reading>}.json, data/phase39_rehearsal.json   # gitignored sidecars
```
RUN_ID = `phase36_ledger.run_id(39, "E6", "ctx")` = `"v6/39/E6/ctx"`. Derive the record paths from `V6_RESULT_PATHS` by equality (`next(p for p in V6_RESULT_PATHS if p == "results/phase39_*")`), as `phase38_prereg.py:120-126` does. Do not type them.

### Pattern 1: The two fills (the prereg's module level)
```python
# Source: scripts/phase38_prereg.py:707-712 (binding shape) + phase35_prereg.py:1674-1690, :910-955
import phase35_prereg  # plain import: no alias, no `from ... import fill` (census M11)

E6_ENTRY_SUBSET = phase35_prereg.fill(
    "e6_entry_subset",
    entry_indices=tuple(range(len(phase35_prereg.a2_corpus_entries()))),   # 216, read not typed
    input_records=("results/phase36_probe_e1.json", "results/phase36_probe_e6.json"),
    derivation={
        "value": tuple(range(216)),   # MUST equal entry_indices exactly (tuple, M5); derive, don't type
        "derivation": "D-01: all 216 A2 entries ... (E1 probe configuration.questions = 216, "
                      "E6 probe configuration.anchor_slots = 8)",
        "kind": "preference",
        "source": "39-CONTEXT D-01 (62af2fe); results/phase36_probe_e1.json; "
                  "results/phase36_probe_e6.json; results/phase36_budget.json",
    },
)
E6_DECOMPOSITION_RULE = phase35_prereg.fill("e6_decomposition_rule", decomposition=ENTRIES["e6_decomposition_rule"])
```
`results/phase36_probe_e1.json` carries `configuration.questions = 216` (the `cap_derivations["E6.entries"]` source), and `..._e6.json` carries the anchor configuration. Consuming both is allowed. At least one is required.

### Pattern 2: Anchor generation (context a), one reading
```python
# Source: scripts/phase36_probe.py:621-637 (ids, guard, seed window) + phase14_recall.draw_all :846
ids = [ASSISTANT_ID] + list(tok.encode(phase18_extraction._frame_preamble(SLOT_FORMS[slot], "ans1")))
phase14_recall.assert_no_value_in_prompt(tok, tok.decode(ids), values, prompt_ids=ids)   # PERS-06
completions, stopped = phase14_recall.draw_all(model, tok, ids, device, forbid, i * K, n_samples=K - 1)
# i = LOCKED_FACTS position of slot; K = phase35_prereg.FULL_FIDELITY_K (48)
# before the first draw: phase16_persistence.forbid_digest(forbid) == phase19_erasure.FORBID_IDS_SHA256
```
Store each (reading, slot) as a `DRAW_RECORD_KEYS`-shaped dict: `family` a non-"A2" label (e.g. `"anchor"`), `prefix_text None`, `seed_index = i`, plus `completions` and `stopped`. Then `phase18_extraction.score_records` scores it on the completion alone with the unchanged `contains_value` predicate (`:1972-1990`).

### Pattern 3: Context-(b) NLL for one question × candidate
```python
# Source: phase18_extraction.span_nll_from_ids :1050 + _guarded_span :3014 (Open Q1: B1 reading shown)
context = phase18_extraction._guarded_span(entry)          # question turn ... <|assistant|> (8186)
row = phase18_extraction.span_nll_from_ids(model, context, list(tok.encode(candidate)), device)
# keep row["nll_mean"] (rank, ADMISSIBLE_NLL_REDUCTION) and row["nll_sum"] (D-17 exp(-sum)); one call, never batched
rank = phase38_prereg.rank_in_prefix({c: mean[c] for c in R}, taught, [c for c in R if c != taught])
```
For context (a), call `phase18_extraction.value_span_nll(..., frame=ADMISSIBLE_NLL_FRAME)`, not `phase19_erasure.value_span_nll_mean`. The mean is the same float (`float(row["nll_mean"])`), so gate equality holds, and it also returns `nll_sum` for D-17. Phase 38's `score_values` returns the mean only.

### Pattern 4: Gate 2 (pure, preflight)
```python
# Source: phase19_run._pooled_rows :620 (the pin's per_fact_rows once per tier, summed) — M2
rows = phase19_run._pooled_rows(record["draws"], values, "A2", phase18_extraction.CORPUS_TIERS)
# compare per slot n_answerable/n_questions with: phase38_prereg.a2_counts() (k0..k78),
# phase19_retrain_scores.json retained[*].m2_answerable + omitted_fact.successes (M2), 0 (adapter-off,
# phase18_extraction_report.md:44/81) — any mismatch: STOP before the ledger start (D-19)
```
Per-question G_q units (needed for the D-07 per-draw rate and any per-question view) come from `score_records` on the same draws: hit = `any(record["hits"])`, keyed by `(tier, seed_index)`.

### Pattern 5: Approval outside the caps (D-11, Phase 38 D-21..D-23)
`APPROVED_E6_ADAPTERS = 8` is the one typed approval value. `COMMITTED_ADAPTER_CAP = budget.unit_caps.E6.adapters` (7), with an import-time proof that it equals `len(PREFIXES) + 1`. The driver calls `phase36_caps.check_unit_caps("E6", entries=216, a2_regenerated_entries=0, anchor_slots=8, max_k=48)` and never passes `adapters=` or `anchor_adapters=`. A test census should forbid `\badapters\s*=` inside `check_unit_caps` calls (the analog of 38-06's `\bprefixes\s*=` census, which bit 38-07 on an innocent local variable name; keep the census narrow to the call). `approval_block()` goes into every record.

### Anti-Patterns to Avoid
- **Importing a private `_rule_*` or binding `E6_*` names outside the fill file.** Census red (M11).
- **`inject_lora` or a hand-built LoRA load.** ISO-06 register red. Use `adapted_model` / `load_adapted_model` (`phase38_rank.py:350-377` is the template, but it yields `(model, tok)` and DROPS `forbid`; Phase 39 needs `forbid` for the anchor draws, so it needs its own `reading_model`).
- **`os.replace` anywhere.** Census (`tests/test_phase25_driver.py:344-360`, and the phase38 AST at `tests/test_phase38_rank.py:1531`). Use `phase25_run.atomic_write_json`.
- **A second JSON record with `provenance.run.device == "mps"`.** Each needs its own ledger end line (M13). Keep one JSON record.
- **Recomputing hits with a new predicate** (e.g. a suffix match for A2). D-06 and `score_records`' docstring (:1935-1950) reject it.
- **Typing a derived number** (projection, stop, margin, counts). Phase 38 has `test_no_derived_value_is_typed_in_the_prereg`. Mirror it.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Prefix-k model | your own ablation/LoRA load | `phase36_probe.adapted_model(device, k)` | ISO-06 register, adapter identity proof, the `ordered_prefix` digest |
| Rank with ties | a sort | `phase38_prereg.rank_in_prefix` | proven ≡ `exposure_rank` on random tied sets (`tests/test_phase38_prereg.py:212`) |
| A2 counts | re-scoring loops | `phase19_run._pooled_rows` → `per_fact_rows` → `score_records`/`aggregate_questions` | defect C (14-question rows) is handled there |
| Damage/collapse/margin | new thresholds | `phase38_prereg.MARGIN`, `first_collapse`, `first_damage`, `drop_formula_audit` | D-14/D-33 published semantics (strict `>`; the person k8 exact tie) |
| Ledger, stop, caps | timers/caps in the driver | `require_launch`, `check_unit_caps` | D-03: no second stop rule; pinned modules |
| Atomic write | tmp + rename | `phase25_run.atomic_write_json` | os.replace census |
| Wilson bound | a new formula | `erasure_gate.wilson_upper_bound` + `phase20_gate_coverage.wilson_lower_bound` | stdlib-only house versions, z read by reference |
| Seeded draws | a sampling loop | `phase14_recall.draw_all` | per-draw generator; prefix stability tested |

**Key insight:** every scoring decision Phase 39 needs already exists as a frozen, tested function. The only new arithmetic is the context-(b) context ids (one line) and the per-cell classifier (a pure truth table).

## Common Pitfalls

### Pitfall 1: The prereg is not frozen before the CPU rehearsal
**What goes wrong:** in Phase 38, `results/phase38_minting.json` froze `phase38_prereg.py` (leg a) before the rehearsal read real ranks. Phase 39's first record is the run record itself, so the decomposition rule stays editable after the rehearsal has seen a real slice of R_q/G_a.
**How to avoid:** the D-34 identity (`data/phase39_rehearsal.json`) must record `sha256(scripts/phase39_prereg.py)`, and real-root preflight must REFUSE if it differs at launch, or the prereg must be in `DISCLOSED_MODULES` so every later commit is listed with its reason. Run the prereg's code review BEFORE the rehearsal (Open Q5).
**Warning signs:** a plan that orders "rehearsal" before "prereg review".

### Pitfall 2: "Lost" for R_q, G_a damage at n = 1, and the WR-01 outcomes are under-specified
**What goes wrong:** D-14 says "rank > 1", but R_q is 27 ranks per cell. For G_a with n = 1, `pre/1 − post/1 > 0.296` holds iff k0 hit and k missed, so "damage" is identical to "collapse" whenever k0's anchor hits, and **unreachable** when it misses. Planners will invent these silently.
**How to avoid:** write them into the frozen rule entry (Open Q2/Q3) and test the full truth table.

### Pitfall 3: Context (a) and B1 context (b) differ by two things
B1 drops the `ans1` preamble AND adds the question. G_a (no injected prefix) and G_q (injected first ⌊0.25·ids⌋ value ids, scored on `prefix_text + completion`) also differ in more than "context". Declare both in the report's limitations whatever Rafael rules (Open Q1).

### Pitfall 4: Anchor seed windows overlap A2 question windows
`i * K` for i = 0..7 (the stage_e6 rule) gives seeds 1337..1720, which equal the windows of A2 `seed_index` 0..7 (e.g. the person_name anchor shares RNG seeds with person_name taught question 0). The prompts differ, so this is harmless, but it is a shared-randomness fact to declare (Open Q6).

### Pitfall 5: `aggregate_questions` needs a corpus tier
It `_prove`s `tier in CORPUS_TIERS` (`:2213`), and the anchor belongs to neither tier. Do not stamp a fake tier into the record. Compute the anchor unit as `int(any(hits))` from `score_records`. In a TEST only, prove it equals `aggregate_questions([scored], tier="core_taught")["n_answerable"]` on the same draws.

### Pitfall 6: Census bites (each red in only the full suite or on CI)
- `tests/test_phase21_sc5.py` counts `== 10` literals in `tests/`, comments included. New tests must not contain it.
- `tests/test_lora_inject.py`: no `inject_lora`.
- The os.replace census.
- The Phase 35 slot census and ordering legs (M11) scan every `scripts/**/*.py`.
- `test_phase36_caps.py` exec's the fill file (M12: CPU-only, no checkpoints at import).
- `test_phase36_ledger.py:722`: commit the ledger first, then the record.
- `mitigation_gate.ratchet_k` accepts only K ∈ (48, 24, 16, 8) if any fixture calls it.
- Phase 38 tests pin `phase38_rank.py`/`phase38_prereg.py` bytes through the record's `module_sha256`, so **never edit them**. Import only.

### Pitfall 7: Fixtures that monkeypatch `_ROOT` but read the real git index
These went red when the Phase 36 ledger became tracked (22 reds). Phase 39 test rigs must stub `phase36_caps.tracked_files` / the ledger path alongside `_ROOT`, and the full suite must re-run after each record commit.

### Pitfall 8: zsh NOMATCH and `$T` word-splitting in verify commands
`ls results/phase39_* 2>/dev/null` is blind or erroneous under zsh. Use `git ls-files 'results/phase39_*'` or `find`. A test-file list in `$T` does not word-split in zsh: write it to a file and use `$(cat f)`.

### Pitfall 9: The verbatim quote is wrapped (M15)
Join the two lines with a single space. Do not search line by line.

### Pitfall 10: Wilson on draws ignores clustering
`wilson_upper_bound`'s docstring says n must count QUESTIONS. D-07's h/48 and total/1296 are draw-unit rates. Label them "draw unit, within-question clustering ignored, descriptive". The two one-sided 95% bounds together form a 90% two-sided interval; state which.

## Code Examples

### Gate-1 rows (reuse, not copy)
```python
# Source: scripts/phase38_rank.py:395-419 — feed it {slot: {candidate: nll_mean}} for the reading
rows[reading] = phase38_rank.gate_reading(reading, nll_by_slot)   # equal = rank AND |R| match
passed = all(r["equal"] for by_slot in rows.values() for r in by_slot.values())
```

### E6 projection (copy the term order; prove at import)
```python
# Source: scripts/phase36_budget.py:566-574 (private _front_seconds), phase38_prereg.py:182-200 precedent
def e6_projection_hours(adapters, anchor_adapters, extra_nlls=0):
    p, c, k = _BUDGET["unit_prices"], _BUDGET["unit_caps"]["E6"], phase35_prereg.FULL_FIDELITY_K
    return (
        adapters * (p["adapter_setup_high"]
                    + c["a2_regenerated_entries"] * p["a2_question_k48_high"] * c["max_k"] / k
                    + (c["entries"] + c["anchor_slots"]) * p["e5_candidates_per_slot_max"] * p["e5_nll_high"])
        + anchor_adapters * c["anchor_slots"] * c["max_k"] * p["e6_anchor_draw_high"]
    ) / 3600 + extra_nlls * p["e5_nll_high"] / 3600
# _prove(e6_projection_hours(7, 7) == front_hours.E6)  -> True (M6); approved = (8, 8, 10584)
```

## State of the Art (in this repo)

| Old approach | Current approach | When | Impact |
|---|---|---|---|
| Cap raised by editing the budget | approval + projection in the phase prereg, caps checked without the raised count | Phase 38 D-21..D-23 | Phase 39 copies it for `adapters` 7 → 8 |
| Rehearsal reads real data unreported | D-34 identity written before the first score + disclosure of later driver commits | Phase 38 | Phase 39 must extend it to the prereg (Pitfall 1) |
| Relation outcomes BEFORE/SAME/AFTER/NEVER | + ALREADY_AT_K0, UNREACHABLE_AT_SIZE (WR-01, d33986c) | Phase 38 review | D-15 wants them per cell; mapping not yet written (Open Q3) |

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|-------|---------|---------------|
| A1 | The MPS run takes ~15-25 min (from Phase 38's 303 s for ~31k NLLs and the probe's 0.16-0.44 s per anchor draw) | M8 | Low: the stop is 0.742 h, and only spent hours at the NEXT launch are checked |
| A2 | The CPU cross-check of ~23k NLLs takes ~2-4 min (Phase 38 CPU 2:32 for ~31k) | Validation | Low |
| A3 | Rafael's "the full A2 question" means B1 (question prompt without the injected tail, whole value scored) | Open Q1 | HIGH: it changes what R_q measures. Ask before the freeze |
| A4 | The recommended 7-plan split fits the sequential-wave practice (`parallelization: false`) | Plan split | Low |

## Open Questions (rule before `scripts/phase39_prereg.py` is frozen; Phase 38 precedent: plan-time rulings D-24..D-32)

1. **Context (b) ids for NLL/rank.** What we know: the A2 prompt = `build_recall_prompt(question)` + the injected ⌊0.25·|ids|⌋ value ids. The per-candidate injected reading is infeasible (M7). The options are:
   - **B1:** `_guarded_span(entry)` + whole value. This is the literal "A2 question". It differs from (a) by the question AND the missing preamble.
   - **B1′:** `_guarded_span(entry)` + `encode(ans1 preamble)` + value. This differs from (a) by the question only, but no A2 prompt has this shape.

   Recommendation: B1 as the main reading (it is what A2 generation conditions on, minus a per-candidate artefact), with Pitfall 3 declared. Rafael rules.
2. **R_q "lost" per cell.** With 27 per-question ranks: median rank > 1 (27 is odd, so the median is an integer, and D-10 already publishes it), or "fewer than X of 27 at rank 1", or the rank of the mean NLL (which D-10 calls descriptive). Recommendation: median rank > 1. Rafael rules.
3. **WR-01 and the k = 0 rules per cell.** Proposed:
   - k0 cells: damage is "reference" (not classified), and collapse is classified.
   - A reading already lost at k0 in its own context → that reading's flag is `ALREADY_AT_K0`. The cell is reported with that label and enters no sufficiency class.
   - G_a damage when the k0 anchor unit = 0 → `UNREACHABLE_AT_SIZE`. G_q damage is reachable in all slots (M9).
   - R_q with median rank at k0 > 1 → `ALREADY_AT_K0`.
   - Damage uses strict `>`, and person_name k8 is the named exact tie.

   Rafael confirms.
4. **(ii) under adapter-off.** The approved price (10,584 NLLs) covers 7 adapters (M6). D-36 says "read each curve beside adapter-off". Adding adapter-off to (ii) costs 1,512 NLLs (+0.0196 h → 0.7227 h ≤ 0.7424 h). Recommendation: ask. The default is to follow the priced 7.
5. **Prereg freeze vs the rehearsal** (Pitfall 1). Recommendation: review the prereg first, pin its sha in the rehearsal identity, and have the real-root preflight refuse on drift. Any later edit needs Rafael's ruling plus disclosure.
6. **Anchor seed index.** Recommendation: stage_e6's `i * K` (i = the LOCKED_FACTS position), already the committed probe configuration. Declare the overlap with A2 windows (Pitfall 4).
7. **D-17 in context (b)** (minor). exp(−nll_sum) under B1 predicts the whole value at assistant position 0, while G_q hands over the prefix. Recommendation: publish as-is, descriptive, with that caveat added to D-17's.

## Recommended Plan Split (Phase 38's pattern, minus minting; `parallelization: false`, so sequential waves)

| Plan | Wave | Content | Autonomous |
|---|---|---|---|
| 39-01 | 1 | `scripts/phase39_prereg.py` + `tests/test_phase39_prereg.py`: paths, D-11 approval + E6 arithmetic (M6), the 8 A2 SHA pins (7 parsed from cap_rulings + adapter-off typed and tested), the two fills, entries (definitions, Open Q1-Q7 rulings), pure `lost`/`classify`/gate-2 functions, the ancestry guard, the slot census, `test_no_derived_value_is_typed`, every-function + no-skip censuses | yes |
| 39-02 | 2 | Code review of the prereg → Rafael rules → fixes (each its own commit). The prereg is then de-facto frozen (Pitfall 1) | **no** (checkpoint) |
| 39-03 | 3 | `scripts/phase39_ctx.py` part 1: preflight refusals (incl. gate 2), `reading_model` with forbid, gate 1, the run with anchor gen + context (b) + (ii) sidecars, ledger start/end, crash/partial shape | yes |
| 39-04 | 4 | Part 2: crosscheck, build_record/emit (classification through the frozen prereg), render_report/report, main. Then the CPU rehearsal on a declared slice (e.g. k0 + k78 × pet_name + birth_year, all 27 questions), feeding ONE real producer record to the report (the dry-run lesson) | yes |
| 39-05 | 5 | Driver review → fixes → full suite → Rafael approves launch → MPS run (`nohup caffeinate -dims`) → crosscheck → emit | **no** |
| 39-06 | 6 | Record to Rafael → approved → commit `ledger/v6_mps_ledger.jsonl` alone, then `results/phase39_ctx.json` alone → full suite | **no** |
| 39-07 | 7 | Render the report from the committed record → approved → commit alone → SC1-SC4 by command; STATE/ROADMAP/REQUIREMENTS by hand | **no** |

The record carries:
- the approval block;
- the SHA of each A2 source and the gate-2 table;
- the gate-1 rows;
- per (reading, slot): the anchor completions + stopped (D-08), the anchor unit and h/48 with Wilson bounds, the per-question G_q hits from the committed draws, total/1296 with Wilson bounds, the R_q per-question ranks + rank-1 count + median + the rank of the mean NLL, and D-17 predicted vs observed;
- (ii) ranks;
- the per-cell flags and classes for collapse and damage, with class counts over the denominator of disagreement cells;
- the CPU cross-check block (criterion False);
- the rehearsal disclosure;
- the limitations (D-22, Pitfall 3/4/10);
- `provenance.run` (RECORD_CLOCK).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `.venv` Python | everything | ✓ | 3.11.15 | — |
| torch + MPS | run | ✓ | 2.7.1, MPS True | none on the real root (D-21 is MPS only); CPU for the rehearsal only |
| `checkpoints/convbase_slim.pt`, `persona_adapter.pt`, `phase19_erase_reference_adapter.pt` | readings | ✓ (gitignored) | 55.6 MB / 1.35 MB / 1.35 MB | — (preflight refuses if missing) |
| `artifacts/tokenizer.json` | all | ✓ tracked | — | — |
| A2 records + `phase18_corpus.json` + `phase38_minting.json` + `phase38_rank.json` | gates, (ii) | ✓ tracked | SHAs per M1 | — |
| pytest | tests | ✓ | 9.0.3 | — |

Missing dependencies: none.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 in `.venv` (Python 3.11), CPU-only, zero skips in Phase 39 files |
| Config file | `pyproject.toml`; `make test` = `.venv/bin/pytest -q` |
| Quick run command | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase39_prereg.py tests/test_phase39_ctx.py` |
| Cross-phase guards | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase35_prereg.py tests/test_phase36_caps.py tests/test_phase36_ledger.py tests/test_phase21_sc5.py tests/test_lora_inject.py tests/test_phase25_driver.py tests/test_phase38_prereg.py tests/test_phase38_rank.py` (~2-3 min) |
| Full suite command | `LOG=$PWD/suite39.log; nohup sh -c ".venv/bin/pytest -q -p no:cacheprovider > $LOG 2>&1; echo EXIT=\$? >> $LOG" &` + a `run_in_background` `until grep -q '^EXIT=' "$LOG"; do sleep 60; done` waiter (the Bash tool caps at 600 s; the suite measured 45:55-49:05 at Phase 38, 4103 passed / 4 skipped) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CTX-01 / SC1 | `E6_ENTRY_SUBSET == tuple(range(216))` is filled once in `scripts/phase39_prereg.py`, consumes probe e1/e6, and is under the cap. The ordering legs and census are green | unit + census + caps exec | `pytest tests/test_phase39_prereg.py -k "entry or fill" tests/test_phase35_prereg.py -k "slot_census or slot_ordering" tests/test_phase36_caps.py -k owner` | ❌ W0 |
| SC4 | The prereg and its test are first-added before every `results/phase39_*`; every prereg commit strictly precedes the first record; `RECORDS_AT_COMMIT == 0` at its first commit | git ancestry | `pytest tests/test_phase39_prereg.py -k "frozen or first_added or records_at_commit"` | ❌ W0 |
| CTX-02 (gate 2) | The 8 A2 records hash to the pins (7 parsed from cap_rulings + adapter-off). `_pooled_rows` reproduces the committed counts (M2 table); a tampered draw → STOP | unit (real tracked JSON, CPU) | `pytest tests/test_phase39_prereg.py -k "gate2 or a2_sha"` | ❌ W0 |
| CTX-02 (gate 1) | 64 committed ranks reproduced before any new scoring; a mismatch gives GATE_FAILED and no anchor/question scoring | unit (fake model rig) | `pytest tests/test_phase39_ctx.py -k gate` | ❌ W0 |
| CTX-02 (a) gen | Anchor ids == the `value_span_nll` context; seeds `i*K`, `n_samples=K-1`, T/top-p from phase14_recall; forbid digest == FORBID_IDS_SHA256; all 48 completions kept; the hit is re-derivable from the record | unit (stubbed draw_all records its args) | `pytest tests/test_phase39_ctx.py -k anchor` | ❌ W0 |
| CTX-02 (b) NLL | One `span_nll_from_ids` call per (question, candidate), context = `_guarded_span(entry)` (or the ruled variant); 216 × |R| per reading; (ii) uses `cleared[:7]` | unit (call log) | `pytest tests/test_phase39_ctx.py -k "question or minted"` | ❌ W0 |
| CTX-03 | Classifier truth table: the 4 classes + NO_DISAGREEMENT, collapse and damage separately, ALREADY_AT_K0 / UNREACHABLE per Open Q3, strict `>` with the person k8 tie; adapter-off and (ii) never in classes; counts with denominators | unit (pure) | `pytest tests/test_phase39_prereg.py -k "classify or lost"` | ❌ W0 |
| D-11 | Quote verbatim (two-line join, from 62af2fe); projection 0.7030772649827931 ≤ 0.7424221732238463; `front_hours.E6` reproduced; caps called without `adapters` | unit + AST | `pytest tests/test_phase39_prereg.py -k "d11 or arithmetic" tests/test_phase39_ctx.py -k caps` | ❌ W0 |
| D-21 run shape | Refusals before the ledger start (dirty tree, open attempt, require_launch, non-MPS on the real root, missing inputs, digests, gate 2, prereg drift since the rehearsal); write-once sidecars; crash → reconcile; one real CPU rehearsal record fed to the report; `main(['run'])` binds with no args | unit + rehearsal | `pytest tests/test_phase39_ctx.py -k "preflight or refus or crash or rehearsal or main"` | ❌ W0 |
| D-20 | CPU cross-check over NLL/rank only; differing cells counted; criterion False | unit | `pytest tests/test_phase39_ctx.py -k crosscheck` | ❌ W0 |
| Report | Rendered from the committed record only, byte-equal to `render_report(record)`, GFM tables parse, every class table has a denominator | unit | `pytest tests/test_phase39_ctx.py -k report` | ❌ W0 |
| Hygiene | No `inject_lora`, no `os.replace`, no `== 10` in tests, instruments imported not redefined (AST, not grep: docstrings mention the terms), every function called by a test, zero skips, `phase18_extraction.py` bytes unchanged | AST census | `pytest tests/test_phase39_*.py -k "census or ast or skips" tests/test_phase21_sc5.py::test_instruments_unchanged_byte_for_byte tests/test_lora_inject.py` | ❌ W0 |

### Sampling Rate
- **After every task commit:** the quick run + the cross-phase guards.
- **After every wave AND after each `results/phase39_*` / ledger commit:** the full suite (records surface latent reds: Phase 36).
- **Before `/gsd:verify-work`:** the full suite green on the committed state.

### Wave 0 Gaps
- [ ] `tests/test_phase39_prereg.py`: ancestry, census, D-11 quote, arithmetic, A2 pins, gate 2 on real tracked JSON, classifier truth table.
- [ ] `tests/test_phase39_ctx.py`: fake-model rig with tmp root, tmp ledger and stubbed `adapter_digests` / `tracked_files` (Pitfall 7); no checkpoint dependency (ubuntu CI).
- No framework install needed.

### Manual-Only Verifications
| Behavior | Why manual | Instruction |
|---|---|---|
| Rafael's "approved" before each record/ledger commit and before the MPS launch | human gate | checkpoint presents the artifact; commit only after the literal word |
| The MPS run | device + ledger | `nohup caffeinate -dims .venv/bin/python scripts/phase39_ctx.py run`; stop (a) 0.7424 h is checked by require_launch only |

## Security Domain

Applicable ASVS: V5 input validation (every consumed record is SHA-pinned or tracked-and-clean; `_prove` refusals, never `assert`). V6 integrity: SHA-256 via hashlib, never hand-rolled. V2/V3/V4 do not apply (no auth, no sessions, no network).

| Threat | STRIDE | Mitigation |
|---|---|---|
| A swapped A2 draw record | Tampering | SHA-256 against cap_rulings (7) + the prereg pin (adapter-off) before gate 2 |
| A pickled checkpoint executing code | Elevation | the existing loaders (`weights_only=True`, `phase14_recall.py:81-84`); digests via `reconstruction_checks` |
| A rule fitted after seeing data | Repudiation | the ancestry guard + rehearsal prereg-sha pin (Pitfall 1) + write-once records |
| Secrets in records | Info disclosure | none written; no tokens or network |

## Sources

### Primary (HIGH: read or executed in this session)
- `scripts/phase35_prereg.py` :1-140, :300-336, :495-520, :840-960, :1125-1150, :1640-1923
- `scripts/phase36_caps.py` (whole), `scripts/phase36_ledger.py` :76, :266-425, `scripts/phase36_budget.py` :536-575, `scripts/phase36_probe.py` :540-760
- `scripts/phase38_prereg.py` :1-245, :470-966; `scripts/phase38_rank.py` (whole)
- `scripts/phase18_extraction.py` :555-700, :820-960, :960-1262, :1874-1990, :2205-2280, :3010-3050, :3600-3665; `scripts/phase19_erasure.py` :2380-2440, :2635-2690, :2800-2920; `scripts/phase19_run.py` :620-648; `scripts/phase14_recall.py` :130-165, :220-232, :300-322, :793-930
- `tests/test_phase35_prereg.py` :2125-2560; `tests/test_phase36_caps.py` :266-295; `tests/test_phase36_ledger.py` :722-790; `tests/test_phase38_prereg.py` :455-600; `tests/test_phase38_rank.py` (test index)
- `results/phase36_budget.json`, `results/phase36_probe_e1.json`, `results/phase36_probe_e6.json`, `results/phase19_retrain_scores.json`, `results/phase38_rank.json`, the 8 A2 records, `results/phase18_corpus.json`, `results/phase18_extraction_report.md:37-44,74-81`, `ledger/v6_mps_ledger.jsonl`
- Phase 38 CONTEXT, VALIDATION, VERIFICATION, plans 01-10 (objectives) and SUMMARY deviations; 36-CONTEXT D-07/D-09
- Memory notes: execute-phase gates, research-gaps, dry-run tests, zsh NOMATCH

### Secondary / Tertiary
- None. No web sources were needed: the phase is internal to the repo.

## Metadata

**Confidence breakdown:**
- Reuse map, censuses, ordering, gates: HIGH (code read, premises executed: M1, M2, M6, M7).
- Context-(b) definition, R_q "lost", WR-01 per-cell mapping: MEDIUM (CONTEXT is silent; options measured, a ruling is needed).
- Run time: MEDIUM (extrapolated from Phase 38 and the E6 probe).

**Research date:** 2026-10-04
**Valid until:** the next commit touching `scripts/phase3[5-8]_*.py`, `phase18_extraction.py`, `phase19_*.py` or the A2 records (otherwise stable).
