# Phase 12: Stage-2 Conversational Fine-Tune - Pattern Map

**Mapped:** 2026-07-31
**Files analyzed:** 14 (3 modified, 7 new code/scripts, 4 new tests)
**Analogs found:** 14 / 14 (no "no analog" files — the phase is a consumer of Phase 9–11 machinery)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/personacore/training/loop.py` (+`train_mask_bin`, +`val_mask_bin`, +`extra_eval_fns`) | training loop (modified, additive) | batch/streaming | itself — the Seam 1 memmap branch (loop.py:280-290) and the `penalty_fn` splice (loop.py:149-151) | exact |
| `src/personacore/evaluation/perplexity.py` (+`masked_perplexity`) | evaluation metric (modified, additive) | batch sweep | `perplexity()` in the same file (perplexity.py:32-79) + mask semantics from `data.py:93-126` | exact |
| `src/personacore/generation/core.py` (+`stop_ids`) | generation (modified, additive) | streaming/generator | itself — the EOS-stop idiom (core.py:52-71) | exact |
| `scripts/finetune_smoke.py` | driver script | batch (multi-run cohort) | `scripts/run_ablations.py` | exact |
| `scripts/finetune_dialog.py` | driver script | batch (single production run) | `scripts/run_ablations.py` (train call) + `scripts/estimate_fisher_tinystories.py` (anchor/Fisher load) | exact |
| `scripts/build_retention_bin.py` | data prep script | file I/O | `scripts/prepare_dialog_corpus.py` (bin write + loud sanity checks) | role-match |
| `scripts/make_transcripts.py` | driver script | file I/O (generate → markdown) | `scripts/evaluate.py` (EVAL-02 samples.md block) | exact |
| `results/finetune_smoke_report.md` (written by smoke driver) | committed report | file I/O | `scripts/measure_inflation.py` → `results/inflation_report.md` | exact (D-06 mandates this register) |
| `results/transcripts.md` | committed evidence | file I/O | `results/samples.md` (via evaluate.py:118-158) | exact |
| `results/ft_*.csv`, `finetune_prod.csv` | tracked CSVs | append log | `results/abl_*.csv` (CSVLogger via `train()`, run_ablations.py:212) | exact |
| `tests/test_masked_train_seam.py` | test | — | `tests/test_loop_penalty_fn.py` (additive-seam + identity idiom) | exact |
| `tests/test_extra_eval_fns.py` | test | — | `tests/test_loop_penalty_fn.py` (`test_penalty_called_once_per_micro_batch` counting idiom + `test_checkpoint_extra_round_trips`) | exact |
| `tests/test_masked_perplexity.py` | test | — | `tests/test_retention_ppl.py` (stub model, exactly-computable oracle) | exact |
| `tests/test_stop_ids.py` | test | — | `tests/test_generation.py::test_eos_stop` (forced-argmax stub) | exact |

## Pattern Assignments

### `src/personacore/training/loop.py` — `train_mask_bin` / `val_mask_bin` seam (modified, additive)

**Analog:** the existing Seam 1 memmap branch in the same file. Copy its shape exactly, adding one conditional.

**Core pattern to extend** (loop.py:280-290):
```python
elif train_bin is not None:
    # Seam 1 — memmap data branch (the full-corpus long-run source). ...
    train_ids, val_ids = train_bin, val_bin

    def batch_fn(_micro):
        return get_batch_memmap(
            train_bin, train_config.batch_size, model_cfg.block_size, runtime.device
        )
```
When `train_mask_bin is not None`, `batch_fn` calls `get_batch_memmap_masked(train_bin, train_mask_bin, ...)` instead — signature verified at `data.py:93`:
```python
def get_batch_memmap_masked(bin_path, mask_path, batch_size, block_size, device):
    ...
    y[m == 0] = -100
    return x.to(device), y.to(device)
