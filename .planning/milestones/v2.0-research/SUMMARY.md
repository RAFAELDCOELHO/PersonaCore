# Project Research Summary

**Project:** PersonaCore — Milestone v2.0 "Weight-Based Memory"
**Domain:** From-scratch LoRA adapters + EWC continual learning + conversational fine-tuning (DailyDialog, PersonaChat) on the shipped v1.0 13.9M-param GPT, with teach-then-recall and EWC A/B research demos
**Researched:** 2026-06-11
**Confidence:** HIGH

## Executive Summary

v2.0 is **additive, not a rewrite** — and the research verified this line-by-line against the shipped v1.0 code rather than assuming it. Every seam v1.0 deliberately built is real and sufficient: the six named `nn.Linear` projections per block receive LoRA via post-load `setattr` injection (`model/gpt.py` is never edited); EWC plugs into `assemble_loss(..., extra_penalties=())` through one additive `penalty_fn=None` kwarg on the training loop; Fisher/θ*/lora_config ride the open-dict checkpoint's `**extra` with zero format change; and the chat-role special tokens (`<|user|>`=8185, `<|assistant|>`=8186, `<|system|>`=8187) are **already reserved and decodable** in the frozen tokenizer, so conversational formatting needs no tokenizer change at all. The stack adds **zero new Python dependencies** — torch + numpy + matplotlib + gradio + stdlib cover everything. The only genuinely new external surface is two dataset endpoints, both HTTP-verified live on 2026-06-11 with pinned checksums (critically: the original DailyDialog URL is dead — use the ParlAI mirror on Facebook's CDN).

The load-bearing design decision, converged on independently by the features, architecture, and pitfalls research, is the **two-mechanism stage split**: stage 2 (conversational fine-tune) is a **full-model fine-tune ± EWC** — this is the A/B, because a LoRA-based naive arm would barely forget by construction and hollow out the EWC story; stage 3 (personalization) is **LoRA on the frozen conversational base** — small, swappable, deletable, exactly the per-user memory artifact the privacy narrative needs. This decision should be treated as made, not open: each mechanism gets the stage where its effect is real and measurable, and it resolves the EWC-parameter-space question (classic EWC on base params, not Fisher-of-LoRA-params, which is degenerate at B=0 init).

The key risks are integrity risks, not feasibility risks. The demos are falsifiable claims a skeptical MIT/Stanford-bar reviewer will attack: prompt leakage in the teach-then-recall demo (chat history silently re-injecting the taught facts) would make the novel claim false *as demonstrated*; the most-copied EWC bug in the wild (squaring mini-batch gradients instead of per-example gradients) produces a penalty that isn't the Fisher at all; and a confounded A/B (arms differing in anything but λ, or retention reported without acquisition) measures something other than EWC. Mitigation is protocol discipline baked into phase acceptance criteria: clean-room recall (fresh process, empty context, context-token dump, control triple), per-example Fisher with an analytic fixture test, and pre-registered identical-arm A/B design. One empirical unknown gates the data design: the frozen 547-live-id tokenizer's tokens-per-word inflation on adult dialogue text must be **measured before the pipeline is built**.

## Key Findings

### Recommended Stack

Nothing new to install. All v2.0 features — LoRA, EWC, fine-tuning, demos, figures — are implemented with the pinned v1.0 environment (`torch 2.7.*` fp32 on M3/MPS primary, numpy `~=2.4`, matplotlib `~=3.10`, gradio `>=5,<6`, pytest, stdlib). LoRA is a hand-written composition wrapper (`LoRALinear`), EWC is pure autograd (`p.grad²` accumulation for the empirical diagonal Fisher), and visualizations are `plt.imshow` + CSV line plots. Explicitly rejected: `peft`/`loralib` (LoRA *is* the deliverable), HF `datasets` (its DailyDialog script points at the dead URL anyway), seaborn, pandas/pyarrow, `ijson`, QLoRA/bitsandbytes, opacus.

