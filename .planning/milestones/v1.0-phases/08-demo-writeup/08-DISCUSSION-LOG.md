# Phase 8: Demo & Writeup - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-10
**Phase:** 8-Demo & Writeup
**Areas discussed:** Writeup shape & story, Notebook narrative scope

---

## Area Selection

Four gray areas were offered: Demo UX & framing, Writeup shape & story, Notebook narrative
scope, Checkpoint packaging. The user selected **Writeup shape & story** and **Notebook
narrative scope**; the other two were left to Claude's discretion (recorded in CONTEXT.md).

---

## Writeup shape & story

### Q1 — Document structure

| Option | Description | Selected |
|--------|-------------|----------|
| README + REPORT (Recommended) | README.md front door (what/why, demo GIF/screenshot, quickstart, headline results) linking to a deeper docs/REPORT.md with the full technical narrative | ✓ |
| Single deep README | One polished README.md carrying everything | |
| README + docs/ series | README plus multiple focused docs (ARCHITECTURE.md, TRAINING.md, RESULTS.md) | |

**User's choice:** README + REPORT

### Q2 — Headline framing

| Option | Description | Selected |
|--------|-------------|----------|
| Vision-led (Recommended) | Lead with the PersonaCore thesis (memory lives in the weights, privacy by design), M1 as the rigorous foundation with LoRA/EWC seams in place; honest that M2 is upcoming | ✓ |
| Artifact-led | Lead with what exists today (from-scratch 13.9M GPT, PPL 2.11); vision as a roadmap section | |
| On-device angle | Lead with the zero-budget/fully-on-device story | |

**User's choice:** Vision-led

### Q3 — REPORT depth

| Option | Description | Selected |
|--------|-------------|----------|
| Decision-driven (Recommended) | Sections organized around design decisions: choice + rationale + validating evidence (test, ablation, curve) | ✓ |
| Component walkthrough | Tokenizer → Model → Training → Generation → Evaluation tutorial structure | |
| Results-first brief | Lean report: numbers, table, curves, short summary | |

**User's choice:** Decision-driven

### Q4 — README proof

| Option | Description | Selected |
|--------|-------------|----------|
| Demo GIF + numbers (Recommended) | Animated GIF of the Gradio demo streaming on CPU + compact results block + quickstart | ✓ |
| Static screenshot + curves | Gradio screenshot + training-loss curve image + results table | |
| Sample-text led | Generated story excerpt as blockquote + numbers, no images | |

**User's choice:** Demo GIF + numbers

---

## Notebook narrative scope

### Q1 — Notebook story

| Option | Description | Selected |
|--------|-------------|----------|
| Results showcase (Recommended) | Load checkpoint, param count, curves, headline PPL, ablation cohort plots+table, live sampling; complements the REPORT | ✓ |
| Minimal DEMO-03 | Just curves, a few samples, param count | |
| Full research narrative | End-to-end tokenizer → bigram → GPT → ablations → generation notebook | |

**User's choice:** Results showcase

### Q2 — Execution model

| Option | Description | Selected |
|--------|-------------|----------|
| Live + committed outputs (Recommended) | Cells genuinely run on CPU; notebook committed with executed outputs so GitHub renders it | ✓ |
| Live, outputs stripped | Clean diffs, but renders empty on GitHub | |
| Pre-captured only | Outputs pasted as markdown/images, no model load | |

**User's choice:** Live + committed outputs

### Q3 — Sampling section

| Option | Description | Selected |
|--------|-------------|----------|
| Settings tour (Recommended) | One fixed prompt under a greedy/temperature/top-k/top-p grid showing how sampling changes the text; seeded | ✓ |
| Mirror samples.md | Re-run the curated EVAL-02 prompts/settings | |
| Free-running stories | [eos_id]-seeded free-running generations at demo defaults | |

**User's choice:** Settings tour

### Q4 — Checkpoint source

| Option | Description | Selected |
|--------|-------------|----------|
| Slim checkpoint (Recommended) | Notebook loads the slim DEMO-02 artifact (weights_only=True) — same artifact as the Gradio demo and offline test | ✓ |
| best.pt directly | Load the full training checkpoint (weights_only=False) | |
| Both, briefly | Slim for everything + one cell on the full checkpoint's resumability contents | |

**User's choice:** Slim checkpoint

---

## Claude's Discretion

- **Demo UX & framing (DEMO-01):** honest framing of an untuned story generator, multi-turn
  history handling, controls beyond temperature/top-k.
- **Checkpoint packaging (DEMO-02):** torch.save-vs-safetensors, what ships alongside,
  commit-vs-release-vs-regenerate distribution for the ~55MB weights.
- **KV-cache:** researcher measures CPU latency first (carried decision).
- **GIF capture tooling, notebook plot style, QA-01 green-gate mechanics.**

## Deferred Ideas

None new this discussion — existing deferrals carried in CONTEXT.md (KV-cache-on-measurement,
M2 demos, strided-PPL footnote, sample-hook rewire).