```
`val_mask_bin` (Open Q3 — planner locks) routes `estimate_loss`'s draw the same way; the existing routing point is loop.py:97-101 (`if is_bin: get_batch_memmap(...)`), inside the `_rng_state()`/`_restore_rng` wrapper (loop.py:82/105) which must stay untouched.

**Kwarg-docstring + default-None discipline** (loop.py:203-236 arg docs, e.g. `penalty_fn`):
```python
penalty_fn: callable ``(model) -> scalar tensor`` added to ``base_loss`` via
    ``assemble_loss`` per micro-batch (the M2 EWC seam, EWC-02); None reproduces
    v1.0 bit-for-bit.
```
Every new kwarg gets this form: default `None`, doc states what seam it is and that `None` ⇒ v1.0 identity.

---

### `src/personacore/training/loop.py` — `extra_eval_fns` seam (modified, additive)

**Analog:** the eval-interval CSV block + `CSV_FIELDNAMES` in the same file.

**Fieldnames pattern** (loop.py:49, 326):
```python
CSV_FIELDNAMES = ["step", "train_loss", "val_loss", "lr", "tokens", "wall_clock"]
...
csv = CSVLogger(log_path, fieldnames=CSV_FIELDNAMES) if log_path is not None else None
```
Per RESEARCH: per-run fieldnames = `CSV_FIELDNAMES + sorted(extra_eval_fns)` computed at `CSVLogger` construction. Never mutate the module constant; never append columns to an existing file. `CSVLogger` (logging.py:24-38) writes the header once (new/empty file only) and its `DictWriter` raises on unknown keys — that is the enforcement mechanism.

**Insertion site** — inside the existing eval block (loop.py:350-369):
```python
if csv is not None and (step % eval_interval == 0):
    if val_ids is not None:
        val_loss = estimate_loss(model, val_ids, train_config, model_cfg, runtime.device)
    else:
        val_loss = train_loss
    csv.log(step=step, train_loss=train_loss, val_loss=val_loss,
            lr=scheduler.get_last_lr()[0], tokens=tokens, wall_clock=step)
```
Extra fns run here, one column per key. Two hygiene rules from RESEARCH (pin with tests):
1. restore `model.train()` after running fns — `perplexity()` sets `model.eval()` and does NOT restore (perplexity.py:55, Pitfall 4);
2. wrap the extras block in the existing `_rng_state()`/`_restore_rng` snapshot (loop.py:52-62) exactly as `estimate_loss` does, so resume-equality survives a non-pure fn.

**Protection contract:** any loop edit must keep `tests/test_train_loop.py`, `tests/test_resume_curve.py`, and the golden fixture `tests/fixtures/golden_trajectory_v1.json` green (the DEBT-01 precedent).

---

### `src/personacore/evaluation/perplexity.py` — `masked_perplexity()` (modified, additive)

**Analog:** `perplexity()` in the same file — a ~30-line mirror.

**Core sweep pattern to copy** (perplexity.py:55-79):
```python
model.eval()
data = np.memmap(val_bin_path, dtype=np.uint16, mode="r")   # re-open per call (RSS-leak avoidance)
n = len(data)
total_ce = 0.0
total_tokens = 0
for i in range(0, n - 1, block_size):
    end = min(i + block_size + 1, n)  # +1 so the shifted target fits in the slice
    chunk = torch.from_numpy(data[i:end].astype(np.int64)).to(device)
    if chunk.numel() < 2:
        continue
    x = chunk[:-1].unsqueeze(0)
    y = chunk[1:].unsqueeze(0)
    logits, _ = model(x)  # ignore the mean loss; recompute a SUM below
    if forbid_ids is not None:
        logits = logits.masked_fill(forbid_ids.to(logits.device), float("-inf"))
    ce = F.cross_entropy(logits.view(-1, logits.size(-1)), y.view(-1), reduction="sum")
    total_ce += ce.item()
    total_tokens += y.numel()
if total_tokens == 0:
    raise ValueError(...)
