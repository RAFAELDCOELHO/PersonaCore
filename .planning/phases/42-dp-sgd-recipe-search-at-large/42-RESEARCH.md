# Phase 42: DP-SGD Recipe Search at Large ε - Research

**Researched:** 2026-10-13
**Domain:** pre-registered DP-SGD grid on the existing PersonaCore stack (Phase 35 slot fills, Phase 25 training/scoring seams, Phase 36 ledger), MPS fp32
**Confidence:** HIGH. Every load-bearing claim below was read in the repo or measured in this session. The exceptions are flagged `[ASSUMED]` or LOW.

## Summary

Phase 42 adds no library and needs no new mechanism. Everything it needs is already in the tree:

- the two Phase-35 slot rules (`_rule_e3_grid_subset`, `_rule_e3_recall_threshold`);
- the v4.0 training seam `phase25_points.train_stage`, which captures the DP seam, `clip_bind_count`, the live mechanism and `train_config`, and resumes;
- the v4.0 recall instrument `teach_persona.score_arm`;
- the dialogue gap, returned free by the training call;
- retention, through the registered `phase25_condition_c.measure_condition_c`;
- the accountant (`epsilon_for`), basic composition (`phase35_prereg.CURVE_TOTAL`) and the ledger (`phase36_ledger.require_launch/append`).

The phase's real work is wiring these with the Phase 41 discipline: two fill files, ancestry, rehearsal and approvals. It must also route around about ten repo-wide censuses that a new driver trips.

Four findings change the plan.

1. **The D-05 seam is module-global rebinding, not an argument.** `train_arm` has no lr/T/warmup parameter. It reads the module globals `LR`, `WARMUP_STEPS` and `MAX_STEPS` at call time (`scripts/teach_persona.py:2005-2007`). The one precedent is `phase36_probe.stage_e3`, which rebinds `tp.MAX_STEPS` in a `try/finally` around `phase25_points.train_stage` (`scripts/phase36_probe.py:903-909`). E3 must rebind all three and restore them, then prove the take from the sidecar's `train_config`. The constant's source is never edited. Editing `teach_persona.py` is also forbidden in practice, because committed records sha-pin it.
2. **The threshold fill must live in a second fill file**, committed after the 3 control records and before any noised record. This is forced by the Phase 35 ordering legs (a)/(b)/(c). The planted green case `g42` already encodes exactly this layout (`tests/test_phase35_prereg.py:2597-2602`). It also needs the grid object by identity (`_is_filled`), so it imports `phase42_prereg.E3_GRID_SUBSET`.
3. **The E3 unit price covers train + `score_arm` only.** It does not cover the v4.0 extraction-draw leg (refusal) or retention. The v4.0 σ = 1 point scored in 1456.7 s, above `e3_score_high` = 1270.6 s. The realistic ceiling is about 5.58 h, or about 6.23 h with retention measured, still under the 6.62 h E3 line.
4. **D-10's noise identity holds on MPS, measured this session**: σ = 1 noise is exactly 2× σ = 0.5 noise at steps 1-3, `torch.equal` on all 72 tensors / 331,776 elements, and successive steps differ.

**Primary recommendation:** mirror Phase 41's file layout:

- `scripts/phase42_prereg.py` (grid fill + every rule and record path), committed before any `results/phase42_*`;
- `scripts/phase42_threshold_prereg.py` (threshold fill only), committed after the 3 controls;
- one driver `scripts/phase42_recipes.py` that calls `phase25_points.train_stage` under a `try/finally` rebinding of `tp.LR/WARMUP_STEPS/MAX_STEPS`, then `tp.score_arm` and `measure_condition_c`, under `require_launch("E3")` and the ledger.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

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

### Deferred Ideas (OUT OF SCOPE)
- Batch < 8 with a subsampled (q < 1) accountant: a new capability, outside v6.0 (D-01).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RECIPE-01 | 4 recipes × σ ∈ {0, 0.5, 1}, n = 8, one-taught-fact unit, committed before any configuration runs; v4.0 σ = 0 control reused by SHA-256; 5th recipe only if budget fits | `fill("e3_grid_subset", …)` verified to succeed today with the D-02 grid (12 cells, reuse on the v4.0 cell, caps {4, 800, 8} + sigmas 3 pass): §"Item 4", Code Example 1. The grid fill file precedes every `results/phase42_*` by leg (a). |
| RECIPE-02 | ε at δ = 1e-5 per configuration, `selection_accounted = false`, basic composition beside it | `phase25_epsilon.point_epsilon_for_sigma(σ, steps=T, delta=DELTA)` per point; `phase35_prereg.CURVE_TOTAL(eps8, delta=DELTA)` = (6078.265039595788, 8e-05) measured; `phase35_prereg.SELECTION_ACCOUNTED` is False. |
| RECIPE-03 | Answer vs F_Y × the SAME recipe's control on both legs; unlearnable control → REFUSED; null with equal weight | `fill("e3_recall_threshold", …)` returns per-recipe `{control, taught, heldout}` or `"REFUSED"`; recall from `tp.score_arm`; comparison `k/n >= threshold` using the fill's float (§Pitfall 6). |
| RECIPE-04 | P22 check for every T used, failing before training | Inside `_rule_e3_grid_subset` (`phase35_prereg.py:1491-1499`): onsets measured 0.07890181429684162 (T=200), 0.15780356992036104 (T=800). It runs at import of the grid fill file. The driver re-asserts before stage 2. |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Python 3.11 venv at `.venv` only. Never the system 3.14. Verified: `.venv/bin/python --version` → 3.11.15; torch 2.7.1; MPS available.
- PyTorch only, from scratch. No HF/peft. Primary training is MPS fp32: no AMP, no GradScaler, no `torch.compile`.
- Tests are CPU-only and GPU-free. MPS-only tests are skipped in CI with an attributed count (PREREG-08; the ubuntu skip pin in `tests/test_phase25_venue.py`).
- Offline CSV logging only. No wandb.
- GSD workflow: edits go through GSD commands. Commits are write-once, each alone, by explicit path. Result records are committed only after Rafael writes "approved".
- Prereg entries are exactly `{value, derivation, kind, source}`. No proposer / adopted_by. Never "selected by THE USER, verbatim".
- Corrections to a closed prereg are dated continuations (`scripts/_addendum.py`), never edits.
- Obsidian vault logging is the orchestrator's job, not the researcher's.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Grid, P22 check, caps, record paths, verdict/label/summary rules | CPU prereg module (`scripts/phase42_prereg.py`) | Phase 35 rule `_rule_e3_grid_subset` | Must be frozen before any `results/phase42_*` (leg a). Torch is loaded at import only via `seed_list()` / `teach_persona`. |
| Recall threshold | CPU fill file 2 (`scripts/phase42_threshold_prereg.py`) | `_rule_e3_recall_threshold` | Consumes in-phase control records, so it sits between stage 1 and stage 2. |
| Training a cell | MPS driver → `phase25_points.train_stage` → teach_persona's trainer | `DPSGD` seam | The only DP training path, already registered in the trainer-call census. |
| Recall scoring | MPS driver → `teach_persona.score_arm` | `phase14_recall.load_adapted_model` | The v4.0 instrument, so v4.0 readings are comparable (D-16). |
| Retention / dialogue gap (descriptive) | `phase25_condition_c.measure_condition_c`; train blob `ppl_adapter_on/off` | — | Registered `retention_perplexity` caller. The dialogue pair comes free from training. |
| ε / composition | `phase25_epsilon` + `accountant` (CPU) | — | Pure functions. |
| Launch gating, spent hours | `phase36_ledger` (append-only `ledger/v6_mps_ledger.jsonl`) | `phase36_caps` | D-13 stops. Every MPS record is named by an end line. |
| Aggregate E3 record + report | CPU emit in driver | prereg pure functions | Emitted from committed records only. |

