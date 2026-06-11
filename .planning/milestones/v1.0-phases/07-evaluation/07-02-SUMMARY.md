---
phase: 07-evaluation
plan: 02
subsystem: evaluation
tags: [ablation-flags, weight-tying, positional-embedding, perplexity, eval, samples]
requires:
  - personacore.evaluation.perplexity (Plan 01 — (ppl, total_tokens) contract)
  - personacore.generation.generate_text_str
  - personacore.tokenizer.from_json (frozen artifacts/tokenizer.json)
  - personacore.preflight.preflight_device (strict gate)
  - personacore.config.RuntimeConfig (.device)
provides:
  - personacore.config.ModelConfig.weight_tying (additive flag, default True)
  - personacore.config.ModelConfig.use_pos_emb (additive flag, default True)
  - scripts/evaluate.py (EVAL-01 headline-PPL + EVAL-02 curated-samples driver)
  - results/samples.md (representative greedy + warm samples)
affects:
  - scripts/run_ablations.py (Plan 03 — flips the two flags to run the locked ablation cohort)
tech-stack:
  added: []
  patterns:
    - "Additive default-preserving ModelConfig flags (GPT(ModelConfig()) reproduces today's arch bit-for-bit)"
    - "Flag-gated wpe REGISTRATION (not just forward use) so use_pos_emb=False drops its params from the count"
    - "Thin no-CLI eval driver mirroring pretrain_tinystories.py (preflight GATE then RuntimeConfig)"
key-files:
  created:
    - scripts/evaluate.py
    - results/samples.md
  modified:
    - src/personacore/config.py
    - src/personacore/model/gpt.py
decisions:
  - "wpe is gated at REGISTRATION (if config.use_pos_emb), not only at forward use — the locked Plan-01 test_no_pos count (13,793,280 = default - 98,304) requires wpe to be absent from model.parameters(); gating only the forward use would leave its 98,304 params counted and fail the test"
  - "evaluate.py reconstructs GPT(ModelConfig(**blob['model_config'])); the existing 7-key best.pt lacks the new flag keys, which fall back to True/True (the trained tied+pos arch) — best.pt loads unchanged"
  - "Canonical headline PPL is the deterministic full-val sweep (2.1066 over 12,636,922 tokens), DISTINCT from best.pt's recorded random-batch ppl 2.091 (Pitfall 5); both are stated in output for honesty"
metrics:
  duration_min: 11
  tasks: 2
  files: 4
  completed: 2026-06-09
---

# Phase 7 Plan 02: Ablation Flags + Headline-PPL/Samples Driver Summary

Two additive `ModelConfig` flags (`weight_tying`, `use_pos_emb`, both default `True`) gate the GPT weight-tie and positional-embedding seams so the locked no-tie / no-pos ablations can exist at all — with defaults that reproduce today's architecture bit-for-bit — plus `scripts/evaluate.py`, the thin no-CLI driver that reports the deterministic full-val perplexity (2.1066 over 12,636,922 scored tokens) and emits representative greedy + warm samples to `results/samples.md`.

## What Was Built

- **`src/personacore/config.py`** — appended `weight_tying: bool = True` and `use_pos_emb: bool = True` to the `ModelConfig` dataclass (after `dropout`, no reorder), each commented with the EVAL-03 ablation it enables. They serialize into FUTURE `asdict`-saved checkpoints; the existing 7-key `best.pt` is untouched.
- **`src/personacore/model/gpt.py`** — gated three seams on the flags, all defaulting to today's behavior: (1) `wpe` is created only `if config.use_pos_emb`; (2) the weight tie `self.lm_head.weight = self.wte.weight` runs only `if config.weight_tying`; (3) the forward positional add is now `x = tok_emb`, then `if self.config.use_pos_emb: x = x + self.wpe(pos)`, then `x = self.drop(x)`. The residual-scaled init, `attn_impl`, and bigram loss tail are untouched.
- **`scripts/evaluate.py`** — thin no-CLI driver: `PYTORCH_ENABLE_MPS_FALLBACK` before `import torch`, `_REPO_ROOT`-relative `BEST_PATH`/`VAL_BIN`/`TOKENIZER_PATH`/`RESULTS_DIR`, the two-object device pattern (`preflight_device(strict=True)` GATE, then `runtime = RuntimeConfig()`), `GPT(ModelConfig(**blob["model_config"]))` + `load_state_dict` from the own trusted `best.pt` (`weights_only=False`), EVAL-01 `perplexity(...)` printing both PPL and `total_tokens`, and EVAL-02 greedy+warm `generate_text_str` over a fixed prompt set written to `results/samples.md`.
- **`results/samples.md`** — the EVAL-02 artifact from the real M3 run (greedy + warm continuations for 4 fixed prompts, with an honest "representative, not cherry-picked" header).

## Task Commits

| Task | Name | Type | Commit | Files |
|------|------|------|--------|-------|
| 1 | Additive flags + flag-gated GPT seams | feat (GREEN) | `e4a6fa7` | src/personacore/config.py, src/personacore/model/gpt.py |
| 2 | evaluate.py headline-PPL + curated samples | feat | `c5f0c05` | scripts/evaluate.py, results/samples.md |

