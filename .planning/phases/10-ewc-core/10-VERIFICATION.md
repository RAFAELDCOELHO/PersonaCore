---
phase: 10-ewc-core
verified: 2026-06-12T20:05:00Z
status: passed
score: 12/12 must-haves verified
overrides_applied: 0
---

# Phase 10: EWC Core Verification Report

**Phase Goal:** From-scratch EWC machinery — per-example empirical diagonal Fisher and the quadratic penalty — plugs into the training loop additively, with v1.0 behavior bit-preserved when the penalty is off
**Verified:** 2026-06-12T20:05:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

Merged must-haves: 4 ROADMAP Success Criteria (the contract) + 8 distinct plan-frontmatter truths.

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1   | SC1: Fisher estimated from per-example gradients over TinyStories at `best.pt` (not batched-gradient squaring), normalized, matches a tiny-fixture oracle | ✓ VERIFIED | `tests/test_fisher.py::test_per_example_oracle` (brute-force per-example oracle, rtol=1e-6/atol=0) + `test_differs_from_batched_gradient_estimate` (rel L2 > 1e-2 anti-van-de-Ven pin) + `test_mean_normalization` — all executed, passed. Real-weights half: `checkpoints/fisher_tinystories.pt` (55.6 MB) loaded via `load_fisher`: n_examples=2000, normalized=True, global mean = 1.0000000269 (fp64), anchor fingerprint = best.pt {git_sha 3a46815…, step 49000, val_loss 0.7378} |
| 2   | SC2: Fisher and anchor θ* persist via the open-dict checkpoint seam and reload intact, tied tensors deduplicated by `data_ptr` | ✓ VERIFIED | `tests/test_fisher_checkpoint.py::test_extra_seam_round_trips` (torch.equal through `save_checkpoint(**extra)`/`load_checkpoint`) + `test_dedup_pinned_through_seam` (`lm_head.weight` absent, `wte.weight` present, `len(theta_star) == len({p.data_ptr()})`) — executed, passed |
| 3   | SC3: Quadratic penalty `(λ/2)·Σ Fᵢ·(θᵢ−θ*ᵢ)²` applied via `assemble_loss` and exactly 0 at the anchor (unit test) | ✓ VERIFIED | `tests/test_ewc_penalty.py::test_exact_zero_at_anchor` (`penalty.item() == 0.0` exact equality) + `test_quadratic_form_oracle` (hand-computed 1.925) + `test_assemble_loss_integration` (torch.equal). Loop splice: `loop.py:149-151` — `penalties = (penalty_fn(model),) …` → `assemble_loss(base_loss, penalties)` → `/accum` after. `test_penalty_once_per_optimizer_step_under_accum` uses a real EWCPenalty — passed |
| 4   | SC4: With `penalty_fn=None` the trajectory is bit-identical to v1.0 and all existing tests stay green | ✓ VERIFIED | `test_golden_trajectory_bit_identity` RAN (not skipped — this is the Darwin/arm64 capture platform) and passed: exact CSV text + final-loss repr + param sha256 vs the pre-edit fixture. `test_omitted_equals_none_in_process` + `test_zero_penalty_is_inert` passed. Full suite re-run by verifier: **222 passed, 1 skipped** (skip is a pre-existing env gate, not a phase-10 test) |
| 5   | estimate_fisher per-example oracle + provably differs from batched estimate (10-01) | ✓ VERIFIED | Subsumed in SC1; both tests executed and passed |
| 6   | Stored Fisher mean-normalized with raw normalizer in fisher_meta (10-01) | ✓ VERIFIED | `test_mean_normalization`: mean=1 within 1e-5 fp64, `normalizer` recorded in both modes, normalized×normalizer recovers raw. Production cache normalizer = 1.0686e-06 > 0 |
| 7   | EWCPenalty gradient = λ·F·(θ−θ*); RNG purity of estimate_fisher (10-01) | ✓ VERIFIED | `test_gradient_matches_analytic` + `test_rng_purity` (python/numpy/torch global states bit-unchanged) — passed; `fisher.py` uses local `np.random.default_rng`, no `torch.no_grad`, no scipy (grep-verified) |
| 8   | Golden trajectory fixture captured from the UN-edited loop BEFORE any loop.py change and committed (10-02) | ✓ VERIFIED | Git history: fixture commit `94b0e81` precedes loop edit `b1fb37a`; only `b1fb37a` touched loop.py between them; fixture `meta.captured_at_sha=01b8e41…` exists in history, `loop_git_clean: true`, platform block Darwin/arm64/3.11.15/torch 2.7.1 |
| 9   | EWC penalty joins base_loss via assemble_loss BEFORE the /accum divide, exactly one full penalty per optimizer step (10-02) | ✓ VERIFIED | `loop.py:149-151` source order + `test_penalty_once_per_optimizer_step_under_accum` (accum=4×batch=4 vs 1×16 match within 1e-3/1e-6) + `test_penalty_called_once_per_micro_batch` (exactly 6 calls) — passed |
| 10  | checkpoint_extra=None threads additively into all three save_checkpoint sites; default produces v1.0-identical checkpoints (10-02) | ✓ VERIFIED | 3 non-comment `**(checkpoint_extra or {})` splats (loop.py:373, 394, 419); `test_checkpoint_extra_round_trips` executes best.pt AND latest.pt sites and pins fisher-key absence in default run — passed |
| 11  | Fisher cache loads through a single weights_only=True choke point with schema gate + missing-key validation that fail loudly (10-03) | ✓ VERIFIED | `checkpoint.py:279` `torch.load(..., weights_only=True)`, schema gate FIRST (line 280), missing-key ValueError (286), hard fingerprint ValueError (292); no weights_only=False fallback anywhere in load_fisher; no `continual/` import in checkpoint.py (locked dependency direction). Tests 3–7 of `test_fisher_checkpoint.py` passed |
| 12  | Smoke script proves on real weights: finite/non-negative, mean(F)=1, penalty exactly 0.0 at anchor, penalty > 0 under perturbation; refuse-to-rerun (10-03) | ✓ VERIFIED | `scripts/estimate_fisher_tinystories.py`: 10 `raise SystemExit` proof checks, no assert-as-proof, no argparse. Verifier executed the script live: refused rerun with exit code 1 and the "Delete it to re-estimate" message. Cache contents independently re-validated (all finite, ≥0, mean≈1) |

