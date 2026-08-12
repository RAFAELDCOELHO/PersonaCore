# Phase 10: EWC Core - Context

**Gathered:** 2026-06-12
**Status:** Ready for planning

<domain>
## Phase Boundary

From-scratch EWC machinery — per-example empirical diagonal Fisher (`continual/fisher.py`) and
the quadratic penalty `(λ/2)·Σ Fᵢ(θᵢ−θ*ᵢ)²` (`continual/ewc.py`) — plugged into the v1.0
training loop additively via one `penalty_fn=None` kwarg feeding the existing
`assemble_loss(..., extra_penalties=())` seam (EWC-01, EWC-02). Fisher and anchor θ* persist
via the open-dict checkpoint `**extra` seam with tied tensors deduplicated by `data_ptr`.
With the penalty off, the v1.0 training trajectory is bit-preserved and all existing tests
stay green. Pure unit-testable machinery against existing artifacts (`best.pt`, TinyStories
bins): no conversational data, no long training runs, and **no λ calibration — the sweep
(EWC-03) is Phase 12's**.

</domain>

<decisions>
## Implementation Decisions

### Fisher normalization scheme
- **D-01:** The stored Fisher is **mean-normalized**: after averaging `gᵢ²` over the N
  examples, divide all Fisher tensors by the global mean over trainable coordinates so
  `mean(F) = 1`. λ then reads as "penalty stiffness relative to an average parameter" and
  Phase 12's log-scale sweep grid is interpretable across runs. The scalar divisor is recorded
  in `fisher_meta` so the raw estimate is recoverable.
- **D-02:** The normalization statistic is computed over **all trainable coordinates** (after
  `data_ptr` dedup of the tied embedding) — dead embedding rows included. Their drag on the
  mean is a constant factor λ absorbs; this keeps Fisher estimation decoupled from the
  `forbid_ids` list and makes `mean(F)=1` literally true over the whole penalty domain.
  (Note: because `wte`/`lm_head` are tied, dead vocabulary rows receive small suppression
  gradients at every position — their Fisher entries are tiny-but-nonzero, not structural
  zeros.)

### Per-example discipline & budget
- **D-03:** Per-example gradients via a **strict batch=1 loop**: one block_size window = one
  example; N independent `zero_grad → forward → CE → backward → accumulate grad²` passes at
  batch size 1, with mean-over-tokens CE matching the training loop's reduction (Pitfall 6).
  EWC-01's "per-example, not batched-gradient squaring" **overrides** ARCHITECTURE.md's
  "batch 1–8" shorthand — with batch > 1, squaring the aggregated gradient is the van de Ven
  bug. Vectorized per-sample grads (`torch.func`) rejected: unneeded at 13.9M and shaky on MPS.
