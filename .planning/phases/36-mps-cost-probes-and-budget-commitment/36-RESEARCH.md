# Phase 36: MPS Cost Probes and Budget Commitment - Research

**Researched:** 2026-10-02
**Domain:** In-repo MPS timing probes, a pre-registered resource budget, a milestone-wide MPS ledger (PersonaCore v6.0)
**Confidence:** HIGH on the contract and repo mechanics (every claim read at path:line). MEDIUM on the hours arithmetic (built from committed numbers, but the E1/E3 unit definitions belong to Phases 41/42).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

All decisions below were decided by Rafael in discuss-phase 36 (2026-10-02).

#### Carried forward (already locked, not re-asked)
- The budget-record contract is fixed by `scripts/phase35_prereg.py`:
  - `front_hours` is keyed by exactly `V6_MPS_FRONTS = ("probes","R1b","E1","E2","E3","E4","E5","E6")`;
  - the record also carries `total_hours`, `stop_line_hours` and `e2_seed_count`;
  - `_prove_budget` enforces Σ ≤ stop line ≤ `mps_ceiling_hours` (90) and 2 ≤ S ≤ `len(seed_list())` = 5.
  - Every consumer re-validates the record (`_budget_record`).
  - Extra keys are allowed: the check is `fields <= set(record)`.
- The probe records live at `results/phase36_probe_*.json`, the declared input of
  `v6_budget_and_stop_line`. Phase 39's `e6_entry_subset` also consumes them directly.
- E2's S is CHOSEN here, in the budget record. Phase 40's `e2_S` only reads it (35-CONTEXT Addendum
  to D-15).
- Per-fill-file ordering (Phase 35 Plan 04):
  - the Phase 36 fill file follows the probe records it consumes;
  - it precedes `results/phase36_budget.json`;
  - once the budget record is tracked, every phase-36 slot must be filled.
- The ARCAL precedent (Phase 31): probes are discarded and isolated, and gate nothing; the budget
  records the formula, every input and its source path, so the total can be recomputed from
  committed files.

#### Principle for every probe
- **D-01:** A probe measures TIME, never a result. Each probe runs on a configuration whose result
  is already published. It records only seconds and counts (steps, draws, tokens), never a new
  recall, rank or extraction reading. Generated text is discarded and no success is counted. If a
  front has no published configuration to probe, Rafael is told which one BEFORE it runs. The two
  such fronts known so far were ruled on in this discussion: E6 anchor generation (D-07) and E3 at
  T = 800 (D-05).
- **D-02:** Uncertainty comes from measurement, not from an invented multiplier:
  - each probe measures at least two repetitions of its unit, or the per-unit distribution within
    one run;
  - the budget uses the high bound;
  - wherever a historical wall-clock exists on record (Phase 19, v4.0, v5.0, Phase 26), the probe
    is compared with it;
  - a divergence above **25%** is investigated BEFORE the budget is committed.
  - Known coverage: Phase 26 records carry only `scoring_seconds`
    (`results/phase26_canary_sources.json`), so that comparison covers scoring only.

#### Probe set
- **D-03 (E1):** The probe takes the exact E1 reading:
  - A2 only, on the eight facts' questions (the 216-entry A2 corpus), at K = 16 (`CURVE_K`) and
    K = 48 (`FULL_FIDELITY_K`);
  - fixed cost separated from per-draw cost;
  - configuration: the published Phase 19 setup, `pet_name`, seed 1337, greedy ordering, k = 78.

  The Phase 31 probe (416 extraction questions in four families plus taught and held-out recall)
  is recorded beside it for comparison and never extrapolated from.
- **D-04 (R1b):** R1b has no probe of its own:
  - its price is the K = 48 reading of the E1 probe;
  - that reading is checked against `results/phase19_arm_erased.json::config.wall_clock_min` = 68.584
    (MPS, k = 78, K = 48, seed 1337);
  - a divergence above 25% means STOP and investigate before the budget.
- **D-05 (E3):** The step-count cap is **T ≤ 800** (`kind = preference`: 4× v4.0's `STEP_BUDGET` =
  200). Two runs:
  - **T = 200:** the published v4.0 recipe (lr 3e-4, batch 8, n = 8) at an already-published σ,
    training plus scoring. Compared with the v4.0 point record's wall-clock for the same point under
    the 25% rule (`results/phase25_point_dp_n8_*.json` carries the training/scoring seconds).
  - **T = 800:** timing-only, training ONLY (seconds and steps), no scoring. The scoring cost does
    not depend on T and comes from the T = 200 run.

  This satisfies COST-01's "one DP configuration at the grid's longest step count" and checks that
  cost is linear in steps. The P22 assertion (RECIPE-04) runs for T = 800. Verified 2026-10-02:
  `phase35_prereg.p22_onset_sigma(800)` = 0.1578 < 0.5, so the σ ∈ {0.5, 1} grid is clear.
- **D-06 (E4):** E4 gets a reserve with a cap:
  - it covers up to **3 points**, each one training run plus scoring, priced at **T = 200** from the
    E3 probe;
  - the derivation must say why: E4 audits v4.0's ε claims, which were made at T = 200 with the
    v4.0 recipe, and the audit uses the same recipe, changing only canary inclusion;
  - auditing another recipe would be another front and needs Rafael's approved;
  - if Phase 43 cuts E4 (AUDIT-02), the hours stay unused, and nothing is reallocated without
    Rafael's approved.
- **D-07 (E6):** Anchor-context generation has no published configuration. Phase 18 only scored
  NLL and rank at the assistant-turn anchor. The probe is a timing-only anchor generation run:
  - it uses Phase 19's k = 78 adapter, seed 1337;
  - it records only seconds and token/draw counts; the text is discarded and nothing is scored;
  - the comparison with the A2 context comes from the E1 probe, with no extra run.
- **D-08 (E2, E5):** These follow COST-01 under D-01/D-02.
  - **E2:** an M2 retrain plus its measurement, on the published configuration (Phase 19 retrain
    arm, M2 without `pet_name`, seed 1337; `phase19_arm_retrain.json` wall_clock_min 46.618 for the
    reading).
  - **E5:** a sample of minting clearance and E5 scoring, on the published Phase 17 clearance and
    Phase 18 scoring configurations (their records carry `wall_clock_min`).

#### Probe → hours
- **D-09:** The budget record carries hours per front AND **unit caps per front**:
  - E1: checkpoints per cell;
  - E3: recipes;
  - E5: number and size of sets;
  - E6: entries and adapters.

  The owning phases (41, 42, 38, 39) cannot exceed these caps. Phase 35's rules do not check caps,
  and `scripts/phase35_prereg.py` is a closed pre-registration (its rules must not be edited), so
  the cap enforcement must live in Phase 36's own code and be reachable by the owners' fill files
  and tests. The planner decides the mechanism.
- **D-10:** The front hours use the HIGH bound of each probe's measured range (D-02).

#### Stop line and ledger
- **D-11:** There is ONE cumulative ledger for the whole milestone against the 90 h ceiling, probes
  included.
  - Spent hours are read from the records' own wall-clock fields by a script, never typed.
  - Every MPS phase consults the ledger before it launches.
- **D-12:** A run that crashed or was aborted counts its hours up to its last heartbeat. It appears
  in the ledger marked **"sem registro de resultado"** (no result record), so Rafael can see how
  many hours were lost and on which front. Mechanism: the driver writes a start line and heartbeats
  to an append-only file (the `phase25_run.start_heartbeat` / `beat` LaunchAgent pattern), still
  script-written.
- **D-13:** `stop_line_hours` = **min(1.5 × Σ front_hours, 90)**: the Phase 31 1.5× rule applied
  milestone-wide and capped by the ceiling. Three stops, each a pause plus a checkpoint to Rafael
  with what already ran and the options:
  - (a) one front passes 1.5× its own high bound (the Phase 31 precedent);
  - (b) the cumulative ledger reaches the stop line;
  - (c) **projection check:** before each front launches, if (ledger hours spent + the high bounds
    of the remaining fronts) > 90 h, pause BEFORE launching and bring the cut table. No front
    starts unless it fits whole in the projection.

#### S, the cut table and run mode
- **D-14:** The proposal sets **S = 5**. Nothing is reduced automatically.
  - S below 3 never enters the cut table without asking Rafael. This is stricter than
    `e2_min_seeds` = 2, so Phase 36's own code must enforce S ≥ 3 for the table.
- **D-15:** If the fronts do not fit 90 h, Rafael gets a table: each cut option, the hours it
  saves, and the scientific question it loses. The rows go in this order:
  1. the E4 reserve;
  2. E6 anchor generation on fewer adapters;
  3. S down to 3;
  4. E3 whole;
  5. E1 checkpoints.

  R1b and the E1 core are last. Claude never cuts on its own.
- **D-16:** The probes run as ONE unattended LaunchAgent sequence (the Phase 25/31 plist pattern:
  `caffeinate -dims`, heartbeat jsonl, logs under `logs/`).
  - The probe records may be committed automatically, but only if the plan lists them in advance.
  - The budget record is committed ONLY after Rafael writes approved.
- **D-17:** Every new threshold above is a four-field entry (`value`, `derivation`, `kind`,
  `source`; no proposer field, PREREG-07) committed in Phase 36's pre-registration before the first
  probe record (PREREG-06). This covers the 25% divergence, T ≤ 800, the E4 reserve of 3 points at
  T = 200, the 1.5× per-front stop, the stop-line formula, the projection check, S ≥ 3 for the
  table and the cut order. Values that are preferences are labelled `kind = preference`.

### Claude's Discretion
- Probe prefixes and paths, provided they cannot collide with any later phase's record or sidecar
  paths (the Phase 31 D-02 isolation guard).
- Record schemas, provided each carries per-stage wall-clock, repetition counts, provenance
  (git_sha, head_at_write, module_sha256) and a "gates nothing" marker.
- The ledger's file format and location, provided it is append-only, script-written, counts every
  launched run, and flags runs without a result record.
