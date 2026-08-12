# Phase 10: EWC Core - Pattern Map

**Mapped:** 2026-06-12
**Files analyzed:** 10 new/modified files
**Analogs found:** 10 / 10

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/personacore/continual/__init__.py` | package init (import surface) | — | `src/personacore/lora/__init__.py` | exact |
| `src/personacore/continual/fisher.py` | service (estimation algorithm) | batch (memmap windows → tensor stats) | `src/personacore/training/data.py` (`get_batch_memmap`) + `training/loop.py` (`estimate_loss` eval/RNG discipline) | role-match |
| `src/personacore/continual/ewc.py` | service (penalty callable) | transform (params → scalar tensor) | `src/personacore/training/loss.py` (seam contract) + `checkpoint.py` (fail-loud validation style) | role-match |
| `src/personacore/training/loop.py` (MODIFIED) | service (training orchestration) | batch | itself — `_optimizer_step` lines 122–147, `train()` lines 150–174 | exact (in-place) |
| `src/personacore/checkpoint.py` (MODIFIED, if cache loader lands here) | service (serialization) | file-I/O | itself — `export_adapter`/`load_adapter` lines 165–229 | exact (in-place) |
| `scripts/estimate_fisher_tinystories.py` | script (real-weights smoke + cache writer) | batch + file-I/O | `scripts/train_adapter_smoke.py` (09-04) | exact |
| `tests/test_fisher.py` | test | — | `tests/test_gpt_weight_tying.py` + `tests/test_ablation_config.py` (data_ptr dedup idioms) | role-match |
| `tests/test_ewc_penalty.py` | test | — | `tests/test_assemble_loss.py` (exact-equality oracle style) | role-match |
| `tests/test_loop_penalty_fn.py` | test | — | `tests/test_resume_curve.py` (trajectory equality) + `tests/test_train_loop.py` (accum equivalence) | exact |
| `tests/test_fisher_checkpoint.py` | test | — | `tests/test_checkpoint.py::test_open_dict_extensible` + `tests/test_lora_artifact.py` (cache schema tests) | exact |

## Pattern Assignments

### `src/personacore/continual/__init__.py` (package init)

**Analog:** `src/personacore/lora/__init__.py` (Phase 9's new-package precedent — copy verbatim shape)

**Whole-file pattern** (`src/personacore/lora/__init__.py` lines 1–40): docstring naming the phase + requirement IDs, relative imports, explicit sorted `__all__`:

```python
"""Phase 9 — from-scratch LoRA (LORA-01..05): public import surface.

Plan 09-01 ships the config (``LoRAConfig``/``TARGET_PROJECTIONS``), the ``LoRALinear``
composition wrapper, and the post-load injection/freeze machinery; ...
"""

from .config import TARGET_PROJECTIONS, LoRAConfig
from .inject import (
    adapter_disabled,
    eject_adapter,
    ...
)
from .layer import LoRALinear

__all__ = [
    "LoRAConfig",
    "LoRALinear",
    ...
]
```

For `continual/`: export `estimate_fisher` from `.fisher` and `EWCPenalty` from `.ewc` (plus the cache loader if it lives in this package — Open Q2 leans `checkpoint.py` instead).

---

### `src/personacore/continual/fisher.py` (service, batch)

**Analogs:** `src/personacore/training/data.py` (window-draw idiom), `src/personacore/training/loop.py` (eval-mode + RNG discipline), `src/personacore/lora/config.py` (optional dataclass-config house pattern).

**Module docstring pattern** — every module in this codebase opens with a multi-paragraph docstring naming requirement IDs and load-bearing properties (see `training/loss.py:1–14`, `checkpoint.py:1–21`, `training/data.py:1–13`). Mirror it: name EWC-01, D-01..D-05, Pitfall 6/7 in the docstring.

**Window-draw idiom to mirror privately** (`training/data.py` lines 73–90, `get_batch_memmap`) — re-open the memmap per draw (RSS discipline), bound starts to `len(data) - block_size - 1`, cast uint16 → int64 at draw time:

```python
def get_batch_memmap(bin_path, batch_size, block_size, device):
    """... a long-lived memmap accumulates RSS across thousands of training steps
    (nanoGPT leak — Pitfall 1), so it is opened fresh and discarded per batch. ..."""
    data = np.memmap(bin_path, dtype=np.uint16, mode="r")
    ix = np.random.randint(0, len(data) - block_size - 1, size=batch_size)
    x = torch.stack([torch.from_numpy(data[i : i + block_size].astype(np.int64)) for i in ix])
    y = torch.stack(
        [torch.from_numpy(data[i + 1 : i + 1 + block_size].astype(np.int64)) for i in ix]
    )
    return x.to(device), y.to(device)
