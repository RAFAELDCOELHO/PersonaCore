# Phase 8: Demo & Writeup - Context

**Gathered:** 2026-06-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 8 ships **the tangible portfolio artifacts** that prove the from-scratch model runs
on-device and reads as rigorous — the Milestone-1 closer. Five deliverables:

- **DEMO-01** — offline Gradio chat UI (`gr.ChatInterface`, `share=False`, localhost) running
  the model on laptop CPU with temperature/top-k controls, streaming via the Phase-6 text wrapper.
- **DEMO-02** — slim fp32 inference checkpoint (no optimizer state, safe `weights_only=True`
  load) that loads and generates on CPU, verified by an offline test.
- **DEMO-03** — `demo.ipynb` research artifact: training curves from `logs/run.csv`, sampling,
  exact parameter count.
- **DOC-01** — polished technical writeup consolidated from the document-as-we-go notes
  (light consolidation per the roadmap decision, not a heavy standalone block).
- **QA-01 / QA-02** — full per-component test suite green via pytest; reproducibility
  discipline re-verified (config-in-checkpoint, seeds, git SHA).

**Mode:** MVP. This phase **does not** change the model, tokenizer, training loop, `generate()`,
or the resume-checkpoint format. LoRA/EWC/personalization and the teach-then-recall demos are
**Milestone 2**. The KV-cache question is resolved by the phase-level researcher on **measured
CPU latency** (carried blocker), not pre-decided here.

</domain>

<decisions>
## Implementation Decisions

### Writeup shape & story (DOC-01)
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

### Notebook narrative scope (DEMO-03)
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
*(Gray areas the user chose not to discuss — researcher/planner resolve within these bounds.)*
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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope & requirements
- `.planning/ROADMAP.md` §"Phase 8: Demo & Writeup" — goal + 5 success criteria + the
  phase-level research flag (KV-cache on measured CPU latency; Gradio 5 streaming +
  fully-offline launch behavior).
- `.planning/REQUIREMENTS.md` — DEMO-01, DEMO-02, DEMO-03, DOC-01, QA-01, QA-02 acceptance
  text; cross-cutting note that QA-01/DOC-01 are consolidated/owned here.
- `.planning/PROJECT.md` — Core Value, vision framing for D-02, zero-budget / on-device /
  privacy constraints; Key Decisions table (Gradio-as-primary-demo, document-as-we-go).

### Evaluation artifacts the notebook/writeup render
- `results/results.md` — EVAL-03 ablation cohort table (self-consistent reduced-budget cohort;
  NOT comparable to the 50k headline — preserve that caveat verbatim in notebook/REPORT).
