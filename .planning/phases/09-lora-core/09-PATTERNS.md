# Phase 9: LoRA Core - Pattern Map

**Mapped:** 2026-06-11
**Files analyzed:** 12 (11 new + 1 modified)
**Analogs found:** 11 / 12 (1 partial — `lora/inject.py` has no single exact analog; composed from three in-repo idioms)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/personacore/lora/__init__.py` | package init | — | `src/personacore/model/__init__.py` | exact |
| `src/personacore/lora/config.py` | config (dataclass) | — | `src/personacore/config.py` (`ModelConfig`/`TrainConfig`) | exact |
| `src/personacore/lora/layer.py` | model component (`nn.Module`) | transform (tensor forward) | `src/personacore/model/gpt.py` (`LayerNorm`, `MLP`) | role-match |
| `src/personacore/lora/inject.py` | utility (model-tree orchestration) | transform | composed: `gpt.py:175-177` + `tests/test_gpt_lora_seam.py:22` + `loop.py:48-58` | partial |
| `src/personacore/checkpoint.py` (MODIFIED, additive) | service (artifact I/O) | file-I/O | itself — `export_slim`/`load_slim` (lines 115-160) | exact |
| `scripts/train_adapter_smoke.py` | script (thin driver) | batch (training run) | `scripts/pretrain_tinystories.py` (primary), `scripts/export_slim.py` (secondary) | exact |
| `tests/test_lora_layer.py` | test | — | `tests/test_ablation_config.py` + `_tiny_config()` from `tests/test_slim_checkpoint.py` | role-match |
| `tests/test_lora_inject.py` | test | — | `tests/test_gpt_lora_seam.py` + `test_gpt_weight_tying.py` + `test_gpt_param_count.py` | exact |
| `tests/test_lora_toggle.py` | test | — | `tests/test_ablation_config.py` (bit-identity) + `test_gpt_attention_equiv.py` (two-path compare) | role-match |
| `tests/test_lora_merge.py` | test | — | `tests/test_gpt_attention_equiv.py` (two-path fp-tolerance equivalence) | exact |
| `tests/test_lora_artifact.py` | test | file-I/O | `tests/test_slim_checkpoint.py` | exact |
| `tests/test_lora_training.py` | test | batch | `tests/test_resume_curve.py` (kill+resume trajectory) | exact |

## Pattern Assignments

### `src/personacore/lora/__init__.py` (package init)

**Analog:** `src/personacore/model/__init__.py` (entire file, lines 1-10)

```python
"""From-scratch model package (D-09) — public import surface.

Phase 3 ships the disposable bigram baseline; Phase 4 adds ``from .gpt import GPT`` here
unchanged, honoring the same LOCKED ``forward(idx, targets=None) -> (logits, loss)`` contract.
"""

from .bigram import BigramLanguageModel
from .gpt import GPT

__all__ = ["BigramLanguageModel", "GPT"]
```

Copy: short docstring naming the phase/decision, relative imports only, explicit `__all__`.
For `lora/`: re-export `LoRAConfig`, `TARGET_PROJECTIONS`, `LoRALinear`, `inject_lora`,
`mark_only_lora_trainable`, `set_adapter_enabled`, `adapter_disabled`, `eject_adapter`,
`merge_lora`, `unmerge_lora`, `merged_state_dict`, `lora_state_dict`, `snapshot_params`.

---

### `src/personacore/lora/config.py` (config, dataclass)

**Analog:** `src/personacore/config.py`

**Module docstring + dataclass pattern** (lines 1-16, 76-94) — docstring leads with the decision
IDs the module implements; fields carry inline comments tying them to requirements:

```python
from dataclasses import dataclass, field          # line 16 — house import

@dataclass
class ModelConfig:
    """Model-sizing hyperparameters.

    ``vocab_size`` is now LOCKED by Phase 2 (the BPE tokenizer): 8192 is the load-bearing
    deliverable ... it travels into the checkpoint automatically because ``save_checkpoint``
    already ``asdict``s ``model_config``.
    """

    vocab_size: int = 8192  # LOCKED by Phase 2 (was the Phase-1 placeholder).
    eos_id: int = 8184  # shared atomic EOS id, recorded in checkpoint (D-03); top-pinned (D-03a).
    block_size: int = 256
    ...
    weight_tying: bool = True  # EVAL-03: False enables the no-weight-tying ablation (untied head).