**Core additions (data, not code):**
- **DailyDialog** via ParlAI mirror `dl.fbaipublicfiles.com/parlai/dailydialog/dailydialog.tar.gz` (~2.6 MB, sha256 pinned, 11,118/1,000/1,000 splits verified) — the original `yanran.li` URL 404s and takes the canonical HF loading script down with it
- **PersonaChat** via HF public S3 `personachat_self_original.json` (~200 MB, plain HTTPS GET, structure byte-inspected) — persona sentences enable the prompt→weights distillation narrative
- **Fetch discipline:** stdlib `urllib.request` + `hashlib` verify → `data/raw/` (gitignored), never network at train time; both CDNs are stable-but-unowned (ParlAI archived 2023), so checksum-and-cache. DailyDialog is CC BY-NC-SA 4.0 (re-hostable with attribution); PersonaChat has no explicit license — do not re-host
- **Preprocessing reuses v1.0 wholesale:** detokenize whitespace-tokenized text → role-token format → frozen-tokenizer encode → `uint16` memmap bins + parallel `uint8` loss-mask bins

### Expected Features

The "users" are portfolio reviewers; table stakes = absence makes the novel claim unproven.

**Must have (committed v2.0 scope, all P1):**
- From-scratch `LoRALinear` over the six named projections + correctness test suite (B=0 identity, grad isolation, merge≡adapter equivalence, param-count formula)
- From-scratch EWC (per-example empirical diagonal Fisher, quadratic penalty via the `assemble_loss` seam, anchor+Fisher in checkpoint) + λ log-scale sweep
- DailyDialog+PersonaChat pipeline with turn formatting, assistant-only loss masking (`ignore_index=-100`, golden-fixture tested), and the tokens-per-word inflation measurement
- Stage-2 conversational fine-tune with TinyStories retention PPL logged every eval interval from step 0
- EWC A/B experiment: identical arms differing only in λ, **both retention and acquisition reported** (retention-only is the classic sleight of hand)
- Teach-then-recall clean-room demo: 5–10 facts, ~10–20 template paraphrases per fact in both QA directions, LoRA adapter on frozen base, fresh-process empty-prompt recall, base-without-adapter control, pre-registered thresholds (~≥80% taught / ≥50% held-out phrasings)
- Forgetting-curve + weight-delta-heatmap figures (committed PNGs); REPORT/README/demo.ipynb v2.0 with honest numbers

**Should have (cheap riders, P2):**
- Live adapter on/off toggle in Gradio — flip a switch, the model forgets you; demo-video gold
- Fisher heatmap juxtaposed with naive-vs-EWC delta heatmaps — makes EWC *visible* (updates dodge high-Fisher cells); the single highest-leverage figure of the milestone
- Held-out-phrasing recall split; λ stability–plasticity frontier plot; prompt-persona measured control

**Defer (P3):** two-persona adapter swap (strongest control, needs a second teaching run), q,v-only vs all-six LoRA ablation, replay comparison arm.

**Anti-features:** online EWC, KFAC/full Fisher, tokenizer retrain (locked decision), chasing ConvAI2 quality, external-API paraphrase generation (violates the thesis at the moment of demonstrating it), merging LoRA as the demo deploy path (kills the toggle), facts in a system prompt at demo time (falsifies the core claim), RLHF/DPO, ROME/MEMIT knowledge editing.

### Architecture Approach

Two new self-contained packages carry the headline deliverables — `lora/` (layer.py + inject.py) and `continual/` (fisher.py + ewc.py) — plus a script family (`prepare_dialog_corpus.py`, `finetune_dialog.py`, `run_ab_forgetting.py`, `personalize_demo.py`, `make_m2_figures.py`). Existing v1.0 modules receive only additive, default-off changes: `training/loop.py` (+`penalty_fn`, +`extra_val_bins`), `training/data.py` (+masked batch variant), `generation/core.py` (+`stop_ids`). All LOCKED contracts hold: `forward()` untouched (masking lives in the data path via `ignore_index=-100`), slim `weights_only=True` artifacts ship as *merged* plain-GPT state dicts, RNG-resume survives (EWC penalty is RNG-free; Fisher runs under forked RNG), and defaults reproduce the v1.0 trajectory bit-for-bit so all 137 existing tests stay green.

