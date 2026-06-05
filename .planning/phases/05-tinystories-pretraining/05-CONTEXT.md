# Phase 5: TinyStories Pretraining - Context

**Gathered:** 2026-06-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Produce **the** trained checkpoint everything downstream (Phases 6–8) consumes — the visceral
proof the from-scratch LM works — by taking the already-built ~13.9M GPT (`6/6/384`,
`block_size=256`, `vocab_size=8192`, `eos_id=8184`) to **fluent, coherent generation** on
TinyStories, with the corpus prepped once as a `uint16` memmap, the run resumable, and
final/val perplexity + training curves recorded for the writeup (PRE-01..03).

**Mode:** MVP (vertical slice) — the deliverable is a trained, coherent checkpoint plus its
recorded curves/perplexity, not new architecture.

**⚠ MAJOR DIRECTION CHANGE this phase (see D-01):** the **training device is M3/MPS, not the
Kaggle P100**. The shipped fluent checkpoint is produced **locally on Apple Silicon (MPS)**.
This *replaces* the Kaggle-P100 framing baked into PRE-01/PRE-02, the ROADMAP Phase-5 success
criteria, and the P100-centric CLAUDE.md/STACK.md prescription. Those texts MUST be reworded to
match — see `<deferred>` → "Required requirements/roadmap rewording" (a REQUIRED action, not
optional polish).

**In scope (PRE-01..03, as redefined by the decisions below):**
- A pre-Phase-5 **device-layer change** landing FIRST: MPS support in `RuntimeConfig` +
  `preflight_p100` → `preflight_device` (D-01). This is the gating prerequisite.
- TinyStories obtained and **encoded once locally** into a `uint16` memmap (`train.bin`/`val.bin`)
  with one EOS between documents, kept on gitignored local disk (PRE-01, redefined — no Kaggle
  Dataset).
- A full, **resumable local M3/MPS run** to fluent/coherent generation (PRE-02, redefined).
- A trained **best-val-loss checkpoint** + recorded perplexity and curves (PRE-03).

**Out of scope (other phases / locked):**
- Empirical **LR / batch size / step count / MPS throughput** sizing → the phase-level
  **calibration study** (researcher), not decided here.
- Full-featured `generate()` (top-k/top-p, EOS-aware stop) + its tests → Phase 6 (GEN-01..03).
- Gradio demo / slim inference checkpoint → Phase 8.
- LoRA / EWC / personalization → Milestone 2.
- Retraining the tokenizer — the frozen `artifacts/tokenizer.json` is reused unchanged (Phase-2 D-09).
- New training-loop/loss/checkpoint code — `training/loop.py`, `loss.py`, `checkpoint.py`,
  `logging.py` reused; only a full-corpus memmap data path is added (see `<code_context>`).

</domain>

<decisions>
## Implementation Decisions

### MPS Device Support — pre-Phase-5 prerequisite (discussed)
- **D-01:** **Add MPS as a real training device and produce the shipped checkpoint locally on
  M3/MPS, REPLACING the Kaggle P100 run.** Kaggle becomes optional/unused. The user made this call
  informed of the risks (see D-01a). This is the project's strongest "fully on-device, zero-budget,
  privacy-by-design" expression — training, not just inference, runs on the user's own machine.
- **D-01a — risks acknowledged (recorded, accepted):** MPS backend op-coverage/correctness gaps
  (possible silent NaNs or CPU fallbacks on some ops), **no fp16-AMP memory win** (fp32 only),
  and laptop wall-clock/thermal limits on a multi-hundred-million-token run. None fatal at 13.9M
  params; the user accepts them. Planner/executor should add a cheap MPS sanity gate (e.g. an
  overfit-one-batch smoke on MPS, finite-loss assertion) before the long run.