```

**Module-level canonical tuple** — mirror the constant style of
`src/personacore/training/loop.py:45` (`CSV_FIELDNAMES = ["step", ...]`) and
`tests/test_gpt_lora_seam.py:16`:

```python
PROJECTIONS = ("q_proj", "k_proj", "v_proj", "c_proj", "fc_in", "fc_out")
```

`TARGET_PROJECTIONS` in `lora/config.py` must equal this tuple; a cross-pin test asserts
equality against the seam test's `PROJECTIONS` (production code never imports from `tests/`).

For `LoRAConfig` defaults per RESEARCH: `r=8, alpha=16.0, dropout=0.0, targets=TARGET_PROJECTIONS`
(use `field(default_factory=...)` or a tuple default — tuples are immutable, direct default is fine).
Config travels as `dataclasses.asdict()` primitives (precedent: `checkpoint.py:66-67`).

---

### `src/personacore/lora/layer.py` (`LoRALinear`, nn.Module)

**Analog:** `src/personacore/model/gpt.py` — the house `nn.Module` style.

**Class shape + docstring style** — `LayerNorm` (lines 32-49) is the template for a small
hand-rolled module with decision-ID docstring, explicit `nn.Parameter` construction, and an
explicit-math forward:

```python
class LayerNorm(nn.Module):
    """Hand-rolled LayerNorm (D-09).

    POPULATION variance (``unbiased=False``) + ``eps=1e-5`` to match ``nn.LayerNorm``'s defaults
    (RESEARCH Pitfall 6 — an ``unbiased=True`` bug diverges at ~1e-3). ...
    """

    def __init__(self, ndim: int, eps: float = 1e-5):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(ndim))
        self.bias = nn.Parameter(torch.zeros(ndim))
        self.eps = eps

    def forward(self, x):
        mean = x.mean(dim=-1, keepdim=True)
        var = x.var(dim=-1, keepdim=True, unbiased=False)  # population variance (== nn.LayerNorm)
        return (x - mean) / torch.sqrt(var + self.eps) * self.weight + self.bias
```

**Dropout-as-member pattern** — `MLP` (lines 118-129): `self.dropout = nn.Dropout(config.dropout)`
constructed in `__init__`, applied in forward; `nn.Dropout` owns train/eval gating.

**Init convention** — `_init_weights` (lines 186-191): house Gaussian std is 0.02:

```python
if isinstance(module, nn.Linear):
    torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
```

`lora_A` uses `nn.init.normal_(self.lora_A, mean=0.0, std=0.02)` (matches house init);
`lora_B` is `torch.zeros(out_features, r)` (identity gate). Create A/B as fresh explicit-shape
tensors, never `weight.T` views (PITFALLS P5).

**Autocast-safety rule** — gpt.py module docstring (lines 12-14): never call `torch.cuda.*`,
never manual dtype casting. `LoRALinear` inherits this rule verbatim.

**`enabled`/`merged`** are plain Python bool attributes (NOT buffers/Parameters) so they never
enter `state_dict()` — there is no in-repo buffer-vs-attr precedent to copy; this is a locked
research decision (RESEARCH Pattern 1). Note gpt.py's non-persistent buffer precedent
(lines 80-86, `persistent=False`) exists but plain attrs are the chosen mechanism here.

**Verified reference implementation:** 09-RESEARCH.md "Code Examples → LoRALinear core"
(lines 365-384) — copy that skeleton; it already encodes scale-single-source, D-05 flag gating,
and dropout placement.

---

### `src/personacore/lora/inject.py` (injection / freeze / toggle / merge orchestration)

**Analog:** partial — composed from three in-repo idioms plus verified RESEARCH reference code.

**1. Name-suffix parameter traversal** — `src/personacore/model/gpt.py:175-177` (the
residual-scaled-init override) is the house pattern for "walk named params, act on name match":

```python
for name, p in self.named_parameters():
    if name.endswith("c_proj.weight") or name.endswith("fc_out.weight"):
        torch.nn.init.normal_(p, mean=0.0, std=0.02 / math.sqrt(2 * config.n_layer))