- How the unit caps are enforced on the owning phases (D-09) without editing `phase35_prereg.py`.

### Deferred Ideas (OUT OF SCOPE)
- Auditing a recipe other than v4.0's in E4: another front, needs Rafael's approved (D-06).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| COST-01 | Every MPS front is priced by a probe on the M3 before any budget: the exact E1 reading (A2 only, eight facts' questions, K = 16 and K = 48) with fixed cost separated from per-draw cost, an M2 retrain plus its measurement, one DP configuration at the grid's longest step count, a sample of minting clearance and E5 scoring, and anchor-context generation; the Phase 31 probe recorded beside the E1 probe, never extrapolated from | §"Probe entry points per front" names the exact function for each probe, what it writes, and how to isolate it. §"Historical wall-clock" lists every 25% comparator with its JSON key path and verified value. §"Fixed vs per-draw separation" gives the mechanism. |
| COST-02 | Budget and stop line committed from the probes before the first measured point, inside 90 h, probes included; if the fronts do not fit, halt and take the cut options to Rafael | §"The Phase 35 contract" (exact `fill` signature, derivation shape, ordering legs). §"Commit sequence" orders prereg, probes, fill file, budget. §"Ledger" and §"Unit caps" cover D-09/D-11..D-13. §"Hours arithmetic" estimates whether the cut-table branch is likely. |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Python 3.11 venv at `.venv` is mandatory; never validate on the system 3.14. Verified: `.venv/bin/python` is 3.11.15, torch 2.7.1, MPS available, on an Apple M3 Pro.
- Python plus PyTorch only. No HF model code. No new dependency is needed for this phase (see Standard Stack).
- Primary training is local M3/MPS in fp32, with no AMP, no `GradScaler` and no `torch.compile`.
- Logging is offline (CSV/JSON). No wandb or network.
- Tests run CPU-only and GPU-free in CI. MPS-only legs are skipped with an attributed count (PREREG-08).
- GSD workflow: edits only through GSD commands. Planning files: never use the gsd-sdk mutation handlers. They have corrupted STATE/ROADMAP/REQUIREMENTS in thirteen sessions (user memory). Edit STATE, ROADMAP and REQUIREMENTS by hand.
- Global: record durable outcomes in the Obsidian vault (orchestrator's job at phase close). Never commit or push unless asked. Never commit secrets.

## Summary

Phase 36 is mostly plumbing around a closed contract. `scripts/phase35_prereg.py` already fixes what the budget must contain and how it is validated. Phase 36 has to do four things: (1) commit its own small pre-registration of the D-17 entries, with an ancestry test, BEFORE any probe record; (2) run five timing probes (E1, E2, E3, E5, E6) on the M3 under one LaunchAgent, each on an already-published configuration, isolated under its own prefix, and emit write-once `results/phase36_probe_*.json`; (3) write a fill file `scripts/phase36_*prereg.py` that computes the hours from those records and calls `phase35_prereg.fill("v6_budget_and_stop_line", ...)`; (4) after Rafael's approved, emit `results/phase36_budget.json`. The ledger and the unit-cap checker are new Phase 36 code that later phases import.

The main structural fact is that the Phase 35 ordering legs force **two separate Phase 36 modules**. The D-17 entries must precede the first probe record. The `fill(...)` file must follow every probe record (leg (b), `tests/test_phase35_prereg.py:2529-2535`) and precede the budget record (leg (a), :2518-2528). It also can never be edited after the budget record exists, because leg (a) checks EVERY commit of the fill file. A second fact matters for the halt branch: no non-probe `results/phase36_*` file may be tracked while the slot is unfilled (leg (c), :2499-2506). So a cut table must never be written under `results/phase36_*`.

The most decision-relevant measurement: every A2 reading on record costs 43–69 min at K = 48 (`results/erasure_kstar_arm_k0{08,16,32,64}.json`, `results/phase19_arm_{erased,retrain,replicate}.json`), and E1 has 16 cells (4 targets × 2 orderings × 2 seeds). At 2–5 checkpoints per cell, E1 alone plausibly takes 35–60 h of the 90 h. **The halt/cut-table branch is a realistic outcome, so plan it as a first-class path, not as an exception.**

**Primary recommendation:** Copy the Phase 31 probe/budget architecture: torch-free at import, write-once emits behind dirty-tree refusals, a provenance block, a CPU live-path fixture, a plist mirrored from `com.personacore.phase31.probe.plist`. Run the E1 K = 48 reading through the pin's own `phase19_erasure.run_erasure_arm` with the committed `ordered_prefix[:78]` (the `erasure_kstar_run.measure` route). Time each draw by wrapping `phase14_recall`'s draw function at runtime. Put the D-17 entries, the ledger and the cap checker in Phase 36 modules that never touch `phase35_prereg` privates.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| D-17 threshold entries + ancestry | CPU rule module (`scripts/phase36_prereg.py`) | git history (ancestry test) | Must be torch-free and frozen before the first probe record; the guard reads git, not the tree |
| Probe execution (timing) | M3/MPS driver under LaunchAgent | data/ sidecars (gitignored) | Only the M3 measures MPS time; sidecars allow per-stage resume and keep text out of results/ |
| Probe records | Write-once JSON under `results/phase36_probe_*.json` | git (commit listed in plan) | Declared input of `v6_budget_and_stop_line` and `e6_entry_subset` |
| Hours derivation + budget fill | CPU fill file `scripts/phase36_*prereg.py` → `phase35_prereg.fill` | `results/phase36_budget.json` emit | `fill` is the only legal door; it re-applies `_prove_budget` |
| Unit-cap enforcement (D-09) | CPU module imported by owner fill files | Phase 36 test that scans owner fill files | Cannot live in `phase35_prereg.py` (closed) |
| Ledger (D-11..D-13) | CPU module + append-only launch/heartbeat file | committed records' own wall-clock fields | Reads committed records for spent hours and heartbeats for lost runs |

## Standard Stack

### Core (all already installed — nothing new)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib (`json`, `hashlib`, `subprocess`, `time`, `datetime`, `math`, `ast`, `fnmatch`, `threading`) | 3.11.15 | Rule modules, ledger, emit, tests | Every v5.0/v6.0 rule module is stdlib-only at import (`scripts/phase35_prereg.py:24-28`, `scripts/phase31_budget.py:12-13`) |
| torch | 2.7.1 (verified `.venv`) | MPS probe runs only, imported lazily | Same version every Phase 17–31 MPS record carries (`results/phase31_probe_point.json::provenance.run.torch_version` = 2.7.1) |
| pytest | in `.venv` | CPU tests | `make test` = `.venv/bin/pytest -q` (Makefile) |

### Supporting (in-repo modules to import, never edit)

| Module | Use |
|--------|-----|
| `phase35_prereg` | `fill`, `V6_MPS_FRONTS`, `ENTRIES`, `V6_RESULT_PATHS`, `seed_list`, `p22_onset_sigma`, `E3_SIGMAS`, `CURVE_K`, `FULL_FIDELITY_K`, `STEP_BUDGET`, `ENTRY_FIELDS`/`KINDS`/`FORBIDDEN_PHRASE` (public only) |
| `phase25_run` | `atomic_write_json` (:118), `start_heartbeat`/`beat` (:298-368), `device()` (:407), `disk_precheck` (:439) |
| `phase19_erasure` | `run_erasure_arm` (:2732), `ablate_components`, `value_span_nll_mean` (:2407) |
| `phase14_recall` | `draw_all` (:846), `load_adapted_model` |
| `phase25_points` | `train_stage` (:350), `point_plan` (:234), registered `train_arm` call site |
| `teach_persona` | `score_arm` (:2466), `arm_outputs` (:357), `train_arm` (:1672) |
| `personacore.provenance` | `git_sha`, `refuse_if_dirty` (`src/personacore/provenance.py:28,47`) |

**Installation:** none. `pip install -e ".[cpu,dev,demo]" --extra-index-url https://download.pytorch.org/whl/cpu` is already done in `.venv`.

## Package Legitimacy Audit

No external package is installed by this phase. Everything is stdlib or an existing in-repo module. slopcheck not run (nothing to check).

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| (none) | — | — | — | — | — | — |

**Packages removed:** none. **Packages flagged:** none.

## The Phase 35 Contract Phase 36 Must Satisfy (read verbatim)

### The slot and its rule

- `V6_RESULT_PATHS` declares exactly two Phase 36 paths: `"results/phase36_probe_*.json"` (COST-01) and `"results/phase36_budget.json"` (COST-02) (`scripts/phase35_prereg.py:317-319`). `ARTIFACT_PATHSPECS` is derived from these as `results/phase36_*` … `results/phase45_*` (:336).
- `V6_MPS_FRONTS = ("probes", "R1b", "E1", "E2", "E3", "E4", "E5", "E6")` (:768). `_BUDGET_RECORD = "results/phase36_budget.json"` (:769).
- `_SLOTS["v6_budget_and_stop_line"] = {"owner_phase": 36, "rule": _rule_v6_budget_and_stop_line, "input_records": ("results/phase36_probe_*.json",)}` (:1792-1796).
- `fill(slot, **inputs)` refuses an undeclared slot, then calls `SLOTS[slot]["rule"](**inputs)` (:1882-1888).
- `_rule_v6_budget_and_stop_line(*, front_hours, stop_line_hours, e2_seed_count, input_records, derivation)` (:1145-1170) runs:
  1. `_prove_budget(front_hours, stop_line_hours, e2_seed_count)` (:955-988), which proves:
     - keys == `V6_MPS_FRONTS`;
     - every value finite and ≥ 0;
     - `total = math.fsum(values) ≤ stop_line_hours ≤ ENTRIES["mps_ceiling_hours"]["value"]` (90, :682-687). Failing this raises "HALT and take the cut options to Rafael (COST-02)";
     - `e2_seed_count` is an int, not a bool, with `2 ≤ S ≤ len(seed_list())`. Verified: `seed_list()` = `(1337, 2024, 1338, 2025, 1339)`, length 5.
  2. `_consume_inputs("v6_budget_and_stop_line", chosen, input_records, derivation)` (:910-952), where `chosen = {"front_hours": dict(front_hours), "stop_line_hours": ..., "e2_seed_count": ...}` (:1157-1161).
  3. Returns a read-only `{front_hours, total_hours, stop_line_hours, e2_seed_count}`.

`_consume_inputs` requires all of the following. Each is a refusal the fill file must satisfy:
- `derivation` passes `_prove_entry`: exactly the four fields, `kind ∈ {derived, preference}`, no `proposer`/`adopted_by`, non-empty `derivation`/`source` strings without the forbidden phrase (:160-191).
- `derivation["value"] == chosen`. This is dict equality, so key order does not matter (:902-907, :916-917).
- `input_records` is a non-empty tuple of str with no duplicates (:918-927). Each entry is:
  - repo-relative with no `..`;
  - a match for `results/phase36_probe_*.json`;
  - **named inside `derivation["source"]`** (:940);
  - an existing file (:941).
- Every declared pattern is matched by at least one consumed path (:942-946).

`_budget_record(records)` (:991-1006) is what consumers re-run. It requires `{"front_hours","total_hours","stop_line_hours","e2_seed_count"} <= set(record)` and `record["total_hours"] == fsum(front_hours)`, exact float equality. A JSON round trip of a Python float is exact. **Never round `total_hours` or the front hours before writing them.**

### Consumers of the budget record (later owners)

| Slot | Owner | How it reads Phase 36 |
|------|-------|----------------------|
| `e2_S` | 40 | `_rule_e2_S` reads `e2_seed_count`; refuses if `front_hours["E2"] <= 0` (:1173-1188, :1184) |
| `e1_checkpoint_grid` | 41 | refuses if `front_hours["E1"] <= 0` (:1229); the grid is the caller's choice and caps are NOT checked here |
| `e3_grid_subset` | 42 | refuses if `front_hours["E3"] <= 0` (:1457); a fifth recipe needs a derivation citing `results/phase36_budget.json` (:1486-1490); P22 is checked for every T used (:1491-1499) |
| `e6_entry_subset` | 39 | consumes `results/phase36_probe_*.json` directly, not the budget (:1834-1838); indices must lie inside the 216 A2 entries (:1674-1691); no cap check |
| `e5_set_sizes` | 38 | consumes `results/phase38_minting*.json` only; sizes `1..512` (:1655-1671); no Phase 36 link |

So **E2, E1 and E3 must each have hours > 0** or their owners' fills refuse. An E3 cut to 0 h by the cut table would block Phase 42 by construction, which is the intended effect.

### The slot census (applies to EVERY file under `scripts/**` and `src/**`)

`_slot_census_failures` (`tests/test_phase35_prereg.py:2166-2269`) parses every `scripts/**/*.py` except the prereg, plus `src/**/*.py`. Any Phase 36 module fails the census if it:
- calls `phase35_prereg.fill("v6_budget_and_stop_line", ...)` anywhere but a file matching `scripts/phase36_*prereg.py`, or more than once in the tree;
- binds the call to anything but a module-level single-target `V6_BUDGET_AND_STOP_LINE = phase35_prereg.fill(...)` (the whole value; :2194-2198);
- reads any `phase35_prereg._*` private name (:2215-2217). **So `_prove_budget`, `_budget_record`, `_prove_entry` and `_REPO_ROOT` are off-limits in scripts.** Tests are not scanned and may use them;
- holds the string constant `"phase35_prereg"` anywhere (:2246-2247, "dynamic import by name"), aliases the module, uses `from phase35_prereg import fill|*|SLOTS`, or touches `SLOTS[...]["rule"]`.

### The per-fill-file ordering legs, applied to Phase 36

`_slot_ordering_failures` (`tests/test_phase35_prereg.py:2475-2536`), with Phase 36's single slot whose input is own-phase (so `free` is empty and `exempt = {"results/phase36_probe_*.json"}`, :2513-2516):
- **(a)** every commit of the fill file strictly precedes the first add of every `results/phase36_*` file that is not a probe record (:2518-2528). Two consequences: the fill file cannot be edited after the budget record is added, and no other phase-36 record may come before the fill file.
- **(b)** the first add of every tracked `results/phase36_probe_*.json` strictly precedes the fill file's FIRST commit (:2529-2535). **No probe record may ever be added after the fill file.** This includes Phase 39 wanting an extra probe later.
- **(c)** once any phase-36 record that is not an input of any phase-36 slot is tracked, `v6_budget_and_stop_line` must be filled (:2499-2506).

The green planted sequence in the test is exactly `[probe_a.json] → [phase36_prereg.py with the fill] → [budget.json]` (:2585-2589). The red sequence `b36` puts a probe after the fill file (:2637-2644).

Phase 39's `e6_entry_subset` also declares `results/phase36_probe_*.json`. Leg (b) therefore requires every probe record to precede Phase 39's fill file too. That holds automatically if Phase 36 finishes first.

### Phase 35's own ancestry freezes at Phase 36's first record

`test_phase35_prereg_is_frozen_before_every_v6_result` (`tests/test_phase35_prereg.py:433-441`) requires every commit touching `scripts/phase35_prereg.py` to precede the first add of every `results/phase3[6-9]_*` / `phase4[0-5]_*` file. **After the first `results/phase36_probe_*.json` is committed, `scripts/phase35_prereg.py` can never be touched again** (STATE.md stopped_at confirms "the prereg freezes at Phase 36's first record"). Any defect found in it later goes through a dated continuation: a new continuation module (the `scripts/phase23_resume_prereg.py` precedent) or `scripts/_addendum.py` for markdown. Never an edit.

## Commit Sequence (derived from the legs above)

```
C1  scripts/phase36_prereg.py  (D-17 entries, NO fill() call)  + tests/test_phase36_prereg.py
      └─ ancestry test: every commit of phase36_prereg.py ≺ first add of every results/phase36_*
C2  probe driver(s) + ledger + caps modules + plist + tests          (may be several commits;
      └─ must be COMMITTED before the run: refuse_if_dirty)            drivers are not frozen,
                                                                       but see WR-02 below)
RUN one LaunchAgent sequence on the M3 (probes write data/ sidecars only)
C3  results/phase36_probe_<front>.json  (write-once emits; auto-commit only if listed in plan)
      ── 25% comparisons evaluated here; divergence > 25% → STOP, investigate, before C4
C4a FITS:  scripts/phase36_budget_prereg.py  (V6_BUDGET_AND_STOP_LINE = phase35_prereg.fill(...))
           — committed only after Rafael's approved is RECOMMENDED (see Open Question 4)
C5a        results/phase36_budget.json  (emit; committed ONLY after Rafael writes approved)
C4b HALT:  fill() raises "HALT"; NO fill file, NO results/phase36_* non-probe file;
           cut table goes to Rafael as a checkpoint (.planning/… or printed), never results/phase36_*
```

`scripts/phase36_prereg.py` matches `owner_prereg_glob` (`scripts/phase36_*prereg.py`), but `_fill_sites` ignores files without a `fill()` call (`tests/test_phase35_prereg.py:2469-2471`). Naming the entries file `*_prereg.py` is therefore safe as long as it never calls `fill`.

## The Phase 31 Precedent, End to End

| Artifact | Path:line | Reuse? |
|----------|-----------|--------|
| Probe identity and isolation guard | `scripts/phase31_probe.py:59-64` (`PROBE_KEY="probe31_advr_n64"`, `PROBE_PREFIX="probe31"`), `probe_plan` label guard `:147-152` (refuses labels starting `phase3` or `phase25_calibration`) | **Pattern.** Use `probe36` and extend the guard to refuse `phase3`/`phase4` (v6.0 owns `results/phase36_*`…`phase45_*`) |
| Pinned modules + provenance | `PINNED_MODULES` `:73-84`; `_write_record` `:537-555` writes `provenance = {run{git_sha,device,torch_version,started_utc,finished_utc}, module_sha256, git_sha, head_at_write, written_utc}` | **Pattern.** Add the 31-REVIEW WR-02 fix: refuse the emit if `git diff --name-only <run_git_sha> HEAD -- PINNED_MODULES` is non-empty (`.planning/milestones/v5.0-phases/31-…/31-REVIEW.md:76-95`) |
| Write-once emit | `_emit_target` `:512-534` (overwrite refusal first, then `refuse_if_dirty(pathspec=("scripts","src","results", ":(exclude)<out>"))`) | **Copy** |
| Heartbeat during run | `run_point_probe` `:384` `start_heartbeat(path, state)`; final `beat(..., stage="done")` `:489` | **Reuse** `phase25_run.start_heartbeat`/`beat` |
| Live-path CPU fixture | `tests/test_phase31_probe.py:310-389` (uses `test_phase22_wiring._e2e_env`, patches `phase25_run._DEVICE="cpu"`, the driver `_ROOT`, `refuse_if_dirty`; spies the real stages) | **Pattern.** This is what defeats "dry-run tests hide an unwired driver" |
| Stray guard | `tests/test_phase31_probe.py:281-298` (`_PROBE31_GLOBS`, real-tree strays before/after) | **Pattern** with `*probe36*` globs |
| Budget builder | `scripts/phase31_budget.py`: `FORMULA` dict `:68-107`, `build_record(tracked)` recomputes from committed blobs `:334-369`, `emit` `:372-409`, `STOP_LINE_FACTOR = 1.5` `:42` | **Pattern.** The Phase 36 hours logic is new (different fronts) |
| Recompute + ancestry tests | `tests/test_phase31_budget.py:378-428` (honest branch when untracked; `_assert_frozen_before(BUDGET, points)` with a natural-RED non-vacuity leg) | **Copy the shape** |
| LaunchAgent | `artifacts/com.personacore.phase31.probe.plist`: `caffeinate -dims` + `.venv/bin/python` + `--heartbeat data/phase25_heartbeat.jsonl`, `RunAtLoad=false`, `KeepAlive=false`, `PERSONACORE_SWEEP_ACTIVE=1` (:53), logs under `logs/`; mirrored-plist test `tests/test_phase31_probe.py:981-1002` | **Copy** to `artifacts/com.personacore.phase36.probe.plist` |
| Phase 31 records (beside E1) | `results/phase31_probe_point.json` stages (s): draw 5620.57, recall 1079.44, train 633.46, measure 89.29, score 0.10; `total_seconds` 7422.87; device mps | **Read and embed** (path + sha256 + stage seconds) in the E1 probe record under a "beside, never extrapolated" key |

Phase 31 review warnings to carry forward:
- **WR-01** (`31-REVIEW.md:53-74`): `train_arm`-style helpers write `results/<prefix>_<arm>/run.csv`. That untracked dir under `results/` trips `refuse_if_dirty` on any restart or emit. Move it to `data/` in the same process (the `phase31_probe.relearn_moves` / phase25_points "csv idiom", `scripts/phase31_probe.py:633-668`), or exclude it from the run-time pathspec.
- **WR-02**: compare the run's git sha against HEAD for the pinned modules before writing.

## Probe Entry Points per Front

Isolation rule for every probe: prefix `probe36`. It must not start with `phase3`/`phase4`/`phase25_calibration`, and no arm name may match an existing stray glob: `data/phase27_*`, `data/phase25_phase27_*`, `data/persona_relearn_attacker_*`, `results/phase27_*`, `checkpoints/phase27_*` (`tests/test_phase27_relearn.py:809-823`), `*probe31*` (`tests/test_phase31_probe.py:281-287`), or the phase32 globs (`tests/test_phase32_live.py:77-81`). All text-bearing outputs go to gitignored `data/`/`checkpoints/` (`.gitignore`: `checkpoints/`, `*.pt`, `logs/`, `data/`) and are deleted or ignored afterwards (D-01: text discarded).

### E1 (+ R1b): A2 on the k = 78 erased adapter, K = 16 and K = 48

- **Exact published entry point:** `phase19_erasure.run_erasure_arm("erased", device, components=ordered_prefix[:78], record_path=<isolated path>)`. This is the route `scripts/erasure_kstar_run.py:109-139` used for k = 8/16/32/64 (`components` from `results/phase19_collateral_curve.json::ordered_prefix`, :136; the call is at :139).
- **Verified this session:** `ordered_prefix` has 78 entries and equals `results/phase19_arm_erased.json::config.ablated_components`. `checkpoints/persona_adapter.pt` sha256 equals the curve record's `adapter_in_sha256`. `checkpoints/phase19_m1_erased_adapter.pt` equals `adapter_out_sha256`.
- **What `wall_clock_min` covers.** It spans `time.time()` at :2802 to :2924-2925:
  - preflight;
  - model load;
  - pre-erasure capability: exposure on 8 core slots, the dialogue PPL pair and retention PPL on `data/retention_val.bin`;
  - ablation;
  - 216 A2 entries × K draws;
  - post-erasure capability;
  - scoring.

  It EXCLUDES the M1 ordering/stop search (`_selected_components` runs before the call, :3558-3587, :3675-3689). A probe that passes the committed prefix is therefore scope-identical to the 68.584 comparator.
- **Writes:** `record_path` (full draws, i.e. text) with `write_text` (:2947); there is no force flag (:2788-2794). Point `record_path` into a `data/probe36_*` path and delete it after timing is extracted. Never use `arm_record_path` (:2560-2568; it would resolve to `results/phase19_arm_erased.json`).
- **K is not a parameter.** `budget = phase18_record["config"]["k"]` (:2825), where `PHASE18_ARM_RECORD_PATH` = `results/phase18_arm_adapter-on.json` (:1628), K = 48. A literal K = 16 run through the pin is impossible without patching its input. See "Fixed vs per-draw separation" below.
- **Parity:** arm `"erased"` triggers `assert_phase18_parity(config)` (:2854-2855). It holds on the published configuration.
- **R1b price:** the K = 48 total, compared with `results/phase19_arm_erased.json::config.wall_clock_min` = 68.58400233189265 (verified). If Phase 37 decides R1b also re-runs the M1 selection to re-derive k = 78, add `results/phase19_collateral_curve.json::wall_clock_min` = 6.959 min (verified). Flag this for Phase 37 (CONTEXT "Specific Ideas").

### E2: M2 retrain + its reading

- **Training (published configuration):** `phase19_run.retrain_train` (`scripts/phase19_run.py:1584-1670`) calls `tp.train_arm(pin.RETRAIN_ARM, facts=pin.retrain_arm_spec(target.id), ..., prefix=pin.RETRAIN_PREFIX)` (:1645-1652). It hardcodes arm `erase_reference` and prefix `phase19`, whose outputs already exist (`checkpoints/phase19_erase_reference_adapter.pt`), and `train_arm` refuses existing outputs. It is **not reusable as-is.**
- Two options:
  - (i) a new probe call site `tp.train_arm("<probe36 arm>", facts=..., prefix="probe36")`. **That requires a register line in `tests/test_phase23_resume.py::_TRAIN_ARM_CALL_SITES` (:60)**, because `test_resume_from_none_is_inert` greps the literal `train_arm(` across `scripts/` and `tests/`, prose included (:255-292). Any docstring or test string containing `train_arm(` also counts.
  - (ii) monkeypatch `pin.RETRAIN_ARM`/`pin.RETRAIN_PREFIX` at runtime around `retrain_train`. No register edit, but it patches a closed pin's constants at runtime.

  **Recommend (i)**: visible, and the register exists for exactly this.
- **Never train the `real` arm name.** `arm_outputs("real")` resolves to `checkpoints/persona_adapter.pt` regardless of prefix (`scripts/teach_persona.py:382-386`), the shippable adapter.
- **`train_arm` writes `results/<prefix>_<arm>/run.csv`** (`teach_persona.py:390`). Apply the WR-01 move.
- **Training-time comparator:** NONE in JSON. The retrain arm's `wall_clock_min` excludes training (`_cmd_retrain` trains at :3701-3708 before `run_erasure_arm` at :3709-3714). The only figures are the docstring "~81 s" (`scripts/phase19_run.py:1587-1588`, prose, not a record) and `results/phase23_control_floor.json::per_seed[].training_seconds` = 78.37–80.34 s (same teach_persona recipe, 200 steps, MPS). Also: `results/*/run.csv` has a `wall_clock` column that is **the step number, not seconds** (`src/personacore/training/loop.py:915` `wall_clock=step`; every tracked run.csv ends at `200,…,200`). **Never read it as time.**
- **Reading:** `run_erasure_arm("retrain", device, adapter_path=<probe adapter>, record_path=<data/ path>)`. The comparator is `results/phase19_arm_retrain.json::config.wall_clock_min` = 46.61799373229345 (verified; `retrain` is also a parity arm).
- **Full taught adapter (NOISE-01's other retrain):** `arm_spec("real")` has one more fact than M2 (`phase19_run.py:1617`). Training cost scales with the bins, not the fact count. State the derivation explicitly (CONTEXT "Specific Ideas"). Observation, not a decision: `checkpoints/phase19_erase_dialogue_floor_seed{1337,2024}_adapter.pt` already exist (full `real` recipe at seeds 1337/2024, `phase19_erasure._cmd_dialogue_floor` :3604-3672). Whether Phase 40 may reuse them is Phase 40's call. The E2 unit price should not assume reuse.

### E3 (+ E4 reserve): DP training at T = 200 and T = 800

- **Entry point:** `phase25_points.train_stage(plan)` (:350) is an already-registered `train_arm` call site (`tests/test_phase23_resume.py:87`). Phase 31 re-keyed a plan with `dict(action["plan"], point_key=PROBE_KEY, prefix=PROBE_PREFIX)` (`scripts/phase31_probe.py:144`). For E3: `phase25_points.point_plan("dp_n8_sigma0p500000")` (:234-263) re-keyed to a probe36 key/prefix. `phase25_run.run_point` is NOT reusable (`31-CONTEXT.md` code_context: it calls `prove_first_attempt`).
- **Writes:** `data/phase25_<key>_training.json` sidecar (:266-267), which train_stage **silently reuses if present** (:365-373, the Phase 31 D-02 hazard). It also writes `checkpoints/<prefix>_dp_n8_{adapter,latest}.pt` and `results/<prefix>_dp_n8/run.csv` (WR-01 move). The arm bins carry no prefix (`data/persona_dp_n8_train*.bin`) and train_stage unlinks/rebuilds them (:393-397). That is harmless now (v4.0 done), but no v6 phase may run concurrently.
- **T = 800:** steps come from the module global `teach_persona.MAX_STEPS = 200` (:1599), read by `train_arm` at :2007 and asserted by train_stage at :447 (`timed = tp.MAX_STEPS - resumed_from_step`). The plan's `pinned_mechanism.composed_steps` (`STEP_BUDGET`, :177-198) is also compared. A T = 800 probe must set both at runtime: monkeypatch `tp.MAX_STEPS = 800` plus a plan copy with `composed_steps=800`. The Phase 31 CPU fixture did exactly this for its fixture steps (`tests/test_phase31_probe.py:345-349`). `teach_persona.py` itself must stay byte-unchanged, since it is sha-pinned by `results/phase24_token_budget.json` (`scripts/phase25_run.py:419-422`).
- **P22 at T = 800:** verified `phase35_prereg.p22_onset_sigma(800)` = 0.15780356992036104 and `p22_onset_sigma(200)` = 0.07890181429684162 (reproduces P22's 0.078902). Both are below min noised `E3_SIGMAS` = 0.5. The Phase 36 prereg should assert this at import via the public function.
- **Scoring:** `phase25_points.measure_stage` scores taught recall **only when `plan["is_control"]`** (:570-572). A σ = 0.5 point gets no recall from it (the 25-18 defect in user memory). Call `teach_persona.score_arm(arm, fs.LOCKED_FACTS, adapter, device)` (:2466) directly, the instrument `results/phase25_recall.json` names (`instrument: teach_persona.score_arm`).
- **Comparators (σ = 0.5, `results/phase25_point_dp_n8_sigma0p500000.json`, verified):**
  - `training.seconds` 209.06;
  - `measure_seconds` 88.35;
  - `shape_timing.{A1-aggressive 31.38, A1-mild 24.57, A2 25.40, A3 37.87}` min (Σ 119.2 min);
  - recall `results/phase25_recall.json::points.dp_n8_sigma0p500000.scoring_seconds` 1246.87;
  - canary `results/phase26_canary_sources.json::points.dp_n8_sigma0p500000.provenance.scoring_seconds` 5556.24.
  - Recipe: lr 3e-4, batch 8, grad_accum 8, max_steps 200, seed 1337, warmup 20.
- **Linearity check:** T = 800 training seconds vs 4 × T = 200 training seconds (D-05). Note the warmup is fixed at 20 steps (`train_config.warmup_steps`).

### E5: minting clearance sample + E5 scoring sample

- **Clearance (published Phase 17 configuration):** `phase17_persona_gate.main` (:204) builds the unadapted base and calls the imported instrument `phase14_factset_gate.probe_guessability(model, tok, device, forbid, value, questions, *, start_index=0)` (`scripts/phase14_factset_gate.py:111`) per minted value, over that slot's held-out questions. The four mechanical filters are CPU (`phase17_persona_facts.assert_material_passes_filters`).
  - **Historical comparator:** **2.1 min for the 24 values, in MARKDOWN, not JSON**: `results/phase17_personas_report.md:723` ("wall `2.1` min") and `results/phase17_personas_gate_run.log` tail.
  - The `results/phase17_sweep_*.json::wall_clock_min` records (3.09–5.30 min) are the ISO isolation sweeps (104 questions × 9 draws per adapter), **not** clearance. Do not use them as the clearance comparator.
  - Re-clearing the 24 published values is a published configuration (D-01 satisfied); time per value.
- **E5 scoring (RANK-02):** re-score prefixes k ∈ {0, 8, 16, 32, 64, 78} with `phase19_erasure.value_span_nll_mean` (:2407-2419, `ans1` frame, mean reduction), applied after `ablate_components(artifact, ordered_prefix[:k])`. Context = `[ASSISTANT_ID] + encode(ans1 preamble)` (`phase18_extraction.py:1110-1128`).
  - **No per-candidate scoring time is on record.** The Phase 18 arm records' `wall_clock_min` (246.5 / 270.1) include 864 entries × 48 draws. The closest committed rank-scoring times are `results/phase19_collateral_curve.json::wall_clock_min` 6.959 and `results/phase19_reference_set_resweep.json::runs.*.wall_clock_min` 6.155 / 6.133, but those include the 288-component ordering sweep.
  - **State "no comparator" for E5 scoring.** Do not force a 25% check against a different unit.

### E6: anchor-context generation (timing only, no published configuration; ruled D-07)

- No entry point exists. Build the anchor context exactly as `value_span_nll` does (`[ASSISTANT_ID] + list(tok.encode(_frame_preamble(forms, "ans1")))`, `phase18_extraction.py:1031-1047, 1126`) and draw with `phase14_recall.draw_all(model, tok, ids, device, forbid, index, n_samples=K-1)` (:846-898) on the k = 78 adapter: `checkpoints/phase19_m1_erased_adapter.pt` (sha-verified against the curve record) or persona_adapter + `ablate_components`.
- Record seconds, draws, generated-token counts and stop-vs-cap counts only. Comparator: none (D-07). The A2-context side comes from the E1 probe.
- Phase 39's `e6_entry_subset` consumes `results/phase36_probe_*.json` (`phase35_prereg.py:1834-1838`). Make the E6 record self-identifying (e.g. `results/phase36_probe_e6.json`) and carry the per-entry A2 unit from E1 beside it, so Phase 39 can consume one record.

### Fixed vs per-draw separation (COST-01 / D-03)

`draw_all` is sequential, and each draw builds its own generator seeded `question_seed(index)+s` (`phase14_recall.py:879-896`). Draw *s* is independent of how many follow; this "prefix stability" is asserted by `tests/test_phase18_draws.py::test_prefix_is_budget_independent` (docstring :855-863). Each draw ends in `.tolist()` (:804), which synchronises MPS, so per-draw wall-clock is attributable.

**Recommended mechanism:** wrap `phase14_recall._complete` (:793-808) at runtime with a timer. `draw_all` looks it up as a module global, and `run_erasure_arm` imports `phase14_recall as recall` lazily (:2778), so a module-attribute patch applies. No file is edited. The wrapper records `(question, s, seconds, n_generated_tokens, hit_cap)`. Then:
- `per_draw` = the distribution over 216 × K draws (D-02 "per-unit distribution within one run");
- `fixed` = run total − Σ draw seconds;
- K = 16 cost = fixed + Σ over the first 16 draws of each question. By prefix stability these ARE the draws a K = 16 run would make.

**Options for "at K = 16" (Open Question 1):**
- (A) one or two pin runs at K = 48 with per-draw timing. K = 16 is measured on the first 16 draws, and two runs give two fixed-cost samples;
- (B) a pin run at K = 48 plus a separate K = 16 process through a probe-owned K-parameterised port of the draw loop (the `phase25_run._draw_one_shape` "port, never edit" precedent, :508-583);
- (C) patch `PHASE18_ARM_RECORD_PATH` to a doctored copy with k = 16. **Do not use (C).** It doctors a published record.

**Depth-dependence warning:** the per-draw cost grows with ablation depth. A K = 48 reading took 43.38 min at k = 8, 45.34 at 16, 50.43 at 32, 56.48 at 64 and 68.58 at 78. M2 took 46.62 and the unablated replicate 45.28. `cal-erased` (187 components, 23 entries) took 10.39 min. **E1 checkpoints deeper than 78 can cost more than the probe's k = 78 reading.** Use the per-draw time of cap-length draws (`hit_cap`, where `len(gen) == RECALL_MAX_NEW_TOKENS`, :808) as the defensible high bound: a deeper adapter cannot generate more than the cap per draw.

## Historical Wall-Clock (verified this session; for the D-02 25% checks)

| Front / stage | Committed path :: key | Value | Same scope as probe? |
|---|---|---|---|
| R1b / E1 K = 48 (k = 78) | `results/phase19_arm_erased.json::config.wall_clock_min` | 68.58400233189265 min | Yes, if the probe passes `ordered_prefix[:78]` to `run_erasure_arm` (ordering excluded on both sides) |
| E1 per-prefix (K = 48) | `results/erasure_kstar_arm_k{008,016,032,064}.json::config.wall_clock_min` | 43.377 / 45.340 / 50.425 / 56.480 min | Evidence of depth-dependence; not a probe comparator |
| E1 ordering (M1 sweep, k = 78) | `results/phase19_collateral_curve.json::wall_clock_min` | 6.959 min | Prices the per-cell ordering; not in the D-03 probe |
| E1 calibration unit | `results/phase19_arm_cal-erased.json::config.wall_clock_min` / `results/phase19_calibration_curve.json::wall_clock_min` | 10.389 / 7.015 min | Prices ERASE-06 calibrations (4 = 2 orderings × 2 seeds) |
| E2 reading | `results/phase19_arm_retrain.json::config.wall_clock_min` | 46.61799373229345 min | Yes (reading only) |
| E2 unablated reference | `results/phase19_arm_replicate.json::config.wall_clock_min` | 45.27792596419652 min | Different seed stride; context only |
| E2 training | — | none in JSON (`phase19_run.py:1588` prose "~81 s"; `phase23_control_floor.json::per_seed[].training_seconds` 78.37–80.34 s) | Partial |
| E3 T = 200 train | `results/phase25_point_dp_n8_sigma0p500000.json::training.seconds` | 209.06 s | Yes |
| E3 measure (cond. c + GATE-05) | same `::measure_seconds` | 88.35 s | If run |
| E3 recall | `results/phase25_recall.json::points.dp_n8_sigma0p500000.scoring_seconds` | 1246.87 s | Yes (score_arm) |
| E3 attack draws (4 families, K = 16) | same point `::shape_timing.*.minutes` | 119.2 min total (A2 25.40) | Only if E3 scoring includes draws (Open Question 2) |
| E4 / canary scoring | `results/phase26_canary_sources.json::points.dp_n8_sigma0p500000.provenance.scoring_seconds` | 5556.24 s (σ=0: 3171.51) | Scoring only (D-02 note) |
| E5 clearance | `results/phase17_personas_report.md:723` (markdown) | 2.1 min / 24 values | Yes, configuration-wise; not a JSON field |
| E5 scoring | — | none found | No comparator |
| E6 anchor gen | — | none (unpublished, D-07) | No comparator |
| Phase 31 beside E1 | `results/phase31_probe_point.json::stages.*.seconds`, `::total_seconds` | 7422.87 s total | Recorded beside, never extrapolated |

The 25% rule needs a stated formula, e.g. `|probe − historical| / historical > 0.25`, plus which probe stage maps to which historical key. Put both in the Phase 36 prereg entry so the comparison is mechanical.

## Ledger (D-11..D-13)

**Reusable pieces:**
- `phase25_run.beat(heartbeat_path, *, point, stage, shape, draw_index)` appends exactly one JSON line `{utc, point, stage, shape, draw_index}` (`scripts/phase25_run.py:298-319`, fields :291, stages :295 `("start","train","measure","draw","score","record","commit","done")`).
- `start_heartbeat(path, state, *, seconds=None)` starts a daemon thread that beats every `phase25_watch.HEARTBEAT_SECONDS` = 60 s of wall clock (:350-368, `scripts/phase25_watch.py:56`).
- `state` is mutated in place by the driver. The `point` field can carry a run id such as `v6/<phase>/<front>/<unit>`.
- `phase25_watch.read_last_beat` (:274-318) returns only the file's LAST complete beat, tolerating a torn tail. The ledger needs a per-run variant (group by `point`, keep the first `start` and the last beat, same torn-tail rule). That is about 20 stdlib lines.

**Hours rule (D-11/D-12):**
- Run with a committed result record → hours from the record's OWN fields. Phase 31 shape: `provenance.run.started_utc`/`finished_utc` (`scripts/phase31_probe.py:540-547`). Phase 19 shape: `config.wall_clock_min`.
- Phase 36 should **publish the contract** that every v6 MPS record carries a run id plus started/finished UTC (or a seconds field) under a fixed key, so later phases conform.
- Launched run with no record → last beat utc − start utc, flagged `"sem registro de resultado"`, attributed to its front.

**Location (Claude's discretion, with hard constraints from the tests):**
- NOT under `results/phase36_*`. It would be a non-input phase-36 record (legs (a)/(c)), and it is appended over time, so not write-once (SC4).
- NOT anywhere under `results/` while untracked. `refuse_if_dirty(pathspec=("scripts","src","results"))` refuses every emit when an untracked file sits there (31-REVIEW WR-01).
- Raw 60-s beats belong in gitignored `data/`, as Phase 25/31 do. Whether a compact launch ledger (start/end lines only) is committed, and where, is Open Question 3. If it lives in gitignored `data/` only, CI cannot check "every MPS record has a ledger launch", and a lost disk loses the crashed-run hours.

**Checks the module should expose** (each a `SystemExit` with a message for Rafael's checkpoint, never `assert`):
- `require_launch(front, run_id)`: the projection check (c), `spent + Σ high(remaining fronts) ≤ 90`;
- the per-front 1.5× check (a);
- the cumulative stop-line check (b).

Every value comes from the committed budget record and the Phase 36 prereg entries, never typed.

## Unit Caps (D-09) — recommended mechanism

1. **Values:** extra keys in `results/phase36_budget.json`, e.g. `unit_caps: {E1: {checkpoints_per_cell}, E3: {recipes, max_steps}, E5: {sets, max_set_size}, E6: {entries, adapters}, E2: {seeds}, E4: {points}}`. This is allowed because `_budget_record` checks `fields <= set(record)` (`phase35_prereg.py:996-1000`). Each cap is derived from the front's hours ÷ its probed unit price, formula in the record.
2. **Owner-side call:** a torch-free `scripts/phase36_caps.py` (or inside a `phase36_budget.py`; NOT matching `*prereg.py`) exposing `check_unit_caps(front, **counts)`.
   - It reads the COMMITTED budget blob (the `phase30_points._tracked_json` idiom: `git show HEAD:<path>` equals the working file, `scripts/phase30_points.py:190-203`).
   - It re-proves the four contract fields and `total_hours == fsum`. It cannot call `phase35_prereg._budget_record`: census "private access".
   - Owners call it at module level in their fill file, beside the `fill(...)` binding. An overrun becomes a refusal at import.
3. **Binding enforcement (cannot be forgotten):** a Phase 36 test that finds the tracked owner fill files filling a capped slot (`e1_checkpoint_grid`, `e3_grid_subset`, `e5_set_sizes`, `e6_entry_subset`) through the same predicate (`owner_prereg_glob` + AST `phase35_prereg.fill("<slot>")`). It imports them and checks the bound values (`E1_CHECKPOINT_GRID["checkpoints"]`, `E3_GRID_SUBSET["cells"]`, …) against the caps.
   - It is honest-green with zero owner files today, and needs a non-vacuity leg on a planted file (like `test_slot_ordering_is_green_on_the_real_repo` / `test_slot_census_reds_on_planted_owner_files`).
   - It goes live when Phase 41/42/38/39 land, which is the intent.
4. Note that `e6_entry_subset` and `e5_set_sizes` do not read the budget at all (`phase35_prereg.py:1655-1691`). Without (2)/(3) their caps would be unchecked.

## Hours Arithmetic (rough, from committed numbers; for the planner's risk read only)

Unit prices, all from verified records above. E3 scoring is the main unknown (Open Question 2).

| Front | Units (from REQUIREMENTS/ROADMAP) | Rough hours | Basis |
|---|---|---|---|
| probes | E1 1–2 × K = 48 runs (~1.15 h each) + E2 (~0.02 h train + 0.78 h reading) + E3 (T = 200 ~3.5 min train + ~21 min recall; T = 800 ~14 min) + E5/E6 samples, each ×2 reps | ~4–6 h | 68.58, 46.62, 209 s, 1247 s |
| R1b | 1 erased reading (+ optional M1 re-sweep 7 min) | 1.15–1.3 h | 68.58, 6.96 |
| E1 | 16 cells (4 targets × 2 orderings × 2 seeds) × [ordering ~7 min + c checkpoints at K = 16 (~20–30 min each at depth ≤ 78) + ≥ 1 confirm at K = 48 (43–69 min)] + 4 calibrations (~18 min) | c = 2: ~33 h; c = 3: ~40 h; c = 5: ~55 h (more if deep prefixes) | erasure_kstar, phase19 records |
| E2 | 2 adapters × S = 5 seeds × (train ~80 s + A2 reading ~47 min at K = 48) | ~8 h (≈ 3 h if read at K = 16) | 46.62, 78–80 s |
| E3 | ~11–12 configs (4 recipes × 3 σ, v4.0 σ = 0 reused) × (train 3.5–14 min + recall ~21 min) | ~6 h; **+ ~24 h if attack draws are included** | 209 s, 1247 s, 119 min |
| E4 reserve | 3 × (T = 200 train + scoring) | ~1.2 h (recall) to ~5 h (Phase 26-style canary scoring) | 209 s, 1247 s / 5556 s |
| E5 | clearance ~5.25 s/candidate × up to 512 × 6 name/place slots (+ rejects) + cheap NLL scoring | ~4.5–6 h | 2.1 min / 24 |
| E6 | 7 adapters × (A2-context on the entry subset + anchor gen 8 slots × K) | ~1–7 h depending on subset/K | E1 per-entry unit |

**Read:** the low end is about 65 h and the high end exceeds 115 h, so the stop line will be `min(1.5Σ, 90)` = 90 h whenever Σ > 60. E1 dominates, and the D-15 cut order leaves E1 checkpoints last. **Expect Σ near or above 90.** The plan must budget a Rafael checkpoint for the cut table (D-15) and state that S ≥ 3 is enforced in the table (D-14). All rows above are [ASSUMED] arithmetic. The probes replace them.

## Common Pitfalls

### Pitfall 1: Probe added after the fill file / fill file edited after the budget
**What goes wrong:** `test_slot_ordering_is_green_on_the_real_repo` turns red permanently (legs (a)/(b)).
**Avoid:** finish every probe emit (including repetitions and any re-run) before the fill file's first commit. Treat the fill file as frozen once committed. Any correction is a continuation module, never an edit after the budget record exists.

### Pitfall 2: Touching `scripts/phase35_prereg.py` after the first probe record
**What goes wrong:** the Phase 35 ancestry guard turns red forever, and delete-and-re-add cannot launder it (`tests/test_phase29_prereg.py:69-106` takes the EARLIEST add).
**Avoid:** dated continuation only (user memory "pin corrections are dated continuations").

### Pitfall 3: Phase 36 code reaching `phase35_prereg` privates or naming it by string
**What goes wrong:** the slot census (`tests/test_phase35_prereg.py:2215-2247`) turns red.
**Avoid:** use public names only. Re-prove what you need locally, using `ENTRY_FIELDS`/`KINDS`/`FORBIDDEN_PHRASE` for the D-17 entries.

### Pitfall 4: Untracked files under `results/` from a run
**What goes wrong:** `train_arm` writes `results/<prefix>_<arm>/run.csv`. `refuse_if_dirty` then aborts every emit and restart (31-REVIEW WR-01).
**Avoid:** move the csv to `data/` in-process. Keep all sidecars and text in `data/`/`checkpoints/`.

### Pitfall 5: Reused stage sidecars
`phase25_points.train_stage` silently reuses `data/phase25_<key>_training.json` and its adapter (:365-373). A stale probe36 sidecar would make the "timed" training 0 s. Copy Phase 31's `reused` flags (`scripts/phase31_probe.py:376-380`), and refuse to price a front from a reused stage.

### Pitfall 6: Recall not scored on noised points
`measure_stage` scores recall only for controls (`scripts/phase25_points.py:570`). For the E3 T = 200 probe at σ = 0.5, call `teach_persona.score_arm` directly.

### Pitfall 7: Reading `run.csv` `wall_clock` as seconds
It is the step number (`src/personacore/training/loop.py:915`). The ledger must use the records' own seconds/UTC fields only. Add a negative test.

### Pitfall 8: Probe records carrying readings (D-01)
`run_erasure_arm` returns per-fact rows, draws and exposure. `score_arm` returns recall. `probe_guessability` returns hits. The probe record must whitelist timing/count keys only. Add a JSON-key gate test that refuses keys such as `per_fact`, `draws`, `completions`, `successes`, `rank`, `nll`, `hits`, `recall`. Prefer an AST/JSON gate to a grep (user memory "grep criteria measure prose").

### Pitfall 9: Dry-run-only tests hiding an unwired live path
Phase 25's driver shipped with its live path unwired behind 23 green dry-run tests (user memory). Two remedies:
- one CPU live-path fixture per probe driver through the REAL stages (the `tests/test_phase31_probe.py:310-389` pattern using `test_phase22_wiring._e2e_env`);
- **feed the consumer one real producer record**: build a probe record with the producer, then run the fill derivation on it via `phase35_prereg.fill(...)` in a test with `_REPO_ROOT` monkeypatched to tmp. Tests may monkeypatch it; scripts may not.

Before the LaunchAgent run, trace `main() → run()` kwargs end to end.

### Pitfall 10: `train_arm(` census and the `real` adapter path
Every literal `train_arm(` in `scripts/` or `tests/`, prose included, must be in `_TRAIN_ARM_CALL_SITES` (`tests/test_phase23_resume.py:60, 255-292`). Never pass arm `"real"`: it resolves to `checkpoints/persona_adapter.pt` (`teach_persona.py:382-386`).

### Pitfall 11: Other repo-wide censuses a new file trips (user memory, execute-phase gates)
- `inject_lora` register (ISO-06): use `phase14_recall.load_adapted_model`, never `inject_lora` directly;
- `os.replace` is only allowed in `phase25_run.py`/`phase25_record.py`: use `phase25_run.atomic_write_json`;
- `tests/test_phase21_sc5.py` counts `== 10` literals under `tests/`;
- `mitigation_gate.ratchet_k` accepts only K in (48, 24, 16, 8).

### Pitfall 12: Timing contamination
- Running `make test` (about 21–25 min, ~2870+ tests) or any MPS test during the probe run contends for the GPU. The plist must set `PERSONACORE_SWEEP_ACTIVE=1` (tests/conftest.py:45-59 skips MPS legs).
- Never run the suite while the LaunchAgent runs.
- Under launchd the driver is the PARENT and `caffeinate -dims` is its child (user memory). The Claude harness also spawns its own `caffeinate -i -t 300`. Identify the wrapper by `ppid == driver pid`.

### Pitfall 13: Provenance drift between run and emit
Copy the 31-REVIEW WR-02 fix: refuse the emit when the pinned modules differ between the run's sha and HEAD. Persist the per-session sha in sidecars and refuse a resume across commits.

### Pitfall 14: A halt that writes a phase-36 record
If `fill` raises HALT, any `results/phase36_cut_table.json` would be a non-input phase-36 record with the slot unfilled, which is leg (c) red. Put the cut table in the checkpoint message or under `.planning/phases/36-…/`.

### Pitfall 15: Basename strays
Prior phases guard tracked files that name their phase outside their prefix (`tests/test_phase23_prereg.py:555-576`, `tests/test_erasure_kstar_prereg.py:61-73`). Add the same for `phase36`/`probe36`.

### Pitfall 16: Agents and the working tree
Peer sessions edit the tree (user memory). Run `git status` before every commit and stage explicit paths. Read each artifact after the executor hands back. Do not trust reported values, since an executor once reported values before its own output existed.

## Code Examples

### The fill file shape the census and legs accept
```python
# scripts/phase36_budget_prereg.py — Source: tests/test_phase35_prereg.py:2166-2269, :2585-2589
import phase35_prereg  # plain import, no alias (census)
import phase36_budget   # Phase 36's own torch-free derivation over the committed probe records

_PROBES = phase36_budget.probe_record_paths()          # tuple of results/phase36_probe_*.json
_CHOSEN = phase36_budget.chosen(_PROBES)                # {"front_hours", "stop_line_hours", "e2_seed_count"}
V6_BUDGET_AND_STOP_LINE = phase35_prereg.fill(          # whole module-level value, exactly once
    "v6_budget_and_stop_line",
    front_hours=_CHOSEN["front_hours"],
    stop_line_hours=_CHOSEN["stop_line_hours"],
    e2_seed_count=_CHOSEN["e2_seed_count"],
    input_records=_PROBES,
    derivation={"value": _CHOSEN, "derivation": "...high bound per front (D-10)...",
                "kind": "derived", "source": " ".join(_PROBES) + " ..."},  # must name every path
)
```

### Per-draw timing without editing a pin
```python
# Source pattern: scripts/phase31_probe.py:388-402 (wrap, call, restore in finally)
import phase14_recall as recall
real = recall._complete
def _timed(model, prompt_ids, device, forbid, **kw):
    t0 = time.monotonic(); gen, stopped = real(model, prompt_ids, device, forbid, **kw)
    draws.append({"seconds": time.monotonic() - t0, "tokens": len(gen), "hit_cap": not stopped})
    return gen, stopped
recall._complete = _timed
try:
    phase19_erasure.run_erasure_arm("erased", device, components=prefix78, record_path=tmp)
finally:
    recall._complete = real
```

### Ancestry test for the Phase 36 prereg
```python
# Source: tests/test_phase35_prereg.py:433-441 + tests/test_phase29_prereg.py:69-106
from test_phase29_prereg import _assert_frozen_before, _git
def test_phase36_prereg_is_frozen_before_every_phase36_record():
    tracked = sorted(_git("ls-files", "results/phase36_*").split())
    _assert_frozen_before("scripts/phase36_prereg.py", tracked)  # honest with zero tracked
```

## State of the Art (in this repo)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Unsourced estimate ("~25–30 h", Phase 25 UAT) | Measured probes + per-stage × counts budget + 1.5× stop line | Phase 31 (v5.0) | Phase 36 extends it milestone-wide with a ledger and caps |
| Per-phase stop line | `min(1.5 × Σ, 90)` + per-front 1.5× + projection check | D-13, this phase | Needs a ledger shared by 37–43 |
| Threshold entries with proposer fields | Four-field entries, no proposer | PREREG-07 (Phase 35) | D-17 entries must use the same schema |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | E1 per-checkpoint K = 16 reading ≈ 20–30 min at depth ≤ 78, i.e. fixed cost a few minutes | Hours Arithmetic | E1 hours off by ±30%; fit/halt verdict may flip. The probe measures it |
| A2 | E1 grid of 2–5 checkpoints per cell, 16 cells, plus 1 K = 48 confirm | Hours Arithmetic | Owned by Phase 41; the cap is the lever |
| A3 | E3 "scoring" = taught/held-out recall (`score_arm`) only, no attack draws | E3, Hours | +~24 h if draws are included (Open Question 2) |
| A4 | E5 clearance unit = Phase 17 instrument at ~5.25 s/candidate; 6 name/place slots | E5, Hours | Linear error in E5 hours |
| A5 | Training time ≈ 80 s for M2/full adapter at 200 steps (only prose + phase23 control record) | E2 | Small; E2 is reading-dominated |
| A6 | Per-draw timing via a runtime wrapper of `phase14_recall._complete` is acceptable under "pins are never edited" | Fixed vs per-draw | If Rafael rules runtime patching of a pin's private as editing, use option (B), a port |

## Open Questions (RESOLVED — 36-CONTEXT Addendum: Q1 D-18, Q2 D-19 by Rafael; Q3–Q6 Claude's discretion defaults)

1. **What does "at K = 16" require: a separate K = 16 process, or K = 16 measured as the first 16 draws of a K = 48 run (prefix-stable)?**
   - Known: the pin hardcodes K from the Phase 18 record (`phase19_erasure.py:2825`), and prefix stability is test-asserted.
   - Recommendation: two pin runs at K = 48 with per-draw timing (option A ×2, ~2.3 h). This gives two fixed-cost samples and exact K = 48 twice for R1b. If Rafael wants a literal K = 16 process, use option (B), a probe-owned port. Ask before the run (D-01 spirit).
2. **What is the E3 (and E4) "scoring" unit?**
   - The v4.0 point = measure (88 s) + 4-family draws (119 min) + recall (1247 s). RECIPE-03 needs recall. E4 audit scoring resembles Phase 26 canary scoring (5556 s/point).
   - D-06 prices E4 "from the E3 probe". If E3's probe scores recall only, E4 is under-priced by about 4×. Recommendation: the T = 200 probe times recall and canary-style scoring as separate stages, and the plan states which stage prices which front.
3. **Ledger location and commitment.** Raw beats go in `data/` (pattern). Should a compact launch ledger be committed, and at which non-`results/phase3x` path? Recommendation: commit it at a path outside `results/` (e.g. alongside `artifacts/`), so CI can prove "no v6 MPS record without a launch line". Rafael to confirm.
4. **Is the fill file committed before or after Rafael's approved?** D-16 gates only the budget record. The fill file is effectively the commitment and is frozen once the budget lands. Recommendation: present the derived numbers (dry computation, uncommitted), get approved, then commit the fill file and the budget record in two consecutive commits (leg (a) needs them separate).
5. **E1 ordering cost:** price it from `phase19_collateral_curve.json` (6.96 min), or time `_selected_components` in the probe (it re-derives the published k = 78; timing-only)? Recommendation: price from the record, and say so in the derivation.
6. **E2 units:** Phase 40 may reuse existing seed-1337/2024 adapters. Price the full 2 × S retrain set; any reuse is savings, not a cut.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `.venv` Python | everything | ✓ | 3.11.15 | — |
| torch + MPS | probes | ✓ | 2.7.1, `mps.is_available()` True | — |
| Apple Silicon | probes | ✓ | Apple M3 Pro | — |
| `checkpoints/persona_adapter.pt` | E1/E5/E6 | ✓ (sha matches curve `adapter_in_sha256`) | — | — |
| `checkpoints/phase19_m1_erased_adapter.pt` | E6 (optional) | ✓ (sha matches `adapter_out_sha256`) | — | rebuild via `ablate_components` |
| `checkpoints/convbase_{best,slim}.pt` | all generation/training | ✓ | — | — |
| `data/retention_val.bin`, `data/dialog_*.bin` | `run_erasure_arm` capability, training replay | ✓ | — | none (gitignored, local only) |
| Disk | sidecars/draw caches | ✓ 473 GiB free | — | — |
| `launchctl`, `/usr/bin/caffeinate` | D-16 run mode | ✓ (used by Phase 25/26/31) | — | — |

Missing with no fallback: none.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (in `.venv`), CPU-only in CI (`.github/workflows/ci.yml` runs `pytest -q`) |
| Config file | none beyond `tests/conftest.py` (SWEEP_ACTIVE skip, fakes) |
| Quick run command | `.venv/bin/pytest -q tests/test_phase36_*.py tests/test_phase35_prereg.py` (phase35 + phase31_budget measured 107 tests in 46.5 s) |
| Full suite command | `make test` (about 21–25 min; run with `run_in_background`/nohup on a COMMITTED tree only, since 11 clean-tree probes fail on untracked files) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| COST-01 / SC4 | Phase 36 prereg precedes every `results/phase36_*` (honest-green at zero; natural RED via an earlier-added file) | unit (git) | `pytest tests/test_phase36_prereg.py -k frozen` | ❌ Wave 0 |
| COST-01 / D-17 | Every D-17 entry has exactly four fields, a known kind, no proposer; preferences labelled; P22 holds at T = 800 via `p22_onset_sigma` | unit + AST | `pytest tests/test_phase36_prereg.py` | ❌ |
| COST-01 | Each probe builder (pure) emits per-stage seconds, repetition counts, provenance, `gates_nothing`, and NO reading keys (JSON-key gate) | unit | `pytest tests/test_phase36_probe.py -k record` | ❌ |
| COST-01 | Probe isolation: prefix/arm/path guards; no collision with stray globs or `V6_RESULT_PATHS` of later phases; real-tree strays unchanged | unit | `pytest tests/test_phase36_probe.py -k isolation` | ❌ |
| COST-01 | Live path through the REAL stages on CPU fixture scale (E1 via `run_erasure_arm`, E2 train+reading, E3 train T = 200 and patched T, E5, E6) | integration (CPU) | `pytest tests/test_phase36_probe.py -k live` | ❌ |
| COST-01 | Write-once emit; dirty-tree refusal first; run-sha vs HEAD pinned-module refusal (WR-02) | unit | `pytest tests/test_phase36_probe.py -k emit` | ❌ |
| COST-01 | plist mirrors the Phase 31/26 agent; `PERSONACORE_SWEEP_ACTIVE=1`; RunAtLoad/KeepAlive false | unit | `pytest tests/test_phase36_probe.py -k plist` | ❌ |
| COST-01 | 25% comparator table: each probe stage maps to its historical key; divergence > 25% refuses budget derivation | unit | `pytest tests/test_phase36_budget.py -k divergence` | ❌ |
| COST-02 | Hours derivation: high bound per front; stop line `min(1.5Σ, 90)`; S = 5; E4 = 3 × T = 200 unit; caps derived | unit | `pytest tests/test_phase36_budget.py -k derive` | ❌ |
| COST-02 | Consumer fed a real producer record: the derived values pass `phase35_prereg.fill("v6_budget_and_stop_line", ...)` on planted probe records; the emitted budget then passes `fill("e2_S")`, `fill("e1_checkpoint_grid")` | integration | `pytest tests/test_phase36_budget.py -k consumer` | ❌ |
| COST-02 / SC3 | Σ > 90 → HALT; cut table rows in D-15 order with hours saved + question lost; S < 3 never in the table; no `results/phase36_*` written | unit | `pytest tests/test_phase36_budget.py -k halt` | ❌ |
| COST-02 | Ancestry: probes ≺ fill file ≺ budget; budget ≺ every `results/phase3[7-9]_*`/`phase4[0-3]_*` MPS record (honest branches) | unit (git) | `pytest tests/test_phase36_budget.py -k ancestry` + `tests/test_phase35_prereg.py::test_slot_ordering_is_green_on_the_real_repo` | ❌ / ✅ |
| COST-02 | Committed budget recomputes from committed probe records (Phase 31 shape) | unit | `pytest tests/test_phase36_budget.py -k recompute` | ❌ |
| D-11..D-13 | Ledger: per-run grouping, torn tail, lost run counted to last beat and flagged "sem registro de resultado", record wall-clock preferred, never `run.csv` wall_clock; projection / 1.5× / stop-line refusals | unit | `pytest tests/test_phase36_ledger.py` | ❌ |
| D-09 | Caps: `check_unit_caps` refusals; owner-fill-file scan honest-green at zero, RED on planted overrun | unit | `pytest tests/test_phase36_caps.py` | ❌ |
| PREREG-08 | Every Phase 36 rule-module function has a CPU test (`_untested_functions` pattern, `tests/test_phase35_prereg.py:2725-2839`); zero skips in the prereg test | unit + AST | `pytest tests/test_phase36_prereg.py -k cpu_test` | ❌ |
| Census | Phase 35 slot census stays green with the new files | existing | `pytest tests/test_phase35_prereg.py -k census` | ✅ |
| M3-only | The probe run itself (timings), the 25% read, Rafael's approved | manual (checkpoint) | LaunchAgent; read records | n/a |

### Sampling Rate
- **Per task commit:** the quick run command (about 1 min).
- **Per wave merge:** the full suite, uncapped in the background, on a committed tree, never during the LaunchAgent run.
- **Phase gate:** full suite green before `/gsd-verify-work`. The final run happens after the budget commit, so the real-repo legs (a)/(b)/(c) and the census are exercised live.

### Wave 0 Gaps
- [ ] `tests/test_phase36_prereg.py`: ancestry, entries, P22, zero-skips, CPU-test census
- [ ] `tests/test_phase36_probe.py`: isolation, record builders, live CPU fixtures (reuse `test_phase22_wiring._e2e_env`), emit, plist
- [ ] `tests/test_phase36_budget.py`: derive, consumer feed, halt/cut table, ancestry, recompute
- [ ] `tests/test_phase36_ledger.py` and `tests/test_phase36_caps.py`
- [ ] Register line(s) in `tests/test_phase23_resume.py::_TRAIN_ARM_CALL_SITES` if a new `train_arm(` call site is added

## Security Domain

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication / V3 Session | no | — (offline, single-user) |
| V4 Access Control | no | — |
| V5 Input Validation | yes | `_prove` refusals on every consumed record: schema, finite numbers, repo-relative paths; never `assert` |
| V6 Cryptography | yes (integrity only) | `hashlib.sha256` for adapter/record/module pins; no hand-rolled crypto |
| V7 Logging | yes | append-only heartbeat/ledger lines, torn-tail tolerant |

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Probe or budget record rewritten after the fact | Tampering | write-once emit (overwrite refusal first), HEAD-blob reads (`_tracked_json`), ancestry tests |
| Record from uncommitted or different code | Repudiation | `refuse_if_dirty`, provenance block, run-sha vs HEAD pinned-module diff (WR-02) |
| Typed numbers instead of read ones | Tampering | hours derived by script from records; budget recomputes from committed files |
| GPU contention or sleep skewing timings | DoS / integrity of measurement | LaunchAgent + `caffeinate -dims`, `PERSONACORE_SWEEP_ACTIVE=1`, no suite during the run |
| Secrets | Info disclosure | none involved; never commit tokens |

## Sources

### Primary (HIGH confidence, read this session)
- `scripts/phase35_prereg.py` :1-90, :132, :155-191, :317-350, :357-515, :682-760, :768-1188, :1211-1237, :1426-1522, :1655-1691, :1791-1923
- `tests/test_phase35_prereg.py` :1-125, :425-500, :880-1066, :1921-1992, :2115-2839; `tests/test_phase29_prereg.py` :52-117
- `scripts/phase31_probe.py` :1-160, :190-610; `scripts/phase31_budget.py` :1-130, :320-420; `tests/test_phase31_probe.py` :263-400, :927-1002; `tests/test_phase31_budget.py` :370-428
- `.planning/milestones/v5.0-phases/31-mps-cost-probes-and-budget-commitment/31-CONTEXT.md`, `31-REVIEW.md` :51-96
- `scripts/phase25_run.py` :275-470, :508-633; `scripts/phase25_watch.py` :56, :274-318; `scripts/phase25_points.py` :177-265, :350-470, :536-640
- `scripts/phase19_erasure.py` :2332-2560, :2732-2951, :3521-3715; `scripts/phase19_run.py` :1584-1670; `scripts/erasure_kstar_run.py` :1-60, :109-139
- `scripts/phase14_recall.py` :793-898, :143-152; `scripts/phase18_extraction.py` :93-98, :981-1128, :1159; `scripts/teach_persona.py` :357-393, :1587-1599, :1672-1712, :2007, :2466
- `scripts/phase17_persona_gate.py` :1-60, :204-260; `scripts/phase14_factset_gate.py` :111; `src/personacore/training/loop.py` :62, :915
- `tests/test_phase23_resume.py` :60-140, :250-292; `tests/test_phase27_relearn.py` :809-823; `tests/test_phase23_prereg.py` :555-576; `tests/test_erasure_kstar_prereg.py` :55-90; `tests/conftest.py`; `artifacts/com.personacore.phase31.probe.plist`
- Records (values printed this session): `results/phase19_arm_{erased,retrain,replicate,cal-erased}.json`, `results/erasure_kstar_arm_k0{08,16,32,64}.json`, `results/phase19_collateral_curve.json`, `results/phase19_calibration_curve.json`, `results/phase19_reference_set_resweep.json`, `results/phase25_point_dp_n8_*.json`, `results/phase25_recall.json`, `results/phase26_canary_sources.json`, `results/phase17_*.json`, `results/phase17_personas_report.md:723`, `results/phase18_arm_adapter-{on,off}.json`, `results/phase23_control_floor.json`, `results/phase31_{probe_point,probe_relearn,budget}.json`
- Live checks: `phase35_prereg.p22_onset_sigma(200|800)`, `seed_list()`, `a2_corpus_entries()` = 216, `e1_targets()`, adapter sha256s vs the curve record

### Secondary
- User auto-memory notes (execute-phase gates, dry-run tests, caffeinate wrapper, pin corrections, misnamed artifacts), used as pitfalls and cross-checked against code where cited

### Tertiary
- None. No web sources were needed: this phase is entirely in-repo.

## Metadata

**Confidence breakdown:**
- Contract / ordering / census: HIGH. Read and quoted with line numbers; planted green/red sequences exist in the test file.
- Entry points and comparators: HIGH. Each function was read and each JSON value printed.
- Hours arithmetic: MEDIUM-LOW. Unit prices are committed, but E1/E3 unit definitions belong to Phases 41/42.
- Ledger/caps mechanism: MEDIUM. A design recommendation inside Claude's discretion; location needs Rafael (Open Question 3).

**Research date:** 2026-10-02
**Valid until:** the first `results/phase36_probe_*.json` commit (after that, Phase 35's prereg is frozen and the legs bind live). Otherwise 30 days.
