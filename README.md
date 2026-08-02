# PersonaCore

A conversational AI where memory lives in the model weights — no databases, no vector
stores, no external files: privacy by design. **Milestone 2 demonstrates that claim rather
than promising it:** a from-scratch LoRA adapter is taught personal facts in conversation,
and a *fresh process with an empty prompt* recalls them from the weights alone — while a
from-scratch EWC penalty keeps the base model from being destroyed in the process.
**Milestone 1** is the foundation this runs on, not a superseded draft: a correct, tested
13.9M-parameter GPT written by hand and trained entirely on-device.

![Gradio chat demo streaming a TinyStories completion token-by-token on a laptop CPU](assets/demo.gif)

## Results at a glance

- **13.9M parameters** — 13,891,584 exact, tied embedding counted once (6 layers, 6 heads,
  384-dim embeddings, 256-token context)
- **Deterministic full-validation perplexity 2.1066 over 12,636,922 scored target tokens**
  (50k-step `best.pt`, computed by `scripts/evaluate.py`)
- **~100 tok/s** streaming on a laptop CPU (measured 95–105) — a complete ~200-token story
  in about 2 seconds
- **Trained on-device** on Apple Silicon (fp32 / MPS) — zero external compute, zero budget
- **100% from-scratch PyTorch** — no HuggingFace model code anywhere in the runtime
- **Choices justified by ablation** — weight tying and positional embeddings both earn
  their parameters; the full four-run cohort (with its honest reduced-budget caveat) is in
  [docs/REPORT.md](docs/REPORT.md)

## Where the memory actually moved

![Fisher diagonal beside the naive and EWC weight-delta grids, 6 layers by 6 projections](results/phase15_fisher_ewc.png)

*The naive and EWC delta panels share one color scale so the two arms are directly comparable; the Fisher panel has its own scale because squared-gradient importance is not a weight-delta ratio.*

![Relative weight change of the taught persona adapter across 6 layers and 6 projections](results/phase15_adapter_delta.png)

*The persona adapter's own ‖ΔW‖_F/‖W₀‖_F grid, on an independent scale — it is not comparable to the panels above (different parameter counts, different training budgets), and the full reasoning is in [docs/REPORT.md](docs/REPORT.md).*

## What is this?

Every component is hand-implemented in pure PyTorch:

- **Byte-level BPE tokenizer** trained from scratch — vocab table 8192 with 547 ids live
  (256 bytes + 283 learned merges + 8 specials; the bounded TinyStories corpus exhausts its
  mergeable pairs, so the remaining 7645 rows are reserved capacity), `<|endoftext|>`
  pinned as an atomic id, validated against a tiktoken oracle (test-only; a guard test
  proves the oracle is never imported by runtime code)
- **GPT-style decoder** built by hand — pre-norm blocks, causal multi-head attention
  (masked before softmax), GELU MLP, weight tying as true shared storage
- **Hand-rolled training loop** — AdamW, warmup + cosine LR schedule, gradient
  clipping/accumulation, resumable open-dict checkpoints that restore RNG state bit-for-bit
- **From-scratch LoRA adapters** — rank-8 wrappers over the six named projections per block
  (`q_proj`, `k_proj`, `v_proj`, `c_proj`, `fc_in`, `fc_out`), 331,776 trainable parameters
  against a base proven bit-untouched, with runtime toggle / merge / eject
- **From-scratch EWC** — per-example diagonal Fisher (N=2000) plus a Kirkpatrick quadratic
  anchor, spliced into the v1.0 loop through its `assemble_loss(base, extra_penalties)`
  seam with a bit-identical trajectory when the penalty is off
- **One shared `generate()`** — greedy / temperature / top-k / top-p with EOS-stop, powering
  the tests, the notebook, and the demo identically
- **Per-component pytest suite** — causality, weight-tying storage identity, init scaling,
  oracle equivalence, resume trajectories, adapter and Fisher invariants (~400 CPU-only
  tests)
- **Two offline Gradio demos** — story completion, and the teach-then-recall demo with its
  live memory ON/OFF toggle; both on localhost with zero outbound network calls

## Run the demo

After the install and the weights download, the demo itself makes zero network calls — it
works with Wi-Fi off.

