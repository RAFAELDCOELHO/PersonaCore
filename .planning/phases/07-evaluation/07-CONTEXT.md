# Phase 7: Evaluation - Context

**Gathered:** 2026-06-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 7 delivers **quantitative and qualitative proof of the trained model, plus the
differentiating ablation study** that lifts this above a student clone. Three deliverables:

- **EVAL-01** — held-out perplexity, computed and reported on `data/val.bin`.
- **EVAL-02** — curated qualitative generation samples captured for the writeup.
- **EVAL-03** — 2–3 architecture ablations presented in a comparison table.

This phase **measures** the existing trained model and trains small ablation variants; it does
**not** change the model, tokenizer, training loop, checkpoint format, or `generate()`. The Gradio
UI, slim inference checkpoint, and `demo.ipynb` rendering are **Phase 8**. LoRA/EWC/personalization
are **Milestone 2**.

</domain>

<decisions>
## Implementation Decisions

### Perplexity protocol (EVAL-01)
- **D-01: Deterministic full-val sweep.** The headline perplexity is computed over the **entire**
  `data/val.bin` in **non-overlapping `block_size` windows**, summing CE across all predicted
  tokens: `PPL = exp(total_CE / total_tokens)`. One canonical, reproducible number — NOT a
  random-batch estimate.
- **D-02: New eval function, distinct from `estimate_loss`.** `loop.py::estimate_loss` (20 random
  batches under `model.eval()`+`no_grad`) stays as the in-training signal. EVAL-01 gets its own
  deterministic full-sweep function. PPL uses `GPT.forward(idx, targets=...)` directly (the
  `(logits, loss)` contract), not `generate()`.
- **D-03: Count all tokens, including inter-document EOS.** Every predicted token counts, including
  the `eos_id=8184` separating stories — matches how the model was trained. **Report the total
  token count alongside PPL** so the denominator is explicit and the number is auditable.
- **D-04: Headline PPL comes from the real 50k `best.pt`**, loaded via
  `checkpoint.load_checkpoint`. This is the genuine model number and is reported separately from the
  reduced-budget ablation cohort (see D-08).

### Ablation study (EVAL-03)
- **D-05: Architecture trio.** Three ablations, each isolating ONE design choice against the
  baseline GPT (6 layers / 6 heads / `d_model=384`, `block_size=256`, `vocab_size=8192`):
  1. **no weight-tying** (untie the input/output embedding — ties directly to the existing
     weight-tying seam proven in Phase 4 via the `data_ptr()` identity test)
  2. **no positional embeddings** (drop the learned positional embedding)
  3. **depth/width cut** (e.g. 6→3 layers; planner picks the exact knob — fewer layers OR narrower
     `d_model`, reported with param count)
- **D-06: Reduced fixed budget with a FRESH re-trained baseline.** Train a new baseline **plus**
  all 3 variants to the **same reduced step budget**, identical config otherwise — only the ablated
  knob changes. The ablation table is its own self-consistent cohort. Do **not** compare reduced
  variants against the 50k `best.pt` (different budgets = unfair).
- **D-07: Budget chosen by a tiny calibration (~5–10k steps).** Planner runs a short calibration to
  find the smallest budget where the baseline reaches clearly-coherent text and the val-loss curve
  has flattened enough that ablation deltas are meaningful (likely ~5–10k steps). ~4× that budget
  (baseline + 3 variants) ≈ a few hours on M3 — affordable under the zero-budget constraint.
- **D-08: Comparison table = PPL + params + val-loss, with shared-seed fairness.** Columns:
  *variant name · param count · held-out perplexity (at the reduced budget) · best val-loss ·
  one-line "what this shows"*. All four runs share the same **seed, data, LR schedule, and step
  budget**; only the ablated knob differs. The reduced-budget PPL uses the same deterministic
  full-val sweep as EVAL-01 (D-01) so the cohort numbers are internally comparable.

### Claude's Discretion
*(User selected "I'm ready for context" — these defaults were proposed and accepted implicitly;
planner may refine within them.)*
- **EVAL-02 qualitative samples:** a handful of **fixed story-starter prompts** generated with the
  **Phase-6 sampling defaults** (the locked `generate()` / text-wrapper path, `[eos_id]`-seeded),
  presented as **representative, not cherry-picked**, with the honest selection method noted in the
  writeup (portfolio integrity for a rigor-focused audience). Greedy + a small temperature/top-p
  spread is acceptable; planner picks the exact prompt set and settings.
- **Artifacts/output:** a standalone **`eval.py` (or `evaluation` module)** + a **committed results
  markdown table** + **per-run CSVs** for the ablation cohort. Phase 8's `demo.ipynb` later
  *renders* these; Phase 7 produces the data/table it consumes. Reuse `logging.py`'s CSV appender
  for run logs.
