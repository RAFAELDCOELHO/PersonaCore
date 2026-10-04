# Phase 38: Exposure Rank at Larger Minted Sets - Context

**Gathered:** 2026-10-04
**Status:** Ready for planning

<domain>
## Phase Boundary

E5 (RANK-01..03): re-measure the exposure rank of the committed Phase 19 ablation prefixes
(k = 0, 8, 16, 32, 64, 78) against same-slot candidate sets far larger than today's committed
reference sets (6-8 members per slot). The sets are minted by a rule pre-registered before any
candidate exists. The report says, per slot and per set size, whether the rank moves before,
at, after, or never relative to the point where generation collapses (and where it is first
damaged), against the committed A2 counts.

`reference_set_for` and `scripts/phase18_extraction.py` stay untouched (RANK-03); the new sets live
in a new module that imports them. Records are write-once and committed only after Rafael writes
"approved"; no `results/phase38_*` record exists before the pre-registration module and its
ancestry test are committed.

Out of scope: E6 (Phase 39), any change to the v3.0 verdict, editing `phase35_prereg.py`,
`phase36_ledger.py`, `phase36_caps.py`, `results/phase36_budget.json` or any pinned module.

</domain>

<decisions>
## Implementation Decisions

All decisions below are Rafael's (2026-10-04, in Portuguese; paraphrased faithfully, the D-09 ruling
quoted). Facts marked "measured" were measured by Claude this session before the question was asked.

### Minting rule (names and places) — fills `e5_minting_rule` (RANK-01)
- **D-01: Generator.** A syllable grammar with a fixed seed, `seed_list()[0]` (`phase35_prereg.seed_list()` returns `phase23_run.SEED_LADDER`; its first seed is 1337). It is deterministic and independent of the taught values. Candidates are never edits of the current set or of the taught value.
- **D-02: Surface format.** Each candidate has the same surface format as the slot's taught value: number of words, capitalization, and a fixed suffix if the slot has one. It also has EXACTLY the same number of tokens. Research must measure, from the committed values, whether a slot really has a fixed suffix before the rule claims one.
- **D-03: Exclusions.** Excluded are every value taught anywhere in the project: core facts, fillers, calibration facts, and the Phase 17 persona values. The four Phase 17 mechanical filters also apply: ≤ 8 tokens, `decode(encode(v)) == v`, substring-disjoint from minted ∪ FORBIDDEN, and absent from the questions.
- **D-04: Clearance** follows Phase 17. A candidate is cleared iff it is absent from the base model's completions for that slot: the 13 held-out questions, greedy plus 3 warm draws, 52 completions per slot, checked with `phase14_factset.exact_match_clean` (`scripts/phase17_persona_gate.py:285-345`).
- **D-05: Order and record.** The cleared list stays in generator order, and every set is a prefix (the first n) of that list. The minting record holds the WHOLE cleared list, with slack beyond 512, because Phase 43 (E4) also consumes it (`e4_parameters` declares `results/phase38_minting*.json` as a required input, `phase35_prereg.py:1823-1827`).
- **D-06: Ordering.** The rule is committed before any candidate exists. Phase 35 enforces this: `e5_minting_rule` has no input record, so its fill file precedes every `results/phase38_*` record, and it cannot share a fill file with `e5_set_sizes`.

### Sets and sizes — fills `e5_set_sizes` (RANK-01)
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

### Definitions — fill `e5_rank_moves_and_generation_collapses`, frozen before any record (RANK-02)
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

### Device, gate and the rank re-implementation (RANK-02/03)
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

### Cap and budget — Rafael's D-09 approval (2026-10-04)
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

### Rulings at plan time (2026-10-04, after 38-RESEARCH.md; Rafael, in Portuguese, paraphrased faithfully)
- **D-24 (Q1, clearance source).** Clear against the 416 committed Phase 17 completions in
  `results/phase17_personas_report.md`. The rule ALSO pins that report's SHA-256, beside the parser
  invariants (416 total, 52 per slot, question order = `held_out_by_slot()`). The minting record
  reports, per slot, how many candidates each filter and the clearance removed; a clearance that
  removes zero in a slot is published as zero.
- **D-25 (Q2, slack).** 2048 cleared per name/place slot, with ONE global stop (the first draw after
  which every name/place slot holds >= 2048). If Phase 43 needs more, the extension is the
  continuation of the SAME generator (same seed, same filters) from the stop point, registered in
  Phase 43's pre-registration before any E4 record, and the first 2048 of each slot do not change.
