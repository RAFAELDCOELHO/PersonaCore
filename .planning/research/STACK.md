# Stack Research — v2.0 Weight-Based Memory

**Domain:** From-scratch LoRA adapters + EWC continual learning + conversational fine-tuning (DailyDialog, PersonaChat) + research-narrative demos and visualizations, layered on the existing v1.0 from-scratch GPT stack (torch 2.7 / MPS fp32 primary, Kaggle P100 fallback, CPU demo)
**Researched:** 2026-06-11
**Confidence:** HIGH (all dataset endpoints HTTP-verified live today with sizes/checksums; formats inspected byte-level; everything else is pure-PyTorch implementation on the already-validated stack)

## TL;DR Prescription

> **Zero new Python dependencies.** Every v2.0 feature — LoRA, EWC, conversational fine-tuning,
> teach-then-recall demo, EWC A/B demo, forgetting curves, weight-delta heatmaps — is implemented
> with the stack already installed: `torch 2.7.*`, `numpy ~=2.4`, `matplotlib ~=3.10`,
> `gradio 5.x`, `pytest`, and the Python stdlib (`json`, `urllib.request`, `tarfile`, `hashlib`).
> The only genuinely *new* stack elements are **two dataset download endpoints** (verified live
> 2026-06-11, checksums below) and the scripts that turn them into `uint16` memmap `.bin` files
> through the existing frozen tokenizer.

- **LoRA = a hand-written `nn.Module`** (`LoRALinear`) wrapping the six named `nn.Linear`
  projections per block (the v1.0 seam). No `peft`, no `loralib`, no
  `torch.nn.utils.parametrize` — plain composition keeps the from-scratch narrative legible and
  the checkpoint format under your control.
- **EWC = pure autograd.** Diagonal (empirical) Fisher from accumulated squared gradients of the
  LM loss over a TinyStories reference sample; quadratic penalty plugged into the existing
  `assemble_loss(..., extra_penalties=())` seam. No `torch.func`, no opacus, no new deps.
- **CRITICAL data fact: the original DailyDialog URL is DEAD.**
  `http://yanran.li/files/ijcnlp_dailydialog.zip` returns **404** (verified 2026-06-11), and the
  canonical HF loading script (`li2017dailydialog/daily_dialog`) points at that same dead URL —
  so the HF `datasets` route is broken too. **Use the ParlAI mirror on Facebook's public CDN**
  (verified live, checksum pinned below).
- **PersonaChat = one plain JSON file from HF's public S3** (`personachat_self_original.json`,
  ~200 MB, verified live 2026-06-11). Plain HTTPS GET — no HF `datasets`, no auth, no API key.
- **Visualizations: matplotlib only.** `imshow` + colorbar covers weight-delta heatmaps;
  forgetting curves come from the existing CSV logger + `evaluate.perplexity()`. **Do not add
  seaborn** — one more dep for zero capability you need.
- **Frozen-tokenizer constraint shapes the data design:** vocab is locked (8192 table, eos 8184,
  547 live ids — no retrain, decided 2026-06-11). **No new special tokens are possible.** Dialogue
  turn markers must be plain text (e.g. `User:` / `Bot:`) that round-trips through the existing
  byte-level BPE.

## Recommended Stack

### Core Technologies (all carried from v1.0 — new roles only)

