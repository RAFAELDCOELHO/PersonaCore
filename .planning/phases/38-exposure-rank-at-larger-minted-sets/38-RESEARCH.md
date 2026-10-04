# Phase 38: Exposure Rank at Larger Minted Sets - Research

**Researched:** 2026-10-04
**Domain:** pre-registered candidate minting (CPU) + teacher-forced NLL exposure rank on the committed Phase 19 ablation prefixes (MPS, under the v6.0 ledger)
**Confidence:** HIGH for everything measured below (commands + raw output are reproduced); MEDIUM for the plan shape; the open questions are flagged as such.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

All decisions below are Rafael's (2026-10-04, in Portuguese; paraphrased faithfully, the D-09 ruling
quoted). Facts marked "measured" were measured by Claude this session before the question was asked.

#### Minting rule (names and places) — fills `e5_minting_rule` (RANK-01)
- **D-01: Generator.** A syllable grammar with a fixed seed, `seed_list()[0]` (`phase35_prereg.seed_list()` returns `phase23_run.SEED_LADDER`; its first seed is 1337). It is deterministic and independent of the taught values. Candidates are never edits of the current set or of the taught value.
- **D-02: Surface format.** Each candidate has the same surface format as the slot's taught value: number of words, capitalization, and a fixed suffix if the slot has one. It also has EXACTLY the same number of tokens. Research must measure, from the committed values, whether a slot really has a fixed suffix before the rule claims one.
- **D-03: Exclusions.** Excluded are every value taught anywhere in the project: core facts, fillers, calibration facts, and the Phase 17 persona values. The four Phase 17 mechanical filters also apply: ≤ 8 tokens, `decode(encode(v)) == v`, substring-disjoint from minted ∪ FORBIDDEN, and absent from the questions.
- **D-04: Clearance** follows Phase 17. A candidate is cleared iff it is absent from the base model's completions for that slot: the 13 held-out questions, greedy plus 3 warm draws, 52 completions per slot, checked with `phase14_factset.exact_match_clean` (`scripts/phase17_persona_gate.py:285-345`).
- **D-05: Order and record.** The cleared list stays in generator order, and every set is a prefix (the first n) of that list. The minting record holds the WHOLE cleared list, with slack beyond 512, because Phase 43 (E4) also consumes it (`e4_parameters` declares `results/phase38_minting*.json` as a required input, `phase35_prereg.py:1823-1827`).
- **D-06: Ordering.** The rule is committed before any candidate exists. Phase 35 enforces this: `e5_minting_rule` has no input record, so its fill file precedes every `results/phase38_*` record, and it cannot share a fill file with `e5_set_sizes`.

#### Sets and sizes — fills `e5_set_sizes` (RANK-01)
- **D-07:** All 8 slots, the target `pet_name` and the 7 non-targets, with one maximum set per slot, within the cap of 8 sets × 512.
- **D-08: Nested sizes** of 8, 32, 128 and 512, as prefixes of the same list. Each maximum set is scored once, and the rank is read at every size prefix.
- **D-09 (numeric slots): plausibility beats size.**
  - `birth_year` enumerates 1800-2025 with the taught value's token count. Measured: there is no committed Phase 14 year generator (the years are hand-listed in `phase14_factset.py:85-123`), and every 4-digit number is exactly 4 tokens, so the range is 226 values before exclusions and clearance.
  - `house_number` enumerates numbers with the taught value's (7412) digit and token count, i.e. the 4-digit numbers, about 9000 values.
  - Where fewer than 512 are available, the largest size is what is available, declared before scoring (`e5_set_sizes`, "as far as minting allows").
- **D-10: Numeric order:** a seeded shuffle. Enumerate the range, apply the exclusions and clearance, then shuffle with `seed_list()[0]`, the same seed as the name grammar. Sets are prefixes of the shuffled list; ascending order is rejected.
- **D-11: Always reported beside the minted sets:**
  - (a) the committed `reference_set_for` set of each slot (6-8 members, measured: street and house_number 6; cat_name, sibling_name, hometown and birth_year 7; person_name and pet_name 8) as the published reference;
  - (b) the same readings with the adapter OFF, as a control for what comes from the base model.

#### Definitions — fill `e5_rank_moves_and_generation_collapses`, frozen before any record (RANK-02)
- **D-12: Rank moved at prefix k** iff `rank_k >= 2 x rank_0` in the same slot and at the same set size, i.e. exposure fell by at least 1 bit relative to k = 0.
  - The 1-bit threshold is labelled `preference`.
  - With the committed sets and rank_0 = 1, this coincides with "left rank 1".
  - Exposure in bits = log2(|R| / rank).
- **D-13: Generation collapsed at prefix k:** 0 of 27 questions answered on A2 at K = 48, read from the committed records.
- **D-14: Additional descriptive event, generation damaged:** the first k whose recall drop relative to k = 0 exceeds the published margin 0.2962962962962963 (`MARGIN_K x NONTARGET_NOISE_FLOOR`).
- **D-15: Answer per slot and per set size:**
  - The rank moved BEFORE, AT THE SAME prefix as, AFTER, or NEVER relative to the collapse, and the same relative to the damage.
  - "Never collapsed within the grid" is a named outcome.
  - The whole curves are published (rank and exposure in bits per prefix and per size), not only the events.
- **D-16:** The two extra readings (adapter off and M2) are descriptive references only. They enter neither "moved" nor "collapsed", which stay relative to k = 0 over the six prefixes.

#### Device, gate and the rank re-implementation (RANK-02/03)
- **D-17:** E5 runs on MPS, under the milestone ledger (`require_launch("E5")`), within E5's budget. The committed ranks are MPS ranks.
- **D-18: Gate before scoring any minted set.** The new rank function must reproduce EXACTLY the committed `exposure_rank` at the committed |R| (6-8 per slot), with the same tie-break by string, for all 8 slots and all eight readings. If it does not, STOP.
  - The eight readings are k = 0, 8, 16, 32, 64, 78, M2 and adapter-off.
  - Committed sources, measured:
    - k = 0: `results/phase19_arm_erased.json` `pre_erasure.exposure`;
    - k = 8/16/32/64: `results/erasure_kstar_summary.json` `exposure_rank_this_run` and `results/phase19_collateral_curve.json` checkpoints;
    - k = 78: `results/phase19_arm_erased.json` `exposure`;
    - M2: `results/phase19_arm_retrain.json` `exposure`, adapter `checkpoints/phase19_erase_reference_adapter.pt`;
    - adapter-off: `results/phase18_arm_adapter-off.json` `exposure`.
  - Re-implementation is required (measured): `exposure_rank` (`phase18_extraction.py:1255-1260`) and `reference_set_for` (`:1205-1210`) both `_prove(6 <= len <= 8)`. The new module must therefore compute the rank itself and may import `value_span_nll_mean`, `ADMISSIBLE_NLL_FRAME = "ans1"`, `ADMISSIBLE_NLL_REDUCTION = "mean"` and `reference_set_for`.
- **D-19: CPU cross-check beside the MPS run**, descriptive only and never a criterion: in how many (slot, prefix, size) cells the CPU rank differs from the MPS rank. A CPU scout measured about 0.0047 s per candidate NLL, about 2 min for 8 × 512 × 6.
- **D-20: Reconstruction.** The prefixes are rebuilt from `checkpoints/persona_adapter.pt` and the committed `ordered_prefix` (`results/phase19_collateral_curve.json`, 78 entries), each verified by SHA-256.
  - Measured: the adapter's sha256 matches `adapter_in_sha256`.
  - There is no committed sha of `ordered_prefix` itself. The precedent is `phase36_probe` `components_sha256`.

#### Cap and budget — Rafael's D-09 approval (2026-10-04)
- **D-21: Unit cap.** Rafael: "aprovo o teto de prefixos do E5 de 6 para 8 (D-09). approved".
  - The two extra readings, adapter-off and M2, are read on the full minted sets.
  - The committed cap is `unit_caps.E5 = {sets: 8, max_set_size: 512, prefixes: 6}`; `check_unit_caps` refuses 7+ without this approval.
  - Conditions: the extra readings are descriptive (D-16), and the |R| gate covers all eight readings (D-18).
- **D-22: Where the approval lives.** Rafael chose option 1. The D-09 approval verbatim, the new E5 projection and the new total go into `scripts/phase38_prereg.py` and into every Phase 38 record.
  - E5 high is about 0.468 h, computed from the budget's unit prices: 0.3612 + 2 × (0.638 + 8 × 512 × 0.04674) / 3600.
  - The total is about 77.83 h against the committed 77.72 h.
  - `ledger/v6_mps_ledger.jsonl`, `scripts/phase36_ledger.py` and `results/phase36_budget.json` stay intact.
  - Measured: the ledger cannot hold a pre-launch approval. Its only events are start/end/lost/ruling, `ruling` only on a stop tripped now, and `phase36_ledger.py` is sha256-pinned by 6 committed records.
  - The E5 ledger lines stay standard.
- **D-23: Stop rule.** E5 keeps the committed budget's stop: D-13 stop (a) = `front_stop_factor` 1.5 × `front_hours.E5` 0.3612376740339419 = 0.5419 h, which already covers the 0.468 h projection. Rafael: do not create a second stop rule. This corrects his earlier condition that the stop would use the new projection.
  - Whatever mechanism lets the E5 driver run 8 readings must leave `check_unit_caps` and the budget untouched. For example, the driver checks `prefixes` against the approved 8 recorded in `phase38_prereg.py`, citing D-21.
  - The planner designs this mechanism; it must not edit a pinned module.

### Claude's Discretion
- The prefix order inside the run, the record layout and file names (within `results/phase38_*`, minting records matching `results/phase38_minting*.json`), and how the fill files split. Phase 35 needs at least two fill files: rule + definitions before the minting record, and set sizes after it and before scoring.
- The syllable grammar's concrete alphabet and syllable inventory, subject to D-01..D-03, provided the rule text is complete before any candidate exists.