- **D-26 (Q4, uniqueness).** Each string belongs to at most one slot, and substring-disjointness
  holds across ALL slots. Rafael's condition: confirm every name/place slot reaches 2048 under the
  global rule; if any does not, STOP and bring him the number, never reduce the slack alone.
  **Measured by Claude (2026-10-04, scratch `m7_yield2048_nb.py`, global rule + D-27 screen):** all six
  slots reach 2048 at 57,811 draws, 17.4 s CPU (rejections: token_count 37762, duplicate 2437,
  substring_minted 1759, substring_forbidden 46, neighbour_d1 5, excluded 1, clearance 1). That
  scratch run used per-slot "slot full" skipping, which research showed is NOT prefix-stable; the
  real driver uses the global stop. The executor must re-measure with the real driver and STOP on
  any slot < 2048.
- **D-27 (Q5, neighbour screen).**
  - A FIFTH filter on the six name/place slots: reject any candidate at edit distance 1 from any
    taught value. The minting record counts these rejections per slot.
  - Numeric slots are exempt, declared as a deviation from Phase 17 (which rejected `1971`). The
    record marks, per slot and per size, which numeric candidates are distance-1 neighbours.
  - Sensitivity reading on the numeric slots: rank curves are ALSO reported without the neighbours
    (in `birth_year`, the 118 remaining; measured: 101 of 219 are distance-1 neighbours of a taught
    value). Descriptive only; never enters the definitions.
- **D-28 (area 3 addendum, before the freeze).** The primary "moved" stays D-12 (rank_k >= 2 x
  rank_0, 1 bit). Record that with rank_0 = 1, rank 2 already counts.
- **D-29.** A second NAMED, descriptive event: "left the top eighth" = rank_k > |R| / 8. At |R| = 8 it
  coincides with the published criterion (left rank 1).
- **D-30.** The before / same prefix / after / never answer (D-15) is given for BOTH events (D-12 and
  D-29), per slot and per set size.

### Defaults taken without a ruling (forced or following an existing decision; flagged to Rafael)
- **D-31 (Q3, |R| counts the taught value).** |R_n| = n INCLUDING the taught value (n - 1 minted),
  sizes 8/32/128/512; `birth_year` maximum |R| = 220 (219 + taught). Forced: `reference_set_for`
  appends the taught value (`phase18_extraction.py:1203`), and a taught value on top of 512 minted
  gives |R| = 513, which both `ENTRIES["e5_max_set_size"]` (512) and `unit_caps.E5.max_set_size`
  refuse.
