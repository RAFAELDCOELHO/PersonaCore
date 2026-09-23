# Phase 22: DP-SGD Core, Accountant, and the Correctness Battery - Pattern Map

**Mapped:** 2026-08-25
**Resolved against:** HEAD = `ee423b4` (only `.planning/` docs changed since `a5f4ac1`, so every
`22-CONTEXT.md` / `22-RESEARCH.md` source anchor is testable against the same tree they were taken from)
**Files analyzed:** 11 new + 4 modified
**Analogs found:** 15 / 15 (11 exact, 4 role-match) — **no file in this phase lacks an analog**

Every excerpt below is copied verbatim from the tree. Seven stale anchors are reported in
[§ Stale Anchor Findings](#stale-anchor-findings) — **one of them lives inside a file this phase
must edit**.

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match |
|---|---|---|---|---|
| `src/personacore/privacy/__init__.py` | package init | — | `src/personacore/continual/__init__.py` | exact |
| `src/personacore/privacy/accountant.py` | numerical service (stdlib only) | transform (pure fn) | `src/personacore/evaluation/perplexity.py` | exact |
| `src/personacore/privacy/dpsgd.py` | mechanism / stateful service | transform, event-driven (per-step) | `src/personacore/lora/layer.py` + `src/personacore/lora/inject.py` | exact |
| `scripts/mitigation_accountant.py` | frozen pre-registration pin | constants + module-scope guards | `scripts/mitigation_unit.py` | **exact** (verbatim template) |
| `tests/test_phase22_accountant.py` | test (numeric) | request-response | `tests/test_phase15_plots.py` (V-09 half) | role-match |
| `tests/test_phase22_dpsgd_ast.py` | test (build-time AST) | static analysis | `tests/test_phase18_docs.py:639-681` + `tests/test_phase14_scoring.py:466-516` | **exact** |
| `tests/test_phase22_dpsgd.py` | test (runtime differential + golden) | request-response | `tests/test_loop_penalty_fn.py` + `tests/test_phase21_replay_volume.py:221-245` | exact |
| `tests/test_phase22_checkpoint.py` | test (round-trip / back-compat) | file-I/O | `tests/test_resume_curve.py` shape via `checkpoint.py:135` back-compat idiom | role-match |
| `tests/test_phase22_fakes.py` | test (positive control, RED→GREEN) | mutation probe | `tests/test_phase20_prereg.py:657-810` | role-match (see gap note) |
| `tests/test_phase22_wiring.py` | test (end-to-end CPU) | request-response | `tests/test_loop_penalty_fn.py::_run_recipe` | exact |
| `src/personacore/training/loop.py` (MOD) | training orchestration | event-driven | **self-analog** — the `replay_*` seam already in this file | exact |
| `src/personacore/checkpoint.py` (MOD) | persistence | file-I/O | **self-analog** — the `cuda` rng slot + `**extra` | exact |
| `scripts/teach_persona.py` (MOD) | production driver | batch | **self-analog** — `:1167`'s `train()` call | exact |
| `tests/test_phase20_prereg.py` (MOD) | test (ancestry guard) | static + git | **self-analog** — the Phase-21 pair at `:130` and `:257-289` | exact |

---

## Pattern Assignments

### 1. `src/personacore/training/loop.py` — the two additive seams (D-01/D-02/D-03, D-08)

**Analog:** itself. `replay_fn` / `penalty_fn` are the exact playbook; copy their shape, not a
paraphrase.

#### 1a. VERBATIM CURRENT TEXT — `_optimizer_step`, `loop.py:136-185`

This is the surgical target. Every `<action>` block must be written against these exact lines.

```python
def _optimizer_step(
    model,
    optimizer,
    scheduler,
    scaler,
    train_cfg,
    runtime,
    batch_fn,
    penalty_fn=None,
    replay_fn=None,
):
    """Run ONE optimizer step with the load-bearing AMP+accum+clip ordering (TRAIN-02).

    ``batch_fn(micro)`` yields ``(xb, yb)`` for each micro-batch. Order is mandatory:
    scale->backward × grad_accum_steps -> unscale_ (once) -> clip -> step -> update -> scheduler.
    Returns the (unscaled, accumulation-corrected) training loss for the step.

    ``penalty_fn`` (the M2 EWC seam, EWC-02) is evaluated per micro-batch and joins
    ``base_loss`` via ``assemble_loss`` BEFORE the ``/accum`` divide — params are constant
    across the accumulation window, so the divided contributions sum to exactly ONE full
    penalty per optimizer step (Pitfall 5). ``None`` keeps the M1 identity bit-for-bit.

    ``replay_fn`` (the Phase-21 replay seam, D-10/D-25) runs ONCE per optimizer step, AFTER the
    per-micro-step accumulation loop and BEFORE ``unscale_``, accumulating into the same
    gradient buffer. It is structurally OUTSIDE the per-record loop above — see :func:`train`
    for what that placement does and does not claim. ``None`` is bit-for-bit inert: no new line
    executes on the default path.
    """
    optimizer.zero_grad(set_to_none=True)
    accum = max(1, train_cfg.grad_accum_steps)
    # Sum the per-micro-batch loss BEFORE the /accum scaling, then average -> the loss for the
    # effective (big) batch. This is what makes grad_accum_steps=N match one N×-bigger batch.
    summed = 0.0
    for micro in range(accum):
        xb, yb = batch_fn(micro)
        with runtime.autocast():  # RuntimeConfig.autocast() — single AMP source (no torch.cuda.*)
            _, base_loss = model(xb, yb)
            penalties = (penalty_fn(model),) if penalty_fn is not None else ()
            total = assemble_loss(base_loss, penalties)  # identity when no penalty (D-04)
            loss = total / accum  # scale so accumulated grads average across micro-batches
        scaler.scale(loss).backward()
        summed += float(base_loss.item())
    if replay_fn is not None:
        replay_fn(model, scaler)  # D-25: its OWN pass per lot, outside the per-record loop
    scaler.unscale_(optimizer)  # UNSCALE before clip (mandatory order — Pitfall 1)
    torch.nn.utils.clip_grad_norm_(model.parameters(), train_cfg.grad_clip)
    scaler.step(optimizer)
    scaler.update()
    scheduler.step()  # ONCE per optimizer step, never per micro-batch (Pitfall 2)
    return summed / accum
```

**Exact line map for the plan:**

| line | current text | Phase-22 obligation |
|---|---|---|
| `:136-146` | signature, 3 positional-after-`batch_fn` params (`penalty_fn`, `replay_fn`) | `dp_fn=None` appends here, same style (**plain default-None, NOT keyword-only** — this function's existing kwargs are positional-or-keyword and `train()` passes them positionally at `:510-519`) |
| `:164` | `optimizer.zero_grad(set_to_none=True)` | the SINGLE zero. D-01's per-micro-step drain lives **inside the DP branch**, never here |
| `:165` | `accum = max(1, train_cfg.grad_accum_steps)` | **the line ROADMAP SC4 + `REQUIREMENTS.md:135` misattribute as the clip** |
| `:169` | `for micro in range(accum):` | the per-record loop the drain + clip + accumulate hook into |
| `:175` | `loss = total / accum` | the divide D-02 **bypasses** on the DP path (`sum → noise → divide`) |
| `:176` | `scaler.scale(loss).backward()` | after this, `.grad` holds record *i* — read/clip/accumulate/drain here |
| `:178-179` | `if replay_fn is not None: replay_fn(model, scaler)` | runs **after** the private loop; `.grad` then holds the public term exactly (D-01) |
| `:181` | `torch.nn.utils.clip_grad_norm_(model.parameters(), train_cfg.grad_clip)` | **THE ACTUAL CLIP SITE** — must become structurally unreachable inside `if dp_fn is None:` (D-03) |
| `:182` | `scaler.step(optimizer)` | nothing between the noise write and this (D-03's surviving rule) |

**How `_optimizer_step` is invoked — `loop.py:510-519` (positional!):**

```python
            train_loss = _optimizer_step(
                model,
                optimizer,
                scheduler,
                scaler,
                train_config,
                runtime,
                batch_fn,
                penalty_fn,
                replay_fn,
```
A new `dp_fn` must be appended to **both** the def and this call, in the same order.

#### 1b. VERBATIM CURRENT TEXT — `train()`'s keyword-only signature, `loop.py:188-220`

```python
def train(
    *,
    train_config,
    runtime_config=None,
    model=None,
    model_config=None,
    corpus_path=None,
    train_bin=None,
    val_bin=None,
    train_mask_bin=None,
    val_mask_bin=None,
    replay_bin=None,
    replay_mask_bin=None,
    replay_windows=None,
    eos_id=8184,
    fixed_batch=None,
    scaler=None,
    resume_from=None,
    checkpoint_path=None,
    best_checkpoint_path=None,
    log_path=None,
    max_steps_override=None,
    eval_interval=1,
    checkpoint_interval=None,
    sample_interval=None,
    sample_prompt=None,
    tokenizer=None,
    sample_max_new_tokens=64,
    penalty_fn=None,
    checkpoint_extra=None,
    extra_eval_fns=None,
    return_final_loss=False,
):
```

`fact_bin=` and `dp_fn=` append here (`*` at `:189` makes everything keyword-only already — D-08's
"keyword-only, no default" applies to `dp_fn`'s *constructor*, not to `train()`'s `dp_fn=None`,
which must stay `None`-defaulted for DPSGD-02).

#### 1c. Multi-kwarg all-or-none refusal — copy from `loop.py:348-370`

The `fact_bin=` seam needs the same all-or-none / type refusal shape (D-08's "refusal on
disagreement" between `grad_accum_steps` and `len(align_facts)`):

```python
    _replay = {
        "replay_bin": replay_bin,
        "replay_mask_bin": replay_mask_bin,
        "replay_windows": replay_windows,
    }
    _missing = sorted(name for name, value in _replay.items() if value is None)
    if _missing and len(_missing) != len(_replay):
        raise ValueError(
            f"the Phase-21 replay seam needs all three of {sorted(_replay)} or none of them — "
            f"missing {_missing}. The token and mask .bin are element-aligned, and "
            "replay_windows is the PUBLIC per-step budget (D-11/D-24: "
            "REPLAY_WINDOWS_PER_FACT * n_facts); this loop never derives it from the data, so "
            "it cannot be defaulted."
        )
```

Note the register: the message names the decision id, the reason, and why the value **cannot be
defaulted**. `loop.py:336-347` (`train_mask_bin requires train_bin`) is the two-kwarg variant.

#### 1d. The `batch_fn` dispatch to extend — `loop.py:402-452`

`fact_bin=` adds a branch here. Nearest sibling (the mask branch, `loop.py:416-426`):

```python
        if train_mask_bin is not None:
            # Phase-12 mask seam: identical draw, but user-turn targets carry -100 so the
            # CE scores assistant tokens only (TUNE-01; -100 semantics live in data.py).
            def batch_fn(_micro):
                return get_batch_memmap_masked(
                    train_bin,
                    train_mask_bin,
                    train_config.batch_size,
                    model_cfg.block_size,
                    runtime.device,
                )
```

**Two shape mismatches the plan must handle explicitly** (measured, not inferred):
1. every existing `batch_fn` ignores its `micro` argument except the synthetic branch
   (`loop.py:450-452`); `get_batch_fact_aligned` needs `step=` **and** `n_facts=`, and the
   *absolute step counter* is not in `batch_fn`'s closure — it lives at `loop.py:507` (`step =
   start_step`) and advances at the `while` loop. The closure must capture something mutable, or
   `batch_fn(micro)` must be re-interpreted.
2. `get_batch_fact_aligned` returns **three** values — `(x, y, fact_index)`
   (`data.py:285-290`) — while `_optimizer_step:170` does `xb, yb = batch_fn(micro)`.

**Signature to route to** — `src/personacore/training/data.py:285`:
```python
def get_batch_fact_aligned(bin_path, mask_path, fact_path, block_size, device, *, step, n_facts):
```

#### 1e. The seam-inertness docstring register — `loop.py:252-291`

`replay_bin`'s Args entry is the model for `dp_fn=`/`fact_bin=`: it states **What this seam DOES
claim**, **What it does NOT claim**, and the rejected alternatives. `:275-279` is the sentence
Phase 22 discharges:

```
            **What it does NOT claim.** Phase 21 delivers the STRUCTURAL SEPARATION ONLY. The
            ``clip_grad_norm_`` call in :func:`_optimizer_step` still clips the AVERAGED
            gradient, replay included. Per-record clipping and a genuinely un-clipped replay
            term are DPSGD-01/DPSGD-04, Phase 22. Do not read an un-clipped public-gradient
            guarantee into this seam; it is not delivered here.
```

#### 1f. `replay_fn` — reused UNCHANGED (`loop.py:454-473`), and why `.grad` is shared

```python
    # --- Phase-21 replay seam (D-10/D-25): its OWN pass per lot, outside the per-record loop ---
    replay_fn = None
    if replay_windows is not None:

        def replay_fn(model, scaler):
            drawn = 0
            while drawn < replay_windows:
                # Ceil division by iteration: the last micro-batch is the ragged remainder, so
                # the total drawn is EXACTLY replay_windows and never a rounded-up overdraw.
                micro = min(train_config.batch_size, replay_windows - drawn)
                xb, yb = get_batch_memmap_masked(
                    replay_bin, replay_mask_bin, micro, model_cfg.block_size, runtime.device
                )
                with runtime.autocast():
                    _, replay_loss = model(xb, yb)
                    # Weight by ACTUAL windows / total, so the ragged tail is not over-weighted
                    # and the pass contributes exactly ONE full replay mean per optimizer step.
                    loss = replay_loss * (micro / replay_windows)
                scaler.scale(loss).backward()
                drawn += micro
```

`:472`'s `scaler.scale(loss).backward()` is the line that makes the replay term land in the same
`.grad` buffers — CONTEXT's measured 67.1% mixing. D-01 keeps this function byte-unchanged.

---

### 2. `src/personacore/privacy/dpsgd.py` (mechanism, torch)

**Analog:** `src/personacore/lora/layer.py` — construct-once single-source constant + `raise`-never-`assert`.

**The single-source-of-truth capture (D-17), `layer.py:24-36`:**

```python
    def __init__(self, base: nn.Linear, r: int, alpha: float, dropout: float = 0.0):
        super().__init__()
        self.base = base  # the frozen original nn.Linear (composition, not inheritance).
        self.scale = alpha / r  # SINGLE source of truth — forward AND merge read this (P3).
```

`self.C` / `self.sigma` / `self._g` follow this line exactly: computed once in `__init__`, read by
every consumer, with the "SINGLE source of truth" comment carrying the reason. `merged_state_dict`
even annotates the read site (`inject.py:282`: `delta = m.scale * (m.lora_B @ m.lora_A)  # reads
self.scale (P3).`) — the same annotation belongs on `dpsgd.py`'s noise line.

**The `raise`-not-`assert` rule and its recorded reason, `layer.py:44-61`:**

```python
    @torch.no_grad()
    def merge(self):
        """Fold the adapter delta into ``base.weight`` in place (LORA-04 / D-08 in-place form).
        ...
        Corruption guards here raise ``RuntimeError`` (never ``assert``): an ``assert`` is
        stripped under ``python -O``, which would turn this loud refusal into silent
        double-folded weights (Pitfall 6).
        """
        if self.merged:
            raise RuntimeError("double merge would fold the delta twice — unmerge first.")
```

`eject_adapter` restates it at the call site (`inject.py:194`):
`Refuses (``RuntimeError``, never a ``-O``-strippable ``assert``) unless each child is unmerged first`.

> **Anchor correction:** CONTEXT cites `layer.py:45-58` for this docstring. The docstring is
> `:46-56`; the `python -O` sentence is `:53-55`; `:57-58` is already the `if self.merged: raise`
> body. Use **`layer.py:53-55`** to cite the reason and **`:57-58`** for the refusal shape.

**Pre-pass-then-act refusal (D-04's three property refusals) — `inject.py:145-153`:**

```python
    wrapped = [m for m in model.modules() if isinstance(m, LoRALinear)]
    for m in wrapped:
        if m.merged:
            raise RuntimeError(
                "set_adapter_enabled on a merged module — the delta is folded into "
                "base.weight, so the flag would have no effect; unmerge_lora first."
            )
    for m in wrapped:
        m.enabled = enabled
```

Two loops, deliberately: *"The check is a pre-pass over every module, so a refusal flips no flag at
all."* D-04's `requires_grad` audit must be a full pre-pass before any DP state is constructed —
partial construction on refusal is the failure this idiom exists to prevent.

**The exact census D-04 lifts to the seam — `scripts/teach_persona.py:1141-1156`:**

```python
    n_wrapped = inject_lora(model, LORA_CFG)
    if n_wrapped != 6 * n_layer:
        raise SystemExit(
            f"[teach_persona] inject_lora wrapped {n_wrapped} projections, expected "
            f"6 * n_layer = {6 * n_layer}"
        )
    mark_only_lora_trainable(model)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    # Closed-form census: 18 * r * n_embd per layer across the six projections (== 331,776 at
    # the production shape r=8 / 6L / 384d).
    expected_trainable = LORA_CFG.r * n_layer * 18 * n_embd
    if trainable != expected_trainable:
        raise SystemExit(
            f"[teach_persona] trainable census {trainable} != r*n_layer*18*n_embd = "
            f"{expected_trainable}"
        )
```

At the seam this becomes `raise RuntimeError` (D-15: `SystemExit` is the `scripts/` register;
`src/` raises `RuntimeError`/`ValueError`). `n_layer`/`n_embd` come from `blob["model_config"]`
at the caller (`:1139-1140`) — at the seam they must be derived from the live model or passed in.

**The trap D-04 refuses, in code — `inject.py:29-55`** (`inject_lora` returns and does **not**
freeze; `mark_only_lora_trainable` is a separate call):

```python
def inject_lora(model: nn.Module, cfg: LoRAConfig) -> int:
    ...
    n = 0
    for parent in model.modules():
        for name in cfg.targets:  # explicit allowlist — NEVER an isinstance scan (P1).
            child = getattr(parent, name, None)
            if isinstance(child, nn.Linear):
                setattr(parent, name, LoRALinear(child, cfg.r, cfg.alpha, cfg.dropout))
                n += 1
    return n


def mark_only_lora_trainable(model: nn.Module) -> None:
    """Freeze everything, then re-enable exactly the LoRA A/B parameters (LORA-02).

    Name-suffix traversal (the ``gpt.py`` residual-scaled-init idiom): trainable census after
    this call equals ``r * n_layer * 18 * n_embd`` (closed form verified in 09-RESEARCH.md).
    """
    model.requires_grad_(False)
    for name, p in model.named_parameters():
        if "lora_" in name:
            p.requires_grad_(True)
```

`"lora_" in name` at `:54` is the exact predicate D-04's `requires_grad` audit must invert
("raise if any non-`lora_` parameter has `requires_grad`"). Also `lora_state_dict`
(`inject.py:73`) uses the same substring test — reuse it, do not re-invent a name rule.

**The scaler refusal (D-04 trap 2) reads `RuntimeConfig`, `config.py:55-65`:**

```python
    def __post_init__(self) -> None:
        if self.device in ("cpu", "mps"):
            # AMP is meaningless/unsupported on CPU; on MPS we hold fp32 only (D-02 — no
            # fp16 AMP on Apple Silicon). Both mirror the same fp32 posture: silently disable.
            self.amp = False
```

The seam refuses on `scaler.is_enabled()` (or `runtime.amp`), which is unreachable on cpu/mps by
this block — hence "the P100 fallback needs a refusal, not a silent wrong clip".

---

### 3. `src/personacore/privacy/accountant.py` (stdlib `math` only)

**Analog:** `src/personacore/evaluation/perplexity.py` — the `src/` module that is a portfolio
numerical deliverable, which is the visibility precedent D-10 invokes.

**Module docstring register — `perplexity.py:1-27`:**

```python
"""Deterministic full-corpus perplexity (EVAL-01).

The single canonical headline number (and every EVAL-03 ablation-cohort PPL cell)
flows through ``perplexity()``. Unlike ``training.loop.estimate_loss`` (20 random
batches -> a non-deterministic mean-of-means), this sweeps the WHOLE corpus once in
NON-OVERLAPPING ``block_size`` windows, sums cross-entropy over every predicted
token with ``reduction="sum"``, and exponentiates the grand total over the EXACT
auditable token count (D-01..D-03).

Accounting invariants (pinned by ``tests/test_perplexity.py``):
  - A length-L window predicts L-1 transitions: token 0 is context-only, never
    scored. So the denominator is ``corpus_len - n_windows`` (each scored window
    loses its first token as unpredictable).
  ...
  - ``reduction="sum"`` is MANDATORY — ``GPT.forward(targets=)`` returns a per-window
    MEAN loss (``gpt.py:203``); averaging per-window means would mis-weight the short
    final window. The model's returned loss is ignored entirely here.
"""

import math
```

Copy this shape exactly: **requirement id in line 1**, a "unlike X, this does Y" contrast, then a
bulleted **invariants block naming the test file that pins it**. `accountant.py`'s invariants block
is where F4's `sigma` = noise multiplier statement lives (cite `mitigation_gate.py:1026`) and where
D-18's `NEIGHBOURING` relation is documented — that docstring text is one of the two sites the
cross-site consistency test reads.

**Signature + returns-with-its-denominator style, `perplexity.py:32-53`:**

```python
@torch.no_grad()
def perplexity(model, val_bin_path, block_size, device, batch_size=32, forbid_ids=None):
    """Deterministic full-corpus PPL over non-overlapping ``block_size`` windows.

    Args:
        model: a ``GPT`` whose ``forward(idx)`` returns ``(logits, loss)``.
        ...
    Returns:
        ``(ppl, total_tokens)`` where ``ppl = exp(total_CE / total_tokens)`` and
        ``total_tokens`` is the exact denominator (D-03) so the number is auditable.
    """
```

**The refusal-on-degenerate-result idiom, `perplexity.py:74-75`:**

```python
    if total_tokens == 0:
        raise ValueError(
```
This is the direct precedent for RESEARCH F1/D-13's *condition 3* (`delta <= 0.0` → refuse, never
return). Same shape, same module family.

**`src/personacore/privacy/__init__.py` — copy `continual/__init__.py` verbatim in form:**

```python
"""Phase 10 — from-scratch EWC core (EWC-01..02): public import surface.

Plan 10-01 ships ``estimate_fisher`` (per-example empirical diagonal Fisher with
mean-normalization and half-split convergence stats, EWC-01 / D-01..D-05) and ``EWCPenalty``
(the Kirkpatrick quadratic anchor ``(lam/2) * sum(F * (theta - theta_star)**2)``, EWC-02 —
exactly 0.0 at the anchor, fed into the training loop via the ``assemble_loss`` seam).
"""

from .ewc import EWCPenalty
from .fisher import estimate_fisher

__all__ = ["EWCPenalty", "estimate_fisher"]
```

**Caution for V-09:** the AST import-walk asserts `accountant.py`'s imports `== {"math"}`. A
`privacy/__init__.py` that re-exports from `accountant` adds a **relative** `ImportFrom`
(`node.module == "accountant"`, `node.level == 1`) to the *package*, not to `accountant.py` — the
guard scopes to the one module, so this is safe, but the plan should say so explicitly.

---

### 4. `scripts/mitigation_accountant.py` (FROZEN pin, zero imports)

**Analog:** `scripts/mitigation_unit.py` — **verbatim template**, all 252 lines. Sections to mirror:

| `mitigation_unit.py` | `mitigation_accountant.py` |
|---|---|
| `:1-67` module docstring: subject, "closed at the first artifact", "why this module imports nothing", "what is deliberately absent" | same four headings, `results/phase23_*` as the closing trigger |
| `:70-79` local `_prove` | copy **verbatim** (name in brackets changes) |
| `:85` `PRIVACY_UNIT = "one taught fact"` | `NEIGHBOURING = "add/remove one fact"` (D-18) |
| `:131` `SAMPLING_RATE_Q = 1.0` | `SENSITIVITY_MULTIPLIER = 1.0` (D-18) |
| `:171` `DELTA = 1e-5` | `GOLDEN_EPSILON` table (outputs only) |
| `:179` `REJECTED_DELTA_RECIPE = "1/N**1.1"` + `:193-207` `REJECTED_DELTA_REASON` | `REJECTED_FORM` + its reason prose |
| `:210-252` module-scope `_prove` guards | the `T ** 0.5` composition proof (operator, no import) |

**The `_prove` helper, `mitigation_unit.py:70-79` — copy this, do not import it:**

```python
def _prove(condition, message):
    """``SystemExit`` on a broken invariant — ``scripts/mitigation_gate.py:66``'s register.

    ``SystemExit`` and deliberately NOT ``assert``: an ``assert`` is strippable under ``-O``, and a
    proof that disappears under an optimisation flag is not a proof. The message carries this
    module's own name in brackets — an abort naming the wrong module sends its reader to the wrong
    file.
    """
    if not condition:
        raise SystemExit(f"[mitigation_unit] {message}")
```

**Why it is copied and not imported — `mitigation_unit.py:38-47`:**

```
WHY ``_prove`` IS DEFINED HERE RATHER THAN IMPORTED FROM ``mitigation_gate``
---------------------------------------------------------------------------
``scripts/mitigation_gate.py:66`` already defines this exact three-line helper, and this project's
standing discipline is "import the instrument, never copy it". That discipline is OVERRIDDEN here
by the ceiling above, not forgotten: importing a sibling would add ``mitigation_gate`` to the
accumulated ``imported`` set and turn ``tests/test_phase20_prereg.py:523`` RED.
```
(That `:523` anchor is itself stale — the live assertion is `:916`. See findings.)

**Module-scope guards, `mitigation_unit.py:210-225`** — placement reason is load-bearing:

```python
# ---------------------------------------------------------------------------------------------
# THE GUARDS. Module scope, so a wrong edit fails at IMPORT rather than inside a consumer that
# has already spent compute — the same placement reason as `mitigation_gate.py:141` and `:175`.
# ---------------------------------------------------------------------------------------------
_prove(
    DELTA * 8 < DELTA_TIMES_N_CEILING,
    f"delta * 8 = {DELTA * 8} against the ceiling {DELTA_TIMES_N_CEILING}. The pinned literal "
    f"{DELTA} clears it by {DELTA_TIMES_N_CEILING / (DELTA * 8)}x at the n = 8 arm; a delta that "
    "does not is a delta whose guarantee is dominated by its own failure probability",
)
```

Note `f"...{DELTA_TIMES_N_CEILING / (DELTA * 8)}x"` — arithmetic **inside the message**, so the
margin is computed rather than transcribed. The `T ** 0.5` composition proof follows this: an
operator expression inside a `_prove` message, no import.

**The rejected-alternative-kept-runnable idiom, `mitigation_unit.py:179-190`:**

```python
REJECTED_DELTA_RECIPE = "1/N**1.1"


def rejected_delta(n):
    """The REJECTED recipe, kept runnable so its self-contradiction is checkable, not quoted.

    Deliberately shipped as executable code rather than as a number in prose: a rejected
    alternative recorded only as prose is a claim, while one recorded as a function is a claim
    anyone can re-run at any N. ``n ** -1.1`` is an operator, so this needs no import — which is
    what lets the rejection live inside D-22's ceiling at all.
    """
    return n**-1.1
```

**⚠ CONFLICT the planner must resolve, not inherit.** `mitigation_unit.py` makes the rejected
recipe **executable** (`rejected_delta`, and `_prove` at `:231-244` asserts it fails). D-09 forbids
`REJECTED_FORM` from "transcribing its logic", and `sqrt(2*ln(1.25/δ))/σ` needs `log` — unreachable
under the zero-import ceiling anyway. So `REJECTED_FORM` is a **string constant + prose reason**
(the `REJECTED_DELTA_REASON` half at `:193-207`), with **no** `rejected_epsilon()` function. Say
this explicitly in the plan so a task does not copy the executable half by pattern-matching.

---

### 5. `tests/test_phase22_dpsgd_ast.py` (V-11, and V-09/V-10's static halves)

Three distinct AST shapes already exist. Pick per guard.

#### 5a. Import-walk (V-09: `accountant.py` imports `math` only) — `tests/test_phase15_plots.py:312-327`

```python
    tree = ast.parse(PLOT_SCRIPT.read_text(encoding="utf-8"))

    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    # Meta-guard first (the tests/test_phase14_scoring.py:441 habit): a walk that silently
    # stopped working would otherwise pass this test by finding nothing at all.
    assert imported, "the AST import walk found no imports — the walk stopped working"
    assert "torch" not in imported, f"plot_phase15 imports torch — D-07 violated ({imported})"
```

Same test also carries the **out-of-process transitive check** (`:338-352`), which catches an
import through a helper the single-file walk cannot see:

```python
    probe = (
        "import importlib.util, sys;"
        "spec = importlib.util.spec_from_file_location('p15', 'scripts/plot_phase15.py');"
        "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m);"
        "sys.exit(1 if 'torch' in sys.modules else 0)"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"plotting module transitively imports torch — D-07 violated\n{result.stderr}"
    )
```
V-09 should carry both halves (`accountant.py` must not reach `torch` transitively either).

#### 5b. Accumulating import ceiling (V-10) — `tests/test_phase20_prereg.py:888-923`

This is the block `mitigation_accountant.py` must not break, and V-10 extends it:

```python
    imported = set()
    from_erasure_gate = set()
    defined = set()
    for module in _GATE_MODULES:
        tree = _tree(module)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                # The FLAT module name, matching `tests/test_phase16_stats.py:396`'s expectation
                # and the gate's own `sys.path`-bootstrapped `from erasure_gate import ...`.
                imported.add((node.module or "").split(".")[0])
                if node.module == "erasure_gate":
                    from_erasure_gate.update(alias.name for alias in node.names)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defined.add(node.name)
    ...
    allowed = {"pathlib", "sys", "erasure_gate"}
    assert imported <= allowed, (
        f"the mitigation modules import {sorted(imported - allowed)} beyond the allow-set "
        f"{sorted(allowed)}. This is asserted as a SUBSET rather than as a list of forbidden "
        "names deliberately: a forbidden-name list only catches the import someone thought to "
        "forbid, while a subset assertion catches the one nobody anticipated. ..."
    )
```

`_GATE_MODULES` is a live glob (`:72`): `mitigation_accountant.py` **joins it automatically** the
moment the file exists. `imported` is a **union across all modules**, so a single `import math`
anywhere in `scripts/mitigation_*.py` turns `:916` RED — this is D-10's forcing mechanism, and it
is already armed. `_tree` helper at `:844-845`:

```python
def _tree(path):
    return ast.parse(path.read_text(encoding="utf-8"))
```

The collapsed-glob meta-guard, `:838-841`:

```python
    assert len(_GATE_MODULES) >= 1, (
        f"the mitigation_*.py glob collapsed to {len(_GATE_MODULES)} file(s) — a broken glob makes "
        "every static guard in this module green while scanning no source at all"
    )
```

#### 5c. Transitive call-graph closure (V-11 — the D-05 axis-1 shape) — `tests/test_phase18_docs.py:650-681`

**This is the single most reusable thing in the repo for this phase.** Verbatim:

```python
    extraction_tree = ast.parse(_EXTRACTION_PATH.read_text(encoding="utf-8"))
    functions = {
        node.name: node
        for node in ast.walk(extraction_tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "render_report" in functions, "render_report is gone — this guard would check nothing"

    seen, frontier, imports = set(), ["render_report"], {}
    while frontier:
        name = frontier.pop()
        if name in seen or name not in functions:
            continue
        seen.add(name)
        for node in ast.walk(functions[name]):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                frontier.append(node.func.id)
            elif isinstance(node, ast.Import):
                imports.setdefault(name, []).extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.setdefault(name, []).append(node.module)

    assert len(seen) > 1, f"the closure over render_report found only {seen} — the walk broke"
    forbidden = {"phase14_factset", "phase17_persona_facts"}
    offenders = {name: sorted(forbidden.intersection(modules)) for name, modules in imports.items()}
    offenders = {name: hit for name, hit in offenders.items() if hit}
    assert offenders == {}, (
        f"functions reachable from render_report import fact-set modules: {offenders}. ..."
    )
```

Its docstring states the property V-11 needs word-for-word (`test_phase18_docs.py:640-648`):
*"Read off the AST as a transitive closure over the driver's own call graph, because the property
is about what the render path CAN reach and not about what today's body happens to call."*

**V-11's adaptation:** frontier-seed = the DP step method; collect `ast.Call`s and
`ast.Attribute`/`ast.Assign` targets instead of imports; forbidden set = `{"backward",
"clip_grad_norm_", "normalize", "manual_seed", "seed"}` plus `.grad` **Store** contexts. Keep both
meta-guards (`"X in functions"` and `len(seen) > 1`).

**Limitation to state in the plan:** this closure only follows `ast.Name` callees
(`node.func.id`), so `self._noise(...)` / `torch.nn.utils.clip_grad_norm_(...)` are seen as
**forbidden calls** but not **traversed into**. For a method-based `dpsgd.py` the frontier must
also accept `ast.Attribute` with `value` = `ast.Name(id="self")` — `test_phase14_scoring.py:506`
already does the `id`-or-`attr` match:

```python
            if callee not in (getattr(node.func, "id", None), getattr(node.func, "attr", None)):
                continue
```

#### 5d. Call-site + enclosing-function (D-05 axis 1's "the legacy clip's only reachable site is inside `if dp_fn is None`") — `tests/test_phase14_scoring.py:466-516`

```python
def _enclosing_functions(tree):
    """``{node: enclosing FunctionDef/AsyncFunctionDef or None}`` for every node in ``tree``.

    ``ast.walk`` is breadth-first, so a parent is always resolved before its children.
    """
    enclosing = {tree: None}
    for parent in ast.walk(tree):
        owner = (
            parent
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef))
            else enclosing[parent]
        )
        for child in ast.iter_child_nodes(parent):
            enclosing[child] = owner
    return enclosing


def _call_sites(callee):
    """Every ``callee(...)`` call in the D-21 file set as ``(file, function, keyword names)``.

    AST rather than ``inspect.getsource`` string matching: a substring check cannot tell a call
    from a mention in a docstring, ...
    """
    sites = []
    for path in _scanned_files():
        file = path.relative_to(_REPO_ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        enclosing = _enclosing_functions(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if callee not in (getattr(node.func, "id", None), getattr(node.func, "attr", None)):
                continue
            owner = enclosing[node]
            sites.append(
                (
                    file,
                    "<module>" if owner is None else owner.name,
                    frozenset(kw.arg for kw in node.keywords),
                )
            )
    return sites
```

The **hard-equality allowlist** discipline it enforces (`:555-561`) is exactly what V-11's "second
clip constant" refusal needs:

```python
    # HARD EQUALITY against the allowlist. Never `in`, never a subset relation: a membership
    # check is the guard getting weaker while looking bigger (16-RESEARCH Pitfall 3).
    with_persona = sorted((file, func) for file, func, kwargs in sites if "persona" in kwargs)
    assert with_persona == sorted(PERSONA_ALLOWLIST), (...)
```

D-05 axis 1's `clip_grad_norm_` claim becomes: `_call_sites("clip_grad_norm_")` restricted to
`loop.py` must equal exactly one site, and that site's enclosing `ast.If` test must be
`dp_fn is None`. `_enclosing_functions` gives the function; the `ast.If` ancestry needs the same
parent-map idiom keyed on `ast.If` instead of `FunctionDef`. **`ast.walk` is breadth-first — the
docstring at `:469` is the reason the parent map is safe to build in one pass.**

#### 5e. `.venv` / scope helper — `tests/test_phase14_scoring.py:455-463`

```python
    """The D-21 file set: ``scripts/*.py`` + ``src/**/*.py``.

    Deliberately not cached: the deliberate-RED probes that prove these guards bite add and
    remove files under ``scripts/``, and a cache would make the guards blind to exactly the
    thing they are being tested against.
    """
    return sorted((_REPO_ROOT / "scripts").glob("*.py")) + sorted(
        (_REPO_ROOT / "src").rglob("*.py")
    )
```
D-18's cross-site consistency test (read `accountant.py`'s docstring **and** `dpsgd.py`'s noise
line **and** `mitigation_accountant.py`'s constants) is V-25's multi-site source read — this is its
file-set helper. Note "deliberately not cached" and its reason.

---

### 6. `tests/test_phase22_dpsgd.py` (V-12, V-14, V-22)

#### 6a. V-14 — golden bit-identity, two-way. `tests/test_loop_penalty_fn.py:56-115`

```python
_GOLDEN = json.loads(GOLDEN_PATH.read_text())
# The gate includes torch_version: fp32 kernel bits are not guaranteed stable across torch
# releases (BLAS-backend sensitivity), so even a routine 2.7.x patch bump on the capture
# machine must SKIP (stale fixture — regenerate) rather than hard-fail as a phantom loop
# regression while the in-process identity tests still pass.
_CAPTURE_PLATFORM = (
    _GOLDEN["meta"]["platform"]["system"],
    _GOLDEN["meta"]["platform"]["machine"],
    _GOLDEN["meta"]["platform"]["torch_version"],
)


def _param_sha256(model):
    """sha256 of the bigram's single parameter tensor — the bitwise trajectory fingerprint."""
    weight = model.token_embedding_table.weight
    return hashlib.sha256(weight.detach().cpu().contiguous().numpy().tobytes()).hexdigest()


def _run_recipe(log_path, **train_kwargs):
    """Run the golden fixture's exact meta recipe; return (csv_text, final_loss_repr, sha256)."""
    cfg = TrainConfig(lr=1e-2, warmup_steps=2, max_steps=5, batch_size=4)
    seed_everything(1234)
    model = BigramLanguageModel(vocab_size=ModelConfig().vocab_size)
    final = train(
        train_config=cfg,
        runtime_config=RuntimeConfig(device="cpu"),
        model=model,
        corpus_path=CORPUS_PATH,
        eos_id=EOS_ID,
        log_path=log_path,
        eval_interval=1,
        return_final_loss=True,
        **train_kwargs,
    )
    return pathlib.Path(log_path).read_text(), repr(float(final)), _param_sha256(model)


@pytest.mark.skipif(
    (platform.system(), platform.machine(), torch.__version__) != _CAPTURE_PLATFORM,
    reason=(
        "golden bitwise replay is only valid on the capture platform + torch build "
        f"{_CAPTURE_PLATFORM} (running torch {torch.__version__}) — fp32 transcendental "
        "kernels are not bit-stable across OS/arch/BLAS backends OR torch releases, ..."
    ),
)
def test_golden_trajectory_bit_identity(tmp_path):
    csv_text, final_repr, sha = _run_recipe(tmp_path / "golden_replay.csv")
    assert csv_text == _GOLDEN["csv_text"]
    assert final_repr == _GOLDEN["final_loss_repr"]
    assert sha == _GOLDEN["param_sha256"]
```

`_run_recipe(**train_kwargs)` is precisely the seam for `dp_fn=None` / `fact_bin=None` — the
existing in-process identity tests (`:117+`) already parameterize omitted-vs-`None`. **Reuse
`_run_recipe`; do not write a second recipe.** The module docstring at `:10-34` carries the
two-way proof statement and the fixture regeneration recipe — copy that prose block into
`test_phase22_dpsgd.py`'s docstring, updated for `dp_fn`.

`:12-20` is also D-14's recorded reason "CPU proves M3 bit-for-bit" was never available.

#### 6b. V-12 — one-kwarg-apart differential. `tests/test_phase21_replay_volume.py:221-245`

```python
def test_side_channel_negative_control(tmp_path, replay_source):
    """The SAME call ONE KWARG APART on the legacy branch MUST leak — or this file is blind."""
    (short_stats, short_ids, short_mask), (long_stats, long_ids, long_mask) = _both_corpora(
        tmp_path
    )
    _assert_fixture_actually_varies(short_stats, long_stats)

    short_replay = tp._prepend_replay(
        short_ids, short_mask, 1.0, short_stats["teaching_tokens"], n_facts=None
    )
    long_replay = tp._prepend_replay(
        long_ids, long_mask, 1.0, long_stats["teaching_tokens"], n_facts=None
    )

    assert short_replay != long_replay, (
        "the LEGACY branch did not leak, so test_side_channel_closed proves nothing — a "
        "differential over an implementation that returns a constant for every input passes "
        "while saying nothing about the mechanism. ..."
    )
    # Same call site, one kwarg apart -> a different verdict for each branch. That is what makes
    # the verdict a property of the BRANCH rather than of two different fixtures.
    assert short_replay == short_stats["teaching_tokens"]
    assert long_replay == long_stats["teaching_tokens"]
```

Two load-bearing halves to copy: (1) `_assert_fixture_actually_varies` — the fixture must be proven
to differ before the differential means anything; (2) the **negative control** — the branch where
the property is *supposed* to fail is run too, so a constant-returning implementation cannot pass.
V-12 varies "public term present / absent" and asserts `torch.equal` on the private noised term.

#### 6c. V-22's positive control — spy on `clip_grad_norm_`. `tests/test_train_loop.py:42-63`

```python
def test_amp_ordering_unscale_clip_step_update(monkeypatch):
    # Record the AMP op sequence and assert unscale_ -> clip -> step -> update with exactly one
    # unscale_ per optimizer step (Pitfall 1). We spy on clip_grad_norm_ via the same call-log.
    calls: list[str] = []
    real_clip = torch.nn.utils.clip_grad_norm_

    def _spy_clip(params, max_norm, *a, **k):
        calls.append("clip")
        return real_clip(params, max_norm, *a, **k)

    monkeypatch.setattr(torch.nn.utils, "clip_grad_norm_", _spy_clip)

    cfg = TrainConfig(max_steps=1, warmup_steps=0, grad_accum_steps=1, grad_clip=1.0)
    runtime = RuntimeConfig(device="cpu")
    # The loop must thread our spy scaler through; train() accepts an injectable scaler so the
    # CPU test can observe the AMP ordering without a real GPU.
    train(train_config=cfg, runtime_config=runtime, scaler=_SpyScaler(calls))

    # Exactly one unscale_ for the single optimizer step, in the locked order.
    assert calls.count("unscale_") == 1
    order = [c for c in calls if c in ("unscale_", "clip", "step", "update")]
    assert order == ["unscale_", "clip", "step", "update"]
```

**Two reusable mechanisms in one test.** (a) `monkeypatch.setattr(torch.nn.utils,
"clip_grad_norm_", _spy_clip)` — D-03's runtime half: with `dp_fn` set, `calls.count("clip") == 0`.
(b) `_SpyScaler` (`test_train_loop.py:~20-39`) — an injectable scaler recording the op sequence;
**this is also how D-05 axis 3's single-write count and axis 4's drain assertion get observed**
without touching production code. `_SpyScaler.scale` returns `loss` unchanged and logs `"scale"`.

---

### 7. `tests/test_phase22_checkpoint.py` (V-15, V-16) and `src/personacore/checkpoint.py`

**Analog:** `checkpoint.py` itself.

**The `rng` dict D-14's `mps` slot joins — `checkpoint.py:102-107`:**

```python
        "rng": {
            "python": random.getstate(),
            "numpy": np.random.get_state(),
            "torch": torch.get_rng_state(),
            "cuda": (torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None),
        },
        # OPEN DICT: M2 may add "fisher" / "theta_star" here with no format change.
        **extra,
```

`"mps": (torch.mps.get_rng_state() if torch.backends.mps.is_available() else None)` mirrors the
`cuda` line exactly, including the `None`-when-unavailable form.

**Restore, and the backward-compat idiom — `checkpoint.py:135-143`:**

```python
    if scaler is not None and ckpt.get("scaler") is not None:
        scaler.load_state_dict(ckpt["scaler"])

    rng = ckpt["rng"]  # RESTORE state -> continue the same stream (NOT re-seed)
    random.setstate(rng["python"])
    np.random.set_state(rng["numpy"])
    torch.set_rng_state(rng["torch"])
    if rng["cuda"] is not None and torch.cuda.is_available():
        torch.cuda.set_rng_state_all(rng["cuda"])
```

⚠ **`rng["cuda"]` uses `[]`, not `.get()`.** An old checkpoint written before the `mps` key exists
would raise `KeyError` under the same form — so the mps restore **must** be
`rng.get("mps") is not None`, which is what D-14 says and what `ckpt.get("scaler")` at `:135`
already does. The docstring at `:122-124` records the precedent verbatim:

```
    ``scaler`` restore uses ``ckpt.get("scaler")`` so a pre-fix (scaler-less) checkpoint resumes
    cleanly without it — the open-dict format stays backward compatible.
```

**`dp_noise_rng` collides with nothing — `checkpoint.py:40-54` + `:85-90`:**

```python
_RESERVED_CKPT_KEYS = frozenset(
    {
        "schema_version", "model", "optimizer", "scheduler", "scaler",
        "step", "val_loss", "model_config", "train_config", "git_sha", "rng",
    }
)
...
    clash = _RESERVED_CKPT_KEYS & extra.keys()
    if clash:
        raise ValueError(
            f"save_checkpoint: extra keys {sorted(clash)} collide with reserved "
            "checkpoint fields — they would silently overwrite core resume state."
        )
```
`dp_noise_rng` is not reserved → arrives through `**extra` with **no format change**, exactly as
`fisher`/`theta_star` did. `CKPT_SCHEMA_VERSION` (`:30`) must **not** bump.

**The `checkpoint_extra` route from the loop — `loop.py:318-320`:**
```
        checkpoint_extra: dict splatted into every in-loop ``save_checkpoint`` call (the
            M2 fisher/theta_star carry, RESEARCH Open Q1); None adds no caller keys (the
            loop itself always records ``best_val_loss`` — Seam 3 continuity).
```
`dp_noise_rng` must be **live at save time**, not a value captured once — so it rides
`checkpoint_extra` only if the caller can refresh it, or the loop reads it off `dp_fn`. Planner's
call; the constraint is that `checkpoint_extra` is bound **once** at `train()` entry.

---

### 8. `tests/test_phase20_prereg.py` (MODIFIED — D-11's two halves)

**Analog:** the Phase-21 pair in the same file. Both edits mirror it exactly.

**Half 1 — `V4_ARTIFACT_GLOBS`, `:130`:**
```python
V4_ARTIFACT_GLOBS = ("results/phase20_*", "results/phase21_*")
```
becomes `(..., "results/phase23_*")`. The comment block above it (`:110-129`) already records why
this alone enforces nothing — extend that comment for phase23 rather than adding a new one.

**Half 2 — the live ordering test, `:257-289`** (copy structure verbatim, swap three literals):

```python
def test_phase21_prereg_is_frozen_before_every_phase21_result():
    """Phase 21 D-20: the privacy-unit pin never moved after a Phase 21 number existed.
    ...
    """
    _assert_ordering_holds(
        root=_ROOT,
        prereg_artifact=PHASE21_PREREG_ARTIFACT,
        artifact_glob="results/phase21_*",
        globs=V4_ARTIFACT_GLOBS,
    )
```

**Half 2b — the hand-written path constant that confers the freeze, `:91` / `:108`:**
```python
PHASE20_PREREG_ARTIFACT = "scripts/mitigation_gate.py"
...
PHASE21_PREREG_ARTIFACT = "scripts/mitigation_unit.py"
```
`PHASE22_PREREG_ARTIFACT = "scripts/mitigation_accountant.py"` lands beside them, with the
`:93-107` comment block's reasoning (glob = protected, explicit path = frozen) carried forward.

**The naming rule D-09's filename must satisfy, `:54-70`:**
```
# The repo's established register is a GLOB (`tests/test_phase18_prereg.py:59`,
# `tests/test_phase17_stats.py:62`) over `phaseNN_*.py`, and its stated purpose is that "every
# driver a later plan adds enters these scans the moment it exists". But the pin
# `scripts/mitigation_gate.py` matches NO `phase20_*.py` glob — it is named for its subject rather
# than for its phase ...
```

**The RED-then-GREEN prefix fixture (V-10's "watch it bite") — `:657-810`,
`test_phase21_glob_sees_the_phase21_prefix_red_then_green`.** Its docstring states the obligation
for `results/phase23_*` word-for-word:

```
    **Why this exists, and why it cannot wait for plan 21-11.** The live
    `test_phase21_prereg_is_frozen_before_every_phase21_result` is vacuous today BY CONSTRUCTION:
    nothing matches `results/phase21_*` yet, so `checked` is 0 and its product assertion reads
    `0 == n * 0` — green having compared nothing. `results/phase21_*` has therefore never once been
    OBSERVED matching anything. Reading a glob pattern and confirming it bites are different acts,
    and a pattern that reads correctly while matching nothing is green over nothing ...
```

and names the mutation that would otherwise be invisible (`:673-676`):
> `V4_ARTIFACT_GLOBS` holds BOTH `results/phase20_*` and `results/phase21_*` since plan 21-01, so a
> mutation swapping this fixture's `artifact_glob` to the phase20 prefix would still satisfy the
> `assert artifact_glob in globs` consistency check and would be INVISIBLE without it.

With three prefixes live, that mutation-invisibility gets **worse** — the phase23 fixture's
`ls-files` positive observation is mandatory, not optional.

**The throwaway-repo scaffold — `:315-328` (from `test_a_same_commit_pin_and_artifact_is_refused`):**

```python
    _git("init", "-q", cwd=tmp_path)
    _git("config", "user.name", "phase21-fixture", cwd=tmp_path)
    _git("config", "user.email", "phase21-fixture@localhost", cwd=tmp_path)

    pin = tmp_path / PHASE21_PREREG_ARTIFACT
    pin.parent.mkdir(parents=True)
    pin.write_text("# stand-in for the pin: the ORDER is the subject, not the content\n")
    probe = tmp_path / "results" / "phase21_probe.json"
    probe.parent.mkdir(parents=True)
    probe.write_text('{"probe": true}\n')
```

Every `_git` call passes `cwd=tmp_path`, never `_ROOT`. `_git`'s keyword-only `cwd` (`:133-146`)
exists for exactly this.

---

### 9. `scripts/teach_persona.py` (MODIFIED — D-08's four wirings)

**Analog:** its own `train()` call. Current text, `:1167-1204`:

```python
    final = train(
        train_config=TrainConfig(
            lr=LR,
            warmup_steps=WARMUP_STEPS,
            max_steps=MAX_STEPS,
            batch_size=BATCH_SIZE,
            weight_decay=WEIGHT_DECAY,
            seed=seed,
        ),
        runtime_config=runtime,
        model=model,
        model_config=model_cfg,
        train_bin=paths["bin"],
        # Phase 14 REVERSES Phase 12's unmasked verdict, ...
        train_mask_bin=paths["mask"],
        # dialog_val.bin + its mask, so the IN-LOOP curve IS the collateral-collapse signal ...
        val_bin=DIALOG_VAL_BIN,
        val_mask_bin=DIALOG_VAL_MASK,
        # penalty_fn=None is STRUCTURALLY FORCED here, not merely preferable, for two
        # independent reasons (14-RESEARCH Pattern 3): ...
        penalty_fn=None,
        log_path=paths["csv"],
        eval_interval=EVAL_INTERVAL,
        checkpoint_path=paths["checkpoint"],
```

Confirms all four measured gaps: **no `grad_accum_steps=` inside `TrainConfig(...)`, no
`replay_bin`/`replay_mask_bin`/`replay_windows`, no fact bin, no `dp_fn`.** Each new kwarg lands
with a comment naming its decision id — that is this call site's established register (three of the
existing kwargs already carry multi-line reason comments).

**CLI shape — `main()` is argv-slicing, NOT argparse, `:987-1014`:**

```python
def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    # Plan 14-09's two modes. Both are defined below in the CALIBRATION RUN section.
    if argv and argv[0] == "--calibration":
        run_calibration(argv[1:])
        return
    if argv and argv[0] == "--rewrite-report":
        rewrite_report(argv[1:])
        return
    if len(argv) != 1 or argv[0] not in ARMS:
        raise SystemExit(USAGE)
    arm = argv[0]

    facts, second_person, replay_ratio = arm_spec(arm)
    train_arm(
        arm,
        facts=facts,
        family_ids=fs.TAUGHT_FAMILY_IDS,
        second_person=second_person,
        replay_ratio=replay_ratio,
        ...
        prefix="phase21" if arm in DP_ARMS else "phase14",
    )
```

D-08's "σ and C arrive keyword-only with NO DEFAULT on the CLI" therefore needs **a new argv
branch**, not an argparse flag — `len(argv) != 1` at `:996` rejects extra tokens today, and `USAGE`
must be extended in the same edit. `run_calibration(argv[1:])` at `:991` is the sub-mode precedent.
`prefix="phase21" if arm in DP_ARMS else "phase14"` at `:1013` is the DP-arm branch idiom.

**`DP_ARMS`, `:260`:** `DP_ARMS = ("dp_n8", "dp_n64")` — the tuple to branch on, already used at
`:1013`.

**The public replay budget the seam consumes — `:180-204`:**
```python
def replay_window_budget(n_facts, block_size=BLOCK_SIZE):
    """The v4.0 replay volume in tokens — THE ONLY SITE that computes it (D-11 / D-24).

    ``REPLAY_WINDOWS_PER_FACT * n_facts * block_size``. Every consumer calls this function:
    :func:`_prepend_replay`'s ``n_facts`` branch, ``train()``'s replay seam via its caller, the
    plan-21-11 driver, and every test. ...
    """
    return REPLAY_WINDOWS_PER_FACT * int(n_facts) * int(block_size)
```
It returns **tokens**; `train(replay_windows=)` wants **windows** — hence CONTEXT's
`replay_window_budget(n_facts) // BLOCK_SIZE`. The docstring's claim *"``train()``'s replay seam
via its caller"* is IN-04: **false today, made true by this phase.** Update this docstring in the
same edit or the claim stays false in the other direction.

---

## Shared Patterns

### Refusal register: `src/` raises, `scripts/` `_prove`s
**Sources:** `src/personacore/lora/layer.py:53-55` (the recorded `python -O` reason),
`scripts/mitigation_unit.py:70-79` (`_prove` → `SystemExit`).
**Apply to:** `dpsgd.py` + `accountant.py` (raise `RuntimeError`/`ValueError`, never `assert`,
never `_prove`); `mitigation_accountant.py` (`_prove`, defined locally, name in brackets).
**Measured (CONTEXT):** `_prove` in 18 `scripts/` modules, 0 `src/`; `src/` raises at 25 sites in
`training/` + `lora/`.

### Refuse by PROPERTY, not by NAME
**Source:** `src/personacore/lora/inject.py:96-112` — key-set **and** shape/dtype **and** scale
audits, each with its own message, before a single tensor loads:
```python
    if expected.keys() != got.keys():
        ...
        raise ValueError(
            f"adapter key-set mismatch: missing={missing} unexpected={unexpected} — "
            "the artifact does not describe this injected model; refusing to load."
        )
```
and `:113-118`'s reason for the third audit: *"`alpha` is shape-invisible, so the two audits above
cannot see it."*
**Apply to:** D-04's three refusals, D-13's non-vacuity conditions (each condition separately
messaged — RESEARCH F1 proves condition 3 is not implied by condition 2), F1's
`a != 0.0 and b != 0.0` precondition.

### Meta-guard: prove the scan is not scanning nothing
**Sources:** `tests/test_phase15_plots.py:326` (`"the AST import walk found no imports — the walk
stopped working"`), `tests/test_phase18_docs.py:656` + `:672`, `tests/test_phase14_scoring.py:552`
(`"no build_recall_prompt call sites found — the AST walk stopped working"`),
`tests/test_phase20_prereg.py:838-841` (collapsed glob).
**Apply to:** every AST guard in V-09, V-10, V-11, V-25. Non-negotiable — an AST guard without one
is green over nothing.

### Reaching a `scripts/` module from a test
**Source:** `tests/test_phase20_prereg.py:44-50` (and `tests/test_phase21_filler.py:43-47`):
```python
_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import _prose  # noqa: E402  (needs the sys.path insert above)
import erasure_gate  # noqa: E402  (same reason)
import mitigation_gate  # noqa: E402  (same reason)
```
Note the `if ... not in sys.path` idempotence guard and the `# noqa: E402` with its reason.
**Apply to:** V-06 (import `mitigation_accountant`'s `GOLDEN_EPSILON`), V-25 (read all three
sites). This is also the measured basis for D-10: **`src/` never does this**, so `src/` cannot
import `scripts/`.

### Numbers travel with their denominator and their bound
**Source:** `scripts/mitigation_unit.py:87-125` (`PRIVACY_UNIT_ARITHMETIC` writes the formula out,
names the wrong reading that stating a denominator invites, and labels itself ANALYTIC), and
`:193-207` (`REJECTED_DELTA_REASON` gives both capacities and both margins).
**Apply to:** `GOLDEN_EPSILON`'s prose, `REJECTED_FORM`'s reason (RESEARCH's measured crossover
`μ = 1.737896746` / `35.7×` at σ=0.3 / the Thm A.1 `ε ∈ (0,1)` hypothesis), `accountant.py`'s
tolerance docstrings (`1e-12` vs the measured `1.07e-14`).

### Tolerance vs `==`, stated per call shape
**Source (this phase's own research, F3):** two different call shapes ⇒ `rel_tol=1e-12`; the same
call shape across processes ⇒ exact `==`. **No existing analog in the tree conflates them** — the
nearest precedent is `inject.py:113-118`, which argues for exact equality *because the same
operation on the same operands gives a bit-identical float*, and explicitly says *"a tolerance
would only weaken this."* Cite that reasoning when justifying V-15's `==`.

---

## No Analog Found

Two gaps. Neither is a missing file — both are shapes the tree does not yet have.

| Need | Why no analog | What the planner should do |
|---|---|---|
| **In-test RED-then-GREEN over a MUTATED SOURCE** (V-19, V-21 — the AST half of FAKE 2 and FAKE 4) | Every AST guard in the tree reads a **fixed committed path** (`_EXTRACTION_PATH`, `PLOT_SCRIPT`, `_GATE_MODULES`) and cannot be pointed at mutated text. The repo's deliberate-RED probes for AST guards are **manual and recorded in plan SUMMARYs** (`tests/test_phase19_erasure.py:184`: *"see the plan SUMMARY's deliberate-RED record"*), not committed fixtures. The only committed RED-then-GREEN is git-state-based (`test_phase20_prereg.py:657-810`). | Factor `test_phase22_dpsgd_ast.py`'s guard as `_assert_no_forbidden_between_noise_and_step(source_text)` taking **text**, so the live test passes `dpsgd.py`'s bytes and the fake probe passes a mutated string under `tmp_path`. `test_phase20_prereg.py:153-155` already states the rule this must satisfy: *"a guard proved correct in a scratch repository and a guard running against this one must be the SAME code, or the proof is about a different function than the one CI runs."* |
| **MPS-gated test** (V-14/V-16's device rows) | Zero `torch.backends.mps.is_available()` skipif markers exist in `tests/`. The nearest is `test_loop_penalty_fn.py:96-107`'s platform-tuple skipif — a **capability**-gate, not a device-gate. | Copy the skipif *register* (a long `reason=` naming why the skip is honest and what still carries the guarantee) from `test_loop_penalty_fn.py:98-106`, with the predicate swapped. D-14 requires the mps slot be recorded as **required-but-unexercised** — put that in the `reason=` string, where a reader hits it. |

---

## Metadata

**Analog search scope:** `src/personacore/**` (37 modules), `scripts/**` (52 modules),
`tests/**` (AST-bearing subset: 8 files).
**Files read in full or in targeted ranges:** 16.
**Verification method:** every path + line range in `22-CONTEXT.md`'s `<canonical_refs>` and
`22-RESEARCH.md`'s repo-internal sources was resolved against HEAD `ee423b4`; excerpts are copied
bytes, not reconstructions.
**Pattern extraction date:** 2026-08-25

---

## Stale Anchor Findings

Seven. Ordered by blast radius. **#3 is live inside a file this phase edits.**

**1. `loop.py:165` → `loop.py:181` (CONFIRMED, already corrected in CONTEXT).**
`.planning/ROADMAP.md` SC4 and `.planning/REQUIREMENTS.md:135` cite `loop.py:165` as the clip site.
Measured: `:165` is `accum = max(1, train_cfg.grad_accum_steps)`; the clip is `:181`
`torch.nn.utils.clip_grad_norm_(model.parameters(), train_cfg.grad_clip)`. `22-CONTEXT.md` already
records this; repeated here so no plan re-imports it from the roadmap.

**2. `tests/test_phase20_prereg.py:121-183` → `:149-225` for `_assert_ordering_holds`.**
`22-CONTEXT.md` cites `:121-183`. Actual: `def _assert_ordering_holds` is at `:149`; its body runs
to `:225`. `:121-130` is the `V4_ARTIFACT_GLOBS` comment block. D-11's plan must cite `:149`.

**3. ⚠ `assert artifact_glob in globs` cited as `:129` — actual `:157`. AND THE STALE ANCHOR IS IN
THE REPO, at `tests/test_phase20_prereg.py:122-123`.** The live comment reads *"`globs` is read in
exactly ONE place inside `_assert_ordering_holds` — the `assert artifact_glob in globs` consistency
check at `:129` — while the ordering loop at `:150` runs on the SINGULAR `artifact_glob`."*
Measured: the consistency check is `:157`; the ordering loop is `:181`. `22-CONTEXT.md` inherited
`:129` from this comment. **Phase 22 is editing this exact comment block to add the phase23 prefix —
fix both anchors in the same edit.** This is the Phase-21 IN-02 defect class recurring in the file
whose entire purpose is pre-registration integrity.

**4. `scripts/mitigation_unit.py` cites `tests/test_phase20_prereg.py:498`, `:522`, `:523`, `:64-66`,
`:72`, `:574`, `:143`, `:157` — four are stale.** Measured against HEAD: the accumulating
`imported` loop is `:891-903` (not `:498`); the subset assertion is `:916` (not `:522`/`:523`);
`git log -- <pin>` is `:171` (not `:143`); `adds[-1]` is `:185` (not `:157`). `:72`
(`_GATE_MODULES`) and `:64-66` are correct. **`mitigation_unit.py` is FROZEN** (two
`results/phase21_*` artifacts are tracked: `results/phase21_multiplicity.json`,
`results/phase21_privacy_unit.json`) — so these **cannot be edited**; a correction is a dated
continuation via `scripts/_addendum.py` (Phase 20 D-24). **Consequence for this phase:**
`mitigation_accountant.py` copies this file's structure, and if it copies its habit of citing
test-file line numbers it will be frozen with the same rot. **Recommend: cite `mitigation_gate.py`
and test files by NAME + symbol (`tests/test_phase20_prereg.py::test_mitigation_gate_import_graph_is_stdlib_and_erasure_gate_only`),
never by line, inside anything that gets frozen.**

**5. `scripts/teach_persona.py:167-178` → `:180-204` for `replay_window_budget`.**
`22-CONTEXT.md` cites `:167-178`; that range is the WR-03 retraction comment.
`REPLAY_WINDOWS_PER_FACT = 4` is `:177`; `def replay_window_budget` is `:180`; the IN-04 docstring
claim (*"``train()``'s replay seam via its caller"*) is `:184`.

**6. `src/personacore/lora/layer.py:45-58` → `:46-56` for the `merge` docstring.**
The `python -O` sentence D-15 rests on is `:53-55`. `:57-58` is already the
`if self.merged: raise RuntimeError(...)` body.

**7. `src/personacore/lora/inject.py:29-44` / `:46-56` → `:29-43` / `:46-55`.** Off by one at both
ends; `mark_only_lora_trainable`'s closed-form docstring line is `:50`.

**Also worth recording (not stale, but under-specified):**
`22-CONTEXT.md` names `tests/test_phase20_prereg.py:281-330` as "the throwaway-repo RED-then-GREEN
fixture shape to copy". That range lands inside `test_a_same_commit_pin_and_artifact_is_refused`
(`:292-388`), which proves *reflexivity*, not *prefix visibility*. The fixture D-11 actually needs
a sibling of is **`test_phase21_glob_sees_the_phase21_prefix_red_then_green` (`:657-810`)** — a
five-state prefix walk that CONTEXT does not name. Both are useful; the second is the one that
matches D-11's obligation.