```

**Critical deviation from the analog:** `get_batch_memmap` draws via **global** `np.random` — `estimate_fisher` must NOT (Pitfall 3 / RNG purity). Use a local `np.random.default_rng(seed)` for the start indices, keeping every other line of the idiom (re-open per draw, the `- block_size - 1` bound, the int64 cast, batch dim `[None]` at batch=1). Either mirror these ~6 lines privately in `fisher.py` or add an additive `rng=None` kwarg to `get_batch_memmap` (RESEARCH "Don't Hand-Roll" allows both).

**Eval-mode + restore discipline** (`training/loop.py` lines 70–102, `estimate_loss`) — the codebase's "side computation that must not perturb training" template:

```python
@torch.no_grad()
def estimate_loss(model, val_ids, train_cfg, model_cfg, device, iters=20):
    rng = _rng_state()
    model.eval()
    ...
    for _ in range(iters):
        ...
        _, loss = model(xb, yb)        # the model's OWN forward — reduction matched for free
        losses.append(loss.item())
    model.train()
    _restore_rng(rng)
    return sum(losses) / len(losses)
```

Deviations for `estimate_fisher`: NO `@torch.no_grad()` (grads are the product); restore the **prior** `model.training` flag (`was_training = model.training`, then conditionally `model.train()`) rather than unconditionally calling `model.train()`; no `_restore_rng` needed because a local Generator never touches global state (the unit test asserts bit-unchanged global RNG using the `_rng_state` tuple idiom below).

**Loss-reduction match:** reuse `_, loss = model(xb, yb)` exactly as `estimate_loss` does — never reimplement CE (RESEARCH anti-pattern; the LOCKED model tail is the matched mean-over-tokens reduction).

**Optional config dataclass** (`src/personacore/lora/config.py` lines 19–26) — if a `FisherConfig` surface is wanted, mirror `LoRAConfig`: plain dataclass, defaulted fields, per-field rationale comments, travels as `dataclasses.asdict()` primitives into `fisher_meta`:

```python
@dataclass
class LoRAConfig:
    """Rank/alpha/dropout/targets for from-scratch LoRA injection (LORA-01)."""

    r: int = 8  # rank — 331,776 trainable params at production shape ...
    alpha: float = 16.0  # classic alpha/r convention -> scale 2.0 at defaults (pinned, P3).
```

Core skeleton, mean-normalization, half-split convergence stats, and the hand-rolled Spearman: use RESEARCH.md Code Examples 1 and 6 directly (no codebase analog — see No Analog Found).

---

### `src/personacore/continual/ewc.py` (service, transform)

**Analogs:** `src/personacore/training/loss.py` (the seam it feeds), `src/personacore/checkpoint.py` (fail-loud-at-the-choke-point validation style).

**The seam contract the penalty must satisfy** (`training/loss.py` lines 17–28) — the penalty `EWCPenalty(model)` returns must be a **precomputed scalar tensor** (D-04: "no callbacks, no lazy callables"):

```python
def assemble_loss(base_loss, extra_penalties=()):
    """Return ``base_loss + sum(extra_penalties)`` — identity when ``extra_penalties`` is empty."""
    total = base_loss
    for p in extra_penalties:
        total = total + p
    return total
```

**Fail-loud construction-time validation style** (`checkpoint.py` lines 215–220, `load_adapter`) — name the gaps in the error, never let a bare `KeyError` surface downstream:

```python
    missing = {"adapter", "lora_config", "base_fingerprint"} - loaded.keys()
    if missing:
        raise ValueError(
            f"malformed adapter artifact {path}: missing keys {sorted(missing)} "
            "(expected an export_adapter persona file)."
        )
