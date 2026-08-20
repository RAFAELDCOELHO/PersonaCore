# Architecture Research

**Domain:** Training-time privacy mitigation (DP-SGD + adversarial training) and relearning validation, spliced into a shipped from-scratch LoRA/GPT stack
**Milestone:** v4.0 "Leakage Mitigation and Relearning Validation" (Phase 20+)
**Researched:** 2026-08-20
**Confidence:** HIGH on integration points (read against the live tree at `4554ef4`), HIGH on the DP mechanism math (verified against primary sources), MEDIUM on the wall-clock estimates (they are the thing Phase 20 is supposed to *measure*, not assume)

---

## TL;DR — the seven load-bearing calls

1. **DP-SGD needs ONE new loop line.** A `grad_privatizer` callable invoked inside `_optimizer_step`'s existing accumulation loop, immediately after `scaler.scale(loss).backward()`. It reads `.grad`, clips, buffers, zeroes, and on the last micro-batch writes back `mean + noise`. Default `None` → the `if` is false → not one float operation changes. Same shape as `penalty_fn`, same golden-trajectory proof.
2. **The DP unit of privacy must be the FACT, not the 256-token window.** Example-level DP over random windows gives no per-fact guarantee, and group privacy at the real multiplicity destroys ε. Fix it in the *data* layer: pad each fact's episodes to a whole number of `block_size` windows, then `grad_accum_steps = n_facts`. This makes the existing grad-accum machinery the per-example loop — no new gradient math at all.
3. **With fact-aligned full-batch steps there is no subsampling, so the accountant is exact and ~20 lines.** T compositions of the Gaussian mechanism is exactly μ-GDP with μ = √T/σ; (ε, δ) comes from a closed-form Φ expression. No RDP order sweep, no Sampled-Gaussian binomial sum, no new dependency, and it is *tight* rather than a bound.
4. **The adversarial arm needs NO training-loop change.** Attack intensity is a data-mixture ratio, exactly the shape `_prepend_replay` already has. It is a `build_bins` kwarg.
5. **The unmitigated control arm should BE a sweep point** — the DP arm at `clip_norm=inf, noise_multiplier=0.0`. Then control and DP differ by exactly the two DP parameters, structurally, and the frontier gets a natural ε=∞ anchor.
6. **Two pre-registration files, not one.** `scripts/mitigation_gate.py` holds only `OUTCOME_*` (X, Y — frozen before any point). `scripts/mitigation_budget.py` holds only `BUDGET_*` (Z — derived from the cost measurement). An AST guard forbids the gate from importing the budget. The X-vs-Z distinction becomes a fact about the import graph and about git ancestry, not a paragraph.
7. **The cost-to-recovery curve is free.** It rides the existing `extra_eval_fns` seam (Phase 12 precedent: `retention_ppl` as a CSV column per eval event). No new instrumentation.

---

## System Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│  PRE-REGISTRATION LAYER  (stdlib only, no torch, committed before data)   │
├──────────────────────────────────────────────────────────────────────────┤
│  scripts/mitigation_gate.py      scripts/mitigation_budget.py            │
│   OUTCOME_* : X, Y, verdict fn    BUDGET_* : Z, sweep width, steps       │
│   frozen before ANY curve point   set FROM the cost measurement          │
│         │  ▲ AST guard: gate MUST NOT import budget                      │
│         │  │ imports wilson_upper_bound from scripts/erasure_gate.py     │
├─────────┼──┼─────────────────────────────────────────────────────────────┤
│  ORCHESTRATION LAYER  (scripts/, unpinned, resumable per sweep point)     │
├─────────┼──┼─────────────────────────────────────────────────────────────┤
│  scripts/phase2X_frontier.py   ── subcommands: cost / sweep / score /    │
│    _refuse() + _merge_block() idempotent per point (phase19_run.py idiom) │
│  scripts/phase2X_relearn.py    ── mitigated arm + fresh arm, one spec     │
│         │                                                                │
├─────────┼────────────────────────────────────────────────────────────────┤
│  MECHANISM LAYER  (src/personacore/, importable, unit-testable, CPU)      │
├─────────┼────────────────────────────────────────────────────────────────┤
│  privacy/dpsgd.py         DPSGDPrivatizer  ── the gradient-side seam      │
│  privacy/accountant.py    mu_gdp() / epsilon_at_delta()  ── pure math     │
│         │                                                                │
├─────────▼────────────────────────────────────────────────────────────────┤
│  EXISTING STACK  (modified only at named additive seams)                  │
├──────────────────────────────────────────────────────────────────────────┤
│  training/loop.py    + grad_privatizer=None   (ONE new call site)         │
│  training/data.py    + get_batch_fact_aligned (NEW fn, nothing modified)  │
│  lora/  continual/  dialogue/  generation/  model/   ── UNTOUCHED         │
├──────────────────────────────────────────────────────────────────────────┤
│  EVIDENCE LAYER  (committed JSON, then plot-only)                         │
├──────────────────────────────────────────────────────────────────────────┤
│  results/phase2X_frontier.json  ──►  scripts/plot_phase2X.py (no torch)   │
│                                 ──►  verdict (imports OUTCOME_* consts)   │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Where DP-SGD splices into `training/train()`

### The problem stated precisely

`penalty_fn` is a **loss-side** seam: it produces a scalar that joins `base_loss` through
`assemble_loss` *before* `backward()` (`training/loop.py:159-161`). DP-SGD is a **gradient-side**
intervention — it must act on per-example gradients between `backward()` and `optimizer.step()`.

There is no existing seam for that. The nearest thing is the fixed AMP ordering block at
`training/loop.py:164-168`:

```python
scaler.unscale_(optimizer)                                       # loop.py:164
torch.nn.utils.clip_grad_norm_(model.parameters(), train_cfg.grad_clip)
scaler.step(optimizer); scaler.update(); scheduler.step()
```

A hook placed *there* is too late: by then `.grad` holds the **sum over all micro-batches**, and
per-example gradients are unrecoverable. The seam must live **inside** the accumulation loop.

### The key insight that makes this cheap

`_optimizer_step` already runs a per-micro-batch loop (`loop.py:155-163`). If the driver sets
`grad_accum_steps = n_facts` and each micro-batch draws exactly one fact's windows, then **the
existing loop already is the per-example loop.** DP-SGD needs no per-sample-gradient machinery
(no `torch.func.vmap(grad(...))`, no ghost-norm hooks, no `functorch` functionalization of the
GPT). It needs a callable that runs once per micro-batch.

> **Why not ghost clipping / closed-form per-example norms?** The arithmetic says don't. Ghost
> norms cost ~`2·T²·(d_out + r)` per example against `2·T·d_out·r` for the direct outer product.
> At this shape (`T=256`, `d_out=384`, `r=8`): ghost = 256²·392 ≈ 25.7M vs direct = 256·384·8 ≈
> 786K. Ghost clipping is a *memory* optimization for large `d_out·r`; at r=8 it is 30× slower.
> And the whole adapter is 331,776 params = 1.33 MB fp32, so materializing per-example gradients
> is trivially affordable anyway. **Both optimizations are unnecessary at this scale.** Record
> this so a later reader does not think the simple design was chosen out of ignorance.