- **D-04:** Production Fisher budget **N ≈ 2000 windows** ("a few thousand" per PITFALLS, with
  margin over ARCHITECTURE's 200–500 floor). Minutes of wall-clock at batch=1 on the M3. N is
  recorded in `fisher_meta`.
- **D-05:** Fisher estimation ships a **lightweight empirical convergence check** alongside the
  unit-test oracle: split the N windows into two disjoint halves, compare the half-estimates
  (rank correlation + relative mean change vs the full estimate), report the numbers in the
  smoke output and store them in `fisher_meta`. "N is enough" becomes a measured claim, in the
  project's evidence-over-assertion register.

### Claude's Discretion
The user delegated two surfaced gray areas to Claude/planner judgment, guided by the research
docs (`.planning/research/ARCHITECTURE.md`, `PITFALLS.md`):

- **Real-weights Fisher run & artifact policy** — smoke-scale proof vs producing the production
  `fisher_tinystories.pt` cache Phase 12/13 arms share; whether the cache file meets the
  safe-load/schema-version bar (Phase 9 `load_adapter` precedent) or stays a plain gitignored
  `torch.save`; script packaging (Phase 9's 09-04 real-weights smoke script is the precedent).
  Constraints that bound the choice: resume checkpoints must stay self-contained (θ*/Fisher by
  value via `**extra` — the cache is an optimization only, ARCHITECTURE anti-pattern 2), and
  Phase 10's success criterion 1 requires Fisher actually estimated at `best.pt` over
  TinyStories batches in this phase.
- **loop.py touch scope** — land only `penalty_fn=None` (the phase's minimum) or also
  `extra_val_bins` + per-run derived CSV fieldnames in the same touch (ARCHITECTURE lists both
  as v2.0 additive loop changes; retention telemetry isn't exercised until Phase 12). Either
  way: defaults must reproduce v1.0 bit-for-bit and the penalty joins `base_loss` **before**
  the `/accum` divide (ARCHITECTURE Pattern 2 / anti-pattern 4).

Also Claude's discretion: λ placeholder convention for Phase-10 tests/smoke, exact
file/module naming within `continual/`, fisher_meta field set (beyond source/N/seed/
anchor-provenance/normalizer/convergence stats already implied), and test-suite organization.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & roadmap
- `.planning/REQUIREMENTS.md` — EWC-01/EWC-02 (the phase's requirement text); EWC-03 explicitly
  excluded (Phase 12); Out of Scope table (no online EWC, no KFAC/full Fisher)
- `.planning/ROADMAP.md` — Phase 10 goal + 4 success criteria; dependency map (Phase 10 is
  independent of 9/11; Phase 12 consumes it)

### v2.0 research (decisions already converged — do not re-litigate)
- `.planning/research/SUMMARY.md` — two-mechanism stage split (EWC = stage-2 full-FT on base
  params, NOT Fisher-of-LoRA-params); `continual/` package shape (`fisher.py` + `ewc.py`);
  Phase-10 deliverable/test list (quadratic-form oracle, zero-at-θ*, penalty-once-per-accum-step,
  `penalty_fn=None` ≡ v1.0 trajectory)
- `.planning/research/ARCHITECTURE.md` — Pattern 2 (EWC as `penalty_fn` in the loop, the exact
  loop.py:138 splice, penalty before `/accum`); component specs for `estimate_fisher`/`EWCPenalty`;
  storage prescription (θ* by value, `fisher_meta` provenance, Fisher cache file as
  optimization); anti-patterns 2–4 (no sidecar resume dependency, no CSV column appends,
  no post-`/accum` penalty, device-move Fisher/θ* once at construction)
- `.planning/research/PITFALLS.md` — Pitfall 6 (the per-example Fisher bug — eval mode, matching
  loss reduction, unit-test list, warning signs); Pitfall 7 (parameter space + tied-tensor
  data_ptr dedup); Pitfall 8 (λ scale awareness — Phase 12 owns the sweep but Phase 10's
  normalization makes it interpretable)

### v1.0 seams this phase consumes (code)
- `src/personacore/training/loss.py` — `assemble_loss(base_loss, extra_penalties=())`: the
  designed EWC seam; D-04 contract (precomputed scalar tensors, no callables inside the tuple)
- `src/personacore/training/loop.py` — `_optimizer_step` (line ~138: `assemble_loss(base_loss, ())`
  is the splice point); `train()` kwarg surface the additive `penalty_fn=None` joins;
  AMP+accum+clip ordering that must not change
- `src/personacore/checkpoint.py` — open-dict `save_checkpoint(**extra)` seam (docstring reserves
  `fisher=`/`theta_star=`); `load_checkpoint` returns the full dict
- `tests/test_assemble_loss.py` — the existing seam-pinning tests that must stay green

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `assemble_loss` (`src/personacore/training/loss.py`): identity-on-empty / additive-on-non-empty,
  built for exactly this phase; EWC supplies `(fisher_penalty,)` per micro-batch
- `train()` / `_optimizer_step` (`src/personacore/training/loop.py`): the full harness (AdamW,
  warmup/cosine, grad-accum, kill+resume, CSV logging) is inherited; only an additive
  `penalty_fn=None` kwarg is added
- `save_checkpoint`/`load_checkpoint` (`src/personacore/checkpoint.py`): `**extra` carries
  `fisher`/`theta_star`/`ewc_lambda`/`fisher_meta` with zero format change
- Existing memmap data path (`training/data.py`): seeded window draws from `train.bin` for
  Fisher estimation
- `best.pt` + TinyStories `train.bin`/`val.bin`: the anchor and estimation data already exist
- Test idioms to mirror: `data_ptr()` dedup tests (`test_gpt_weight_tying.py`), bit-identical
  defaults pattern (`test_ablation_config.py`), trajectory-equality resume tests (Phase 3),
  Phase 9's real-weights smoke script shape (09-04)

### Established Patterns
- **Purity rule:** `model/gpt.py` is never edited; EWC lives in a new `continual/` package
- **Additive, default-off changes only** to v1.0 modules; defaults reproduce v1.0 bit-for-bit
  (all 180 current tests stay green — roadmap's "137" predates Phase 9's additions)
- **Thin scripts, logic in package**; CPU-only GPU-free tests
- **From-scratch boundary:** Fisher via plain autograd `grad²` accumulation — no opacus, no
  torch.func, no library EWC
- Fisher estimation runs under forked RNG (`torch.random.fork_rng`) or before `train()` starts —
  the training RNG trajectory is untouched (resume-equality contract survives)

### Integration Points
- `loop.py` micro-batch site (line ~138): `penalties = (penalty_fn(model),) if penalty_fn else ()`
  feeding `assemble_loss`, **before** `loss = total / accum`
- Phase 12 consumes: `estimate_fisher()`, `EWCPenalty`, the `penalty_fn` kwarg, Fisher/θ*
  checkpoint extras (and the λ sweep builds on D-01's normalization)
- Phase 15 consumes: the Fisher tensors for the VIZ-03 Fisher heatmap (mean-normalized values,
  log color scale)

</code_context>

<specifics>
## Specific Ideas

- λ interpretability is the point of D-01: the Phase-12 sweep grid and the stability–plasticity
  frontier plot should read in "mean(F)=1" units, and the writeup names the variant (empirical
  Fisher, ground-truth targets, mean-normalized) explicitly — same honesty register as the
  v1.0 547-live-ids disclosure
- Evidence over assertion: the half-sample convergence check (D-05) exists so the report can
  say "N=2000 was measured to be enough", not "the literature says a few thousand suffices"

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 10-EWC Core*
*Context gathered: 2026-06-12*