```

Apply the same style in `EWCPenalty.__init__`: validate `fisher.keys() == theta_star.keys()` and that every key names a model parameter, raising `ValueError` naming the offending keys at construction, not mid-run. Move Fisher/θ* to `device` exactly once in `__init__` (ARCHITECTURE anti-pattern 4 — cross-device tensors crash mid-run on MPS).

Penalty body: RESEARCH.md Code Example 4 (Kirkpatrick quadratic form; `(p − θ*)` is bitwise-zero at the anchor in fp32, so exact `0.0` is testable with equality).

---

### `src/personacore/training/loop.py` (service, MODIFIED — additive only)

**Analog:** itself. The phase's bit-identity success criterion forbids any restructure; copy the existing shapes when threading the new kwarg.

**The exact splice point** (`loop.py` lines 134–141, inside `_optimizer_step`):

```python
    for micro in range(accum):
        xb, yb = batch_fn(micro)
        with runtime.autocast():  # RuntimeConfig.autocast() — single AMP source (no torch.cuda.*)
            _, base_loss = model(xb, yb)
            total = assemble_loss(base_loss, ())  # identity in M1 (D-04)
            loss = total / accum  # scale so accumulated grads average across micro-batches
        scaler.scale(loss).backward()
        summed += float(base_loss.item())
```

Becomes (ARCHITECTURE Pattern 2, verbatim — penalty joins BEFORE `/accum`):

```python
        with runtime.autocast():
            _, base_loss = model(xb, yb)
            penalties = (penalty_fn(model),) if penalty_fn is not None else ()
            total = assemble_loss(base_loss, penalties)
            loss = total / accum
```

`summed += float(base_loss.item())` stays base-loss-only (logged `train_loss` keeps its v1.0 meaning).

**Kwarg-threading pattern** (`loop.py` lines 122 and 150–174): `_optimizer_step(model, optimizer, scheduler, scaler, train_cfg, runtime, batch_fn)` gains `penalty_fn` as a trailing parameter; `train(*,...)` is keyword-only with documented defaults — add `penalty_fn=None` to the signature and an Args entry in the same docstring style as the existing kwargs (e.g. line 195's `fixed_batch` entry). The call site at lines 309–311 threads it through.

**If the planner takes Open Q1 (checkpoint_extra threading):** the three `save_checkpoint` call sites to splat `**(checkpoint_extra or {})` into are lines 342–353 (Seam 3 best.pt), 362–373 (Seam 4a in-loop latest.pt), and 386–397 (end-of-call latest.pt). All three share this exact shape:

```python
                save_checkpoint(
                    checkpoint_path,
                    model=model,
                    optimizer=optimizer,
                    scheduler=scheduler,
                    scaler=scaler,
                    step=step,
                    model_config=model_cfg,
                    train_config=train_config,
                    git_sha=git_sha(),
                    val_loss=final_loss,
                )
```

**Must not change:** the AMP+accum+clip ordering at lines 140–146 (`scale → backward × accum → unscale_ → clip → step → update → scheduler.step`) — it is spy-pinned by `tests/test_train_loop.py::test_amp_ordering_unscale_clip_step_update`.

---

### `src/personacore/checkpoint.py` (MODIFIED, if `export_fisher`/`load_fisher` land here — RESEARCH Open Q2 recommendation)

**Analog:** itself — `export_adapter`/`load_adapter` (lines 165–229) are the schema-versioned safe-artifact precedent to mirror symmetrically.

**Schema constant pattern** (lines 30–32) — add `FISHER_SCHEMA_VERSION = 1` alongside:

```python
CKPT_SCHEMA_VERSION = 1
SLIM_SCHEMA_VERSION = 1  # slim INFERENCE artifact schema (DEMO-02), independent of the full one.
ADAPTER_SCHEMA_VERSION = 1  # adapter "persona file" schema (LORA-03 / D-01); independent again.
```

**Exporter pattern** (lines 165–189, `export_adapter`) — caller supplies plain dicts; `checkpoint.py` NEVER imports the feature package (locked dependency direction); returns the dict it wrote:

```python
def export_adapter(path, *, adapter, lora_config, base_fingerprint) -> dict:
    """... tensors and primitive containers exclusively, so it round-trips through
    ``torch.load(..., weights_only=True)`` ... The caller supplies plain dicts —
    ``checkpoint.py`` NEVER imports ``lora/`` (locked dependency direction ...)."""
    art = {
        "schema_version": ADAPTER_SCHEMA_VERSION,
        "adapter": adapter,
        "lora_config": lora_config,
        "base_fingerprint": base_fingerprint,
    }
    torch.save(art, path)
    return art