```

`mark_only_lora_trainable` is the same shape: `model.requires_grad_(False)` then re-enable
params whose name contains `"lora_"`.

**2. Module-tree scan + allowlist** — `tests/test_gpt_lora_seam.py:22` shows the
`named_modules()` + `isinstance(m, nn.Linear)` traversal; `inject_lora` inverts it into the
allowlist form (iterate `model.modules()` as parents, `getattr(parent, name)` for each name in
`cfg.targets`, `setattr` the wrapper). NEVER a bare `isinstance` scan — that picks up the tied
`lm_head` (PITFALLS P1). Verified reference: 09-RESEARCH.md lines 388-404.

**3. Snapshot/restore helper idiom** — `src/personacore/training/loop.py:48-58`
(`_rng_state`/`_restore_rng`) is the house "snapshot state, restore it later" helper pair;
`snapshot_params(model)` follows the same shape using the clone idiom from
`tests/test_resume_curve.py:51`:

```python
ref_param = ref_model.token_embedding_table.weight.detach().clone()
```

→ `{n: p.detach().clone() for n, p in model.named_parameters()}`.

**4. Exception-safe scoped state** — for `adapter_disabled(model)` there is no existing context
manager in the codebase. Nearest precedent for exception-safe restore is the `try/finally`
in `train()` (`loop.py:307-383`, CSV close). Use stdlib `@contextlib.contextmanager` with
`try/yield/finally` re-enable; per-module prior `enabled` values captured before disable.

**5. Merge/unmerge** — no in-repo analog; copy the verified RESEARCH reference
(09-RESEARCH.md lines 445-459): `@torch.no_grad()`, stored-clone `_w0` (plain attr),
`add_`/`copy_` in-place ops, asserts on `merged` state. `merge_lora` asserts
`model.training is False` (Pitfall 6); `eject_adapter` asserts unmerged.

**Import direction:** `inject.py` imports relatively (`from .config import ...`,
`from .layer import ...` — precedent `loop.py:41-43` `from .data import ...`) and never
imports `checkpoint.py`. `checkpoint.py` never imports `lora/` (locked dependency direction).

---

### `src/personacore/checkpoint.py` (MODIFIED — additive only)

**Analog:** itself. `export_adapter`/`load_adapter` mirror `export_slim`/`load_slim` verbatim
in style, placed after them; `ADAPTER_SCHEMA_VERSION` beside `SLIM_SCHEMA_VERSION`.

**Schema-version constant** (lines 29-30):

```python
CKPT_SCHEMA_VERSION = 1
SLIM_SCHEMA_VERSION = 1  # slim INFERENCE artifact schema (DEMO-02), independent of the full one.
```

**Safe-load choke point + raise style** — `load_slim` (lines 147-160) is the exact template:

```python
def load_slim(path, *, map_location="cpu") -> dict:
    """Load the slim INFERENCE checkpoint under the locked safe-load bar (T-08-01).

    ``weights_only=True`` is the restricted unpickler — tensors + primitive containers only,
    ZERO code execution on load. Every slim consumer (demo, notebook, tests) goes through this
    single choke point; the module docstring reserved exactly this split in Phase 1.
    """
    loaded = torch.load(path, map_location=map_location, weights_only=True)
    if loaded.get("schema_version") != SLIM_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported slim checkpoint schema_version {loaded.get('schema_version')!r} in "
            f"{path} (expected {SLIM_SCHEMA_VERSION}). Re-export with scripts/export_slim.py."
        )
    return loaded