## Honest Framing (architectural note)

Per the plan's HONEST FRAMING directive: this plan makes an **additive model-code edit** to `config.py` + `gpt.py`. The phase claim "does not change the model" holds for the **artifacts** — `best.pt`, `tokenizer.json`, `loop.py`, the checkpoint schema, and `generate()` are all untouched — and the flag defaults (`True`/`True`) reproduce the trained architecture exactly (same tied `data_ptr`, same 13,891,584 params). This is the minimum edit that lets the locked no-tie / no-pos ablations be expressed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Gated `wpe` at REGISTRATION, not only at forward use**
- **Found during:** Task 1.
- **Issue:** The plan's interface prose said to keep `self.wpe = nn.Embedding(...)` defined regardless and gate "only its forward USE". But the locked Plan-01 `test_no_pos` asserts `count_parameters == 13,793,280` (= default `13,891,584 - 98,304`), and `count_parameters` iterates `model.parameters()` deduped by `data_ptr`. If `wpe` stays registered, its `block_size*n_embd = 98,304` params are still counted and the test fails (`13,891,584 != 13,793,280`).
- **Fix:** Wrapped the `wpe` creation in `if config.use_pos_emb:` so under the no-pos ablation `wpe` is absent from `model.parameters()`, producing the locked count. The plan's own `<behavior>` block and the param-count literal are the authoritative contract; the "keep wpe defined" prose was reconciled to them. Documented the reasoning in an in-code comment.
- **Files modified:** src/personacore/model/gpt.py
- **Commit:** `e4a6fa7`
- **Note:** Defaults are unaffected — `GPT(ModelConfig())` still creates `wpe` and ties the head; `test_defaults_unchanged` is green.

**2. [Rule 3 - Blocking] Reworded comments to satisfy ruff (E501 + literal "argparse")**
- **Found during:** Tasks 1 and 2 (`make lint` / acceptance grep).
- **Issue:** A `config.py` flag comment hit 102 chars (E501); two `evaluate.py` docstring lines hit 101/102 chars; and the literal token `argparse` in the docstring violated the `grep -c "argparse" == 0` acceptance criterion.
- **Fix:** Trimmed the over-length comments and replaced "NO argparse" with "No CLI flag parsing". No behavior change.
- **Files modified:** src/personacore/config.py, scripts/evaluate.py
- **Commits:** `e4a6fa7`, `c5f0c05`

## Deferred Issues (out of scope)

- `ruff format` reports drift in two **Plan-01** files (`src/personacore/evaluation/perplexity.py`, `tests/test_perplexity.py`). They predate this plan and are outside the 07-02 blast radius — logged to `.planning/phases/07-evaluation/deferred-items.md`, not fixed. All files created/edited in 07-02 pass `ruff check` and `ruff format --check` cleanly.

## Verification

- `pytest tests/test_ablation_config.py tests/test_gpt_weight_tying.py tests/test_gpt_param_count.py tests/test_gpt_init.py tests/test_config.py tests/test_checkpoint.py tests/test_best_ckpt.py -x -q` → **23 passed** (the three ablation-config cases now green).
- `make test` (full CPU suite) → **122 passed, 1 skipped** (the GPU-only fp16 smoke). No regression; the two previously-RED ablation tests flipped to green.
- Default-still-tied + untie-works one-liners both exit 0.
- `grep -c "if config.weight_tying" gpt.py` = 1; `grep -c "if self.config.use_pos_emb" gpt.py` = 1.
- `scripts/evaluate.py`: `ast.parse` OK; `perplexity(` = 3, `generate_text_str` = 4, `preflight_device(strict=True)` = 2, `RuntimeConfig()` = 3, `argparse` = 0, `total_tokens` = 3, `weights_only=False` = 2, `results` = 3; `ruff check`/`ruff format --check` clean.
- **MANUAL (M3, MPS):** `python scripts/evaluate.py` ran end-to-end — printed **headline full-val perplexity = 2.1066 over 12,636,922 scored target tokens** (the canonical deterministic sweep, distinct from best.pt's recorded random-batch ppl 2.091), and wrote `results/samples.md` with coherent greedy + warm TinyStories-style continuations for all 4 prompts.

## Known Stubs

None. Both flags are real gates wired into `GPT.__init__`/`forward`; `evaluate.py` is fully wired to the real `best.pt`, `val.bin`, `tokenizer.json`, and the Plan-01 `perplexity()` — verified by an actual M3 run producing real numbers and samples.

## TDD Gate Compliance

Task 1 is `tdd="true"`. Its RED tests (`test_ablation_config.py::test_untie`, `test_no_pos`) were authored in Plan 07-01 (RED commit `c68a9c0`); this plan provides the GREEN implementation (`e4a6fa7`). The RED→GREEN sequence spans the two plans by design (Wave-0 scaffold → Wave-2 implementation), and both ablation tests are now green with the existing suite intact.

## Self-Check: PASSED

Files (all FOUND):
- scripts/evaluate.py
- results/samples.md
- src/personacore/config.py (weight_tying/use_pos_emb present)
- src/personacore/model/gpt.py (both gates present)

Commits (all FOUND): `e4a6fa7`, `c5f0c05`.
