# Requirements: PersonaCore

**Defined:** 2026-06-11
**Milestone:** v2.0 Weight-Based Memory
**Core Value:** Personalization lives in the weights, not in a prompt or a store — and the from-scratch implementation must be correct enough to prove it.

## v2.0 Requirements

Requirements for this milestone. Each maps to roadmap phases.

### Tech-Debt Pre-Work

- [ ] **DEBT-01**: `run.csv` tokens column counts true tokens (×`block_size` fix in `loop.py` telemetry) — landed before the first v2.0 training run, so forgetting-curve x-axes are correct
- [ ] **DEBT-02**: Dead-id `forbid_ids` policy threaded into `evaluate.py`/the retention-PPL path and frozen one way for all curve points, so in-loop retention metrics are consistent

### LoRA Adapters

- [ ] **LORA-01**: From-scratch `LoRALinear` (A-Gaussian/B-zero init, α/r scaling, configurable rank/alpha/dropout) wraps the six named `nn.Linear` projections via post-load injection — no HF PEFT
- [ ] **LORA-02**: Frozen-base training discipline — gradients flow only to A/B; base params bit-untouched (test-verified)
- [ ] **LORA-03**: Adapter weights save/load as a separate small artifact, compatible with open-dict checkpoints and the LOCKED `weights_only=True` slim contract
- [ ] **LORA-04**: `merge()`/unmerge utility with fp32-tolerance equivalence test (merged forward ≡ base+adapter); demo path always stays unmerged
- [ ] **LORA-05**: Correctness unit tests pin: zero-delta at init, enable/disable round-trip bit-identical to base, param-count formula, tied-embedding safety (`data_ptr` test post-injection)

### EWC Continual Learning

- [ ] **EWC-01**: From-scratch empirical diagonal Fisher estimated from per-example gradients over TinyStories batches (not batched-gradient squaring), normalized, stored with anchor θ* via the open-dict checkpoint seam
- [ ] **EWC-02**: Quadratic penalty `(λ/2)·Σ Fᵢ·(θᵢ−θ*ᵢ)²` plugged in via `assemble_loss(..., extra_penalties=())`; penalty exactly 0 at the anchor (unit test)
- [ ] **EWC-03**: λ calibrated by log-scale sweep with short runs (D-07 pattern), λ* picked off the stability–plasticity tradeoff; sweep logs retained for the frontier plot

### Conversational Data Pipeline

- [ ] **DATA-01**: DailyDialog + PersonaChat acquired by direct download with pinned checksums (ParlAI mirror for DailyDialog — original URL is dead; S3 JSON for PersonaChat), parsed from scratch — no HF `datasets` at runtime
- [ ] **DATA-02**: Dialogues serialized with the already-reserved role tokens (`<|user|>`/`<|assistant|>`/`<|system|>`, ids 8185–8187) through the frozen tokenizer into uint16 memmap bins
- [ ] **DATA-03**: User-turn loss masking via `ignore_index=-100` (parallel mask bins); turn-boundary correctness unit-tested against a hand-built fixture
- [ ] **DATA-04**: Tokenizer-inflation measurement (tokens-per-word, %-over-`block_size` on dialogue text) produced and documented as a gate before fine-tune design — the frozen-tokenizer tax becomes a number, not a surprise

### Stage-2 Conversational Fine-Tune

- [ ] **TUNE-01**: `best.pt` full-fine-tuned on the conversational corpus through the untouched v1.0 `train()` to dialogue-format adherence (conversational val PPL + curated transcripts)
- [ ] **TUNE-02**: Retention metric (TinyStories val PPL vs the 2.1066 anchor) logged at every eval interval during fine-tuning, per-arm CSVs — forgetting curves fall out of training logs, not post-hoc reconstruction

### Demos & Experiments