### The signature — NEW parameter, `training/loop.py`

```python
# MODIFIED: src/personacore/training/loop.py
def _optimizer_step(
    model, optimizer, scheduler, scaler, train_cfg, runtime, batch_fn,
    penalty_fn=None,
    grad_privatizer=None,          # <-- NEW, keyword-defaulted, last
):
    ...
    for micro in range(accum):
        xb, yb = batch_fn(micro)
        with runtime.autocast():
            _, base_loss = model(xb, yb)
            penalties = (penalty_fn(model),) if penalty_fn is not None else ()
            total = assemble_loss(base_loss, penalties)
            loss = total / accum
        scaler.scale(loss).backward()
        if grad_privatizer is not None:                              # <-- THE ONLY NEW LINE
            grad_privatizer(model, micro=micro, n_micro=accum)
        summed += float(base_loss.item())
    scaler.unscale_(optimizer)
    ...
```

```python
# MODIFIED: src/personacore/training/loop.py — train() signature, one new kwarg
def train(
    *,
    train_config, runtime_config=None, model=None, model_config=None,
    ...
    penalty_fn=None,
    grad_privatizer=None,          # <-- NEW
    checkpoint_extra=None, extra_eval_fns=None, return_final_loss=False,
):
```

**Docstring contract to add (mirroring `penalty_fn`'s at `loop.py:256-258`):**

> `grad_privatizer`: callable `(model, *, micro: int, n_micro: int) -> None` invoked after each
> micro-batch's `backward()` (the DP-SGD gradient-side seam, PRIV-01). The callable owns the
> whole accumulation: it reads `p.grad` (which holds exactly THIS micro-batch's gradient because
> the callable zeroes it each time), clips, accumulates into its own buffer, and on
> `micro == n_micro - 1` writes `buffer / n_micro + noise` back into `p.grad`. `None` (the
> default) reproduces v1.0/v2.0 bit-for-bit — the `if` never evaluates its body.

### The mechanism — NEW module

```python
# NEW: src/personacore/privacy/dpsgd.py
class DPSGDPrivatizer:
    """Per-example (per-FACT) clipping + Gaussian noise on the LoRA gradients only.

    The base is frozen (mark_only_lora_trainable), so `params` is exactly the 331,776
    lora_A/lora_B tensors. Nothing else has a .grad to privatize.
    """

    def __init__(self, params, *, clip_norm, noise_multiplier, generator, device):
        ...

    def __call__(self, model, *, micro, n_micro) -> None:
        """Clip this micro-batch's grad, buffer it, and on the last micro emit mean+noise."""

    @property
    def clipped_fraction(self) -> float:
        """Diagnostic: fraction of per-example grads whose norm exceeded clip_norm.
        Near 1.0 means clip_norm is too small and the signal is being destroyed;
        near 0.0 means the clip never binds and the sensitivity bound is loose."""
```

Body sketch (the load-bearing 8 lines):

```python
def __call__(self, model, *, micro, n_micro):
    total_sq = sum(float(p.grad.detach().pow(2).sum()) for p in self._params)
    norm = total_sq ** 0.5
    coef = min(1.0, self.clip_norm / (norm + 1e-12))
    self._clipped += (coef < 1.0)
    for buf, p in zip(self._buf, self._params):
        buf.add_(p.grad, alpha=coef)
        p.grad.zero_()                    # next micro-batch starts clean
    if micro == n_micro - 1:
        std = self.noise_multiplier * self.clip_norm
        for buf, p in zip(self._buf, self._params):
            noise = torch.normal(0.0, std, buf.shape, generator=self._gen, device=buf.device)
            p.grad.copy_((buf + noise) / n_micro)
            buf.zero_()
```

### Three fail-loud guards that belong in `train()`, not in the privatizer

| Guard | Where | Why |
|-------|-------|-----|
| `grad_privatizer is not None and runtime.amp` → raise | `train()` preamble | Under fp16 AMP, `.grad` is still scaled at the point the privatizer reads it, so the clip norm is wrong by `scaler.get_scale()` and the (ε,δ) claim is void. `estimate_fisher` already refuses autocast for the analogous reason (`continual/fisher.py:34-36`). MPS/CPU are fp32 so this never fires on the primary path — it fires on the P100 fallback, loudly, which is exactly right. |
| `grad_privatizer is not None and math.isfinite(train_config.grad_clip)` → raise | `train()` preamble | `clip_grad_norm_` at `loop.py:165` would re-clip the *noised* gradient. DP survives (post-processing immunity), but the reported ε would describe a gradient the optimizer never saw. Drivers set `grad_clip=float("inf")`, which `clip_grad_norm_` treats as a no-op (its coefficient is clamped to ≤1). |
| `grad_privatizer is not None and any(p.requires_grad for non-lora p)` → raise | `DPSGDPrivatizer.__init__` | The (ε,δ) claim covers exactly the parameters that were clipped and noised. A base parameter with `requires_grad=True` would be updated in the clear while the report claims DP. |

### Proving the default path is bit-identical

Exactly the `penalty_fn` playbook (`tests/test_loop_penalty_fn.py`), two independent legs:

1. **Golden replay, platform-gated.** Regenerate `tests/fixtures/golden_trajectory_v1.json`? **No.**
   The existing fixture still applies — it was captured pre-EWC and the EWC splice did not
   invalidate it, because a splice that is bit-identical when off keeps every earlier golden valid.
   Add `test_grad_privatizer_omitted_replays_golden` reusing `_run_recipe`. Skips off the capture
   platform, exactly as today.
2. **In-process identity, never skips.** `grad_privatizer` omitted ≡ `=None` ≡ (bitwise) — assert
   equal CSV text, `repr(final)`, and param sha256.

**Do NOT add a third leg comparing the plain path to `DPSGDPrivatizer(clip_norm=inf,
noise_multiplier=0.0)`.** It will fail, correctly: the privatizer's zero-and-re-add changes the
floating-point summation order, and fp addition is not associative. Pin that arm against the
**batch-1 reference oracle** instead (below) with a documented tolerance, not against the plain path.

### The reference oracle — the from-scratch correctness proof

`tests/test_dpsgd_oracle.py` (CPU, seconds, tiny fixture model):

- Compute the per-fact gradients by a **strict batch-1 autograd loop** — literally the shape
  `estimate_fisher` uses (`continual/fisher.py:110-121`, `torch.autograd.grad(loss, params)`).
- Clip and average them by hand in the test.
- Assert `DPSGDPrivatizer` at `noise_multiplier=0.0` reproduces that vector within fp32 tolerance.

This is the same discipline as `tiktoken`-as-oracle for BPE and the brute-force oracle for
`perplexity()`: the fast path is the deliverable, the obvious-but-slow path is the judge.

### The accountant — NEW module, pure stdlib

```python
# NEW: src/personacore/privacy/accountant.py   (no torch, no numpy, no scipy)
def mu_gdp(*, steps: int, noise_multiplier: float) -> float:
    """mu = sqrt(T)/sigma — the exact GDP parameter of T composed Gaussian mechanisms."""

def delta_at_epsilon(*, mu: float, epsilon: float) -> float:
    """Phi(-eps/mu + mu/2) - exp(eps) * Phi(-eps/mu - mu/2). Exact, via math.erf."""

def epsilon_at_delta(*, mu: float, delta: float, tol: float = 1e-10) -> float:
    """Invert delta_at_epsilon by bisection (delta is strictly decreasing in eps)."""
```

**Why GDP and not RDP.** Because the fact-aligned design has **no subsampling** (`q = 1`: every
fact participates in every step), composition of T Gaussian mechanisms is *exactly* μ-GDP with
`μ = √T/σ`, and the (ε,δ) tradeoff has a closed form. That is tight, not a bound — no order sweep,
no Sampled-Gaussian binomial sum, no `lgamma`. ~20 lines against ~120 for an RDP-SGM accountant,
and a *better* number.

**Do not chase subsampling amplification.** At n≈8 facts, `q` would be ≈0.5–1.0 and amplification
buys nothing while costing the entire SGM accountant. Declare it: "no subsampling amplification is
claimed; the mechanism is full-batch."

**Test oracle for the accountant:** hard-code 4–6 published (σ, T, δ) → ε reference triples with
their citation in the test file. Do not add `opacus` or `dp-accounting` as a dev dependency — the
zero-new-deps posture has been held through three subsystems and taking a dependency *here*, in the
milestone whose entire output is trust in a measurement, would retcon all of it. A second self-check
is available for free: `delta_at_epsilon(mu=1/σ, ...)` at T=1 must equal the analytic Gaussian
mechanism value.

---

## 2. The unit of privacy — the decision that determines whether the ε means anything

**This is the single most consequential architectural choice in v4.0, and it is easy to get
silently wrong.**

Today `get_batch_memmap_masked` (`training/data.py:117`) draws **random contiguous 256-token
windows** from a flat concatenation of all facts' episodes (`teach_persona.build_bins`,
`scripts/teach_persona.py:277-280`). Under that layout:

