# Phase 10: EWC Core - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-12
**Phase:** 10-EWC Core
**Areas discussed:** Fisher normalization scheme, Per-example discipline & budget

---

## Gray Area Selection

Four gray areas were surfaced; the user selected two for discussion and delegated the other
two (Real-weights Fisher run & artifact, loop.py touch scope) to Claude's discretion.

| Surfaced area | Selected |
|---------------|----------|
| Fisher normalization scheme | ✓ |
| Real-weights Fisher run & artifact | (delegated) |
| loop.py touch scope | (delegated) |
| Per-example discipline & budget | ✓ |

---

## Fisher normalization scheme

### Q1: Beyond averaging over the N examples, should the stored Fisher be rescaled so λ becomes interpretable?

| Option | Description | Selected |
|--------|-------------|----------|
| Mean-normalize (Recommended) | Divide all Fisher tensors by the global mean over trainable coordinates so mean(F)=1; λ reads as penalty stiffness relative to an average parameter; divisor recorded in fisher_meta | ✓ |
| Raw only — λ absorbs scale | Plain averaged empirical Fisher (paper-faithful Kirkpatrick form); λ values become non-portable magic numbers | |
| Raw stored, normalize at use | estimate_fisher() stores raw; EWCPenalty optionally normalizes at construction — two places where scale can drift (Pitfall-8 hazard) | |

**User's choice:** Mean-normalize (Recommended)
**Notes:** Aligns with research SUMMARY's "Normalize Fisher so λ is interpretable" gap-resolution guidance.

### Q2: Which coordinates feed the mean-normalization statistic?

| Option | Description | Selected |
|--------|-------------|----------|
| All trainable coords (Recommended) | Global mean over every trainable parameter after data_ptr dedup; dead-row drag is a constant factor λ absorbs; no forbid_ids coupling | ✓ |
| Exclude dead embedding rows | Mean over live coordinates only; couples Fisher estimation to the 547-live-ids list and adds a masking step | |

**User's choice:** All trainable coords (Recommended)
**Notes:** Context raised during discussion: tied wte/lm_head means dead vocabulary rows receive
small suppression gradients at every position — their Fisher entries are tiny-but-nonzero, not
structural zeros; the all-coords mean is the cleaner population either way.

---

## Per-example discipline & budget

### Q1: How should per-example Fisher gradients be computed?

| Option | Description | Selected |
|--------|-------------|----------|
| Strict batch=1 loop (Recommended) | One window = one example; N independent forward/backward passes at batch 1, mean-CE matching the training reduction; EWC-01 wins over ARCHITECTURE's "batch 1–8" shorthand | ✓ |
| Vectorized per-sample grads | torch.func (vmap+grad) — correct at batch>1 but bolts functional-transform machinery onto a from-scratch narrative; shaky on MPS | |
| Accept small-batch approximation | Keep ARCHITECTURE's batch 1–8 squaring — violates EWC-01's explicit text; reintroduces a mild form of the van de Ven bug | |

**User's choice:** Strict batch=1 loop (Recommended)
**Notes:** Resolves a genuine documentation conflict: REQUIREMENTS.md EWC-01 ("per-example
gradients ... not batched-gradient squaring") vs ARCHITECTURE.md's "(batch 1–8)" sketch. The
requirement text wins; ARCHITECTURE's range is treated as a shorthand error.

### Q2: How many TinyStories windows (N) feed the production Fisher estimate?

| Option | Description | Selected |
|--------|-------------|----------|
| ~2000 windows (Recommended) | Matches PITFALLS' "a few thousand windows" with margin over ARCHITECTURE's 200–500 floor; minutes of wall-clock at batch=1 on the M3 | ✓ |
| ~500 windows | ARCHITECTURE's upper sketch value; fastest, but λ calibration in Phase 12 inherits any tail-coordinate noise | |
| ~5000 windows | Extra statistical margin; diminishing returns beyond "a few thousand" | |

**User's choice:** ~2000 windows (Recommended)

### Q3: Should the Fisher estimation ship an empirical convergence check alongside the unit-test oracle?

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — lightweight check (Recommended) | Two disjoint half-sample estimates compared (rank correlation + relative mean change); reported in smoke output and stored in fisher_meta | ✓ |
| No — oracle tests suffice | Tiny-fixture oracle + non-negativity + determinism tests prove correctness; N documented with a literature citation | |

**User's choice:** Yes — lightweight check (Recommended)
**Notes:** "N is enough" becomes a measured claim — consistent with the project's
evidence-over-assertion register.

---

## Claude's Discretion

- **Real-weights Fisher run & artifact policy** — smoke-scale vs production
  `fisher_tinystories.pt` cache; safe-load bar for the cache file; script packaging
  (bounded by: self-contained resume checkpoints, success criterion 1 requiring a real
  `best.pt` estimation in-phase)
- **loop.py touch scope** — `penalty_fn=None` only vs also `extra_val_bins` + per-run CSV
  fieldnames in the same touch (bounded by: bit-identical defaults, penalty before `/accum`)
- λ placeholder convention for Phase-10 tests/smoke; `continual/` module naming;
  fisher_meta field set; test-suite organization

## Deferred Ideas

None — discussion stayed within phase scope.