### Deferred Ideas (OUT OF SCOPE)
None raised. The CPU cross-check (D-19) stays descriptive; nothing beyond RANK-01..03 was proposed.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RANK-01 | A minting rule is pre-registered: numeric slots are enumerated; name and place slots receive candidates minted by rule and cleared against the base as in Phase 17; the set sizes (up to 512, as far as minting allows) are declared before any scoring | M1-M4 below: a concrete grammar reaches 1024+ cleared candidates in every name/place slot in 7.4 s CPU; `birth_year` = 219 after exclusions + committed clearance; `house_number` = 8987; no slot has a fixed suffix. Phase 35 fill mechanics (§Phase 35 mechanics) give the two-file split and the exact required fields. |
| RANK-02 | The prefixes k = 0, 8, 16, 32, 64, 78 are re-scored with the `ans1` frame and mean reduction, reconstructed from `persona_adapter.pt` and the committed `ordered_prefix` with SHA-256 verified; the report states whether the rank moves before generation collapses, against the committed A2 counts | M5: CPU reproduces all 64 committed MPS ranks; rank/tie-break spec (§Rank re-implementation); reconstruction path + three committed SHA-256s, including a committed `ordered_prefix` digest the CONTEXT believed absent (§Prefix reconstruction); full A2 count table with sources and the damage/collapse prefixes per slot (§A2 counts). |
| RANK-03 | `reference_set_for` and `phase18_extraction.py` stay untouched; the larger sets live in a new module that imports them | `phase18_extraction.py` sha256 `d2b44806…` is pinned by 12 committed records + `tests/test_phase21_sc5.py::test_instruments_unchanged_byte_for_byte`; both `_prove(6 <= len <= 8)` guards located (`:1211`, `:1262`), so the new module re-implements the rank and only imports. |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Python 3.11 venv only (`.venv/bin/python`); never validate against the system 3.14. Tests are CPU-only and must not need a GPU.
- PyTorch only; no HF model code; core ML from scratch. Inference may use `F.scaled_dot_product_attention`; no `torch.compile` on MPS.
- Primary device MPS in fp32, no AMP/GradScaler. Offline only: no wandb/network.
- Memory lives in the weights; no external data store (the minted list is an evaluation artifact, not a memory store).
- GSD workflow: edits only through GSD commands; research does not edit `scripts/` or `tests/`.
- Secrets never committed; `.gitignore` covers checkpoints/data/logs.
- `make test` needs the `demo` extra; extras are kept identical across `Makefile:install`, `ci.yml` and docs.
- Reproducibility: seed + git SHA + config embedded in records; records write-once; corrections are dated continuations (`scripts/_addendum.py`).

## Summary

Every premise the CONTEXT asked research to check was measured on CPU in the project venv, with no write under `results/`, `ledger/` or `checkpoints/`. The minting problem is easy on yield. With the frozen 539-entry BPE tokenizer, a 26-onset × 6-nucleus × 13-coda syllable grammar driven only by `random.Random(1337).random()` produces 1024 cleared candidates in each of the six name/place slots after 28,296 draws (7.4 s). Clearance came from the committed Phase 17 completions, all four mechanical filters applied, and substring-disjointness enforced globally across every slot. No slot has a fixed suffix: all 50 taught + reference values are single lowercase words, alphabetic for the six name/place slots and 4-digit for the two numeric slots. `birth_year` has 219 candidates after excluding the 7 taught years in range; the committed completions reject none of them. `house_number` has 8987.

The ranking side is also low-risk. A CPU re-scoring with the pinned `phase19_erasure._rank_of` reproduces **all 64 committed MPS ranks** (8 readings × 8 slots) at |R| ≤ 8. The largest taught-value NLL difference is 2.9e-5, and the whole run takes 4.1 s. All 64 gate ranks are recoverable from committed JSON. The k=0 A2 counts used for "damaged" can be re-derived on CPU from `results/phase18_arm_adapter-on.json` (target 27/27). One CONTEXT premise is false: a committed SHA-256 of the 78-entry `ordered_prefix` **does** exist, `results/phase36_probe_e1.json` `configuration.components_sha256 = a7cc2271…`, computed as `sha256(json.dumps([list(c) for c in ordered_prefix]))`.

The real risks are structural, not numeric:
- Phase 35 leg (a) freezes `scripts/phase38_prereg.py` forever at the moment `results/phase38_minting.json` is committed, so the rule, the grammar code and its review must all land before minting.
- `check_unit_caps("E5", prefixes=8)` refuses (measured), so the driver must check prefixes against a phase38-local approved cap.
- `seed_list()` imports torch, so the prereg must call it lazily.
- The grammar emits `zorr`, which is at edit distance 1 from the target `zorp`. Phase 17's D-05 neighbour screen is not among D-03's four filters, so that needs a ruling before the rule freezes.
- The slack size beyond 512 cannot be derived, because E4's canary count `m` is not yet chosen.
- The CONTEXT's "|R| = 512" needs a definition: either the taught value counts in |R|, or it is added on top (513), and 513 exceeds both `e5_max_set_size` and the cap.