```

For Fisher: `{schema_version, fisher, fisher_meta, anchor_fingerprint}` — `anchor_fingerprint` is the provenance trio read from `best.pt` (the `export_adapter` D-02 precedent). NO θ* in the cache (recoverable from `best.pt`); NO dataclass instances or callables (keeps the `weights_only=True` bar — `fisher_meta` is primitives only).

**Loader pattern** (lines 192–214, `load_adapter`) — single choke point, `weights_only=True`, schema gate fires before any consumption:

```python
def load_adapter(path, *, expected_fingerprint=None, map_location="cpu") -> dict:
    loaded = torch.load(path, map_location=map_location, weights_only=True)
    if loaded.get("schema_version") != ADAPTER_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported adapter schema_version {loaded.get('schema_version')!r} in "
            f"{path} (expected {ADAPTER_SCHEMA_VERSION}). Re-export with "
            "personacore.checkpoint.export_adapter."
        )
    missing = {"adapter", "lora_config", "base_fingerprint"} - loaded.keys()
    if missing:
        raise ValueError(...)
```

**The `**extra` persistence seam (UNCHANGED — consume verbatim)** (lines 60–80, `save_checkpoint`): the docstring at line 77 reserves exactly this use:

```python
        # OPEN DICT: M2 may add "fisher" / "theta_star" here with no format change.
        **extra,
    }
    torch.save(ckpt, path)
```

`load_checkpoint` (line 114) returns the full dict — callers read `ckpt["fisher"]` etc. directly.

---

### `scripts/estimate_fisher_tinystories.py` (script, batch + file-I/O)

**Analog:** `scripts/train_adapter_smoke.py` (the 09-04 precedent — copy its shape section by section).

**Header pattern** (lines 29–60): MPS-fallback env BEFORE the torch import, `noqa: E402` on every post-env import, `_REPO_ROOT` path constants with gitignore notes:

```python
import math
import os
import pathlib

# An uncovered MPS op falls back to CPU rather than crashing the run (T-05-04 precedent).
# Set BEFORE importing torch so the backend honors it for the whole process.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import torch  # noqa: E402  (must follow the MPS-fallback env set above)

from personacore.preflight import preflight_device  # noqa: E402
from personacore.seeding import seed_everything  # noqa: E402

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BEST_PATH = _REPO_ROOT / "checkpoints" / "best.pt"  # own trusted base checkpoint (gitignored)
TRAIN_BIN = _REPO_ROOT / "data" / "train.bin"  # LOCAL memmap corpus
```

**Tuned-constants block** (lines 62–71) — named module-level constants with rationale comments, no argparse (house D-04 pattern):

```python
# --- Tuned constants (smoke-scale: prove the discipline, not train a persona) ---
LORA_CFG = LoRAConfig()  # production defaults r=8/alpha=16.0 ...
LR = 1e-3
MAX_STEPS = 50
```

For Fisher: `N_EXAMPLES = 2000` (D-04), `SEED`, λ placeholder constant, `FISHER_CACHE = _REPO_ROOT / "checkpoints" / "fisher_tinystories.pt"`.

**Preflight + prerequisite gate** (lines 74–87):

```python
def main() -> None:
    # Gate on a usable device (CUDA-P100 -> MPS -> CPU raise) BEFORE the run (pretrain precedent).
    summary = preflight_device(strict=True)
    print(f"[train_adapter_smoke] preflight: {summary}")

    if not BEST_PATH.exists():
        raise FileNotFoundError(
            f"Missing {BEST_PATH}. Run `python scripts/pretrain_tinystories.py` first."
        )