**Score:** 12/12 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `src/personacore/continual/fisher.py` | estimate_fisher → (fisher, fisher_meta), min 80 lines | ✓ VERIFIED | 169 lines; strict batch=1 `torch.autograd.grad` loop, local RNG, fp64-on-CPU stats, fail-loud guards; wired (imported by tests, script, package init) |
| `src/personacore/continual/ewc.py` | EWCPenalty callable, min 40 lines | ✓ VERIFIED | 71 lines; full Kirkpatrick quadratic form with construction/call validation; wired (tests, loop test, script) |
| `src/personacore/continual/__init__.py` | exports estimate_fisher + EWCPenalty | ✓ VERIFIED | `__all__ = ["EWCPenalty", "estimate_fisher"]`; both import in venv |
| `tests/test_fisher.py` | EWC-01 unit pins, min 120 lines | ✓ VERIFIED | 219 lines, 9 tests, all passed in verifier run |
| `tests/test_ewc_penalty.py` | EWC-02 penalty pins, min 60 lines | ✓ VERIFIED | 134 lines, 8 tests incl. `== 0.0` exact-equality anchor, all passed |
| `tests/fixtures/golden_trajectory_v1.json` | contains captured_at_sha | ✓ VERIFIED | Exactly {meta, csv_text, final_loss_repr, param_sha256}; captured_at_sha=01b8e41…; 64-hex sha; 6 CSV rows; platform block present |
| `src/personacore/training/loop.py` | penalty_fn + checkpoint_extra additive kwargs | ✓ VERIFIED | `penalty_fn=None` in both `_optimizer_step` (line 127) and `train` (185) signatures; docstring Args entries present |
| `tests/test_loop_penalty_fn.py` | platform-gated + in-process identity pins, min 100 lines | ✓ VERIFIED | 230 lines, 6 tests; golden replay ran on capture platform and passed bitwise |
| `tests/test_fisher_checkpoint.py` | seam round-trip + cache gate pins, min 80 lines | ✓ VERIFIED | 203 lines, 10 tests, all passed |
| `src/personacore/checkpoint.py` | export_fisher/load_fisher + FISHER_SCHEMA_VERSION | ✓ VERIFIED | `FISHER_SCHEMA_VERSION = 1` (line 33), `export_fisher` (233), `load_fisher` (265) |
| `scripts/estimate_fisher_tinystories.py` | real-weights Fisher run + cache writer, min 80 lines | ✓ VERIFIED | 197 lines; MPS-fallback env before torch import, `preflight_device(strict=True)`, `N_EXAMPLES = 2000`, 10 SystemExit proof checks |
| `checkpoints/fisher_tinystories.pt` | production cache (gitignored) | ✓ VERIFIED | 55,598,597 bytes; loads via `load_fisher` with n_examples=2000; `git status --porcelain checkpoints/` empty |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| fisher.py | model.forward (LOCKED CE tail) | `_, loss = model(x, y)` | ✓ WIRED | fisher.py:116 — model's own CE, no reimplemented reduction |
| fisher.py | per-example gradients | `torch.autograd.grad` | ✓ WIRED | fisher.py:117 inside the batch=1 loop |
| ewc.py | model params by name | `dict(model.named_parameters())` | ✓ WIRED | ewc.py:59 in `__call__` |
| loop.py | penalty_fn callable | `penalty_fn(model)` per micro-batch | ✓ WIRED | loop.py:149, inside `_optimizer_step` autocast block |
| loop.py | loss.py | `assemble_loss(base_loss, penalties)` before /accum | ✓ WIRED | loop.py:150 → `/accum` at 151 |
| loop.py | save_checkpoint **extra seam | `**(checkpoint_extra or {})` ×3 | ✓ WIRED | Lines 373, 394, 419 (best.pt, in-loop latest.pt, end-of-call latest.pt); executed by test, not just grep |
| checkpoint.py | Fisher cache file | `weights_only=True` choke point | ✓ WIRED | checkpoint.py:279; no fallback path |
| script | continual package | `estimate_fisher` + `EWCPenalty` on real best.pt | ✓ WIRED | script lines 105, 149 |
| script | checkpoints/best.pt | trusted `weights_only=False` anchor load + fingerprint read from blob | ✓ WIRED | script line 89; fingerprint read at 177-181, never recomputed |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| fisher_tinystories.pt | fisher tensors / fisher_meta | estimate_fisher at real best.pt over data/train.bin | Yes — normalizer 1.0686e-06, spearman_half 0.9886, rel_mean_change ≈0.002, fingerprint from real anchor | ✓ FLOWING |
| EWCPenalty in training loop | penalties tuple | penalty_fn(model) per micro-batch | Yes — accum-equivalence test uses a real displaced-anchor EWCPenalty with non-zero gradient | ✓ FLOWING |
| Resume checkpoints | fisher/theta_star extras | checkpoint_extra splat | Yes — real tensors round-trip torch.equal through best.pt and latest.pt | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| All 4 phase test files pass | `pytest tests/test_fisher.py tests/test_ewc_penalty.py tests/test_fisher_checkpoint.py tests/test_loop_penalty_fn.py -q` | 33 passed, 0 skipped, 17.8s (golden replay RAN on this platform) | ✓ PASS |
| Full suite green (SC4) | `pytest tests -q` | 222 passed, 1 skipped, 93.5s | ✓ PASS |
| Production cache loads via safe choke point | `load_fisher('checkpoints/fisher_tinystories.pt')` | n_examples=2000, mean=1.0000000269, no theta_star, dedup intact, all finite/≥0 | ✓ PASS |
| Refuse-to-rerun | `python scripts/estimate_fisher_tinystories.py` | Exit code 1, "refusing to overwrite … Delete it to re-estimate" | ✓ PASS |
| Lint | `make lint` | ruff check + format-check clean (96 files) | ✓ PASS |

