# Phase 40: M2 Seed Noise Floor (E2) - Research

**Researched:** 2026-10-05 (HEAD 2ff9c20)
**Domain:** in-repo MPS retrain + A2 scoring driver, pre-registration fill, noise-floor estimator
**Confidence:** HIGH (every load-bearing claim measured this session on CPU from committed records
or on-disk gitignored artifacts; nothing trained, no `results/phase40_*` written)

<user_constraints>
## User Constraints (from CONTEXT.md, verbatim)

### Locked Decisions

#### Carried forward (not re-decided)
- S = 5 is READ from `results/phase36_budget.json::e2_seed_count` by the `e2_S` slot; it is never
  typed (35-CONTEXT Addendum to D-15). Unit caps E2: adapters 2, seeds 5. Front hours E2
  7.890925927716101 h = 5 x (e2_train_m2_high 76.11 s + e2_train_full_high 80.84 s + 2 x
  e2_a2_pass_high 2762.26 s).
- Process as in Phases 37-39: a phase-owned prereg + ancestry test committed before any
  `results/phase40_*`; one MPS run under the milestone ledger (`require_launch("E2")`) and the
  committed stop rule; a CPU rehearsal first; result records write-once, committed only after
  Rafael writes "approved"; any automatic per-point commits listed in the plan in advance.

#### Recall floor — the `e2_noise_floor_estimator` (NOISE-01, NOISE-02)
- **D-01 (what is measured):** two groups, kept SEPARATE: the full taught adapter (5 seeds) and M2
  (5 seeds). In each adapter, the 7 gated non-targets' A2 recall at K = 48, each with its
  denominator (27 questions = 14 core_taught + 13 core_held_out).
- **D-02 (pair statistic):** for each pair of seeds (i, j) of the SAME group, d(i, j) = the largest
  |recall difference| over the 7 slots. This is the statistic of v3.0's sampling floor (one pair,
  max over slots; `phase19_erasure.nontarget_noise_floor = max`).
- **D-03 (group floor):** the group's floor = the MEAN of d(i, j) over its 10 pairs. The published
  training floor, placed beside 0.148148, = the LARGER of the two group floors. The mean is
  labelled `kind: preference`: it keeps the "one pair" scale of the v3.0 number.
- **D-04 (always beside it):** the max and min of the 10 pairs, every pair's d(i, j), and per slot
  the range and the standard deviation across the 5 seeds.
- **D-05 (declared):** every A2 measurement is itself a sample, so the training floor INCLUDES
  sampling noise. Stated in the prereg entry and the report.

#### Train fresh; old adapters only as checks
- **D-06:** train all 10 (full and M2 at each of the 5 seeds) with today's code and recipe. No old
  adapter enters the set.
- **D-07 (determinism check, no MPS cost):** compare the sha256 of the new M2@1337 with the committed
  `22e66552e92ec7d5f853a6b8d15f350cfc0f127f20ee85aaec1967147c375b57`
  (`results/phase19_arm_retrain.json::adapter_sha256`). IF the recipe of Phase 19's dialogue-floor
  adapters (`phase19_erase_dialogue_floor_seed1337/2024`, sha256 `f12ab4c3…` / `3fd5aba4…`) is
  identical to the new full adapter's, compare those too. If not bit-identical, report the
  difference in the A2 counts as "ruído de re-execução com a mesma semente"
  (same-seed re-run noise). Descriptive. (For M2@1337, the A2 counts are already committed in
  `phase19_arm_retrain.json`. The dialogue-floor adapters have NO A2 record, so for them only the
  sha256 comparison is free; anything beyond that is priced under D-14.)
- **D-08 (v3.0 'taught' limitation):** v3.0's taught side of the M1 x M2 comparison is
  `checkpoints/persona_adapter.pt` (sha256 `226f2ae5…`, Phase 18 record), NOT a seed-1337 retrain
  under the Phase 19 recipe. Record in the Phase 40 record, field by field, how its recipe differs
  from the retrain's (steps, data, replay, code). This is a v3.0 limitation and goes to the
  milestone report. Compare persona_adapter.pt with the new full@1337, descriptively.

#### `gap_noise_floor` (feeds Phase 41's condition-(c) band, so it is a CRITERION)
- **D-09:** measure the adapter-ON dialogue PPL (`masked_perplexity`, the Phase 19 dialogue-floor
  metric) on the 5 full adapters. Adapter-OFF is the committed value 4.573349214207799
  (`results/phase19_noise_floors.json`, `adapter_off_identical_across_seeds: true`), checked, not
  retyped. gap = on − off.
- **D-10 (estimator):** `gap_noise_floor` = the MEAN of |gap difference| over the 10 pairs, built
  as in D-02/D-03. The max is shown beside it. `kind: preference`, same reason (one-pair scale; v3.0
  and v4.0 used one pair, |dPPL| = 0.005214448168350039).
- **D-11 (not in the E2 budget):** the dialogue-PPL measurement is not priced in the E2 formula.
  Bring its price BEFORE the run, for approval in the D-09 format (the 38-D-21/D-22 pattern: the
  cap/hours approval under 36-D-09 quoted verbatim, with the new projection and total written into
  `scripts/phase40_prereg.py` and into every Phase 40 record). Also bring the price of measuring it
  on the 5 M2 adapters (descriptive).

#### M1 x M2 re-reading
- **D-12:** publish the floor beside 0.148148 without touching v3.0's (b) margin, AND re-read v3.0's
  `delta_taught_to_m2` per slot beside the distribution of full x M2 differences with no erasure at
  all (5 x 5 = 25 pairs, the 5 same-seed pairs marked). Descriptive, never a verdict.

#### Addition: target rank across the 5 M2 seeds (descriptive, scoring only, CONDITIONAL)
- **D-13:** in each of the 5 M2 adapters:
  - the anchor rank of zorp (`pet_name`) against Phase 38's minted list at the nested sizes
    8, 32, 128, 512 (38-D-08 prefixes);
  - n1 of the target under the question context (Phase 39's R_q), on the committed set and on the
    minted set at |R| = 8.
  Purpose: read the two Phase 38/39 signals (rank 16 at k78 vs 32 for M2 at |R| = 512; n1 5/27 at
  k78 vs 0/27 for M2 at |R| = 8) against the retrain's seed-to-seed variation.
- **D-14:** bring its price and the unit cap it needs. It is NOT included without Rafael's
  "approved".

#### Run order and where the estimator text lives (Rafael's follow-up)
- **D-15 (run order):** per seed, in `seed_list()` order (1337, 2024, 1338, 2025, 1339). For each
  seed: train the full adapter, train M2, and run both A2 passes before moving to the next seed.
  If the stop rule fires mid-run, what exists is whole seeds, and the two Phase 41 uses (1337,
  2024) are ready first. A stop in the middle of a seed DROPS that seed from the estimator. This is
  declared in the prereg before any record. (The dialogue-PPL readings of D-09, if approved, and the
  D-13 scoring, if approved, are placed in the per-seed unit by the planner unless that changes the
  "whole seeds" property; state where.)
- **D-16 (estimator home) — PATH 1 HOLDS:** both estimators (recall floor, D-01..D-05, and
  `gap_noise_floor`, D-09..D-10) go in the SAME fill of the `e2_noise_floor_estimator` slot, as one
  four-field entry whose `value` is a mapping holding both, so the gap criterion is frozen by the
  same mechanism. Measured, not inferred: `_rule_e2_noise_floor_estimator` only runs
  `_prove_entry` (exactly the four D-14 fields, kind in KINDS, non-empty derivation/source; the
  value is checked for the forbidden phrase only when it is a str), and a dry `fill()` on CPU (no
  write) accepted a mapping value with both estimators and returned it frozen (mappingproxy). The
  slot's `input_records = ()` with owner 40, so Phase 35's ordering rule (a) already forces its
  fill file before every `results/phase40_*` record. Path 2 (the gap estimator in
  `phase40_prereg.py`) is NOT needed.

#### Planning items (Rafael wants to SEE both before approving any training)
- **P-1 (dialogue-PPL price):** no committed unit price for `masked_perplexity` exists:
  `results/phase36_budget.json::unit_prices` has none, and `results/phase19_dialogue_floor.json` has
  no wall-clock field. The plan derives one from a committed record that carries timing or proposes
  a small timing step, and states which.
- **P-2 (recipe identity):** whether the Phase 19 dialogue-floor adapters' recipe (`arm_spec`
  "real", `n_facts` 10, `replay_ratio` 1.0, `second_person` false, prefix `phase19`) is identical to
  the new full adapter's. Research settles it before D-07's comparison is planned.

