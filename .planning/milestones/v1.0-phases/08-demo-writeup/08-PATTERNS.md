# Phase 8: Demo & Writeup - Pattern Map

**Mapped:** 2026-06-10
**Files analyzed:** 9 new/modified files
**Analogs found:** 5 / 9 (4 are net-new artifact types with no codebase analog — covered by RESEARCH.md patterns + shared prose conventions)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `scripts/export_slim.py` | script (thin entry point) | file I/O (transform best.pt → slim.pt) | `scripts/evaluate.py` | exact (load-ckpt → write-tracked-artifact shape) |
| `scripts/demo_app.py` | script (demo launcher) | streaming request-response | `scripts/evaluate.py` (wiring) + `src/personacore/generation/text.py` (producer contract) | role-match |
| `tests/test_slim_checkpoint.py` | test | file I/O + generation | `tests/test_best_ckpt.py` + `tests/test_mps_smoke.py` + `tests/test_gpt_weight_tying.py` + `tests/test_generation_text.py` | exact (composite of 4 existing idioms) |
| `demo.ipynb` | notebook (evidence artifact) | batch (load + plot + sample) | none in repo — reuse `scripts/evaluate.py` load idiom + RESEARCH Pattern 4 | partial |
| `README.md` | documentation | — | `results/results.md` (rigor-signal prose register) | partial |
| `docs/REPORT.md` | documentation | — | `results/results.md` + `.planning/phases/*/0X-VERIFICATION.md` (source material + register) | partial |
| `results/run.csv` | data artifact (committed copy) | — | `results/abl_*.csv` precedent (committed eval CSVs) | exact (placement precedent only) |
| `pyproject.toml` (modify) | config | — | itself — extras table lines 15–18 | exact |
| `assets/demo.gif` | binary asset | — | no analog (RESEARCH Pattern 5, human-action capture) | none |

**Note:** `README.md` does not exist yet and there is no `docs/` directory — both are net-new, not rewrites.

## Pattern Assignments

### `scripts/export_slim.py` (script, file I/O)

**Analog:** `scripts/evaluate.py` — the established "thin no-CLI driver that loads `best.pt` and writes a shippable artifact" shape.

**Module docstring + security-note pattern** (`scripts/evaluate.py` lines 1–28, abridged):
```python
"""Thin no-CLI evaluation driver: headline full-val perplexity + curated samples (EVAL-01/EVAL-02).

Mirrors ``scripts/pretrain_tinystories.py``: logic lives in ``src/personacore`` — this script only
wires the FROZEN artifacts ... No CLI flag parsing (Phase-1 D-04): all
paths are ``_REPO_ROOT``-relative constants.

SECURITY: ``torch.load(..., weights_only=False)`` is used ONLY for the project's OWN trusted
``best.pt`` (T-07-02) — never a foreign checkpoint. ...
"""
```
Every script in `scripts/` opens with a docstring that (a) names the requirement IDs it serves, (b) states "no argparse, `_REPO_ROOT`-relative constants" (Phase-1 D-04), (c) carries an explicit SECURITY note when `torch.load` appears. Copy this discipline.

**Path-constants pattern** (`scripts/evaluate.py` lines 46–50):
```python
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BEST_PATH = _REPO_ROOT / "checkpoints" / "best.pt"  # own trusted shipped checkpoint (gitignored)
TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"  # FROZEN production artifact
RESULTS_DIR = _REPO_ROOT / "results"  # git-TRACKED output (NOT logs/ or checkpoints/)
```
For the slim export: `SLIM_PATH = _REPO_ROOT / "checkpoints" / "model_slim.pt"` (stays gitignored; distributed via Release per RESEARCH Pitfall 3).

**Missing-input guard + main() shape** (`scripts/evaluate.py` lines 62–75, 162–163):
```python
def main() -> None:
    if not BEST_PATH.exists():
        raise FileNotFoundError(
            f"Missing {BEST_PATH}. Run `python scripts/pretrain_tinystories.py` first."
        )
    ...

if __name__ == "__main__":
    main()
```

**Trusted-load pattern to copy for reading `best.pt`** (`scripts/evaluate.py` line 81):
```python
blob = torch.load(BEST_PATH, weights_only=False)  # own trusted file ONLY (T-07-02).
```