| Technology | Version | v2.0 Role | Why Recommended |
|------------|---------|-----------|-----------------|
| **PyTorch (`torch`)** | `2.7.*` (local M3/CPU, pinned in pyproject); Kaggle pre-installed (fallback) | LoRA modules, Fisher estimation, EWC penalty, fine-tuning loop | `nn.Module` + `nn.Parameter` + autograd is literally all LoRA and EWC require. `requires_grad_(False)` freezes the base; `p.grad.detach() ** 2` accumulation gives the empirical Fisher diagonal. No version bump needed — nothing in v2.0 touches an API newer than torch 2.0. |
| **NumPy** | `~=2.4` (pinned in pyproject) | Stage-2 corpus memmaps (`dialog_train.bin` etc.), heatmap matrices | Same `uint16` memmap pattern as v1.0 TinyStories — reuse the proven data path verbatim for the conversational corpus. |
| **matplotlib** | `~=3.10` (pinned in pyproject, `demo`/`notebook` extras) | Forgetting curves, weight-delta heatmaps | `plt.imshow(delta_grid, cmap=...)` + `colorbar` is the entire heatmap requirement; line plots off the CSV log are the forgetting curves. Committed-figure deliverables render offline. |
| **Gradio** | `>=5,<6` (pinned in pyproject `demo` extra) | Teach-then-recall demo UI (adapter on/off toggle) | The existing `gr.ChatInterface` demo extends with a checkbox/dropdown to load/unload the LoRA adapter — the visual "same model, memory in the weights" moment. `gr.Blocks` (same package) if side-by-side A/B layout is wanted. |
| **Python stdlib** (`json`, `urllib.request`, `tarfile`, `zipfile`, `hashlib`, `re`/`regex`) | 3.11 venv (mandatory) | Dataset download + parse + detokenize | Both corpora are plain files behind plain HTTPS GETs. `urllib.request` follows the redirects (parl.ai → fbaipublicfiles CDN; HF resolve → xet-bridge) without help. stdlib `json` loads the 200 MB PersonaChat file in seconds on the M3 — no streaming parser needed. |

### Supporting Libraries (carried; v2.0-relevant notes)

| Library | Version | v2.0 Use | Notes |
|---------|---------|----------|-------|
| **pytest** | `~=9.0` (pinned) | LoRA/EWC unit tests | Highest-value tests: (1) LoRA-wrapped forward == base forward when B is zero-init; (2) merged weights `W+BA·(α/r)` forward == adapter forward within fp32 tolerance; (3) only adapter params have `requires_grad`; (4) EWC penalty == 0 at θ*, > 0 after perturbation, and gradient matches `2·λ·F·(θ−θ*)` analytically; (5) Fisher entries all ≥ 0; (6) data scripts round-trip a fixture dialogue through format→encode→decode. All CPU-only, GPU-free, like the existing 137. |
| **safetensors** | 0.4+ (optional, as in v1.0) | Shippable adapter files | An adapter-only state dict is the "persona file" artifact (~0.7–1.3 MB fp32 at r=4–8, see sizing below) — `safetensors` export makes the "your memory is this tiny file of weights" demo prop concrete. Optional; `torch.save` adapter dicts are fine for internal use. |
| **tiktoken** | `~=0.13` (dev extra) | Unchanged | Test oracle only; no v2.0 role beyond existing tokenizer tests. |

### Development Tools (unchanged)

| Tool | Purpose | v2.0 Notes |
|------|---------|------------|
| venv (Python 3.11) + pyproject extras | Reproducible env | No dependency changes → no pyproject edits required for v2.0. |
| ruff | Lint/format | Unchanged. |
| Jupyter/nbconvert | `demo.ipynb` v2 narrative | The EWC A/B comparison (naive vs EWC fine-tune, side-by-side forgetting curves) lives most naturally in the notebook + committed PNGs, not the Gradio app. |
| Kaggle Notebooks (fallback) | Optional P100 fine-tune runs | If used: attach the two raw corpus files as a Kaggle Dataset once (same pattern as TinyStories) so sessions stay offline. See P100 variant notes for the EWC-fp16 caveat. |

## Dataset Acquisition (the real "stack addition")

All endpoints verified live **2026-06-11** with HTTP status, size, and (where downloaded) checksum.

### Primary sources

| Dataset | URL | Size | Status (2026-06-11) | Format |
|---------|-----|------|---------------------|--------|
| **DailyDialog** (ParlAI mirror, Facebook CDN) | `https://dl.fbaipublicfiles.com/parlai/dailydialog/dailydialog.tar.gz` | 2,715,285 B (~2.6 MB) | **200 OK** | tar.gz → `train.json` / `valid.json` / `test.json`, JSONL — one dialogue per line: `{"fold", "topic", "dialogue": [{"emotion", "act", "text"}]}` |
| **PersonaChat** (HF public S3, the `transfer-learning-conv-ai` distribution) | `https://s3.amazonaws.com/datasets.huggingface.co/personachat/personachat_self_original.json` | 209,850,483 B (~200 MB) | **200 OK** | Single JSON: `{"train": [...], "valid": [...]}`; each entry `{"personality": [4–5 persona sentences], "utterances": [{"candidates": [20], "history": [...]}]}` — gold reply is `candidates[-1]`; the last utterance's `history` + its gold reply reconstructs the full dialogue |

