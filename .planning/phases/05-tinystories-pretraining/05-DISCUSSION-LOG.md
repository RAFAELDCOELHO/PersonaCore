# Phase 5: TinyStories Pretraining - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-05
**Phase:** 5-tinystories-pretraining
**Areas discussed:** MPS device support, Corpus scope & token budget, 'Done' / fluency bar & stopping

---

## Area Selection (gray areas offered)

| Option | Description | Selected |
|--------|-------------|----------|
| Corpus scope & token budget | Full corpus vs capped subset | ✓ |
| Precision & attention path | fp32+manual vs fp16-AMP+sdpa for the long run | |
| 'Done' / fluency bar & stopping | Fixed budget vs val-plateau vs time-boxed; what 'fluent' means | ✓ |
| Data prep & resume persistence | Memmap location, val source, checkpoint cadence | (folded into others) |
| **Other (free text)** | Add MPS support to RuntimeConfig + rename preflight_p100→preflight_device (CUDA-P100→mps→cpu), fp32 on MPS | ✓ |

**Note:** "Precision & attention path" became moot once MPS (fp32-only) was chosen as the run device.

---

## MPS Device Support

### Q1 — Scope of MPS support
| Option | Description | Selected |
|--------|-------------|----------|
| Local calibration + dev/inference | MPS for calibration/smoke + demo; full run stays P100 | |
| Dev/inference convenience only | MPS only speeds generation/demo/smoke | |
| MPS as a training target | Treat M3/MPS as a genuine pretraining device | ✓ |

**User's choice:** MPS as a training target (chosen despite explicit pushback re: project constraints).

### Q2 — Phasing
| Option | Description | Selected |
|--------|-------------|----------|
| Prerequisite within Phase 5 | Early plan/task inside Phase 5 | |
| Separate inserted infra phase | Own phase (e.g. INSERTED 4.1) | |
| Do it now, before planning Phase 5 | Immediate prerequisite outside the Phase-5 plan | ✓ |

**User's choice:** Do it now, before planning Phase 5.

### Q3 — API/behavior change
| Option | Description | Selected |
|--------|-------------|----------|
| Rename + priority + fp32 guard | Hard rename preflight_p100→preflight_device; MPS detection; fp32-on-MPS; update callers/tests | ✓ |
| Add new fn, keep old as alias | preflight_device alongside a deprecated preflight_p100 | |

**User's choice:** Hard rename + priority (CUDA-P100→MPS→CPU) + fp32-on-MPS guard.

### Q4 — Replace vs augment the Kaggle P100 run
| Option | Description | Selected |
|--------|-------------|----------|
| Augment — P100 stays canonical | MPS added; Kaggle still produces the shipped checkpoint | |
| Replace — M3/MPS is the run | Shipped checkpoint produced locally on M3; Kaggle optional/unused | ✓ |
| Decide after calibration | Smoke both, pick by measured throughput | |

**User's choice:** Replace — M3/MPS is the run.
**Notes:** Claude pushed back twice (MPS op-coverage gaps, no fp16-AMP win, laptop wall-clock/thermal limits; conflicts with locked PROJECT/REQUIREMENTS/STACK P100 framing). User made an informed decision to proceed. Consequence: PRE-01/PRE-02, ROADMAP success criteria, and CLAUDE.md/STACK.md need rewording (captured as a REQUIRED follow-up in CONTEXT).

---

## Corpus Scope & Token Budget

### Q1 — Corpus size
| Option | Description | Selected |
|--------|-------------|----------|
| Full TinyStoriesV2-GPT4 | ~500–550M tokens | ✓ |
| Capped subset | Fixed token budget for guaranteed completion | |
| You decide (calibration picks) | Let research size it | |

**User's choice:** Full TinyStoriesV2-GPT4.

### Q2 — Run budget (tolerable local run length)
| Option | Description | Selected |
|--------|-------------|----------|
| A few hours, one sitting | ~2–6h single session | |
| Overnight / multi-session | ~8–24h with resume | |
| As long as it takes | Quality-first, run until fluent | ✓ |

**User's choice:** As long as it takes (quality-first, checkpoint throughout).

### Q3 — Validation set source
| Option | Description | Selected |
|--------|-------------|----------|
| Official valid file | TinyStoriesV2 valid file (~22.5MB), zero leakage by construction | ✓ |
| Carve N docs from train | Hold out whole docs at EOS boundaries | |

**User's choice:** Official valid file.

---

## 'Done' / Fluency Bar & Stopping

### Q1 — Stopping criterion
| Option | Description | Selected |
|--------|-------------|----------|
| Val-loss plateau + sample checks | Train while improving; confirm via samples | ✓ |
| Fixed token/step budget | Stop at a calibration-set target | |
| Manual judgment | Stop when samples look good | |

**User's choice:** Val-loss plateau + periodic qualitative sample checks.

### Q2 — Fluency acceptance bar (PRE-02)
| Option | Description | Selected |
|--------|-------------|----------|
| TinyStories-style coherence | Curated coherent samples only | |
| Numeric val-loss/perplexity target | Measured threshold pass/fail | |
| Both — perplexity + curated samples | Recorded perplexity AND coherent samples | ✓ |

**User's choice:** Both — recorded perplexity (PRE-03) + curated coherent TinyStories samples.

### Q3 — Which checkpoint ships downstream
| Option | Description | Selected |
|--------|-------------|----------|
| Best val-loss checkpoint | Lowest-val-loss, early-stopping hygiene | ✓ |
| Final-step checkpoint | Whatever the run ends on | |

**User's choice:** Best val-loss checkpoint.

---

## Claude's Discretion

- Memmap build script shape/location (thin `scripts/` entry, no CLI), checkpoint cadence,
  best-checkpoint tracking mechanism, sample-generation cadence, and the calibration smoke harness.
- Empirical LR / batch / steps / MPS block-size sizing → delegated to the phase-level calibration
  research, not pre-decided.

## Deferred Ideas

- **Required requirements/roadmap rewording** (PRE-01/PRE-02, ROADMAP SC #1/#2, PROJECT/CLAUDE/STACK
  P100 framing) — consequence of the MPS-replace decision; flagged as REQUIRED in CONTEXT.
- fp16 AMP / sdpa for memory — moot on MPS (fp32 only); only relevant for a CUDA fallback run.
- KV-cache for CPU/MPS inference latency — Milestone-2 / Phase-8-conditional.
- Architecture / LR ablation table — Phase 7 (EVAL-03).
- Full `generate()` (top-k/top-p, EOS-stop) — Phase 6 (GEN-01..03).