**Slim-dict keys to keep** — mirror the open-dict convention of `src/personacore/checkpoint.py` lines 57–77 (`schema_version`, `model`, `model_config`, `git_sha`, `step`, `val_loss`), dropping `optimizer`/`scheduler`/`scaler`/`rng`/`train_config`. `checkpoint.py` line 29 already defines `CKPT_SCHEMA_VERSION = 1`; the slim file should carry its own `schema_version` key (RESEARCH Pattern 2, verified end-to-end). The checkpoint.py module docstring (lines 16–18) explicitly reserves this split: *"The slim INFERENCE checkpoint (Phase 8) will use ``weights_only=True``."* — cite that in the export script's docstring.

**Anti-copy warning:** do NOT copy evaluate.py's `preflight_device(strict=True)` gate (lines 65–66) — it RAISES on a CPU-only box. The export is a one-shot local transform; no accelerator gate.

---

### `scripts/demo_app.py` (script, streaming request-response)

**Analog A — model/tokenizer wiring:** `scripts/evaluate.py` lines 77–86 + 114:
```python
runtime = RuntimeConfig()  # the SEPARATE device-carrying config (.device); MPS-aware (D-02).

blob = torch.load(BEST_PATH, weights_only=False)  # own trusted file ONLY (T-07-02).
model_cfg = ModelConfig(**blob["model_config"])
model = GPT(model_cfg)
model.load_state_dict(blob["model"])
model.to(runtime.device)
model.eval()
...
tok = from_json(TOKENIZER_PATH)  # FROZEN artifact — never retrain.
```
The demo copies this reconstruction idiom but **loads the slim artifact with `weights_only=True`** (the locked safe-load bar) and resolves to CPU via `RuntimeConfig` (CONTEXT code_context: "no ad-hoc device strings"). Imports come from the same surfaces evaluate.py uses (lines 39–44): `personacore.config.{ModelConfig, RuntimeConfig}`, `personacore.generation.generate_text` (streaming) — note evaluate.py imports the non-streaming `generate_text_str`; the demo wants the streaming `generate_text`. `personacore.model.GPT`, `personacore.tokenizer.from_json`.

**Analog B — the producer contract the callback consumes:** `src/personacore/generation/text.py` lines 39–93. Load-bearing facts for the Gradio callback:
- `generate_text(model, tokenizer, prompt, *, max_new_tokens, **gen_kw)` — `max_new_tokens` is **keyword-only and required**, bounded to `(0, 4096]` (`DEFAULT_MAX_NEW_TOKENS_CAP = 4096`, line 28); out-of-range raises `ValueError` before the loop. The demo's max-tokens slider must stay ≤ 4096.
- It yields **string deltas** (new suffixes), prompt already stripped, EOS never shown (lines 90–93). The ChatInterface contract wants cumulative strings → the callback must accumulate (`acc += delta; yield acc` — RESEARCH Pattern 1 / Pitfall 1).
- `gen_kw` threads `temperature`, `top_k`, `top_p`, `greedy`, `generator` through to the core (docstring lines 58–61) — the sliders map 1:1 onto these kwargs.
- It already calls `model.eval()` internally (line 75); no extra no_grad plumbing needed in the callback.

**Env-var-before-import pattern** (`scripts/evaluate.py` lines 34–37) — same ordering trick the demo needs for `GRADIO_ANALYTICS_ENABLED`:
```python
# An uncovered MPS op falls back to CPU rather than crashing — set BEFORE importing torch.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import torch  # noqa: E402  (must follow the MPS-fallback env set above)
```
Copy the shape: `os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"` before `import gradio`, with `# noqa: E402` on the late imports (ruff `E` is enabled, line-length 100 — `pyproject.toml` lines 27–32).

**Gradio specifics** (no codebase analog — use RESEARCH Pattern 1 verbatim): `gr.ChatInterface(type="messages", analytics_enabled=False, ...)`, fresh story per message (no history concatenation), `demo.launch(share=False)`.

---

### `tests/test_slim_checkpoint.py` (test, file I/O + generation)

Composite of four existing idioms — copy each piece from its source:

**1. Tiny-CPU-GPT fixture** (`tests/test_generation_text.py` lines 31–43):
```python
def _tiny_model():
    """A minimal CPU GPT — eos_id (15) < vocab_size (16), small block_size for cheap crops."""
    return GPT(
        ModelConfig(
            block_size=8,
            vocab_size=16,
            n_layer=1,
            n_head=1,
            n_embd=8,
            eos_id=15,
        )
    )
```
(RESEARCH Pattern 3 suggests `ModelConfig(block_size=32, n_layer=1, n_head=2, n_embd=16)` with vocab/eos at defaults — either works; keep `n_embd % n_head == 0`.) Real-tokenizer alternative if the test generates text: `tests/test_best_ckpt.py` lines 31–38 loads the frozen `artifacts/tokenizer.json` via `from_json(TOKENIZER_PATH)` with the comment "FROZEN production artifact — never retrain".

**2. Blob inspection via tmp_path** (`tests/test_best_ckpt.py` lines 90–95):
```python
    assert best_path.exists(), "best.pt must be written when best_checkpoint_path is set"

    # best.pt holds the LOWEST observed val loss (the dip), NOT the final step's larger value.
    blob = torch.load(best_path, weights_only=False)  # own trusted file.
    assert blob["val_loss"] == pytest.approx(min_observed)
```
The slim test inverts the load flag — `torch.load(slim_path, weights_only=True)` IS the assertion (the locked safe-load bar). Assert the key set (`schema_version`, `model`, `model_config`, `git_sha`, `step`, `val_loss`) and the absence of `optimizer`/`rng`.

**3. Tying survival assert** (`tests/test_gpt_weight_tying.py` lines 15–19):
```python
def test_lm_head_shares_storage_with_token_embedding():
    # data_ptr() identity is the load-bearing assert: a copy would differ here AND inflate the
    # param count by one vocab x n_embd block (cross-checks test_gpt_param_count).
    model = GPT(ModelConfig())
    assert model.lm_head.weight.data_ptr() == model.wte.weight.data_ptr()
```
After round-tripping through the slim file: rebuild `GPT(ModelConfig(**loaded["model_config"]))`, `load_state_dict(loaded["model"])`, then this exact `data_ptr()` assert. Tying happens in `GPT.__init__` (`src/personacore/model/gpt.py` line 184: `self.lm_head.weight = self.wte.weight`); state-dict keys are `wte.weight` / `lm_head.weight` — **no `transformer.` prefix** (RESEARCH §2).