```

**Trusted anchor load** (lines 92–98) — `weights_only=False` with the trusted-own-file comment, config rebuilt from the blob, load BEFORE anything else:

```python
    blob = torch.load(BEST_PATH, weights_only=False)
    model_cfg = ModelConfig(**blob["model_config"])
    model = GPT(model_cfg)
    model.load_state_dict(blob["model"])  # LOAD BEFORE INJECT — the load-bearing ordering.
```

**Proof checks as explicit raises, never asserts** (lines 102–106 and 160–176) — every check is a `raise SystemExit(...)` so failures exit non-zero even under `python -O`:

```python
    if n_wrapped != 6 * n_layer:
        raise SystemExit(
            f"inject_lora wrapped {n_wrapped} projections, expected 6 * n_layer = {6 * n_layer}"
        )
    ...
    if not math.isfinite(float(final)):
        raise SystemExit(f"non-finite final loss {final!r} (PITFALLS P5)")
```

Phase 10's checks: Fisher finite/≥0; tied entry once with `lm_head.weight` absent; `mean(F)=1` within fp32 tolerance; penalty exactly `0.0` at anchor; perturbed param → penalty > 0; convergence stats printed (report, not gate — D-05).

**Refuse-to-rerun semantics** (lines 130–139) — the RESEARCH-recommended cache policy mirrors this:

```python
    if SMOKE_CKPT.exists():
        prior_step = torch.load(SMOKE_CKPT, weights_only=False)["step"]
        if prior_step >= MAX_STEPS:
            raise SystemExit(
                f"[train_adapter_smoke] {SMOKE_CKPT} is already complete (step {prior_step} >= "
                f"MAX_STEPS {MAX_STEPS}). Delete it to rerun the smoke from scratch."
            )
```

For Fisher: refuse-if-cache-exists with a "delete to re-estimate" message.

**Provenance fingerprint READ, never recomputed** (lines 178–188):

```python
    export_adapter(
        ADAPTER_PATH,
        adapter=lora_state_dict(model),
        lora_config=asdict(LORA_CFG),
        base_fingerprint={
            "git_sha": blob["git_sha"],
            "step": blob["step"],
            "val_loss": blob["val_loss"],
        },
    )
```

**Footer** (lines 190–196): print sizes/results with the `[script_name]` prefix; `if __name__ == "__main__": main()`.

---

### `tests/test_fisher.py` (test)

**Analogs:** `tests/test_gpt_weight_tying.py` (data_ptr identity), `tests/test_ablation_config.py` (dedup counting), `training/loop.py` `_rng_state` (RNG-purity assertion).

**data_ptr dedup assertion** (`test_gpt_weight_tying.py` lines 15–19):

```python
def test_lm_head_shares_storage_with_token_embedding():
    # data_ptr() identity is the load-bearing assert: a copy would differ here AND inflate the
    # param count by one vocab x n_embd block (cross-checks test_gpt_param_count).
    model = GPT(ModelConfig())
    assert model.lm_head.weight.data_ptr() == model.wte.weight.data_ptr()
```

**Dedup-by-storage counting helper** (`test_ablation_config.py` lines 24–29) — reuse for "exactly one Fisher entry per storage":

```python
def count_parameters(model) -> int:
    # Dedup by storage pointer: a tied wte/lm_head tensor maps to one key, counted once.
    seen = {}
    for p in model.parameters():
        seen[p.data_ptr()] = p.numel()
    return sum(seen.values())
```

Fisher variant: assert `"lm_head.weight" not in fisher and "wte.weight" in fisher`, and that `len(fisher)` equals the number of distinct `data_ptr`s among `model.parameters()`.

**RNG-purity assertion** — capture/compare the global-state triple using the loop's own idiom (`training/loop.py` lines 48–50):

```python
def _rng_state():
    """Snapshot the full (python/numpy/torch) global RNG state."""
    return (random.getstate(), np.random.get_state(), torch.get_rng_state())