```

**Export + return-the-dict style** — `export_slim` (lines 135-144): build the dict with
`schema_version` first, `torch.save`, return the dict so callers can print/inspect.

**Provenance fingerprint trio** — `export_slim` lines 137-141 carry
`model_config` / `git_sha` / `step` (QA-02). The adapter's `base_fingerprint`
(`{"git_sha": ..., "step": ..., "val_loss": ...}`) reads these same keys from the base
checkpoint. `git_sha` source: `src/personacore/provenance.py:15-31` (never raises; returns
`"unknown"` default).

**Warn-but-load (D-02)** — `import warnings` + `warnings.warn(...)` on fingerprint mismatch;
no in-repo `warnings` precedent, copy the verified RESEARCH reference (09-RESEARCH.md
lines 425-440) which already matches house style.

**Keep:** `checkpoint.py` takes plain dicts (`adapter`, `lora_config`, `base_fingerprint`) —
never imports `lora/` (mirrors how `export_slim` takes a path, not a model).

**Existing tests guard this file:** `tests/test_checkpoint.py` + `tests/test_slim_checkpoint.py`
must stay green — the change is purely additive.

---

### `scripts/train_adapter_smoke.py` (thin training driver)

**Analog (primary):** `scripts/pretrain_tinystories.py` — the only existing training-run script
against real artifacts.

**MPS env guard before torch import** (lines 30-34):

```python
# An uncovered MPS op falls back to CPU rather than crashing the multi-hour run (T-05-04).
# Set BEFORE importing torch so the backend honors it for the whole process.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import torch  # noqa: E402  (must follow the MPS-fallback env set above)
```

**No-CLI `_REPO_ROOT` constants** (lines 43-49):

```python
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"
TRAIN_BIN = _REPO_ROOT / "data" / "train.bin"  # LOCAL memmap (not a Kaggle dataset mount)
...
CKPT_PATH = _REPO_ROOT / "checkpoints" / "latest.pt"  # gitignored (*.pt / checkpoints/)
```

Smoke script needs its own gitignored outputs: e.g. `checkpoints/adapter_smoke.pt`,
`checkpoints/adapter.pt`, `logs/adapter_smoke.csv` — NEVER append to `logs/run.csv`
(ARCHITECTURE anti-pattern 3).

**Named tuned constants block** (lines 51-59 style): `LR`, `BATCH_SIZE`, `MAX_STEPS` (~50-100),
`WEIGHT_DECAY = 0.0` (adapter runs — RESEARCH Pattern 3).

**main() skeleton** (lines 62-114): `preflight_device(strict=True)` gate → `FileNotFoundError`
on missing inputs (also `export_slim.py:32-35` precedent) → `seed_everything(...)` →
build configs → `train(...)` keyword call. Phase-9 insertion: between model build and
`train()`, do `load_checkpoint`/manual base load → `inject_lora` → `mark_only_lora_trainable`
→ `snapshot_params` (canary) — the load→inject→freeze ordering is load-bearing.

**Post-run own-checkpoint read** (lines 116-127):

```python
blob = torch.load(BEST_PATH, weights_only=False)  # own trusted file.
```

Smoke script ends with the canary asserts (trainables moved, frozen bit-untouched via
`torch.equal`) and `export_adapter(...)`; assert inline and exit non-zero on failure
(RESEARCH Open Q2 recommendation).

**Analog (secondary):** `scripts/export_slim.py` — the print-what-shipped tail (lines 36-40):

```python
slim = export_slim(BEST_PATH, SLIM_PATH)
size_mb = SLIM_PATH.stat().st_size / 1e6
print(f"[export_slim] wrote {SLIM_PATH} ({size_mb:.1f} MB)")
```

(The adapter export print should show the ~1.3 MB size — it IS the persona-file story.)

**`train()` call surface** — `src/personacore/training/loop.py:150-174` keyword-only signature;
relevant kwargs: `train_config`, `runtime_config`, `model` (the injected GPT), `model_config`,
`train_bin`/`val_bin`, `log_path`, `checkpoint_path`, `resume_from`, `max_steps_override`.
Optimizer is constructed inside `train()` over `model.parameters()` (lines 234-236) — verified
frozen-param safe; do not modify the loop.

---

### `tests/test_lora_layer.py` (unit: B=0 identity, scale, dropout, contiguity)

**Analog:** `tests/test_ablation_config.py` (construct-and-assert style) +
`tests/test_slim_checkpoint.py:_tiny_config` (cheap CPU fixture).

**Tiny-config fixture** (`test_slim_checkpoint.py:49-52`) — reuse verbatim:

```python
def _tiny_config() -> ModelConfig:
    # vocab_size/eos_id stay at the LOCKED defaults (8192/8184) so the artifact's embedded
    # config matches production shape; everything else is shrunk for a cheap CPU fixture.
    return ModelConfig(block_size=32, n_layer=1, n_head=2, n_embd=16)