- **D-02 — device-layer API change (do NOW, before planning Phase 5; outside the Phase-5 plan):**
  - Rename `preflight_p100` → **`preflight_device`** with detection priority **CUDA-P100 → MPS →
    CPU**. On the user's M3 (no CUDA) this resolves to MPS.
  - `RuntimeConfig` detects `torch.backends.mps.is_available()` and resolves `device="mps"`.
  - **MPS forces fp32 with AMP disabled** (same posture as CPU); the existing bf16-on-Pascal guard
    is unchanged. fp16 AMP remains a CUDA-only memory measure.
  - Update callers/tests for the rename: `scripts/preflight_demo.py` and the preflight tests.
    (Chosen: hard rename, NOT a deprecated alias.)
  - Keep the existing P100 detection logic available under the new priority order so a CUDA box
    still preflights correctly (Kaggle stays a usable fallback even if unused).

### Corpus Scope & Token Budget (discussed)
- **D-03:** **Train on the full TinyStoriesV2-GPT4 corpus** (~500–550M tokens, ~2.23GB raw).
  Best fluency-per-param; the calibration study sizes epochs/steps to the available local budget.
- **D-04:** **Quality-first / "as long as it takes."** No fixed wall-clock cap — run until the
  fluency bar is met (D-06), leaning on **resumable checkpoints throughout** to survive
  sleep/interrupts across sessions. Calibration optimizes coherence, not time.
- **D-05:** **Held-out val = the official TinyStoriesV2-GPT4 `valid` file** (~22.5MB) — clean,
  **zero leakage by construction** (no overlap with train docs). Preferred over carving docs from
  train.

### Fluency Bar & Stopping (discussed)
- **D-06:** **Stop on validation-loss plateau + periodic qualitative sample checks** — keep
  training while val loss meaningfully improves; confirm coherence with periodic generations.
- **D-07:** **Acceptance bar (PRE-02) = BOTH** a recorded perplexity figure (PRE-03) **AND**
  curated samples that read as coherent TinyStories-register text (grammatical, on-topic, simple
  narrative coherence with consistent characters/actions over a few sentences — the TinyStories
  paper's qualitative bar). Strongest evidence for the writeup.
- **D-08:** **Ship the best-val-loss checkpoint** (track lowest val loss, not necessarily the
  final step) as the canonical model handed to Phases 6–8. Standard early-stopping hygiene.

### Data Prep (follows from D-03/D-05 + existing patterns — Claude's discretion on mechanics)
- **D-09:** **Encode once, locally.** Load the frozen `artifacts/tokenizer.json` (never retrain —
  Phase-2 Pitfall 6), encode the full train corpus → `train.bin` and the official valid file →
  `val.bin` as flat `np.uint16` memmaps, **one EOS (8184) between documents**. Stored on
  **gitignored local disk** (CLAUDE.md already gitignores checkpoints/data) — no Kaggle Dataset
  step. A new full-corpus memmap data path (`np.memmap` reads + bounded random-window `get_batch`)
  is added alongside the existing bounded-fixture `load_split` in `training/data.py`; the fixture
  path stays for tests.

### Claude's Discretion (planner may refine mechanics, honor intent)
- Memmap build script location/shape (thin `scripts/` entry, no CLI — Phase-1 D-04), checkpoint
  cadence (every K steps), best-checkpoint tracking mechanism, sample-generation cadence during
  training, and the calibration smoke harness are delegated to research/planning.
- The empirical **LR / batch / steps / block-size-for-MPS** values are the **calibration study's**
  output (phase-level research), not pre-decided here.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase requirements & goal
- `.planning/REQUIREMENTS.md` — **PRE-01, PRE-02, PRE-03** (acceptance text this phase satisfies).
  ⚠ PRE-01/PRE-02 currently say "Kaggle Dataset" / "Kaggle P100" — **stale after D-01**; treat the
  decisions in this CONTEXT as authoritative and reword the requirement text (see `<deferred>`).
- `.planning/ROADMAP.md` §"Phase 5: TinyStories Pretraining" — goal + 3 success criteria + the
  phase-level **research flag** (empirical LR/batch/steps + coherence-per-quota unmeasured).
  ⚠ Success-criteria #1/#2 are P100/Kaggle-Dataset-worded — stale after D-01; reword.

### Locked stack & device discipline (now MPS-primary, P100 fallback)
- `CLAUDE.md` (Technology Stack section) + `.planning/research/STACK.md` — the P100/Kaggle
  prescription (fp16 AMP + GradScaler, no bf16, `torch.compile` skipped, sdpa math-backend).
  ⚠ Largely **superseded for training** by D-01 (M3/MPS, fp32). Still authoritative for: the
  frozen tokenizer reuse, the `uint16` memmap pattern, CSV+matplotlib offline logging, and the
  bf16-guard. Reword the "train on Kaggle P100" framing to "train on M3/MPS (Kaggle P100 optional
  fallback)".

