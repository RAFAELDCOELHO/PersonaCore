# Phase 36: MPS Cost Probes and Budget Commitment - Context

**Gathered:** 2026-10-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Every v6.0 MPS front is priced by a timing probe on the M3. From those probe records, Phase 36
fills the Phase 35 slot `v6_budget_and_stop_line` (owner 36) and publishes
`results/phase36_budget.json`, inside Rafael's 90 h MPS ceiling for the whole milestone,
probes included. If the fronts do not fit, the work halts and a cut table goes to Rafael; no
front is cut unilaterally (COST-01, COST-02).

Phase 36 also builds the milestone-wide MPS ledger that every later MPS phase (37-43) checks
before it launches.

Out of scope: any scientific reading. Probes measure time, never results. Designing the fronts
themselves (E1 checkpoint grid, E3 recipes, E5 sets, E6 entries, R1b tolerance) belongs to their
owning phases. Phase 36 only sets the hours and the unit caps those designs must fit.

</domain>

<decisions>
## Implementation Decisions

All decisions below were decided by Rafael in discuss-phase 36 (2026-10-02).

### Carried forward (already locked, not re-asked)
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

### Principle for every probe
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

### Probe set
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

### Probe → hours
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

### Stop line and ledger
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

### S, the cut table and run mode
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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements and roadmap
- `.planning/REQUIREMENTS.md` (v6.0 block) — COST-01, COST-02; also NOISE-01 (S), RECIPE-01/04
  (E3 grid, P22), AUDIT-01/02 (E4 conditional), RANK-01, CTX-01, ERASE-07, REPRO-03
- `.planning/ROADMAP.md` §"Phase 36" and the v6.0 header (ordering constraint, approvals rule)

### The contract Phase 36 fills
- `scripts/phase35_prereg.py` — module docstring "THE BUDGET-RECORD CONTRACT" (:61-65);
  `V6_MPS_FRONTS` (:768); `_prove_budget` (:955); `_budget_record` (:991);
  `_rule_v6_budget_and_stop_line` (:1145); `_rule_e2_S`; `p22_onset_sigma` (:1028); `_SLOTS` (:1791);
  `ENTRIES["mps_ceiling_hours"]`, `ENTRIES["e2_min_seeds"]`
- `tests/test_phase35_prereg.py` — slot census and per-fill-file ordering legs (a)/(b)/(c) that a
  Phase 36 fill file must satisfy
- `.planning/phases/35-v6-0-pre-registration-and-the-research-it-rests-on/35-CONTEXT.md` — D-02,
  D-06 (S STOP), D-14 (four-field entries), D-17, Addendum to D-15 (S chosen in Phase 36)

### The ARCAL precedent
- `.planning/milestones/v5.0-phases/31-mps-cost-probes-and-budget-commitment/31-CONTEXT.md` —
  D-01..D-12 (isolated probe, per-stage × counts formula, measured spread, 1.5× stop line, LaunchAgent)
- `scripts/phase31_probe.py`, `scripts/phase31_budget.py` — probe driver and budget builder patterns
- `results/phase31_budget.json`, `results/phase31_probe_point.json`, `results/phase31_probe_relearn.json`
  — the Phase 31 probe kept beside the E1 probe for comparison (never extrapolated from)
- `artifacts/com.personacore.phase31.probe.plist` — LaunchAgent pattern

### Historical wall-clock for the 25% comparisons
- `results/phase19_arm_erased.json` (`config.wall_clock_min` 68.584; R1b and E1 K = 48)
- `results/phase19_arm_retrain.json` (46.618; E2 measurement), `results/phase19_arm_replicate.json` (45.278)
- `results/phase25_point_dp_n8_*.json` (v4.0 DP training/scoring seconds; E3 T = 200)
- `results/phase17_*.json`, `results/phase18_*.json` (`wall_clock_min`; E5)
- `results/phase26_canary_sources.json` (`scoring_seconds` only)

### Pinned constants (import, never retype)
- `scripts/mitigation_budget.py` — `CURVE_K` = 16, `FULL_FIDELITY_K` = 48, `STEP_BUDGET` = 200, `SIGMA_LADDER`
- `scripts/phase19_erasure.py` — Phase 19 erasure configuration (k = 78 prefix, `TARGET_RANKING`)
- `scripts/phase25_run.py` — `start_heartbeat` / `beat` (ledger heartbeats, D-12)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `phase31_probe.run_point_probe` and `phase25_run.start_heartbeat`/`beat`: probe driver plus
  heartbeat, the base for the D-12 ledger.
- `phase31_budget.py`: a per-stage × counts budget with spread and a 1.5× stop line, recomputable
  from committed files.
- `phase35_prereg.fill("v6_budget_and_stop_line", ...)`: the only legal way to produce the budget
  values; it re-applies `_prove_budget`.