**Major components:**
1. `lora/layer.py` + `lora/inject.py` — `LoRALinear` composition wrapper; load-vanilla → inject → freeze order is load-bearing (wrapping before loading breaks every checkpoint key)
2. `continual/fisher.py` + `continual/ewc.py` — `estimate_fisher()` over TinyStories memmap windows at `best.pt`; `EWCPenalty` callable handed to `train()` per micro-batch *before* the `/accum` divide
3. `scripts/prepare_dialog_corpus.py` — role-token-formatted dialogues → aligned token bins + uint8 mask bins; eos 8184 stays a document separator (never a turn terminator); turn-stop at inference = `stop_ids={eos, <|user|>}`
4. Stage-2 driver + A/B runner — reuse `train()` end-to-end (warmup/cosine, grad-accum, kill+resume, best.pt tracking all inherited); new CSV file per run/arm, never appended columns
5. `personalize_demo.py` — `gr.Blocks` Teach/Chat/Reset; ~100–300-step adapter fit on-device; Reset = drop adapter = instant forget
6. `make_m2_figures.py` — pure read-side: CSV → forgetting curves; checkpoint pairs → layer×6-projection ΔW heatmaps (LoRA arms compute ΔW = scale·B@A exactly)

**Cross-file resolution (turn markers):** STACK assumed no special tokens were available and prescribed plain-text `User:`/`Bot:` markers; ARCHITECTURE verified `tokenizer/special.py` line-level and found `<|user|>`/`<|assistant|>`/`<|system|>` already reserved, already in the decodable-mask formula. **Use the reserved role tokens** — zero tokenizer change, atomic encoding, no inflation cost. One caveat carried from PITFALLS: rows 8185–8187 of the tied embedding are suppressed-at-init, so expect an early loss spike on role positions (warmup covers it; check in the stage-2 calibration smoke).

### Critical Pitfalls

1. **Prompt leakage fakes weight-based memory** (the demo-killer) — recall demonstrated in the same session where facts were typed is ordinary in-context lookup. Avoid: clean-room protocol as the demo phase's acceptance criterion — fresh process, empty history, context-token dump displayed, control triple (base fails closed-book / base succeeds in-context / adapter succeeds closed-book).
2. **Fisher computed wrong** (the most-copied EWC bug, van de Ven ICLR 2025) — squaring mini-batch-aggregated gradients is not the Fisher; λ shifts orders of magnitude. Avoid: per-example `grad²` accumulation (cheap at 13.9M), eval mode, TinyStories data at `best.pt`, same loss reduction as training, tied tensor deduplicated by `data_ptr()`, analytic tiny-fixture test, variant named in the writeup.
3. **LoRA correctness cluster** — touching the tied embedding/lm_head tensor (explicit six-name allowlist, never class-based scans), non-zero B init (bit-identical-logits-at-init test), α/r double-scaling at merge (single `scale` source of truth + merge-equivalence test ≤1e-5 on CPU), injecting before loading base weights (load → inject → freeze, pinned by test).
4. **Confounded A/B** — EWC arm "wins" via lower effective LR, mismatched arms, or a LoRA-vs-full-FT mechanism mismatch. Avoid: pre-registered design, arms differ in exactly λ, 2×2 result (acquisition + retention × naive + EWC), penalty and task loss logged separately each interval (ratio 1e-6 or 1e+4 is a diagnosis, not data).
5. **Frozen-tokenizer inflation on dialogue text** — 547 live ids fragment casual vocabulary toward byte level; block_size may hold too little conversation. Avoid: measure tokens/word + %-over-block_size on real corpus samples as the data phase's **first deliverable and go/no-go gate** for the format design.
6. **MPS silent failures + measurement drift** — params-actually-update canary on every run's first step (~10 lines, catches the silent-freeze bug class); one blessed `perplexity()` entry point with per-point provenance for every forgetting-curve point; fix the run.csv ×256 token-count bug **before** the first fine-tune run.