- `results/samples.md` — curated EVAL-02 qualitative samples ("representative, not
  cherry-picked" — keep the honest selection-method note).
- `results/abl_baseline.csv`, `results/abl_no_tie.csv`, `results/abl_no_pos.csv`,
  `results/abl_depth_cut.csv` — per-run ablation curves for the notebook's cohort plots.
- `logs/run.csv` — the 50k-step training curve (DEMO-03's required data source).

### Reusable code (read before writing the demo/notebook)
- `src/personacore/generation/text.py` + `generation/core.py` — the streaming `str→str`
  wrapper (running-buffer delta, EOS-clean, `[eos_id]`-seeded) built FOR this demo (Phase-6
  D-01/D-03/D-06); the Gradio callback consumes it.
- `src/personacore/checkpoint.py` — `save_checkpoint`/`load_checkpoint`; resume file is
  `weights_only=False` (trusted own-file), the slim artifact is the `weights_only=True` path
  (Phase-1 01-02 decision).
- `src/personacore/evaluation/perplexity.py` + `scripts/evaluate.py` — the deterministic
  full-val sweep behind the headline 2.1066 number cited in README/notebook.
- `src/personacore/config.py` — `ModelConfig` (incl. `weight_tying`/`use_pos_emb` flags) and
  `RuntimeConfig` (CPU resolution for the demo); config travels in the checkpoint (QA-02).
- `src/personacore/tokenizer/` + `artifacts/tokenizer.json` — frozen production tokenizer,
  loaded data-only (never retrained).
- `checkpoints/best.pt` — the source the slim checkpoint is exported from.
- `pyproject.toml` — `[demo]` extra (`gradio>=5,<6`, `matplotlib~=3.10`) already defined;
  the demo install story is `pip install -e ".[cpu,demo]"`.

### Carried-forward decisions
- `.planning/phases/07-evaluation/07-CONTEXT.md` — eval artifacts produced for Phase 8 to
  render; the "report PPL with its token denominator" rigor signal (carry into README/REPORT).
- `.planning/phases/06-generation-sampling/06-CONTEXT.md` — `generate()` contract, streaming
  wrapper design, "no raw separator ever shown"; KV-cache deferred-to-Phase-8-on-measurement.
- `.planning/phases/05-tinystories-pretraining/05-CONTEXT.md` — the on-device M3/MPS training
  story (lean into it in the writeup as thesis reinforcement, not a workaround); D-07
  fluency-bar register.
- `.planning/phases/*/*-VERIFICATION.md` (phases 02–07) — the document-as-we-go evidence base
  the decision-driven REPORT consolidates.
- `CLAUDE.md` — stack guidance: Gradio 5 ChatInterface, safetensors-for-shippable-weights
  recommendation, offline/no-network posture, notebook keeps heavy training out.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `generation/text.py` streaming wrapper — drop-in producer for `gr.ChatInterface`'s streaming
  callback; already prompt-strips, EOS-stops, and avoids mojibake by design.
- `evaluation/perplexity.py` — re-cite, don't recompute: the headline number and denominator
  are already produced and committed.
- `logging.py` CSV format + `logs/run.csv`, `results/abl_*.csv` — matplotlib-ready inputs for
  notebook curves.
- Full CPU-only pytest suite (37 test files) — QA-01 is a consolidation/green-gate, not new
  test authoring; the only new test is the DEMO-02 slim-checkpoint offline load/generate test.

### Established Patterns
- Thin `scripts/` entry points, no CLI/argparse (Phase-1 D-04) — the demo launcher and
  slim-export follow this shape.
- CPU-only, GPU/MPS-free test suite — the DEMO-02 test must run on CPU in CI.
- `RuntimeConfig` is the single device source — the demo resolves to CPU through it, no ad-hoc
  device strings.
- Artifacts that ship must never execute code on load (tokenizer.json precedent, T-02-05) —
  the slim checkpoint's safe-load requirement is the same principle.

### Integration Points
- Gradio callback ← `generation/text.py` streaming wrapper ← slim checkpoint + frozen tokenizer.
- `demo.ipynb` ← slim checkpoint (D-08), `logs/run.csv`, `results/*` artifacts.
- README GIF ← captured from the running Gradio demo; README numbers ← `scripts/evaluate.py`
  output already committed in `results/`.
- New files land in: `README.md`, `docs/REPORT.md`, `demo.ipynb`, a demo launcher script, a
  slim-checkpoint export script + its test.

</code_context>

<specifics>
## Specific Ideas

- **Vision-led but honest** — the writeup leads with the weight-memory thesis while being
  explicit that M1 is the foundation and M2 delivers the mechanism; the from-scratch seams
  (LoRA-ready projections, `assemble_loss`, open-dict checkpoints) are the proof the plan is
  real, not vaporware.
- **The GIF is the hero asset** — a story streaming token-by-token on a laptop CPU is the
  single most convincing artifact for "fully on-device" and should sit at the top of the README.
- **One shippable artifact** — slim checkpoint is THE model file: Gradio demo, notebook, and
  the offline test all load it; `best.pt` remains internal training state.
- **Rigor signals carry through** — PPL always cited with its token denominator; ablation
  cohort always presented with its not-comparable-to-headline caveat; samples labeled
  representative-not-cherry-picked.

</specifics>

<deferred>
## Deferred Ideas

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

### None folded
No pending todos matched this phase.

</deferred>

---

*Phase: 8-Demo & Writeup*
*Context gathered: 2026-06-10*
