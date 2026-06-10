# Phase 8: Demo & Writeup - Research

**Researched:** 2026-06-10
**Domain:** Offline Gradio CPU demo, slim inference checkpoint, research notebook, technical writeup consolidation
**Confidence:** HIGH (both carried research questions resolved empirically / from primary sources)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Writeup shape & story (DOC-01)**
- **D-01 — README + REPORT structure.** `README.md` is the compelling front door: what/why,
  demo evidence, quickstart, headline results, link to the deep dive. `docs/REPORT.md` carries
  the full technical narrative (architecture, training, evaluation, ablations, design
  decisions). Reviewers skim the README; the serious ones click through.
- **D-02 — Vision-led framing.** Lead with the PersonaCore thesis — *memory lives in the
  weights, privacy by design* — then present Milestone 1 as the rigorously-built from-scratch
  foundation with the LoRA/EWC seams already in place (named `nn.Linear` projections,
  `assemble_loss`, open-dict checkpoints). Be honest that M2 (the weight-memory mechanism) is
  upcoming; the writeup sells ambition AND demonstrated depth, never overclaims.
- **D-03 — Decision-driven REPORT.** Organize `docs/REPORT.md` around design decisions: each
  section presents a choice (byte-level BPE, weight tying, pre-norm, residual-scaled init,
  fp32-on-MPS training, …), the rationale, and the evidence that validates it (unit test,
  ablation row, or curve). Engineering judgment, not a nanoGPT tutorial walkthrough. Source
  material: the per-phase VERIFICATION.md notes, `results/results.md`, `results/samples.md`,
  `logs/run.csv`.
- **D-04 — README proof = demo GIF + numbers.** An animated GIF of the Gradio demo streaming
  a story on CPU, plus a compact results block (13.9M params, headline full-val PPL **2.1066**
  over 12,636,922 tokens, ablation one-liner) and a quickstart. Motion proves "it works on a
  laptop" instantly.

**Notebook narrative scope (DEMO-03)**
- **D-05 — Results showcase.** `demo.ipynb` is the focused evidence artifact: load the model,
  exact param count, training/val curves from `logs/run.csv`, headline PPL, the EVAL-03
  ablation cohort rendered as plots + table (from `results/abl_*.csv` / `results/results.md`),
  and live sampling. It complements the REPORT (which owns the WHY-prose) without duplicating it.
- **D-06 — Live cells, committed WITH executed outputs.** Cells genuinely run on CPU
  (re-runnable end-to-end for anyone with the checkpoint), and the notebook is committed with
  outputs so GitHub's renderer shows curves and samples to reviewers who never execute it.
- **D-07 — Sampling section = settings tour.** One fixed prompt generated under a small grid —
  greedy vs temperature vs top-k/top-p — showing HOW each sampling choice changes the text.
  Exercises the Phase-6 from-scratch sampling toolkit visibly; seeded for reproducibility.
- **D-08 — Notebook loads the slim checkpoint.** `demo.ipynb` loads the new slim DEMO-02
  artifact (safe `weights_only=True` path), the same artifact the Gradio demo uses — notebook,
  demo, and offline test all converge on one shippable artifact. `best.pt` stays the
  training/resume checkpoint only.

### Claude's Discretion
- **Demo UX & framing (DEMO-01):** how the chat UI honestly frames a TinyStories generator
  that has no conversational tuning yet (story-completion framing vs chat metaphor), multi-turn
  history handling (fresh story per message vs concatenation), and which controls beyond the
  locked temperature/top-k (e.g. top-p, max tokens) are exposed. Honor D-02's no-overclaim
  posture: the demo must not pretend to be a tuned chatbot.
- **Checkpoint packaging & distribution (DEMO-02):** exact slim format (`torch.save` state_dict
  loaded `weights_only=True` is the locked safe-load bar; `safetensors` is the CLAUDE.md-
  recommended option for the shippable artifact — planner picks), what ships alongside (config,
  pointer to `artifacts/tokenizer.json`), and whether the ~55MB weights are committed, attached
  to a GitHub Release, or regenerable-by-script (checkpoints are currently gitignored).
- **KV-cache:** measure CPU generation latency first (researcher); only add a cache if the demo
  is unacceptably slow — it is otherwise out of M1 scope (carried decision).
- **GIF tooling / capture mechanics** for D-04, notebook plotting style, QA-01 consolidation
  mechanics (the suite already exists and is CPU-only — this is a verification gate, not new
  test development).

### Deferred Ideas (OUT OF SCOPE)
- **KV-cache for CPU inference latency** — researcher measures actual demo latency first;
  implement only if unacceptable (carried from Phases 5/6; otherwise Milestone 2).