### Probe Execution

No probes declared in PLAN/SUMMARY files and no `scripts/*/tests/probe-*.sh` convention exists in this project. Behavioral spot-checks above serve as the executed evidence. Status: N/A.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| EWC-01 | 10-01, 10-03 | Per-example empirical diagonal Fisher (not batched-gradient squaring), normalized, stored with anchor θ* via open-dict checkpoint seam | ✓ SATISFIED | Estimation: test_fisher.py 9 pins + real N=2000 run at best.pt. Persistence: test_fisher_checkpoint.py 10 pins + export_fisher/load_fisher choke point. REQUIREMENTS.md checked [x], traceability "Complete" |
| EWC-02 | 10-01, 10-02 | Quadratic penalty plugged in via assemble_loss; exactly 0 at the anchor (unit test) | ✓ SATISFIED | Penalty math: test_ewc_penalty.py 8 pins (== 0.0 exact). Loop splice: test_loop_penalty_fn.py 6 pins incl. golden bitwise replay. REQUIREMENTS.md checked [x], traceability "Complete" |

No orphaned requirements: REQUIREMENTS.md maps exactly EWC-01 and EWC-02 to Phase 10; both are claimed by plan frontmatter.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| scripts/estimate_fisher_tinystories.py | 56 | `EWC_LAMBDA = 1.0  # Phase-10 placeholder convention` | ℹ️ Info | Not a stub: documented convention; the real λ is Phase 12's sweep (EWC-03 per ROADMAP). The constant is only used for the exact-zero/perturbation proof checks, which hold for any λ |

No TBD/FIXME/XXX markers in any phase-modified file. No empty implementations, no hardcoded empty data, no console-log-only handlers. `fisher.py` contains no `np.random.randint`, `torch.no_grad`, or scipy import (acceptance-criteria source assertions hold).

### Human Verification Required

None. All four success criteria are programmatically verifiable and were verified by executed tests and live script runs. No deferred `<human-check>` blocks exist in any phase plan. No visual, real-time, or external-service surface in this phase.

### Gaps Summary

No gaps. All 12 merged must-haves verified against the codebase with executed evidence:

- The from-scratch Fisher implementation is structurally per-example (batch=1 autograd loop) and test-pinned against both a brute-force oracle and an anti-batched discriminator.
- Persistence works end-to-end through both seams (resume `**extra` by value; shareable cache behind a schema-versioned `weights_only=True` choke point), with the tied wte/lm_head storage deduplicated by data_ptr.
- The loop splice is provably additive: the golden bitwise replay ran on the capture platform (Darwin/arm64) during this verification and passed exactly, and the in-process omitted==None==zero-penalty identities carry the guarantee elsewhere.
- The production Fisher cache exists on the main checkout with strong convergence evidence (spearman_half=0.9886 at N=2000).

Minor cosmetic note (no action needed): 10-01 SUMMARY states fisher.py is 170 lines; actual is 169 (a lint reflow).

---

_Verified: 2026-06-12T20:05:00Z_
_Verifier: Claude (gsd-verifier)_
