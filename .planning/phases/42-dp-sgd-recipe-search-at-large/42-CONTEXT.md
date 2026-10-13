# Phase 42: DP-SGD Recipe Search at Large ε - Context

**Gathered:** 2026-10-13
**Status:** Ready for planning

<domain>
## Phase Boundary

E3 runs a pre-registered grid of 4 DP-SGD recipes × σ ∈ {0, 0.5, 1} at n = 8 and the one-taught-fact
unit, seed 1337. It answers RECIPE-03's question: does any recipe keep recall where the guarantee is
vacuous? Every ε is published with `selection_accounted = false`, beside the basic composition over
the whole grid, and null answers carry the same weight.

The phase only FILLS the two Phase-42-owned slots that Phase 35 already wrote into
`scripts/phase35_prereg.py`: `e3_grid_subset` (rule `_rule_e3_grid_subset`, L1426-1522) and
`e3_recall_threshold` (rule `_rule_e3_recall_threshold`, L1525-1590). The rules, `p22_onset_sigma`
(L1028-1056), `_v4_control` (L800-841), `F_Y`, `REFUSED`, `CURVE_TOTAL`, `SELECTION_ACCOUNTED` and
`DELTA` are already locked there and are not re-decided here. No `scripts/phase42_*`,
`results/phase42_*` or `tests/test_phase42_*` exists yet.

**Requirements:** RECIPE-01, RECIPE-02, RECIPE-03, RECIPE-04.
</domain>

<decisions>
## Implementation Decisions