### Claude's Discretion
- Record field layout of `results/phase40_noise_floor.json` beyond the contract key
  `gap_noise_floor` (finite >= 0), and how per-seed records (if any) are split; the per-seed records
  must keep the "whole seed" unit of D-15.
- Driver/rehearsal mechanics, following the Phases 37-39 pattern.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope. (D-13 is an in-phase descriptive addition gated on
Rafael's "approved", not a deferral.)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| NOISE-01 | Full taught adapter and M2 retrained at S seeds from `seed_list` (S from COST-01, pre-registered; S = 5), Phase 40 before Phase 41; each non-target's A2 recall reported per seed with its denominator | Training path traced (`train_arm` via `arm_spec("real")` / `retrain_arm_spec`); scoring via the pinned `run_erasure_arm(..., record_path=...)`; per-fact 27-denominator rows via `phase19_run._pooled_rows` (reproduces v3.0's numbers on CPU, M2); `e2_S` dry fill returns 5; per-seed whole-unit driver design (§Architecture) |
| NOISE-02 | Training-seed floor published beside 0.14814814814814814 without amending v3.0's (b) margin | Pair statistic = `pin.nontarget_noise_floor(pin.nontarget_deltas(...))` (reproduces 0.14814814814814814 and the taught→M2 deltas on CPU); margin read via `phase35_prereg.e1_condition_b_margin()`; `phase19_floor` / `phase19_noise_floors.json` never edited; `gap_noise_floor` contract and the Phase 41 consumer traced |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Python 3.11 `.venv` only (`.venv/bin/python`, 3.11.15 measured); never validate on the system 3.14.
- PyTorch only, no HF model code; MPS fp32 primary, no AMP/`GradScaler`/`torch.compile` on MPS.
- Offline CSV logging; no wandb/network.
- GSD workflow: edits only through GSD commands; this research writes only RESEARCH.md.
- `make test` needs the `demo` extra; tests CPU-only and GPU-free.
- Never commit secrets; `checkpoints/`, `data/`, `*.pt` are gitignored (`.gitignore:15-18`).
- Memory rules that bind this phase (user auto-memory): evidence before numbers (raw per-item logs,
  denominator, bound); pin corrections are dated continuations (`scripts/_addendum.py`), never edits
  of a closed prereg; GSD plans misname artifacts (resolve every path from module constants);
  `== 10` / `os.replace` / ISO-06 / `train_arm(` censuses bite new files; dry-run-only tests hide
  an unwired driver (feed the consumer one real producer record); verify stated premises and say
  plainly when one is false; checkpoint answers drafted by claude.ai are measured before adoption.

## Summary

Phase 40 needs no new library and almost no new instrument: the whole measurement is a loop over
existing, pinned functions — `teach_persona.train_arm` (training), `phase19_erasure.run_erasure_arm`
(the A2 pass at K = 48, which ALSO measures the D-09 dialogue PPL), `phase19_run._pooled_rows` (the
27-question denominator), and `phase19_erasure.nontarget_deltas` / `nontarget_noise_floor` (the
v3.0 pair statistic). Run on CPU against committed records, that chain reproduces v3.0's sampling
floor 0.14814814814814814 and the taught→M2 deltas (house_number 0.2592592592592592, hometown
0.11111111111111116) exactly. The new code is a phase-owned prereg (two fills, approvals, pure
estimator functions) and a per-seed driver in the Phase 36/37 pattern.

**P-2 (recipe identity): YES, identical, and stronger than the CONTEXT premise.** The Phase 19
dialogue-floor adapters were trained by `tp.train_arm(arm, facts=arm_spec("real") facts,
family_ids=TAUGHT_FAMILY_IDS, second_person, replay_ratio, seed=seed, prefix="phase19")`
(`scripts/phase19_erasure.py:3618-3637`) — exactly the call a Phase 40 full@seed makes. Measured:
`phase19_erase_dialogue_floor_seed1337_adapter.pt` and `persona_adapter.pt` are **tensor-identical**
(`torch.equal` on every key, max abs diff 0.0), and the teaching bins of `real`, `dialogue_floor_seed1337`
and `dialogue_floor_seed2024` are byte-identical. The two FILE sha256 values differ only because
`torch.save` writes the file stem as the zip archive root: re-saving the dialogue-floor-1337 artifact
under the name `persona_adapter.pt` yields exactly `226f2ae5…`. **This falsifies the D-08 premise**
("persona_adapter.pt is NOT a seed-1337 retrain under the Phase 19 recipe") and the scout note in
CONTEXT `<specifics>` ("persona_adapter.pt ≠ the dialogue-floor seed-1337 adapter"): at the tensor
level they are the same adapter. Rafael must see this before D-08 is planned.

**P-1 (dialogue-PPL price): 0 s marginal MPS, derived from committed records, no timing step
needed.** Every A2 pass (`run_erasure_arm`) already measures the D-09 instrument twice — the
`dialogue_ppl_pair` (adapter ON and OFF, `masked_perplexity` with `forbid_ids`, the exact function
`_cmd_dialogue_floor` used for the Phase 19 floor) in `_capability()` before and after the draws
(`scripts/phase19_erasure.py:2860-2872, 2918`) — and that pass is what `e2_a2_pass_high` (2762.26 s)
prices (`scripts/phase36_probe.py:1069-1077`; `results/phase36_probe_e2.json::stages.a2_pass`). The
committed records prove instrument identity: `persona_adapter.pt`'s `pre_erasure.dialogue_ppl.adapter_on`
in `results/phase19_arm_erased.json` is 5.815445876712191, equal to the dialogue-floor seed-1337
reading in `results/phase19_dialogue_floor.json`. So D-09 on the 5 full adapters and the descriptive
reading on the 5 M2 adapters are both read from the A2 records at +0 s. A committed upper bound on
one standalone sweep pair also exists: the probe's train overhead 42.54 s (`train_reps[0].overhead_seconds`)
contains bins build + export + one ON/OFF pair (`scripts/teach_persona.py:2095-2101`), so one pair ≤ 42.55 s.

**Primary recommendation:** plan Phase 40 as the Phase 39 ten-plan template with one checkpoint up
front (P-1, P-2, the D-08 premise correction and the D-13 price to Rafael), a prereg that fills
`e2_S` and `e2_noise_floor_estimator` and carries the approvals, a per-seed driver that makes ONE
ledger attempt per seed (Phase 36 `run_front` precedent) and reads D-09 from the A2 records, a
full-shape CPU rehearsal with MPS hidden, and an end-to-end feed of the rehearsal's
`phase40_noise_floor.json` into Phase 35's `e1_condition_c_band_inputs` rule before the ~8 h launch.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Seed list, S, estimator text, approvals, projection | Pre-registration module (`scripts/phase40_prereg.py`) | Phase 35 registry (`fill`) | Frozen before any record (rule (a)); four-field entries |
| Training 10 adapters | Pinned training driver (`teach_persona.train_arm`) on MPS | Phase 40 driver (orchestration, naming, csv relocation) | Recipe must be the pinned one; driver adds nothing to the recipe |
| A2 recall + dialogue PPL + exposure | Pinned scorer (`phase19_erasure.run_erasure_arm`) | — | Parity-asserted, same instrument as v3.0 |
| 27-question rows, pair statistic | `phase19_run._pooled_rows` + `phase19_erasure.nontarget_*` | Phase 40 prereg pure functions (means, D-04 extras, D-12 table) | Reuse the v3.0 reduction; only the mean over pairs is new |
| Ledger, stop rule, heartbeat | `phase36_ledger` + `phase25_run.beat/start_heartbeat` | LaunchAgent plist | Milestone-wide accounting |
| Records, report | Phase 40 driver `emit` / `report` (CPU) | `phase25_run.atomic_write_json` | Write-once, rebuilt from sidecars |
| D-13 scoring (conditional) | `phase38_rank.score_values/curve_for`, `phase39_ctx.score_question/rank_rows` | Phase 40 driver | Instruments imported, never redefined |

## Standard Stack

### Core (already in `.venv`; nothing to install)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| torch | 2.7.1 [VERIFIED: `.venv/bin/python -c "import torch"`] | training/scoring on MPS | the version every v3.0/v6.0 record was produced with (`results/phase36_probe_e2.json::provenance.run.torch_version`) |
| pytest | 9.0.3 [VERIFIED: `.venv/bin/pytest --version`] | CPU tests | repo standard |
| stdlib `statistics`, `math`, `itertools`, `json`, `hashlib` | 3.11 | means, SD, `math.comb`, pairs, digests | no dependency |

### Repo modules to IMPORT (never edit; most are byte-pinned by committed records)
| Module / symbol | Use | Pinned by (count of `results/*.json` naming it in `module_sha256`) |
|---|---|---|
| `teach_persona.train_arm`, `arm_spec`, `arm_outputs`, `TAUGHT_FAMILY_IDS` via `phase14_factset` | train full / M2 | teach_persona.py: 21 records |
| `phase19_erasure.retrain_arm_spec`, `TARGET_SLOT`, `run_erasure_arm`, `nontarget_rows`, `nontarget_deltas`, `nontarget_noise_floor`, `GATED_NONTARGET_SLOTS`, `N_TARGET_QUESTIONS`, `dialogue_ppl_pair`, `DIALOGUE_FLOOR_RECORD_PATH`, `PHASE18_ARM_RECORD_PATH`, `arm_record_path` | scoring + reduction | 19 records |
| `phase19_run._pooled_rows`, `RETRAIN_SCORES_PATH`, `NOISE_FLOORS_PATH` | 27-denominator rows; v3.0 `delta_taught_to_m2` | 5 records |
| `phase19_floor.NONTARGET_NOISE_FLOOR` (0.14814814814814814), `DIALOGUE_PPL_NOISE_FLOOR`, `EVIDENCE_ARTIFACT` | "beside" values | 2 records |
| `phase35_prereg.fill`, `seed_list`, `SLOTS`, `V6_RESULT_PATHS`, `ENTRIES`, `e1_condition_b_margin`, `MARGIN_K` | fills, paths, margin | 13 records |
| `phase36_ledger` (`run_id`, `append`, `require_launch`, `HEARTBEAT_PATH`, `LEDGER_PATH`, `stop_checks`), `phase36_caps.check_unit_caps/committed_budget`, `phase36_prereg.ENTRIES["front_stop_factor"]` | ledger, caps, stop | 11 / 5 records |
| `phase25_run.beat`, `start_heartbeat`, `atomic_write_json`, `disk_precheck` | heartbeat + atomic writes | 16 records |
| `phase37_prereg.draw_identity` | D-07 descriptive draw comparison | 3 records |
| `phase38_prereg.rank_in_prefix`, `nested_sizes`, `NESTED_SIZES`, `exposure_bits`, `MINTING_RECORD`; `phase38_rank.score_values`, `curve_for`, `scoring_plan` | D-13 anchor rank | 5 / 4 records |
| `phase39_prereg.n1`, `minted_members`, `MINTED_SET_SIZE`; `phase39_ctx.score_question`, `rank_rows` | D-13 R_q n1 | 3 / 3 records |
| `personacore.provenance.git_sha`, `refuse_if_dirty`; `personacore.checkpoint.load_adapter` | provenance, safe adapter load | — |

**Installation:** none. **Version verification:** not applicable (no external package added).

## Package Legitimacy Audit

No external package is installed by this phase. slopcheck not run (nothing to check).

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Measured Facts (this session; every number has its command or record field)

| # | Fact | Source / command |
|---|------|------------------|
| M1 | M2@1337 (Phase 19, `22e66552…`) and the two Phase 36 probe M2@1337 adapters (`probe36_probe36_m2_a/b_adapter.pt`, trained 2026-10-02 at 877b92b on MPS) are tensor-identical (`torch.equal` all keys, max abs diff 0.0) | CPU `torch.load(weights_only=True)` of `checkpoints/phase19_erase_reference_adapter.pt`, `checkpoints/probe36_probe36_m2_{a,b}_adapter.pt` |
| M2 | Their FILE sha256 differ (`58db2fcc…`, `c411a3b0…` vs `22e66552…`) only by file stem: re-saving probe m2_a's artifact as `phase19_erase_reference_adapter.pt` gives `22e66552e92ec7d5f853a6b8d15f350cfc0f127f20ee85aaec1967147c375b57`; re-saving dialogue-floor-1337 as `persona_adapter.pt` gives `226f2ae59938e389b396d999bc5f3e1e464874db5f3352d513dc5cd85984ebfb` | `torch.save` into scratchpad + `hashlib.sha256`; zip `namelist()` shows `<stem>/data.pkl` |
| M3 | `phase19_erase_dialogue_floor_seed1337_adapter.pt` (`f12ab4c3…`) is tensor-identical to `persona_adapter.pt` (`226f2ae5…`); dialogue-floor 1337 vs 2024 differ (max abs diff 0.1496) | CPU tensor comparison |
| M4 | Teaching bins: `persona_real_train.bin` = `persona_erase_dialogue_floor_seed1337_train.bin` = `..._seed2024_train.bin` (sha256 prefix `69eaf121aa207a40`); masks equal (`42287ddc6306c91d`); `persona_erase_reference_train.bin` = `persona_probe36_m2_{a,b}_train.bin` (`d3f761a9a2e63d66`) | `shasum -a 256 data/persona_*_train*.bin` (gitignored) |
| M5 | Training/scoring path unchanged since the Phase 36 probe: `teach_persona.py` `aabf4381…`, `training/loop.py` `40e9b32f…`, `phase19_erasure.py` `c407246d…`, `phase14_recall.py` `a40bed7f…`, `phase18_extraction.py` `d2b44806…` equal the pins in `results/phase36_probe_e2.json::provenance.module_sha256`; `git log 877b92b..HEAD` over those files, `phase14_factset.py` and `src/personacore/` is empty | `shasum`, `git log` |
| M6 | Dialogue instrument identity: `phase19_arm_erased.json::pre_erasure.dialogue_ppl.adapter_on` = `phase19_arm_replicate.json` = `phase19_dialogue_floor.json::dialogue_ppl.1337.adapter_on` = 5.815445876712191; `adapter_off` 4.573349214207799 in every arm record; `n_targets` 270203 | committed JSON |
| M7 | CPU re-derivation on committed records: `_pooled_rows` → `nontarget_deltas(taught=phase18 adapter-on, M2=phase19_arm_retrain)` = (0.0, 0.0, 0.0, 0.0, 0.2592592592592592, 0.0, 0.11111111111111116), max 0.2592592592592592; replicate → 0.14814814814814814; M2 counts pet_name 0/27, house_number 17/27, hometown 18/27, birth_year 18/27, person_name 26/27, cat/sibling/street 27/27; family A2, tiers (core_held_out, core_taught), k 48 | `.venv/bin/python` with `phase19_run._pooled_rows` |
| M8 | `GATED_NONTARGET_SLOTS` = (cat_name, street, sibling_name, person_name, house_number, birth_year, hometown); `TARGET_SLOT` pet_name | `phase19_erasure` |
| M9 | Dry fills (no write): `fill("e2_S", input_records=("results/phase36_budget.json",), derivation={value 5, ...source names the path})` → `5`; a source omitting the path is refused; `fill("e2_noise_floor_estimator", estimator={value: {recall_floor:…, gap_noise_floor:…}, ...})` → nested mappingproxy | `.venv/bin/python` |
| M10 | `SLOTS["e1_condition_c_band_inputs"]["input_records"]` = (`results/phase40_noise_floor.json`, `results/phase41_band_inputs_*.json`); `seed_list()` = (1337, 2024, 1338, 2025, 1339); `e1_teaching_seeds()` = (1337, 2024) | same |
| M11 | Budget: `front_hours.E2` 7.890925927716101 reproduced exactly by `seeds x (e2_train_m2_high + e2_train_full_high + adapters x e2_a2_pass_high) / 3600`; `unit_caps.E2` {adapters 2, seeds 5}; `total_hours` 77.72433149898184; `stop_line_hours` 90; `front_stop_factor` 1.5 → E2 stop (a) 11.83638889157415 h | `phase36_caps.committed_budget()` |
| M12 | Ledger spent: probes 3.66 h, R1b 1.1401 h, E5 0.0843 h, E6 0.2279 h, total 5.1123 h; `stop_checks` all None; `require_launch("E2")` passes today (writes nothing) | `phase36_ledger.spent()`, `require_launch` |
| M13 | D-13 price at budget unit prices: per M2 adapter `adapter_setup_high + (512 anchor + 8 gate + 27x8 R_q committed + 27x7 minted) x e5_nll_high` = 43.87426673062146 s; x5 = 0.06093648157030758 h; E2 projection 7.9518624092864085 h ≤ stop 11.836 h; total 77.78526798055215 h | arithmetic on `results/phase36_budget.json::unit_prices`; pet_name committed `|R|` = 8 (`phase18_extraction.reference_set_for`) |
| M14 | Measured MPS NLL rate (Phase 38 run): 303.383428 s over 8 x (3804 minted + 56 gate) = 30880 NLLs → 0.00982 s/NLL incl. setups; at that rate D-13 ≈ 5 x 925 x 0.00982 ≈ 45 s | `results/phase38_rank.json` provenance.run + set_sizes |
| M15 | `train_arm` resolves its device itself (`RuntimeConfig()` → `_default_device()` CUDA→MPS→CPU, `src/personacore/config.py:21-32`; `scripts/teach_persona.py:1818-1820`): on the M3 it ALWAYS trains on MPS unless `torch.backends.mps.is_available` is hidden | source |
| M16 | `arm_outputs` writes the csv to `results/{prefix}_{arm}/run.csv` (`scripts/teach_persona.py:357-393`); past run.csv files are TRACKED (`git ls-files results/phase19_erase_reference/run.csv`); bins are `data/persona_{arm}_train.bin` (no prefix) | source + git |

## Architecture Patterns

### System Architecture Diagram

```
 committed inputs                     phase40_prereg.py (frozen first)
 results/phase36_budget.json ──fill e2_S──▶ S=5 ; E2_NOISE_FLOOR_ESTIMATOR (both estimators)
 seed_list() ───────────────────────────▶ SEEDS = seed_list()[:S]   APPROVALS (D-11, D-13?)
                                                      │
              LaunchAgent (caffeinate -dims) ── phase40 driver `run` ──────────────┐
                                                      │                            │
   for seed in SEEDS (D-15 order):                    ▼                            │
     require_launch("E2") ─ stop? ─yes─▶ stop BEFORE the seed (whole seeds kept)   │
        │ no                                                                       │
     ledger start v6/40/E2/seed<s> + heartbeat                                     │
     train_arm(full@s)  ─▶ checkpoints/phase40_..._adapter.pt, csv → data/        │
     train_arm(M2@s)    ─▶ (same)                                                  │
     run_erasure_arm(full) ─▶ A2 draws + dialogue_ppl + exposure ─▶ arm record    │
     run_erasure_arm(M2)   ─▶ (same)                                               │
     [D-13 if approved: M2 anchor rank 8/32/128/512, R_q n1 committed + minted]   │
     seed sidecar (write-once) ─▶ ledger end (record = per-seed record)            │
                                                      │                            │
 emit (CPU) ◀── sidecars + arm records + committed v3.0 records ◀──────────────────┘
   per seed: _pooled_rows → 27-denominator rows; gap = on − off (off checked)
   group pairs (C(S',2)): d = nontarget_noise_floor(nontarget_deltas(.)) ; mean, max, min
   floor = max(group floors) beside phase19_floor.NONTARGET_NOISE_FLOOR ; margin unchanged
   gap_noise_floor = mean |gap_i − gap_j| (full) ─▶ results/phase40_noise_floor.json
   D-07/D-08 descriptive checks ; D-12 25-pair table
                                                      │
 consumers: Phase 41 phase35_prereg.fill("e1_condition_c_band_inputs") reads gap_noise_floor;
            Phase 41 reuses seed 1337/2024 adapters by sha256; Phase 45 report
```

### Recommended Project Structure (new files only)
```
scripts/phase40_prereg.py      # fills E2_S, E2_NOISE_FLOOR_ESTIMATOR; approvals; pure estimator fns
scripts/phase40_noise.py       # driver: preflight / run / emit / report (name must NOT match *prereg.py)
artifacts/com.personacore.phase40.e2.plist   # copy of the phase37 r1b agent
tests/test_phase40_prereg.py   # ancestry + entries + estimator on committed real records
tests/test_phase40_noise.py    # driver refusals, per-seed unit, emit, consumer feed
```
`scripts/phase40_*prereg.py` is the owner glob (`phase35_prereg.owner_prereg_glob`); a driver named
`phase40_driver.py`/`phase40_noise.py` is correctly NOT a fill file (`tests/test_phase35_prereg.py:2448-2461`).

### Pattern 1: The two fills (module level of `scripts/phase40_prereg.py`)
```python
# Source: scripts/phase35_prereg.py:1173-1187 (_rule_e2_S), :1773-1776, :1857-1861; precedent
# scripts/phase39_prereg.py (binding shape). Paths read from modules, never typed:
RECORD_GLOB = next(p for p in phase35_prereg.V6_RESULT_PATHS if p == "results/phase40_*")
NOISE_FLOOR_RECORD = phase35_prereg.SLOTS["e1_condition_c_band_inputs"]["input_records"][0]
BUDGET_RECORD = phase35_prereg.SLOTS["e2_S"]["input_records"][0]   # results/phase36_budget.json

E2_S = phase35_prereg.fill(
    "e2_S",
    input_records=(BUDGET_RECORD,),
    derivation={"value": <read e2_seed_count>, "derivation": "...", "kind": "derived",
                "source": f"{BUDGET_RECORD}::e2_seed_count; 35-CONTEXT Addendum to D-15"},
)
E2_NOISE_FLOOR_ESTIMATOR = phase35_prereg.fill(
    "e2_noise_floor_estimator",
    estimator={"value": {"recall_floor": {...D-01..D-05...}, "gap_noise_floor": {...D-09/D-10...}},
               "derivation": "...", "kind": "preference", "source": "40-CONTEXT D-01..D-10, D-15, D-16 (<sha>)"},
)
```
The `derivation["value"]` must EQUAL the read S (typing 5 is checked against the record, but the
"no derived value typed" test precedent wants it read: `json.loads(...)["e2_seed_count"]`). The slot
census refuses `phase35_prereg._anything` and any `_rule_` reference in `scripts/` (`tests/test_phase35_prereg.py:2166-2226`);
reading `phase35_prereg.SLOTS[...]["input_records"]` is allowed (registry read).

### Pattern 2: One seed = one ledger attempt (Phase 36 `run_front` precedent)
```python
# Source: scripts/phase36_probe.py:357-417 (start line, beat once, heartbeat thread, sidecar, end line)
for seed in SEEDS:
    phase36_ledger.require_launch("E2")          # committed D-13 stops, no second rule (38-D-23)
    rid = phase36_ledger.run_id(40, "E2", f"seed{seed}")
    phase36_ledger.append("start", run_id=rid, phase=40, front="E2", ledger_path=...)
    ... train full, train M2, A2 full, A2 M2, [D-13] ... write-once seed sidecar ...
    phase36_ledger.append("end", run_id=rid, phase=40, front="E2", record=<per-seed record>, ...)
```
Whole seeds hold by construction: a crash mid-seed leaves an open start → `reconcile` writes a
`lost` line and that seed is dropped (D-15); `require_launch` between seeds is the committed stop,
so no in-run timer is added (Phases 38/39 had none: `scripts/phase38_rank.py:519`, `phase39_ctx.py:758`).
Each per-seed record must carry `provenance.run.started_utc/finished_utc/device` (`phase36_ledger.RECORD_CLOCK`)
or the ledger counts its span as "record not yet tracked".

### Pattern 3: Training one adapter (exact recipe, csv out of `results/`)
```python
# Source: scripts/phase19_erasure.py:3618-3637 (_cmd_dialogue_floor), scripts/phase19_run.py:1607-1653
# (retrain_train), scripts/phase36_probe.py:1003-1028 (csv moved to data/, WR-01)
facts, second_person, replay_ratio = tp.arm_spec("real")                 # full
facts, second_person, replay_ratio = pin.retrain_arm_spec(target.id)     # M2 (prove dropped == [target.id])
result = tp.train_arm(arm, facts=facts, family_ids=phase14_factset.TAUGHT_FAMILY_IDS,
                      second_person=second_person, replay_ratio=replay_ratio, seed=seed, prefix=PREFIX)
# result["ppl_adapter_on"/"ppl_adapter_off"/"scored_targets"]: bind and keep beside (descriptive)
shutil.move(paths["csv"], data/<...>/run.csv); paths["csv"].parent.rmdir()
```
Arm names must be new (bins have no prefix; `refuse_if_exists` refuses existing ones), never `real`
(writes the shippable `persona_adapter.pt`, `teach_persona.py:381-385`), and must differ between the
rehearsal and the real run.

### Pattern 4: One A2 pass (pinned scorer, parity asserted)
```python
# Source: scripts/phase36_probe.py:1069-1077; scripts/phase37_r1b.py:298-300
pin.run_erasure_arm("retrain", device, adapter_path=<adapter>, record_path=root / <arm record>)
```
`"retrain"` is in `PARITY_ASSERTED_ARMS` (`phase19_erasure.py:2552`), so `assert_phase18_parity`
runs before the first draw; with `record_path` given, the label is not routed through
`arm_record_path` (`:2787`). The record's `dialogue_ppl` (post) and `pre_erasure.dialogue_ppl` are
the same adapter measured twice (no components; `phase19_run.py:1820-1826` says so for M2) — read
`dialogue_ppl.adapter_on/off` for D-09 and prove `pre == post`.

### Pattern 5: The estimator (pure, in the prereg)
```python
# Source: scripts/phase19_run.py:620-648 (_pooled_rows), :1713-1722; phase19_erasure.py:1333-1416
rows = {seed: p19run._pooled_rows(rec["draws"], values, family, tiers)}       # 27 = 14 + 13
d = pin.nontarget_noise_floor(pin.nontarget_deltas(pin.nontarget_rows(rows[i]),
                                                   pin.nontarget_rows(rows[j])))  # D-02, max of 7
pairs = itertools.combinations(sorted(whole_seeds), 2)                           # C(S',2), S' >= 2
group_floor = statistics.fmean(d for each pair)                                  # D-03 (preference)
training_floor = max(full_floor, m2_floor)                                       # D-03
gap[s] = rec["dialogue_ppl"]["adapter_on"] - rec["dialogue_ppl"]["adapter_off"]  # off checked == committed
gap_noise_floor = statistics.fmean(abs(gap[i] - gap[j]) for pairs over full seeds)  # D-10
```
`values` = `{f.id: f.value for f in LOCKED_FACTS + SOFT_TIER_FACTS}`; `family` = record
`config.attack_family`; `tiers` = sorted tiers of that family's draws (exactly as `retrain_score`).

### Pattern 6: Approval outside the caps (38-D-21/D-22, 39-D-11)
`scripts/phase38_prereg.py:156-228` and `scripts/phase39_prereg.py:198-410`: one typed approval
value + the ruling quoted verbatim (`D21_RULING`), the projection computed from
`results/phase36_budget.json` in the committed formula's term order and proved to reproduce
`front_hours` at the committed caps, the new total = `math.fsum(front_hours with this front
replaced)`, stop = `front_stop_factor x front_hours[front]` proved ≥ projection, and an
`approval_block()` embedded in every record listing `untouched` = ledger, budget record,
`phase36_ledger.py`, `phase36_caps.py`. The verbatim quote is tested against the CONTEXT bullet at
its commit (`tests/test_phase39_prereg.py:486-499`).

### Anti-Patterns to Avoid
- **Reading `per_fact` from an arm record:** `run_erasure_arm`'s `rows.update` across tiers keeps
  only one tier (14 questions; 19-09 defect C, `phase19_run.py:85-92`). Always `_pooled_rows`
  over the draws.
- **Comparing adapter FILE sha256 across names (D-07, D-08, ERASE-05):** the digest includes the
  file stem (M2). Use `torch.equal` per key, and/or the sha256 of the artifact re-serialized under
  the comparator's file stem in a scratch dir.
- **A second stop rule / in-run timer:** forbidden by the 38-D-23 precedent; use `require_launch`
  between seeds.
- **Calling `train_arm` in a "CPU" rehearsal without hiding MPS:** it trains on MPS outside the
  ledger (M15).
- **Re-implementing `masked_perplexity`, `nontarget_deltas` or the rank:** import them.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| A2 scoring | a new draw loop | `phase19_erasure.run_erasure_arm(..., record_path=)` | parity assertion, in-prompt guard, same instrument as v3.0 |
| 27-question rows | per-tier sums | `phase19_run._pooled_rows` | already proven; reproduces v3.0 |
| Pair statistic | `max(abs(...))` inline | `nontarget_deltas` + `nontarget_noise_floor` | refuses wrong slots/denominators; v3.0's own reduction |
| Dialogue PPL | a new sweep | the A2 record's `dialogue_ppl` (`dialogue_ppl_pair`) | identical instrument, already paid for |
| Atomic JSON | `os.replace` | `phase25_run.atomic_write_json` | `os.replace` census (`tests/test_phase25_driver.py:340-366`) |
| Ledger/stop | timers | `phase36_ledger.require_launch/append/reconcile` | milestone accounting |
| Rank / n1 | rank code | `phase38_prereg.rank_in_prefix`, `phase39_ctx.rank_rows`, `phase39_prereg.n1` | Phase 38/39 instruments |
| Draw comparison | diff loop | `phase37_prereg.draw_identity` | R1b precedent, descriptive |
| Pairs count | literal 10 | `math.comb(len(seeds), 2)` / `itertools.combinations` | `== 10` census |

## Common Pitfalls

### Pitfall 1: The D-07/D-08 sha256 comparison is false by construction
**What goes wrong:** new `phase40_..._adapter.pt` sha256 ≠ `22e66552…` even when the weights are bit-identical.
**Why:** `torch.save` stores `<file stem>/data.pkl` (M2). **Avoid:** compare tensors (`torch.equal`)
and report the re-serialized-under-comparator-name digest; state both in the record.
**Warning sign:** a "not bit-identical" finding with A2 counts exactly equal.

### Pitfall 2: The D-08 premise is false
Measured: `persona_adapter.pt` IS the `real` arm at seed 1337, tensor-identical to the Phase 19
dialogue-floor seed-1337 re-teach (M3, M4). Field-by-field differences that exist (none reach the
weights): arm name `real` vs `erase_dialogue_floor_seed1337`; prefix `phase14` vs `phase19`; driver
git sha `ed254a1` (`results/phase14_teaching_run.log:16`) vs `5efb01c`
(`results/phase19_dialogue_floor.json::config.git_sha`); date 2026-08-02 vs 2026-08-18; the logged
dialogue PPL 5.8176 was the unmasked twin (WR-01, `phase19_run.py:549-556`). Same: seed 1337, lr
3e-4, wd 0, batch 8, 200 steps, warmup 20, block 256, 10 facts, replay 1.0 in-bin, second_person
False, base fingerprint `04e724c…` step 4000 (all in `phase14_teaching_run.log:10,16` and the
artifact's `base_fingerprint`). The residual v3.0 difference that IS real: v3.0's taught-side A2
counts came from Phase 18's `run_arm` (`results/phase18_arm_adapter-on.json`, git `c71bade`), not
`run_erasure_arm` — whether those draws equal a `run_erasure_arm` pass on the same weights is
unmeasured and becomes a free D-07/D-08 reading at full@1337. Rafael must rule how D-08 is reworded.

### Pitfall 3: The csv lands under `results/phase40_*`
`train_arm` writes `results/{prefix}_{arm}/run.csv` (M16); with prefix `phase40` that matches the
v6.0 record glob `results/phase40_*` and leaves `results/` dirty (untracked counts as dirty in
`refuse_if_dirty`, `src/personacore/provenance.py:62-66`), so `emit` refuses and the clean-tree
probes go red. Move it to `data/` right after each `train_arm` and `rmdir` the empty dir (probe WR-01).

### Pitfall 4: Rehearsal collides with the real run, or runs on MPS
Bins are `data/persona_{arm}_train.bin` without prefix: a rehearsal using the real arm names makes
the real launch refuse (`refuse_if_exists`). And `train_arm` picks MPS on the M3 (M15): the
rehearsal process must set `torch.backends.mps.is_available = lambda: False` before any call, or it
spends unledgered MPS hours. CPU-trained adapters will NOT equal MPS ones; D-07 in the rehearsal is
expected "not identical".

### Pitfall 5: Repo-wide censuses a new file trips
| Census | Applies to Phase 40? | What to do |
|---|---|---|
| `train_arm(` register `_TRAIN_ARM_CALL_SITES` (`tests/test_phase23_resume.py:60-...`, raw `grep -rn "train_arm(" scripts tests`, per-file counts, AST call count, sum literal `8+1+1+1+1+2+1+1+1+1`) | YES — the driver adds one call | add `("scripts/phase40_noise.py", "call", "<fn>")`, bump the sum with `+ 1` and a dated comment; never write `train_arm(` in prose or tests (monkeypatch with `setattr(tp, "train_arm", fake)`) |
| `== 10` wall (`tests/test_phase21_sc5.py`, regex `(?:==|!=)\s*10(?![0-9_])` over every line of `tests/*.py`, comments included) | YES — C(5,2) | never write `== 10`/`!= 10` in `tests/test_phase40_*.py`; use `math.comb(len(SEEDS), 2)` |
| `os.replace` only in `phase25_run.py`/`phase25_record.py` (`tests/test_phase25_driver.py:340-366`) | YES | `phase25_run.atomic_write_json`; `shutil.move` is fine |
| ISO-06 `inject_lora` registers (`tests/test_lora_inject.py:261-293`) | NO if adapters load via `phase14_recall.load_adapted_model` (registered consumer) | never call `inject_lora` directly |
| `draw_all` call sites must assert (`tests/test_phase14_scoring.py:728`) | NO (scoring goes through `run_erasure_arm`/`score_question`) | don't call `draw_all` directly |
| `mitigation_gate.ratchet_k` K menu (48, 24, 16, 8) | NO (K read from the Phase 18 record) | fixtures that need K use 48 |
| `train_never_taught`, `retention_perplexity`, `mitigation_point_verdict` censuses | NO | don't call them |
| Slot census (`_slot_census_failures`) | YES | module-level `E2_S = phase35_prereg.fill("e2_S", ...)`, no private access |
| module_sha256 pins | YES for any edit to a pinned module | Phase 40 edits NO existing script; only adds files and the one register line in `tests/test_phase23_resume.py` (a test, not pinned) |
| `_SUPERSEDED_PINS` (`tests/test_phase27_relearn.py:1190`, `test_phase30_calibration.py:355`) | only if `teach_persona.py`/`phase30_points.py` is edited | don't edit them |

### Pitfall 6: Fixtures that read the real git index
A test that monkeypatches a module's `_ROOT` to `tmp_path` but leaves `phase36_caps.tracked_files()`
reading the real index goes red once the real Phase 40 ledger lines/records are tracked (Phase 36
memory). Pass `tracked=` explicitly in tests.

### Pitfall 7: Common random numbers across adapters (affects D-05's wording)
Every adapter's A2 pass uses the same per-question generator states (`stride = seed_index * K`,
`phase19_erasure.py:2826`; `seed_everything(recall.SEED)`), so the 10 seeds' samples are drawn under
common random numbers. v3.0's sampling floor instead re-drew the SAME adapter at a different stride
(`SEED_STRIDE_OFFSET`, `:1188`). D-05's "includes sampling noise" holds, but the sampling component
of a pair difference is correlated, not independent — say so in the prereg entry.

### Pitfall 8: Seeds 1337/2024 are predicted to reproduce existing adapters
From M1/M3/M5 (same code, same torch, same device, three prior reproductions), full@1337 is predicted
tensor-identical to `persona_adapter.pt`, full@2024 to `phase19_erase_dialogue_floor_seed2024`, M2@1337
to `22e66552…`. Then the (1337, 2024) full pair's |Δgap| is predicted to equal 0.005214448168350039
and M2@1337's A2 counts to equal `phase19_arm_retrain.json`'s. These are D-07 predictions, recorded
before the run; a mismatch is a finding. (D-06 still trains all 10; 36-Q6 calls reuse "savings".)

### Pitfall 9: The verbatim approval quote wraps across lines
Test the quote against the CONTEXT bullet joined by single spaces at its fixed commit (Phase 39
`_bullet`, `tests/test_phase39_prereg.py:464-479`).

### Pitfall 10: zsh NOMATCH / `$T` splitting in verify commands
Use `find` for leak guards and a file list with `$(cat f)` (user memory).

## Code Examples

### D-11 / D-13 projection (copy the term order; prove at import)
```python
# Source: scripts/phase36_budget.py formula.E2 (record field `formula`), phase38_prereg.py:182-212
p, c = _BUDGET["unit_prices"], _BUDGET["unit_caps"]["E2"]
def e2_projection_hours(d13_adapters=0, d13_nlls_per_adapter=0):
    return (c["seeds"] * (p["e2_train_m2_high"] + p["e2_train_full_high"]
                          + c["adapters"] * p["e2_a2_pass_high"])) / 3600 \
           + d13_adapters * (p["adapter_setup_high"] + d13_nlls_per_adapter * p["e5_nll_high"]) / 3600
_prove(e2_projection_hours() == _BUDGET["front_hours"]["E2"], "...")          # True (M11)
# D-11 dialogue PPL: + 0 (inside e2_a2_pass_high). D-13: 5 adapters x 925 NLLs -> 7.9518624092864085 h
E2_STOP_HOURS = phase36_prereg.ENTRIES["front_stop_factor"]["value"] * _BUDGET["front_hours"]["E2"]
```
The 925 = 512 (anchor, `phase38_rank.scoring_plan(slots=("pet_name",))`, size 512) + 8 (anchor
gate on the committed |R|) + 27 x 8 (R_q committed `reference_set_for("pet_name")`) + 27 x 7
(minted `cleared[:7]`), each derived in code, never typed.

### The D-13 per-adapter gate (internal, free)
The adapter's own A2 record carries `exposure[pet_name].rank` and `.nll.ans1.mean` on the committed
|R| = 8 (e.g. M2@1337: rank 2, `results/phase19_arm_retrain.json`). Re-scoring the 8 committed
values with `phase38_rank.score_values` and `phase38_prereg.rank_in_prefix` must reproduce that
rank — the Phase 38 gate (`scripts/phase38_rank.py:395-419`) against a same-session record.

## State of the Art (in this repo)

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| One-pair floors (v3.0 sampling 0.148148; v3.0/v4.0 dialogue 0.005214) | Mean over C(S,2) pairs, max/min beside | Phase 40 (D-03, D-10) | one-pair scale kept; spread visible |
| Fused `_cmd_retrain` (train + score) | split halves (19-13), probe | v3.0 | Phase 40 keeps halves separate per seed |
| One ledger attempt per run | one per unit (`run_front`) | Phase 36 | whole-seed accounting |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | CPU draw cost ~0.07 s/draw (inferred from Phase 39's 118.9 s CPU rehearsal run, `39-07-SUMMARY.md:107`) so a full-shape CPU A2 pass is ~12-20 min | Validation / rehearsal | rehearsal of 2 seeds may take hours; measure one pass first |
| A2 | `run_erasure_arm` on full@1337 reproduces Phase 18's `run_arm` A2 draws | Pitfall 2/8 | none (descriptive D-07/D-08 reading) |
| A3 | Seeds 1337/2024 reproduce prior adapters bit-identically | Pitfall 8 | a D-07 finding, not a failure |
| A4 | Sample SD (`statistics.stdev`, n−1) is the intended D-04 "standard deviation" | Open Q2 | wrong scale on a descriptive column |

## Open Questions

1. **D-08 rewording (Rafael).** Measured: the premise is false at the tensor level (Pitfall 2).
   Recommendation: record the field list above, state tensor identity with
   `phase19_erase_dialogue_floor_seed1337` and (predicted) full@1337, and name the one real residual
   (Phase 18 `run_arm` vs `run_erasure_arm` scoring) as what the milestone report carries.
2. **D-04 SD convention.** Not fixed by CONTEXT. Recommend `statistics.stdev` (sample, n−1) with
   the population SD beside, written into the estimator entry before any record.
3. **A2 label for the full adapter.** `"retrain"` is the only label in `PARITY_ASSERTED_ARMS` that
   applies no components; recommend it for both groups with the group carried in Phase 40's own
   fields (the alternative `"erased"` with `components=()` is equally parity-asserted but misnames).
4. **D-11/D-13 approvals.** D-11: +0 s (projection unchanged, 7.890925927716101 h). D-13: +0.0609 h
   priced high (≈ 45 s at the Phase 38 measured rate), E2 projection 7.9519 h ≤ stop 11.836 h, total
   77.7853 h. E2 caps have no field for scoring readings (`phase36_caps.CAP_FIELDS["E2"]` =
   adapters, seeds), so, as in 38-D-21 / 39-D-11, the approval is recorded in `phase40_prereg.py`
   and every record, and `check_unit_caps("E2", adapters=2, seeds=S)` stays as committed.
5. **Commit policy for the 10 arm records (~0.64-0.75 MB each).** Recommend committing them (R1a
   precedent: counts re-derivable on CPU from committed draws) after "approved", no automatic commits.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `.venv` Python | everything | ✓ | 3.11.15 | — |
| torch + MPS | the run | ✓ | 2.7.1, `mps.is_available()` True | — |
| pytest | tests | ✓ | 9.0.3 | — |
| `checkpoints/convbase_best.pt`, `persona_adapter.pt`, `phase19_erase_reference_adapter.pt`, dialogue-floor adapters | training base, D-07/D-08 | ✓ (gitignored, this host only) | — | tests that need them must not skip on ubuntu without a named skip leg |
| `data/dialog_val.bin`/mask, `data/retention_val.bin`, `results/phase18_corpus.json` | A2 pass | ✓ | — | — |
| Disk | ~10 x (1.35 MB adapter + 59.7 MB latest.pt) ≈ 0.6 GB | ✓ 463 GiB free | — | — |
| LaunchAgent slots | run | ✓ (old phase25 agents loaded, no PID) | — | — |

**Missing dependencies with no fallback:** none.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 in `.venv` (Python 3.11), CPU-only, zero skips in Phase 40 files |
| Config file | `pyproject.toml` (`make test` = `.venv/bin/pytest -q`) |
| Quick run command | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase40_prereg.py tests/test_phase40_noise.py` |
| Cross-phase guards | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase35_prereg.py tests/test_phase36_caps.py tests/test_phase36_ledger.py tests/test_phase23_resume.py tests/test_phase21_sc5.py tests/test_lora_inject.py tests/test_phase25_driver.py tests/test_phase14_scoring.py` |
| Full suite command | `nohup sh -c ".venv/bin/pytest -q -p no:cacheprovider > $LOG 2>&1; echo EXIT=\$? >> $LOG" &` + a `run_in_background` waiter `until grep -q '^EXIT=' "$LOG"; do sleep 60; done` (Bash caps at 600 s) |
| Estimated runtime | quick ~60 s; guards ~3-5 min (`test_phase23_resume` has an MPS leg ~105 s); full ~50-55 min (Phase 39: 4300 passed / 4 skipped) |

### Phase Requirements → Test Map
| Req / Decision | Behavior | Test Type | Automated Command | File Exists? |
|---|---|---|---|---|
| NOISE-01 / SC1 (S) | `E2_S` = `results/phase36_budget.json::e2_seed_count` (read, not typed), `SEEDS = seed_list()[:E2_S]`; slot census + ordering legs green | unit + census | `pytest tests/test_phase40_prereg.py -k "e2_s or seeds"` ; `pytest tests/test_phase35_prereg.py -k "slot_census or slot_ordering"` | ❌ W0 |
| NOISE-01 (per seed, denominators) | per seed, per group, 7 non-targets + target with `n_answerable/27` and per tier 14/13 via `_pooled_rows`; built from the arm records, never from their `per_fact` | unit on committed real records (`phase19_arm_retrain.json`, `phase18_arm_adapter-on.json`) | `pytest tests/test_phase40_prereg.py -k "rows or denominator"` | ❌ W0 |
| NOISE-02 / D-02 | pair d = `nontarget_noise_floor(nontarget_deltas(...))`; on committed records reproduces 0.14814814814814814 (replicate) and 0.2592592592592592 (taught→M2) | unit (real records) | `pytest tests/test_phase40_prereg.py -k pair` | ❌ W0 |
| D-03 / D-04 | group floor = mean over C(S',2) pairs; published = max of groups; max/min/all pairs; per-slot range and SD; synthetic truth table incl. ties and S' = 2 | unit (pure) | `pytest tests/test_phase40_prereg.py -k "floor or extras"` | ❌ W0 |
| NOISE-02 (no amendment) | record carries `phase19_floor.NONTARGET_NOISE_FLOOR` and `phase35_prereg.e1_condition_b_margin()` (0.2962962962962963) read, not typed; `results/phase19_noise_floors.json` and `scripts/phase19_floor.py` byte-unchanged since their last commit (git) | unit + git | `pytest tests/test_phase40_noise.py -k "beside or margin"` | ❌ W0 |
| D-05 | the estimator entry text names sampling noise and common random numbers | unit (AST over the entry string, not grep) | `pytest tests/test_phase40_prereg.py -k sampling` | ❌ W0 |
| D-06 / D-15 | driver trains full then M2 then A2 full then A2 M2 per seed in `seed_list()` order; one ledger attempt per seed; a crash mid-seed drops it; stop checked by `require_launch` before each seed | unit (stubbed train/score, tmp ledger) | `pytest tests/test_phase40_noise.py -k "order or whole_seed or crash or stop"` | ❌ W0 |
| D-07 / P-2 | tensor equality + re-serialized-name digest vs `22e66552…`, `f12ab4c3…`, `3fd5aba4…`; draw identity vs `phase19_arm_retrain.json`; descriptive | unit (tiny tensors in tmp) + rehearsal | `pytest tests/test_phase40_noise.py -k "identity or digest"` | ❌ W0 |
| D-08 | field-by-field table, each field with its committed source; tensor identity statement | unit | `pytest tests/test_phase40_noise.py -k d08` | ❌ W0 |
| D-09 / D-10 | gap = on − off from each full A2 record; off == the committed 4.573349214207799 read from `results/phase19_noise_floors.json`; `pre == post`; `gap_noise_floor` = mean of |Δgap| over pairs, max beside, finite ≥ 0 | unit | `pytest tests/test_phase40_prereg.py -k gap` | ❌ W0 |
| D-11 / D-13 / D-14 | ruling quoted verbatim from the CONTEXT bullet at its commit; projection reproduces `front_hours.E2` at committed caps; D-13 NLL counts derived; projection ≤ stop; total; `approval_block()` in every record | unit | `pytest tests/test_phase40_prereg.py -k "approval or projection"` | ❌ W0 |
| D-12 | 25 full×M2 signed per-slot differences, 5 same-seed marked, beside v3.0 `delta_taught_to_m2` read from `phase19_run.RETRAIN_SCORES_PATH` | unit | `pytest tests/test_phase40_prereg.py -k d12` | ❌ W0 |
| D-16 | one fill holding both estimators, frozen mappingproxy | unit | `pytest tests/test_phase40_prereg.py -k fill` | ❌ W0 |
| Contract → Phase 41 (consumer feed) | a `phase40_noise_floor.json` built by the real `build_record` from real committed arm records (and, at rehearsal, the rehearsal record) passes `phase35_prereg.fill("e1_condition_c_band_inputs", ...)` with tmp `_REPO_ROOT` and synthetic band-input records; band equals `mitigation_gate.dialogue_gap_band(control_gap=..., gap_noise_floor=<record value>)` | integration (CPU) | `pytest tests/test_phase40_noise.py -k consumer` | ❌ W0 |
| SC3 ordering | prereg and its test first-added before every `results/phase40_*`; records write-once | git ancestry | `pytest tests/test_phase40_prereg.py -k "frozen or first_added or records_at_commit"` | ❌ W0 |
| Hygiene | no `inject_lora`, no `os.replace`, no `== 10` in tests, `train_arm(` registered, instruments imported not redefined (AST), every prereg function called by a test, zero skips | AST census | `pytest tests/test_phase40_prereg.py tests/test_phase40_noise.py -k "census or ast or skips"` ; `pytest tests/test_phase23_resume.py -k inert` ; `pytest tests/test_phase21_sc5.py tests/test_lora_inject.py` | ❌ W0 |
| Rehearsal | full-shape CPU rehearsal (MPS hidden, rehearsal arm names, scratch root, tmp ledger) → emit → report → consumer feed, `REHEARSAL_EXIT=0`, real tree unchanged | manual-run script (detached) | `tail -1 <scratch>/rehearsal40.log | grep -qx REHEARSAL_EXIT=0 && test "$(git status --porcelain -- scripts src results tests ledger | wc -l)" -eq 0` | ❌ W0 |

### Sampling Rate
- **Per task commit:** quick run + cross-phase guards
- **Per wave merge and after each `results/phase40_*` / ledger commit:** full suite
- **Phase gate:** full suite green on the committed state before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_phase40_prereg.py` — fills, entries, ancestry, estimator on committed real records
- [ ] `tests/test_phase40_noise.py` — driver refusals, per-seed unit, emit, consumer feed
- [ ] one register line + sum bump in `tests/test_phase23_resume.py`
- Framework install: none

## Security Domain

`security_enforcement` is absent from `.planning/config.json` (treated as enabled). No network, auth,
or user input; the relevant controls are integrity ones.

| ASVS Category | Applies | Standard Control |
|---|---|---|
| V2/V3/V4 | no | — |
| V5 Input Validation | yes (records, adapters) | `_prove` refusals; `load_adapter` with `weights_only=True`; schema checks on consumed records |
| V6 Cryptography | yes (digests only) | `hashlib.sha256` (stdlib) |

| Pattern | STRIDE | Mitigation |
|---|---|---|
| Record overwritten after approval | Tampering | write-once refusals; `atomic_write_json`; ancestry tests |
| Adapter swapped before Phase 41 reuse | Tampering | sha256 + path in the record; never rename/copy (stem-dependent digest) |
| Pickle code execution | Elevation | adapters via `load_adapter(weights_only=True)`; `latest.pt` only own trusted files |
| Unledgered MPS hours | Repudiation | ledger start/end per seed; rehearsal with MPS hidden |

## Sources

### Primary (HIGH confidence — repo code and committed records, read this session)
- `scripts/phase35_prereg.py` :59-69 (contracts), :156-191 (`_prove_entry`), :357-375, :708-719 (`e2_min_seeds`), :773, :1133-1138, :1173-1187, :1700-1770, :1773-1776, :1797-1866, :1882-1888
- `scripts/teach_persona.py` :357-393, :1214-1283, :1672-2140; `src/personacore/config.py:21-32`
- `scripts/phase19_erasure.py` :1025-1120, :1174-1416, :1420-1520, :2541-2600, :2704-2955, :2996-3026, :3604-3716
- `scripts/phase19_run.py` :116-125, :535-560, :620-648, :1584-1906
- `scripts/phase36_probe.py` :357-441, :986-1131; `scripts/phase36_ledger.py` :1-80, :279-460; `scripts/phase36_caps.py`
- `scripts/phase37_r1b.py`; `scripts/phase38_prereg.py` :150-228; `scripts/phase38_rank.py` :242-420, :621-633; `scripts/phase39_prereg.py` :198-410; `scripts/phase39_ctx.py` :344-372, :564-593, :970-975, :1098-1117, :1244-1260
- `tests/test_phase23_resume.py` :60-345; `tests/test_phase21_sc5.py` :170-300; `tests/test_lora_inject.py` :261-480; `tests/test_phase25_driver.py:340-366`; `tests/test_phase35_prereg.py` :2166-2226, :2448-2640; `tests/test_phase39_prereg.py`
- `results/phase36_budget.json`, `results/phase36_probe_e2.json`, `results/phase19_*.json`, `results/phase18_arm_adapter-on.json`, `results/phase38_rank.json`, `results/phase39_ctx.json`, `results/phase14_teaching_run.log`, `results/phase19_retrain_training.log`, `ledger/v6_mps_ledger.jsonl`

### Secondary / Tertiary
- None external. A1 (CPU draw rate) is an inference from `39-07-SUMMARY.md` and is LOW confidence.

## Metadata

**Confidence breakdown:**
- P-1 / P-2 / D-08 premise: HIGH — measured tensor identity, re-serialization digests, committed PPL equality
- Estimator reuse: HIGH — reproduced v3.0 numbers on CPU
- Driver mechanics: HIGH — direct precedents (36 `run_front`, 37 R1b, 38/39)
- Rehearsal cost: LOW — not measured

**Research date:** 2026-10-05
**Valid until:** until any pinned module or `results/phase36_budget.json` changes (re-run M5 before launch)
