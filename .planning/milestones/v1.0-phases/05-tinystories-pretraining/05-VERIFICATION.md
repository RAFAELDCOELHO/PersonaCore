---
phase: 05-tinystories-pretraining
verified: 2026-06-11T00:00:00Z
status: passed
score: 3/3 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: none
  note: "Retroactive verification performed at milestone audit (2026-06-11). The phase executed 2026-06-05 but no VERIFICATION.md was created at the time; this report closes that gap from live codebase + on-disk artifact evidence, not SUMMARY claims."
warnings:
  - "scripts/pretrain_tinystories.py:52-56 — five TODO(calibration) markers remain on constants that ARE the shipped-final calibrated values (lr=3e-4, batch=32, accum=1, max_steps=50000, eval=250, matching best.pt's embedded train_config exactly). Stale markers, not missing work; recommend deleting the TODO prefixes."
  - "src/personacore/training/loop.py:305 — tokens_per_step = batch_size × grad_accum_steps omits × block_size; run.csv 'tokens' column under-counts ×256 (logs 1,600,000 at step 50000 vs ~409.6M actual). Loss/lr/step curves are unaffected; telemetry blemish only."
  - ".planning/REQUIREMENTS.md:44-45,120-121 — PRE-02/PRE-03 traceability rows still read 'Pending'/unchecked despite being satisfied (PRE-01 row is checked). Tracking staleness only."
---

# Phase 5: TinyStories Pretraining Verification Report