return math.exp(total_ce / total_tokens), total_tokens
```
Additions per RESEARCH Code Example (12-RESEARCH.md "masked_perplexity core"): open the mask memmap (`np.uint8`), slice it SHIFTED with `y` (`mask[i+1:end]` — the `data.py:103-108` target-space semantics), `y = y.masked_fill(m == 0, -100)`, use `ignore_index=-100` in the CE, and denominator = `int((y != -100).sum())`. Fail loud on token/mask length mismatch — copy the raise from `data.py:112-116`. Keep the `(ppl, total_tokens)` auditable-return contract and the `@torch.no_grad()` decorator.

**Docstring register:** copy `retention_perplexity()`'s policy-freeze framing (perplexity.py:84-98) — state that this is THE frozen dialogue-val gate metric for all arms (Pitfall 3, incommensurability).

---

### `src/personacore/generation/core.py` — `stop_ids` kwarg (modified, additive)

**Analog:** the EOS-stop idiom in the same function.

**Current pattern** (core.py:52-71):
```python
bs = block_size if block_size is not None else model.config.block_size
eid = eos_id if eos_id is not None else model.config.eos_id

for _ in range(max_new_tokens):
    ...
    tok = int(next_id)
    if tok == eid:
        return  # D-05 — stop on EOS WITHOUT yielding/appending it.
    idx = torch.cat([idx, next_id], dim=1)
    yield tok
```
**The entire change** (RESEARCH Pattern 6): add `stop_ids=None` to the signature; `stops = stop_ids if stop_ids is not None else {eid}`; replace `if tok == eid:` with `if tok in stops:`. Default ≡ v1.0 single-EOS behavior. `collect()` (core.py:74-83) needs no change — `**kw` passes through.

---

### `scripts/finetune_smoke.py` (driver, sequential smoke cohort)

**Analog:** `scripts/run_ablations.py` — copy its whole register.

**Header/imports/constants pattern** (run_ablations.py:44-94):
```python
import math
import os
import pathlib

# An uncovered MPS op falls back to CPU rather than crashing the multi-hour run — set BEFORE torch.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import torch  # noqa: E402  (must follow the MPS-fallback env set above)

from personacore.config import ModelConfig, RuntimeConfig, TrainConfig  # noqa: E402
...
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TRAIN_BIN = _REPO_ROOT / "data" / "train.bin"
RESULTS_DIR = _REPO_ROOT / "results"   # git-TRACKED output (NOT logs/ or checkpoints/)
CKPT_DIR = _REPO_ROOT / "checkpoints"  # gitignored
SEED = TrainConfig().seed  # 1337
```
No CLI flags (Phase-1 D-04); named tuned constants with a comment per knob; `[script_name]`-prefixed prints.

**Preflight + runtime pattern** (run_ablations.py:320-334):
```python
summary = preflight_device(strict=True)   # side-effecting GATE only; return NOT used for placement
print(f"[run_ablations] preflight: {summary}")
...
runtime = RuntimeConfig()  # the SEPARATE device-carrying config (.device)
```

**Per-arm seed + train pattern** (run_ablations.py:202-226) — the load-bearing fairness discipline:
```python
for name, knob in KNOBS.items():
    # seed_everything re-seeds random/numpy/torch BEFORE building the variant: this makes the
    # DATA sampler's global-numpy draws bit-for-bit identical across all variants. train() only
    # self-seeds when model is None; we pass an explicit model, so the driver owns the seed.
    seed_everything(SEED)
    model = GPT(ModelConfig(**knob))
    ...
    csv_path = str(RESULTS_DIR / f"abl_{name}.csv")  # tracked results/ path (NOT logs/).
    train(
        train_config=cfg_reduced, runtime_config=runtime, model=model,
        model_config=ModelConfig(**knob), train_bin=TRAIN_BIN, val_bin=VAL_BIN,
        eos_id=ModelConfig().eos_id, best_checkpoint_path=ckpt_path, log_path=csv_path,
        eval_interval=EVAL_INTERVAL, checkpoint_interval=CHECKPOINT_INTERVAL,
    )
```
Per arm here: load `best.pt` weights fresh (`GPT(ModelConfig(**blob["model_config"]))` + `load_state_dict` — NEVER `resume_from=best.pt`, PITFALLS P4), then add the new kwargs (`train_mask_bin=`, `penalty_fn=`, `extra_eval_fns=`, `checkpoint_extra=`).

**Budget calibration pattern** (run_ablations.py:130-188 `calibrate()` + 341-346 lock enforcement):
```python
recommended = calibrate(runtime)
if abs(recommended - REDUCED_MAX_STEPS) > EVAL_INTERVAL:
    raise SystemExit(
        f"Calibration recommends max_steps={recommended} but REDUCED_MAX_STEPS="
        f"{REDUCED_MAX_STEPS}. Update the constant and re-run (D-07)."
    )