### The grid (RECIPE-01, RECIPE-04)
- **D-01: Batch fixed at 8 (q = 1); the 4 recipes vary only lr × T.** The accountant is frozen at
  q = 1 (Phase 21 D-07/D-23; `src/personacore/privacy/accountant.py:850`, where a penalty "out of
  caution" is still a wrong published number). The v4.0 point published `accounting.q = 1.0` and
  `composed_lot_sizes [8]`. Batch < 8 with a subsampled accountant is deferred (outside v6.0).
- **D-02: A 2×2 factorial: lr ∈ {3e-4, 1e-3} × T ∈ {200, 800}, batch 8.** The v4.0 corner
  (lr 3e-4, T = 200, batch 8) is one of the 4. That stays inside `unit_caps.E3` = {recipes 4,
  sigmas 3, max_steps 800, max_batch 8} (`results/phase36_budget.json`).
- **D-03: The v4.0 σ = 0 control is reused by SHA-256, and the whole grid runs at seed 1337.**
  - The control record is `results/phase25_point_dp_n8_sigma0p000000.json`, sha256
    `0c23f6c11bb25aa53a4b01548c923668119d005bae5e0aa8d6e4e9f6bdcc76ed`, byte-identical to tag `v5.0`.
  - Its counts: taught 790/1008, held-out 346/648; train_config seed 1337.
  - It is verified through `phase35_prereg._v4_control`. Only the record is reused, not the adapter.
- **D-04: Declared limit — one seed for the whole grid.** Phase 40 measured variation between
  seeds, so no E3 result is claimed for any other seed.
- **D-05: Warmup at 10% of T (20 at T = 200, 80 at T = 800), with cosine decay over the whole T.**
  This is the v4.0 shape (warmup 20 / T 200; `src/personacore/training/schedule.py`).
  - The prereg declares that `WARMUP_STEPS = 20` (`scripts/teach_persona.py:1600`) is the v4.0 value.
  - E3 passes a T-derived warmup to the run and does NOT change that constant.
- **D-06: DP clip C = 1.3254119157791138 fixed on every noised point.**
  - This is the v4.0 CLIP_NORM: the no-interpolation median rule over the `dp_n64` per-record norms
    in `results/phase25_clip_calibration.json`, measured in a probe with non-binding clip.
  - Declared limit: C was calibrated at dp_n64, σ = 0, lr 3e-4, T = 200. At lr = 1e-3 or T = 800 the
    norm distribution may differ.
  - Each point publishes `clip_bind_count` as a descriptive reading, with no verdict.
- **D-07: The 3 new σ = 0 controls follow the v4.0 control exactly.**
  - They use `clip_norm` = 1e6 (non-binding), `grad_clip` 1.0 and the same train_config. Only lr,
    T and the T-derived warmup change.
  - Declared limit: the gap between a control and its noised points mixes the per-record clip and
    the noise. E3 does not separate the two, as v4.0 did not.
- **D-08: P22 / RECIPE-04.** The grid uses T = 800 ≠ 200, so the prereg assertion runs
  `p22_onset_sigma` for every T used and must pass before any training.
  - Measured onsets: T = 200 → 0.0789, T = 800 → 0.1578.
  - Both noised σ (0.5, 1) clear them; the check still runs and is recorded.
- **D-09: No fifth recipe. The recipes cap stays at 4.**
  - The high-bound cost from the Phase 36 unit prices: 0.4118 h per run at T = 200, 0.5519 h at
    T = 800. The 11 runs (5 at T = 200, 6 at T = 800; the v4.0 control is reused) total 5.37 h
    against the E3 line of 6.62 h.
  - The 1.25 h of slack stays as margin for the real run. The E3 probe diverged 1.4% at T = 200 and
    6.4% from linear at T = 800 (`results/phase36_probe_e3.json`).

### Shared noise across the grid (declared, measured 2026-10-13)
- **D-10: The σ points of one recipe are NOT independent replicates, and no reading treats them as
  such.** Rafael asked for this to be checked in the code. Here is what the code does.
  - The DP noise generator is a dedicated `torch.Generator`, seeded ONCE from the run seed
    (`src/personacore/privacy/dpsgd.py:311-314`; `scripts/teach_persona.py:1937-1944` passes
    `seed=seed`).
  - Every step draws `torch.normal(mean=0, std=σ·C, generator=self._g)` with no σ branch, so the
    call sequence is identical at every σ (`dpsgd.py:486-500`).
  - Measured on CPU (GPT(ModelConfig()) + LoRA, seed 1337, 72 tensors, 331,776 elements): the
    σ = 1 noise is exactly 2× the σ = 0.5 noise at steps 1-3 (`torch.equal`), and successive steps
    differ.
  - The noise does not depend on lr or the parameters. So the sharing goes further:
    - same-σ points of the two lr recipes at the same T draw identical noise;
    - the first 200 steps of a T = 800 point draw the same noise as the T = 200 point at the same σ.
  - Not measured: the same identity on the MPS generator. The research or rehearsal checks it.

### The answer (RECIPE-02, RECIPE-03)
- **D-11: "Vacuous" is by construction, with no new cut line.**
  - The source is the biased-coin bound already on record in `.planning/research/V6-PREREG-09.md:53`:
    under ε-DP no guesser beats probability e^ε/(e^ε+1).
  - The smallest ε in the grid is 159.44 (σ = 1, T = 200), where that bound is 1.0 in float64.
  - The grid's ε at δ = 1e-5: T = 200 → 519.70 (σ 0.5) / 159.44 (σ 1); T = 800 → 1840.30 / 519.70.
    σ = 0.5 at T = 200 and σ = 1 at T = 800 share μ = √T/σ = 28.28, so there are 3 distinct ε values.
  - The TPR ≤ e^ε·FPR + δ form enters the text only if research finds and verifies a source for it.
    Without a verified source it stays out.
- **D-12: Unit of the answer — per noised point, on both legs.**
  - A point passes iff taught recall ≥ F_Y × the SAME recipe's control taught recall AND held-out
    recall ≥ F_Y × its held-out recall, with F_Y = 0.7 (`scripts/mitigation_gate.py:203`).
  - A recipe whose control is unlearnable (`phase29_prereg.control_is_unlearnable`) has its points
    REFUSED.
  - The published table is 4 × 2 (recipe × σ), each cell labelled passa / não passa / REFUSED.
- **D-13: Readings that never enter the "yes".** Retention and the dialogue gap are published per
  point as descriptive readings only.
  - RECIPE-03 asks only about recall.
  - The v4.0 retention cap 3.9085 fails intact adapters (Phase 41 D-14: Phase 40's intact adapters
    read 4.156-4.332 against it).
- **D-14: The summary line is the whole count, never a bare "sim/não".**
  - It reads "k de 8 pontos passam; m REFUSED", because a yes in 1 of 8 is a selection inside the
    grid and `selection_accounted` stays false.
  - Composition is basic only (PREREG-09 §3(b), locked in `phase35_prereg` ENTRIES `e3_composition`
    and `e3_selection_accounted`). It sums only the noised points; the σ = 0 controls carry no ε.
- **D-15: The null case, worded.** If no point passes, the report's FIRST line is, literally:
  "nenhuma receita manteve o recall onde a garantia é vazia (0 de 8 pontos)".
  - It is followed by every point's raw recall on both legs and its ε.
  - No "ainda", no "possivelmente com outra receita", and no extrapolation beyond the 4 recipes and
    seed 1337.

### Predictions (recorded before the run; descriptive; a disagreement is a finding, not a failure)
- **D-16:** The σ = 0.5 and σ = 1 points of the v4.0 recipe repeat the v4.0 recall: 0/1008 taught,
  0/648 held-out.
  - Source: `results/phase25_recall.json`, points `dp_n8_sigma0p500000` and `dp_n8_sigma1p000000`.
    The point records themselves carry no recall fields.
  - The report puts the two readings side by side.
- **D-17:** None of the 4 recipes passes the threshold at σ = 0.5 or σ = 1. If one does, it is
  expected at T = 800, not at lr = 1e-3.
  - The rationale is an argument, not a project measurement. Under AdamW (the DP optimizer,
    `dpsgd.py:32`) lr scales signal and noise together, and only T accumulates signal faster than
    noise.
- **D-18: Declared possible outcome.** A σ = 0 control at lr = 1e-3 may fail to learn or degrade
  retention. Its recipe's points are then REFUSED, as in v4.0, and that is reported with the same
  weight.

### Order, rehearsal and approvals
- **D-19: Two stages.**
  - **Stage 1:** the 3 new σ = 0 controls, plus the SHA-256 check of the reused v4.0 control.
    Then the stage-1 records are committed, and `e3_recall_threshold` is filled and committed.
  - **Stage 2:** the 8 noised points. The P22 check (D-08) runs and passes before any training.
  - The ancestry test proves that the filled threshold precedes the first noised-point record.
- **D-20: REFUSED points still run.** A recipe whose control is unlearnable still runs its noised
  points, as v4.0 did for n64 (`results/phase25_point_dp_n64_sigma*` exist).
  - Those points publish ε and raw recall on both legs, labelled REFUSED.
  - Their cost is already inside the 5.37 h (all 8 noised points are priced).
- **D-21: Before any MPS run, a code review of the prereg and the driver, then a short CPU
  rehearsal (as in Phase 41, where rehearsal 41-11 found a real defect, fixed in 075f5ea).** The
  rehearsal must exercise:
  - the reuse of the v4.0 control through its SHA-256 check;
  - the T-derived warmup (20 at T = 200, 80 at T = 800);
  - the P22 check for T = 800;
  - the REFUSED path of a control that does not learn.
- **D-22: Approvals follow the Phase 41 pattern.** All commits are write-once, each alone, by
  explicit path.
  - One approved per launch (stage 1, stage 2).
  - The stage-1 records and the filled threshold go under one approved.
  - The stage-2 records go under three: the ledger and the point records, the E3 record, the report.
  - Launch goes through `phase36_ledger.require_launch("E3")` (E3 is in `V6_MPS_FRONTS`; MPS fp32).

### Claude's Discretion
- Module and record file names (`scripts/phase42_prereg.py` / driver), within the Phase 35 globs
  `results/phase42_control_*.json` and `results/phase42_*` (`phase35_prereg.py:328-329`) and the
  control-record contract in its module docstring (L70-72).
- How the fill and ancestry tests mirror `scripts/phase40_prereg.py` / `scripts/phase41_prereg.py`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and requirements
- `.planning/ROADMAP.md` — "### Phase 42: DP-SGD Recipe Search at Large ε" (success criteria 1-5)
- `.planning/REQUIREMENTS.md` L753-756 — RECIPE-01..04 (verbatim, reworded 2026-10-01); L711 PREREG-09

### Locked rules (Phase 35) and research
- `scripts/phase35_prereg.py` — `_rule_e3_grid_subset` (L1426-1522), `_rule_e3_recall_threshold` (L1525-1590), `p22_onset_sigma` (L1028-1056), `_v4_control` (L800-841), `E3_N`/`E3_UNIT` (L781-786), slot registry (L1818-1845), result globs (L328-329), control-record contract (docstring L70-72), ENTRIES `e3_composition` (L536) / `e3_selection_accounted` (L549) / `F_Y`
- `.planning/research/V6-PREREG-09.md` §3(b) (verdict L214: no finer accountant; basic composition) and L53 (biased-coin bound, D-11)
- `.planning/phases/35-*/35-CONTEXT.md` D-02, D-12, D-15, D-17 — the E3 slot, composition, threshold and grid decisions

### Budget and ledger (Phase 36)
- `results/phase36_budget.json` — `front_hours.E3` 6.6225 h, `unit_caps.E3`, `unit_prices.e3_*`, approved text "4 receitas; lote 8"
- `results/phase36_probe_e3.json` — E3 probe (σ 0.5, seed 1337, T 200/800, batch 8, lr 3e-4)
- `scripts/phase36_ledger.py` — `require_launch` (L400), stops a/b/c; `scripts/phase36_caps.py` `check_unit_caps` (L165)
- `.planning/phases/36-*/36-CONTEXT.md` D-05 (T ≤ 800; p22 onset at 800 is 0.1578)

### v4.0 records reused or cited
- `results/phase25_point_dp_n8_sigma0p000000.json` — the reused σ = 0 control (sha256 0c23f6c1…)
- `results/phase25_point_dp_n8_sigma0p500000.json`, `…sigma1p000000.json` — ε 519.698 / 159.441, `selection_accounted: False`
- `results/phase25_recall.json` — recall of every v4.0 point (D-16 source)
- `results/phase25_clip_calibration.json` — C = 1.3254 median rule (D-06)

### Mechanism and gate code
- `src/personacore/privacy/accountant.py` — `epsilon_for` (L819), q = 1 frozen (L850)
- `src/personacore/privacy/dpsgd.py` — generator seeding (L311-314), noise draw (L486-500) (D-10)
- `scripts/teach_persona.py` — `LR` (L1587), `WARMUP_STEPS` (L1600), DPSGD construction (L1937-1944)
- `scripts/mitigation_gate.py:203` — `F_Y = 0.7`; `scripts/phase29_prereg.py:190-200` — `control_is_unlearnable`
- `scripts/phase40_prereg.py`, `scripts/phase41_prereg.py`, `scripts/phase41_erasure.py` — the prereg/fill/ancestry/driver/approval conventions to mirror
- `.planning/phases/41-erasure-across-facts-orderings-and-seeds/41-CONTEXT.md` D-14 (the retention cap fails intact adapters; cited by D-13)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `phase35_prereg.fill('e3_grid_subset', …)` / `fill('e3_recall_threshold', …)`: the two fills this phase makes. The grid fill enforces exactly 4 recipes, one seed, P22 and the optional v4.0 control input. The threshold fill reads `results/phase42_control_*.json` plus the v4.0 control and returns per-recipe thresholds or REFUSED.
- `phase35_prereg._v4_control`: the SHA-256 against `git show v5.0:<path>`, plus the sigma/n_facts/seed checks.
- `accountant.epsilon_for(sigma, steps, delta)`: the exact composed Gaussian at q = 1. `phase25_epsilon.curve_total`: basic composition.
- `teach_persona` DP training path (`is_dp`, `dp_sigma`, `dp_clip_norm`) and the Phase 25 point-record scorer (taught/held-out recall, refusal, retention, `clip_bind_count`).

### Established Patterns
- Prereg ENTRIES are `{value, derivation, kind, source}`, with no proposer fields.
- An ancestry test proves the prereg and its fills precede every record.
- Write-once records; corrections are dated continuations via `scripts/_addendum.py`.
- `require_launch(front)` and its ledger lines; MPS fp32; one approved per launch, records committed only after Rafael's approved.

### Integration Points
- New `scripts/phase42_*` (prereg + driver) and `tests/test_phase42_*`.
- Records under `results/phase42_control_*.json` and `results/phase42_*`.
- Ledger lines in `ledger/v6_mps_ledger.jsonl` under front E3.

</code_context>

<specifics>
## Specific Ideas

- The null-case first line, literally: "nenhuma receita manteve o recall onde a garantia é vazia (0 de 8 pontos)" (D-15).
- The summary is always "k de 8 pontos passam; m REFUSED" (D-14).
- The v4.0 recipe's noised points are shown side by side with the v4.0 readings (D-16).

</specifics>

<deferred>
## Deferred Ideas

- Batch < 8 with a subsampled (q < 1) accountant: a new capability, outside v6.0 (D-01).

</deferred>

---

*Phase: 42-dp-sgd-recipe-search-at-large*
*Context gathered: 2026-10-13*