**Phase Goal:** The trained checkpoint everything downstream consumes — the visceral proof the LM works — produced by a full, resumable local M3/MPS run (fp32) on TinyStories to coherent, fluent generation. Kaggle P100 is an optional fallback.
**Verified:** 2026-06-11
**Status:** passed
**Re-verification:** No — retroactive initial verification (milestone audit; the phase completed 2026-06-05 without a VERIFICATION.md)

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP Success Criterion) | Status | Evidence |
| --- | --- | --- | --- |
| 1 | TinyStories obtained, encoded once (frozen tokenizer) into a `uint16` memmap with one EOS between documents, persisted on local disk; official TinyStoriesV2 `valid` file is the no-leakage held-out split [PRE-01] | ✓ VERIFIED | `scripts/encode_corpus.py:42-99` streams per-document on `<|endoftext|>`, encodes via `from_json` (`:75`, never `.train()`) with `allowed_special="all"` (`:86` — atomic eos 8184, no manual injection), writes `uint16` via `.tofile` (`:90`). On disk: `data/train.bin` 2,503,912,242 B = 1,251,956,121 tokens; `data/val.bin` 25,273,846 B = 12,636,923 tokens (built 2026-06-05 from `TinyStoriesV2-GPT4-train.txt` 2.23 GB / `-valid.txt` 22.5 MB — sizes match the cited official files; val is disjoint by construction, `:33-34`). Live probe of the REAL train.bin: max id 8184 < 8192; 10,725 EOS in first 5M tokens, **zero doubled-EOS pairs**; decoded prefix is a coherent story ("Once upon a time there was a little boy named Ben…"). `pytest tests/test_memmap_data.py` 4/4 green live. |
| 2 | Full local M3/MPS run (fp32) trains the GPT to fluent, coherent generation — quality-first, surviving session kills via resumable checkpoints [PRE-02] | ✓ VERIFIED | `scripts/pretrain_tinystories.py` gates on `preflight_device(strict=True)` (`:65`), asserts LOCAL `.bin`s (`:69-73`, no `/kaggle/input`), builds the real `GPT(ModelConfig())` (`:78`), resumes from `latest.pt` iff present (`:93`), sets `PYTORCH_ENABLE_MPS_FALLBACK=1` before torch import (`:32`). Memmap seam wired at `loop.py:256-265`; resume restores RNG state, never re-seeds (`:288-294`). Live: `test_resume_memmap.py` (bit-for-bit kill+resume on the memmap source, CPU oracle) GREEN; `test_mps_smoke.py` **RAN on this M3 (not skipped) and PASSED in 12.8s** (finite-loss + overfit gates, D-01a). `checkpoints/best.pt` (166.8 MB, 2026-06-05 22:18) embeds `train_config` lr=3e-4/batch=32/max_steps=50000/seed=1337 and git_sha `3a46815` (= the committed Task-4 pause marker). `results/run.csv` is a single-header, strictly-monotonic 200-row curve on an exact 250-step grid to step 50000 — the restart-safe CSVLogger contract held across the run. Coherence: committed `results/samples.md` holds grammatical TinyStories-register stories from best.pt; Phase-7 HUMAN-UAT (complete) re-attested sample quality downstream. |
| 3 | A trained checkpoint is produced (best val-loss), and final/val perplexity plus training curves are recorded for the writeup [PRE-03] | ✓ VERIFIED | Live `torch.load('checkpoints/best.pt')`: `step=49000`, `val_loss=0.7378001868724823`, full resume state (optimizer/scheduler/scaler/rng/configs/schema_version/git_sha). Independent `awk` over `results/run.csv`: global min val_loss = 0.7378001868724823 **at step 49000, not the final step 50000 (0.73935)** — the best-val contract held on the real run (seam at `loop.py:300,340-353`; gated by `test_best_ckpt.py`, green live, dip-then-rise non-tautological). Curves committed at `results/run.csv` (201 lines, == `logs/run.csv` byte-for-byte). Perplexity recorded for the writeup: checkpoint-derived exp(0.7378)=2.0913, and the headline deterministic full-val sweep **2.1066 over 12,636,922 scored target tokens** (= val.bin's 12,636,923 tokens − 1 shift) in `results/samples.md:8`, `results/results.md:10`, `README.md:15`, `docs/REPORT.md:255,377`. |

**Score:** 3/3 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `scripts/encode_corpus.py` | Run-once streaming encode → train.bin/val.bin, no CLI | ✓ VERIFIED | 113 lines; streams line-by-line per `<|endoftext|>` doc (`_iter_documents`, never one 2.23 GB string); frozen `from_json`; post-build EOS-count + decode-prefix sanity (`:92-98`); no argparse. |
| `src/personacore/training/data.py::get_batch_memmap` | Memmap sampler mirroring `get_batch`, re-opened per call | ✓ VERIFIED | `:73-90` — `np.memmap` re-opened inside the function each call (`:84`, nanoGPT leak-avoidance); identical `len-block-1` bound, `uint16→int64` at draw, plain `.to(device)`; zero `pin_memory`/`non_blocking`. |
| `src/personacore/training/loop.py` | 4 additive seams (memmap branch, estimate_loss path, best-val best.pt, periodic latest.pt + sample hook) | ✓ VERIFIED | Seam 1 `:256-265`; Seam 2 `:84-95` with `_rng_state()`/`_restore_rng()` wrapper preserved (`:78,101`); Seam 3 `:300,340-353`; Seam 4 `:357-380`. All guarded by optional kwargs (default None/off); `_optimizer_step` `:122-147` keeps the locked scale→backward→unscale_→clip→step→update→scheduler ordering. |
| `scripts/pretrain_tinystories.py` | Thin no-CLI run entry: preflight LOCAL memmaps, calibrated config, resume, post-run sample + perplexity | ✓ VERIFIED | 131 lines; `preflight_device(strict=True)`; LOCAL paths only (no `/kaggle/input`); real `GPT`; resume-from-latest; prints `exp(best_val_loss)` + decoded samples (`:117-127`). |
| `tests/test_memmap_data.py` | 4 PRE-01 tests (roundtrip, one-EOS, in-bounds, no-leakage) | ✓ VERIFIED | All 4 node-ids present; non-tautological; **4 passed live** (this verification). |
| `tests/test_mps_smoke.py` | Skipif-guarded MPS finite-loss + overfit gate | ✓ VERIFIED | Module-level `skipif(not torch.backends.mps.is_available())`; **1 passed live on this M3** (ran, not skipped). |
| `tests/test_resume_memmap.py` | Bit-for-bit resume on the memmap source | ✓ VERIFIED | Ref-vs-kill+resume within 1e-6 (loss AND param tensor); **passed live**. |
| `tests/test_best_ckpt.py` | best.pt lowest-val + perplexity recoverability | ✓ VERIFIED | Scripted dip-then-rise val curve; asserts `blob["val_loss"] == min` AND `!= final`; **passed live**. |
| `tests/fixtures/tinystories_fixture.txt` | ≥3-doc `<|endoftext|>` micro-corpus | ✓ VERIFIED | 4 docs (test asserts `len(docs) >= 3` and passes). |
| `data/train.bin` / `data/val.bin` (gitignored) | Full-corpus uint16 memmaps | ✓ VERIFIED | 1.25B / 12.64M tokens on local disk; `.gitignore` covers `data/`; live decode + EOS-discipline probes pass on the real files. |
| `checkpoints/best.pt` + `latest.pt` (gitignored) | Trained best-val + resume checkpoints | ✓ VERIFIED | Both on disk (2026-06-05); best.pt blob inspected live (step 49000, val_loss 0.7378, full state); `.gitignore` covers `checkpoints/`/`*.pt`. |
| `results/run.csv` (committed) | Training curves for the writeup | ✓ VERIFIED | Committed (`git ls-files`); 201 lines; identical to `logs/run.csv`; clean monotonic 250-step grid, single header. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `scripts/encode_corpus.py` | `artifacts/tokenizer.json` | `from_json` (FROZEN — never `.train()`) | ✓ WIRED | `:75`; grep confirms zero `.train()` calls in the script. |
| `data.py::get_batch_memmap` | `data/train.bin` | `np.memmap` re-opened per call | ✓ WIRED | `:84`; live draw from the REAL train.bin: shape (4,256), int64, y == x shifted-by-one, max id 8184. |
| `training/__init__.py` | `get_batch_memmap` | barrel re-export + `__all__` | ✓ WIRED | Both present; `from personacore.training import get_batch_memmap` resolves. |
| `scripts/pretrain_tinystories.py` | `data/train.bin` / `data/val.bin` | `train(train_bin=…, val_bin=…)` memmap seam | ✓ WIRED | `:102-103`. |
| `scripts/pretrain_tinystories.py` | `preflight_device(strict=True)` | long-run device gate on LOCAL paths | ✓ WIRED | `:65`; no `/kaggle/input` reference anywhere in the script. |
| `loop.py` | `checkpoints/best.pt` | `save_checkpoint` when `val_loss < best_val_loss` | ✓ WIRED | `:340-353`; proven on the real run — best.pt is step 49000, NOT final step 50000. |
| `loop.py::estimate_loss` | `get_batch_memmap` | val_ids-as-path branch (`_is_bin_path`) | ✓ WIRED | `:84-95`; RNG snapshot/restore wrapper intact (resume-equality contract). |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `data/train.bin` | corpus token stream | TinyStoriesV2-GPT4-train.txt → frozen tokenizer | Yes — live decode of the real bin yields coherent story text; EOS discipline holds (0 doubled pairs in 5M tokens) | ✓ FLOWING |
| `checkpoints/best.pt` | model weights + val_loss | 50k-step M3/MPS run via the wired seams | Yes — blob holds trained weights consumed live by Phases 6-8 (slim export, headline-PPL reproduction); val_loss matches run.csv global min exactly | ✓ FLOWING |
| `results/run.csv` | train/val/lr curves | CSVLogger in the eval branch | Yes — 200 real eval rows, val_loss 2.38 → 0.7378, smooth cosine lr decay | ✓ FLOWING |
| `results/samples.md` | curated generations | generate over best.pt (Phase 7 driver) | Yes — real coherent TinyStories-register text | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| PRE-01 data tests + PRE-02 resume + PRE-03 best-ckpt | `.venv/bin/python -m pytest -q tests/test_memmap_data.py tests/test_resume_memmap.py tests/test_best_ckpt.py` | **6 passed in 5.87s** | ✓ PASS |
| MPS sanity gate (D-01a) on this M3 | `.venv/bin/python -m pytest -q tests/test_mps_smoke.py` | **1 passed in 12.76s** (ran on MPS, not skipped) | ✓ PASS |
| best.pt blob integrity | live `torch.load('checkpoints/best.pt')` | step=49000, val_loss=0.7378001868724823, exp=2.0913, git_sha=3a46815, full optimizer/scheduler/scaler/rng/config state | ✓ PASS |
| best.pt = global-min val, not final step | `awk` min over `results/run.csv` | min 0.7378001868724823 @ step 49000 (final 50000 = 0.73935) — exact match to blob | ✓ PASS |
| Real-corpus EOS discipline + round-trip | live numpy/tokenizer probe on `data/train.bin` | 10,725 EOS / 0 doubled in first 5M tokens; coherent decoded prefix; max id 8184 < 8192 | ✓ PASS |
| Live memmap draw from real bin | `get_batch_memmap('data/train.bin', 4, 256, 'cpu')` | (4,256) int64, y == x shifted-by-one, in-vocab | ✓ PASS |
| Curve continuity across kill+resume | header count + step-grid awk on `results/run.csv` | 1 header, 200 rows on exact 250-grid 250→50000, no duplicates/gaps | ✓ PASS |
| Task commits exist | `git log -1` × 7 hashes | all 7 present (ea1cd5c, bfe4fb8, 075be1a, 1422b4c, 35577b4, 38dd1d9, 3a46815) | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` probes exist or are declared by either PLAN — probe contract not applicable to this phase. Skipped.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| PRE-01 | 05-01 | Corpus obtained, encoded once into uint16 memmap (one EOS/doc), official valid = held-out split | ✓ SATISFIED | Truth 1: encode_corpus.py + real .bin probes + 4/4 tests green live. |
| PRE-02 | 05-02 | Pretrained on TinyStories to fluent coherent generation; local M3/MPS fp32 primary, resumable; Kaggle optional fallback (unused) | ✓ SATISFIED | Truth 2: MPS smoke passed live on M3; bit-for-bit resume proven; best.pt from the 50k M3 run; coherent samples committed. Fallback unused by design — criterion says "optional". |
| PRE-03 | 05-02 | Final/val perplexity + training curves recorded for the writeup | ✓ SATISFIED | Truth 3: best.pt val_loss 0.7378 / exp=2.0913; headline full-val PPL 2.1066 over 12,636,922 tokens in results/samples.md, results.md, README, REPORT; run.csv committed. |

No orphaned requirements: REQUIREMENTS.md maps exactly PRE-01/02/03 to Phase 5; both plans claim all three. (Tracking staleness: PRE-02/PRE-03 rows still read "Pending" — see warnings.)

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `scripts/pretrain_tinystories.py` | 52-56 | Five `TODO(calibration)` markers on the calibration constants | ⚠️ Warning | The constants ARE the shipped-final measured values (they match best.pt's embedded train_config field-for-field: lr=3e-4, batch=32, accum=1, max_steps=50000, seed=1337) — the markers should have been removed after Task-4 calibration filled them in. Stale comments, not missing work; misleading to a reader. No TBD/FIXME/XXX blocker-class markers anywhere in phase files. |
| `src/personacore/training/loop.py` | 305 | `tokens_per_step = batch_size × grad_accum` omits `× block_size` | ⚠️ Warning | run.csv `tokens` column under-counts by ×256 (1,600,000 logged at step 50000 vs ~409.6M tokens actually consumed). Pure telemetry: training, loss/lr curves, checkpointing, and resume are all step-indexed and unaffected. Worth a one-line fix + column note if the tokens column is ever plotted. |
| `05-02-SUMMARY.md` | — | Claims "17M-param GPT" / "17.04M total" | ℹ️ Info | 17,037,312 is the raw state_dict numel (the tied `lm_head.weight`/`wte.weight` serialized as two entries); the true unique-parameter count is 13,891,584 (tied-once, inside the 10-15M band — Phase 4 verification). The SUMMARY's "slightly above target" framing over-counts; no code impact. |
| best.pt vs headline | — | Two perplexity figures coexist (2.0913 vs 2.1066) | ℹ️ Info | exp(best eval-estimate val_loss) = 2.0913 (20 random batched windows, recorded in best.pt) vs deterministic full-val sweep = 2.1066 over 12,636,922 tokens (Phase 7 EVAL-01). Both are honest; the writeup correctly leads with the rigorous 2.1066. Not a contradiction — different estimators. |
| `artifacts/tokenizer.json` (upstream) | — | Only 547 of 8192 vocab ids live (fixture-trained tokenizer) | ℹ️ Info | A Phase-2 artifact honestly documented in README.md:29 / docs/REPORT.md:64 (post-08-08). Consequence for Phase 5: the corpus encodes near byte-level (train.bin = 1.25B tokens vs ~500M expected with a corpus-trained vocab). The Phase-5 criteria require encoding "from the frozen tokenizer" — which it is — and the coherence/perplexity bar was met anyway. Documented, not hidden. |

### Human Verification Required

None outstanding. The one inherently-human item in this phase — the D-07 qualitative coherence judgement on the trained model — was exercised twice: at the Task-5 blocking human-action checkpoint during execution (resume-signal "shipped" with curated samples), and again downstream in Phase 7's HUMAN-UAT (status: complete), which reproduced the headline PPL against best.pt and re-attested sample quality. The committed `results/samples.md` text was re-read during this verification and is grammatical, on-topic, TinyStories-register narrative. The "kill+resume succeeded on the real run" sub-claim is human-attested from execution; the resume *mechanism* is independently machine-proven bit-for-bit by `test_resume_memmap.py` (green live) and the single-header continuous run.csv is consistent with a mid-run resume having occurred.

### Gaps Summary

No gaps block the phase goal. All three ROADMAP success criteria are observably true in the codebase and on-disk artifacts, verified by direct execution and live probes rather than SUMMARY claims:

- **The data path is real:** `data/train.bin` (1.25B tokens) and `data/val.bin` (12.64M tokens) exist on local disk, built once by the streaming encoder from the official TinyStoriesV2-GPT4 files through the frozen tokenizer. Live probes of the real bins confirm in-vocab ids, exactly-one-EOS discipline (zero doubled pairs), and coherent decode round-trip. Train/val are disjoint by construction (separate official source files).
- **The run is real and resumable:** the MPS smoke gate passed live on this M3 (ran, not skipped); bit-for-bit kill+resume on the memmap source is machine-proven; the four loop seams are additive with the load-bearing `_optimizer_step` ordering and RNG-restore contract intact; `best.pt` carries the full resumable state and the git SHA of the launching commit.
- **The deliverable is real:** `best.pt` holds the run's global-minimum val loss (0.7378 at step 49000 — independently recomputed from run.csv, and provably NOT the final step), perplexity is recorded both as exp(best_val_loss)=2.0913 and as the rigorous headline 2.1066 over 12,636,922 tokens in four committed documents, and the 200-row training curves are committed at `results/run.csv`.
- **Downstream consumption corroborates:** Phase 6 generated from it, Phase 7 reproduced the headline PPL against it, Phase 8 slim-exported it (step 49000) to a CPU demo, and the 2026-06-10 milestone integration check executed the full chain live (20/20 links wired). The checkpoint everything downstream consumes exists and works.

Three warnings are recorded (stale TODO(calibration) markers carrying the final values, the ×256 tokens-column under-count at loop.py:305, and REQUIREMENTS.md tracking staleness for PRE-02/03) plus three info notes (the 547-live-id tokenizer caveat — honestly documented, the dual perplexity figures, and the SUMMARY's tied-weight double-count). None affects goal achievement.

---

_Verified: 2026-06-11 (retroactive, at milestone audit)_
_Verifier: Claude (gsd-verifier)_