```
D-03's dialogue-budget recalibration mirrors `calibrate()`: one run at `eval_interval=250`, read the curve back via the `_read_val_curve` CSV-reader idiom (run_ablations.py:109-127 — note the `math.isfinite` NaN/Inf skip, reusable for the D-02 instability gate), slope rule, LOCK the constant, enforce the lock with a loud `SystemExit`.

**Gate checks:** loud `raise SystemExit(f"[proof x] ...")`, never bare `assert` — copy the register from estimate_fisher_tinystories.py:115-162 (see finetune_dialog below). D-07 mid-sequence halt = a `SystemExit` naming the violated gate.

---

### `scripts/finetune_dialog.py` (production run driver)

**Analog:** `run_ablations.py` for the train call; `scripts/estimate_fisher_tinystories.py` for anchor/Fisher loading.

**Anchor-load pattern** (estimate_fisher_tinystories.py:89-103):
```python
# weights_only=False: TRUSTED-only read of the project's OWN checkpoint (T-10-05) —
# never a foreign file.
blob = torch.load(BEST_PATH, weights_only=False)
model_cfg = ModelConfig(**blob["model_config"])
model = GPT(model_cfg)
model.load_state_dict(blob["model"])
model.to(runtime.device)
...
# theta_star: detached CPU clones snapshot from named_parameters() — the dedup rule:
# the tied wte/lm_head storage appears exactly once.
theta_star = {n: p.detach().clone().cpu() for n, p in model.named_parameters()}
```
Fisher comes from `load_fisher(FISHER_CACHE, expected_fingerprint=...)` (fingerprint READ from the anchor blob — estimate_fisher_tinystories.py:176-182 shows the trio: `git_sha`/`step`/`val_loss`). `EWCPenalty(fisher, theta_star, lam=λ*, device=runtime.device)` constructed ONCE per run.

**Full invocation:** the RESEARCH Code Example ("Production fine-tune invocation") is the authoritative template — `train()` with `train_mask_bin`/`val_mask_bin`, `penalty_fn=penalty`, `extra_eval_fns={retention_ppl, dialog_ppl, ewc_penalty}`, `checkpoint_extra={"fisher": ..., "theta_star": ..., "ewc_lambda": ..., "fisher_meta": ...}`, `log_path=RESULTS_DIR / "finetune_prod.csv"`, checkpoints `convbase_latest.pt`/`convbase_best.pt`.

**Missing-prerequisite pattern** (estimate_fisher_tinystories.py:66-74):
```python
if not BEST_PATH.exists():
    raise FileNotFoundError(
        f"Missing {BEST_PATH}. Run `python scripts/pretrain_tinystories.py` first."
    )
```

---

### `scripts/build_retention_bin.py` (run-once sub-bin builder)

**Analog:** `scripts/prepare_dialog_corpus.py` — bin write + loud post-build proofs.

**Bin-write pattern** (prepare_dialog_corpus.py:120-131):
```python
id_shards = []
for ...:
    id_shards.append(np.asarray(ids, dtype=np.uint16))
np.concatenate(id_shards).tofile(bin_path)
```
Here the input is `data/val.bin` (memmap) subsampled at `EOS_ID = 8184` document boundaries (doc-level, RESEARCH Pattern 1); ~1.0M tokens; seeded local RNG (`np.random.default_rng(SEED)` — the estimate_fisher_tinystories.py:55 discipline: local rng, global streams untouched).

**Refuse-to-rerun pattern** (estimate_fisher_tinystories.py:78-82) — the sub-bin is FROZEN for the milestone:
```python
if FISHER_CACHE.exists():
    raise SystemExit(
        f"[estimate_fisher_tinystories] {FISHER_CACHE} already exists — refusing to "
        "overwrite the shared production cache. Delete it to re-estimate."
    )