- **Teach-then-recall + EWC no-forgetting demos, weight-delta heatmaps** — Milestone 2 payoff
  (the writeup's roadmap section may preview them).
- **Strided/sliding-window PPL** — possible REPORT footnote only (already noted in
  `results/results.md`); no new compute.
- **Rewiring the training loop's sample hook to call `generate()`** — cleanup idea from
  Phase 6, still out of scope.
- **Demo UX & framing and Checkpoint packaging details** — not deferred from the phase, but
  delegated to researcher/planner discretion (see Claude's Discretion above).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DEMO-01 | Gradio local web UI (`gr.ChatInterface`, offline `share=False`) runs the model on laptop CPU | Gradio 5.50.0 streaming/offline behavior verified from wheel source; cumulative-yield callback pattern over the existing `generate_text` delta stream; offline launch recipe (analytics env var + `analytics_enabled=False`; fonts already bundled locally in 5.50.0) |
| DEMO-02 | Slim fp32 inference checkpoint (no optimizer state, safe `weights_only` load) loads and generates on CPU, verified by an offline test | Empirically verified end-to-end: slim dict (`state_dict` + config + SHA) via `torch.save` → 55.6 MB → `weights_only=True` load → generation works. Tied-weight round-trip confirmed. CI-safe test pattern identified (tiny-model mechanism test; real artifact gated by skipif) |
| DEMO-03 | `demo.ipynb` reads CSV log, shows curves + sampling + exact param count | `logs/run.csv` columns confirmed (`step,train_loss,val_loss,lr,tokens,wall_clock`, 201 rows); param count 13,891,584 re-verified; ablation CSVs committed in `results/`; **pitfall: `logs/run.csv` is gitignored — must be committed (e.g. copy to `results/`) for re-runnability** |
| DOC-01 | Polished technical writeup (README + docs/REPORT.md) | Source inventory confirmed: 6 phase VERIFICATION.md files exist, `results/results.md` + `results/samples.md` carry caveats verbatim; measured demo throughput (~95–105 tok/s CPU) is a new README-worthy number |
| QA-01 | Full per-component suite green via pytest | Verified TODAY in `.venv` (Python 3.11.15, torch 2.7.1): **122 passed, 1 skipped (CUDA fp16 smoke on CPU), 69.9s** — consolidation gate, not new test authoring; only new test is the DEMO-02 slim-checkpoint test |
| QA-02 | Reproducibility discipline (config-in-checkpoint, seeds, git SHA) | Verified: `best.pt` embeds `model_config`/`train_config`/`git_sha` (3a46815…, step 49000); slim format carries `model_config` + `git_sha` forward so the shipped artifact keeps QA-02 intact |
</phase_requirements>

## Summary

Both carried research questions are resolved with primary evidence. **(1) KV-cache: NOT
needed.** Measured on this machine's CPU inside the project venv (torch 2.7.1, 6 threads), the
existing `generate()` path produces **~95–105 tok/s sustained** (manual attention; ~105 tok/s
steady-state with sdpa) on the real 13.9M-param `best.pt` — a complete ~200-token story streams
in ~2 seconds, first visible chunk in milliseconds. That is ~10× faster than reading speed; the
KV-cache stays deferred to Milestone 2, and the measured number itself is a README-worthy proof
point. **(2) Gradio 5 offline streaming: confirmed from the 5.50.0 wheel source** (the pin
`gradio>=5,<6` resolves to 5.50.0; note gradio.app docs now default to Gradio 6). Streaming =
a generator callback that yields the **cumulative** response (the project's `generate_text`
yields deltas — the callback accumulates). Fully-offline launch requires only
`GRADIO_ANALYTICS_ENABLED=False` set before `import gradio` (this also gates the
`version_check()` HTTP ping) — the default theme in 5.50.0 uses `LocalFont("IBM Plex Sans")`
with `.woff2` files bundled in the wheel, so **no Google Fonts CDN call happens at all**; the
old offline-fonts horror stories are Gradio 3/4-era.

The slim checkpoint path was also verified end-to-end: a dict of `{state_dict, model_config,
git_sha, step, val_loss}` saved with `torch.save` is **55.6 MB** (torch deduplicates the tied
`wte`/`lm_head` storage), loads under the locked `weights_only=True` bar, and generates
correctly on CPU. The phase is mostly assembly and writing; the genuinely new code is one
export script, one launcher script, one test file, and one notebook. Two environment gaps
need plan tasks: the `[demo]` extra (gradio, matplotlib) is not yet installed in `.venv`, and
no notebook-execution tooling (`ipykernel`/`nbconvert`) or GIF tooling (`ffmpeg`) exists yet.
One repo-hygiene trap: `logs/`, `checkpoints/`, and `*.pt` are gitignored, so the notebook's
required data source `logs/run.csv` is currently untracked and the slim `.pt` cannot be
committed as-is — the plan must commit the curve CSV (e.g. into `results/`) and distribute the
weights via a GitHub Release.

**Primary recommendation:** Build the demo as a thin `scripts/demo_app.py` wrapping
`generate_text` in a cumulative-yield `gr.ChatInterface(type="messages", ...)` callback with
story-completion framing; ship one slim `torch.save`/`weights_only=True` artifact consumed by
demo, notebook, and test; no KV-cache.

## Project Constraints (from CLAUDE.md)

- **GSD workflow enforcement:** file changes only through GSD commands (this phase: plan → execute).
- **Python 3.11 venv MANDATORY** — never validate against the system Python 3.14; use `.venv/bin/python` (verified: `.venv` → Python 3.11.15).
- **Zero budget / offline / on-device:** no network dependencies at demo runtime; no wandb/SaaS; demo must run on laptop CPU with no internet.
- **Stack pins:** `gradio>=5,<6`, `matplotlib~=3.10` (already in `[demo]` extra); torch 2.7.* local; pytest CPU-only and GPU/MPS-free.
- **From-scratch ethos:** no HF transformers/PEFT model code; tokenizer loaded data-only from `artifacts/tokenizer.json`, never retrained.
- **safetensors recommended for shippable weights** (CLAUDE.md) — but CONTEXT.md locks `weights_only=True` as the safe-load bar and delegates the format pick to the planner (see Standard Stack / Architecture Patterns).
- **Notebook keeps heavy training out** — `demo.ipynb` loads a checkpoint + CSV log and renders the narrative.
- **Thin `scripts/` entry points, no argparse** (Phase-1 D-04, confirmed in `scripts/evaluate.py`).
- **Shippable artifacts must never execute code on load** (tokenizer.json precedent T-02-05) — the slim checkpoint's `weights_only=True` requirement is the same principle.
- **Never commit Kaggle tokens / checkpoints / logs** (`.gitignore` covers `checkpoints/`, `*.pt`, `logs/`, `data/`).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Token generation / sampling | Python package (`personacore.generation`) | — | Already built (Phase 6); demo and notebook are pure consumers |
| Slim checkpoint export | Script (`scripts/export_slim.py`) | Package helper (optional) | One-shot transformation of `best.pt`; thin-script convention |
| Safe checkpoint load | Package consumer code (demo/notebook/test) | — | `torch.load(..., weights_only=True)` at every consumption site |
| Chat UI + streaming | Gradio server (localhost, `scripts/demo_app.py`) | Browser (rendering only) | Gradio serves all assets locally; browser holds no logic; `save_history` would be browser localStorage (leave default False) |
| Evidence rendering (curves/tables) | `demo.ipynb` (matplotlib, executed outputs) | GitHub renderer (static display) | D-05/D-06: live cells, committed with outputs |
| Narrative / results prose | `README.md` + `docs/REPORT.md` (static markdown) | — | D-01/D-03; numbers re-cited from committed `results/`, never recomputed |
| Test gate | pytest in `.venv` + CPU-only CI | — | QA-01 consolidation; new slim-checkpoint test must pass on CI without the real artifact |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| gradio | 5.50.0 (pin `>=5,<6` resolves here) | `gr.ChatInterface` streaming chat UI | Already a locked project decision; 5.50.0 verified: local fonts bundled, analytics fully gateable, `type="messages"` supported `[VERIFIED: PyPI + wheel source inspection]` |
| torch | 2.7.1 (installed) | Model load + inference + slim save | Already installed in `.venv`; `weights_only=True` load of a tensors+primitives dict verified working `[VERIFIED: ran in .venv]` |
| matplotlib | ~=3.10 (3.10.9 current) | Notebook curves/ablation plots | Already pinned in `[demo]` extra `[VERIFIED: pip index versions]` |
| pytest | 9.0.3 (installed) | QA-01 gate + new DEMO-02 test | Already the project framework; suite green today `[VERIFIED: ran suite]` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| ipykernel | 7.3.0 | Kernel for executing `demo.ipynb` | Required to execute the notebook in `.venv` `[ASSUMED — see Package Legitimacy Audit]` |
| nbconvert | 7.17.1 | `jupyter nbconvert --to notebook --execute --inplace demo.ipynb` | Produces the committed-with-outputs notebook reproducibly (D-06) `[ASSUMED — see Package Legitimacy Audit]` |
| imageio-ffmpeg | 0.6.0 | pip-installable static ffmpeg binary for GIF conversion | Only if `ffmpeg` is not installed by other means (neither ffmpeg nor gifski is on this machine) `[ASSUMED — see Package Legitimacy Audit]` |
| safetensors | 0.8.0 | OPTIONAL alternative slim format | Only if the planner picks safetensors over the verified torch.save path — see shared-tensor pitfall `[ASSUMED — see Package Legitimacy Audit]` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `torch.save` slim dict + `weights_only=True` (recommended, VERIFIED) | `safetensors` | safetensors is framework-agnostic and unpickle-free, BUT (a) `save_file` **errors on shared tensors** — tied `wte.weight`/`lm_head.weight` share memory, requiring `save_model`/duplicate-stripping + re-tie discipline; (b) config can only ride in `Dict[str,str]` metadata (JSON-encoded string), breaking the clean config-travels-with-weights idiom; (c) new dependency. `weights_only=True` already meets the locked safe-load bar (restricted unpickler: tensors + primitive containers only, no arbitrary code execution) |
| nbconvert headless execution | Run cells interactively in JupyterLab/VS Code | Interactive is fine for authoring; nbconvert gives a clean sequential top-to-bottom execution for the committed artifact |
| imageio-ffmpeg's bundled ffmpeg | `brew install ffmpeg` / Gifski.app / Kap.app | brew/apps work too; the pip wheel keeps everything inside the documented venv workflow |
| GitHub Release asset for the 55.6 MB weights | Commit to repo / Git LFS | Committing bloats every clone and fights the `*.pt` gitignore (a deliberate "memory lives in weights — never commit them" posture); LFS has free-tier bandwidth quotas. Release asset + regeneration script is cleanest |

**Installation:**
```bash
source .venv/bin/activate
pip install -e ".[cpu,demo]" --extra-index-url https://download.pytorch.org/whl/cpu
pip install ipykernel nbconvert        # notebook execution (consider adding to [dev] or [demo] extra)
# optional, only for GIF conversion if ffmpeg is absent:
pip install imageio-ffmpeg
```

**Version verification (done 2026-06-10):**
- `gradio` latest = 6.17.3; latest 5.x = **5.50.0** (what the project pin installs) `[VERIFIED: pip index versions]`
- `matplotlib` 3.10.9; `safetensors` 0.8.0; `ipykernel` 7.3.0; `nbconvert` 7.17.1; `imageio-ffmpeg` 0.6.0 `[VERIFIED: pip index versions]`
- `.venv`: Python 3.11.15, torch 2.7.1, pytest 9.0.3 installed; gradio/matplotlib NOT yet installed `[VERIFIED: pip list]`

## Package Legitimacy Audit

slopcheck could not be run in this environment (sandbox denied installing/executing it).
Per protocol, packages newly recommended by this research are tagged `[ASSUMED]` and the
planner must gate each first install behind a `checkpoint:human-verify` task. Read-only
registry verification was performed for all of them.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| gradio | PyPI (5.50.0) | ~6 yrs, 400+ releases | very high | github.com/gradio-app/gradio | unavailable | Approved — already a locked pyproject `[demo]` dependency, wheel inspected directly in this session |
| matplotlib | PyPI (3.10.9) | ~20 yrs | very high | github.com/matplotlib/matplotlib | unavailable | Approved — already a locked pyproject `[demo]` dependency |
| ipykernel | PyPI (7.3.0) | ~10 yrs | very high | github.com/ipython/ipykernel | unavailable | `[ASSUMED]` — planner gates install behind checkpoint:human-verify |
| nbconvert | PyPI (7.17.1) | ~10 yrs | very high | github.com/jupyter/nbconvert | unavailable | `[ASSUMED]` — planner gates install behind checkpoint:human-verify |
| imageio-ffmpeg | PyPI (0.6.0) | ~7 yrs | high | github.com/imageio/imageio-ffmpeg | unavailable | `[ASSUMED]`, optional — planner gates install behind checkpoint:human-verify |
| safetensors | PyPI (0.8.0) | ~4 yrs | very high | github.com/huggingface/safetensors | unavailable | `[ASSUMED]`, optional — only if the safetensors format is picked |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

*slopcheck was unavailable at research time — packages not already pinned in `pyproject.toml`
are tagged `[ASSUMED]` and each first install should be gated behind a `checkpoint:human-verify`
task.*

## Empirical Results (carried research questions)

### 1. KV-cache decision: NOT NEEDED — stays deferred to Milestone 2

Measured in `.venv` (Python 3.11.15, torch 2.7.1, 6 CPU threads, this M3 machine), real
`checkpoints/best.pt` (13,891,584 params, block_size 256), via the existing
`generate_text_str` path (no cache, full re-forward each step), prompt "Once upon a time,
there was a little dog named Max.", temperature 0.8 / top_k 50, seeded `[VERIFIED: ran in .venv]`:

| attn_impl | tokens requested | tokens produced | wall time | tok/s |
|-----------|-----------------|-----------------|-----------|-------|
| manual (model default) | 100 | 100 | 0.79 s | 127.0 |
| manual | 256 | 207 (EOS) | 2.20 s | 94.2 |
| manual | 400 | 207 (EOS) | 2.16 s | 95.8 |
| sdpa | 100 | 100 | 0.72 s | 138.4 |
| sdpa | 256 | 207 (EOS) | 1.98 s | 104.6 |

- Steady-state (context saturated at block_size 256): **~95 tok/s manual, ~105 tok/s sdpa**.
- First streamed chunk arrives in **milliseconds** (one short-prompt forward).
- A complete TinyStories-length story (~200 tokens, ends naturally on EOS) streams in **~2 s**.
- Conclusion: 10×+ faster than human reading speed; the demo experience is excellent without a
  KV-cache. **Resolution of the carried blocker: KV-cache is out of M1 scope; defer to M2.**
- Bonus: "~100 tokens/sec on a laptop CPU" is itself a D-04 README headline number.
- `attn_impl="sdpa"` gives ~10% more throughput and is equivalence-tested
  (`test_gpt_attention_equiv.py`); either is acceptable for the demo — manual (the default)
  is already more than fast enough and is the zero-surprise choice.

### 2. Slim checkpoint mechanics — verified end-to-end

`[VERIFIED: ran in .venv]`:
- Slim dict `{schema_version, model: state_dict, model_config: dict, git_sha: str, step: int, val_loss: float}` saved with `torch.save` → **55.6 MB** (torch serializes the tied `wte.weight`/`lm_head.weight` shared storage ONCE; the naive per-key sum would be 68.1 MB).
- `torch.load(path, weights_only=True)` succeeds — plain dicts/str/int/float/tensors are all admissible under the restricted unpickler. Config and git SHA travel inside the same file (QA-02 preserved: best.pt's recorded SHA `3a46815d…`, step 49000, val_loss 0.7378 all round-tripped).
- `GPT(ModelConfig(**loaded["model_config"]))` + `load_state_dict` + generation on CPU works; the freshly-constructed model is tied at `__init__` (gpt.py:184 `self.lm_head.weight = self.wte.weight`), and `load_state_dict` writes through the shared tensor — tying survives the round-trip (assert with the existing `data_ptr()` test idiom; note the modules are `model.wte` / `model.lm_head`, no `transformer.` prefix).

### 3. Gradio 5.50.0 offline + streaming facts (from the wheel source)

All `[VERIFIED: gradio-5.50.0-py3-none-any.whl source inspection]`:
- **Streaming contract:** the ChatInterface `fn` is a generator; each `yield` is the **full cumulative response so far**, which replaces the displayed message (Gradio diffs server→client internally). The project's `generate_text` yields **deltas** — the callback must accumulate (`acc += delta; yield acc`).
- **`type` parameter:** `Literal["messages","tuples"] | None = None`; `"tuples"` is documented deprecated. **Pass `type="messages"`** — history arrives as openai-style `{"role","content"}` dicts.
- **`additional_inputs`:** components render in an accordion under the chatbot; their values are passed to `fn` positionally **after** `(message, history)`.
- **Analytics & version ping:** `analytics_enabled()` reads `os.getenv("GRADIO_ANALYTICS_ENABLED", "True") == "True"`. In `Blocks.__init__`: parameter → env var → default-True resolution; if enabled it spawns a `version_check()` thread that does `httpx.get("https://api.gradio.app/pkg-version", timeout=3)`. **Setting the env var (and/or `analytics_enabled=False`) disables BOTH telemetry and the version ping.** Set `os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"` at the top of the launcher *before* `import gradio`, and pass `analytics_enabled=False` to `ChatInterface` — belt and braces. When disabled, Gradio itself sets `HF_HUB_DISABLE_TELEMETRY=True`.
- **Fonts are LOCAL in 5.50.0:** the base theme defaults to `fonts.LocalFont("IBM Plex Sans")` / `LocalFont("IBM Plex Mono")`, whose CSS is `@font-face { src: url('static/fonts/…woff2') }` served by the local Gradio server; the `.woff2` files ship inside the wheel (`gradio/templates/frontend/static/fonts/IBMPlex*/`). **No Google Fonts CDN request with the default theme.** (The well-known offline-fonts issues are Gradio 3/4-era; do not import Gradio-6-doc claims that the default is a GoogleFont.)
- **`share=False`** (the default) → no frpc tunnel binary download, binds localhost (`GRADIO_SERVER_NAME` default `127.0.0.1`, port 7860).
- **`ssr_mode`** defaults to **False** locally (None → env `GRADIO_SSR_MODE` → False); the SSR-only Google-Fonts issue (gradio#10101) does not apply.
- **Queue/streaming** work locally with no extra config; `save_history=False` default (browser localStorage if enabled — keep default); `cache_examples` defaults False outside Spaces (keep — caching would run the model at launch).
- Other signature facts: `analytics_enabled: bool | None = None`, `api_name="chat"`, `concurrency_limit="default"` (=1 via queue, fine for a single-user local demo).

## Architecture Patterns

### System Architecture Diagram

```
                    checkpoints/best.pt  (159 MB training/resume state, gitignored, local-only)
                            │
                            ▼
              scripts/export_slim.py  (strip optimizer/scheduler/RNG; keep
                            │           model state_dict + model_config + git_sha)
                            ▼
            checkpoints/model_slim.pt  (55.6 MB, torch.save, weights_only=True-loadable)
              │  local file; distributed as a GitHub Release asset
              │
    ┌─────────┼──────────────────────────────┐
    ▼         ▼                              ▼
 Gradio demo  demo.ipynb                tests/test_slim_checkpoint.py
 scripts/     (D-08: loads slim ckpt;   (mechanism test on a TINY GPT in CI;
 demo_app.py   curves from run.csv;      real-artifact integration check
    │          ablation plots from       skipped when file absent)
    │          results/abl_*.csv;
    │          settings-tour sampling)
    ▼
 gr.ChatInterface(type="messages", analytics_enabled=False)
    │  callback: accumulate generate_text() deltas → yield cumulative
    ▼
 localhost:7860 (share=False, zero outbound network calls)
    │
    ▼
 screen capture → GIF → README.md hero asset (D-04)

 artifacts/tokenizer.json ──(data-only load)──▶ demo + notebook + test
 logs/run.csv + results/*.{csv,md} ──▶ demo.ipynb plots + README numbers + docs/REPORT.md
 .planning/phases/*/*-VERIFICATION.md ──(consolidation)──▶ docs/REPORT.md ◀──link── README.md
```

### Recommended Project Structure (new files only)

```
PersonaCore/
├── README.md                      # D-01/D-04 front door (GIF + numbers + quickstart + REPORT link)
├── docs/
│   └── REPORT.md                  # D-03 decision-driven technical narrative
├── demo.ipynb                     # D-05..D-08 results showcase, committed WITH outputs
├── assets/
│   └── demo.gif                   # README hero GIF (small, committed)
├── scripts/
│   ├── export_slim.py             # best.pt → checkpoints/model_slim.pt (thin, no argparse)
│   └── demo_app.py                # Gradio launcher (thin, no argparse)
├── results/
│   └── run.csv                    # COMMITTED copy of the 50k training curve (see Pitfall 2)
└── tests/
    └── test_slim_checkpoint.py    # DEMO-02 offline load/generate test (CPU-only, CI-safe)
```

### Pattern 1: Cumulative-yield Gradio callback over the delta-streaming wrapper
**What:** Adapt `generate_text` (yields string deltas) to ChatInterface's cumulative-yield contract.
**When to use:** `scripts/demo_app.py`.
**Example:**
```python
# Source: gradio 5.50.0 chat_interface.py docstring + guides/creating-a-chatbot-fast
import os
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"  # BEFORE import gradio — kills telemetry + version ping
import gradio as gr
import torch

from personacore.config import ModelConfig
from personacore.generation import generate_text
from personacore.model import GPT
from personacore.tokenizer import from_json

SLIM_PATH = "checkpoints/model_slim.pt"

ckpt = torch.load(SLIM_PATH, map_location="cpu", weights_only=True)  # locked safe-load bar
config = ModelConfig(**ckpt["model_config"])
model = GPT(config)
model.load_state_dict(ckpt["model"])
model.eval()
tokenizer = from_json("artifacts/tokenizer.json")  # frozen, data-only


def tell_story(message, history, temperature, top_k, max_new_tokens):
    # Fresh story per message (no history concatenation — the model has no dialogue tuning).
    acc = ""
    for delta in generate_text(
        model, tokenizer, message,
        max_new_tokens=int(max_new_tokens),
        temperature=float(temperature),
        top_k=int(top_k) if top_k else None,
    ):
        acc += delta
        yield acc  # Gradio contract: yield the FULL response so far, not the delta.


demo = gr.ChatInterface(
    tell_story,
    type="messages",                # "tuples" is deprecated in 5.x
    analytics_enabled=False,
    title="PersonaCore — TinyStories story completion (13.9M params, fully on-device)",
    description=(
        "A from-scratch GPT running on your CPU. Type a story opening and the model "
        "continues it. This is the Milestone-1 base model — no chat tuning, no "
        "personalization yet (that's Milestone 2)."
    ),
    additional_inputs=[
        gr.Slider(0.1, 1.5, value=0.8, step=0.05, label="Temperature"),
        gr.Slider(0, 200, value=50, step=1, label="Top-k (0 = disabled)"),
        gr.Slider(16, 1024, value=400, step=16, label="Max new tokens"),
    ],
)

if __name__ == "__main__":
    demo.launch(share=False)  # localhost only; no tunnel, no CDN, no analytics
```

### Pattern 2: Slim export + safe load (VERIFIED in this session)
**What:** One shippable artifact carrying weights + config + provenance, loadable with no code execution.
**When to use:** `scripts/export_slim.py`; every consumer loads identically.
**Example:**
```python
# Source: verified empirically in .venv this session; torch.load weights_only semantics per
# https://docs.pytorch.org/docs/stable/generated/torch.load.html
import torch

full = torch.load("checkpoints/best.pt", map_location="cpu", weights_only=False)  # trusted own file
slim = {
    "schema_version": 1,
    "model": full["model"],                # state_dict only — no optimizer/scheduler/RNG
    "model_config": full["model_config"],  # plain dict of primitives (QA-02: config travels)
    "git_sha": full["git_sha"],            # provenance (QA-02)
    "step": full["step"],
    "val_loss": float(full["val_loss"]),
}
torch.save(slim, "checkpoints/model_slim.pt")  # 55.6 MB (tied storage stored once)

# Every consumer (demo, notebook, test):
ckpt = torch.load("checkpoints/model_slim.pt", map_location="cpu", weights_only=True)
```

### Pattern 3: CI-safe DEMO-02 test (mechanism + gated integration)
**What:** CI has no 55.6 MB artifact (`checkpoints/` gitignored), so test the export/load/generate
**mechanism** on a tiny GPT, and gate a real-artifact check behind a skipif.
**When to use:** `tests/test_slim_checkpoint.py`.
**Example:**
```python
# Source: existing project idioms (test_best_ckpt.py tiny-model pattern; test_mps_smoke skipif style)
import pathlib
import pytest
import torch
from personacore.config import ModelConfig

TINY = ModelConfig(block_size=32, n_layer=1, n_head=2, n_embd=16)  # vocab/eos stay locked

def test_slim_roundtrip_weights_only(tmp_path):
    # build tiny GPT -> export slim via the export helper -> load weights_only=True ->
    # assert: no optimizer key, config round-trips, tied data_ptr survives, greedy
    # generation is deterministic and non-empty.
    ...

REAL = pathlib.Path("checkpoints/model_slim.pt")

@pytest.mark.skipif(not REAL.exists(), reason="real slim artifact not present (CI)")
def test_real_slim_artifact_generates_on_cpu():
    ...
```

### Pattern 4: Reproducible notebook execution
**What:** Author `demo.ipynb`, then execute top-to-bottom headlessly so committed outputs are
clean and sequential (D-06).
```bash
.venv/bin/python -m ipykernel install --user --name personacore  # once
.venv/bin/jupyter nbconvert --to notebook --execute --inplace demo.ipynb
```
Notebook cell order per D-05: (1) intro markdown (thesis framing, no overclaim), (2) load slim
ckpt + print exact param count (13,891,584) + git SHA, (3) train/val curves from the committed
run CSV (`step,train_loss,val_loss,lr,tokens,wall_clock`; 201 rows; plot loss vs step and vs
tokens), (4) headline PPL **re-cited, not recomputed** (2.1066 over 12,636,922 tokens), (5)
ablation cohort: plot the four `results/abl_*.csv` val-loss curves + render the results.md table
**with the not-comparable-to-headline caveat verbatim**, (6) D-07 settings tour: one fixed
prompt × {greedy, temperature 0.8, top-k 50, top-p 0.95} with a seeded `torch.Generator`.

### Pattern 5: GIF capture (D-04 hero asset)
**What:** Record the streaming demo, convert to a small GIF.
**How (macOS, zero brew):** record with QuickTime / `screencapture -v` (interactive — this is a
human-action step), then two-pass palette conversion for quality/size:
```bash
FF=$(.venv/bin/python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())")
"$FF" -i demo.mov -vf "fps=12,scale=720:-1:flags=lanczos,palettegen" palette.png
"$FF" -i demo.mov -i palette.png -filter_complex "fps=12,scale=720:-1:flags=lanczos[x];[x][1:v]paletteuse" assets/demo.gif
```
Keep the GIF short (~10–15 s, one story) and well under ~10 MB so the README renders snappily.
`[ASSUMED]` — standard ffmpeg recipe from training knowledge; verify output size/quality at execution time.

### Anti-Patterns to Avoid
- **Yielding deltas to ChatInterface:** the UI would show only the last fragment. Always accumulate.
- **Concatenating chat history into the prompt:** the model has zero dialogue tuning; feeding prior turns back produces incoherent output and overclaims chat ability (violates D-02). Fresh story per message.
- **Recomputing the headline PPL in the notebook/demo:** re-cite `results/` numbers; the deterministic sweep is already committed (CONTEXT: "re-cite, don't recompute").
- **`pip install` outside `.venv` / validating on system Python 3.14:** CLAUDE.md hard rule.
- **Copying Gradio 6 doc snippets:** gradio.app docs now default to v6 (6.17.3 current); the project runs 5.50.0. Behavior verified here is from the 5.50.0 wheel.
- **Letting the writeup claim "conversational AI that knows you" for M1:** D-02 honesty bar — M1 is the from-scratch foundation; M2 delivers weight-memory.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Streaming chat UI | Custom FastAPI + websockets + HTML | `gr.ChatInterface` | Locked decision; queueing, stop button, history UI, streaming diffs all built in |
| Safe weight serialization | Custom binary format | `torch.save` + `weights_only=True` (or safetensors) | Restricted unpickler already guarantees no-code-execution; verified working |
| GIF encoding | Frame-by-frame PIL writer | ffmpeg (via imageio-ffmpeg) palettegen/paletteuse | Palette quantization + dithering quality is a solved problem |
| Notebook execution-with-outputs | Manual cell-running discipline | `jupyter nbconvert --execute --inplace` | Guarantees clean sequential execution counts for the committed artifact |
| CSV parsing/plotting | Custom parser | `numpy.genfromtxt`/`csv` + matplotlib | Already the project's logging pattern |

**Key insight:** This phase's value is assembly, evidence, and prose — every hard component
(generation, eval numbers, tests) already exists. New code should stay thin.

## Common Pitfalls

### Pitfall 1: Gradio cumulative-yield vs the project's delta-streaming wrapper
**What goes wrong:** Wiring `generate_text` straight into ChatInterface shows only the last token fragment.
**Why:** ChatInterface replaces the message with each yielded value; `generate_text` yields suffix deltas (by design, D-06 of Phase 6).
**How to avoid:** Accumulate in the callback (`acc += delta; yield acc`).
**Warning signs:** The chat bubble "flickers" single words instead of growing text.

### Pitfall 2: `logs/run.csv` is gitignored — the notebook's required data source isn't in the repo
**What goes wrong:** `demo.ipynb` (and a fresh clone) can't re-run D-05's training-curve cell; DEMO-03's "reads the CSV log" silently depends on an untracked local file.
**Why:** `.gitignore` ignores `logs/` wholesale (verified: `git check-ignore` flags `logs/run.csv`); the ablation CSVs were committed under `results/` but the 50k-run curve never was.
**How to avoid:** Commit the curve as evidence — copy to `results/run.csv` (consistent with the committed `abl_*.csv`) or add a `!logs/run.csv` exception; point the notebook at the committed path.
**Warning signs:** Notebook executes locally but CI/fresh-clone execution fails on `FileNotFoundError`.

### Pitfall 3: `*.pt` + `checkpoints/` gitignore blocks committing the slim artifact
**What goes wrong:** Plan task "commit model_slim.pt" silently no-ops or requires gitignore surgery that contradicts the deliberate "never commit checkpoints" posture.
**How to avoid:** Distribute via GitHub Release asset (55.6 MB is fine there; repo files >50 MB trigger GitHub warnings and bloat clones). Ship `scripts/export_slim.py` so anyone with a `best.pt` can regenerate. README quickstart: download Release asset → `checkpoints/model_slim.pt`.
**Warning signs:** `git add checkpoints/model_slim.pt` reports the path is ignored.

### Pitfall 4: safetensors refuses tied weights (if that format is picked)
**What goes wrong:** `safetensors.torch.save_file(model.state_dict())` raises `RuntimeError` about tensors sharing memory — `wte.weight` and `lm_head.weight` are the same storage (MODEL-03 weight tying).
**How to avoid:** If safetensors is chosen: use `save_model`/strip the duplicate `lm_head.weight` key and rely on the model's `__init__` re-tying; carry `model_config`/`git_sha` as JSON in the str→str metadata. Or simply use the verified `torch.save` + `weights_only=True` path. `[ASSUMED — safetensors shared-tensor behavior from training knowledge + HF docs; not executed this session]`
**Warning signs:** RuntimeError mentioning "tensors share memory" at export time.

### Pitfall 5: Analytics env var set after `import gradio`
**What goes wrong:** A telemetry/version-check request can fire from module/Blocks init before your `launch(analytics_enabled=False)` ever runs.
**How to avoid:** `os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"` as the first lines of `scripts/demo_app.py`, before `import gradio`; also pass `analytics_enabled=False`. Verify offline-ness by launching with Wi-Fi off — the UI must load and stream normally (fonts are wheel-local in 5.50.0).
**Warning signs:** Startup hangs ~3 s without network (the version-check timeout), or `httpx` connect errors in logs.

### Pitfall 6: CI breaks on the DEMO-02 test because the real checkpoint doesn't exist there
**What goes wrong:** A test that loads `checkpoints/model_slim.pt` unconditionally fails in GitHub Actions (checkpoints are gitignored).
**How to avoid:** Pattern 3 — tiny-model mechanism test always runs; real-artifact test behind `pytest.mark.skipif(not path.exists(), reason=...)` (project precedent: the CUDA smoke skip, the only skip in today's green run).
**Warning signs:** CI red with `FileNotFoundError` while local suite is green.

### Pitfall 7: Notebook committed with stale/out-of-order outputs or bloated size
**What goes wrong:** GitHub renders half-executed cells, non-sequential execution counts, or a multi-MB ipynb from high-DPI inline figures — undermining the rigor signal (D-06).
**How to avoid:** Final artifact produced by one `nbconvert --execute --inplace` pass in `.venv`; keep figure DPI modest (~100); no training in the notebook (CLAUDE.md).
**Warning signs:** `execution_count` not 1..N monotonic; ipynb file > ~5 MB.

### Pitfall 8: Sampling-tour cells unseeded → notebook not reproducible
**What goes wrong:** D-07 requires the settings tour to be seeded; re-running produces different text and the committed outputs no longer match.
**How to avoid:** A fresh `torch.Generator().manual_seed(...)` per sampled cell (the `generator` kwarg threads through `generate_text`/`generate`); greedy cells are deterministic by construction. Note: identical seeds give identical output only on the same torch version/platform — state the pinned env (torch 2.7.1, CPU) in the notebook preamble.
**Warning signs:** Diff noise in `demo.ipynb` outputs after re-execution.

### Pitfall 9: Overclaiming in README/REPORT
**What goes wrong:** "Conversational AI assistant with weight-based memory" describes the M2 vision, not the M1 artifact; reviewers who run the demo see a TinyStories generator and trust collapses.
**How to avoid:** D-02 framing discipline: thesis first, then "Milestone 1 = the from-scratch foundation (this repo, working today: 13.9M params, PPL 2.1066 over 12,636,922 tokens, ~100 tok/s CPU streaming), Milestone 2 = LoRA+EWC weight-memory (seams already in place)". Carry the rigor signals verbatim: PPL always with its token denominator; ablation cohort always with its not-comparable caveat; samples labeled representative-not-cherry-picked.
**Warning signs:** README sentences about "remembering you" without an explicit M2 qualifier.

## Code Examples

(Primary patterns are inline above. Additional verified facts:)

### Loading curves in the notebook
```python
# Source: logs/run.csv header verified this session: step,train_loss,val_loss,lr,tokens,wall_clock
import csv
import matplotlib.pyplot as plt

with open("results/run.csv") as f:           # committed copy (Pitfall 2)
    rows = list(csv.DictReader(f))
steps = [int(r["step"]) for r in rows]
plt.plot(steps, [float(r["train_loss"]) for r in rows], label="train")
plt.plot(steps, [float(r["val_loss"]) for r in rows], label="val")
plt.xlabel("step"); plt.ylabel("loss"); plt.legend()
```

### Exact parameter count (matches MODEL-05 / results.md)
```python
# Source: verified this session — sum over named_parameters dedups the tied tensor
n_params = sum(p.numel() for p in model.parameters())   # -> 13,891,584
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Gradio 5.x (project pin) | Gradio 6.x is current upstream (6.17.3, 2026-06) | Gradio 6.0 ~Nov 2025 | gradio.app docs default to v6 — verify 5.x behavior against the 5.50.0 wheel (done here); do not bump the pin this phase |
| ChatInterface `type="tuples"` history | `type="messages"` (openai-style dicts) | deprecated through 5.x, removed in 6 | Always pass `type="messages"` |
| `torch.load` default `weights_only=False` | default flipped to `True` in torch 2.6 | torch 2.6 (2025) | The slim artifact's safe-load bar aligns with the modern default; the resume path explicitly opts out (documented in checkpoint.py) |
| Gradio 3/4 Google-Fonts CDN at runtime | 5.50.0 default theme = `LocalFont` + wheel-bundled woff2 | during Gradio 5.x line | Offline launch needs no font workaround |

**Deprecated/outdated:**
- Gradio 3-era offline patches (`gradio-offline`, CDN-rewrite gists): unnecessary on 5.50.0.
- `tuples` chat history format: deprecated.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | ipykernel/nbconvert are the right minimal notebook-execution tooling (slopcheck unavailable → install gated) | Standard Stack | Low — Jupyter-official packages; alternative is interactive execution in an editor |
| A2 | imageio-ffmpeg's bundled ffmpeg handles the .mov→GIF palette pipeline | Pattern 5 | Low — fall back to `brew install ffmpeg` or Gifski.app |
| A3 | safetensors `save_file` errors on tied/shared tensors and `save_model` is the workaround | Pitfall 4 | Low — only matters if safetensors is picked over the verified torch.save path |
| A4 | GitHub Release assets are the right distribution channel for the 55.6 MB weights (vs LFS/commit) | Don't Hand-Roll / Pitfall 3 | Low — user/planner may prefer regenerate-only; flagged as discretion in CONTEXT |
| A5 | ffmpeg GIF two-pass palette recipe parameters (fps/scale) | Pattern 5 | Cosmetic — tune at capture time |

## Open Questions

1. **Weights distribution channel (GitHub Release vs regenerate-only)**
   - What we know: 55.6 MB; `*.pt`/`checkpoints/` deliberately gitignored; CONTEXT leaves this to planner discretion.
   - What's unclear: whether the user wants a public Release on the repo at this point.
   - Recommendation: plan for a Release asset + `export_slim.py` regeneration path; make the Release upload a `checkpoint:human-action` task (needs the user's repo publishing intent).
2. **GIF capture is inherently interactive**
   - Screen-recording the streaming demo can't be fully automated.
   - Recommendation: plan it as a `checkpoint:human-action` (record ~10–15 s) followed by the scripted ffmpeg conversion.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `.venv` Python 3.11 | everything | ✓ | 3.11.15 | — |
| torch (CPU/MPS) | demo, test, notebook | ✓ | 2.7.1 | — |
| pytest | QA-01 | ✓ | 9.0.3 | — |
| gradio | DEMO-01 | ✗ (pinned in `[demo]` extra, not installed) | will resolve 5.50.0 | `pip install -e ".[cpu,demo]"` — plan task |
| matplotlib | DEMO-03 | ✗ (pinned in `[demo]` extra, not installed) | will resolve 3.10.x | same install task |
| ipykernel + nbconvert | DEMO-03 execution | ✗ (in no extra) | 7.3.0 / 7.17.1 | install task (consider adding to an extra for reproducibility) |
| ffmpeg / gifski | D-04 GIF conversion | ✗ | — | `pip install imageio-ffmpeg` (bundled binary) or brew/Gifski.app |
| `checkpoints/best.pt` | slim export source | ✓ (local) | step 49000, SHA 3a46815d | — (irreplaceable without retraining; never delete) |
| `artifacts/tokenizer.json` | demo/notebook/test | ✓ (committed) | schema v1, vocab 8192 | — |
| `logs/run.csv` | DEMO-03 curves | ✓ local, ✗ in git | 201 rows | commit a copy (Pitfall 2) |
| `results/*.csv`, `results.md`, `samples.md` | notebook + writeup | ✓ (committed) | — | — |
| Phase VERIFICATION.md notes (02–07) | DOC-01 source material | ✓ (6 files) | — | — |
| GitHub remote / `gh` | Release-asset distribution | ✓ (`gh` works) | — | regenerate-by-script fallback |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** gradio/matplotlib (install task), ipykernel/nbconvert (install task), ffmpeg (imageio-ffmpeg or brew).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 (in `.venv`) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (testpaths=tests) |
| Quick run command | `.venv/bin/python -m pytest tests/test_slim_checkpoint.py -q` |
| Full suite command | `.venv/bin/python -m pytest -q` (~70 s, verified green today: 122 passed, 1 skipped) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DEMO-02 | Slim ckpt exports, loads `weights_only=True`, generates, keeps config+SHA+tying | unit | `.venv/bin/python -m pytest tests/test_slim_checkpoint.py -q` | ❌ Wave 0 |
| DEMO-01 | Callback yields growing cumulative strings; offline launch | unit (callback) + manual (UI/offline) | callback unit test in the same file or `tests/test_demo_app.py`; UI smoke = human (launch, Wi-Fi off, stream a story) | ❌ Wave 0 |
| DEMO-03 | Notebook executes end-to-end on CPU | smoke | `.venv/bin/jupyter nbconvert --to notebook --execute demo.ipynb --output /tmp/demo_executed.ipynb` (exit code 0) | ❌ (notebook is the deliverable) |
| DOC-01 | README/REPORT complete, honest, numbers carry caveats | manual-only | human review against D-01..D-04 checklist | — |
| QA-01 | Full per-component suite green | full suite | `.venv/bin/python -m pytest -q` | ✅ (122 pass / 1 skip today) |
| QA-02 | Config+seed+SHA discipline holds incl. slim artifact | unit | existing `test_checkpoint.py`/`test_seeding.py` + slim-test asserts on `model_config`/`git_sha` keys | ✅ existing + ❌ slim asserts in Wave 0 |

### Sampling Rate
- **Per task commit:** `.venv/bin/python -m pytest tests/test_slim_checkpoint.py tests/test_generation_text.py -q`
- **Per wave merge:** `.venv/bin/python -m pytest -q`
- **Phase gate:** full suite green + notebook executes + manual offline demo smoke before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_slim_checkpoint.py` — covers DEMO-02 + slim-side QA-02 (tiny-model mechanism + skipif-gated real artifact)
- [ ] (optional) callback unit test for the demo's cumulative-yield adapter — covers the testable slice of DEMO-01
- [ ] Tooling install: `pip install -e ".[cpu,demo]"` + `ipykernel nbconvert` in `.venv` (gated per Package Legitimacy Audit)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no (localhost single-user demo) | — (`share=False`, bind 127.0.0.1 default) |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | `generate_text`'s existing DoS guard (`max_new_tokens` bounded to (0, 4096], raises before the loop — T-06-04); slider ranges enforce sane values; prompt is data-only (encoded, never eval'd) |
| V6 Cryptography | no | — |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Pickle code-execution on checkpoint load | Tampering / EoP | Slim artifact loads `weights_only=True` (restricted unpickler — the phase's locked bar); resume `best.pt` stays trusted-own-file-only (documented in checkpoint.py) |
| Accidental network exposure of the demo | Information Disclosure | `share=False`, default `GRADIO_SERVER_NAME=127.0.0.1`; never set `0.0.0.0` |
| Telemetry leaking usage data offline | Information Disclosure | `GRADIO_ANALYTICS_ENABLED=False` before import + `analytics_enabled=False` (also disables the version-check HTTP ping) |
| Unbounded generation request (DoS) | DoS | Existing 4096-token cap in `generation/text.py`; max-tokens slider ≤ that cap |
| Secrets in committed artifacts | Information Disclosure | Slim ckpt contains only tensors/config/SHA (verified key set); .gitignore already covers tokens/logs/checkpoints |

## Sources

### Primary (HIGH confidence)
- **Empirical runs in `.venv` (this session):** CPU latency benchmark on real `best.pt` (manual + sdpa, 3 lengths); slim save → `weights_only=True` load → generate round-trip (55.6 MB, key set, SHA/step/val_loss); full pytest suite (122 passed, 1 skipped, 69.9 s); `git check-ignore` on `logs/run.csv` / `checkpoints/*.pt`
- **gradio-5.50.0-py3-none-any.whl source** (downloaded from PyPI, inspected): `chat_interface.py` full `__init__` signature + docstring; `analytics.py` (`GRADIO_ANALYTICS_ENABLED` gating, `version_check` → `api.gradio.app/pkg-version`); `blocks.py` (param→env→default resolution, version-check thread, `ssr_mode` default False, `HF_HUB_DISABLE_TELEMETRY`); `themes/base.py` + `themes/utils/fonts.py` (`LocalFont("IBM Plex Sans")`, `static/fonts/` @font-face); wheel manifest (bundled IBMPlex `.woff2` files)
- https://www.gradio.app/docs/gradio/chatinterface + https://www.gradio.app/guides/creating-a-chatbot-fast — cumulative-yield streaming contract, additional_inputs ordering (note: v6 docs; cross-checked against the 5.50.0 wheel)
- https://www.gradio.app/guides/environment-variables — `GRADIO_ANALYTICS_ENABLED` ("True"/"False", default "True"), `GRADIO_SERVER_NAME` (default 127.0.0.1), `GRADIO_SHARE` (default False)
- PyPI registry via `pip index versions` — gradio 6.17.3 / 5.50.0, matplotlib 3.10.9, safetensors 0.8.0, ipykernel 7.3.0, nbconvert 7.17.1, imageio-ffmpeg 0.6.0
- Project files read this session: 08-CONTEXT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md, pyproject.toml, .gitignore, Makefile, checkpoint.py, generation/{core,text}.py, model/gpt.py (tying at L184), config.py, logs/run.csv header, results/results.md, results/samples.md, tests/ inventory

### Secondary (MEDIUM confidence)
- https://www.gradio.app/guides/theming-guide — system-font-string theme pattern (v6 doc; 5.50.0 default already LocalFont so only needed if a custom theme is introduced)
- Gradio offline history: github.com/gradio-app/gradio issues #1450, #4332, #10101 (SSR fonts) — context for why old offline advice doesn't apply to 5.50.0

### Tertiary (LOW confidence)
- safetensors shared-tensor save behavior (A3) — training knowledge + HF docs, not executed
- ffmpeg palettegen GIF recipe parameters (A5) — standard recipe, tune at capture time

## Metadata

**Confidence breakdown:**
- KV-cache decision: HIGH — measured on the real model, real machine, real code path
- Slim checkpoint format: HIGH — full round-trip executed this session
- Gradio 5 streaming/offline: HIGH — read from the exact wheel the pin installs
- Writeup/notebook guidance: HIGH for data sources (verified on disk), MEDIUM for prose-structure recommendations (judgment within locked D-01..D-08)
- GIF tooling: MEDIUM — recipe assumed, tools registry-verified only

**Research date:** 2026-06-10
**Valid until:** ~2026-07-10 (stable: the gradio `<6` pin freezes the only fast-moving dependency)
