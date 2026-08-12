# Phase 12: Stage-2 Conversational Fine-Tune - Context

**Gathered:** 2026-07-31
**Status:** Ready for planning

<domain>
## Phase Boundary

`best.pt` becomes a dialogue-capable conversational base via full fine-tune with calibrated
EWC. The phase runs a **sequential calibration smoke** (budget recalibration → masked-vs-unmasked
→ LR sweep → λ log-scale sweep, each stage on the prior winner) with every gate pre-registered
and measurable, then — after ONE blocking user checkpoint on the full smoke report — the
production fine-tune on the Phase 11 PersonaChat bins through the untouched v1.0 `train()`,
with TinyStories retention PPL (`retention_perplexity()`, DEBT-02 frozen policy) logged at
every eval interval from step 0 in per-run CSVs. Deliverables: λ* + retained sweep logs
(EWC-03), conversational base checkpoint + dialogue val PPL + curated transcripts (TUNE-01),
retention curves falling out of training logs (TUNE-02), and a committed smoke report.

**Pre-work already done (not in this phase's plans):** DEBT-01 (true-token `run.csv` column)
and DEBT-02 (`retention_perplexity()` with frozen dead-id mask) closed in commit `ca14a89`,
2026-07-31 — golden trajectory recaptured bit-identical, headline 2.1066 re-verified.

</domain>

<decisions>
## Implementation Decisions

### Masking decision rule (resolves Phase 11 D-02)
- **D-01:** Two short fine-tunes (masked loss vs train-on-everything) compared on dialogue
  val PPL; **tie goes to masked**. Unmasked is adopted only if it beats masked by MORE than
  the pre-registered margin (see D-05 noise floor). Research ARCHITECTURE prescribes masking;
  the smoke only overturns it on clear evidence. Rule is pre-registered — no per-stage human
  stop needed (see D-07).

### LR selection
- **D-02:** 3-point log-spaced LR sweep (pretrain-peak ×1, ×0.3, ×0.1) run on the winning
  mask arm. Selection = lowest dialogue val PPL **passing two pre-registered measurable
  gates** — never a post-hoc visual call on a loss curve:
  1. **Retention proxy:** `retention_perplexity()` (DEBT-02) on a small held-out base-task
     sample, measured before and after each short run. "Collapse" = retention PPL degrades
     past a pre-registered threshold derived from the D-05 noise-floor logic (no invented
     numbers).
  2. **Instability:** mechanically defined — loss diverges (NaN/Inf) OR dialogue val PPL is
     non-monotonic across the short run's own logging intervals. Not a human eyeballing a plot.
  **Fallback pre-registered:** if defining these gates cheaply isn't feasible within the smoke
  budget, say so explicitly and fall back to a blocking user checkpoint on the raw curves
  (masking-smoke register) — never let "no instability" become a silent subjective call.

### Smoke ordering & budget
- **D-03:** **Sequential, recalibrated budget.** Order: budget recalibration → masking (D-01)
  → LR sweep (D-02) → λ sweep (EWC-03), each stage running on the prior stage's winner —
  fewest confounds. The short-run budget is **recalibrated for the dialogue corpus** using the
  v1.0 D-07 method (long enough that val-PPL separation exceeds seed noise), NOT assumed to be
  the TinyStories-calibrated 2500 steps.

### Role-token cold-start (ids 8185–8187)
- **D-04:** **Diagnostic with escalation trigger, measured framing.** Log early-step loss AND
  role-token embedding norms at a **fixed cadence** (every N steps through the first ~10% of
  the smoke budget) during the masking smoke, so there's an actual before/after trajectory —
  not a single post-hoc "yes it spiked" observation. Pre-registered trigger: violation of the
  same D-02 instability gates (NaN/Inf, non-monotonic recovery) escalates to a mitigation
  lever (row reinit to live-row mean, targeted warmup for the three rows, or other — chosen at
  escalation time). **Any mitigation is evaluated with its own before/after comparison against
  the un-mitigated diagnostic run** — no claim of "the mitigation worked" without the number
  showing the un-mitigated baseline it improved on. No mitigation is built unless triggered.

### Noise floor & margins
- **D-05:** **Seed-pair noise run:** one smoke configuration run twice with different seeds at
  the recalibrated budget; the observed dialogue-val-PPL and retention-PPL deltas ARE the
  noise floor. Gate margins = k× that delta. **k is pre-registered with a stated reason:**
  k=2 is declared a deliberately conservative default chosen blind, before seeing any smoke
  result (no principled derivation is available at this budget — say so explicitly). The
  committed report (D-06) must also record, for each gate, **what k the actually-observed
  noise floor would have required**, alongside the verdict — keeping k defensible as "chosen
  blind" rather than "chosen because it validated the pick."

### Smoke report artifact
- **D-06:** **One committed smoke report** — thin script + `results/` markdown, same register
  as Phase 11's `results/inflation_report.md` — recording, for EACH of the four smoke
  decisions (masking threshold, LR stability gates, budget-recalibration noise measurement,
  cold-start spike diagnostic), the raw numbers and the verdict. NOT four different logging
  styles scattered across code comments, terminal prints, and CONTEXT prose. Phase 15's
  honest-numbers writeup cites this report directly, the same way it cites the inflation
  report.

### Checkpoint cadence
- **D-07:** Pre-registered rules **auto-proceed stage-to-stage** (that's what pre-registration
  buys — the masking verdict and LR pick don't each need a human stop). **ONE blocking user
  checkpoint before the production fine-tune**, presenting the full smoke report (including
  the λ sweep results / λ* pick, since the λ sweep is the smoke sequence's final stage).
  **EXCEPTION:** any violated gate mid-sequence (instability, retention collapse, cold-start
  escalation trigger) **halts immediately** and surfaces to the user right then — never
  bundled silently into the final report.

### Claude's Discretion
Areas offered but not selected for discussion — decide from research, within the pre-registration
discipline above:
- **λ sweep design details** (EWC-03): grid size/range within the reported 0.1–10⁶, per-point
  budget (the D-03 recalibrated short budget), and the concrete stability–plasticity λ* pick
  rule — presented for confirmation at the D-07 blocking checkpoint. Sweep logs retained for
  Phase 13's frontier plot (requirement text).
- **Production run budget & stopping policy**, and what evidence constitutes dialogue-format
  adherence (transcript count, prompt set) for TUNE-01.
- **Conversational-base artifact contract**: best-checkpoint criterion, embedded extras
  (fisher/theta_star/ewc_lambda per research ARCHITECTURE), naming/location, slim export, and
  whether the production run doubles as Phase 13's EWC arm (coordinate with Phase 13's
  identical-seed requirement).
- **`stop_ids` wiring** in `generate()` (Phase 11 D-03: lands here, additive, default
  `{eos_id}`) — needed for curated transcripts.
- Mechanics: retention-proxy sample size, cold-start logging cadence N, CSV/file naming
  (new per-run CSV files per research — never append columns to v1.0 `run.csv`).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & roadmap
- `.planning/REQUIREMENTS.md` — EWC-03, TUNE-01, TUNE-02 requirement text; DEBT-01/02 marked
  complete (pre-work 2026-07-31)
- `.planning/ROADMAP.md` — Phase 12 goal + 5 success criteria; research flag (λ selection
  empirical, LR/budget calibration → plan with `--research-phase`); dependency map (12 needs
  10+11; 13 needs 12; 14 needs 9+12)

### v2.0 research (converged — do not re-litigate)
- `.planning/research/ARCHITECTURE.md` — Pattern 2 (EWC penalty joins base_loss BEFORE the
  `/accum` divide; `EWCPenalty` constructed once per run; Fisher/θ* moved to device at
  construction); Pattern 4 (`stop_ids` additive design); CSV discipline (per-run
  `CSV_FIELDNAMES`, new files like `logs/finetune_<arm>.csv`, optional `ewc_penalty` column);
  checkpoint extras (`fisher=`, `theta_star=`, `ewc_lambda=`, `fisher_meta=`); data-flow
  diagram (best.pt → estimate_fisher → EWCPenalty → convbase checkpoints); role-token
  cold-start flagged as this phase's calibration concern
- `.planning/research/PITFALLS.md` — the accum-divide/device-mismatch pitfall (λ silently
  scales with `grad_accum_steps`); Pitfall 14 (LM-regime masking is the Phase 11 path this
  phase consumes)

### Prior phase context (decisions this phase inherits)
- `.planning/phases/11-conversational-data-pipeline/11-CONTEXT.md` — D-02 (masked-vs-unmasked
  deferred HERE as a measured decision — resolved by this phase's D-01), D-03 (`stop_ids`
  lands here), D-04 serialization format, D-09 gate verdict (GO, 1.129×)
- `.planning/phases/10-ewc-core/10-CONTEXT.md` — Fisher normalization (mean-normalized),
  N≈2000 budget, per-example discipline
- `results/inflation_report.md` — the committed gate-report register D-06 mirrors; the
  tokenizer-tax number

### v1.0/v2.0 seams this phase consumes (code)
- `src/personacore/training/loop.py` — the untouched v1.0 `train()` (TUNE-01 requires it stay
  untouched): `train_bin`/`val_bin` memmap seams, `penalty_fn`/`checkpoint_extra` EWC splice,
  kill+resume with `best_val_loss`; DEBT-01 true-token telemetry fix lives here
- `src/personacore/training/data.py` — `get_batch_memmap_masked` (Phase 11, the D-01 masked
  arm's batch fn) + `get_batch_memmap` (unmasked arm)
- `src/personacore/continual/fisher.py` + `ewc.py` — `estimate_fisher` / `EWCPenalty`;
  production Fisher cache at `best.pt` (N=2000, spearman_half 0.989)
- `src/personacore/evaluation/perplexity.py` — `retention_perplexity()` (DEBT-02, frozen
  dead-id policy — the ONLY sanctioned retention-PPL for curve points) and unmasked
  `perplexity()` (headline 2.1066 anchor)
- `src/personacore/generation/core.py` — `generate()` gaining additive `stop_ids` here
- `data/dialog_{train,val}.bin` + `data/dialog_{train,val}_mask.bin` — the Phase 11 bins
  (5.26M train / 638K val tokens, masked fraction ~0.43)
- `scripts/run_ablations.py` — the D-07 calibrated-short-budget precedent D-03's
  recalibration mirrors

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `train()` (`training/loop.py`): the entire production loop — fine-tune = `train()` with
  `best.pt` weights loaded into the model, `train_bin=dialog_train.bin`,
  `penalty_fn=EWCPenalty(...)`, new log/checkpoint paths. Nothing new to build in the loop.
- `estimate_loss`/CSVLogger: restart-safe per-run CSVs; extra columns (retention PPL,
  ewc_penalty) ride the per-run `CSV_FIELDNAMES` design
- `run_ablations.py`: the calibrated-short-budget cohort pattern for all smoke stages
- Phase 10's `EWCPenalty` + cached Fisher: constructed once per run, zero estimation cost
  per smoke arm (all arms share the one N=2000 cache)

### Established Patterns
- **Pre-registration discipline:** bands/margins/gates locked before numbers exist (Phase 11
  D-09 precedent) — this phase extends it to k, LR gates, and mitigation evaluation
- **Evidence-over-assertion:** committed results/ reports with raw numbers + verdicts
- **Purity/additivity:** `train()` and `model/gpt.py` untouched; everything rides existing
  seams; all 250 existing tests stay green
- **Golden-trajectory protection:** any loop-adjacent change must keep the recaptured
  fixture bit-identical (DEBT-01 precedent)

### Integration Points
- Phase 13 consumes: the fine-tune harness/config, λ*, retained sweep logs (frontier plot),
  and the per-arm CSV format (forgetting curves)
- Phase 14 consumes: the conversational-base checkpoint (LoRA substrate) and `stop_ids`
- Phase 15 consumes: the committed smoke report (D-06) and the honest numbers in it

</code_context>

<specifics>
## Specific Ideas

- **Measured framing everywhere:** every gate in this phase is a number compared against a
  pre-registered threshold — "no instability" is NaN/Inf or non-monotonicity, never a human
  reading a plot; "the mitigation worked" requires the un-mitigated baseline number it
  improved on
- **k chosen blind:** thresholds must be defensible as "chosen before seeing results", with
  the counterfactual k-required-per-gate reported alongside — explicitly guarding against
  thresholds that happen to validate the recommended choice
- **One report, one register:** all smoke evidence lands in a single committed report in the
  inflation-report style, citable by Phase 15 verbatim

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. (The unselected gray areas — λ sweep design,
production stopping, conv-base artifact — are in-phase and delegated to Claude's discretion
above, not deferred to other phases.)

</deferred>

---

*Phase: 12-Stage-2 Conversational Fine-Tune*
*Context gathered: 2026-07-31*