```

Snapshot before/after `estimate_fisher`, assert bit-equality (note: `np.random.get_state()` returns a tuple with an array — compare element-wise or via `np.random.get_state(legacy=False)`).

**Tiny-model fixture pattern** (`tests/test_lora_artifact.py` lines 62–65) — shrink everything except the locked vocab/eos:

```python
def _tiny_config() -> ModelConfig:
    # vocab_size/eos_id stay at the LOCKED defaults (8192/8184) so the artifact's embedded
    # config matches production shape; everything else is shrunk for a cheap CPU fixture.
    return ModelConfig(block_size=32, n_layer=1, n_head=2, n_embd=16)
```

The anti-batched-Fisher discriminating fixture (per-example ≠ batched on opposing gradients): RESEARCH.md Code Example 2 — no codebase analog (see No Analog Found).

---

### `tests/test_ewc_penalty.py` (test)

**Analog:** `tests/test_assemble_loss.py` (exact-equality scalar-tensor oracle style).

**Exact-equality oracle style** (`test_assemble_loss.py` lines 16–31) — `torch.equal` on hand-computed scalars, one behavior per test, comment naming the contract:

```python
def test_empty_is_identity():
    # No penalties -> the base loss passes through unchanged (the M1 path).
    x = torch.tensor(2.5)
    assert torch.equal(assemble_loss(x, ()), x)


def test_additive_with_single_penalty():
    # One penalty adds exactly (the EWC seam: base + lambda * fisher term).
    x, p = torch.tensor(2.0), torch.tensor(0.5)
    assert torch.equal(assemble_loss(x, (p,)), torch.tensor(2.5))
```

Apply to: quadratic-form oracle vs hand-computed value on a toy param dict; exact-zero at θ* (`penalty.item() == 0.0` — equality, not allclose, on CPU); λ linearity (`penalty(2λ) == 2 * penalty(λ)`); gradient check (`torch.autograd.grad` of the penalty equals `λ·F·(θ−θ*)`).

---

### `tests/test_loop_penalty_fn.py` (test)

**Analogs:** `tests/test_resume_curve.py` (trajectory-equality on the committed fixture), `tests/test_train_loop.py` (accum-vs-big-batch equivalence — directly reusable for the penalty-once-per-step pin).

**Trajectory-equality template** (`test_resume_curve.py` lines 23–24, 38–79) — committed fixture + `seed_everything(1234)` + two `train()` runs + loss-and-param comparison:

```python
CORPUS_PATH = pathlib.Path(__file__).parent / "fixtures" / "bigram_corpus.txt"
EOS_ID = 8184


def test_resume_identical_trajectory(tmp_path):
    cfg = TrainConfig(lr=1e-2, warmup_steps=2, max_steps=6, batch_size=4)

    # --- Reference: an uninterrupted run of all max_steps ---
    seed_everything(1234)
    ref_model = _build()
    ref = train(
        train_config=cfg,
        model=ref_model,
        corpus_path=CORPUS_PATH,
        eos_id=EOS_ID,
        return_final_loss=True,
    )
    ref_param = ref_model.token_embedding_table.weight.detach().clone()
    ...
    assert abs(float(resumed) - float(ref)) < 1e-6
    assert torch.allclose(resumed_param, ref_param, atol=1e-6)
```

For Phase 10: `penalty_fn=None` run vs kwarg-omitted run vs the pre-edit golden trajectory fixture (per RESEARCH Pitfall 6, the golden JSON of per-step losses + a param checksum must be captured BEFORE the loop edit). Use **exact** equality for the default-path pin (same process, same seed, identical code path — `torch.equal`, not 1e-6).

**Penalty-once-per-accum-step pin** (`test_train_loop.py` lines 66–75) — the directly reusable idiom (the synthetic data path slices one big fixed batch into micro-batches, so accum=N is provably the same data as one N×-bigger batch):

```python
def test_grad_accum_equivalent_to_big_batch():
    # N micro-batches with grad_accum_steps=N must match one big batch within tolerance ...
    cfg_accum = TrainConfig(max_steps=1, warmup_steps=0, grad_accum_steps=4, batch_size=4)
    cfg_big = TrainConfig(max_steps=1, warmup_steps=0, grad_accum_steps=1, batch_size=16)
    runtime = RuntimeConfig(device="cpu")

    accum_loss = train(train_config=cfg_accum, runtime_config=runtime, return_final_loss=True)
    big_loss = train(train_config=cfg_big, runtime_config=runtime, return_final_loss=True)
    assert abs(float(accum_loss) - float(big_loss)) < 1e-3