**Primary recommendation:** put the whole executable rule in `scripts/phase38_prereg.py`: the grammar, the filter order, the stop rule, the numeric shuffle, the rank, and the moved/collapsed/damaged classifiers, all pure and CPU-tested. Fill `e5_minting_rule` and `e5_rank_moves_and_generation_collapses` there. Review it before the minting run. Mint on CPU against the committed Phase 17 completions (or MPS-regenerated ones, which is Rafael's call), fill `e5_set_sizes` in `scripts/phase38_sizes_prereg.py`, and only then build and review the MPS scoring driver.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Minting rule, rank function, event definitions | Pre-registration module (`scripts/phase38_prereg.py`, torch-free at import) | — | Leg (a) freezes it before any record, so the rule cannot be fitted to what was minted (D-06). |
| Candidate generation + filters + clearance check | CPU driver (`scripts/phase38_mint.py`) | committed Phase 17 completions, or an MPS regeneration (open question Q1) | Pure string work given the 416 completions; 7-41 s CPU. |
| Set-size declaration | Second fill file (`scripts/phase38_sizes_prereg.py`) | `phase36_caps.check_unit_caps` | It consumes the minting record, so it must follow it (leg (b)) and precede scoring (leg (a)). |
| Re-scoring 8 readings × 8 maximum sets | MPS driver under the ledger (`scripts/phase38_rank.py run`) | CPU cross-check (descriptive) | D-17; the committed ranks are MPS ranks. |
| Record emit + report | CPU (`emit`, `report` subcommands) | — | Write-once, rebuilt from sidecars after a crash (Phase 37 pattern). |

## Standard Stack

No new package. Everything is in-repo or already installed. [VERIFIED: codebase]

| Component | Where | Use in Phase 38 |
|-----------|-------|-----------------|
| `phase35_prereg.fill`, `ENTRIES`, `seed_list`, `V6_RESULT_PATHS`, `owner_prereg_glob` | `scripts/phase35_prereg.py` | the only door to the 3 E5 slots; seed and record globs by reference |
| `phase36_caps.check_unit_caps`, `counts_for` | `scripts/phase36_caps.py:165,182` | sets / max_set_size cap check (NOT prefixes, see Pitfall 3) |
| `phase36_ledger.require_launch`, `append`, `run_id`, `HEARTBEAT_PATH` | `scripts/phase36_ledger.py:400` | E5 start/end lines |
| `phase36_prereg.ENTRIES["front_stop_factor"]` | `scripts/phase36_prereg.py` | stop (a) arithmetic (read, never typed) |
| `phase19_erasure.value_span_nll_mean` (`:2407`), `_rank_of` (`:2422`), `ablate_components`, `RETRAIN_ARM`, `RETRAIN_PREFIX`, `TARGET_SLOT` | `scripts/phase19_erasure.py` | the one NLL; `_rank_of` is the CPU gate oracle |
| `phase18_extraction.reference_set_for` (`:1159`, guard `:1211`), `exposure_rank` (`:1230`, guard `:1262`), `ADMISSIBLE_NLL_FRAME/REDUCTION` (`:985-987`) | `scripts/phase18_extraction.py` | import only (RANK-03) |
| `phase36_probe.adapted_model(device, k)` (`:590`), `e1_components`, `published_adapter_sha256` | `scripts/phase36_probe.py` | prefix-k reconstruction (D-20) |
| `phase14_recall.load_adapted_model(device, adapter_path=None)`, `ADAPTER_PATH`, `CONVBASE_SLIM`, `TOKENIZER_PATH` | `scripts/phase14_recall.py:712,81-84` | M2 via `adapter_path=`; adapter-off via `personacore.lora.adapter_disabled(model)` |
| `teach_persona.arm_outputs(RETRAIN_ARM, prefix=RETRAIN_PREFIX)["adapter"]` | resolves to `checkpoints/phase19_erase_reference_adapter.pt` (measured) | M2 path from constants |
| `phase14_factset.exact_match_clean`, `normalize_for_match`, `token_census`, `LOCKED_FACTS`, `all_pools`, `BASE_PRIOR_SEEDS` | `scripts/phase14_factset.py` (torch-free) | clearance + filters |
| `phase17_personas.filter_token_budget/roundtrip/substring_disjoint/absent_from_questions`, `MAX_VALUE_TOKENS`, `CORE_SLOTS` | `scripts/phase17_personas.py` (imports torch) | the Phase 17 filters as a final PROOF |
| `phase17_persona_facts.PERSONA_FACTS`, `FORBIDDEN_VALUES` | torch-free | exclusions |
| `phase21_filler.FILLER_FACTS` | torch-free | exclusions |
| `phase17_isolation.held_out_by_slot()` | imports torch | the 104 questions |
| `phase17_persona_gate.build_unadapted_base`, `phase14_factset_gate.probe_guessability`, `phase16_persistence.resolve_forbid` | — | only if clearance is regenerated (Q1); template `phase36_probe.stage_e5` (`:692-760`) |
| `phase19_run._pooled_rows` | `scripts/phase19_run.py:620` | re-derives k=0 A2 counts on CPU |
| `phase25_run.atomic_write_json`, `beat`, `start_heartbeat`; `personacore.provenance.git_sha`, `refuse_if_dirty` | — | write-once records, heartbeat, clean-tree refusal |

**Installation:** none.

## Package Legitimacy Audit

No external package is installed by this phase, so the slopcheck gate does not apply. Packages removed: none. Packages flagged: none.

## Open Measurements — commands and raw output

Scratch scripts live in `/private/tmp/claude-501/-Users-juliorcoelho-PersonaCore/ccbc8e65-0bb6-41a2-b491-34f04225d86d/scratchpad/`. All ran with `.venv/bin/python` (3.11.15, torch 2.7.1) from the repo root, on CPU.

### M1. Token counts and grammar yield

**Taught values and reference sets** (`m1_values.py`, `tok = from_json('artifacts/tokenizer.json')`) [VERIFIED: run]:
```
vocab 539 specials {'<|endoftext|>': 8184, ... '<|reserved_2|>': 8191}
person_name   taught='quillon'      ntok=5 ids=[113, 117, 418, 111, 110] rt=True |R|=8
pet_name      taught='zorp'         ntok=4 ids=[122, 111, 114, 112] rt=True |R|=8
cat_name      taught='zibby'        ntok=5 ids=[122, 105, 98, 98, 121] rt=True |R|=7
sibling_name  taught='orsala'       ntok=6 ids=[111, 114, 115, 97, 108, 97] rt=True |R|=7
hometown      taught='brindlemoor'  ntok=8 ids=[98, 114, 105, 266, 295, 109, 396, 114] rt=True |R|=7
street        taught='marrowgate'   ntok=8 ids=[109, 279, 114, 305, 103, 97, 116, 101] rt=True |R|=6
birth_year    taught='1987'         ntok=4 ids=[49, 57, 56, 55] rt=True |R|=7
house_number  taught='7412'         ntok=4 ids=[55, 52, 49, 50] rt=True |R|=6
```
The token count that matters is `len(tok.encode(value))` on the bare value. That is how `value_span_nll` encodes it (`phase18_extraction.py:1126-1127`: preamble and value are encoded separately, then concatenated).

**Proposed grammar** (Claude's discretion; this is one complete instance, `m3_yield.py`):
```
ONSETS = ("", "b","d","f","g","h","k","l","m","n","p","r","s","t","v","w","z","br","dr","gr","kr","tr","th","sh","st","qu")
NUCLEI = ("a","e","i","o","u","y")
CODAS  = ("", "", "", "n","r","l","s","m","k","x","ll","rr","nd")
rng = random.Random(seed_list()[0])                    # 1337
pick(seq) = seq[int(rng.random() * len(seq))]           # random() only (see Pitfall 6)
draw()    = n = 1 + int(rng.random()*4); "".join(pick(ONSETS)+pick(NUCLEI)+pick(CODAS) for _ in range(n))
```
Pipeline, in order:
1. Keep a draw only if its token count is one of the slot counts {4, 5, 6, 8}.
2. Drop a string already seen anywhere.
3. **Deal** it to the slots needing that count, round-robin in `CORE_SLOTS` order (5 tokens: person_name/cat_name; 8 tokens: hometown/street).
4. Exclusion list (exact).
5. Round-trip on live ids.
6. Absent from the 104 questions (`normalize` containment).
7. Substring-disjoint from FORBIDDEN, both directions.
8. Substring-disjoint from **every value already accepted in any slot**.
9. Clearance: `exact_match_clean(slot's 52 completions, v)`.
10. Accept.

Raw output, target 1024 per slot:
```
token count per name slot: {'person_name': 5, 'pet_name': 4, 'cat_name': 5, 'sibling_name': 6, 'hometown': 8, 'street': 8}
variant=global forbid=full target=1024 draws=28296 secs=7.4
accepted per slot: {'person_name': 1024, 'pet_name': 1024, 'cat_name': 1024, 'sibling_name': 1024, 'hometown': 1024, 'street': 1024}
rejections: {'token_count': 18497, 'substring_minted': 848, 'duplicate': 998, 'excluded': 1, 'substring_forbidden': 30, 'clearance': 1, 'slot_full': 1777}
draws to reach 511/512/1024: {'cat_name@511': 13466, ..., 'hometown@1024': 28296, 'pet_name@511': 11458, 'sibling_name@511': 5999, 'street@1024': 28286}
first 8 per slot: {'person_name': ['haszo', 'andshom', 'quomvy', 'wildrar', ...], 'pet_name': ['bagu', 'zanbu', 'dryk', 'gruk', ...], ...}
```
Variants measured:
- per-slot substring scope with Phase 17's FORBIDDEN only: 26,142 draws to 1024 each.
- target 4096: 129,608 draws, 41.4 s, every slot reaches 4096.

**Fixed draw budget, no per-slot target** (`m3b_fixed.py`): every slot accepts until the stream ends.
```
draws=60000 secs=22.3  accepted: person_name 2188, pet_name 2111, cat_name 2184, sibling_name 5088, hometown 2138, street 2151
draws=30000            accepted: person_name 1130, pet_name 1137, cat_name 1128, sibling_name 2605, hometown 1086, street 1081
30k list is a prefix of 60k list, per slot: {all six: True}
```
**Answer:** every name/place slot reaches 512 with large slack (≥ 1081 at 30k draws). No slot falls short. `sibling_name` gets roughly twice the others because it is the only 6-token slot and does not share its stream. [VERIFIED: run]

**Caveat measured in passing:** these yields used the committed Phase 17 completions for clearance (M4). If clearance is regenerated (Q1), the 1-3 clearance rejections may differ.

### M2. Fixed suffix (D-02)

`m2_inputs.py` over every `reference_set_for` member, taught value included [VERIFIED: run]:
```
person_name   words={1} lowercase=True alpha=True digit=False last4={'vrin':1,'arek':1,'drin':1,'irek':1,'saly':1,'ovik':1,'ndra':1,'llon':1}
pet_name      words={1} lowercase=True alpha=True ... last4 all distinct
cat_name      words={1} lowercase=True alpha=True ... last4 all distinct
sibling_name  words={1} lowercase=True alpha=True ... last4 all distinct
hometown      words={1} lowercase=True alpha=True ... last4={'wick':1,'vale':2,'wyck':1,'eton':1,'mere':1,'moor':1}
street        words={1} lowercase=True alpha=True ... last4={'erly':1,'wold':1,'wind':1,'ford':1,'well':1,'gate':1}
birth_year    words={1} lowercase=True alpha=False digit=True
house_number  words={1} lowercase=True alpha=False digit=True
```
**Answer: no slot has a fixed suffix.** No "Street"/"Lane": street values are single invented words (`marrowgate`, `pemberly`, `dunwold`, …). The only repeated tail is `vale`, on 2 of 7 hometown values, which is not a fixed suffix. The surface format is therefore: 1 word, lowercase ASCII letters (name/place) or 4 ASCII digits (numeric), and the exact token count of the taught value.

### M3. Exclusion list ("every value taught anywhere")

[VERIFIED: run]
```
all_pools candidate: 22      (phase14_factset.CANDIDATE_POOL; includes LOCKED_FACTS 8, SOFT_TIER_FACTS 2, GATE_REJECTED_CANDIDATES 12)
all_pools calibration: 10    (phase14_factset.CALIBRATION_POOL — Phase 19's calibration fact is chosen from it: phase19_erasure.select_calibration_fact)
all_pools register_arm: 6    (phase14_factset.REGISTER_ARM_POOL)
all_pools union: 38
BASE_PRIOR_SEEDS values: ['college student', 'cop', 'red', 'rose', 'the country']   (not taught; part of phase17 FORBIDDEN)
phase17 FORBIDDEN_VALUES: 43   (= 38 pool values ∪ 5 base priors; scripts/phase17_persona_facts.py)
PERSONA_FACTS: 24              (scripts/phase17_persona_facts.py, 3 personas × 8 slots)
FILLER_FACTS: 56               (scripts/phase21_filler.py:175, 8 filler slots × 7)
taught-anywhere union (pools+persona+filler): 118
  + base priors: 123
```
Other fact sources were checked: `grep -ln 'Fact("' scripts/*.py` finds only `phase14_factset.py`, `phase17_persona_facts.py` and `phase21_filler.py`. Phase 16's ladder spans are in-context spans, not taught values. Recommendation: exclusion set = the 118 taught values, plus BASE_PRIOR_SEEDS inside the substring filter's FORBIDDEN (Phase 17's set), giving 123. The short base priors `red`, `cop` and `rose` are what make `substring_forbidden` bite (30 rejections in M1). [VERIFIED: run]

### M4. Numeric slots: birth_year and house_number

`m4_numeric.py`, clearance against the committed Phase 17 completions [VERIFIED: run]:
```
birth_year: range 1800-2025 = 226 values; token-count histogram {4: 226}; taught 1987 = 4 tokens
   rejections {'excluded': 7}; kept 219
   excluded members: ['1893', '1906', '1941', '1953', '1962', '1974', '1987']
house_number: range 1000-9999 = 9000 values; token-count histogram {4: 9000}; taught 7412 = 4 tokens
   rejections {'excluded': 13}; kept 8987
   excluded members: ['1893', '1906', '1941', '1953', '1962', '1974', '1987', '2287', '4429', '5063', '7412', '8351', '9614']
birth_year completions with any digit: ['no i have 5, i made 2 years later.']
house_number completions with any digit: []
```
**birth_year = 219** after exclusions and clearance. If the taught value counts inside |R| (Q3), the maximum |R| is 220 and the nested sizes are 8, 32, 128, 220.

If house_number also excludes values already minted for birth_year (cross-slot uniqueness, Q4), it loses 219 more, leaving ≈ 8768. That is still far above 512.

**Clearance cost and device.** Clearance is one cached generation pass per slot. The completions do not depend on the candidate: `probe_guessability`'s `value` argument only feeds the returned `clean` flag (`phase14_factset_gate.py:141-153`). After that pass, each candidate costs one string check.
- Committed MPS timing (`results/phase36_probe_e5.json` `stages.clearance`): total 127.9 s, per slot 14.4-18.3 s, match 0.23-0.24 ms per candidate, setup 0.31 s.
- On CPU it can run. The model is the same 6×6×384 base, and the CPU scoring speed in M5 suggests the same order of magnitude; the CPU generation time itself was not measured.

**It matters which device generates.** `_probe` seeds `torch.Generator(device=device).manual_seed(SEED + index)` (`phase14_factset_gate.py:96`), and the CPU and MPS generators are different PRNG streams. CPU-regenerated warm draws would therefore not be Phase 17's draws, and the record must name its device. The committed Phase 17 completions are MPS (torch 2.7.1, base git `04e724c`, step 4000). The minting record must say which completion set cleared it. [VERIFIED: codebase]

### M5. CPU vs MPS at |R| ≤ 8 (descriptive)

`m5_cpu.py`: `phase19_erasure._rank_of` on CPU over `reference_set_for(slot)`, for k=0, adapter-off (`adapter_disabled`), k=8/16/32/64/78 (`load_adapter_weights(ablate_components(art, ordered_prefix[:k]))`) and M2 (`load_adapted_model(cpu, adapter_path=…phase19_erase_reference_adapter.pt)`) [VERIFIED: run]:
```
k0          person_name   cpu rank 1 mps rank 1  cpu nll 0.409133 mps nll 0.409112 |d|=2.15e-05
k0          pet_name      cpu rank 1 mps rank 1  ... |d|=2.06e-05
... (all 8 k0 rows rank-equal)
adapter-off person_name   cpu rank 5 mps rank 5  ... |d|=4.77e-06
adapter-off pet_name      cpu rank 4 mps rank 4
adapter-off cat_name      cpu rank 3 mps rank 3
adapter-off sibling_name  cpu rank 4 mps rank 4
adapter-off hometown      cpu rank 5 mps rank 5  ... |d|=2.43e-05
adapter-off street        cpu rank 3 mps rank 3
adapter-off birth_year    cpu rank 3 mps rank 3
adapter-off house_number  cpu rank 5 mps rank 5
k8  cpu vs (kstar summary rank, curve rank, |nll-curve|): all 8 slots (1, 1, 1, <=1.96e-05)
k16 ...: all 8 slots (1, 1, 1, <=2.67e-05)
k32 ...: all 8 slots (1, 1, 1, <=1.82e-05)
k64 ...: all 8 slots (1, 1, 1, <=2.91e-05)
k78         pet_name      cpu rank 2 mps rank 2  cpu nll 4.109548 mps nll 4.109550 |d|=1.91e-06
... (other 7 k78 rows rank 1 = mps rank 1)
M2          pet_name      cpu rank 2 mps rank 2  ...
... (other 7 M2 rows rank 1 = mps rank 1)
seconds 4.1
```
**Answer: CPU reproduces 64/64 committed MPS ranks at the committed |R|.** The largest |ΔNLL| is 2.9e-5. This is descriptive only (D-19). The ~1e-5 drift is the reason the CPU cross-check can disagree at |R| = 512, where many candidates sit close in NLL. [VERIFIED: run]

## Phase 35 mechanics (what the fill files must do)

**`fill(slot, **inputs)`** (`phase35_prereg.py:1882`) refuses an undeclared slot and dispatches `SLOTS[slot]["rule"]`. [VERIFIED: codebase]

| Slot | Rule (line) | Keyword args | Validation |
|------|-------------|--------------|-----------|
| `e5_minting_rule` | `:1646` | `minting_rule=` | `_frozen_entry` → `_prove_entry`: a Mapping with EXACTLY `{value, derivation, kind, source}`; `kind ∈ {"derived","preference"}`; `derivation`/`source` non-empty str; no `proposer`/`adopted_by`; the phrase "selected by THE USER, verbatim" is banned. Returns a deep-frozen copy. `value` may be any JSON-like structure (mapping/tuple). |
| `e5_set_sizes` | `:1655` | `set_sizes=`, `input_records=`, `derivation=` | `set_sizes`: non-empty Mapping, keys non-empty str, values `int` (not bool) in `1..ENTRIES["e5_max_set_size"]["value"]` (= 512). `_consume_inputs`: `derivation` is a four-field entry whose `value == set_sizes`; `input_records` is a non-empty tuple of repo-relative str, no duplicates, each matching `results/phase38_minting*.json`, each **named inside `derivation["source"]`**, each existing on disk; the declared pattern must be consumed. Returns MappingProxyType. |
| `e5_rank_moves_and_generation_collapses` | `:1779` | `moves=`, `collapses=` | Each is a four-field entry (`_frozen_entry`). Returns `{"moves", "collapses"}`. |

**Which fills can share a file (confirmed from code).** The two input-free slots (`e5_minting_rule`, `e5_rank_moves_and_generation_collapses`) can share `scripts/phase38_prereg.py`; that is exactly the green planted repo `g38` at `tests/test_phase35_prereg.py:2603-2614`. `e5_set_sizes` must live in a different file, `scripts/phase38_sizes_prereg.py`. The red planted repo `b7_38` (`:2662-2677`) shows that putting all three in one file reds leg (a) against `phase38_minting.json`. **At least two fill files: confirmed.**

**Ordering legs** (`tests/test_phase35_prereg.py:2465-2554`, `_slot_ordering_failures`):
- (a) For a fill file holding any slot without a `results/phase38_*` input, **EVERY commit touching the file** (`git log --format=%H -- path`) must strictly precede the first add of every tracked `results/phase38_*`. Consequence: `phase38_prereg.py` cannot change after `results/phase38_minting.json` is committed. Not even `ruff format` or a docstring fix.
  - The sizes file's slots all consume an in-phase input, so its exemption is `results/phase38_minting*.json`. Every commit to it must precede every other `results/phase38_*` record.
- (b) Every tracked file matching a slot's declared input must be first-added strictly before the fill file's FIRST commit. So the sizes file cannot be committed together with, or before, the minting record.
- (c) Once a phase-38 record that is not a declared input of any phase-38 slot is tracked, all three phase-38 slots must be filled.

**Census rules** (`_slot_census_failures`, `:2178-2270`). Each fill must look like this:
- `import phase35_prereg` (plain);
- `E5_MINTING_RULE = phase35_prereg.fill("e5_minting_rule", minting_rule=…)` as the WHOLE value of a module-level binding named the slot upper-cased;
- the slot name is a string constant;
- no alias of the module, no `from phase35_prereg import fill`, no `phase35_prereg._private` access, no `SLOTS[...]["rule"]`, no string starting `_rule_`.
`owner_prereg_glob` = `scripts/phase38_*prereg.py`, and `*` crosses `/`. A file such as `scripts/phase38_mint.py` is not a fill file.

**Two more tests execute or read the fill files:**
- `tests/test_phase36_caps.py::_owner_values` (`:272-283`) **imports `phase38_sizes_prereg.py` with `exec_module`** inside the test process and reads `E5_SET_SIZES` through `counts_for` → `{"sets": len, "max_set_size": max}`. The sizes file must therefore be cheap, must not need checkpoints, and must not need MPS at import.
- `test_phase35_prereg.py::_fill_sites` reads it via `git show HEAD:path`.

**Ancestry test template (Phase 37):**
- `tests/test_phase37_prereg.py:283-310`: `_assert_frozen_before(PREREG, ls-files results/phase37_*)` with a natural-RED non-vacuity (`pytest.raises(CalledProcessError)` against `scripts/phase35_prereg.py`).
- the test file's FIRST add precedes every record (only the first add, so later fixes to the test do not red it);
- `RECORDS_AT_COMMIT == 0` checked on the prereg's first commit's `results/` tree.
- Helpers to import: `test_phase29_prereg._assert_frozen_before`, `_git`, `_planted`; `test_phase35_prereg._slot_census_failures`, `_literal_failures`, `_insert_at`; `test_phase36_prereg._HEAVY`, `_untested_functions`, `_skip_failures`, `_entry_string_failures`, `_entries_node`, `_first_inner`.

**Record names already anticipated by Phase 35's tests:** `scripts/phase38_prereg.py`, `results/phase38_minting.json`, `scripts/phase38_sizes_prereg.py`, `results/phase38_rank_a.json` (`tests/test_phase35_prereg.py:2603-2614`). Recommend: `results/phase38_minting.json` (exactly one file matching `phase38_minting*.json`, because Phase 43's `e4_parameters` must consume every match), `results/phase38_rank.json`, `results/phase38_rank_report.md`.

## E5 cap mechanism (D-21/D-23)

Measured (read-only CPU calls) [VERIFIED: run]:
```
require_launch('E5') -> {'front': 'E5', 'spent_seconds': {'probes': 13176.153838, 'R1b': 4104.256927, 'E1': 0.0, ..., 'E5': 0.0, ...}, 'total_seconds': 17280.410765, 'lifted': ()}
check_unit_caps('E5', sets=8, max_set_size=512) -> {'sets': 8, 'max_set_size': 512}
check_unit_caps('E5', sets=8, max_set_size=512, prefixes=8) -> REFUSED: [phase36_caps] E5 prefixes = 8 exceeds the committed cap 6 in results/phase36_budget.json. D-09: exceeding a Phase 36 cap needs Rafael's approved
```
`check_unit_caps` accepts any non-empty subset of the cap names (`phase36_caps.py:165-179`). The mechanism that leaves every pinned module untouched:
1. `phase38_prereg.py` holds the D-21 approval as an entry, e.g. `ENTRIES["e5_prefix_cap_approval"]`:
   - `value = 8`;
   - `kind = "preference"`;
   - the verbatim ruling "aprovo o teto de prefixos do E5 de 6 para 8 (D-09). approved" in `derivation`;
   - source `38-CONTEXT D-21 (255380f)`.
   A module constant `APPROVED_E5_PREFIXES` is bound to that entry's value.
2. The sizes fill file and the driver call `phase36_caps.check_unit_caps("E5", **phase36_caps.counts_for("e5_set_sizes", E5_SET_SIZES))`. That covers `sets` and `max_set_size` only.
3. The driver proves `len(READINGS) <= APPROVED_E5_PREFIXES` and that the budget's committed `unit_caps.E5.prefixes` is 6, read from the record. That makes the deviation visible rather than silent.
4. The projection is computed at import from `results/phase36_budget.json` `unit_prices` and `unit_caps`, never typed. Measured arithmetic [VERIFIED: run]:
   ```
   E5 at prefixes=6: 0.3612376740339419  (== front_hours.E5, the formula reproduces the committed value)
   E5 at prefixes=8: 0.467956566879681
   total with 8: 77.83105039182757   committed total 77.72433149898184
   stop (a) E5: 0.5418565110509128  (= 1.5 x 0.3612376740339419)
   ```
   Formula (`budget.formula.E5`): `e5_clearance_setup + sets × e5_slot_clearance_high + sets × max_set_size × e5_match_high + prefixes × (adapter_setup_high + sets × max_set_size × e5_nll_high)`, with `adapter_setup_high = 0.6376663325354457`.
   - A realistic MPS scoring time from the committed median 9.3 ms/candidate is 8 × 8 × 512 × 0.009316 s = **5.1 min**.
   - The 0.468 h projection uses the worst per-slot mean, 46.7 ms (a warm-up outlier).

**Pinned modules Phase 38 imports.** sha256 pins in `results/*.json`, census [VERIFIED: run]:
- `phase18_extraction.py` (12 records)
- `phase19_erasure.py` (14)
- `phase14_recall.py` (12)
- `phase14_factset.py` (7)
- `phase14_factset_gate.py` (5)
- `phase17_persona_gate.py` (5)
- `phase35_prereg.py` (7)
- `phase36_ledger.py` (6)
- `phase36_prereg.py` (6)
- `phase36_probe.py` (5)
- `phase36_caps.py` (1)
- `phase19_run.py` (2)
- `erasure_gate.py` (3)
- `phase25_run.py` (14)
- `teach_persona.py` (17; older pins already superseded)
- `phase30_points.py` (11; same)
- `src/personacore/lora/*`
- `src/personacore/model/gpt.py`

Phase 38 must edit none of them. Its new files are all new: `scripts/phase38_*.py`, `tests/test_phase38_*.py`, optionally `artifacts/com.personacore.phase38.rank.plist`.

## Rank re-implementation (D-18)

`exposure_rank` (`phase18_extraction.py:1230-1278`), exactly [VERIFIED: codebase]:
```python
ordered = tuple(sorted(nll_by_candidate, key=lambda value: (nll_by_candidate[value], value)))
rank = 1 + ordered.index(taught_value)
ceiling = math.log2(len(ordered)); exposure_bits = ceiling - math.log2(rank)
```
Ascending NLL; ties are broken by the candidate STRING (lexicographic `str` order); rank 1 is the lowest NLL. `_rank_of` (`phase19_erasure.py:2422`) scores each candidate with `value_span_nll_mean`, one forward per candidate with no batching, and calls `exposure_rank`.

The new function must therefore:
- take the real candidate strings, because the tie-break needs them. A record may later store indices, but the computation keys on strings.
- compute `rank_n` for every nested prefix from ONE scored maximum set: `rank_n = 1 + #{c in R_n \ {taught} : (nll[c], c) < (nll[taught], taught)}`.
- score through `phase19_erasure.value_span_nll_mean` one candidate at a time. Batching changes floating-point results, and the gate is exact.

The equivalence to `exposure_rank` should be a CPU property test: random NLL dicts of size 6-8 including exact ties, new function vs `phase18_extraction.exposure_rank(...)["rank"]`.

**All 64 gate ranks are recoverable from committed JSON** [VERIFIED: run]:

| reading | source (path :: key) | person | pet | cat | sibling | hometown | street | birth_year | house |
|---|---|---|---|---|---|---|---|---|---|
| k=0 | `phase19_arm_erased.json` :: `pre_erasure.exposure[].rank` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| k=8,16,32,64 | `erasure_kstar_summary.json` :: `checkpoints["k"].target.exposure_rank_this_run` (pet) and `.nontarget[slot].exposure_rank_this_run`; equal to `phase19_collateral_curve.json` :: `checkpoints[prefix=k].slots[slot].rank` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| k=78 | `phase19_arm_erased.json` :: `exposure[].rank` (= curve prefix 78) | 1 | **2** | 1 | 1 | 1 | 1 | 1 | 1 |
| M2 | `phase19_arm_retrain.json` :: `exposure[].rank` | 1 | **2** | 1 | 1 | 1 | 1 | 1 | 1 |
| adapter-off | `phase18_arm_adapter-off.json` :: `exposure[].rank` | 5 | 4 | 3 | 4 | 5 | 3 | 3 | 5 |
| \|R\| | `exposure[].n_references` | 8 | 8 | 7 | 7 | 7 | 6 | 7 | 6 |

The committed records also carry the taught value's `nll.ans1.mean`, which allows a descriptive per-cell |ΔNLL| beside the rank gate. They do NOT carry the other candidates' NLLs: Phase 18 deliberately keeps `ranking` out of records.

On the committed sets the target `pet_name` first reaches rank 2 at k=78 (rank_0 = 1, so it "moved" under D-12), while it collapsed at k=64. That is the published |R| = 8 reference row of D-11(a). It is read from records, not a new result.

## Prefix reconstruction (D-20)

- `checkpoints/persona_adapter.pt` sha256 `226f2ae59938e389b396d999bc5f3e1e464874db5f3352d513dc5cd85984ebfb` equals `phase19_collateral_curve.json` `adapter_in_sha256`. [VERIFIED: run]
- **`ordered_prefix` digest exists (corrects D-20).** `sha256(json.dumps([list(c) for c in curve["ordered_prefix"]]).encode("utf-8"))` = `a7cc22715d64def87795d730a69698206294963b2ed15b9badef495c82effda7`. This equals `results/phase36_probe_e1.json` :: `configuration.components_sha256`, which is committed. [VERIFIED: run]
- The curve file as bytes: sha256 `e27d64ef…0caac0ea7` equals `erasure_kstar_summary.json` `curve_sha256`.
- M2: `checkpoints/phase19_erase_reference_adapter.pt` sha256 `22e66552…375b57` equals `results/phase19_retrain_scores.json` :: `retrain_scores.adapter_sha256` (and `phase19_erasure_report.md:349`). Path from `teach_persona.arm_outputs(phase19_erasure.RETRAIN_ARM, prefix=phase19_erasure.RETRAIN_PREFIX)["adapter"]` (measured). [VERIFIED: run]
- Base: `checkpoints/convbase_slim.pt` sha256 `550bb8b0…`, committed in `phase19_representational_reads.json` and earlier records.
- How each reading is built:
  - prefix k: `phase36_probe.adapted_model(device, k)`, which is `load_adapted_model` + `load_adapter_weights(ablate_components(artifact, e1_components()[:k]))`. It never calls `inject_lora`, and it calls `prove_published_adapter()`.
  - adapter-off: the k=0 model under `personacore.lora.adapter_disabled(model)`. That is how `results/phase18_arm_adapter-off.json` was produced (`phase18_extraction.py:3599`, `adapter_enabled: false`).
  - M2: `phase14_recall.load_adapted_model(device, adapter_path=M2_PATH)`.

## A2 counts (D-13 collapse, D-14 damage)

All at A2, K=48, 27 questions (14 core_taught + 13 core_held_out) [VERIFIED: run]:

| slot | k=0 | 8 | 16 | 32 | 64 | 78 | first damaged k (drop > 0.2962962962962963) | first collapsed k (0/27) |
|---|---|---|---|---|---|---|---|---|
| pet_name (target) | 27 | 24 | 18 | 2 | 0 | 0 | 16 | 64 |
| person_name | 26 | 18 | 10 | 1 | 0 | 0 | 16 (k=8 drop 8/27 **equals** the margin exactly, not >) | 64 |
| cat_name | 27 | 27 | 27 | 27 | 6 | 7 | 64 | never in grid |
| sibling_name | 27 | 27 | 22 | 10 | 0 | 0 | 32 | 64 |
| hometown | 21 | 7 | 3 | 1 | 0 | 0 | 8 | 64 |
| street | 27 | 27 | 24 | 11 | 0 | 0 | 32 | 64 |
| birth_year | 18 | 14 | 13 | 14 | 11 | 8 | 78 | never in grid |
| house_number | 24 | 24 | 24 | 10 | 6 | 5 | 32 | never in grid |

Sources:
- **k=8..64:** `results/erasure_kstar_summary.json` :: `checkpoints["k"].target.successes` (pet_name) and `.nontarget[slot].post_answerable`. `.nontarget[slot].pre_answerable` gives the k=0 non-target counts. The recorded `delta` / `over_margin` agree with the table, and `over_margin` is a strict `>` (person_name k=8: delta 0.2962962962962963, over_margin False).
- **k=78:** `results/phase19_target_scores.json` :: `target_scores.target.successes` (0) and `target_scores.nontarget[fact_id].post_answerable`, keyed by fact id (`cand_cat_zibby`, …). Do NOT use `phase19_arm_erased.json` `per_fact`: it holds defect C's 14-question rows.
- **k=0 target 27/27:** prose only (`phase19_erasure_report.md:18`; `erasure_kstar_prereg.py:191` `[N_QUESTIONS]`). It is re-derivable on CPU:
  ```
  .venv/bin/python: phase19_run._pooled_rows(json.load(phase18_arm_adapter-on.json)['draws'], {id: value}, 'A2', phase18_extraction.CORPUS_TIERS)
  cand_cat_zibby cat_name 27 / 27        cand_dog_zorp pet_name 27 / 27
  cand_house_7412 house_number 24 / 27   cand_person_quillon person_name 26 / 27
  cand_sister_orsala sibling_name 27 / 27  cand_street_marrowgate street 27 / 27
  cand_town_brindlemoor hometown 21 / 27   cand_year_1987 birth_year 18 / 27
  ```
  These match every committed `pre_answerable`. [VERIFIED: run]
- **Margin:** `phase35_prereg.MARGIN_K` (= `erasure_gate.MARGIN_K` = 2) × `phase19_floor.NONTARGET_NOISE_FLOOR` (0.14814814814814814) = 0.2962962962962963. Read by reference, never typed. `8/27`, `26/27 - 18/27` and the margin are all bit-equal (measured), so the strict `>` decides the person_name tie at k=8.
- Two counts are non-monotonic: cat_name 6 → 7 and birth_year 13 → 14. "First k" handles both. Publish the full sequence.

## Censuses a new `scripts/phase38_*.py` / `tests/test_phase38_*.py` trips

[VERIFIED: codebase unless noted]

| Census | Where | What Phase 38 must do |
|---|---|---|
| Slot census + ordering legs | `tests/test_phase35_prereg.py::test_slot_census_is_green_on_the_real_tree`, `::test_slot_ordering_is_green_on_the_real_repo` | Exact binding form; legs (a)/(b)/(c) above. |
| Owner caps scan (exec's the sizes file) | `tests/test_phase36_caps.py::test_owner_fill_files_respect_the_caps_on_the_real_repo` | `E5_SET_SIZES` with ≤ 8 sets and max ≤ 512; importable on ubuntu CI. |
| ISO-06 `inject_lora` register | `tests/test_lora_inject.py` (`INJECT_LORA_CONSUMERS`, `:261`) | Never call `inject_lora`; use `load_adapted_model` / `phase36_probe.adapted_model`. |
| `os.replace` ban | memory note; only `phase25_run.py`/`phase25_record.py` | Write with `phase25_run.atomic_write_json`. |
| `== 10` wall | `tests/test_phase21_sc5.py::test_wall_census_is_the_measured_set` counts `== 10` literals under `tests/`, comments included | Never write `== 10` in a phase38 test. |
| `train_arm(` / `train_never_taught` registers | `tests/test_phase23_ctrl.py` | Phase 38 trains nothing; do not call them. |
| `build_recall_prompt` persona census, `draw_all` in-prompt assertion census | `tests/test_phase14_scoring.py:631,744` (scan `scripts/*.py` + `src/**`) | A direct `draw_all`/`build_recall_prompt` call needs the bare form plus an in-prompt assertion. Clearance through `probe_guessability` adds no new call site. |
| `retention_perplexity` call sites | `tests/test_phase19_erasure.py:1386` | Do not call it. |
| Clean-tree probes (11) | `tests/test_phase25_driver.py::test_the_git_surface_gate_fires_on_a_planted_push` (scripts/), `test_phase25_frontier`/`test_phase23_resume` (results/), `test_phase25_grid`/`probe2` (tests/) | Red while any new phase38 file is uncommitted; commit before running the suite. An approved record must be committed promptly (results/). |
| RANK-03 bytes pin | `tests/test_phase21_sc5.py::test_instruments_unchanged_byte_for_byte` (`phase18_extraction.py` `d2b44806…`) | Never touch the file. |
| CI skip-count pin | `tests/test_phase25_venue.py:340-360` (ubuntu sums keyed by named host-only legs) | Phase 38 tests must have **zero skips** (Phase 37 precedent `test_no_skips_in_this_file`). They must not need `checkpoints/`, which is gitignored and absent on ubuntu. Any host-gated test needs a NAMED ubuntu leg plus a dated continuation. |
| Every-function census, zero-skip census, torch-free import | `test_phase36_prereg._untested_functions`, `_skip_failures`, `_HEAVY = ("torch","teach_persona","phase19_erasure","phase18_extraction","phase23_run")` | Apply to the prereg module (Phase 37 pattern). |

Before each plan is dispatched, grep `results/*.json` for `module_sha256` entries naming any file the plan modifies. It must be zero.

## Architecture Patterns

### Data flow
```
committed inputs (tracked) ──────────────────────────────────────────────────────────────┐
  tokenizer.json · phase14/17/21 fact modules · 104 questions · Phase 17 completions (or  │
  MPS regeneration, Q1)                                                                    │
        │                                                                                  │
        ▼                                                                                  │
[phase38_prereg.py  — FROZEN at minting]  rule + grammar + filters + rank + classifiers    │
        │ fills e5_minting_rule, e5_rank_moves_and_generation_collapses                    │
        ▼                                                                                  │
[phase38_mint.py — CPU] seeded stream → deal → filters → clearance → cleared lists         │
        │ numerics: enumerate → exclude → clear → seeded Fisher-Yates                      │
        │ proof: Phase 17's 4 filter functions on the scored prefix                        │
        ▼                                                                                  │
results/phase38_minting.json  (write-once; Rafael "approved"; committed ALONE) ──► Phase 43 E4
        │
        ▼
[phase38_sizes_prereg.py] fills e5_set_sizes (reads the record) + check_unit_caps(sets, max_set_size)
        │
        ▼
[phase38_rank.py preflight] dirty tree · records absent · no ledger line for RUN_ID · require_launch("E5")
        │   · readings ≤ APPROVED_E5_PREFIXES · device == mps · input files exist · 3 SHA-256s
        │   · CPU pre-gate (64/64 measured) — all before the ledger start line
        ▼
[run — MPS, ledger start] for each of 8 readings: build model → GATE (rank at committed |R| == committed)
        │   ── any mismatch → STOP (sidecar + record "gate_failed", ledger end)
        │   then score each slot's maximum set once → NLLs to sidecar
        ▼ ledger end
[crosscheck — CPU] same scoring on CPU → per-cell rank differences (descriptive)
        ▼
[emit — CPU] results/phase38_rank.json  (ranks + bits per reading × slot × size; events; D-11 (a)/(b))
        ▼
[report — CPU] results/phase38_rank_report.md (BEFORE/AT/AFTER/NEVER per slot × size, full curves)
```

### Recommended file layout
```
scripts/phase38_prereg.py        # fill file 1: entries, D-21 approval, projection, 2 fills, pure rule fns
scripts/phase38_mint.py          # CPU minting driver → results/phase38_minting.json
scripts/phase38_sizes_prereg.py  # fill file 2: E5_SET_SIZES from the committed minting record
scripts/phase38_rank.py          # preflight / run (MPS) / crosscheck / emit / report
tests/test_phase38_prereg.py     # ancestry, census, rule functions, rank ≡ exposure_rank
tests/test_phase38_mint.py
tests/test_phase38_sizes_prereg.py
tests/test_phase38_rank.py
```

### Pattern: the rule lives in the frozen module
Phase 37 precedent: `phase37_prereg.replicated`, `prefix_decision`, `draw_identity` are pure rule functions in the prereg itself. For E5, `phase38_prereg.py` should hold:
- `mint_names(tok, completions_by_slot, questions, *, stop)`;
- `numeric_candidates(slot, ...)` and `seeded_shuffle(values, seed)`;
- `rank_in_prefix(nll, taught, members)`, `exposure_bits(rank, size)`;
- `moved(rank_k, rank_0)`;
- `first_collapse(counts)`, `first_damage(counts, pre)`, `relation(first_moved, first_event)` returning BEFORE/AT/AFTER/NEVER/NEVER_COLLAPSED.

All of these are pure. Imports of torch-bearing modules (`phase17_personas`, `phase17_isolation`, `phase18_extraction`, `phase23_run` via `seed_list()`) are LAZY, inside functions.

### Pattern: fill bindings (exact form the census accepts)
```python
# scripts/phase38_prereg.py — source: tests/test_phase35_prereg.py census + phase37_prereg.py:426
import phase35_prereg

E5_MINTING_RULE = phase35_prereg.fill("e5_minting_rule", minting_rule=ENTRIES["e5_minting_rule"])
E5_RANK_MOVES_AND_GENERATION_COLLAPSES = phase35_prereg.fill(
    "e5_rank_moves_and_generation_collapses",
    moves=ENTRIES["rank_moved"],
    collapses=ENTRIES["generation_collapsed"],
)

# scripts/phase38_sizes_prereg.py
import phase35_prereg

MINTING_RECORD = next(p for p in phase35_prereg.V6_RESULT_PATHS if p.startswith("results/phase38_minting")).replace("*", "")
E5_SET_SIZES = phase35_prereg.fill(
    "e5_set_sizes",
    set_sizes=_SIZES,                    # {slot: max |R|}, read from the record, ints 1..512
    input_records=(MINTING_RECORD,),     # "results/phase38_minting.json"
    derivation={"value": _SIZES, "derivation": "...", "kind": "derived",
                "source": f"... {MINTING_RECORD} ..."},   # source MUST contain the path
)
```

### Anti-patterns to avoid
- **Calling `exposure_rank` or `reference_set_for` on |R| > 8.** Both `_prove(6 <= len <= 8)`, which is a SystemExit mid-run. Use them only for the gate at the committed |R|.
- **A per-slot early stop ("slot full") with global substring-disjointness.** Measured: the target-1024 run and the target-4096 run disagree (`cat_name@1024` at draw 27,134 vs 27,185), because a full slot stops absorbing collisions. Use a single global stop (Pitfall 5).
- **Batching NLLs for speed.** Changes floats; the gate is exact.
- **Keying the tie-break on a placeholder** (e.g. `"<taught>"`) instead of the real string.

## Don't Hand-Roll

| Problem | Don't build | Use instead | Why |
|---|---|---|---|
| Value-span NLL | a new scorer | `phase19_erasure.value_span_nll_mean` | It is the one NLL every committed rank used. |
| Clearance generation | a new sampler | `phase14_factset_gate.probe_guessability` on `phase17_persona_gate.build_unadapted_base` (template `phase36_probe.stage_e5`) | Phase 17's seeding, stop ids, forbid mask, `start_index` discipline. |
| Containment / normalization | a regex | `phase14_factset.normalize_for_match` / `exact_match_clean` (torch-free; pinned equal to `phase14_recall.normalize`) | Scorer parity. |
| Prefix ablation | weight edits | `phase36_probe.adapted_model` / `phase19_erasure.ablate_components` + `load_adapter_weights` | ISO-06, duplicate refusal, identity check. |
| k=0 counts | typing 27 | `phase19_run._pooled_rows` on `phase18_arm_adapter-on.json` | The defect C recovery path. |
| Atomic write, heartbeat, ledger | new I/O | `phase25_run.atomic_write_json/beat/start_heartbeat`, `phase36_ledger.append/require_launch` | `os.replace` ban; ledger invariants. |
| Phase 17 filters as proof | copies | `phase17_personas.filter_*` on the final scored prefix | "import the instrument, never copy it". |

## Common Pitfalls

### Pitfall 1: the prereg freezes at the minting record
**What goes wrong:** a review fix, `ruff format` or docstring edit to `phase38_prereg.py` after `results/phase38_minting.json` is committed reds leg (a) permanently. `git log` lists every commit, and the first add is `adds[-1]`.
**Avoid:** run the code review on the prereg plus the mint driver BEFORE the minting run; run `ruff format` before the freeze commit. Any later correction goes in a dated continuation module whose name does NOT match `phase38_*prereg.py` if it carries no fill (or does match but has no fill call).

### Pitfall 2: `seed_list()` imports torch
Measured: `torch before False … seed_list (1337, 2024, 1338, 2025, 1339) torch after True`. Call it inside the generator function, not at import. The entry text names it by reference (`phase35_prereg.seed_list()[0]`). A test asserts `seed_list()[0] == 1337` and that the generator called it.

### Pitfall 3: `check_unit_caps` refuses `prefixes=8`
Measured above. Never pass `prefixes` to it. Check prefixes against `APPROVED_E5_PREFIXES` from `phase38_prereg`, and prove that the budget's committed prefixes cap is still 6, so the record states the deviation.

### Pitfall 4: |R| arithmetic at 512
`e5_set_sizes` caps each size at 512, and `unit_caps.E5.max_set_size` = 512. If the taught value is added ON TOP of 512 minted, |R| = 513 and both refuse. Define |R_n| = n *including* the taught value: n − 1 minted, sizes 8/32/128/512, `birth_year` maximum 220. Write this into the rule text (Q3).

### Pitfall 5: list stability depends on the stop rule
Acceptance of draw i depends only on draws < i, so a fixed draw budget is prefix-stable (measured: the 30k lists are prefixes of the 60k lists, all six True). A per-slot target with "slot full" skipping is not. Recommended stop: "stop at the end of the first draw after which every name/place slot holds ≥ N cleared", with all slots accepting until that global stop. N is set in the rule (Q2).

### Pitfall 6: Python `random` reproducibility
Python guarantees only that `random()` is reproducible under the same seed across versions. `choice`/`shuffle`/`randrange` may change [ASSUMED: from Python docs knowledge; verify against docs.python.org `random` "Notes on Reproducibility"]. Derive every choice from `rng.random()` and write Fisher-Yates explicitly for the numeric shuffle. CI and dev both pin 3.11 anyway.

### Pitfall 7: edit-distance neighbours of the target
The grammar produced `zorr` (distance 1 from the target `zorp`) and `krux`/`brix` (distance 1 from `krix`) in pet_name's first 511. Phase 17's D-05 neighbour screen (`results/phase17_personas_report.md` "Filters" table) is explicitly NOT one of the four filters, and D-03 names only the four. This needs a ruling before the freeze (Q5).

### Pitfall 8: `phase17_personas.filter_substring_disjoint` is O(n²) with normalize inside the loop
Measured: n=200 0.19 s; n=400 0.62 s; n=3066 (511 × 6) 31.0 s, passed. Over the whole cleared lists (~15-23k values incl. house_number) it would take tens of minutes. Use a pre-normalized predicate for selection. Run the Phase 17 functions as a proof on the scored prefix only, in the driver, not in a CI test.

### Pitfall 9: device-dependent clearance
CPU and MPS `torch.Generator`s are different streams. A CPU regeneration is not Phase 17's draws. Name the completion source and device in the minting record.

### Pitfall 10: the k=0 target count is not in a JSON field
Re-derive it with `_pooled_rows`; do not type 27.

### Pitfall 11: defect C rows
`phase19_arm_erased.json` `per_fact` (post) is 14-question rows. Use `phase19_target_scores.json`.

### Pitfall 12: dry-run green, live path unwired
Memory precedent (Phase 25). Each driver gets one real smallest-shape run on CPU into a tmp root with a tmp ledger: 1 reading × 2 slots × n=8 → sidecar → emit → report. The report consumer is fed one real producer record before any MPS launch.

### Pitfall 13: fact strings in records
Phase 18 kept `ranking` (candidate strings) out of records. The minting record must hold the minted strings (D-05). For the rank record, store per-candidate NLLs keyed by index into the minting record's lists, with the taught value's NLL under a slot key.

## Code Examples

### Rank at nested prefixes from one scored maximum set
```python
# Mirrors phase18_extraction.exposure_rank's sort key exactly (ascending NLL, tie by string).
def rank_in_prefix(nll, taught, members):
    """members: the n-1 minted strings of R_n (taught excluded); nll: {string: float} incl. taught."""
    key = (nll[taught], taught)
    return 1 + sum((nll[c], c) < key for c in members)

def exposure_bits(rank, size):
    return math.log2(size) - math.log2(rank)   # = log2(|R| / rank), the committed formula's order
```
Property test: for random dicts of 6-8 entries with forced ties, `rank_in_prefix(d, t, [c for c in d if c != t]) == phase18_extraction.exposure_rank(d, taught_value=t, reduction="mean", length_spread=0)["rank"]`.

### Clearance against committed Phase 17 completions (option A of Q1)
```python
# Parser measured: 52 completions per slot, questions equal held_out_by_slot() in order, 0 escapes.
#   ### Slot `<slot>` — 13 questions, 52 completions
#   - Q `<question>` — prompt = <n> ids
#     - greedy: `<text>` / - warm <i>: `<text>`
cleared = phase14_factset.exact_match_clean(completions_by_slot[slot], candidate)
```

## State of the Art (in-repo)

| Old | Current | When | Impact |
|---|---|---|---|
| |R| = 6-8 per slot, ceiling 2.58-3.0 bits | minted |R| up to 512 (9 bits) | Phase 38 | A rank can move by up to 9 bits before generation collapses; the committed sets could show only "rank 1 vs 2". |
| CONTEXT: "no committed sha of ordered_prefix" | `phase36_probe_e1.json` `configuration.components_sha256` = `a7cc2271…` | committed 2026-10-02 | D-20 can verify against a committed digest. |

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|-------|---------|---------------|
| A1 | Python guarantees reproducibility only for `random()`, not `choice`/`shuffle` | Pitfall 6 | Low: deriving everything from `random()` is safe either way. |
| A2 | CPU clearance generation cost is of the same order as MPS (~2 min) | M4 | Low: not measured; matters only if Q1 picks CPU regeneration. |
| A3 | E4's canary count `m` is unknown, so the slack beyond 512 cannot be derived | Q2 | Medium: too little slack forces a second minting, a new record, for Phase 43. |

## Open Questions (rulings needed before the rule freezes)

1. **Q1. Which completions clear the candidates?**
   - (A) The 416 committed Phase 17 completions, parsed from `results/phase17_personas_report.md`: zero compute, the exact Phase 17 evidence (MPS, base `04e724c`), reproducible on CPU by anyone.
   - (B) An MPS regeneration via `phase36_probe.stage_e5`'s path under the ledger (≈ 128 s, budgeted), compared descriptively with (A).
   - (C) A CPU regeneration: different warm draws, so not recommended.
   - Recommendation: **A**, with the parser's invariants (416 completions, question order == `held_out_by_slot()`) asserted in the rule.
2. **Q2. Slack.** N cleared per name/place slot is a preference. 1024 costs 7.4 s; 4096 costs 41 s.
   - Recommend a single global stop at N = 2048 (cheap, generous for E4) unless Phase 43's `m` is known.
   - Numeric slots keep their whole cleared lists (219 and ~8.7-9k).
3. **Q3. Does |R| count the taught value?** Recommend yes (|R_n| = n, n−1 minted). Otherwise 512 is unreachable under the cap and `e5_max_set_size`.
4. **Q4. Cross-slot uniqueness.** Recommend that each string belongs to at most one slot: the round-robin deal for names, and house_number excludes birth_year's cleared list. This helps E4's containment scoring. Substring scope: global (all slots) vs per-slot. Measured: both reach 1024 easily. Global is stricter and matches D-03's "minted ∪ FORBIDDEN".
5. **Q5. The D-05 neighbour screen** (edit distance 1 from any excluded value; `zorr`~`zorp` measured). Options:
   - (a) add it as a fifth screen, which departs from D-03's "four filters";
   - (b) record the neighbours descriptively only;
   - (c) ignore it.
   Recommendation: (b), unless Rafael wants (a).
6. **Q6. Which questions does filter 4 use?** Phase 17 used the 104 `core_held_out` questions. Recommend the same 104 (`phase17_isolation.held_out_by_slot()`). The 216 A2 corpus prompts are not part of Phase 17's filter.

## Environment Availability

| Dependency | Required by | Available | Version | Fallback |
|---|---|---|---|---|
| Python 3.11 venv | everything | ✓ | 3.11.15 | — |
| torch + MPS | scoring run | ✓ | 2.7.1, `mps.is_available() True` | none (D-17 requires MPS) |
| `checkpoints/persona_adapter.pt` | readings k=0..78, adapter-off | ✓ | sha `226f2ae5…` | — |
| `checkpoints/phase19_erase_reference_adapter.pt` | M2 | ✓ | sha `22e66552…` | — |
| `checkpoints/convbase_slim.pt` | all | ✓ | sha `550bb8b0…` | — |
| `artifacts/tokenizer.json`, `results/phase17_personas_report.md`, `results/phase16_recall_sample.json`, `results/phase18_arm_adapter-on.json`, `ledger/v6_mps_ledger.jsonl` | minting / counts / ledger | ✓ tracked | — | — |
| ubuntu CI | tests | checkpoints absent | — | tests must not need checkpoints (zero skips) |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x (venv), CPU-only |
| Config file | `pyproject.toml` / Makefile (`make test` = `.venv/bin/pytest -q`) |
| Quick run command | `.venv/bin/pytest -q tests/test_phase38_prereg.py tests/test_phase38_mint.py tests/test_phase38_sizes_prereg.py tests/test_phase38_rank.py` |
| Cross-phase guards | `.venv/bin/pytest -q tests/test_phase35_prereg.py -k "slot_census or slot_ordering" tests/test_phase36_caps.py tests/test_phase21_sc5.py tests/test_lora_inject.py tests/test_phase25_driver.py tests/test_phase25_venue.py` |
| Full suite | `nohup sh -c ".venv/bin/pytest -q -p no:cacheprovider > $LOG 2>&1; echo EXIT=\$? >> $LOG" &`, then an `until grep -q '^EXIT='` waiter (~43-45 min; the Bash tool caps at 600 s) |

### Phase Requirements → Test Map
| Req / SC | Behavior | Type | Automated command | File exists? |
|---|---|---|---|---|
| RANK-01 / SC1 | Rule entry is four-field, kind labelled, seed by reference; `E5_MINTING_RULE` filled once in `phase38_prereg.py` | unit + census | `pytest tests/test_phase38_prereg.py -k "entries or fill or census"` | ❌ Wave 0 |
| RANK-01 / SC1 | Generator is deterministic and prefix-stable (30k ⊂ 60k), uses `random()` only (AST), surface format (1 word, lowercase, exact token count), exclusions (118 + priors), the 4 filters, clearance; numeric enumerate → exclude → clear → Fisher-Yates with `seed_list()[0]` | unit (tiny fixtures) | `pytest tests/test_phase38_prereg.py -k "mint or numeric or shuffle"` | ❌ Wave 0 |
| RANK-01 / SC1 | Minting record: whole cleared lists, slack, completion source + device named, Phase 17 filter proof on the scored prefix, write-once | unit + one real CPU smallest-shape run into tmp | `pytest tests/test_phase38_mint.py` | ❌ Wave 0 |
| RANK-01 / SC1 | `E5_SET_SIZES` read from the record (never typed), ≤ 8 sets, ≤ 512, caps checked without `prefixes`; legs (a)/(b) | unit + ancestry | `pytest tests/test_phase38_sizes_prereg.py tests/test_phase36_caps.py -k owner` | ❌ Wave 0 |
| RANK-02 / SC2 | `rank_in_prefix` ≡ `exposure_rank` on 6-8 sets with ties (property test); bits formula; moved = rank_k ≥ 2·rank_0; collapse/damage prefixes reproduce the measured table (pet 16/64, person 16/64 with the k=8 tie, cat 64/never, sibling 32/64, hometown 8/64, street 32/64, birth 78/never, house 32/never); BEFORE/AT/AFTER/NEVER | unit | `pytest tests/test_phase38_prereg.py -k "rank or moved or collapse or damage or relation"` | ❌ Wave 0 |
| RANK-02 / SC2 | Gate sources resolve to the 64 committed ranks; the 3 SHA-256s (adapter `226f2ae5…`, ordered_prefix `a7cc2271…` = probe e1 `components_sha256`, M2 `22e66552…`) read from records; k=0 counts re-derived = 27 | unit (JSON only; SHA of checkpoints via monkeypatched path, since ubuntu has no checkpoints) | `pytest tests/test_phase38_rank.py -k "gate_sources or sha or counts"` | ❌ Wave 0 |
| RANK-02 / SC2 | Driver preflight refusals before the ledger start; gate STOP path; sidecar → emit → report wired | unit with fake model + one CPU rehearsal into tmp root/ledger | `pytest tests/test_phase38_rank.py -k "preflight or gate_stop or rehearsal or emit or report"` | ❌ Wave 0 |
| RANK-03 / SC3 | `phase18_extraction.py` bytes unchanged; phase38 modules import (not redefine) `reference_set_for`; no `exposure_rank` call outside the gate (AST) | AST + bytes | `pytest tests/test_phase21_sc5.py::test_instruments_unchanged_byte_for_byte tests/test_phase38_rank.py -k ast` | partly ✅ |
| SC4 | Prereg frozen before every `results/phase38_*` (natural RED vs `phase35_prereg.py`); test file first-add precedes records; `RECORDS_AT_COMMIT == 0`; records write-once (overwrite refusal) | git ancestry | `pytest tests/test_phase38_prereg.py -k "frozen or first_add or records_at_commit"` and `tests/test_phase35_prereg.py::test_slot_ordering_is_green_on_the_real_repo` | ❌ Wave 0 |
| hygiene | torch-free prereg import, zero skips, every function CPU-tested, no `== 10`, no `os.replace`, no `inject_lora` | census | `pytest tests/test_phase38_prereg.py -k "torch or skips or every_function"`, `tests/test_phase21_sc5.py`, `tests/test_lora_inject.py` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** the quick run plus the cross-phase guards (≈ 1-3 min).
- **Per wave merge, and after every record commit:** full suite (records reveal latent reds: Phase 36 memory).
- **Phase gate:** full suite green before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] `tests/test_phase38_prereg.py`: ancestry, census, rule functions, rank equivalence.
- [ ] `tests/test_phase38_mint.py`: fixtures from the committed Phase 17 completions (tracked), so it runs on ubuntu.
- [ ] `tests/test_phase38_sizes_prereg.py`.
- [ ] `tests/test_phase38_rank.py`: fake-model fixtures; no checkpoint dependency.
- [ ] No framework install needed.

## Proposed plan shape (Phase 37 split)

| Wave | Plan | Content | Gate |
|---|---|---|---|
| 1 | 38-01 | `phase38_prereg.py`: entries, D-21 approval + projection (read from the budget), `APPROVED_E5_PREFIXES`, both fills, all pure rule functions. Plus `tests/test_phase38_prereg.py`. | autonomous |
| 2 | 38-02 | `phase38_mint.py` (CPU) + tests + a real CPU smallest-shape run into tmp. **Code review of 38-01 + 38-02 here**, then fixes, before anything is minted. Rafael rules Q1-Q6 BEFORE 38-01 freezes (best at plan-check time). | review |
| 3 | 38-03 | **[checkpoint]** run the minting → Rafael "approved" → commit `results/phase38_minting.json` alone → full suite. | human |
| 4 | 38-04 | `phase38_sizes_prereg.py` (fills `e5_set_sizes` from the record; cap check) + test; then `phase38_rank.py` (preflight/run/crosscheck/emit/report) + tests + CPU rehearsal. Optional LaunchAgent (the run is ~5-10 min; a terminal launch with `caffeinate -i` suffices). | autonomous |
| 5 | 38-05 | Code review of the drivers BEFORE the MPS run (Phase 36: the pre-run review found 6 recovery-path defects); fixes. | review |
| 6 | 38-06 | **[checkpoint]** Rafael approves launch → `preflight` → `run` on MPS (ledger E5 start/end) → `crosscheck` → `emit` → Rafael "approved" → commit `results/phase38_rank.json` alone. | human |
| 7 | 38-07 | `report` → `results/phase38_rank_report.md` → Rafael "approved" → commit; REQUIREMENTS/ROADMAP/STATE by hand (memory: gsd-sdk handlers corrupt planning frontmatter). | human |

## Security Domain

| ASVS category | Applies | Control |
|---|---|---|
| V5 Input validation | yes | `_prove` (SystemExit, never `assert`) on every record field read; `phase30_points._tracked_json` / `committed_budget` refuse untracked or edited records. |
| V6 Cryptography | yes (integrity) | SHA-256 via `hashlib` of adapters, the curve, `ordered_prefix` and modules; never hand-rolled. |
| V2/V3/V4 | no | offline, single-user. |

| Threat | STRIDE | Mitigation |
|---|---|---|
| Rule fitted to minted candidates | Tampering | Leg (a) ancestry; rule + code frozen before the minting record. |
| Silent record overwrite | Tampering | Write-once refusal; `atomic_write_json`; commit alone after "approved". |
| Wrong adapter / prefix | Spoofing | Three committed SHA-256s checked in preflight before the ledger start line. |
| Unsafe checkpoint load | Elevation | `load_slim` / `load_adapter` with `weights_only=True` (existing loaders). |

## Sources

### Primary (HIGH, from the codebase and committed records, measured this session)
- `scripts/phase35_prereg.py`: 136-210, 313-370, 840-955, 1124-1145, 1646-1672, 1779-1784, 1797-1923
- `tests/test_phase35_prereg.py`: 2120-2330, 2430-2700
- `scripts/phase36_caps.py` (whole); `scripts/phase36_ledger.py` (whole); `results/phase36_budget.json`; `results/phase36_probe_e5.json`; `results/phase36_probe_e1.json`
- `scripts/phase18_extraction.py`: 975-1285, 1361-1421, 3515-3720
- `scripts/phase19_erasure.py`: 2380-2445, 2732-2800, 2955-3000, 3690-3720
- `scripts/phase14_factset.py`; `scripts/phase14_factset_gate.py:62-153`; `scripts/phase17_persona_facts.py`; `scripts/phase17_personas.py:200-460`; `scripts/phase17_persona_gate.py`; `scripts/phase21_filler.py:150-400`; `scripts/phase36_probe.py:440-820`; `scripts/phase37_prereg.py`; `scripts/phase37_r1b.py`; `tests/test_phase37_prereg.py`; `tests/test_phase36_caps.py:266-296`; `tests/test_phase25_venue.py:290-360`; `tests/test_phase14_scoring.py:560-790`
- Records: `phase19_arm_erased.json`, `phase19_arm_retrain.json`, `phase18_arm_adapter-off.json`, `phase18_arm_adapter-on.json`, `phase19_collateral_curve.json`, `erasure_kstar_summary.json`, `phase19_target_scores.json`, `phase19_retrain_scores.json`, `phase17_personas_report.md`, `phase19_reference_set_correction.md`

### Tertiary (LOW)
- Python `random` reproducibility guarantee (training knowledge; A1).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH. Every component is in-repo and was exercised on CPU.
- Measurements M1-M5: HIGH. Raw output above.
- Architecture / plan shape: MEDIUM. It depends on the Q1-Q6 rulings.
- Pitfalls: HIGH. Each one was measured, or read from the test code that enforces it.

**Research date:** 2026-10-04
**Valid until:** the first commit of `results/phase38_minting.json`. After that, the prereg facts are frozen and the rest stays valid until any pinned module or the ledger changes.