```

**Module docstring style** (every test file): purpose line with requirement IDs +
"CPU-only, GPU-free." note (`test_gpt_lora_seam.py:1-9` template).

**Bit-identity assertion culture:** `torch.equal` for bit-identity (zero-delta at init: wrap a
seeded `nn.Linear`, assert wrapped(x) `torch.equal` base(x)); `torch.allclose(atol=...)` only
where fp math forces tolerance. Seeding: `torch.manual_seed(1234)` before model construction
(`test_slim_checkpoint.py:76`).

---

### `tests/test_lora_inject.py` (unit: allowlist, ordering, tied tensor, param count)

**Analog:** three exact-match test files.

**Allowlist cross-pin** — `tests/test_gpt_lora_seam.py:16` is the canonical tuple to pin against:

```python
PROJECTIONS = ("q_proj", "k_proj", "v_proj", "c_proj", "fc_in", "fc_out")
```

Add: `assert TARGET_PROJECTIONS == PROJECTIONS` (import the seam test's tuple in the test, or
restate the literal — tests may import tests; production code may not).

**Tied-tensor `data_ptr` assert** — `tests/test_gpt_weight_tying.py:15-19`, reused verbatim
post-injection:

```python
model = GPT(ModelConfig())
assert model.lm_head.weight.data_ptr() == model.wte.weight.data_ptr()
```

**Param-count dedup idiom** — `tests/test_gpt_param_count.py:16-21`:

```python
def count_parameters(model) -> int:
    # Dedup by storage pointer: the same tensor (tied wte/lm_head) maps to one key, counted once.
    seen = {}
    for p in model.parameters():
        seen[p.data_ptr()] = p.numel()
    return sum(seen.values())
```

Trainable census variant: filter `p.requires_grad`; assert `== cfg.r * n_layer * 18 * n_embd`
(= 331,776 at production defaults; compute from the tiny config in CI tests).

**Load→inject→freeze ordering pin** — load real-shaped weights into a vanilla tiny GPT, inject,
assert post-injection logits `torch.equal` pre-injection logits (B=0 + loaded base).

---

### `tests/test_lora_toggle.py` (unit: enable/disable bit-identity, context manager, eject)

**Analog:** `tests/test_ablation_config.py:32-36` (the bit-identity-to-base default culture):

```python
def test_defaults_unchanged():
    """Defaults reproduce today's arch: tied head + 13,891,584 params."""
    model = GPT(ModelConfig())
    assert model.lm_head.weight.data_ptr() == model.wte.weight.data_ptr()
    assert count_parameters(model) == 13_891_584
```

Toggle shape: seeded tiny GPT → capture base logits on a fixed batch → inject (trained-ish: nudge
`lora_B` so the delta is nonzero) → `set_adapter_enabled(model, False)` → assert logits
`torch.equal` base → re-enable → assert delta returns. Context-manager exception safety:
`pytest.raises` around a `with adapter_disabled(model):` body that raises; assert `enabled`
restored. Eject: `eject_adapter(model)` → assert every wrapped name is plain `nn.Linear` again
and logits `torch.equal` vanilla.

Two-instance fixed-input comparison pattern from `tests/test_gpt_attention_equiv.py:28-33`
(`torch.randint` fixed batch, `torch.no_grad`, compare logits).

---

### `tests/test_lora_merge.py` (unit: merge equivalence, bit-exact unmerge, pure merged_state_dict)

**Analog:** `tests/test_gpt_attention_equiv.py` (exact data-flow match: two computation paths,
shared weights, fp tolerance) — lines 21-33:

```python
def test_manual_attention_matches_sdpa():
    torch.manual_seed(0)
    cfg = ModelConfig(block_size=16)
    m_manual = GPT(cfg, attn_impl="manual").eval()
    m_sdpa = GPT(cfg, attn_impl="sdpa").eval()
    m_sdpa.load_state_dict(m_manual.state_dict())  # SAME weights, only the attn path differs.

    idx = torch.randint(0, cfg.vocab_size, (2, 12))
    with torch.no_grad():
        la, _ = m_manual(idx)
        lb, _ = m_sdpa(idx)

    assert torch.allclose(la, lb, atol=1e-5)