```

Phase 10 variant: same two-config comparison but with `penalty_fn=EWCPenalty(...)` at a displaced θ — post-step parameter deltas must match between accum=1 and accum=4 (proves the penalty is counted exactly once per optimizer step, before `/accum`).

---

### `tests/test_fisher_checkpoint.py` (test)

**Analogs:** `tests/test_checkpoint.py::test_open_dict_extensible` (the `**extra` round-trip — this test already uses `fisher=` as its example key), `tests/test_lora_artifact.py` (cache schema-gate tests, if the cache loader ships).

**`**extra` round-trip template** (`test_checkpoint.py` lines 83–105):

```python
def test_open_dict_extensible(tmp_path):
    # An arbitrary extra key (the M2 EWC seam: fisher/theta_star) must round-trip,
    # and schema_version must be present — proving the dict is OPEN.
    model, opt, sched = _build()
    ckpt_path = tmp_path / "extra.pt"
    save_checkpoint(
        ckpt_path,
        model=model,
        optimizer=opt,
        scheduler=sched,
        step=0,
        model_config=ModelConfig(),
        train_config=TrainConfig(),
        git_sha="deadbeef",
        fisher={"x": 1},
    )
    raw = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    assert raw["schema_version"] == CKPT_SCHEMA_VERSION
    assert raw["fisher"] == {"x": 1}
```

Phase 10 upgrades the placeholder to real tensors: save `fisher=`, `theta_star=`, `ewc_lambda=`, `fisher_meta=`; reload via `load_checkpoint`; compare keys + values with `torch.equal` (NOT `data_ptr` — pointers legitimately change across serialization, per RESEARCH Pattern 3).

**Cache schema-gate tests** (`test_lora_artifact.py` lines 97–138) — if `export_fisher`/`load_fisher` ship, mirror these three test shapes:

```python
def test_artifact_safe_loads_with_exact_keys(adapter_artifact):
    _, _, path, _, _ = adapter_artifact
    # The raw restricted-unpickler load SUCCEEDING is itself the safe-load bar (T-09-07):
    loaded = torch.load(path, map_location="cpu", weights_only=True)
    assert set(loaded.keys()) == ADAPTER_KEYS


def test_schema_version_mismatch_raises(adapter_artifact, tmp_path):
    _, _, _, art, _ = adapter_artifact
    bad = dict(art)
    bad["schema_version"] = 999
    bad_path = tmp_path / "bad_schema.pt"
    torch.save(bad, bad_path)
    with pytest.raises(ValueError, match="schema_version"):
        load_adapter(bad_path)


@pytest.mark.parametrize("dropped", ["adapter", "lora_config", "base_fingerprint"])
def test_malformed_artifact_missing_key_raises(adapter_artifact, tmp_path, dropped):
    ...
    with pytest.raises(ValueError, match=dropped):
        load_adapter(bad_path, expected_fingerprint=fp)
```

---

## Shared Patterns

### Module docstring house style
**Source:** every module — exemplary: `src/personacore/training/loss.py` lines 1–14, `src/personacore/checkpoint.py` lines 1–21
**Apply to:** all new modules, scripts, and test files
Multi-paragraph docstring naming requirement IDs (EWC-01/EWC-02), locked decisions (D-01..D-05), and the load-bearing properties — never a one-liner. Test files additionally enumerate pinned behaviors (see `test_lora_artifact.py` lines 1–30).

### RNG snapshot/restore triple
**Source:** `src/personacore/training/loop.py` lines 48–58
**Apply to:** `tests/test_fisher.py` (RNG-purity assertion); design constraint on `fisher.py` (must pass it)
```python
def _rng_state():
    """Snapshot the full (python/numpy/torch) global RNG state."""
    return (random.getstate(), np.random.get_state(), torch.get_rng_state())