**4. Skipif gate for the real artifact** (`tests/test_mps_smoke.py` lines 29–32 — the suite's only existing skip, the precedent CI relies on):
```python
# Guard the WHOLE module: only the real M3 (MPS) runs it; CPU-only CI SKIPS (not ERRORS).
pytestmark = pytest.mark.skipif(
    not torch.backends.mps.is_available(), reason="MPS not available (CPU-only CI)"
)
```
For the slim test, gate only the real-artifact function (not the whole module — the tiny-model mechanism test must always run):
```python
REAL = pathlib.Path("checkpoints/model_slim.pt")

@pytest.mark.skipif(not REAL.exists(), reason="real slim artifact not present (CI)")
def test_real_slim_artifact_generates_on_cpu(): ...
```

**Module-docstring convention** (every test file): opening docstring names the requirement IDs, states "CPU-only, GPU/MPS-free", and cites the decision being proven — see `tests/test_generation_text.py` lines 1–12 and `tests/test_best_ckpt.py` lines 1–14.

---

### `demo.ipynb` (notebook, batch)

**No notebook exists in the repo.** Reuse these codebase idioms inside cells:

**Slim-load cell** — same reconstruction as the demo script (above), `weights_only=True`, CPU. Param count idiom (RESEARCH, verified): `sum(p.numel() for p in model.parameters())` → 13,891,584 (tied tensor deduped). Print `loaded["git_sha"]` and `loaded["step"]` for QA-02.

**Curves cell** — CSV columns are `step,train_loss,val_loss,lr,tokens,wall_clock` (produced by `src/personacore/logging.py`, 201 rows verified). Read the **committed** copy `results/run.csv` (Pitfall 2 — `logs/run.csv` is gitignored), `csv.DictReader` + matplotlib (RESEARCH Code Examples).

**Sampling cell** — use `generate_text_str` exactly as `scripts/evaluate.py` lines 133–143 does (greedy + warm variants over a fixed prompt):
```python
        greedy = generate_text_str(
            model, tok, prompt, max_new_tokens=SAMPLE_MAX_NEW_TOKENS, greedy=True
        )
        warm = generate_text_str(
            model, tok, prompt, max_new_tokens=SAMPLE_MAX_NEW_TOKENS,
            temperature=0.8, top_p=0.95,
        )
```
D-07 settings tour = this idiom over a grid {greedy, temperature, top-k, top-p}, each sampled cell seeded via the `generator` kwarg (`torch.Generator().manual_seed(...)` — threads through `generate_text`/`generate`, RESEARCH Pitfall 8).

**Ablation cell** — plot `results/abl_baseline.csv` / `abl_no_tie.csv` / `abl_no_pos.csv` / `abl_depth_cut.csv` (same CSV schema) and reproduce the `results/results.md` table **with its caveat verbatim** (see Shared Patterns).

Execution: `nbconvert --execute --inplace` in `.venv` (RESEARCH Pattern 4); commit WITH outputs (D-06).

---

### `README.md` + `docs/REPORT.md` (documentation)

**No README exists** — net-new. The prose register to copy is the committed evidence artifacts:

**Rigor-signal phrasing** (`results/results.md` lines 3–10 — carry this caveat VERBATIM wherever the ablation table appears):
```markdown
> **Reduced-budget, self-consistent cohort (D-06).** All four runs below train through
> the UNTOUCHED `train()` harness at IDENTICAL seed (1337), data, LR, warmup, and
> budget (`max_steps=2500`, calibrated per D-07) — only the ablated knob
> differs. The numbers are comparable to EACH OTHER, NOT to the headline 50k `best.pt`.
>
> The headline production figure is reported SEPARATELY (EVAL-01, `scripts/evaluate.py`):
> deterministic full-val perplexity **2.1066** over **12,636,922** scored target tokens
> on the 50k-step `best.pt` — a different (larger) budget, listed here only for context.
```
PPL is ALWAYS cited with its token denominator (the Phase-7 rigor signal); samples are labeled "REPRESENTATIVE, not cherry-picked" (`results/samples.md` header, generated by `scripts/evaluate.py` lines 118–129).

**Headline numbers (single-source from committed artifacts, never recompute):** 13,891,584 params; full-val PPL **2.1066** over **12,636,922** tokens; ~95–105 tok/s CPU streaming (RESEARCH §1); ablation table from `results/results.md` lines 12–17.

**DOC-01 source material** (decision-driven REPORT consolidates these — note Phase 1's file is unnumbered):
`.planning/phases/01-scaffolding-reproducible-environment/VERIFICATION.md`, `02-from-scratch-bpe-tokenizer/02-VERIFICATION.md`, `03-bigram-baseline-training-harness/03-VERIFICATION.md`, `04-gpt-transformer-decoder/04-VERIFICATION.md`, `06-generation-sampling/06-VERIFICATION.md`, `07-evaluation/07-VERIFICATION.md` (no Phase-5 VERIFICATION.md exists), plus `results/results.md`, `results/samples.md`.

**Quickstart command precedent** (CLAUDE.md / pyproject): `pip install -e ".[cpu,demo]" --extra-index-url https://download.pytorch.org/whl/cpu` inside a Python 3.11 venv.

---

### `pyproject.toml` (modify — extras)

**Analog: itself**, lines 15–18:
```toml
[project.optional-dependencies]
cpu = ["torch==2.7.*"]
demo = ["gradio>=5,<6", "matplotlib~=3.10"]
dev = ["pytest~=9.0", "ruff~=0.15", "tiktoken~=0.13"]
```
If the planner adds notebook tooling (`ipykernel`, `nbconvert` — `[ASSUMED]` packages, install gated per RESEARCH audit), follow this exact compatible-release pin style and put them in an existing or new extra. Ruff config (lines 27–32): line-length 100, `select = ["E","F","W","I"]` — new scripts/tests must pass `make lint`.

### `results/run.csv` (data artifact)

No code pattern — placement precedent only: eval CSVs are committed under `results/` (`abl_*.csv`), while `logs/` is gitignored. Copy `logs/run.csv` → `results/run.csv` (consistent with the `abl_*.csv` precedent; RESEARCH Pitfall 2) and point the notebook at the committed path.

## Shared Patterns

### Thin-script shape (Phase-1 D-04)
**Source:** `scripts/evaluate.py` (richest), `scripts/preflight_demo.py` (minimal 37-line example)
**Apply to:** `scripts/export_slim.py`, `scripts/demo_app.py`
Structure: decision-citing module docstring → env vars set BEFORE the import they affect (`# noqa: E402` on late imports) → `_REPO_ROOT`-relative path CONSTANTS (never argparse) → `def main() -> None:` → `if __name__ == "__main__": main()`. Logic lives in `src/personacore/`; scripts only wire.

### Safe-load discipline (T-02-05 / T-07-02 lineage)
**Source:** `src/personacore/checkpoint.py` lines 16–20 and 92–95
**Apply to:** export script (reads `best.pt`), demo, notebook, test (all read the slim file)
```python
    # weights_only=False: the resume checkpoint carries pickled optimizer/RNG/numpy
    # objects that the torch>=2.6 weights_only=True default rejects. TRUSTED-only file
    # (own checkpoint); the slim INFERENCE checkpoint (Phase 8) uses weights_only=True.
    ckpt = torch.load(path, map_location=map_location, weights_only=False)
```
Rule: `weights_only=False` ONLY for our own `best.pt`, always with this style of justifying comment; every slim-artifact consumer loads `torch.load(path, map_location="cpu", weights_only=True)`.

### Model-reconstruction idiom (config travels with weights — QA-02)
**Source:** `scripts/evaluate.py` lines 82–86
**Apply to:** demo, notebook, test (real-artifact branch)
```python
model_cfg = ModelConfig(**blob["model_config"])
model = GPT(model_cfg)
model.load_state_dict(blob["model"])
model.eval()
```
`ModelConfig` fields (`src/personacore/config.py` lines 86–94): `vocab_size=8192` (LOCKED), `eos_id=8184`, `block_size=256`, `n_layer=6`, `n_head=6`, `n_embd=384`, `dropout=0.0`, `weight_tying=True`, `use_pos_emb=True`.

### Frozen-tokenizer load
**Source:** `scripts/evaluate.py` line 114 / `tests/test_best_ckpt.py` line 38
**Apply to:** demo, notebook, test
```python
tok = from_json(TOKENIZER_PATH)  # FROZEN artifact — never retrain.
```
`TOKENIZER_PATH = "artifacts/tokenizer.json"` (committed, data-only JSON, vocab 8192).

### CPU-only test posture
**Source:** `tests/test_best_ckpt.py` line 34 (`CPU_RUNTIME = RuntimeConfig(device="cpu")`), `tests/test_generation_text.py` (tiny in-memory GPT, no GPU/MPS)
**Apply to:** `tests/test_slim_checkpoint.py`
Tests pin CPU explicitly or use a tiny model with no device plumbing; the suite must stay green on CPU-only CI (today: 122 passed, 1 skipped).

### Decision-citing docstrings/comments
**Source:** every file read (e.g. `generation/text.py` lines 1–21, `checkpoint.py` lines 1–21)
**Apply to:** all new Python files
Module docstrings and load-bearing comments cite the decision/requirement IDs they implement (D-xx, DEMO-xx, T-xx, QA-xx) and explain WHY. This is the project's dominant convention — new files that lack it will read as foreign.

## No Analog Found

Files with no close match in the codebase (planner should use RESEARCH.md patterns instead):

| File | Role | Data Flow | Reason | RESEARCH fallback |
|------|------|-----------|--------|-------------------|
| Gradio UI portion of `scripts/demo_app.py` | UI definition | streaming | First UI in the project | RESEARCH Pattern 1 (verified against the 5.50.0 wheel) |
| `demo.ipynb` (as an artifact type) | notebook | batch | First notebook in the repo | RESEARCH Pattern 4 (nbconvert execution + cell ordering per D-05) |
| `assets/demo.gif` | binary asset | — | No media assets exist | RESEARCH Pattern 5 (human-action capture + ffmpeg palette recipe) |
| `README.md` / `docs/REPORT.md` overall structure | docs | — | No README/docs exist | D-01..D-04 locked decisions + Shared Patterns prose register |

## Metadata

**Analog search scope:** `scripts/`, `tests/`, `src/personacore/` (incl. `generation/`, `evaluation/`, `model/`), `results/`, `pyproject.toml`, `.planning/phases/*/`*VERIFICATION.md*
**Files scanned:** 12 read in full or targeted, ~45 listed/classified
**Pattern extraction date:** 2026-06-10