- An "example" is a random window, which may straddle two facts.
- Each fact appears in **many** windows across the ~8,200-token corpus.
- Example-level (ε, δ)-DP therefore says nothing about a fact. Converting via group privacy at
  multiplicity `k` gives `(kε, k·e^{(k-1)ε}·δ)` — which at realistic `k` is vacuous.

**A milestone whose claim is "the taught fact is protected" cannot ship an example-level ε.**

### Recommended fix: fact-aligned windows (data layer, additive)

```python
# MODIFIED (additive kwarg): scripts/teach_persona.py
def build_bins(tok, episodes, bin_path, mask_path, *, replay_ratio=0.0,
               align_facts=None):     # <-- NEW: list[fact_id] parallel to `episodes`
    """When align_facts is given, group shards by fact and EOS-pad each group to a whole
    multiple of BLOCK_SIZE, so window index -> fact id is a total function. None reproduces
    the v2.0 layout byte-for-byte."""
```

```python
# NEW function (nothing modified): src/personacore/training/data.py
def get_batch_fact_aligned(bin_path, mask_path, fact_index, windows_per_fact,
                           block_size, device):
    """Draw the `windows_per_fact` windows belonging to ONE fact, at fixed aligned offsets.

    Deterministic by construction — no np.random draw at all, so the data order is a
    function of the fact schedule and not of the global RNG stream.
    """
```

Then:

| Setting | Value | Consequence |
|---------|-------|-------------|
| `grad_accum_steps` | `n_facts` | the existing accumulation loop IS the per-example loop |
| `batch_size` | `windows_per_fact` | one micro-batch = one fact, entirely |
| sampling rate `q` | 1.0 | exact GDP, no amplification machinery |
| tokens/step | whole teaching corpus | full-batch gradient descent |

### The structural enforcement (not a docstring)

`build_bins` must raise if any `block_size`-aligned window contains token ids from two different
fact shards. This is the same move as Phase 14's `assert_value_in_prompt` — a token-id containment
check that fails loudly, not an invariant asserted in prose. Concretely: record each fact's
`[start, end)` byte range at build time, assert every range starts and ends on a `block_size`
boundary, and assert `end - start` is a positive multiple of `block_size`.

### The confound this creates, and its fix

Full-batch fact-aligned training has different optimization dynamics from v2.0's stochastic-window
recipe. If the DP arm used the new recipe and the baseline used v2.0's, every difference would be
uninterpretable.

**This is precisely why PROJECT.md demands a retrained unmitigated control** — and it upgrades that
requirement from hygiene to load-bearing. Recommendation:

> **The unmitigated control arm IS a sweep point: the DP arm at `clip_norm=float("inf")`,
> `noise_multiplier=0.0`.** Same driver, same data path, same `grad_privatizer` arithmetic, same
> seed. It differs from every DP point by exactly the two DP parameters. It also gives the frontier
> a natural ε=∞ anchor at zero extra implementation cost.

Record explicitly, before anyone rediscovers it as a "bug": the ε=∞ point is **not** bit-identical
to a `grad_privatizer=None` run, because the buffer round-trip reorders fp additions. That is
intentional — every curve point including the control shares one arithmetic path.

### If fact-alignment turns out infeasible

Fallback, in preference order:
1. Report example-level ε **and** the measured multiplicity `k` per fact **and** the group-privacy
   inflation, with the headline scoped to "example-level" — an honest weaker claim.
2. Do not report an ε at all and run the DP arm as an empirical noise-injection mechanism with no
   formal claim. This is strictly worse: DP-SGD is the *only* arm that makes a formal claim, and
   without it v4.0 has two empirical arms and no theory.

Option 2 should be treated as a milestone-scope failure, not an acceptable fallback.

---

## 3. Where the sweep orchestration lives

### Verdict: `scripts/`, not `src/`

The sweep has **zero reuse surface**. It runs once, produces committed evidence, and is never
imported by the demo, the tests-under-`src`, or another milestone. `src/personacore/` earns its
place by being the import surface everything depends on; a sweep loop is not that. This matches
every precedent in the repo — `phase19_run.py` (3,036 lines of orchestration) lives in `scripts/`
while its mechanism (`ablate`, `load_adapter_weights`) lives in `src/`.

What goes in `src/personacore/privacy/`: `DPSGDPrivatizer` and the accountant. **Nothing else.**

### The driver

```
NEW: scripts/phase2X_frontier.py         # unpinned, editable, resumable
     subcommands:  cost | sweep | score | report
NEW: scripts/mitigation_gate.py          # PINNED: OUTCOME_* only  (see §4)
NEW: scripts/mitigation_budget.py        # PINNED-after-cost: BUDGET_* only
```

### Resumability — two levels, and only one of them is worth building

**Level 1: the sweep point (BUILD THIS).** Reuse `phase19_run.py`'s `_merge_block` idiom verbatim
(`scripts/phase19_run.py:250-265`):

```python
def _merge_point(path, point_id, block):
    """Merge ONE sweep point into results/phase2X_frontier.json. An existing point is NOT
    replaced — it is recorded evidence and there is no force flag."""
```

A killed session resumes by re-running `sweep`; every point whose block already exists is skipped
with a printed reason. The unit of resumption is a sweep point.