def _restore_rng(state):
    py_state, np_state, torch_state = state
    random.setstate(py_state)
    np.random.set_state(np_state)
    torch.set_rng_state(torch_state)
```

### Trusted vs safe load split
**Source:** `src/personacore/checkpoint.py` lines 95–98 (trusted `weights_only=False` with justifying comment) and lines 156–162 / 208–214 (safe `weights_only=True` choke points)
**Apply to:** `scripts/estimate_fisher_tinystories.py` (trusted `best.pt` read), the Fisher cache loader (safe), `tests/test_fisher_checkpoint.py`
Every `weights_only=False` call carries the "TRUSTED-only file (own checkpoint)" comment; every shareable artifact loads `weights_only=True` through exactly one choke point with a schema gate.

### Provenance fingerprint trio
**Source:** `scripts/train_adapter_smoke.py` lines 183–187; `checkpoint.py` `export_adapter` docstring lines 176–179
**Apply to:** Fisher cache `anchor_fingerprint`, `fisher_meta` anchor provenance
`{"git_sha": blob["git_sha"], "step": blob["step"], "val_loss": blob["val_loss"]}` — always READ from the anchor checkpoint, never recomputed.

### SystemExit-not-assert in scripts
**Source:** `scripts/train_adapter_smoke.py` lines 102–106, 160–175
**Apply to:** every proof check in `scripts/estimate_fisher_tinystories.py`
`raise SystemExit(f"...")` with a message naming the requirement/pitfall — never a `-O`-strippable `assert`.

### Seeding + determinism in tests
**Source:** `tests/test_resume_curve.py` lines 42, 55 (`seed_everything(1234)` before each compared run); `tests/test_lora_artifact.py` line 81 (`torch.manual_seed(1234)` for deterministic tiny weights)
**Apply to:** all new test files comparing trajectories or building fixtures
CPU-only, GPU-free (house discipline — no `cuda`/`mps` in the suite; real-device proof lives in the smoke script).

## No Analog Found

Files/components with no close codebase match (planner should use RESEARCH.md patterns instead):

| Component | Role | Data Flow | Reason | Use Instead |
|-----------|------|-----------|--------|-------------|
| Per-example grad² accumulation loop (core of `fisher.py`) | service | batch | No gradient-statistics code exists; `_optimizer_step` aggregates gradients (the exact thing Fisher must NOT do) | RESEARCH.md Code Example 1 (verified skeleton) |
| Hand-rolled Spearman + half-split convergence stats | utility | transform | No statistics code in the codebase; scipy is not a dependency | RESEARCH.md Code Example 6 (double-argsort + `np.corrcoef`, fp64 on CPU) |
| Anti-batched-Fisher discriminating test fixture | test | — | No existing test distinguishes per-example from batched gradients | RESEARCH.md Code Example 2 (opposing-gradients fixture) |
| Golden-trajectory JSON fixture (pre-edit capture) | test fixture | file-I/O | Existing trajectory tests compare two in-process runs, not a committed golden file | RESEARCH Pitfall 6 prescription: 5-step seeded fixture run → per-step losses + param checksum → committed JSON, captured BEFORE the loop edit |

## Metadata

**Analog search scope:** `src/personacore/` (all packages), `scripts/`, `tests/`
**Files read in full:** 14 (`training/loop.py`, `training/loss.py`, `training/data.py`, `checkpoint.py`, `lora/__init__.py`, `lora/config.py`, `scripts/train_adapter_smoke.py`, `tests/test_assemble_loss.py`, `tests/test_gpt_weight_tying.py`, `tests/test_ablation_config.py`, `tests/test_train_loop.py`, `tests/test_resume_curve.py`, `tests/test_checkpoint.py`, `tests/test_lora_artifact.py`)
**Pattern extraction date:** 2026-06-12
**Note:** RESEARCH.md line references (splice at loop.py:136–139, `**extra` reservation at checkpoint.py:77) were re-verified against the files read in this session and are accurate.