- `phase19_erasure` (wrapped, never edited) for the k = 78 / K = 48 configuration;
  `teach_persona.score_arm` for A2 readings.

### Established Patterns
- Probe isolation (Phase 31 D-02): own prefix, own sidecars and adapters; a guard proves no later
  driver can pick them up.
- Closed pins are imported, never copied or edited; a closed pre-registration is corrected only by
  a dated continuation (an addendum plus a tripwire), never by editing it.
- Provenance block on every record (git_sha, head_at_write, module_sha256, run started/finished UTC).

### Integration Points
- `scripts/phase36_*prereg.py`: the owner-36 fill file(s), with the D-17 entries committed before
  the first probe record and the budget fill after the probes.
- `results/phase36_budget.json`: consumed by `e2_S` (40), `e1_checkpoint_grid` (41),
  `e3_grid_subset` (42) and the D-09 cap checks.
- The ledger script: called by every MPS phase 37-43 before launch (D-11, D-13c).

</code_context>

<specifics>
## Specific Ideas

- R1b's scope: D-04 prices R1b as one erased-arm reading (k = 78, K = 48). Whether Phase 37's
  replica also needs other Phase 19 arms (retrain 46.6 min, replicate 45.3 min) is Phase 37's
  discuss. If it does, the extra hours need Rafael's approved under D-06's "nothing reallocated"
  rule. Surface this in the plan.
- E2 prices both retrains NOISE-01 needs (the full taught adapter and M2 without `pet_name`) from
  the M2 probe. The planner states how the full adapter's cost is derived (more facts than M2).

</specifics>

<deferred>
## Deferred Ideas

- Auditing a recipe other than v4.0's in E4: another front, needs Rafael's approved (D-06).

</deferred>

---

*Phase: 36-mps-cost-probes-and-budget-commitment*
*Context gathered: 2026-10-02*

## Addendum — plan-phase decisions (2026-10-02)

Rafael ruled the first two open questions from 36-RESEARCH.md during `/gsd-plan-phase 36`, in his own
words (Portuguese, translated faithfully here). The remaining four are Claude's discretion,
defaulted to the research recommendation, and are surfaced in the plan for his review.

- **D-18 (E1 at K = 16 and K = 48; research Open Question 1), Rafael:** two pin runs at K = 48
  through `phase19_erasure.run_erasure_arm("erased", ..., components=ordered_prefix[:78])`, with a
  runtime per-draw timer (no file edited). K = 16 cost = fixed cost + the first 16 draws of each
  question (prefix stability, `tests/test_phase18_draws.py:118`).
  - Both runs record ONLY times and counts (per draw, per question, fixed cost) in the probe record.
  - The draws and any hit/success count are discarded. They go into NO record and NOT into the log.
    No `results/phase19_*` or `results/phase37_*` file is written.
  - "R1b reading" here means only the wall-clock compared with the 68.584 min of
    `results/phase19_arm_erased.json::config.wall_clock_min`.
  - The two fixed-cost samples are recorded SEPARATELY (not averaged), so Rafael can see whether the
    first one includes warm-up.
- **D-19 (E3 / E4 scoring; research Open Question 2), Rafael:** the E3 probe at T = 200 times
  training plus taught recall (`teach_persona.score_arm`) only. E4's canary-scoring stage is priced
  from `results/phase26_canary_sources.json` (5556.24 s per point, used as the high bound), and the
  derivation states that it was NOT re-measured. E4 per point = T = 200 training (from the E3 probe)
  + 5556.24 s canary scoring, × 3 points (D-06).
  - Obligation carried to Phase 43, pre-registered in Phase 36 as a four-field entry: if E4 runs, its
    first point is timed and compared with the reserve's per-point price before the rest launch; a
    divergence above 25% pauses and goes back to Rafael.

### Claude's Discretion (defaulted at plan time; Rafael may overrule at the budget checkpoint)
- **Q3 ledger location:** raw 60-s beats in gitignored `data/`; a compact, append-only,
  script-written launch ledger (start/end lines per run) is COMMITTED at a path outside `results/`,
  chosen so it trips neither `refuse_if_dirty` nor any clean-tree probe.
- **Q4 fill timing:** the fill file (`V6_BUDGET_AND_STOP_LINE = phase35_prereg.fill(...)`) and
  `results/phase36_budget.json` are both committed only after Rafael writes approved, in two
  consecutive commits (leg (a) requires them separate). Before approval, the numbers are shown from
  a dry computation that writes nothing under `results/phase36_*`.
- **Q5 E1 ordering:** each cell's ordering cost is priced from
  `results/phase19_collateral_curve.json::wall_clock_min` (6.959 min); the derivation says it was
  not re-measured (the same pattern Rafael chose for E4 in D-19).
- **Q6 E2 units:** price the full 2 adapters × S retrain set; any reuse of existing seed adapters by
  Phase 40 is savings, not a cut.