**Level 2: within a training run (DO NOT BUILD THIS).** `train()` already has
`checkpoint_interval` + `resume_from`, but `teach_persona.train_arm` deliberately calls
`refuse_if_exists` on all five outputs (`scripts/teach_persona.py:560-562`), so a killed point
leaves a checkpoint that *blocks* the retry. At 200 steps (~40 s on the M3 at the v2.0 measured
rate) the correct answer is to **delete the point's five artifacts and restart it**, not to thread
resume. Give the driver a `--redo-point <id>` that deletes exactly those five paths after printing
them. Anything more is engineering for a 40-second failure.

Note this is a *deliberate divergence* from the pretraining precedent (where a 50,000-step run
genuinely needed step-level resume). Write the reason down in the driver docstring so a reviewer
does not read it as an oversight.

### What each point records

`train_arm` already prints a full provenance line (`scripts/teach_persona.py:734-744`: seed, lr,
weight_decay, batch_size, max_steps, base fingerprint, `driver_git_sha`, device, torch version,
final loss, UTC). v4.0's job is to **capture that into the artifact instead of only printing it** —
see the schema in §5. Add: `noise_multiplier`, `clip_norm`, `clipped_fraction`, the derived
`(epsilon, delta, mu, steps)`, the adapter path and its `sha256` (`phase19_run._sha256`).

---

## 4. Where the pre-registered constants live — and how X/Y-vs-Z becomes structural

### The precedent to follow exactly

`scripts/erasure_gate.py` — phase-neutral, stdlib-only, no torch, no numpy; module-level literals;
verdict function; `if __name__ == "__main__"` self-check; committed at `23a830c` **before Phase 16
ran**; ancestry proved by `tests/test_phase16_prereg.py` using `git merge-base --is-ancestor`
against the *first-add commit* of every artifact it judges (never a committer date, which is
rewritable and non-monotonic after a rebase).

### The v4.0 subtlety, and the architecture that makes it visible

X (extraction ceiling) and Y (recall floor) are **outcome thresholds** — locked before any curve
point exists. Z (sweep width, step budget) is a **resource parameter** — set *from* a measured
M3 cost. A single file holding both invites exactly the misreading PROJECT.md warns about: a reader
sees a constant that was chosen after a measurement and concludes the thresholds were peeked at.

**Recommendation: two files, and let the import graph carry the distinction.**

```python
# NEW: scripts/mitigation_gate.py
#   Committed BEFORE the cost measurement, BEFORE any curve point.
#   stdlib only. Imports wilson_upper_bound from erasure_gate (never redefines it).
#   MUST NOT import mitigation_budget — enforced by an AST scan (see below).

OUTCOME_EXTRACTION_CEILING_X = ...   # the extraction rate a point must be at or below
OUTCOME_RECALL_FLOOR_Y       = ...   # the taught-recall rate a point must be at or above
OUTCOME_RELEARN_CEILING_X    = ...   # recovered recall ceiling for the relearning gate

def frontier_gate_passed(points) -> tuple[str, list[str]]:
    """EXISTENCE gate: is there >=1 point with extraction <= X AND recall >= Y?
    Returns (verdict, reasons) with verdict in VERDICTS. Bounds, never point estimates:
    extraction uses the one-sided 95% UPPER bound and recall the LOWER bound, both with
    QUESTIONS as the unit (erasure_gate's clustering rule, imported not restated)."""

def relearning_is_worth_attempting(frontier_points) -> tuple[bool, str]:
    """PRECONDITION, in the shape of erasure_is_worth_attempting: relearning is only
    meaningful against a point that actually cleared the frontier gate. If no point
    cleared, the relearning result is MOOT, not a pass."""

def relearning_gate_passed(*, recovered_successes, recovered_questions,
                           fresh_successes, fresh_questions, budget_steps) -> ...:
    """Binary gate on the ABSOLUTE recovery ceiling. The fresh-adapter comparison is
    DESCRIPTIVE and qualifies this reading — it is not a second gate (the v3.0
    'an instrument qualifies a gate, it does not replace it' pattern)."""
```

```python
# NEW: scripts/mitigation_budget.py
#   Committed AFTER the cost measurement, BEFORE the first curve point.
#   Every constant carries a _PROVENANCE sibling naming the artifact it was derived from.

BUDGET_SWEEP_POINTS_PER_ARM = ...
BUDGET_SWEEP_POINTS_PER_ARM_PROVENANCE = (
    "Derived from results/phase2X_cost.json (committed <sha>, <date>): measured "
    "<X> s/step at grad_accum_steps=n_facts on the M3, so N points x 200 steps x 2 arms "
    "fits <H> hours. This is a RESOURCE parameter, not an outcome threshold."
)
BUDGET_STEPS_PER_POINT = ...
BUDGET_STEPS_PER_POINT_PROVENANCE = "..."
BUDGET_RELEARN_STEPS_Z = ...
BUDGET_RELEARN_STEPS_Z_PROVENANCE = "..."
```

### The three mechanisms that make it a fact rather than a claim

| Mechanism | Test | What it forbids |
|-----------|------|-----------------|
| **Ancestry, outcome side** | `test_mitigation_gate_precedes_every_frontier_artifact` — `git merge-base --is-ancestor` from *every* commit touching `mitigation_gate.py` to the first-add of *every* `results/phase2X_*` file (the `test_phase16_prereg.py:406` pattern: every commit, not just the first) | Rewriting X or Y once a curve point is visible |
| **Ancestry, budget side** | `test_budget_follows_cost_and_precedes_every_curve_point` — the cost artifact's first-add is an ancestor of `mitigation_budget.py`'s first-add, which is an ancestor of every frontier point's first-add (the two-sided sandwich at `test_phase16_prereg.py:500`) | Setting Z after seeing a curve point — the *only* way Z can cheat |
| **Import isolation** | `test_gate_cannot_read_the_budget` — AST scan over `mitigation_gate.py` for any `Import`/`ImportFrom` naming `mitigation_budget`, plus a fresh-interpreter probe asserting `mitigation_budget` never lands in `sys.modules` after importing the gate (the `plot_phase15.py` no-checkpoint guard, applied here) | An outcome threshold silently defined in terms of the resource budget |

Also carry forward two existing disciplines:

- **`test_gate_does_not_redefine_shared_statistics`** — AST scan for `def wilson_upper_bound`,
  `def cluster_bootstrap`, `def sign_test_exact`, `def holm` in any new v4.0 file. The pattern is
  live at `tests/test_phase18_prereg.py:648-661`. Canonical homes: `wilson_upper_bound` →
  `scripts/erasure_gate.py:139`; `cluster_bootstrap` / `sign_test_exact` / `holm` →
  `scripts/phase16_persistence.py:843 / 1088 / 1170`.
- **No fact value in the pin, in any string, docstrings included** — the
  `phase19_erasure.py` rule. Key everything by slot.

### One more pre-registration the milestone needs and PROJECT.md does not yet name

The frontier existence gate can fail in two very different ways: *no point cleared* versus *the
sweep never reached the region where a point would clear*. Those are `FAILURE` and `INCONCLUSIVE`.
Pre-register the discriminator now, in `mitigation_gate.py`: e.g. "INCONCLUSIVE if the swept axis
never produced a point on both sides of X (or of Y) — the curve was truncated, and a truncated
curve cannot refute existence." This is the direct v4.0 analogue of `erasure_gate`'s
`zero_results_have_nll` clause, and it is exactly the failure mode a mis-set Z produces.