- **D-32 (Q6, filter 4's questions).** The same 104 `core_held_out` questions Phase 17 used
  (`phase17_isolation.held_out_by_slot()`), per D-03/D-04 "as in Phase 17".
- **D-20 correction (measured).** A committed digest of `ordered_prefix` DOES exist:
  `results/phase36_probe_e1.json` `configuration.components_sha256` = sha256(json.dumps(ordered_prefix))
  = `a7cc22715d64…` (re-measured by Claude, 78 entries). Verify against it.

### Claude's Discretion
- The prefix order inside the run, the record layout and file names (within `results/phase38_*`, minting records matching `results/phase38_minting*.json`), and how the fill files split. Phase 35 needs at least two fill files: rule + definitions before the minting record, and set sizes after it and before scoring.
- The syllable grammar's concrete alphabet and syllable inventory, subject to D-01..D-03, provided the rule text is complete before any candidate exists.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements and roadmap
- `.planning/REQUIREMENTS.md` §"Exposure rank at larger sets (RANK) — E5" (RANK-01..03)
- `.planning/ROADMAP.md` §"Phase 38: Exposure Rank at Larger Minted Sets" (SC1-SC4)

### Pre-registration slots this phase fills
- `scripts/phase35_prereg.py`:
  - `_rule_e5_minting_rule` :1646;
  - `_rule_e5_set_sizes` :1655;
  - `_rule_e5_rank_moves_and_generation_collapses` :1779;
  - `_SLOTS` :1823-1835 (e4_parameters also consumes `results/phase38_minting*.json`);
  - `ENTRIES["e5_max_set_size"]` :688-693;
  - ordering rules :47-60;
  - `seed_list()` :357;
  - record paths :321-322.
- `scripts/phase37_prereg.py:426` is the precedent for filling a Phase 35 slot (`phase35_prereg.fill(...)` bound at module level in `scripts/phase38_*prereg.py`).
- `.planning/phases/35-v6-0-pre-registration-and-the-research-it-rests-on/35-CONTEXT.md` (D-02 slot table: E5 row).

### Budget, caps and ledger (read-only)
- `results/phase36_budget.json`: `front_hours.E5`, `unit_caps.E5`, `unit_prices`, `formula.E5`.
- `scripts/phase36_caps.py`: `check_unit_caps` :165, `counts_for` :182-195, `owner_overruns`.
- `scripts/phase36_ledger.py`: `EVENTS` :46, `stop_checks`, `require_launch` :400, `rule` :427.
- `scripts/phase36_budget.py:81` (`RANK02_PREFIXES`).
- `results/phase36_probe_e5.json` (E5 probe: clearance and scoring timings).
- `.planning/phases/36-mps-cost-probes-and-budget-commitment/36-CONTEXT.md` (D-09 unit caps, D-13 stops).

### Instrument and minting precedent
- `scripts/phase18_extraction.py`: `reference_set_for` :~1180-1215, `exposure_rank` :1230-1262, `ADMISSIBLE_NLL_FRAME` / `ADMISSIBLE_NLL_REDUCTION` :985-987, the larger-R remark :1143-1155. Do NOT edit (RANK-03).
- `scripts/phase19_erasure.py`: `value_span_nll_mean` :2407, `_rank_of` :2422, `run_erasure_arm`, M2 (`RETRAIN_ARM`, `RETRAIN_PREFIX`).
- `scripts/phase17_persona_gate.py:285-345` (clearance), `scripts/phase17_personas.py:216ff, 361-440` (mechanical filters), `scripts/phase17_persona_facts.py:49-81` (hand-authored values), `results/phase17_personas_report.md:702-746` (34 measured → 24 committed).
- `scripts/phase14_factset.py` (`LOCKED_FACTS`, `exact_match_clean` :334-342, year facts :85-123), `scripts/phase21_filler.py:243-384` (`refuse_collisions`, `verify_round_trips`).
- `scripts/phase36_probe.py`: `adapted_model(device, k)` :590-606, `components_sha256` :565.

### Committed readings (gate sources and A2 counts)
- `results/phase19_collateral_curve.json` (`ordered_prefix`, `checkpoints`, `adapter_in_sha256`).
- `results/erasure_kstar_summary.json` (per-k target `successes` 24/18/2/0 at k = 8/16/32/64; non-target counts; `exposure_rank_this_run`).
- `results/phase19_arm_erased.json` (k = 78 and `pre_erasure` = k = 0).
- `results/phase19_target_scores.json` (k = 78 target 0/27; pre 27/27, also `results/phase19_erasure_report.md:18`).
- `results/phase19_arm_retrain.json` (M2).
- `results/phase18_arm_adapter-off.json` (adapter-off ranks: 5/4/3/4/5/3/3/5).
- `results/phase19_reference_set_correction.md` (defect E: k = 78's stop was read on the 6-member twin).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `phase19_erasure.value_span_nll_mean` plus the `ans1`/`mean` constants: the NLL the new rank function sorts by.
- `phase36_probe.adapted_model(device, k)`: rebuilds the prefix-k adapter from `persona_adapter.pt` + `ordered_prefix`.
- `phase17_persona_gate` clearance and `phase21_filler` collision/round-trip checks: the D-03/D-04 machinery.
- `phase36_ledger.require_launch` / `append`, `phase25_run.atomic_write_json`, heartbeat, and the LaunchAgent plist pattern (`artifacts/com.personacore.phase37.r1b.plist`), as in Phase 37.
- `phase37_r1b` as a driver template: preflight refusals before the ledger start line, the sweep written write-once before the long stage, `git_sha` at launch and at end, emit on CPU.

### Established Patterns
- Phase 35 slot ordering (legs a/b/c) and its ancestry tests: the fill file with no input precedes every `results/phase38_*` record.
- Write-once records committed alone after Rafael's "approved"; the code review runs BEFORE the prereg freeze and BEFORE the MPS run (Phases 35-37).
- Every function called by a test (census), AST gates, and the clean-tree probes in the full suite (~43-45 min).

### Integration Points
- Phase 43 (E4) consumes `results/phase38_minting*.json` (the full cleared list with slack, D-05).
- The milestone ledger: the E5 start/end lines.

</code_context>

<specifics>
## Specific Ideas

- Score each slot's maximum set once per reading and read the rank at the 8/32/128/512 prefixes, rather than re-scoring per size.
- Publish the full curves (rank and bits per prefix × size × slot), with the adapter-off and M2 curves beside them as references.
- Open research measurements (premises to check before planning, not decisions):
  - **Token-count yield:** how many cleared candidates the grammar yields per name/place slot at EXACTLY the taught value's token count. Can every slot reach 512 with slack?
  - **Fixed suffix:** whether any slot has a fixed suffix, measured from the committed values.
  - **Exclusion list:** the exact list of "every taught value anywhere" and where each list lives.
  - **`birth_year` count:** the post-exclusion, post-clearance count out of the 226 values.
  - **CPU vs MPS:** whether the CPU NLL reproduces the MPS ranks at |R| ≤ 8.

</specifics>

<deferred>
## Deferred Ideas

None raised. The CPU cross-check (D-19) stays descriptive; nothing beyond RANK-01..03 was proposed.

</deferred>

---

*Phase: 38-exposure-rank-at-larger-minted-sets*
*Context gathered: 2026-10-04*