### Reusable Phase-1/3/4 code (read before writing the data path + run)
- `src/personacore/config.py` — `RuntimeConfig` (device/AMP resolution, bf16-on-Pascal guard) and
  `ModelConfig`/`TrainConfig`. **D-02 modifies `RuntimeConfig` to detect MPS + force fp32 there.**
- `src/personacore/preflight.py` — `preflight_p100(require_p100=...)`. **D-02 renames it to
  `preflight_device` (CUDA-P100 → MPS → CPU priority).**
- `scripts/preflight_demo.py` — caller of the preflight fn; update for the D-02 rename.
- `src/personacore/training/data.py` — bounded-fixture `load_split` + nanoGPT `get_batch`
  (random contiguous `block_size` windows, start bounded to `len-block_size-1`, `uint16`→`int64`
  at batch time). The full-corpus memmap path mirrors `get_batch` (PRE-01).
- `src/personacore/training/loop.py` — the proven `train(...)` orchestration: AMP/accum/clip
  ordering, `estimate_loss` (RNG-snapshot val), resume (RNG-state restore, never re-seed), CSV
  curve append-on-resume, end-of-call `save_checkpoint`. **Reused for the long run** (the run is a
  `corpus_path`-style data source pointed at the memmaps; best-val-loss tracking is the main
  addition).
- `src/personacore/checkpoint.py` — open-dict `save_checkpoint`/`load_checkpoint`, full RNG
  restore, `**extra` seam. Resumable run depends on this (D-04). `weights_only=False` on resume
  (own trusted file); Phase-8 slim ckpt uses `weights_only=True`.
- `src/personacore/model/gpt.py` — the trained model; `forward(idx, targets=None)->(logits,loss)`
  contract, autocast-safe. Must run correctly under `device="mps"` (D-01a sanity gate).
- `src/personacore/logging.py` — restart-safe CSV appender for the loss/lr/perplexity curves (PRE-03).
- `src/personacore/seeding.py` / `provenance.py` — determinism + git-SHA-in-checkpoint (QA-02).

### Carried-forward decisions
- `.planning/phases/04-gpt-transformer-decoder/04-CONTEXT.md` — model sizing (~13.9M),
  `attn_impl` default `manual`, locked forward contract; D-02 there left precision/attn switchable
  for Phase 5 (now moot under fp32-MPS).
- `.planning/phases/03-bigram-baseline-training-harness/03-CONTEXT.md` — D-02 forward contract,
  D-09 module layout, the doc-level no-leakage split + `get_batch` idiom the memmap path extends.
- `.planning/phases/02-from-scratch-bpe-tokenizer/02-CONTEXT.md` — `vocab_size=8192`/`eos_id=8184`
  locked; `artifacts/tokenizer.json` is the FROZEN production artifact reused with no retrain.
- `.planning/phases/01-scaffolding-reproducible-environment/01-CONTEXT.md` — no CLI/argparse
  (thin scripts), `RuntimeConfig` as the single device/precision source (the thing D-02 extends).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `training/loop.py::train(...)` — already does AMP/accum/clip, periodic `estimate_loss`,
  resumable checkpointing, and restart-safe CSV logging. The long run is this loop pointed at the
  full-corpus memmaps; the new work is the memmap data source + best-val-loss tracking (D-08) +
  periodic sample generation (D-06).
- `training/data.py::get_batch` — the random-window sampler is corpus-size-agnostic; the
  full-corpus path swaps the in-RAM `uint16` array for an `np.memmap` with the same indexing.
- `checkpoint.py` open-dict + full-RNG restore — gives the "as long as it takes / survive
  interrupts" guarantee (D-04) for free; no format change needed.