```

**Loud sanity-check pattern** (prepare_dialog_corpus.py:134-160): `SystemExit` (never bare assert) on eos-count/length checks; print token count + decoded prefix. Step-0 anchor measurements (masked sub-bin, masked full-val, 2.1066 reference — Pitfall 1) belong with this script or Stage 0 of the smoke driver.

---

### `scripts/make_transcripts.py` → `results/transcripts.md`

**Analog:** `scripts/evaluate.py` EVAL-02 block → `results/samples.md`.

**Sample-then-write pattern** (evaluate.py:114-159):
```python
tok = from_json(TOKENIZER_PATH)  # FROZEN artifact — never retrain.
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
samples_path = RESULTS_DIR / "samples.md"

lines = [
    "# PersonaCore — Qualitative Samples (EVAL-02)",
    "",
    "> These samples are REPRESENTATIVE, not cherry-picked. ...",
    ...
]
for prompt in PROMPTS:
    greedy = generate_text_str(model, tok, prompt, max_new_tokens=..., greedy=True)
    warm   = generate_text_str(model, tok, prompt, max_new_tokens=..., temperature=0.8, top_p=0.95)
    lines += [f"## Prompt: {label}", "", "**Greedy (deterministic):**", "", f"> {prompt}{greedy}", ...]
samples_path.write_text("\n".join(lines), encoding="utf-8")
```
Differences here: prompts = held-out val episodes' persona + first user turn rendered through `dialogue/serialize.render_document` (serialize.py:42-52) / `encode_dialogue` (serialize.py:55-83) ending with the `<|assistant|>` id — NEVER hand-formatted strings (Pitfall 4: transcripts must tokenize identically to the bins). Decode via `generate()`/`collect()` with `forbid_ids` + `stop_ids={8184, 8185}`. Report the measurable proxies (stop-id termination fraction, no mid-utterance role-token leakage) alongside — the "representative, not cherry-picked" header framing carries over.

---

### `results/finetune_smoke_report.md` (D-06 committed report)

**Analog:** `scripts/measure_inflation.py` → `results/inflation_report.md` (D-06 explicitly mandates this register).

**Report skeleton** (measure_inflation.py:138-192) — copy this f-string structure:
```python
report = f"""# PersonaChat Tokenizer-Inflation Report (DATA-04, D-08/D-09/D-10)

> **What these numbers are:** ... **What they are not:** ...

## D-08 Metrics
| # | Metric | Value | Auditable denominator |
...
## D-09 Bands (RELATIVE — pre-registered, locked before this measurement ran)
| Band | Condition | Action |
...
## Verdict

PENDING — user decision at checkpoint (D-09).
"""
REPORT_PATH.write_text(report, encoding="utf-8")
```
Phase-12 sections: one block per smoke decision (budget recalibration, noise floor + k counterfactual per D-05, masking verdict, LR gates, cold-start diagnostic, λ sweep + λ*), each with raw numbers + auditable denominators + pre-registered threshold + verdict. `## Verdict` stays PENDING until the D-07 blocking checkpoint.

**Never-clobber-recorded-verdict guard** (measure_inflation.py:69-75):
```python
if REPORT_PATH.exists() and "--force" not in sys.argv[1:]:
    recorded = REPORT_PATH.read_text(encoding="utf-8").split("## Verdict")[-1]
    if "PENDING" not in recorded:
        raise SystemExit(f"[...] {REPORT_PATH} already carries a recorded verdict — ...")
```

**Downstream-gate reader** (prepare_dialog_corpus.py:61-82 `_require_go_verdict`): `finetune_dialog.py` should refuse to run without a recorded non-PENDING verdict in the smoke report — same regex-on-`## Verdict` pattern.

---

### `tests/test_masked_train_seam.py` + `tests/test_extra_eval_fns.py`

**Analog:** `tests/test_loop_penalty_fn.py` — the additive-seam test playbook.

