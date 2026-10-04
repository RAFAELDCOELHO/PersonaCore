# Phase 39: Instrument × Context 2×2 - Context

**Gathered:** 2026-10-04
**Status:** Ready for planning

<domain>
## Phase Boundary

E6 (CTX-01..03). On the same adapters, measure rank/NLL (the Phase 18/38 instrument) and generation (the
A2 instrument) in two contexts: (a) the answer anchor without the question, (b) the full A2 question.
Then split the rank/generation disagreement (rank intact while A2 generation is lost, the pattern
Phase 38 measured) into an instrument part and a context part, by a rule written and frozen before any
record. New capabilities belong in other phases.

</domain>

<decisions>
## Implementation Decisions

Decided by Rafael in discuss-phase 39 (2026-10-04), except where marked as carried forward.

### Carried forward (not re-asked)
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

### Anchor generation — context (a)
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

### Rank with the full question — context (b)
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

### Decomposition rule — `e6_decomposition_rule`, frozen before any record
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

### Gate and run shape — Phase 38's pattern with these differences
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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements and roadmap
- `.planning/ROADMAP.md` §"Phase 39: Instrument × Context 2×2" — goal and SC1-SC4
- `.planning/REQUIREMENTS.md` — CTX-01, CTX-02, CTX-03

### Pre-registration slots and budget
- `scripts/phase35_prereg.py` — `_rule_e6_entry_subset` (:1674), `_rule_e6_decomposition_rule` (:1786),
  `_SLOTS` (owner 39), `a2_corpus_entries()` (:507), `V6_RESULT_PATHS` ("results/phase39_*"), `fill()`
- `results/phase36_budget.json` — `unit_caps.E6`, `formula.E6`, `unit_prices`,
  `cap_rulings["E6.a2_regenerated_entries"]` (the seven SHA-256), `front_hours.E6`, `approved`
- `.planning/phases/36-mps-cost-probes-and-budget-commitment/36-CONTEXT.md` — D-07 (E6 anchor probe),
  D-09 (unit caps), D-15 (cut table)
- `scripts/phase36_caps.py` (check_unit_caps), `scripts/phase36_ledger.py` (require_launch, append)
- `results/phase36_probe_e6.json` — anchor generation timing configuration

### Precedent (Phase 38 — same pattern, definitions reused)
- `.planning/phases/38-exposure-rank-at-larger-minted-sets/38-CONTEXT.md` — D-12..D-36, WR-01
- `scripts/phase38_prereg.py` — MARGIN, first_collapse/first_damage, relation (WR-01 outcomes),
  approval_block pattern (D-21..D-23)
- `scripts/phase38_rank.py` — gate, ledger run, sidecars, crosscheck, emit, report, D-34 rehearsal
- `results/phase38_rank.json`, `results/phase38_minting.json`

### Instruments
- `scripts/phase18_extraction.py` — value_span_nll (:1110), reference_set_for (:1159), exposure_rank
  (:1230), score_records (:1919), aggregate_questions (:2223)
- `scripts/phase19_erasure.py` — value_span_nll_mean (:2407), per_fact_rows (:2641)
- `scripts/phase19_run.py` — `_pooled_rows`
- `scripts/phase14_recall.py` — SAMPLE_TEMPERATURE, SAMPLE_TOP_P, RECALL_MAX_NEW_TOKENS
- `scripts/phase36_probe.py` — adapted_model (:590), stage_e6 (:609): anchor generation code path

### Committed inputs
- A2 K = 48 records: `results/phase18_arm_adapter-on.json`, `results/erasure_kstar_arm_k008.json`,
  `..._k016.json`, `..._k032.json`, `..._k064.json`, `results/phase19_arm_erased.json`,
  `results/phase19_arm_retrain.json`, `results/phase18_arm_adapter-off.json` (D-11 i)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `phase38_rank.py`: the whole run skeleton (preflight refusals, digests, gate before scoring,
  write-once sidecars, ledger start/end, CPU cross-check, emit, report, rehearsal identity/disclosure).
- `phase36_probe.stage_e6`: anchor generation at the ans1 anchor (timing-only so far) — the code path
  for D-04/D-05.
- `phase38_prereg`: MARGIN, drop formula, first_event/relation with the WR-01 outcomes.

### Established Patterns
- Prereg frozen at the first `results/phase39_*` commit; dated continuations via `scripts/_addendum.py`.
- Approvals that raise a committed cap live in the prereg and every record (Phase 38 D-21..D-23).
- Review before each freeze and before the MPS run; latent reds fixed in tests only.

### Integration Points
- `results/phase39_*` is already a V6_RESULT_PATHS member; the Phase 35 ordering legs and the slot
  census scan new `scripts/phase39_*.py` automatically.
- The `phase36_caps` owner scan reads the fill file's `e6_entry_subset` value against `unit_caps.E6`.

</code_context>

<specifics>
## Specific Ideas

- Read each context's curve beside the adapter-off reading (Phase 38's D-36 applies to (ii)).
- The decomposition classes are named exactly: CONTEXT_SUFFICIENT, INSTRUMENT_SUFFICIENT, EITHER,
  INTERACTION_ONLY, NO_DISAGREEMENT.

</specifics>

<deferred>
## Deferred Ideas

- Minted-set reading under the full question at |R| > 8 (32, 128, 512; birth_year 220) — recorded as not
  measured in E6 (D-12); may run later as a dated continuation after E1-E4, labelled as after E6.

</deferred>

---

*Phase: 39-instrument-context-2-2*
*Context gathered: 2026-10-04*