- `RuntimeConfig` is the single device/AMP source — D-02 adds MPS detection here so the WHOLE
  stack (loop, scaler-disabled, model `.to(device)`) follows automatically.

### Established Patterns
- **Single device/precision source of truth** (`RuntimeConfig`) — MPS support belongs there, not
  scattered `torch.backends.mps` checks. fp32-on-MPS mirrors the existing AMP-off-on-CPU posture.
- **Frozen-tokenizer reuse** — load `artifacts/tokenizer.json`, never `.train()` (Pitfall 6).
- **`uint16` memmap, `int64` only at batch time** — compact storage, cast for embedding/CE.
- **Doc-boundary EOS, no mid-doc leakage** — preserved; here leakage is avoided trivially by
  using the separate official `valid` file (D-05).
- **CPU-only test suite** — Phase-5 tests must stay GPU/MPS-free; the MPS run itself is exercised
  manually + via a guarded smoke (skipif no MPS).
- **Thin `scripts/` entry points, no CLI/argparse** (Phase-1 D-04).

### Integration Points
- `preflight_device` (renamed) → run entry script asserts the active device before the long run.
- New memmap data path → `training/loop.py` via the existing `corpus_path`/`get_batch` seam.
- Best-val-loss checkpoint → consumed by Phase 6 `generate()` and Phase 8 slim-checkpoint export.
- CSV curve + recorded perplexity → Phase 7 evaluation + Phase 8 `demo.ipynb`.

</code_context>

<specifics>
## Specific Ideas

- **On-device training is the point now** — the user deliberately moved the *training* run onto
  their own M3 (MPS), not just inference. Downstream framing/writeup should lean into this as a
  reinforcement of the privacy/zero-budget/on-device thesis, not treat it as a workaround.
- **Verbatim infra request (D-01/D-02):** "Adiciona suporte a MPS no RuntimeConfig. Quando
  device='mps' está disponível, usa torch.backends.mps.is_available(). Atualiza o preflight_p100
  para preflight_device que detecta: CUDA P100 → mps → cpu, nessa ordem de prioridade. fp16 AMP
  não funciona no MPS — usa fp32 por padrão no M3."
- **Fluency bar = TinyStories paper's register** (D-07) — grammatical, on-topic, simple coherent
  short narratives; judged on curated samples alongside a perplexity number.

</specifics>

<deferred>
## Deferred Ideas

### ⚠ Required requirements/roadmap rewording (NOT optional — consequence of D-01)
The "M3/MPS replaces Kaggle P100" decision invalidates locked text. Before/at Phase-5 planning,
update so the artifacts stay coherent:
- `.planning/REQUIREMENTS.md` **PRE-01** — drop "pinned/persisted as a versioned Kaggle Dataset";
  replace with local `uint16` memmap persistence.
- `.planning/REQUIREMENTS.md` **PRE-02** — drop "Kaggle P100 run … within the 30h/week budget …
  dataset-persisted"; replace with resumable local M3/MPS run.
- `.planning/ROADMAP.md` Phase-5 success criteria #1/#2 — same reword.
- `.planning/PROJECT.md` constraints + `CLAUDE.md`/`STACK.md` — reframe "train on Kaggle P100" →
  "train on M3/MPS (Kaggle P100 optional fallback)"; keep the bf16-guard + memmap + offline-logging
  guidance.
- Suggested mechanism: `/gsd-phase` edit for the ROADMAP criteria + a direct REQUIREMENTS/PROJECT
  edit, sequenced with the D-02 device-layer work (which the user wants done NOW, before planning).

### Lower-priority / later phases
- **fp16 AMP / sdpa for memory** — moot on MPS (fp32 only); only relevant if a CUDA fallback run is
  ever used. Carried, not actioned.
- **KV-cache for CPU/MPS inference latency** — Milestone-2 / Phase-8-conditional (already deferred).
- **Architecture / LR ablation table** — Phase 7 (EVAL-03).
- **Full `generate()` (top-k/top-p, EOS-stop)** — Phase 6 (GEN-01..03).

</deferred>

---

*Phase: 05-tinystories-pretraining*
*Context gathered: 2026-06-05*