- [ ] **DEMO-04**: EWC A/B no-forgetting experiment — identical seeds/config/data-order arms differing ONLY in the penalty; both retention AND acquisition reported (retention-only is the classic sleight of hand)
- [ ] **DEMO-05**: Teach-then-recall clean-room demo — 5–10 atomic user facts, ~20–50 template/hand-written paraphrases per fact (no external-API augmentation), LoRA adapter on the frozen conversational base, fresh-process empty-prompt scripted recall with pre-registered thresholds, base-without-adapter control
- [ ] **DEMO-06**: Held-out-phrasing recall split — taught phrasings vs never-seen phrasings scored and reported separately (learning vs memorization)
- [ ] **DEMO-07**: Adapter on/off toggle in the Gradio demo — same process, same prompt, memory on/off live

### Visualization

- [ ] **VIZ-01**: Forgetting-curve figure — retention PPL vs fine-tune steps per arm, dashed baseline at 2.1066, acquisition companion panel; committed to repo
- [ ] **VIZ-02**: Weight-delta heatmap — relative Frobenius change `‖ΔW‖_F/‖W₀‖_F` on the layer×module grid (six named projections), log color scale; committed to repo
- [ ] **VIZ-03**: Fisher heatmap juxtaposed with naive-vs-EWC delta heatmaps (three-panel figure — EWC visibly dodging high-Fisher coordinates)
- [ ] **VIZ-04**: λ stability–plasticity frontier plot (retention vs acquisition, one point per λ from the sweep logs)

### Writeup

- [ ] **DOC-02**: REPORT.md + README v2.0 narrative and updated `demo.ipynb` with honest numbers (recall percentages, retention deltas, tokenizer-inflation tax) in the same register as the v1.0 547-live-ids disclosure

## Future Requirements

Deferred to a later milestone. Tracked but not in the current roadmap.

### Demos & Experiments

- **DEMO-F1**: Two-persona adapter swap — second adapter, different memory, same base weights (strongest scientific control; needs a second teaching set + training run)
- **DEMO-F2**: Prompt-persona measured control — same question set with facts stuffed in context vs adapter-only with empty prompt, framed strictly as a control

### Ablations

- **ABL-F1**: q,v-only vs all-six-projection LoRA ablation (continues v1.0 ablation rigor; one config flag + short calibrated runs)
- **ABL-F2**: Replay-comparison arm as a clearly-labeled honesty line (replay often beats EWC in NLP, but is external-memory-adjacent)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Online / multi-task EWC chains | Designed for long task sequences; PersonaCore has 1–2 transitions — γ-decay machinery with zero narrative payoff |
| KFAC / block-diagonal / full Fisher | Massive complexity; diagonal empirical Fisher is the accepted standard in every EWC reproduction |
| Tokenizer retrain on conversational data | Locked decision (2026-06-11): invalidates `best.pt`, restarts the milestone; inflation tax measured + documented instead (DATA-04) |
| ConvAI2-style chat quality / benchmarks | Unreachable at 13.9M with this tokenizer; failure would overshadow the achievable claim — quality framed as format adherence + fact recall |
| External-API paraphrase generation | Violates zero-budget AND the privacy/on-device thesis at the exact moment it is being demonstrated — template/hand-written paraphrases only |
| Merging LoRA as the demo deploy path | Destroys the on/off toggle — the most convincing demo moment; CPU overhead at 13.9M is irrelevant (`merge()` ships as engineering completeness only, LORA-04) |
| Knowledge editing (ROME/MEMIT-style) | Different mechanism, different claim; a from-scratch reimplementation is a milestone of its own — cite as related work |
| RLHF / DPO / safety tuning | Wrong milestone, wrong scale; SFT with loss masking is the right tool |
| Facts in a system prompt at demo time | Falsifies the core claim — empty-prompt clean room is the protocol; prompt-stuffing appears only as a labeled future control (DEMO-F2) |
| HuggingFace PEFT / transformers model code | Excluded by design across the whole project — everything from scratch |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| — | — | — |

**Coverage:**
- v2.0 requirements: 25 total
- Mapped to phases: 0
- Unmapped: 25 ⚠️ (roadmap pending)

---
*Requirements defined: 2026-06-11*
*Last updated: 2026-06-11 after initial definition*