## Standard Stack

### Core (all in-repo; nothing to install)
| Module | Role in Phase 42 | Evidence |
|--------|-----------------|----------|
| `scripts/phase35_prereg.py` | `fill`, `E3_SIGMAS`, `E3_N`, `E3_UNIT`, `F_Y`, `DELTA`, `CURVE_TOTAL`, `SELECTION_ACCOUNTED`, `p22_onset_sigma`, `seed_list`, `V6_RESULT_PATHS`, `SLOTS` | L317-333, L1028-1057, L1426-1590, L1818-1845, L1882-1888 |
| `scripts/phase25_points.py` | `point_plan`, `train_stage` (seam capture, resume, sidecar, mechanism pin, control clip check) | L234-263, L350-529 |
| `scripts/teach_persona.py` | `score_arm`, `arm_outputs`, `LR`/`WARMUP_STEPS`/`MAX_STEPS`/`BATCH_SIZE` | L357-392, L1587-1600, L2466-2521 |
| `scripts/phase25_condition_c.py` | `measure_condition_c` (dialogue pair + retention, one model) | L176-236 |
| `scripts/phase25_epsilon.py` | `point_epsilon_for_sigma`, `curve_total`, `SELECTION_ACCOUNTED` | L68, L226-235, L271-294 |
| `scripts/phase29_prereg.py` | `control_is_unlearnable`, `REFUSED` (= `'REFUSED'`) | L190-200, L333 |
| `scripts/phase36_ledger.py` | `require_launch`, `append`, `run_id`, `reconcile` | L76-78, L194-235, L400-423 |
| `scripts/phase36_caps.py` | `check_unit_caps`, `counts_for("e3_grid_subset", …)` | L165-180, L183-200 |
| `scripts/phase25_run.py` | `atomic_write_json`, `beat`/`start_heartbeat`, `device`, `head_sha` | the only sanctioned `os.replace` writer |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `phase25_points.train_stage` | A new direct call to teach_persona's trainer | Needs a new register entry, a count bump in `tests/test_phase23_resume.py:60,192,348`, and re-implementing the seam capture. Rejected. |
| Rebinding `tp.LR/WARMUP_STEPS/MAX_STEPS` | Wrapping `tp.TrainConfig` before `train_stage` | `train_stage` reads `tp.MAX_STEPS` for its composed-step proof (`phase25_points.py:447`), so MAX_STEPS must be rebound anyway. One mechanism is simpler. |
| `score_arm` | The full Phase 25 point record (extraction draws + refusal) | About 80 min/point of attack draws (v4.0 `shape_timing` sums ~79.5 min). Unpriced in E3; not asked by RECIPE-01..04 or D-13. |

**Installation:** none. `pip install -e ".[cpu,dev,demo]"` is already the venv.

## Package Legitimacy Audit

No external package is installed by this phase, so the audit is empty. slopcheck was not run (nothing to check).

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| (none) | — | — | — | — | — | — |

**Packages removed:** none. **Packages flagged:** none.

## Answers to the eight open items

### Item 1 — D-10 on MPS: MEASURED, identity holds
- **Probe:** `<scratchpad>/p42_mps_noise_probe.py`. It wrote nothing in the repo; `git status` showed only the pre-existing `.claude/scheduled_tasks.lock`. It builds `GPT(ModelConfig())` + `inject_lora(LoRAConfig())` + `mark_only_lora_trainable`, moved to the device, then two `DPSGD(model, sigma=0.5 | 1.0, clip_norm=1.3254119157791138, device=…, seed=1337)`, and calls `_draw_noise()` three times on each.
- **Output, MPS** (`generator device mps:0 state bytes 44`):
  ```
  step 1: equal(2*n_0.5, n_1)=True max|diff|=0.0 differs_from_prev=None
  step 2: equal(2*n_0.5, n_1)=True max|diff|=0.0 differs_from_prev=True
  step 3: equal(2*n_0.5, n_1)=True max|diff|=0.0 differs_from_prev=True
  tensors 72 elements 331776 seconds 0.8
  ```
- **CPU:** the same output, reproducing the CONTEXT measurement (state 5056 bytes, 0.5 s).
- **What follows for D-10:** the "Not measured" bullet can become "measured on MPS 2026-10-13". The rehearsal does not need to re-check it.
  - Lr-independence follows from the code: `_draw_noise` reads only `sigma`, `C`, `buf.shape` and `self._g` (`dpsgd.py:486-500`).
  - T-independence also follows from the code: the draws per step are fixed by the 72 buffers.
  - Not measured: identical data order across lr. It is plausible because `seed_everything(seed)` precedes the GPT build (`teach_persona.py:1882`) `[ASSUMED]`.

### Item 2 — D-11 source for TPR ≤ e^ε·FPR + δ: VERIFIED (as a one-line rearrangement)
- **Source, fetched and read:** Kairouz, Oh, Viswanath, "The Composition Theorem for Differential Privacy", arXiv:1311.0776v4 (6 Dec 2015; ICML 2015), §2 "Differential Privacy as Hypothesis Testing", p. 3, **Theorem 2.1**: "For any ε≥0 and δ∈[0,1], a database mechanism M is (ε,δ)-differentially private if and only if … for all pairs of neighboring databases D0 and D1, and all rejection region S ⊆ X: P_FA + e^ε·P_MD ≥ 1−δ, and e^ε·P_FA + P_MD ≥ 1−δ."
  - Definitions, same page: P_FA = P(M(D0) ∈ S) (type I), P_MD = P(M(D1) ∈ S̄) (type II).
  - The paper credits the δ = 0 case to "[WZ10, Theorem 2.4]" (Wasserman and Zhou 2010; KOV spells it "Zhu"). The proof for general δ is in its §9.2.
- **The TPR form:** with FPR = P_FA and TPR = 1 − P_MD, the second inequality gives **TPR ≤ e^ε·FPR + δ** directly. The text must present it as "a rearrangement of KOV Theorem 2.1", not as a quotation. KOV never writes "TPR".
- **Caveat the text must carry.** This form is vacuous only for FPR ≥ (1−δ)e^{−ε}. At the smallest grid ε (159.44) that threshold is 5.69e-70, computed this session. At FPR = 0 it still says TPR ≤ δ. So "vacuous for every test" is false for this form.
  - The biased-coin bound e^ε/(e^ε+1) (V6-PREREG-09.md:53) is the cleaner "vacuous by construction" statement and stays primary.
  - Recommend: cite KOV Thm 2.1 beside it, with the caveat, or keep it out. Rafael's call; flagged in Open Questions.
- **Not verified:** Wasserman–Zhou 2010 itself (not fetched).