```

Copy: seeded construction, `.eval()` (mandatory — dropout off, also satisfies the
`merge_lora` training-mode assert), `torch.no_grad()`, `torch.allclose(atol=1e-5)` for
merged-vs-live equivalence. Unmerge round-trip uses `torch.equal` on `base.weight`
(bit-exact via stored clone, D-07). `merged_state_dict` purity: snapshot
`model.state_dict()` before, call, assert unchanged (`torch.equal` per tensor) AND assert the
returned key set `== GPT(cfg).state_dict().keys()` (vanilla key-set parity).

---

### `tests/test_lora_artifact.py` (unit: weights_only round-trip, schema raise, fingerprint warn, two-artifact load)

**Analog:** `tests/test_slim_checkpoint.py` — near line-for-line template.

**Module-scoped artifact fixture** (lines 71-95): build tiny seeded GPT → hand-build/export
artifact into `tmp_path_factory.mktemp(...)` once, share across tests.

**The raw safe-load IS the assertion** (lines 98-104):

```python
def test_export_strips_training_state(slim_paths):
    _, slim_path = slim_paths
    # The raw restricted-unpickler load SUCCEEDING is itself the safe-load bar (T-08-01).
    loaded = torch.load(slim_path, map_location="cpu", weights_only=True)
    assert set(loaded.keys()) == SLIM_KEYS
```

Adapter version: exact key set `{"schema_version", "adapter", "lora_config", "base_fingerprint"}`;
also assert no `"lora_"`-free tensor keys leaked (base weights never in the persona file).

**Exact-key-set constants** (lines 45-46 style): module-level `ADAPTER_KEYS = {...}`.

**Schema-mismatch raise test:** save artifact with `schema_version: 999`, `pytest.raises(ValueError)`
on `load_adapter` (mirrors `load_slim` contract; no existing slim test does this — the raise
style is `checkpoint.py:156-159`).

**Fingerprint warn-but-load (D-02):** `pytest.warns(UserWarning)` — no in-repo `pytest.warns`
precedent; standard pytest, no fixture needed.

**Provenance round-trip** (lines 122-129): assert `git_sha`/`step` travel through the artifact.

**skipif-gated real-artifact test** (lines 168-178) — for the optional real two-artifact load:

```python
@pytest.mark.skipif(not REAL_SLIM.exists(), reason="real slim artifact not present (CI)")
def test_real_slim_artifact_generates_on_cpu():
    loaded = load_slim(REAL_SLIM)
    model = GPT(ModelConfig(**loaded["model_config"]))
    model.load_state_dict(loaded["model"])
```

Two-artifact-load mechanism test (tiny fixtures, tmp_path): `export_slim` a tiny full ckpt →
`load_slim` → rebuild GPT from embedded config → `inject_lora` from artifact's `lora_config`
→ key-audited adapter load → assert logits `torch.equal` the exporting model's logits.

---

### `tests/test_lora_training.py` (unit: canary, frozen-base bit-untouched, kill+resume)

**Analog:** `tests/test_resume_curve.py:38-79` — the kill+resume trajectory template:

```python
def test_resume_identical_trajectory(tmp_path):
    cfg = TrainConfig(lr=1e-2, warmup_steps=2, max_steps=6, batch_size=4)

    # --- Reference: an uninterrupted run of all max_steps ---
    seed_everything(1234)
    ref_model = _build()
    ref = train(train_config=cfg, model=ref_model, corpus_path=CORPUS_PATH,
                eos_id=EOS_ID, return_final_loss=True)
    ref_param = ref_model.token_embedding_table.weight.detach().clone()

    # --- Resumed: run half, checkpoint, KILL, fresh model, resume to the end ---
    seed_everything(1234)
    half_model = _build()
    ckpt_path = tmp_path / "latest.pt"
    train(..., max_steps_override=3, checkpoint_path=ckpt_path)

    fresh_model = _build()
    resumed = train(..., resume_from=ckpt_path, return_final_loss=True)

    assert abs(float(resumed) - float(ref)) < 1e-6
    assert torch.allclose(resumed_param, ref_param, atol=1e-6)