- **PPL window stride:** non-overlapping is locked (D-01); planner may add a strided/sliding-window
  variant only if it falls out cheaply — not required.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope & requirements
- `.planning/ROADMAP.md` §"Phase 7: Evaluation" — goal + 3 success criteria (EVAL-01..03).
- `.planning/REQUIREMENTS.md` — EVAL-01 (held-out perplexity), EVAL-02 (curated samples), EVAL-03
  (2–3 ablations + comparison table).
- `.planning/PROJECT.md` — Core Value (real ML depth, from-scratch correctness); zero-budget /
  on-device / privacy constraints that bound the ablation compute.

### Upstream phase decisions this phase depends on
- `.planning/phases/05-tinystories-pretraining/05-CONTEXT.md` — **D-07** acceptance bar (recorded
  perplexity AND coherent curated samples = the TinyStories qualitative register); the trained
  `best.pt` + `run.csv` curves this phase measures.
- `.planning/phases/06-generation-sampling/06-CONTEXT.md` — the shared `generate()` contract,
  text-wrapper `[eos_id]`-seed behavior (D-03), and the note that "perplexity uses `forward`
  directly; qualitative samples call `generate()`."

### No new external specs
- No external ADRs/specs beyond the planning docs above — decisions are fully captured here.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/personacore/training/loop.py::estimate_loss(model, val_ids, ...)` — mean val CE under
  `model.eval()`+`no_grad`, restores `model.train()`. Reference for the EVAL-01 sweep, but a NEW
  deterministic full-val function is required (D-02) — estimate_loss only does 20 random batches.
- `src/personacore/model/gpt.py::GPT.forward(idx, targets=...) -> (logits, loss)` — the locked
  contract; pass `targets` to get CE directly for perplexity.
- `src/personacore/generation/core.py::generate` + `generation/text.py` — qualitative samples
  (EVAL-02); `[eos_id]`-seeded, prompt-stripped continuation.
- `src/personacore/training/data.py::get_batch_memmap` / `load_split` — `np.memmap` over
  `data/val.bin`; the full-val sweep tiles non-overlapping windows over the same memmap.
- `src/personacore/checkpoint.py::load_checkpoint` — loads `best.pt` (open-dict, full RNG/config).
- `src/personacore/training/loop.py::train(...)` — the run harness the ablation cohort re-uses
  (baseline + 3 variants) under a reduced step budget; only `ModelConfig`/`TrainConfig` knobs change.
- `src/personacore/logging.py` — restart-safe CSV appender for per-run ablation curves.
- `src/personacore/config.py` — `ModelConfig` (layers/heads/d_model, weight-tying, positional-emb
  flags) and `TrainConfig` (steps, seed, LR) are where the ablation knobs are set.

### Established Patterns
- **Held-out split is document-boundary clean** (`data.py` splits at `eos_id=8184`, no leakage) —
  the perplexity number is honest.
- **Open-dict checkpoints carry config + RNG** — each ablation run is reproducible and its config
  travels with its checkpoint (QA-02 reproducibility discipline).
- **fp32 on M3/MPS, no AMP** — ablation runs follow the same precision posture as pretraining.

### Integration Points
- Existing assets: `checkpoints/best.pt`, `checkpoints/latest.pt`, `data/train.bin`,
  `data/val.bin`, `logs/run.csv` (50k-step training curve) — Phase 7 reads these; does not modify.
- New code: `eval.py`/`evaluation` module + ablation driver script + committed results table — feed
  Phase 8's `demo.ipynb`.

</code_context>

<specifics>
## Specific Ideas

- The **no-weight-tying** ablation is deliberately chosen to exercise the Phase-4 weight-tying seam
  (verified by the `data_ptr()` tensor-identity test) — the ablation story and the from-scratch
  implementation reinforce each other.
- Report perplexity **with its token count** so reviewers can audit the denominator — a small
  rigor signal for the MIT/Stanford-bar audience.
- Ablation table wants a one-line **"what this shows"** per row so the writeup reads as analysis,
  not just numbers.

</specifics>

<deferred>
## Deferred Ideas

- **Strided/sliding-window (GPT-2-style) perplexity** — more rigorous, lower number, more compute.
  Not required; planner may add only if cheap. Otherwise a possible writeup footnote.
- **LR / training-dynamics ablations** (peak-LR or warmup sweep) — considered, not selected; the
  architecture trio tells the stronger "why the design works" story. Could extend the study later.
- **Capacity scaling curve** (3/6/9 layers as a PPL-vs-params plot) — considered, not selected.
- **Overlaid val-loss curves per variant + train-time column** — richer evidence; overlaps Phase 8
  notebook plotting, so deferred to keep Phase 7 focused on the table.
- **`demo.ipynb` rendering of results** — Phase 8 (DEMO-03).

### None folded
No pending todos matched this phase.

</deferred>

---

*Phase: 7-Evaluation*
*Context gathered: 2026-06-09*