**In-process identity pattern** (test_loop_penalty_fn.py:73-93, 117-124) — default-None ⇒ v1.0 identity, platform-independent:
```python
def _run_recipe(log_path, **train_kwargs):
    cfg = TrainConfig(lr=1e-2, warmup_steps=2, max_steps=5, batch_size=4)
    seed_everything(1234)
    model = BigramLanguageModel(vocab_size=ModelConfig().vocab_size)
    final = train(train_config=cfg, runtime_config=RuntimeConfig(device="cpu"), model=model,
                  corpus_path=CORPUS_PATH, eos_id=EOS_ID, log_path=log_path,
                  eval_interval=1, return_final_loss=True, **train_kwargs)
    return pathlib.Path(log_path).read_text(), repr(float(final)), _param_sha256(model)

def test_omitted_equals_none_in_process(tmp_path):
    omitted = _run_recipe(tmp_path / "omitted.csv")
    explicit_none = _run_recipe(tmp_path / "none.csv", penalty_fn=None)
    assert omitted == explicit_none  # (csv_text, final_loss_repr, param_sha256) all bitwise
```
Reuse `_run_recipe` verbatim for `train_mask_bin=None` / `extra_eval_fns=None` identity (`None` ⇒ byte-identical CSV). Golden replay stays in the existing `test_golden_trajectory_bit_identity` (platform-gated, test_loop_penalty_fn.py:96-114) — just re-run it.

**Call-counting pattern** (test_loop_penalty_fn.py:181-196) for "extra fn runs once per eval interval":
```python
calls = []
def counting_penalty(model):
    calls.append(1)
    return torch.tensor(0.0)
train(train_config=cfg, runtime_config=RuntimeConfig(device="cpu"), penalty_fn=counting_penalty)
assert len(calls) == 6
```
Same idiom with `extra_eval_fns={"probe": counting_fn}`; also assert `model.training is True` after the run (train-mode restore, Pitfall 4). For mask-seam routing, draw on a real tiny bin pair — the fixture recipe is `tests/test_retention_ppl.py:40-46` (`ids.tofile(path)` in `tmp_path`) plus a `uint8` mask; assert `-100` sentinels reach the loss (the prepare_dialog_corpus.py:174-178 smoke-draw check).

---

### `tests/test_masked_perplexity.py`

**Analog:** `tests/test_retention_ppl.py` — stub model with exactly-computable PPL.

**Stub + fixture pattern** (test_retention_ppl.py:26-46):
```python
class _UniformLogitsModel(nn.Module):
    """``forward(idx) -> (zeros logits, None)``: uniform distribution over VOCAB."""
    def forward(self, idx, targets=None):
        return torch.zeros(idx.shape[0], idx.shape[1], VOCAB), None

@pytest.fixture()
def val_bin(tmp_path):
    ids = np.array([0, 1, 2, ...], dtype=np.uint16)
    path = tmp_path / "val.bin"
    ids.tofile(path)
    return path
```
For the masked oracle: hand-build an aligned `uint8` mask bin, compute expected CE by hand over mask==1 shifted targets only, assert the exact denominator (`total_tokens == number of scored targets`) — RESEARCH names this the "hand-fixture oracle" (T-11-04 register). Also assert the length-mismatch raise.

---

### `tests/test_stop_ids.py`

**Analog:** `tests/test_generation.py::test_eos_stop` (lines 121-138).

**Forced-argmax stub pattern:**
```python
def _forward(idx, targets=None):
    # Make eos_id the argmax for every position so the very first step would emit EOS.
    logits = torch.full((idx.size(0), idx.size(1), model.config.vocab_size), -1e9)
    logits[..., eos_id] = 1e9
    return logits, None

model.forward = _forward  # type: ignore[method-assign]
out = collect(model, prompt, max_new_tokens=5, greedy=True)
assert out[0, -1].item() != eos_id
assert out.shape[1] == prompt.shape[1]  # stop-without-yield
```
Tests: (a) `stop_ids` omitted ≡ v1.0 EOS behavior (same asserts as above); (b) force a non-EOS id (e.g. the user-role id) as argmax with `stop_ids={that_id}` — must stop without yielding it. Use the `_tiny_model()` fixture recipe (test_generation.py:31-47, `ModelConfig(block_size=8, vocab_size=16, n_layer=1, n_head=1, n_embd=8, eos_id=15)`), read `eos_id`/`block_size` from `model.config`, never hardcode.