**Pinned provenance (record in the fetch script and verify on download):**

- `dailydialog.tar.gz` — **sha256 `c3adb09bd715b9fa5cd1ac41613b7de61eb5afbe477826a6146abefef573e6bb`**, md5 `dec2b7552a62888b667ec162f6d743b1` (matches the S3 ETag). Splits verified by line count: **11,118 / 1,000 / 1,000 = 13,118 dialogues** — exactly the published dataset statistics. Inspected first record matches the original corpus ("Say , Jim , how about going for a few beers after dinner ?").
- `personachat_self_original.json` — S3 ETag `ab09debedcc45366d110b85f78c35e22-26` (multipart — not a plain md5). Compute and commit a sha256 at first download; first/last bytes inspected 2026-06-11 and match the documented thomwolf-gist structure.

### Fallback sources (also verified live 2026-06-11)

| Dataset | Fallback URL | Size | Notes |
|---------|--------------|------|-------|
| DailyDialog | `https://huggingface.co/datasets/ConvLab/dailydialog/resolve/main/data.zip` | 3,738,236 B, 200 OK after redirect | Plain HTTPS GET through HF's resolve endpoint — **no `datasets` library involved**. ConvLab unified format (restructured), so prefer the ParlAI mirror, which preserves the original splits + act/emotion labels. |
| PersonaChat | `https://dl.fbaipublicfiles.com/parlai/personachat/personachat.tgz` | 223,221,886 B, 200 OK | ParlAI's raw distribution (both original + revised personas, `.txt` line format). The S3 JSON is easier to parse; this is the backup if S3 ever vanishes. |

### Why these and not the "official" routes

- **`http://yanran.li/files/ijcnlp_dailydialog.zip` → 404.** The author's hosting is gone, and the
  HF `li2017dailydialog/daily_dialog` repo is a *loading-script* repo whose `_URL` is that dead
  link (verified in `daily_dialog.py` line 41). The HF parquet auto-conversion would work but
  requires `pyarrow`/`pandas` — two heavyweight deps for a 2.6 MB corpus that exists as plain JSON
  on a reliable CDN.
- **Both primary mirrors are on AWS-backed CDNs** (Facebook's `dl.fbaipublicfiles.com`, HF's S3)
  that have served these exact files unchanged since 2019 — but ParlAI the *project* was archived
  on 2023-11-03 (read-only). Treat the CDNs as stable-but-unowned: **download once, verify sha256,
  cache under `data/raw/` (gitignored), and never depend on the network at train time** — same
  discipline as the v1.0 TinyStories flow.
- **Re-hosting:** DailyDialog is **CC BY-NC-SA 4.0** — attaching the 2.6 MB tarball to a GitHub
  Release with attribution is license-compatible insurance (non-commercial portfolio project).
  PersonaChat has **no explicit license** on the S3 distribution (released by Facebook via the
  MIT-licensed ParlAI; HF mirrors list it as unknown) — keep the download script + checksum,
  **do not re-host** (MEDIUM confidence on the licensing read; standard research-use practice).

### Preprocessing pipeline (reuses v1.0 patterns wholesale)

1. **Fetch:** `scripts/fetch_corpora.py` — stdlib `urllib.request` + `hashlib` sha256 verify →
   `data/raw/`. No `requests` needed (it's not in pyproject today; don't add it for two GETs).
2. **Detokenize:** both corpora ship whitespace-tokenized text (`"how about going for a few beers
   after dinner ?"`, `"i ' m"` / lowercase in PersonaChat). Run a small regex detokenizer (the
   existing `regex ~=2026.5` core dep covers it) so the model isn't taught artificial
   space-before-punctuation — the frozen BPE was trained on natural TinyStories spacing.
3. **Format turns as plain text:** e.g. `User: ...\nBot: ...\n` with persona sentences as a
   plain-text preamble for PersonaChat, dialogues separated by the existing eos id 8184.
   **No new special tokens — the vocab is frozen.** Markers encode as multiple byte-level BPE ids;
   at 13.9M params and this corpus size that cost is negligible.