---

## 5. Data flow for the frontier artifact

### Flow

```
sweep point i
   │  train() + grad_privatizer  ──►  checkpoints/phase2X_p<i>_adapter.pt   (gitignored)
   │  attack scoring (phase18 corpus, held-out tier)  ──┐
   │  recall scoring (phase16 binding fixture)        ──┤
   │  masked_perplexity on/off (utility)              ──┤
   │  accountant.epsilon_at_delta(...)                ──┤
   ▼                                                    ▼
  _merge_point(FRONTIER_PATH, point_id, block)  ──► results/phase2X_frontier.json  [COMMITTED]
                                                          │
                    ┌─────────────────────────────────────┴────────────────────┐
                    ▼                                                          ▼
        scripts/plot_phase2X.py                                    verdict renderer
        (AST-guarded: no torch, no                       imports OUTCOME_* from mitigation_gate,
         checkpoint open, no adapter read)               calls frontier_gate_passed(points)
                    │                                                          │
                    ▼                                                          ▼
          assets/phase2X_frontier.png                        results/phase2X_frontier_report.md
```

**Extract once, plot only from the committed JSON.** Nothing downstream of the artifact may open
a checkpoint or an adapter. Enforce with the `plot_phase15.py` guard verbatim: AST walk over
imports plus a fresh-interpreter probe that fails if `torch` lands in `sys.modules`.

### Schema

Following `results/phase15_norms.json` (provenance header + data block) and
`results/phase18_arm_*.json` (`{arm, config, draw_record_keys, draws}` with counts, never rates):

```jsonc
{
  "schema_version": 1,
  "git_sha": "<sha of the driver that wrote the FIRST point>",
  "built": "2026-XX-XX",
  "gate_module_sha256": "<sha256 of scripts/mitigation_gate.py at write time>",
  "budget_module_sha256": "<sha256 of scripts/mitigation_budget.py at write time>",
  "corpus_sha256": "<phase18 attack corpus sha256 — the SAME input both arms dispatch>",
  "fixture_sha256": "<phase16 binding-fixture sha256 — the 270-question set>",
  "delta": 1e-5,
  "quantity_note": "extraction_successes / extraction_questions is the GATED held-out tier only; core_taught is the ATK-03 positive control and is reported tier-split, never merged (phase18_extraction.TIER_SPLIT_RATIONALE).",
  "unit_note": "Every denominator is a count of QUESTIONS. Draw counts are recorded separately and are never the unit of analysis (erasure_gate clustering rule).",
  "point_keys": ["point_id","arm","axis","axis_value","...ORDERED hard-equality schema tuple..."],

  "points": [
    {
      "point_id": "dp-eps-inf",              // the unmitigated CONTROL, as a sweep point
      "arm": "dp-sgd",                        // "dp-sgd" | "adversarial"
      "axis": "noise_multiplier",             // "noise_multiplier" | "attack_intensity"
      "axis_value": 0.0,

      "mechanism": {
        "clip_norm": null,                    // null encodes float("inf") in JSON
        "noise_multiplier": 0.0,
        "dp_unit": "fact",
        "n_facts": 8,
        "windows_per_fact": 4,
        "sampling_rate_q": 1.0,
        "adversarial_ratio": 0.0,
        "clipped_fraction": 0.0
      },

      "accounting": {                          // null on the adversarial arm — no formal claim
        "steps": 200, "mu": null, "epsilon": null, "delta": 1e-5,
        "accountant": "gdp-exact/full-batch-gaussian/no-subsampling",
        "note": "No subsampling amplification is claimed."
      },

      "train": {
        "seed": 1337, "lr": 3e-4, "weight_decay": 0.0,
        "batch_size": 4, "grad_accum_steps": 8, "max_steps": 200, "warmup_steps": 20,
        "block_size": 256, "grad_clip": null,
        "final_train_loss": 0.0,
        "base_fingerprint": {"git_sha": "...", "step": 0, "val_loss": 0.0},
        "driver_git_sha": "...", "device": "mps", "torch": "2.7.x",
        "adapter_path": "checkpoints/phase2X_p<i>_adapter.pt",
        "adapter_sha256": "...", "adapter_param_census": 331776
      },

      "privacy": {                             // the ATTACK read — held-out tier, gated
        "tier": "core_held_out",
        "questions": 104, "successes": 0, "draws": 42480,
        "per_family": {"A1-mild": {"questions": 0, "successes": 0}, "A1-aggressive": {},
                       "A2": {}, "A3": {}},
        "per_question_successes": [0]          // enables re-derivation of ANY bound downstream
      },
      "privacy_control_tier": {                // core_taught positive control, reported not gated
        "tier": "core_taught", "questions": 0, "successes": 0, "draws": 0
      },

      "utility": {                             // the RECALL read + the collateral read
        "recall_questions": 104, "recall_successes": 0, "recall_draws": 0,
        "recall_per_question_successes": [0],
        "masked_dialogue_ppl_on": 0.0,
        "masked_dialogue_ppl_off": 0.0,
        "scored_targets": 0
      }
    }
  ]
}
```

**Four schema rules that are load-bearing, not stylistic:**

1. **Counts, never rates.** `successes` + `questions` + `per_question_successes`, so any bound
   (`wilson_upper_bound`, `cluster_bootstrap`) is re-derivable from the artifact alone. A stored
   rate silently fixes the estimator.
2. **`point_keys` is ONE ordered tuple**, proved as a hard equality against every point on write —
   the `phase18_extraction.CORPUS_ENTRY_KEYS` discipline (`scripts/phase18_extraction.py:733`). An
   added, dropped, or reordered field goes red on the commit that writes it, not at report time
   after the sweep is paid for.
3. **`accounting` is `null` on the adversarial arm.** Nulling it is the structural statement that
   the adversarial arm makes no formal claim. An adversarial point carrying a plausible-looking
   epsilon is the single most likely way this milestone's headline gets misread.
4. **The gate/budget module sha256s travel in the artifact.** A report can then name the exact rule
   text it was judged under, rather than the rule the reader happens to have checked out.

---

## 6. The relearning harness

### What it reuses (all of it existing)

| Need | Existing API | Path |
|------|--------------|------|
| Read a mitigated adapter | `load_adapter(path, expected_fingerprint=...)` | `src/personacore/checkpoint.py:223` |
| Rebuild the injected model | `GPT(cfg)` → `load_state_dict` → `inject_lora` → `mark_only_lora_trainable` | `lora/inject.py:29,46` |
| Apply the mitigated weights | `load_adapter_weights(model, artifact)` — key + shape + **scale** audit | `lora/inject.py:76` |
| Continue training | `train(...)` unchanged (`grad_privatizer=None` — the attacker is not private) | `training/loop.py:172` |
| Export the recovered adapter | `export_adapter(...)` | `checkpoint.py:196` |
| Frozen-base canary | `snapshot_params` + the `torch.equal` loop | `lora/inject.py:58`, `teach_persona.py:689-698` |
| **Cost-to-recovery curve** | `extra_eval_fns={"recovered_recall": fn}` → one CSV column per eval event | `training/loop.py:262-271` |

