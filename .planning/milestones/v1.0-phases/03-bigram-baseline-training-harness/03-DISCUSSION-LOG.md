# Phase 3: Bigram Baseline & Training Harness - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-04
**Phase:** 3-bigram-baseline-training-harness
**Areas discussed:** Bigram↔harness contract, assemble_loss seam

---

## Gray-Area Selection

| Area | Description | Selected |
|------|-------------|----------|
| Bigram↔harness contract | nn.Module interface the bigram implements to de-risk Phase-4 GPT | ✓ |
| Harness data path | What Phase 3 trains on without doing Phase 5's memmap | (delegated) |
| assemble_loss seam | TRAIN-06 M2 EWC hook signature + location | ✓ |
| AMP discipline on CPU CI | Keeping fp16 unscale-before-clip honest GPU-free | (delegated) |

**User's choice:** Bigram↔harness contract, assemble_loss seam
**Notes:** The two non-selected areas were explicitly delegated to Claude's discretion.

---

## Bigram↔Harness Contract

### Bigram form

| Option | Description | Selected |
|--------|-------------|----------|
| Lookup-table, GPT-shaped | nn.Embedding(8192, 8192); logits=table(idx) shape (B,T,V); forward(idx,targets)->(logits,loss) — SAME signature as Phase-4 GPT | ✓ |
| Neural bigram (embed→linear) | nn.Embedding(V,n_embd) → nn.Linear(n_embd,V); closer to transformer shape but over-engineers a throwaway | |
| You decide | — | |

**User's choice:** Lookup-table, GPT-shaped
**Notes:** ~67M lookup params irrelevant (never pretrained); value is exercising the harness contract identically to the future GPT.

### Loss ownership (the hinge between both selected areas)

| Option | Description | Selected |
|--------|-------------|----------|
| forward returns base CE; loop assembles | model.forward->(logits, base_loss); training step calls assemble_loss(base_loss, extra_penalties=()); M2 injects penalties at loop with zero model changes | ✓ |
| Loop computes everything; forward returns logits only | maximally decoupled model but diverges from nanoGPT (logits,loss) convention, weakening de-risk | |
| assemble_loss computes base CE too | single entry point but breaks the GPT forward contract the bigram exists to validate | |

**User's choice:** forward returns base CE; loop assembles
**Notes:** Keeps the nanoGPT-canonical forward AND provides a loop-level seam — best of both.

---

## assemble_loss Seam

### Penalty representation

| Option | Description | Selected |
|--------|-------------|----------|
| Tuple of scalar tensors, summed | assemble_loss(base, extra_penalties=()) -> base + sum(extra_penalties); M1 passes () (identity); M2 passes (fisher_penalty,); fully unit-testable now | ✓ |
| Tuple of zero-arg callables | lazy callable()->tensor; adds indirection M1 can't exercise | |
| You decide | — | |

**User's choice:** Tuple of scalar tensors, summed
**Notes:** No callbacks; empty-tuple identity + additive behavior both unit-tested in M1 so the EWC contract is locked before EWC is written.

---

## Claude's Discretion

- **Harness data path (D-06)** — small committed EOS-separated fixture encoded via the frozen tokenizer; doc-level train/val split; nanoGPT random-window sampling. No full-corpus memmap (that's Phase 5).
- **AMP-on-CPU-CI verification (D-07)** — CPU ordering unit test + GPU-conditional smoke test (`skipif(not cuda)`).
- **LR schedule (D-08)** — warmup+cosine as a `LambdaLR` (resumable, satisfies checkpoint.py's `scheduler.state_dict()` requirement).
- **Module layout (D-09)** — `model/bigram.py` + `training/` package + thin `scripts/train_bigram.py`; no CLI.
- **Overfit gate (D-10)** and **minimal sampling (D-11)**.

## Deferred Ideas

- GPT decoder / attention / param sizing — Phase 4.
- Full-corpus memmap + TinyStories fetch + pretraining run — Phase 5.
- Full `generate()` (top-k/top-p, EOS stop) + tests — Phase 6.
- EWC Fisher computation + LoRA adapters — Milestone 2.
- LR/architecture ablation table — Phase 7.