### Item 3 — D-05 seam: rebind three module globals around `train_stage`
- **No argument exists.** `train_arm` builds `TrainConfig(lr=LR, warmup_steps=WARMUP_STEPS, max_steps=MAX_STEPS, …)` from module globals at call time (`scripts/teach_persona.py:2003-2012`; the signature L1672-1685 has no lr/T/warmup).
- **Precedent for rebinding:** `scripts/phase36_probe.py:902-909` sets `real_steps = tp.MAX_STEPS; tp.MAX_STEPS = steps; try: … phase25_points.train_stage(plan) … finally: tp.MAX_STEPS = real_steps`.
  - It is the ONLY rebinding of a teach_persona constant in `scripts/` or `tests/` (grep: `tp.MAX_STEPS = ` → phase36_probe.py:904/909 only; no `tp.LR =` / `tp.WARMUP_STEPS =` anywhere).
  - That probe kept warmup 20 at T = 800. E3 differs: it sets 80.
- **`train_stage` itself already swaps `tp.DPSGD` and `tp.TrainConfig` for factories** (`phase25_points.py:390-420`). It reads `tp.MAX_STEPS` for its composed-step proof (`timed = tp.MAX_STEPS - resumed_from_step`, L447-451). So rebinding `tp.MAX_STEPS` is mandatory for T = 800; otherwise the proof refuses.
- **Proof of take:** the returned sidecar blob carries `train_config = tp.asdict(cfg)` (`phase25_points.py:514`). The driver must assert `blob["train_config"]["lr"] == recipe lr`, `["warmup_steps"] == T // 10`, `["max_steps"] == T`, and `blob["live_mechanism"]["composed_steps"] == T`. These are the record's evidence that the constant was untouched and the run used the recipe.
- **Plan dict:** start from `phase25_points.point_plan(phase25_record.point_key("dp_n8", σ))`. Then override `point_key`, `prefix` and `pinned_mechanism=dict(..., composed_steps=T)`, exactly as `phase36_probe.e3_plan` does (`phase36_probe.py:858-873`).
  - `point_plan` already gives `dp_clip_norm` = `CONTROL_CLIP_NORM` (1e6) at σ = 0 and `CLIP_NORM` (1.3254119157791138) otherwise (`mitigation_budget.py:930,988`). D-06/D-07 therefore hold by construction.
  - `point_plan`'s `point_epsilon`/`accounting` are computed at STEP_BUDGET = 200. **Ignore them for T = 800** and compute ε with `point_epsilon_for_sigma(σ, steps=T, delta=DELTA)`.
- **How phases 40/41 called the trainer:** each added its own direct call, registered in `tests/test_phase23_resume.py:120-129` (phase40_noise.train_adapter, phase41_erasure.train_calibration_adapter, non-DP, no resume). Phase 36's E3 probe went through `phase25_points.train_stage`. That is the DP precedent E3 should follow.
- **D-05 wording for the prereg:** "E3 passes the T-derived warmup by rebinding teach_persona's module globals LR / WARMUP_STEPS / MAX_STEPS for the duration of one `train_stage` call (restored in `finally`, the phase36_probe precedent). The source constants (`WARMUP_STEPS = 20`, `LR = 3e-4`, `MAX_STEPS = 200`) are the v4.0 values and are not edited." `[ASSUMED]` that Rafael reads runtime rebinding as "does not change the constant"; worth one line in the review checkpoint.

### Item 4 — the two fills: exact inputs, checks and record contract
**`phase35_prereg.fill("e3_grid_subset", *, recipes, seed, input_records, derivation, fifth_recipe_derivation=None)`** (`phase35_prereg.py:1426-1522`):
- `recipes`: a non-empty **tuple** of mappings with exactly the keys `{lr, steps, batch}`. lr is finite > 0. steps and batch are ints ≥ 1, not bools. No duplicates.
- `seed ∈ seed_list()`. This imports phase23_run, so torch loads at import.
- `input_records` must include `results/phase36_budget.json`. It must include `results/phase25_point_dp_n8_sigma0p000000.json` iff the v4.0 recipe `{lr: tp.LR, steps: STEP_BUDGET, batch: tp.BATCH_SIZE}` is in the grid AND `seed == v4 record seed` (1337). `_v4_control()` then checks the sha against `git show v5.0:<path>` in the real repo.
- `derivation`: a four-field entry whose `value == recipes` and whose `source` names every input path (`_consume_inputs`, L910-952).
- Budget: E3 hours > 0. P22: every noised σ > `p22_onset_sigma(T)` for every T in the recipes ∪ {200}.
- Returns a `_filled` MappingProxy `{cells (12), p22_onset_sigma, n, unit}`.
- **Measured today in a scratch process, read-only:** with recipes = (`tp.LR`, 1e-3) × (`STEP_BUDGET`, `phase36_prereg.ENTRIES["e3_max_steps"]["value"]` = 800) × `tp.BATCH_SIZE`, seed `seed_list()[0]` and inputs (budget, v4 control) → `cells 12`, `reuse ['results/phase25_point_dp_n8_sigma0p000000.json']` on the v4.0 σ = 0 cell only, onsets `{200: 0.07890181429684162, 800: 0.15780356992036104}`, n 8, unit "one taught fact". `check_unit_caps("E3", **counts_for(...))` → `{'recipes': 4, 'max_steps': 800, 'max_batch': 8}`; `check_unit_caps("E3", sigmas=3)` passes. Runtime 1.0 s.

**`phase35_prereg.fill("e3_recall_threshold", *, grid, input_records, derivation)`** (`phase35_prereg.py:1525-1587`):
- `grid` must BE the object returned by the grid fill (identity via `_FILLED_GRIDS`, L862-872). So fill file 2 does `import phase42_prereg` and passes `phase42_prereg.E3_GRID_SUBSET`.
- `input_records`: the v4.0 control (it is reused) plus one `results/phase42_control_*.json` per new recipe (3). Each must be repo-relative, exist, be listed once and be named in `derivation["source"]`.
- `derivation["value"]`: the tuple of the 4 grid keys `(lr, steps, batch, seed)`, in any order (`_prove_keys_value`). Never the paths.
- Each new control record is keyed by the recipe READ from the record, never by position. The key set must equal the grid's.
- Returns `{key: {"control": path, "taught": F_Y*tk/tn, "heldout": F_Y*hk/hn}}`, or `"REFUSED"` where `control_is_unlearnable(tk, tn, hk, hn)`.
- v4.0 key `(0.0003, 200, 8, 1337)` → taught 0.5486111111111112, held-out 0.3737654320987654 (learnable: `control_is_unlearnable(790,1008,346,648)` → False).