The fresh never-taught arm is **the same code path minus one call**: skip `load_adapter_weights`.
`LoRALinear.__init__` sets `lora_B` to zeros (`lora/layer.py:30`), so a fresh adapter starts at
exact identity — a genuinely never-taught baseline by construction, not by assertion.

### What is new

1. `scripts/phase2X_relearn.py` — the driver (two arms, one spec).
2. A **relearning corpus**: what the attacker is allowed to show the model. This is a scope
   decision the roadmap must make explicitly, because it *is* the threat model. Candidates:
   the taught-template episodes for the target fact (strongest attacker), or held-out-family
   phrasings only (weaker, more realistic). Whichever is chosen, pre-register it — it is an
   outcome-shaping choice, not a resource one.
3. A recall probe cheap enough to run at every eval interval (see the caveat below).

### Enforcing "identical budget and seed protocol" structurally

Convention would be: "we used the same settings." That is exactly what this project converts into
a mechanism. Three layers, cheapest first:

**Layer 1 — one object, two arms.** The driver constructs **one** `TrainConfig` instance and passes
that same instance to both `train()` calls. A single object cannot diverge. This is the laziest
correct enforcement and it removes the whole class of "someone edited one arm's lr" bugs.

```python
spec = TrainConfig(lr=..., max_steps=budget.BUDGET_RELEARN_STEPS_Z, seed=..., ...)
mitigated = _relearn_arm("mitigated", spec, adapter=mitigated_adapter_path)
fresh     = _relearn_arm("fresh",     spec, adapter=None)
```

**Layer 2 — prove it from the written evidence, not from intent.** After both arms land, read the
two artifacts back off disk and assert equality of the recorded configs:

```python
if mitigated_record["train"] != fresh_record["train"] | {"arm", "adapter_path", "adapter_sha256"}:
    raise SystemExit("the two relearning arms differ in a recorded training setting — "
                     "the comparison would measure the recipe, not the mitigation")
```

This is `phase19_run.retrain_train`'s move exactly (`scripts/phase19_run.py:1613-1628`): it diffs
the two specs, names *which* member differs, and re-proves the delegated settings survived — rather
than asserting sameness in a comment.