## Implications for Roadmap

v1.0 ended at phase 8; suggested v2.0 phases continue from 9. Phases 9–11 are mutually independent (any order or parallel); 12 needs 10+11; 13 needs 12; 14 needs 9+12; 15 is read-side last.

### Phase 9: LoRA Core
**Rationale:** Zero data/training dependencies — pure unit-testable math; the highest-confidence starting point and half the milestone's name.
**Delivers:** `lora/` package (`LoRALinear`, inject/merge/freeze/state-dict utilities) + full test suite.
**Addresses:** From-scratch LoRA table stake; merge utility; adapter-only "persona file" artifact (~1.3 MB at r=8).
**Avoids:** Pitfalls 1–4 + MPS canary (tied-tensor allowlist, B=0 identity gate, merge-equivalence, inject-after-load discipline, params-update canary).

### Phase 10: EWC Core
**Rationale:** Independent of LoRA (stage-2 is full-FT EWC on base params); needs only existing TinyStories bins + `best.pt`. The Fisher-correctness pitfall justifies doing this as its own carefully-tested phase.
**Delivers:** `continual/` package (per-example empirical diagonal Fisher, `EWCPenalty`), the additive `penalty_fn` hook in `loop.py`, Fisher/θ* checkpoint extras + cache, tests (quadratic-form oracle, zero-at-θ*, penalty-once-per-accum-step, `penalty_fn=None` ≡ v1.0 trajectory).
**Uses:** `assemble_loss(extra_penalties)` seam, open-dict checkpoint `**extra`, existing memmap path.
**Avoids:** Pitfalls 6–7 (Fisher variant, parameter space, tied-tensor dedup).

### Phase 11: Conversational Data Pipeline
**Rationale:** Independent of 9 and 10; gates everything downstream on one empirical measurement (tokenizer inflation) that must happen before format decisions harden.
**Delivers:** `fetch_corpora.py` (checksum-verified ParlAI + S3 downloads), detokenizer, role-token formatting, `dialog_{train,val}.bin` + mask bins, `get_batch_memmap_masked`, `stop_ids` in `generate()`, golden-fixture mask test, **tokens-per-word inflation report (go/no-go gate)**.
**Uses:** Verified dataset endpoints, frozen tokenizer with reserved role ids 8185–8187, v1.0 memmap/encode discipline.
**Avoids:** Pitfalls 13–14 (inflation measured first; masking fixture-tested; eos semantics preserved).

### Phase 12: Stage-2 Conversational Fine-Tune
**Rationale:** Needs 10+11. The long-training phase and the biggest empirical unknown (λ); produces the conversational base both demos stand on.
**Delivers:** `finetune_dialog.py`; calibration smoke (LR, role-token cold-start check); λ log-scale sweep; the EWC stage-2 run → conversational-base checkpoint; dual-task telemetry (`val_tinystories` column from step 0); blessed-PPL-harness contract. Pre-phase cleanup: run.csv ×256 fix; PPL mask-policy decision (recommended: no `forbid_ids` in PPL, matching the 2.1066 headline).
**Avoids:** Pitfalls 8–9, 15 (λ mis-scaling via sweep + dual logging; harness drift via one blessed entry point; fluency collapse via cadenced retention evals + kept checkpoints).

### Phase 13: EWC A/B No-Forgetting Experiment + Forgetting Curves
**Rationale:** Needs 12's harness; runs the λ=0 arm against the EWC arm and produces committed evidence. Design pre-registered during phase 12 planning.
**Delivers:** `run_ab_forgetting.py` (identical seeds/budget, λ the only diff), 2×2 headline table (acquisition + retention × both arms), forgetting-curve figure, optional λ frontier plot from sweep logs.
**Avoids:** Pitfall 10 (confounded A/B).