**Control-record contract** (docstring L70-72; read checks L1559-1565): each `results/phase42_control_*.json` carries:
- `recipe` = {lr, steps, batch};
- `seed`;
- `sigma` = 0.0;
- `taught_recall` / `heldout_recall`, each with at least `numerator` and `denominator` (v4.0 shape: plus `rate`, `questions`, `draws_per_question`, `per_family`; `phase25_recall._tier`, L100-111, builds exactly this from `score_arm`'s blocks).

The ledger additionally requires `provenance.run.{started_utc, finished_utc, device}` on every MPS record (`phase36_ledger.py:62-63, 279-311`).

**Path constants** (resolve, never type): `next(p for p in phase35_prereg.V6_RESULT_PATHS if p == "results/phase42_control_*.json")` and `== "results/phase42_*"` (phase41_prereg.py:128-139 pattern). The budget path is `phase35_prereg.SLOTS["e3_grid_subset"]["input_records"][0]`, and the v4 control is `[...][1]`.

### Item 5 — what yields a full point; the driver assembles it
There is **no single call**. The driver assembles each point from three calls:
1. **`phase25_points.train_stage(plan)`** gives (sidecar blob):
   - `adapter`/`adapter_sha256`, `checkpoint_step`, `csv`/`csv_sha256`, `stats`, `final_train_loss`;
   - the dialogue pair `ppl_adapter_on`/`ppl_adapter_off` (+ `ppl_scored_targets`; v4.0's `condition_c.point_dialogue_ppl_on` equals `training.ppl_adapter_on` bit-for-bit on the control record);
   - `seconds`, `resumed_from_step`, `live_mechanism` (composed_steps, lot sizes, q, clip_norm), `pinned_mechanism`;
   - **`clip_bind_count`** (run-lifetime; the control is proved 0 before scoring, L457-464; v4.0 noised points read 1600 = 200 × 8, i.e. C bound on every record);
   - `train_config`, `git_sha`.
2. **`teach_persona.score_arm("dp_n8", phase14_factset.LOCKED_FACTS, adapter, device)`** gives `on_taught`/`on_heldout`/`off_taught`/`off_heldout` (k, n, rate, per_family, questions) + `per_family_gain`. Use the `phase25_recall._tier` shape for the record's `taught_recall`/`heldout_recall`(+`_off`). Denominators: 1008 taught / 648 held-out.
3. **Retention (D-13, descriptive):** `phase14_recall.load_adapted_model(device, adapter)` then `phase25_condition_c.measure_condition_c(model, tok, device, forbid=forbid)` → `retention_ppl`, `retention_total_tokens` (+ a second dialogue pair). Measured cost 87-213 s, **not in the E3 unit price**.

**Refusal** in v4.0 records comes from the extraction attack-draw leg (`phase25_points._refusal`, L675-683, over `blob["shapes"]` A1-A3 draws). It is about 80 min/point, unpriced, and asked by no RECIPE requirement nor D-13. **Recommend: not produced**, stated in the prereg as a declared omission. Rafael confirms in the review.

**D-16 numbers re-read:** `results/phase25_recall.json` `points.dp_n8_sigma0p500000` and `…1p000000` → taught 0/1008, held-out 0/648, scoring 1246.9 s and 1456.7 s on MPS. The point records carry no recall fields; their key sets lack `taught_recall`, `heldout_recall`, `scoring_seconds`, etc.

### Item 6 — ancestry, approvals, ledger
- **Phase 35 legs, automatic on the real repo** (`tests/test_phase35_prereg.py:2475-2536`, green test L2557). Once the phase42 fill files are tracked they enforce:
  - **(a)** `phase42_prereg.py` (grid; no in-phase input) — every commit touching it strictly precedes the first add of every `results/phase42_*`.
  - **(a)** `phase42_threshold_prereg.py` (in-phase input) — every commit precedes every `results/phase42_*` except `results/phase42_control_*.json` (and the v4 control).
  - **(b)** every tracked declared input (3 controls; v4 control; budget) is first-added strictly before the threshold file's first commit.
  - **(c)** once any non-input phase-42 record is tracked, both slots are filled.
  - The planted green case `g42` (L2597-2602) is exactly: grid file → control → threshold file → point.
  - Census rules (L2166-2269): `E3_GRID_SUBSET = phase35_prereg.fill("e3_grid_subset", …)` as the whole module-level binding, `import phase35_prereg` plainly, no private `phase35_prereg._*` access, no alias, each slot filled once, and only in `scripts/phase42_*prereg.py`.
- **Phase-local ancestry tests** (mirror `tests/test_phase41_prereg.py:465-500`, `tests/test_phase41_floors_prereg.py:251-277`):
  - `test_phase42_prereg_is_frozen_before_every_phase42_record`;
  - `test_this_test_file_is_first_added_before_every_phase42_record` (first add only);
  - `test_records_at_commit_is_true_at_the_first_commit`;
  - for the threshold file: `test_every_declared_input_precedes_the_threshold_file`, `test_threshold_file_is_frozen_before_every_noised_record`;
  - each with a natural-RED non-vacuity leg, e.g. the threshold file was committed AFTER the first control record (as 41's floors test does against its first calibration). The `_assert_frozen_before` helper is the Phase-18 mould (`tests/test_phase27_prereg.py:74-…`). It refuses shallow clones.
- **Edit window:** every commit of `phase42_prereg.py` must precede the first control record, so all pure functions (labels, summary line, D-15 sentence, report readings, predictions, rehearsal/launch rules) must land there BEFORE stage 1. After that it is closed (Phase 41 lesson, 41-05).
- **Ledger** (`scripts/phase36_ledger.py`):
  - `require_launch("E3")` before each launch. It writes nothing.
  - `append("start", run_id=run_id(42, "E3", unit), phase=42, front="E3")` before each run.
  - `append("end", …, record="results/phase42_….json")` after. The record must match `V6_RESULT_PATHS` (L208-213).
  - Line shape: sort_keys JSON with exactly `utc, event, run_id, phase, front, record, seconds, flag, stop, ruling` (L47-58). Sample: `{"event": "end", "flag": null, "front": "E1", "phase": 41, "record": "results/phase41_cell_…json", "ruling": null, "run_id": "v6/41/E1/…", "seconds": null, "stop": null, "utc": "…"}`.
  - Dead runs: `reconcile` → `lost` line.
  - **Measured now:** `require_launch("E3")` passes (no stop tripped). Spent 49.134 h of the 90 h line; E3 0.0 h.
  - Stop (a) for E3 fires above 1.5 × 6.6225 = 9.93 h. Stop (c) projection is sum(max(front_hours, spent)) ≈ 81.5 h < 90.
- **Approvals (D-22):** stage-1 launch approved → stage-1 records (3 controls; ledger) + threshold fill file + its test under ONE approved, each commit alone by explicit path. Stage-2 launch approved → then three approveds: (ledger + 8 point records), the E3 aggregate record, the report. Mirror 41-12..41-16's checkpoint tasks (`checkpoint:human-verify`, `gate="blocking"`).

### Item 7 — frozen tests on the real tree that new phase42 files trip
| # | Test (file:line) | What it does | How to route around |
|---|-------------------|--------------|---------------------|
| 1 | `tests/test_phase23_resume.py:270` (`test_resume_from_none_is_inert`; register L60, count L348, resume passers L192) | `grep -rn "train_arm("` over scripts/ and tests/ must equal the register, per file, prose included | Never write the literal `train_arm(` (code, docstring or comment) in any phase42 file. Reach the trainer only through `phase25_points.train_stage`. A direct call needs a register line + count bump + reason. |
| 2 | `tests/test_phase25_driver.py:341` | `os.replace` only in `phase25_run.py`/`phase25_record.py` (scripts/*.py + src) | Write records with `phase25_run.atomic_write_json` (or a write-once helper calling it). |
| 3 | `tests/test_lora_inject.py:450` (registers L261-…) | Every `inject_lora` call is in a closed consumer/producer register (ISO-06) | Never call `inject_lora` in the driver. Use `phase14_recall.load_adapted_model` / `score_arm`. |
| 4 | `tests/test_phase19_erasure.py:1371` (scan L1386) | `retention_perplexity` call sites are fixed to the pin + 3 successors | Get retention through `phase25_condition_c.measure_condition_c`, never a direct call. |
| 5 | `tests/test_phase20_correction.py:1377` | `mitigation_point_verdict` has no caller outside its sanctioned module | Do not call it. The E3 rule is the F_Y comparison on the fill's thresholds. |
| 6 | `tests/test_phase21_sc5.py:280` (patterns L190-197) | Counts `== 10` / `!= 10` literals in tests/**, comments included | No `== 10` / `!= 10` in new tests (e.g. never assert a count of 10). |
| 7 | `tests/test_phase35_prereg.py:2313` (census) and `:2557` (ordering legs on real repo) | Slot census + legs (a)/(b)/(c) | Fill-file layout above; commit order grid → controls → threshold → points; never edit fill files after their window. |
| 8 | `tests/test_phase36_caps.py:286` (loader L272-281) | Exec's every tracked owner fill file holding a SLOT_COUNTS slot (only `e3_grid_subset` here) in a FRESH module and checks caps | `phase42_prereg.py` must be import-idempotent with no file writes at import. It re-runs the grid fill + git show v5.0 + p22 (≈1 s). |
| 9 | `tests/test_phase36_ledger.py:722` | Every tracked `results/phase4[0-3]_*` with `provenance.run.device == "mps"` is named by an end line | Per-run records (controls, points) get end lines. The aggregate E3 record and the report carry emit provenance only (`phase41_erasure.json` has `provenance` = {emitted_utc, git_sha, module_sha256}). |
| 10 | `tests/test_phase32_frontier.py:638` (pathspec L654) | `git diff v4.0 HEAD -- results` with `:(exclude)results/phase4[0-9]_*` | Keep every phase42 record under `results/phase42_*`. Any other new path under results/ trips it. |
| 11 | 11 clean-tree probes (memory note; e.g. `tests/test_phase25_frontier.py:123` `git status --porcelain results/` == "") | Red while anything is untracked under results/, tests/, scripts/ | Run the suite only on a committed tree. The cell csv lands in `results/<prefix>_dp_n8/run.csv` DURING training (`teach_persona.arm_outputs`, L389). |
| 12 | `results/*.json` module sha pins + `tests/test_phase27_relearn.py:1190` `_SUPERSEDED_PINS` | Committed records pin `teach_persona.py` (and phase30_points) bytes | Do not edit `teach_persona.py`, `phase25_points.py` or `phase35_prereg.py`. |
| 13 | `tests/test_phase41_floors_prereg.py:349` | Uses `scripts/phase42_floors_prereg.py` as a NON-VACUITY "misplaced" fill site | Do not name a phase42 file `phase42_floors_prereg.py` (the census test still passes, but avoid confusion). |

**Prefix choice:** `arm_outputs(arm, prefix)` writes `checkpoints/{prefix}_dp_n8_adapter.pt`, `checkpoints/{prefix}_dp_n8_latest.pt` and `results/{prefix}_dp_n8/run.csv` (`teach_persona.py:383-392`).
- The prefix must be per cell (`train_stage` assumes it).
- It must NOT start with `phase25_` (that would collide with v4.0 adapters) or `phase42_` (the csv would match the `results/phase42_*` record glob while the run lives or after a crash).
- Recommend `phase42e3_<cell>` for real runs and `phase42rh_<cell>` for the rehearsal. Neither matches `results/phase42_*`, the `phase41rh` precedent (`phase41_erasure.py:85-86`).
- Add `results/phase42e3_*/` and `results/phase42rh_*/` to `.gitignore` with a test (precedent: `.gitignore:18-20` + `tests/test_phase41_prereg.py:2326`).
- `train_stage` moves the csv to `data/phase25_runs/<point_key>/run.csv` after a successful run (L478-488).

### Item 8 — wall-clock: 5.37 h confirmed; the real ceiling is higher
Recomputed from `results/phase36_budget.json` `unit_prices` (`e3_overhead_high` 43.818 s, `e3_per_step_high` 0.84045 s, `e3_score_high` 1270.563 s):
- per run 0.41180 h (T = 200) / 0.55187 h (T = 800);
- 5 × 0.41180 + 6 × 0.55187 = **5.370215732835186 h**;
- E3 line = 12 × 0.55187 = 6.622459432036141 h (the formula prices every cell at max_steps).

Two items the price does not cover, both read from committed records:
- **σ = 1 scoring is slower than the high bound.** v4.0 `dp_n8_sigma1p000000` scored in 1456.74 s against `e3_score_high` 1270.56 s (+186 s). With the 4 σ = 1 points: +0.207 h → ≈ 5.58 h.
- **Retention (if measured, D-13):** 11 × 87.4-213.4 s → +0.27-0.65 h → ≈ 5.84-6.23 h.

Both stay under 6.62 h, and far under stop (a) at 9.93 h. The prereg should state these as the expected ceiling, not 5.37 h.

## Architecture Patterns

### System Architecture Diagram

```
                      (CPU, before any record)
 phase36_budget.json ─┐
 v4.0 control record ─┼─► scripts/phase42_prereg.py ──► fill("e3_grid_subset") ──► E3_GRID_SUBSET (12 cells)
 (sha == v5.0 tag)   ─┘        │  P22 onsets @T=200,800 assert; check_unit_caps("E3")
                               │  rules: labels, summary, D-15 line, predictions D-16/D-17, paths
                               ▼
 ── STAGE 1 (MPS; require_launch("E3"); approved #1) ───────────────────────────────────────────
  for each NEW σ=0 recipe (3):  ledger start ─► rebind tp.LR/WARMUP/MAX_STEPS ─► phase25_points.train_stage
        ─► assert train_config + clip_bind_count == 0 ─► score_arm ─► measure_condition_c
        ─► results/phase42_control_<cell>.json (write-once, provenance.run) ─► ledger end
  v4.0 control: _v4_control() sha check (no training)
                               ▼  commit ledger + 3 controls  (approved)
 scripts/phase42_threshold_prereg.py ─► fill("e3_recall_threshold", grid=phase42_prereg.E3_GRID_SUBSET)
        ─► per recipe {taught, heldout} or "REFUSED"          (commit, same approved)
                               ▼
 ── STAGE 2 (MPS; require_launch("E3"); approved #2) ───────────────────────────────────────────
  P22 re-assert ─► for each noised cell (8, REFUSED recipes included): same chain as stage 1
        ─► ε = point_epsilon_for_sigma(σ, steps=T, delta=DELTA) ─► results/phase42_point_<cell>.json
                               ▼  approved #3: ledger + 8 points
 CPU emit ─► results/phase42_recipes.json (4×2 table, labels, k de 8 / m REFUSED, CURVE_TOTAL, D-16 side by side)
                               ▼  approved #4
 report ─► results/phase42_recipes_report.md (D-15 first line if 0 pass)   approved #5
```

### Recommended file layout
```
scripts/phase42_prereg.py            # fill 1 (grid) + every rule, path, label, prediction; frozen before stage 1
scripts/phase42_threshold_prereg.py  # fill 2 (threshold) only; ~30 lines like phase41_floors_prereg.py
scripts/phase42_recipes.py           # driver: preflight, run(stage), emit, report; NOT *prereg.py
tests/test_phase42_prereg.py         # added in the SAME commit as phase42_prereg.py
tests/test_phase42_threshold_prereg.py
tests/test_phase42_recipes.py
results/phase42_control_<cell>.json  # 3
results/phase42_point_<cell>.json    # 8
results/phase42_recipes.json, results/phase42_recipes_report.md
```

### Pattern 1: Fill file 2 (mirror `scripts/phase41_floors_prereg.py`)
Put the kwargs builder in `phase42_prereg` (`threshold_fill_inputs()`, returning a fresh dict each call, as `floors_fill_inputs` does at `phase41_prereg.py:1266-1288`). The fill file then types nothing and the rehearsal passes identical arguments.

### Pattern 2: Rehearsal (mirror 41-11)
- A scratch script outside `scripts/`, with device hiding asserting `RuntimeConfig().device == "cpu"`, and the `phase42rh_` prefix.
- Copy `results/phase36_budget.json` and the v4.0 control byte-identical under the scratch root T.
- Set `phase35_prereg._REPO_ROOT = T` only around the threshold fill. `_v4_control` still runs `git show` in the real repo via `-C _SCRIPTS`.
- Use its own ledger and heartbeat paths.
- Afterwards move (never delete) the `phase42rh_*` artifacts out of the real `checkpoints/` and `data/`.

**REFUSED leg:** to exercise it without training 3 full controls on CPU, feed the threshold rule one planted unlearnable control (e.g. 0/1008), labelled a rehearsal stand-in. `_rule_e3_recall_threshold` needs all 4 keys, so the other two new controls can also be planted. Then show the noised point labelled REFUSED in emit.

**T-derived warmup leg:** run at least one real `train_stage` per T on CPU with the rebinding, and assert `train_config.warmup_steps` is 20 / 80. CPU DP per-step cost is not on record (`[ASSUMED]` 1-4 s/step from the non-DP 41-11 reading of ~180 s / 200 steps). Measure it first with a bounded run.

### Anti-Patterns to Avoid
- **Editing `WARMUP_STEPS`/`LR`/`MAX_STEPS` or adding a parameter to teach_persona.** It breaks sha pins and D-05.
- **Reusing `point_plan`'s `point_epsilon`/`accounting`.** They are computed at T = 200 and checked against `EPSILON_LADDER`.
- **Recomputing the threshold** (`F_Y * (tk/tn)`) instead of reading the fill's value (Pitfall 6).
- **Writing the aggregate record with `provenance.run.device = "mps"`** (census #9).
- **A rehearsal file under `results/phase42_*`**, or a prefix starting `phase42_`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| DP training + seam capture + resume | A new training call | `phase25_points.train_stage` | Already proves σ/C, composed steps, control non-binding, mechanism pin, and resumes from `latest.pt`. |
| ε / composition | Own RDP/GDP code | `phase25_epsilon.point_epsilon_for_sigma`, `phase35_prereg.CURVE_TOTAL` | Locked by `e3_composition` (identity-bound). |
| Recall | A new scorer | `teach_persona.score_arm` | The v4.0 control's instrument (D-16 comparability). |
| Retention | Direct `retention_perplexity` | `phase25_condition_c.measure_condition_c` | Census #4. |
| Atomic writes | tmp + `os.replace` | `phase25_run.atomic_write_json` | Census #2. |
| Launch gating / spent hours | Own timers | `phase36_ledger.require_launch/append/reconcile` | D-13 stops, append-only proof. |
| Unlearnable test | `F_Y * rate > 0` inline | `phase29_prereg.control_is_unlearnable` | Already inside the threshold rule. |

## Runtime State Inventory

Not a rename or migration phase, so this section is omitted. The new runtime state it creates:
- ledger lines in `ledger/v6_mps_ledger.jsonl`;
- gitignored sidecars `data/phase25_<point_key>_training.json` and `data/phase25_runs/<point_key>/run.csv`;
- adapters and checkpoints under `checkpoints/phase42e3_*`;
- the heartbeat `data/v6_mps_heartbeat.jsonl`.

## Common Pitfalls

### Pitfall 1: resume under a different schedule
`train()` rebuilds the scheduler from the PASSED `train_config` on resume and never compares it to the checkpoint's embedded config (`src/personacore/training/loop.py:575-577,728-…`). A relaunch without the same rebinding resumes T = 800 under warmup 20 / max 200, silently.
**Avoid:** before `train_stage`, if `latest.pt` exists, assert its `train_config` lr/warmup_steps/max_steps equal the cell's. After it, assert the sidecar's `train_config`.

### Pitfall 2: the T = 800 composed-step proof
If `tp.MAX_STEPS` is not rebound, `train_stage` refuses: "seam composed 800 step(s) but this leg covers 200" (`phase25_points.py:447-451`). If it is rebound but not restored (an exception path), every later call in the process trains the wrong T. Use `try/finally`.

### Pitfall 3: the threshold file's edit window and the grid file's window
Leg (a) is about EVERY commit touching the file. One fix to `phase42_prereg.py` after the first control record is tracked reddens the guard forever; delete + re-add cannot launder it (memory: pin corrections are dated continuations). Finish all pure functions (including emit/report rules) before stage 1.

### Pitfall 4: ε on glibc at a new (σ, T)
`EPSILON_LADDER` rungs σ = 8 and 50 differ by 4 ULP between macOS libm and glibc (`phase25_epsilon.py:138-151`). T = 200, σ ∈ {0.5, 1} agree bit-for-bit (the ladder test is green on CI). T = 800, σ = 0.5 (1840.2946450499012) has **never been computed on glibc**.
**Avoid:** CI tests comparing ε must recompute live and compare against the record's value with `math.isclose(rel_tol=1e-12)`, or a named twin once measured. Never `==` against a typed literal.

### Pitfall 5: σ = 1 scoring exceeds the unit price
1456.7 s vs 1270.6 s (Item 8). Not a stop, but the prereg's expected-hours line should say ≈ 5.58 h (≈ 6.23 h with retention), or a reader will think the run overran.

### Pitfall 6: float association in the threshold
- The fill computes `F_Y * tk / tn` (`phase35_prereg.py:1585`).
- `mitigation_gate` computes `F_Y * control_taught_recall` with the rate pre-divided (`mitigation_gate.py:765-768`).
- Measured: 0.5486111111111112 vs 0.548611111111111 (1 ULP apart) for 790/1008.
- The tie point 553/1008 = 0.5486111111111112 passes both, and passes exactly in rationals with F_Y = 7/10.
- **Avoid:** the verdict compares `k / n >= threshold[key]["taught"]` using the FILL's value, never recomputed. Add a CPU test enumerating, per committed control, every k in 0..n where float and exact-rational (7/10) readings disagree; expected empty, otherwise declared.

### Pitfall 7: REFUSED recipe still needs its noised points run (D-20)
The driver must not skip a recipe whose threshold is `"REFUSED"`. The label is applied in emit, not at launch.

### Pitfall 8: unwired driver behind dry-run tests (memory: dry-run tests hide an unwired driver)
Trace `main() → run()` kwargs. Feed the threshold fill one REAL producer control record (from the rehearsal) before any multi-hour launch.

### Pitfall 9: plans naming paths the code refuses (memory)
Every record path comes from `phase42_prereg` functions built on `V6_RESULT_PATHS` entries selected by equality. Plans quote the function, not a typed string.

### Pitfall 10: noised-point names must not match the control glob
`results/phase42_control_*.json` is a declared INPUT pattern. A noised record named `phase42_control_…` would be exempted from leg (a) and break the D-19 guarantee.

## Code Examples

### 1. Grid fill (verified to execute today, read-only)
```python
# Source: phase35_prereg._rule_e3_grid_subset (L1426-1522); measured 2026-10-13 in a scratch process
import phase35_prereg, phase36_caps, phase36_prereg, teach_persona as tp   # torch at import (seed_list)
BUDGET_RECORD = phase35_prereg.SLOTS["e3_grid_subset"]["input_records"][0]
V4_CONTROL_RECORD = phase35_prereg.SLOTS["e3_grid_subset"]["input_records"][1]
T_MAX = phase36_prereg.ENTRIES["e3_max_steps"]["value"]           # 800, read not typed
RECIPES = tuple({"lr": lr, "steps": t, "batch": tp.BATCH_SIZE}
                for lr in (tp.LR, 1e-3) for t in (phase35_prereg.STEP_BUDGET, T_MAX))  # 1e-3: the one caller-chosen literal
E3_GRID_SUBSET = phase35_prereg.fill(
    "e3_grid_subset", recipes=RECIPES, seed=phase35_prereg.seed_list()[0],
    input_records=(BUDGET_RECORD, V4_CONTROL_RECORD), derivation=ENTRIES["e3_grid_subset"])
phase36_caps.check_unit_caps("E3", **phase36_caps.counts_for("e3_grid_subset", E3_GRID_SUBSET))
phase36_caps.check_unit_caps("E3", sigmas=len(phase35_prereg.E3_SIGMAS))
```
(`ENTRIES["e3_grid_subset"]["value"]` must be `RECIPES` itself; its `source` must name both paths.)

### 2. The D-05 seam around train_stage
```python
# Source: precedent scripts/phase36_probe.py:902-909; seam scripts/phase25_points.py:350-529
def train_cell(plan, *, lr, steps):
    import phase25_points, teach_persona as tp
    saved = (tp.LR, tp.WARMUP_STEPS, tp.MAX_STEPS)
    tp.LR, tp.WARMUP_STEPS, tp.MAX_STEPS = lr, warmup_for(steps), steps   # warmup_for: prereg rule, T // 10
    try:
        blob = phase25_points.train_stage(plan)
    finally:
        tp.LR, tp.WARMUP_STEPS, tp.MAX_STEPS = saved
    cfg = blob["train_config"]
    _prove((cfg["lr"], cfg["warmup_steps"], cfg["max_steps"]) == (lr, warmup_for(steps), steps), "...")
    _prove(blob["live_mechanism"]["composed_steps"] == steps, "...")
    return blob
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Recall scored only at controls (v4.0 25-14) | `score_arm` on every point (phase25_recall, 25-18) | 2026-09-08 | E3 scores all 11 runs from the start. |
| Single fill file per phase | Split fill files when a slot consumes in-phase records (41) | 2026-10-08 | Phase 42 needs two. |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Rafael reads runtime rebinding of `tp.LR/WARMUP_STEPS/MAX_STEPS` (restored in `finally`) as "does not change the constant" (D-05) | Item 3 | A different seam would need a teach_persona edit, which breaks sha pins. Ask at the prereg review. |
| A2 | Data order is identical across lr at the same seed | Item 1 | Only affects the D-10 narrative of "shared" runs; no verdict depends on it. |
| A3 | CPU DP per-step cost is ~1-4 s (from the non-DP 41-11 CPU training at ~0.9 s/step) | Pattern 2 | Rehearsal wall-clock could be longer. Measure first with a bounded run. |
| A4 | Refusal is not required for E3 (declared omission) | Item 5 | If Rafael wants it, +~80 min/point (≈ 14.7 h): far over the E3 line, a cap ruling. |
| A5 | Retention is measured via `measure_condition_c` (unpriced, +0.27-0.65 h) | Item 5/8 | Within slack. If declined, retention is published only for the v4.0 control (3.783). |

## Open Questions

1. **The TPR ≤ e^ε·FPR + δ line.**
   - Known: it is verified as a rearrangement of KOV Thm 2.1, p. 3. It is non-vacuous only for FPR < (1−δ)e^{−ε} (5.69e-70 at ε = 159.44).
   - Unclear: whether Rafael wants it in the text with that caveat.
   - Recommendation: offer it with the caveat; the biased-coin bound stays primary.
2. **Retention measured or not, and refusal omitted.** Recommend retention yes (D-13 asks for it) and refusal no, both stated in the prereg.
3. **Rehearsal shape.** Which legs train for real on CPU and which are planted stand-ins (REFUSED control, the other controls)? Recommend: one real control per T with real warmup, plus the planted unlearnable control. Decide at planning.
4. **ε on glibc at T = 800, σ = 0.5.** Unmeasured. The first CI run after the prereg lands will show it. Write tests tolerance-based from day one.
5. **Exact-rational vs fill-float comparison.** No disagreement exists for the v4.0 control (measured). Planner: add the enumerating test (Pitfall 6) and pre-register "the fill's float" as the comparison.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `.venv` Python | everything | ✓ | 3.11.15 | — |
| torch + MPS | training, scoring | ✓ | 2.7.1, `mps.is_available()` True | CPU (rehearsal only) |
| git tag `v5.0` | `_v4_control` | ✓ | tags v1.0..v5.0 present; `git show v5.0:…` sha = 0c23f6c1… | — |
| `checkpoints/convbase` + dialog/retention bins | trainer, scoring | assumed present (Phases 40/41 trained on this box 2026-10-06..11) | — | none; the trainer refuses loudly |
| Phase 36 budget + ledger | launch | ✓ committed; `require_launch("E3")` passes | — | — |

**Missing with no fallback:** none found.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x in `.venv` (CPU-only) |
| Config file | `pyproject.toml` / `Makefile` (`make test` = `.venv/bin/pytest -q`) |
| Quick run command | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase42_prereg.py tests/test_phase42_threshold_prereg.py tests/test_phase42_recipes.py` |
| Census subset | `.venv/bin/pytest -q tests/test_phase35_prereg.py -k "slot_census or slot_ordering or grids_must or e3_" tests/test_phase36_caps.py tests/test_phase36_ledger.py tests/test_phase23_resume.py::test_resume_from_none_is_inert tests/test_phase25_driver.py::test_os_replace_appears_only_in_the_two_phase25_writers tests/test_lora_inject.py tests/test_phase21_sc5.py tests/test_phase19_erasure.py::test_retention_measurement_pins_a_new_call_site_with_no_adapted_precedent tests/test_phase20_correction.py::test_mitigation_point_verdict_has_no_caller_outside_this_module tests/test_phase32_frontier.py::test_v4_bytes_unchanged_since_the_v4_tag` |
| Full suite command | `nohup sh -c ".venv/bin/pytest -q -p no:cacheprovider > $LOG 2>&1; echo EXIT=\$? >> $LOG" &` + a `until grep -q '^EXIT='` waiter. About 40-45 min, committed tree only (Phase 41 close: 4709 passed / 4 skipped). |

### Phase Requirements → Test Map
| Req / D | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RECIPE-01, D-01/02/03/09 | 4 recipes, batch 8, seed 1337, v4.0 reuse consumed, caps (recipes 4, sigmas 3, steps 800, batch 8) | unit (CPU, real repo) | `pytest tests/test_phase42_prereg.py -k grid` | ❌ Wave 0 |
| RECIPE-01, SC5 | prereg + test file precede every `results/phase42_*`; RECORDS_AT_COMMIT | ancestry | `pytest tests/test_phase42_prereg.py -k "frozen or first_added or records_at_commit"` + `test_phase35_prereg.py -k slot_ordering` | ❌ Wave 0 |
| RECIPE-04, D-08 | P22 onsets 0.0789/0.1578 asserted; planted onset > σ refuses | unit | `pytest tests/test_phase42_prereg.py -k p22` (phase35 has `test_e3_grid_refuses_a_p22_crossing`) | ❌ Wave 0 |
| RECIPE-02, D-11/D-14 | ε per point = `point_epsilon_for_sigma(σ, T, DELTA)` (tolerance), `selection_accounted` False, CURVE_TOTAL over the 8 noised only, controls excluded | unit | `pytest tests/test_phase42_prereg.py -k epsilon` | ❌ Wave 0 |
| RECIPE-03, D-12 | pass iff both legs ≥ fill threshold; REFUSED from the fill; 4×2 labels | unit (truth table) | `pytest tests/test_phase42_prereg.py -k "label or verdict"` | ❌ Wave 0 |
| RECIPE-03, D-19 | threshold file after its inputs, before every noised record | ancestry | `pytest tests/test_phase42_threshold_prereg.py` | ❌ Wave 0 |
| D-05 | `warmup_for(200) == 20`, `warmup_for(800) == 80`; seam rebinds and restores (also on exception); sidecar `train_config` asserted | unit (fake train_stage) | `pytest tests/test_phase42_recipes.py -k warmup` | ❌ Wave 0 |
| D-06/D-07 | noised plan clip = CLIP_NORM, control plan clip = CONTROL_CLIP_NORM, `grad_clip` 1.0 | unit | `pytest tests/test_phase42_recipes.py -k clip` | ❌ Wave 0 |
| D-10 | identity measured (this research); descriptive only | manual (rehearsal note) | — | n/a |
| D-13 | retention/dialogue gap present per point, never read by the label function (AST/argument check) | unit | `pytest tests/test_phase42_prereg.py -k descriptive` | ❌ Wave 0 |
| D-14/D-15 | summary "k de 8 pontos passam; m REFUSED"; null first line literal; no "ainda"/"possivelmente" | unit | `pytest tests/test_phase42_prereg.py -k "summary or null"` | ❌ Wave 0 |
| D-16/D-17 | predictions recorded in prereg before any record; D-16 read from `phase25_recall.json` | unit + ancestry | `pytest tests/test_phase42_prereg.py -k prediction` | ❌ Wave 0 |
| D-20 | a REFUSED recipe's noised cells are still in the run order | unit | `pytest tests/test_phase42_recipes.py -k refused_still_runs` | ❌ Wave 0 |
| D-21 | rehearsal legs (v4 sha reuse, warmup 20/80, P22 at 800, REFUSED) | manual-only CPU rehearsal (hours) | scratch script + `REHEARSAL_EXIT=0` + `STEP` lines grep | n/a |
| D-22 | launch refuses without `require_launch("E3")`; write-once records; end line per MPS record | unit | `pytest tests/test_phase42_recipes.py -k "launch or write_once or ledger"` + `test_phase36_ledger.py::test_every_tracked_v6_mps_record_has_a_launch_line` | ❌ Wave 0 |
| Pitfall 6 | float vs exact-rational threshold disagreement enumerated | unit | `pytest tests/test_phase42_threshold_prereg.py -k exact` | ❌ Wave 0 |
| census | phase42 files pass every repo census (#1-#13) | existing | census subset above | ✅ |

### Sampling Rate
- **Per task commit:** quick run + census subset (< 2 min).
- **Per wave / after each record commit:** the full suite, uncapped (memory: reds appear only once a phase's own records are committed).
- **Phase gate:** full suite green before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] `tests/test_phase42_prereg.py`, committed in the same commit as `scripts/phase42_prereg.py` (ancestry: the first add precedes records).
- [ ] `tests/test_phase42_threshold_prereg.py`, with fill file 2.
- [ ] `tests/test_phase42_recipes.py` (driver; fake `train_stage`/`score_arm`, tmp ledger/heartbeat).
- [ ] `.gitignore` lines for the `phase42e3_*` / `phase42rh_*` csv dirs + a test (41 precedent).
- No framework install needed.

## Security Domain

`security_enforcement` is absent from config, so the section is included. The phase is local, offline and single-user. Its threats are integrity and provenance, not network.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | `_prove` refusals in the Phase 35 rules; record shape checks (`_prove_record`) |
| V6 Cryptography | yes (integrity only) | SHA-256 via `hashlib` (v4.0 control vs tag, adapter digests); never hand-rolled |
| V10/V14 Data integrity | yes | write-once records, append-only ledger proof, ancestry tests |

### Known Threat Patterns
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Threshold chosen after seeing noised results | Tampering | Fill file 2 committed before any noised record (leg a) + phase-local test |
| Reused control silently edited | Tampering | `_v4_control` sha vs `git show v5.0:` |
| Wrong schedule on resume | Tampering | Pitfall 1 check of the checkpoint `train_config` |
| Stand-in approval mistaken for Rafael's | Repudiation | Stand-ins only in the scratch rehearsal root, labelled |
| Untrusted pickle load | Elevation | Only the project's own checkpoints (`weights_only=False` is already scoped to them) |
| Downloaded PDF (KOV) | — | Read in an isolated scratch dir; nothing entered the repo |

## Sources

### Primary (HIGH confidence)
- Repo reads (file:line cited inline): `scripts/phase35_prereg.py`, `scripts/phase25_points.py`, `scripts/teach_persona.py`, `scripts/phase36_probe.py`, `scripts/phase36_ledger.py`, `scripts/phase36_caps.py`, `scripts/phase41_prereg.py`, `scripts/phase41_floors_prereg.py`, `scripts/phase41_erasure.py`, `scripts/phase25_recall.py`, `scripts/phase25_condition_c.py`, `scripts/phase25_epsilon.py`, `scripts/mitigation_gate.py`, `scripts/phase29_prereg.py`, `src/personacore/privacy/dpsgd.py`, `src/personacore/training/schedule.py`, `tests/test_phase35_prereg.py`, `tests/test_phase23_resume.py`, `tests/test_phase36_caps.py`, `tests/test_phase36_ledger.py`, `tests/test_lora_inject.py`, `tests/test_phase19_erasure.py`, `tests/test_phase20_correction.py`, `tests/test_phase21_sc5.py`, `tests/test_phase25_driver.py`, `tests/test_phase32_frontier.py`, `tests/test_phase41_prereg.py`, `tests/test_phase41_floors_prereg.py`.
- Committed records: `results/phase36_budget.json`, `results/phase25_point_dp_n8_sigma{0p000000,0p500000,1p000000}.json`, `results/phase25_recall.json`, `ledger/v6_mps_ledger.jsonl`.
- Measurements this session: MPS/CPU noise probe; read-only grid fill + ε + composition; `require_launch("E3")` + `spent()`; sha of the v4.0 control vs `v5.0`.
- Kairouz, Oh, Viswanath, arXiv:1311.0776v4, §2 Theorem 2.1, p. 3 (fetched; text extracted with PDFKit).

### Secondary / Tertiary
- Wasserman & Zhou 2010, Theorem 2.4: cited through KOV only (not fetched). LOW.

## Metadata
**Confidence breakdown:**
- Standard stack: HIGH. All modules are in the repo, and the grid fill was executed.
- Architecture: HIGH. Leg rules are read from code; the `g42` planted case matches.
- Pitfalls: HIGH for 1-3 and 6-10 (read or measured). MEDIUM for 4 (glibc at T = 800 unmeasured). MEDIUM for 5 (one σ = 1 reading).

**Research date:** 2026-10-13
**Valid until:** the first commit of `scripts/phase42_prereg.py` (after which the Phase 35/42 code is frozen), or 30 days.