**Layer 3 — a data-order proof.** Same seed alone does not guarantee the same data order if the
two arms consume RNG differently (the mitigated arm's `load_adapter_weights` consumes none, but
`GPT(cfg)`'s init draw differs in *use* between the arms). Record a `sha256` of the concatenated
window-index sequence each arm actually drew and assert equality. With the fact-aligned
deterministic draw of §2 this is trivially true, which is a second reason to prefer that data path.

### One honest caveat on the cost curve

Scoring recall requires generation, which is orders of magnitude slower than a training step. If
`extra_eval_fns` runs a full 104-question probe every eval interval, the eval dominates the run. Use
a small fixed probe subset (e.g. the target fact's questions only, greedy, k=1 draw) for the curve,
and score the **endpoint** with the full instrument. Then say so in the artifact: the curve is
DESCRIPTIVE at a reduced denominator; the gate reads the endpoint at the full one. That split is
already this project's house pattern ("gate only what the sample supports").

---

## 7. The adversarial arm — the seam that isn't needed

Extraction-aware training is a **data-mixture** change, not a gradient or loss change. Attack
intensity is the fraction of training episodes rendered through the Phase 18 attack transforms with
a non-committal target instead of the fact value.

- **Zero training-loop changes.** The mixture is built at bin-build time, exactly the shape
  `_prepend_replay` already has (`scripts/teach_persona.py:327`). New kwarg:
  `build_bins(..., adversarial_ratio=0.0)`, default reproduces v2.0 byte-for-byte.
- **Import the transforms; never fork them.** `apply_a1`, `build_a2_prompt`, `build_a3_prompt`
  (`scripts/phase18_extraction.py:474, 640, 545`) are read-only imports. `phase18_extraction.py` is
  **permanently uneditable** (ancestry-guarded, closed CLI surface) — but importing it as a library
  is established practice (`phase19_run.py:280`). A forked copy would let the attack trained against
  and the attack scored by drift apart silently, which would invalidate the arm.
- **The train/test attack split already exists.** Train the adversarial arm on the
  `REPORTED_TIER = "core_taught"` attacks; score on the `GATED_TIER = "core_held_out"`
  (`scripts/phase18_extraction.py:173-175`). This gives generalization-to-unseen-attacks a real
  measurement instead of a caveat — and PROJECT.md currently lists it as the declared open
  question. **Flag this to the roadmap: the existing tier split partially answers a question the
  milestone scope treats as unanswerable.** It answers unseen *questions* within known attack
  families; unseen *families* remain genuinely open.
- **Enforce no leakage structurally**: assert the adversarial training episode set and the scored
  corpus entries share zero `(fact_id, seed_index)` pairs, read from
  `results/phase18_corpus.json`. Token-id level, not prose.

---

## Anti-patterns

### AP-1: Putting DP-SGD behind `penalty_fn`

**What people do:** add an L2-ish term to the loss and call it privacy.
**Why it's wrong:** `penalty_fn` runs pre-backward; DP acts on gradients. A loss-side "DP" makes no
(ε, δ) claim at all, and the milestone's only formal claim evaporates.
**Instead:** the gradient-side `grad_privatizer` seam in §1.

### AP-2: `torch.func.vmap(grad(...))` or ghost-norm hooks for per-sample gradients

**What people do:** reach for the general per-sample-gradient machinery because that is what the
DP-SGD literature uses.
**Why it's wrong:** it functionalizes the whole GPT (MPS support uncertain, large diff, and it
imports a fair amount of PyTorch machinery into a from-scratch narrative). Both optimizations exist
to avoid materializing per-example gradients — which at 331,776 params × 8 examples = 10.6 MB is a
non-problem. Ghost norms are additionally ~30× *slower* at r=8 (see §1).
**Instead:** `grad_accum_steps = n_facts` over the existing loop, with the batch-1 autograd loop as
the oracle.

### AP-3: Example-level ε reported as if it protected facts

**What people do:** run standard DP-SGD over random windows, report ε, headline "the fact is
protected."
**Why it's wrong:** §2. The guarantee is over windows; a fact spans many windows; group privacy at
that multiplicity is vacuous. This would be a *false claim*, not a loose one — the worst possible
outcome for a milestone whose subject is a previously-falsified privacy claim.
**Instead:** fact-aligned windows, or a scoped "example-level" headline with the multiplicity
published.

### AP-4: A single pre-registration file holding both X/Y and Z

**What people do:** one `mitigation_gate.py` with all the constants.
**Why it's wrong:** Z is legitimately set after a measurement. In the same file as X and Y, that
makes the *whole file's* ancestry claim weaker than it needs to be, and a reader cannot tell by
inspection which constants were frozen and which were calibrated. PROJECT.md already anticipates
this misreading.
**Instead:** two files, an AST guard forbidding gate → budget imports, and two separate ancestry
tests (§4).

### AP-5: Comparing the ε=∞ control against a `grad_privatizer=None` run and calling the diff a bug

**What people do:** notice the two are not bit-identical and "fix" it.
**Why it's wrong:** fp addition is not associative; the buffer round-trip legitimately reorders
sums. Chasing bit-identity here would either weaken the privatizer or produce a false confidence.
**Instead:** the plain path's bit-identity is proven against `grad_privatizer=None` (§1); the
privatizer's correctness is proven against the batch-1 oracle with a stated tolerance. Two
different proofs for two different claims.

### AP-6: Forking `phase18_extraction.py` to add adversarial-training helpers

**What people do:** "just add a function to the attack module."
**Why it's wrong:** that file is a pre-registration whose CLI surface is explicitly closed and
whose every commit must remain an ancestor of every `results/phase18_*` artifact. A commit there
reddens the ancestry guard permanently, and per this project's own recorded experience a
delete-and-re-add cannot undo it.
**Instead:** import it read-only. New code goes in new v4.0 files.

### AP-7: Building step-level resume for a 40-second training unit

**What people do:** thread `resume_from` through the sweep driver because the pretraining phase
needed it.
**Why it's wrong:** the precedent's *reason* (a 50,000-step run) does not hold at 200 steps.
**Instead:** `--redo-point <id>` deletes the point's five artifacts and restarts it. Write down why.

---

## New vs Modified — the complete split

### NEW files

| Path | Purpose | CPU-testable without training? |
|------|---------|-------------------------------|
| `src/personacore/privacy/__init__.py` | package export surface | yes |
| `src/personacore/privacy/dpsgd.py` | `DPSGDPrivatizer` — clip + buffer + noise | **yes** (oracle test) |
| `src/personacore/privacy/accountant.py` | `mu_gdp` / `delta_at_epsilon` / `epsilon_at_delta` — pure stdlib | **yes** (published triples) |
| `scripts/mitigation_gate.py` | `OUTCOME_*` X/Y + verdict fns; imports `wilson_upper_bound` | **yes** (self-check + ancestry) |
| `scripts/mitigation_budget.py` | `BUDGET_*` Z + `_PROVENANCE` siblings | **yes** (provenance completeness) |
| `scripts/phase2X_frontier.py` | sweep driver: `cost \| sweep \| score \| report` | partially (stubbed train) |
| `scripts/phase2X_relearn.py` | relearning harness: mitigated + fresh arms | partially |
| `scripts/plot_phase2X.py` | figures from the committed JSON only; AST-guarded | **yes** (synthetic fixture) |
| `tests/test_dpsgd_oracle.py` | batch-1 autograd equivalence | **yes** |
| `tests/test_dp_accountant.py` | published-value oracle + T=1 analytic identity | **yes** |
| `tests/test_grad_privatizer_seam.py` | golden replay + in-process bit-identity | **yes** |
| `tests/test_mitigation_prereg.py` | 3 ancestry/import guards + no-redefinition AST scan | **yes** |
| `tests/test_phase2X_frontier_schema.py` | ordered `point_keys` hard equality, counts-not-rates | **yes** |
| `results/phase2X_cost.json` | the M3 cost measurement that sets Z | — |
| `results/phase2X_frontier.json` | the frontier artifact (§5) | — |
| `results/phase2X_relearn.json` | the two relearning arms | — |

### MODIFIED files

| Path | Change | Additive? | Default reproduces v2.0/v3.0? |
|------|--------|-----------|-------------------------------|
| `src/personacore/training/loop.py` | `_optimizer_step(..., grad_privatizer=None)` + one `if` in the accumulation loop; `train(..., grad_privatizer=None)` + 2 preamble guards | yes | **bit-for-bit** (golden replay + in-process identity) |
| `src/personacore/training/data.py` | **add** `get_batch_fact_aligned(...)` — a new function; no existing function touched | yes | trivially (nothing modified) |
| `scripts/teach_persona.py` | `build_bins(..., align_facts=None, adversarial_ratio=0.0)`; `train_arm` gains pass-throughs | yes | byte-for-byte when both default |
| `.planning/PROJECT.md`, `CLAUDE.md` | v4.0 structure notes | — | — |

### UNTOUCHED (and must stay so)

`lora/` · `continual/` · `dialogue/` · `generation/` · `model/` · `tokenizer/` · `checkpoint.py` ·
`config.py` · `seeding.py` · `provenance.py` · `preflight.py` · `logging.py` ·
`scripts/erasure_gate.py` · `scripts/phase16_persistence.py` · `scripts/phase17_*.py` ·
`scripts/phase18_extraction.py` · `scripts/phase19_erasure.py` — the last five are ancestry-guarded
pre-registrations; a commit to any of them reddens a guard permanently.

---

## Build order

The v2.0 lesson — front-load every unit-testable component so each expensive run stands on
already-pinned parts — plus a cost-measurement dependency that is unique to v4.0.

### Stage A — zero training, all CPU, all green before anything runs (Phase 20)

| # | Deliverable | Gated by | Why first |
|---|-------------|----------|-----------|
| A1 | `scripts/mitigation_gate.py` (X, Y, verdict fns, `relearning_is_worth_attempting`, the FAILURE-vs-INCONCLUSIVE discriminator) + its 3 prereg tests | nothing | **Must be committed before any measurement exists.** Everything else can be reordered; this cannot. |
| A2 | `privacy/accountant.py` + oracle test | nothing | Pure math. Its output (ε at a given σ, T) is what makes the sweep axis *choosable*, so it precedes sweep design. |
| A3 | `privacy/dpsgd.py` + batch-1 oracle test | A2 (for the σ semantics) | The from-scratch deliverable. Fully testable on a 3-parameter toy module in milliseconds. |
| A4 | Loop seam + bit-identity proof (golden replay + in-process) | A3 | The additive-seam contract. A red golden replay here means stop. |
| A5 | Fact-aligned bins + `get_batch_fact_aligned` + the no-window-spans-two-facts structural check | nothing | Determines whether the ε means anything (§2). If this proves infeasible the milestone's scope changes, so discover it now, not after a sweep. |
| A6 | Frontier schema + writer/reader + `_merge_point` + `plot_phase2X.py` against a **synthetic** fixture artifact | nothing | The plotting guard and the schema hard-equality can be fully green before a real point exists. |
| A7 | Sweep + relearn drivers with a **stubbed 3-step train**, exercising resume/refuse/redo | A6 | Proves the orchestration without paying for it. |
| A8 | Adversarial bins mixture + the zero-`(fact_id, seed_index)`-overlap check | nothing | Data-only; no loop change to validate. |

**Stage A gate:** full CPU suite green (845 + new), ruff clean, all three prereg guards green,
`mitigation_gate.py` pushed.

### Stage B — the one cheap measurement that sets Z (Phase 20 tail)

| # | Deliverable | Cost | Gated by |
|---|-------------|------|----------|
| B1 | `results/phase2X_cost.json` — M3 wall-clock: `grad_accum_steps=n_facts, batch_size=windows_per_fact` vs `grad_accum_steps=1, batch_size=n_facts×windows_per_fact` at matched token count, ~20 steps each, plus the privatizer's marginal overhead | minutes | A3, A4, A5 |
| B2 | `scripts/mitigation_budget.py` — `BUDGET_*` derived from B1, each with `_PROVENANCE` | minutes | B1 committed |

**Expect roughly 1–4×, not 8×.** Total token throughput is identical between the two
configurations; only kernel-launch parallelism differs, and the privatizer adds one norm + one
`normal_` over 1.33 MB per micro-batch. PROJECT.md's "~B×, the shape `estimate_fisher` already
exhibits at N=2000" is the *conservative* prior — `estimate_fisher` is B× because it runs
`batch_size=1` against a batch the loop would otherwise run at full width, which is exactly what
the fact-aligned design avoids. **Measure it; do not assume either number.**

**Stage B gate:** B1's first-add commit is an ancestor of B2's first-add (test), and B2's first-add
precedes every frontier point (test).

### Stage C — the sweep (Phase 21)

Order within the stage is dependency-driven and cost-ascending:

1. **The unmitigated control point first** (`clip_norm=inf, noise_multiplier=0`). It is the cheapest,
   it is the baseline the entire frontier is read against, and it validates the full
   train → score → merge pipeline end-to-end before any DP run burns time. **If its recall does not
   land in a defensible neighbourhood of v2.0's 0.4921 / 0.3483, stop** — the fact-aligned recipe
   changed something and every later point would be uninterpretable.
2. **DP arm sweep** over `noise_multiplier`, `BUDGET_SWEEP_POINTS_PER_ARM` points, one merge per
   point. Order the σ values so the extremes run first (largest and smallest): if the frontier is
   going to be empty, the extremes reveal it in two runs instead of N.
3. **Adversarial arm sweep** over `adversarial_ratio`. Independent of the DP arm; can run in either
   order, but it needs no new mechanism so it is lower-risk — a reasonable hedge to run second.
4. **Verdict + figures** from the committed JSON only.

**Stage C gate for the relearning phase:** `relearning_is_worth_attempting(points)` — imported from
the committed gate, called once, on measured numbers. If no point cleared the frontier, relearning
is MOOT (there is nothing whose durability is worth attacking) and the milestone ships that finding.
This is the exact shape of `erasure_is_worth_attempting(92, 104, 0, 104)` authoring Phase 19.

### Stage D — relearning (Phase 22)

1. Mitigated arm + fresh arm, one `TrainConfig` object, both at `BUDGET_RELEARN_STEPS_Z`.
2. Layer-2 evidence-diff and Layer-3 data-order proof (§6).
3. Endpoint scored at the full instrument; cost curve descriptive at the reduced probe.
4. `relearning_gate_passed(...)` called once. The fresh-adapter comparison qualifies the reading; it
   is not a second gate.

### What gates each expensive run — summary

| Expensive run | Cannot start until |
|---------------|--------------------|
| Cost measurement (B1) | A3 oracle green, A4 bit-identity green, A5 alignment check green |
| Any frontier point | B2 committed; A1 ancestry green; A6 schema green; A7 resume proven |
| DP points | control point landed and its recall is defensible |
| Relearning | `relearning_is_worth_attempting` returns True on measured frontier numbers |

---

## Open questions the roadmap must resolve (not resolvable by research)

1. **Is the fact-aligned layout feasible at the real corpus shape?** Needs the actual per-fact token
   counts. If one fact's episodes exceed a few `block_size` windows the padding waste grows, but the
   corpus is ~8,200 tokens total so this is very likely fine. **Verify in Stage A5, before anything
   depends on it.**
2. **What is the relearning corpus?** It is the threat model, and it is an outcome-shaping choice —
   pre-register it in `mitigation_gate.py`, not in the driver.
3. **Does the replay arm (`replay_ratio=1.0`) participate in the DP arm?** PersonaChat replay tokens
   are public data already in the base's training distribution and arguably need no privacy
   accounting, but they land in windows. Cleanest: the DP arm draws only from the fact-aligned
   region and replay is excluded. Needs a decision, and the decision changes the ε.
4. **`δ` value.** Conventionally `δ ≪ 1/n_records`. At n≈8 facts, any `δ` below ~1e-2 is already
   conservative; `1e-5` is the safe conventional choice. Lock it in `mitigation_gate.py` as an
   `OUTCOME_*`-adjacent constant — it is part of the claim, not part of the budget.
5. **How is a "success" defined for the recall probe on the DP arm?** Reuse the Phase 14/16 cell-blind
   scorer unchanged. If it needs any adaptation, that adaptation is an instrument change and must be
   validated against the existing arms before it scores a new one.

---

## Sources

- Live codebase read at `4554ef4` — `src/personacore/training/loop.py`, `training/data.py`,
  `training/loss.py`, `lora/{layer,inject,config}.py`, `continual/fisher.py`, `config.py`,
  `checkpoint.py`, `scripts/{erasure_gate,teach_persona,phase18_extraction,phase19_run,phase19_erasure}.py`,
  `tests/{test_loop_penalty_fn,test_phase16_prereg,test_phase18_prereg}.py`,
  `results/{phase15_norms,phase18_arm_adapter-on}.json` — **HIGH** (primary source, not inference)
- [Enabling Fast Gradient Clipping and Ghost Clipping in Opacus (PyTorch blog)](https://pytorch.org/blog/clipping-in-opacus/) — ghost clipping computes per-example gradient norms from activations and activation gradients for linear layers only; it is a memory optimization. **HIGH** (official PyTorch source). The r=8 arithmetic showing it is counterproductive here is my own derivation from that cost model — **MEDIUM**, and checkable by hand.
- [Privacy Enhanced PEFT: Tensor Train Decomposition under DP-SGD (arXiv 2601.10045)](https://arxiv.org/pdf/2601.10045) — ghost clipping extended to LoRA-family adapters; confirms the technique is adapter-applicable but structurally involved. **MEDIUM**
- [Gaussian DP for Reporting Differential Privacy Guarantees in ML (arXiv 2503.10945)](https://arxiv.org/html/2503.10945v2) and [Additive noise mechanisms (Wikipedia)](https://en.wikipedia.org/wiki/Additive_noise_mechanisms) — adaptive composition of Gaussian mechanisms is μ-GDP with `μ = sqrt(Σ(Δᵢ/σᵢ)²)`, i.e. `√T/σ` for T identical steps; the `δ(ε) = Φ(−ε/μ + μ/2) − e^ε·Φ(−ε/μ − μ/2)` dual is exact. **HIGH** (two independent sources agree)
- [Hyperparameter Tuning with Rényi Differential Privacy (arXiv 2110.03620)](https://arxiv.org/pdf/2110.03620) — the improved RDP→DP conversion `ε + log((α−1)/α) − (log δ + log α)/(α−1)` (Balle et al. 2020), recorded as the fallback if subsampling ever has to be introduced. **HIGH**
- `scripts/erasure_gate.py` module docstring — the equivalence problem, the clustering rule
  (questions as the unit), and the refusal to import unlearning-benchmark thresholds. Inherited
  wholesale by v4.0. **HIGH** (committed project source)

---
*Architecture research for: PersonaCore v4.0 leakage mitigation + relearning validation*
*Researched: 2026-08-20*