### Phase 14: Teach-Then-Recall Demo
**Rationale:** Needs 9 (LoRA) + 12 (conversational base — a TinyStories-only model can't hold a QA exchange). Independent of 13. The core-value proof.
**Delivers:** `personalize_demo.py` (gr.Blocks Teach/Chat/Reset, adapter toggle), template paraphrase generator (~10–20/fact, both QA directions, zero-budget), clean-room recall protocol with context-token dump + control triple + pre-registered thresholds, all transcripts committed (failures included), merged-checkpoint ship path via existing slim export.
**Avoids:** Pitfalls 11–12, 16 (prompt leakage; verbatim-only recall via paraphrase diversity + entity tokenizer pre-flight; reviewer framing via the verification kit).

### Phase 15: Figures + Writeup
**Rationale:** Pure read-side; consumes checkpoints/CSVs from 12–14.
**Delivers:** `make_m2_figures.py` — weight-delta heatmaps (layer×6-projection relative Frobenius grid), Fisher-heatmap juxtaposition (the milestone's highest-leverage figure), final forgetting curves; REPORT/README/demo.ipynb v2.0 narrative with honest numbers, named Fisher variant, parametric-memory framing, and a real Limitations section.

### Phase Ordering Rationale

- **9/10/11 first and independent:** the architecture research verified they share no dependencies — LoRA is pure math, EWC needs only v1.0 artifacts, data prep needs only the frozen tokenizer. Front-loads all unit-testable correctness work before any long training run.
- **The two-mechanism split drives the 12/14 ordering:** stage-2 full-FT+EWC must precede stage-3 LoRA personalization both architecturally (the conversational base is LoRA's substrate) and scientifically (the naive arm must be a full fine-tune for the A/B to mean anything).
- **Measurement gates before build commitments:** tokenizer inflation (phase 11, gates format), λ sweep (phase 12, gates the A/B), clean-room recall tested in dev not at the end (phase 14 — if recall fails clean-room, recovery is teaching-set redesign, cheap early and fatal late).
- **Tech debt lands exactly where it bites:** run.csv ×256 and the PPL mask policy are phase-12 pre-work because the forgetting curve's axes depend on them.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 12 (Stage-2 fine-tune):** λ selection is empirical with no universal value (reported range 0.1–10⁶); LR/epoch budget for a 13.9M full-FT on small dialogue corpora needs calibration; the architecture research explicitly flags this as the single biggest unknown. Run `/gsd-plan-phase --research-phase`.
- **Phase 14 (Teach-then-recall):** the protocol is synthesized from knowledge-injection literature (MEDIUM confidence — no canonical reference); fact-recall rates at 13.9M params with a fragmenting tokenizer are genuinely unknown. Worth a discuss/spec pass on the teaching-set template grammar and threshold pre-registration.

Phases with standard patterns (skip research-phase):
- **Phase 9 (LoRA):** paper-canonical mechanics, fully specced including tests; HIGH confidence everywhere.
- **Phase 10 (EWC core):** mechanics are paper-canonical and the pitfalls research already did the verification deep-dive (Fisher variant, fixture tests); the *unknown* (λ) belongs to phase 12, not here.
- **Phase 11 (Data pipeline):** endpoints verified live with checksums; pipeline reuses v1.0 patterns verbatim; the one unknown (inflation) is a measurement task inside the phase, not a research gap.
- **Phases 13, 15:** experiment-running and matplotlib-from-CSV against templates v1.0 already proved (`run_ablations.py`, committed-figure discipline).

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Zero new deps; both dataset endpoints HTTP-verified live 2026-06-11 with sizes/checksums; the dead-URL finding (DailyDialog original) is a verified negative |
| Features | HIGH (mechanics) / MEDIUM (outcomes) | LoRA/EWC/SFT conventions are paper-verified stable knowledge; achievable chat quality and recall rates at 13.9M params are extrapolation from TinyStories + knowledge-injection literature |
| Architecture | HIGH | Every seam claim verified line-by-line against shipped v1.0 code (gpt.py, loop.py, checkpoint.py, special.py, tests); reserved role tokens confirmed first-party |
| Pitfalls | HIGH | Grounded in primary sources: van de Ven 2025 (Fisher bug), HF PEFT issue tracker (tied weights), the MPS silent-freeze post-mortem, knowledge-injection papers |

**Overall confidence:** HIGH

### Gaps to Address

- **λ for EWC:** no portable value exists; the log-scale sweep in phase 12 *is* the resolution. Normalize Fisher so λ is interpretable; log penalty/task-loss ratio every interval.
- **Tokenizer inflation on dialogue text:** unmeasured and corpus-dependent; phase 11's first deliverable. If tokens/word > ~2.5–3 or median examples exceed block_size, the format design (persona-line budget, truncation) must adapt before the pipeline hardens.
- **Recall rates at 13.9M:** pre-register honest thresholds (≥80% taught / ≥50% held-out) and commit failures; partial recall honestly reported beats perfect recall suspiciously reported. If clean-room recall fails, escalate to teaching-set redesign (more paraphrases, simpler entities pre-flighted through the tokenizer).
- **PersonaChat licensing:** no explicit license on the S3 distribution — keep the fetch script + checksum, do not re-host; DailyDialog (CC BY-NC-SA 4.0) may be re-hosted with attribution as link-rot insurance.
- **Stage-2 quality expectations:** generic, short, format-correct replies are the realistic ceiling; frame quality as format adherence + fact recall, never ConvAI2-style chat (anti-feature).
- **v1.0 tech debt on the critical path:** run.csv ×256 token count and the `forbid_ids`-in-PPL policy must be resolved before the first fine-tune run (phase 12 pre-work) or every forgetting-curve axis inherits the error.

## Sources

### Primary (HIGH confidence)
- Shipped v1.0 code, line-level verified: `src/personacore/model/gpt.py`, `training/{loop,loss,data}.py`, `checkpoint.py`, `generation/{core,text}.py`, `tokenizer/special.py`, `evaluation/perplexity.py`, `tests/test_gpt_lora_seam.py`
- `dl.fbaipublicfiles.com/parlai/dailydialog/dailydialog.tar.gz` — 200 OK, sha256 `c3adb09…73e6bb`, splits verified 11,118/1,000/1,000
- `s3.amazonaws.com/datasets.huggingface.co/personachat/personachat_self_original.json` — 200 OK, 209,850,483 B, structure byte-inspected
- `yanran.li/files/ijcnlp_dailydialog.zip` — **404 verified** (load-bearing negative; takes the HF loading-script route down too)
- Hu et al. 2021 (LoRA, arXiv:2106.09685); Kirkpatrick et al. 2017 (EWC, PNAS); "EWC Nuts and Bolts" (arXiv:2105.04093)
- van de Ven, *On the Computation of the Fisher Information in Continual Learning* (arXiv:2502.11756) — the batched-gradient Fisher bug
- HF PEFT issues #2018/#2777/#2864 (tied-weight adapter corruption); Elana Simon 2025 MPS post-mortem
- TinyStories paper (arXiv:2305.07759) — sub-10M coherence/instruction-following feasibility

### Secondary (MEDIUM confidence)
- Ovadia et al., *Fine-Tuning or Retrieval?* (arXiv:2312.05934) + arXiv:2404.00213 — paraphrase-count drives fact-injection recall, saturating ~10/fact
- *LoRA Learns Less and Forgets Less* (arXiv:2405.09673) — the A/B LoRA confound
- PersonaChat schema via thomwolf gist / transfer-learning-conv-ai (corroborated by direct byte inspection)
- PersonaChat licensing read (no explicit license; research-use practice)

### Tertiary (LOW confidence)
- Achievable recall %/chat quality at exactly 13.9M params with the 547-live-id tokenizer — extrapolated, resolved empirically in phases 12/14

---
*Research completed: 2026-06-11*
*Ready for roadmap: yes*