```

Adapter variant: `_build()` becomes vanilla tiny GPT → `inject_lora` → `mark_only_lora_trainable`
(the deterministic reconstruction order — identical on resume). Use the committed fixture
corpus path (`tests/fixtures/bigram_corpus.txt`, `test_resume_curve.py:23`) or a tiny in-test
batch; `TrainConfig(weight_decay=0.0, ...)` for adapter runs.

Canary test: `snapshot_params(model)` before `train(max_steps_override=1)`; after — for each
named param: `requires_grad` → `assert not torch.equal(p, before[n])`; frozen →
`assert torch.equal(p, before[n])` (bit-level, LORA-02). Fresh-optimizer-state check: after a
step, optimizer state keys cover only A/B params.

---

## Shared Patterns

### Module docstring discipline
**Source:** every file (e.g. `src/personacore/checkpoint.py:1-21`, `tests/test_gpt_lora_seam.py:1-9`)
**Apply to:** all new files
Every module opens with a docstring naming the requirement/decision IDs it implements
(`(LORA-01)`, `(D-05)`), explains *why* the design is load-bearing, and — for tests —
ends with "CPU-only, GPU-free." Inline comments cite decision IDs and pitfalls.

### Import conventions
**Source:** `gpt.py:23-29`, `loop.py:29-43`, `test_slim_checkpoint.py:29-39`
**Apply to:** all new files
- Within-package: relative (`from ..config import ModelConfig`, `from .data import get_batch`)
- Cross-package in src: absolute (`from personacore.checkpoint import save_checkpoint`)
- Tests/scripts: absolute `from personacore.X import Y` only
- Order: stdlib → third-party (`numpy`, `torch`) → first-party (ruff rule I enforces;
  line-length 100)

### Bit-identity vs tolerance assertion split
**Source:** `test_gpt_attention_equiv.py:33` (`torch.allclose(atol=1e-5)`),
`test_resume_curve.py:79`, weight-tying/`torch.equal` culture
**Apply to:** all test files
`torch.equal` for everything structurally bit-exact (zero-delta init, toggle round-trip,
unmerge restore, frozen params); `torch.allclose(atol=1e-5)` on CPU ONLY for the
merged-forward equivalence where fp non-associativity forces it.

### Safe-load choke point + schema version
**Source:** `checkpoint.py:147-160` (`load_slim`)
**Apply to:** `load_adapter`, `tests/test_lora_artifact.py`
`torch.load(..., weights_only=True)` at exactly one function; `schema_version` checked with a
`ValueError` whose message names the actual value, expected value, and the re-export remedy.

### Tiny CPU fixture
**Source:** `tests/test_slim_checkpoint.py:49-52`
**Apply to:** all six test files
`ModelConfig(block_size=32, n_layer=1, n_head=2, n_embd=16)` (vocab/eos at locked defaults);
`torch.manual_seed(1234)` before construction for determinism.

### Param-count dedup by data_ptr
**Source:** `tests/test_gpt_param_count.py:16-21` (idiom duplicated in
`test_ablation_config.py:24-29`, `test_slim_checkpoint.py:159-165` — house precedent is to
restate the 6-line helper per test file, not share it)
**Apply to:** `test_lora_inject.py`

### Thin scripts, no CLI
**Source:** `scripts/export_slim.py`, `scripts/pretrain_tinystories.py`
**Apply to:** `scripts/train_adapter_smoke.py`
`_REPO_ROOT`-relative path constants, no argparse, `main()` + `if __name__ == "__main__":`,
`FileNotFoundError` with a "run X first" remedy, `[script_name]`-prefixed prints, all outputs
gitignored.

### Provenance trio
**Source:** `checkpoint.py:137-141` (export_slim), `provenance.py:15-31`
**Apply to:** `export_adapter` (`base_fingerprint`), smoke script
`git_sha` + `step` (+ `val_loss`) read from the base checkpoint dict — never recomputed.

## No Analog Found

| File | Role | Data Flow | Reason | Fallback |
|------|------|-----------|--------|----------|
| `lora/inject.py` (partial) | model-tree orchestration | transform | No existing module mutates a model tree (`setattr` injection) or exposes a context manager | Composed idioms above + verified reference code in 09-RESEARCH.md lines 388-404 / 445-459; stdlib `contextlib.contextmanager` |

Sub-features with no precedent anywhere in the codebase (use RESEARCH.md verified patterns):
`warnings.warn` (first use — D-02), `contextlib.contextmanager` (first use — D-06),
in-place `weight.data.add_/copy_` under `torch.no_grad()` (first use — D-07).

## Metadata

**Analog search scope:** `src/personacore/**`, `scripts/**`, `tests/**` (entire codebase — 6,543 LOC total)
**Files scanned:** 78 Python files surveyed by role; 14 read in full
**Pattern extraction date:** 2026-06-11