```bash
# 1. Get the code
git clone https://github.com/RAFAELDCOELHO/PersonaCore.git
cd PersonaCore

# 2. Environment (Python 3.11)
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[cpu,demo]" --extra-index-url https://download.pytorch.org/whl/cpu

# 3. Weights — slim inference checkpoint (~55.6 MB) from the m1-demo-v1 release
gh release download m1-demo-v1 --pattern model_slim.pt --dir checkpoints
# or download model_slim.pt from
#   https://github.com/RAFAELDCOELHO/PersonaCore/releases/tag/m1-demo-v1
# and place it at checkpoints/model_slim.pt

# 4. Launch
python scripts/demo_app.py
# -> http://127.0.0.1:7860
```

The artifact loads with `torch.load(..., weights_only=True)` — plain tensors and containers
only, no code execution — and embeds its own `ModelConfig` plus the git SHA that produced
it. If you have a local training checkpoint (`best.pt`) instead, regenerate the artifact
with `python scripts/export_slim.py`.

The teach-then-recall demo (`python scripts/personalize_demo.py`) runs the same way but
needs two locally produced checkpoints that are not in the `m1-demo-v1` release: the
conversational base (`checkpoints/convbase_slim.pt`) and the taught persona adapter
(`checkpoints/persona_adapter.pt`, 1.35 MB), produced by `scripts/finetune_dialog.py` and
`scripts/teach_persona.py`. Teaching happens in a *different* process from the demo, which
is what makes the clean room true by construction rather than by assertion.

## Evidence

- **[docs/REPORT.md](docs/REPORT.md)** — the decision-driven technical deep dive: every
  load-bearing choice with its rationale and the test, ablation row, or training curve that
  validates it, plus the Milestone 2 results narrative and every honest negative quoted
  from its source report
- **[demo.ipynb](demo.ipynb)** — the executed results notebook (rendered by GitHub): the
  model loaded from the slim artifact, exact parameter count, training curves, ablation
  plots, and a seeded sampling-settings tour
- **[results/](results/)** — committed evaluation artifacts: training-curve CSVs, the
  ablation cohort table, qualitative samples (representative, not cherry-picked), the EWC
  A/B report, the recall report with per-question counts, and
  `results/phase15_norms.json` — the committed grid of weight-delta and Fisher norms both
  figures above are plotted from

## Tests and reproducibility

```bash
make test    # full CPU-only suite — no GPU required
```

Reproducibility discipline: fixed seeds, the producing git SHA and full `ModelConfig`
embedded in every checkpoint (including the shipped slim artifact), and resume that
restores RNG state rather than re-seeding — an interrupted run continues its loss curve
bit-for-bit.

## Milestone 2 — what shipped

Milestone 1 deliberately built the sockets the thesis mechanism would plug into: six named
`nn.Linear` projections per block for LoRA, an `assemble_loss(base, extra_penalties)` seam
for EWC, and open-dict checkpoints for Fisher state. Milestone 2 plugged the thesis into
them and measured what came out:

- **From-scratch LoRA adapters** over those six projections — the weight-memory write
  mechanism, with a canary proving every trainable parameter moved and every frozen base
  parameter stayed bit-identical
- **From-scratch EWC** through the `assemble_loss` seam — per-example diagonal Fisher and a
  quadratic anchor, both hand-written and pinned against analytic oracles
- **The unconfounded no-forgetting A/B** — two 4000-step arms differing *only* in the
  penalty, with both axes reported (what each arm learned and what it destroyed) and the
  gate pre-registered in committed code before either run existed
- **The clean-room teach-then-recall demo** — a live memory ON/OFF toggle over the same
  weights, a one-way Reset, and a panel showing the exact prompt token ids, so a reviewer
  can watch the answer change while the prompt does not

### Honest next steps

- The recall gate covers the proper-noun core; the soft preference tier and reversed
  phrasings were not measured as held-out properties
- The retention result is teacher-forced perplexity; in free-running story mode both arms
  still leak role tokens, so qualitative retention is not claimed
- The tokenizer stays frozen from Milestone 1 at 547 live ids — retraining it would
  invalidate every checkpoint here, so the cost of keeping it was measured instead
- Every bound on every claim above is collected and quoted from its source report in
  [docs/REPORT.md](docs/REPORT.md#milestone-2-limitations--nine-honest-negatives-quoted)