## Shared Patterns

### Driver-script register (all four new scripts)
**Source:** `scripts/run_ablations.py:44-63`, `scripts/estimate_fisher_tinystories.py:29-56`
Apply to: `finetune_smoke.py`, `finetune_dialog.py`, `build_retention_bin.py`, `make_transcripts.py`
- `os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")` BEFORE `import torch` (with the `# noqa: E402` comments)
- No CLI flags; `_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent` constants; named tuned constants with rationale comments
- `preflight_device(strict=True)` gate first (side-effecting; return unused for placement), then `runtime = RuntimeConfig()`
- `[script_name]`-prefixed prints; `if __name__ == "__main__": main()`

### Seed/data-order ownership
**Source:** `scripts/run_ablations.py:202-208`
Apply to: every arm in `finetune_smoke.py` and `finetune_dialog.py`
```python
seed_everything(SEED)   # IMMEDIATELY before each explicit GPT(...) build — driver owns the seed
model = GPT(ModelConfig(**...))
```
`train()` only self-seeds when `model is None`; the batch sampler draws from the GLOBAL numpy RNG (`data.py:85/117`), so this call is also what makes arms share data order (D-05, Phase-13 identical-seed twin).

### Loud proof checks, never bare asserts
**Source:** `scripts/estimate_fisher_tinystories.py:115-162`, `scripts/prepare_dialog_corpus.py:139-178`
Apply to: all script-level gates (smoke gates, sub-bin sanity, mid-sequence halts)
```python
if not torch.isfinite(t).all():
    raise SystemExit(f"[proof a] non-finite Fisher entries in {name!r} (Pitfall 7)")
```

### Trusted checkpoint loads
**Source:** `scripts/evaluate.py:81`, `scripts/estimate_fisher_tinystories.py:89`
Apply to: every `torch.load` in the new scripts
`torch.load(path, weights_only=False)` ONLY on the project's own checkpoints/caches, with the comment saying so; shippable artifacts stay `weights_only=True` (`export_slim`/`export_fisher`).

### Tracked results/ vs gitignored logs//checkpoints/
**Source:** `run_ablations.py:63-64, 212`
Apply to: all CSV/report/transcript outputs
Per-arm CSVs and reports → `results/` (tracked — Phase 13 reads them); checkpoints → `checkpoints/` (gitignored). Never write sweep evidence to `logs/` (Pitfall 6).

### CSV read-back for gate logic
**Source:** `run_ablations.py:109-127` (`_read_val_curve`)
Apply to: budget recalibration, instability gate (NaN/Inf skip via `math.isfinite`), noise-floor deltas
```python
for row in csv.DictReader(fh):
    v = row.get("val_loss", "")
    if v in (None, ""):
        continue
    val = float(v)
    if not math.isfinite(val):
        continue  # skip nan/inf/-inf (a diverged run)
    rows.append((int(float(row["step"])), val))
```

### Role-norm extra fns (D-04 cold-start)
**Source:** `gpt.py:159` (`wte` attribute, verified in RESEARCH)
```python
extra_eval_fns["role_norm_user"] = lambda m: m.wte.weight[8185].norm().item()  # 8186/8187 likewise
```

## No Analog Found

None. Every file has a direct in-repo analog — RESEARCH's key insight holds: "the entire phase is a consumer of Phase 9–11 machinery."

## Metadata

**Analog search scope:** `src/personacore/{training,evaluation,generation,continual,dialogue}`, `scripts/`, `tests/`, `results/`
**Files scanned:** 15 read in full or targeted (loop.py, perplexity.py, core.py, data.py, logging.py, serialize.py, run_ablations.py, estimate_fisher_tinystories.py, evaluate.py, measure_inflation.py, prepare_dialog_corpus.py, test_loop_penalty_fn.py, test_retention_ppl.py, test_generation.py, directory listings)
**Pattern extraction date:** 2026-07-31