4. **Encode once → `uint16` memmap:** `dialog_train.bin` / `dialog_val.bin` via the existing
   tokenizer + data path. Keep TinyStories `val.bin` untouched — it is the forgetting-curve
   measurement set.
5. **Kaggle fallback only:** upload `data/raw/` once as a private Kaggle Dataset so P100 sessions
   stay offline (same as the v1.0 TinyStories attach).

Scale check: DailyDialog (~13k dialogues, ~1.4M words) + PersonaChat (~18.9k dialogues, ~10k
personas) together are far smaller than TinyStories — preprocessing is minutes, and stage-2
fine-tuning is comfortably inside M3/MPS budgets. The 200 MB PersonaChat JSON parses with stdlib
`json` in one shot (~1–2 GB transient RAM, fine on the M3); a streaming parser (`ijson`) is
unjustified.

## New-Capability → Implementation Map (no new deps)

| v2.0 Feature | Implementation | Stack Used |
|--------------|----------------|------------|
| **LoRA adapters** | `LoRALinear(nn.Module)`: holds the frozen base `nn.Linear` + `A` (r×d_in, Kaiming/normal init) and `B` (d_out×r, **zero-init**) `nn.Parameter`s; forward = `base(x) + (α/r)·(x @ Aᵀ @ Bᵀ)`. Wrap/unwrap utilities target the six named projections per block (v1.0 seam). Adapter-only `state_dict` save/load through the existing open-dict checkpoint code; `merge()` utility computes `W' = W + (α/r)·B@A` for export and for the merged-vs-adapter equivalence test. | torch only |
| **Adapter sizing (the "persona file")** | Params per wrapped Linear = `r·(d_in + d_out)`. At the 13.89M config (≈ d_model 384, 6 blocks — confirm against `ModelConfig`), r=8 over all six projections ≈ **330k params ≈ 1.3 MB fp32** (r=4 ≈ 0.66 MB). Small enough that "your entire memory of me is a ~1 MB weight delta" is a demo line. | — |
| **EWC** | After stage-1 consolidation point: one pass over a TinyStories reference sample (existing `train.bin`/`val.bin` memmap), accumulate `p.grad² → F̂` per parameter (empirical Fisher diagonal), snapshot `θ*`. Store `{name: F̂, name: θ*}` via the open-dict checkpoint. Penalty `λ/2 · Σ F̂·(θ−θ*)²` returned as a callable into `assemble_loss(..., extra_penalties=(ewc_penalty,))` — the seam shipped and test-verified in v1.0. | torch only |
| **Conversational fine-tuning** | Existing training loop (AdamW, warmup/cosine, grad-accum, CSV log, resumable checkpoints) pointed at `dialog_train.bin`; two arms for the A/B — naive full/LoRA fine-tune vs same + EWC penalty. | existing harness |
| **Teach-then-recall demo** | Gradio app v2: teach facts in a session → fine-tune the LoRA adapter on the session transcript → **fresh process, empty prompt, adapter loaded** → model recalls. Adapter on/off toggle proves memory is in the weights, not the context. | gradio 5.x (installed) |
| **EWC A/B no-forgetting demo** | Notebook + committed PNGs: identical fine-tune with/without EWC; report TinyStories val PPL (existing `evaluate.perplexity()`) at checkpoints for both arms. | matplotlib, existing eval |
| **Forgetting curves** | During every fine-tune, log TinyStories-val loss/PPL alongside dialog-val loss to the existing CSV logger each eval interval; plot both arms. (Note v1.0 tech debt: `forbid_ids` mask is not threaded into `evaluate.py` — thread it or document it before quoting cross-stage PPL numbers.) | existing CSV + matplotlib |
| **Weight-delta heatmaps** | `delta[layer, module] = mean(|θ_after − θ_before|)` over the 6 projections × n_layers grid → `plt.imshow` + annotated colorbar. Variants: naive vs EWC (EWC's deltas should avoid high-Fisher cells), full-FT vs LoRA (`(α/r)·B@A` per module). Pure tensor reductions. | numpy + matplotlib |

## Installation

```bash
# Nothing new to install. The existing v1.0 environment covers all of v2.0:
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[cpu,dev]" --extra-index-url https://download.pytorch.org/whl/cpu
# demo/notebook extras as in v1.0 when needed:
pip install -e ".[demo,notebook]" --extra-index-url https://download.pytorch.org/whl/cpu

# One-time corpus fetch (script to be written in the data phase; stdlib only):
python scripts/fetch_corpora.py   # → data/raw/dailydialog.tar.gz (sha256-verified)
                                  # → data/raw/personachat_self_original.json
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| ParlAI CDN tarball (DailyDialog) | HF parquet auto-conversion of `li2017dailydialog/daily_dialog` | Only if the Facebook CDN *and* the ConvLab zip both die — costs `pyarrow`/`pandas` deps for a 2.6 MB corpus. |
| S3 JSON (PersonaChat) | ParlAI `personachat.tgz` (txt format) or HF mirrors (`bavard/personachat_truecased`) | tgz if S3 dies; truecased mirror only if lowercase text proves to hurt — it adds a parquet dependency and diverges from the canonical distribution. |
| Explicit `LoRALinear` wrapper module | `torch.nn.utils.parametrize.register_parametrization` | Parametrize is elegant but hides the mechanism behind framework machinery and complicates state_dict naming — wrong trade for a portfolio whose value is *visible* mechanics. |
| Per-batch `p.grad²` accumulation (empirical Fisher) | `torch.func` (`functional_call` + `vmap`/`grad`) for true per-sample Fisher | torch.func is available in torch 2.7 and gives per-sample grads, but adds conceptual machinery for a second-order nicety; the empirical diagonal is the standard EWC practice and unit-testable by hand. |
| stdlib `urllib.request` for fetches | `requests ~=2.32` | If download UX (progress bars, retries) becomes annoying — it's not in pyproject today and two GETs don't justify it. |
| matplotlib `imshow` heatmaps | seaborn | Never, for this project — seaborn is a styling layer over matplotlib that adds a dependency for zero needed capability. |
| `torch.save` adapter dicts (+ optional safetensors export) | Custom binary format | No reason; the open-dict checkpoint pattern already exists and safetensors covers the shippable artifact. |

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **HF `peft` / `loralib`** | Excluded by design — LoRA *is* the portfolio deliverable. Reference their papers/READMEs for conventions (α/r scaling, B zero-init), never their code. | From-scratch `LoRALinear`. |
| **HF `datasets` (runtime)** | The canonical DailyDialog script inside it points at a dead URL anyway; pulls `pyarrow`/`pandas`/network machinery for two plain files. | stdlib fetch + `json`. |
| **ParlAI pip package** | Archived read-only 2023-11-03; enormous dependency tree; you only need one file from its CDN. | Direct CDN GET of `dailydialog.tar.gz`. |
| **`pandas` / `pyarrow`** | Only needed for the parquet fallback route; both corpora exist as JSON/tar. | stdlib `json`, `tarfile`. |
| **`seaborn`** | Pure styling dep; matplotlib (already pinned) does heatmaps natively. | `plt.imshow` + colorbar. |
| **`ijson` / streaming JSON** | The 200 MB PersonaChat file fits trivially in M3 RAM for a one-shot preprocessing pass. | stdlib `json.load`. |
| **`wandb` / online tooling** | Unchanged v1.0 exclusion — offline/zero-budget/privacy. | Existing CSV + matplotlib. |
| **New special tokens / tokenizer retrain** | Locked decision (2026-06-11): retrain invalidates `best.pt` as the M2 base. The 8192-table/8184-eos vocab is frozen. | Plain-text turn markers + existing eos id. |
| **`bitsandbytes` / quantized LoRA (QLoRA)** | Quantization machinery for a 13.9M-param fp32 model is cargo-culting big-model practice; bnb needs CUDA (primary path is MPS). | Plain fp32 LoRA. |
| **`opacus` / per-sample-gradient libraries** | Built for DP-SGD; massive overkill for a diagonal Fisher estimate. | `p.grad²` accumulation. |
| **External AI APIs for synthetic persona data** | Zero-budget + privacy exclusions unchanged. | DailyDialog + PersonaChat + hand-written teach-session fixtures. |

## Stack Patterns by Variant

**Primary — local M3/MPS (fp32):**
- LoRA fine-tuning at 13.9M base + ~0.3M adapter params is light even relative to v1.0
  pretraining; fp32 throughout, no AMP/GradScaler/compile (unchanged posture).
- Fisher estimation is one forward/backward pass over a few hundred reference batches — minutes
  on MPS.
- All v2.0 checkpoints (adapter-only, Fisher/θ*, A/B arms) ride the existing resumable
  open-dict checkpoint + RNG-restore infrastructure unchanged.

**Fallback — Kaggle P100 (fp16 AMP):**
- **EWC + fp16 caveat:** compute the Fisher accumulation and the quadratic penalty in **fp32
  outside the autocast region** — `F̂·(θ−θ*)²` multiplies two small quantities and underflows in
  fp16. Keep `F̂` and `θ*` buffers fp32. (Moot on the primary MPS path, which is fp32 anyway.)
- Attach `data/raw/` as a Kaggle Dataset once; never download inside a session.

**Demo/inference — laptop CPU:**
- Teach-then-recall fine-tunes only adapter params (~330k) — feasible *on CPU* in the live demo
  loop if the teach transcript is short; otherwise run the adapter fit as a short offline step
  between "teach" and "recall" sessions.
- Adapter load/unload at inference = swap two small tensors per wrapped Linear or pre-merge;
  no measurable latency change vs the v1.0 demo (~95–105 tok/s CPU).

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| torch `2.7.*` | Everything in v2.0 | No API newer than torch 2.0 is required (nn.Module composition, autograd, `requires_grad_`). No bump needed or wanted (Pascal-fallback constraint from v1.0 still holds: `cu126`-era wheels only on P100). |
| numpy `~=2.4` | torch 2.7, uint16 memmaps | Unchanged v1.0 data path. |
| matplotlib `~=3.10` | numpy 2.x, Python 3.11 | Already pinned in `demo`/`notebook` extras; heatmaps need nothing newer. |
| gradio `>=5,<6` | Python 3.11, offline `launch()` | Unchanged; v2.0 only adds UI controls within Gradio 5's existing API. |
| pyproject `requires-python >=3.10,<3.12` | All of the above | Unchanged — keep developing only inside the 3.11 venv (dev box's 3.14 remains unsupported). |

## Sources

- `https://dl.fbaipublicfiles.com/parlai/dailydialog/dailydialog.tar.gz` — **HTTP 200 verified 2026-06-11**; downloaded; sha256 `c3adb09…73e6bb`; JSONL format and 11,118/1,000/1,000 splits inspected directly (HIGH — load-bearing)
- `https://s3.amazonaws.com/datasets.huggingface.co/personachat/personachat_self_original.json` — **HTTP 200 verified 2026-06-11**, 209,850,483 B; head/tail byte ranges inspected, structure matches the documented distribution (HIGH — load-bearing)
- `http://yanran.li/files/ijcnlp_dailydialog.zip` — **HTTP 404 verified 2026-06-11**; original source is dead (HIGH — load-bearing negative)
- `https://huggingface.co/datasets/li2017dailydialog/daily_dialog` — loading-script repo only; `daily_dialog.py` `_URL` points at the dead yanran.li zip; license card CC BY-NC-SA 4.0 (HIGH)
- `https://huggingface.co/datasets/ConvLab/dailydialog/resolve/main/data.zip` — HTTP 200 via resolve redirect, 3,738,236 B, verified 2026-06-11 (HIGH, fallback)
- `https://dl.fbaipublicfiles.com/parlai/personachat/personachat.tgz` — HTTP 200, 223,221,886 B, verified 2026-06-11 (HIGH, fallback)
- `https://github.com/huggingface/transfer-learning-conv-ai` + thomwolf gist — canonical documentation of the `personachat_self_original.json` schema (MEDIUM, corroborated by direct byte inspection above)
- `https://github.com/facebookresearch/ParlAI` — archived read-only 2023-11-03; informs the cache-and-checksum discipline (MEDIUM)
- `/Users/juliorcoelho/PersonaCore/pyproject.toml` + `.planning/PROJECT.md` — existing pins, seams (six named Linears, `assemble_loss(extra_penalties)`), frozen-tokenizer decision (HIGH, first-party)
- PersonaChat licensing read (no explicit license on the S3 distribution; don't re-host) — MEDIUM, flagged for honesty

---
*Stack research for: PersonaCore v2.0 Weight-Based Memory (LoRA + EWC + conversational fine-tuning + demos/visualizations)*
*Researched: 2026-06-11*
