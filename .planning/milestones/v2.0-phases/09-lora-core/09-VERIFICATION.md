---
phase: 09-lora-core
verified: 2026-06-11T23:55:00Z
status: passed
score: 13/13 must-haves verified
overrides_applied: 0
re_verification: false
---

# Phase 9: LoRA Core Verification Report

**Phase Goal:** From-scratch LoRA adapters wrap the six named `nn.Linear` projections via post-load injection, with correctness proven by tests and adapter weights shipping as a small swappable artifact
**Verified:** 2026-06-11T23:55:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

Merged set: 5 ROADMAP Success Criteria (the contract) + 8 distinct plan-frontmatter truths that are not restatements.

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | SC1: Adapters injected at init (A-Gaussian/B-zero) leave logits bit-identical to vanilla base; enable/disable round-trip returns exactly to base | ✓ VERIFIED | `layer.py:30` (`torch.zeros` B), `layer.py:31` (`normal_ std=0.02` A); `test_injection_preserves_logits_bit_identical` + `test_toggle_round_trip_bit_identity` (both `torch.equal`); both pass in run executed by verifier |
| 2 | SC2: After adapter training only A/B changed — every base param bit-untouched; tied embedding never wrapped (`data_ptr` post-injection) | ✓ VERIFIED | `test_canary_and_frozen_base_bit_untouched` (frozen → `torch.equal`, trainable → `not torch.equal` through untouched v1.0 `train()`); `test_tied_tensor_never_wrapped` asserts `lm_head.weight.data_ptr() == wte.weight.data_ptr()` post-injection; both pass |
| 3 | SC3: Adapter weights save/load as separate small artifact compatible with open-dict checkpoints and the LOCKED `weights_only=True` slim contract | ✓ VERIFIED | `checkpoint.py:165-219` (`export_adapter`/`load_adapter`, `ADAPTER_SCHEMA_VERSION`); verifier loaded the REAL `checkpoints/adapter.pt` (1.35 MB) through `load_adapter` in its own process: exact 4-key set, 72 `lora_`-only tensors, real fingerprint (sha/step=49000/val_loss); `test_two_artifact_load_reproduces_logits` (D-03, `torch.equal`); `test_lora_config_rides_checkpoint_extra` (open-dict `**extra` seam) |
| 4 | SC4: `merge()`/unmerge passes fp32-tolerance equivalence (merged ≡ base+adapter); demo path stays unmerged | ✓ VERIFIED | `test_merged_forward_matches_live` (`atol=1e-5`), `test_unmerge_bit_exact` (`torch.equal` stored-clone restore), `test_merge_refuses_in_training_mode`; nothing in the codebase merges by default (`merged=False` at construction; merged-slim export deliberately not wired) |
| 5 | SC5: Param-count formula + load→inject→freeze ordering pinned by unit tests; params-actually-update canary passes on smoke run | ✓ VERIFIED | `test_trainable_census_formula` (`r * n_layer * 18 * n_embd`); `test_injection_preserves_logits_bit_identical` (ordering pin); smoke run evidence: `checkpoints/adapter.pt` exported (export only reachable after the script's inline canary asserts at `train_adapter_smoke.py:139-147`), all 72 tensors nonzero — training provably moved B off its zero init; gitignored confirmed |
| 6 | `inject_lora` wraps exactly `6 * n_layer` projections; `lm_head`/`wte` never `LoRALinear` | ✓ VERIFIED | `inject.py:29-43` explicit `cfg.targets` allowlist (no isinstance scan; `lm_head` appears nowhere in inject.py); `test_wrap_count_and_targets`, `test_allowlist_cross_pin` pass |
| 7 | `adapter_disabled` is exception-safe and preserves per-module prior state | ✓ VERIFIED | `inject.py:106-122` (`@contextlib.contextmanager`, prior-dict capture, `finally:` restore); `test_adapter_disabled_exception_safe` + `test_adapter_disabled_preserves_prior_state` pass |
| 8 | `eject_adapter` restores plain `nn.Linear` everywhere: vanilla key set + `torch.equal`-to-base logits; refuses while merged | ✓ VERIFIED | `inject.py:125-146` (assert not merged, `setattr(parent, name, child.base)`); `test_eject_restores_vanilla_model` (key parity vs `GPT(cfg).state_dict()`), `test_eject_refuses_while_merged`, `test_eject_after_unmerge_interplay` pass |
| 9 | `merged_state_dict` mutates nothing, vanilla key parity, fresh GPT `strict=True` reload reproduces live logits within 1e-5 | ✓ VERIFIED | `inject.py:172-201` pure fold with detached clones + double-merge guard; `test_merged_state_dict_purity_and_parity` + `test_w0_hygiene` pass |
| 10 | `load_adapter` raises `ValueError` on wrong schema_version naming actual + expected; fingerprint mismatch warns-but-loads (D-02), match is silent | ✓ VERIFIED | `checkpoint.py:205-218`; `test_schema_version_mismatch_raises`, `test_fingerprint_mismatch_warns_but_loads`, `test_matching_fingerprint_is_silent` pass |
| 11 | No base weight ever appears in the adapter dict — every adapter key contains `lora_` | ✓ VERIFIED | `lora_state_dict` filter (`inject.py:67-73`); `test_no_base_weight_leak` + verifier's direct inspection of the real adapter.pt (72/72 keys contain `lora_`, none contain `.base.`) |
| 12 | Optimizer state holds entries only for stepped A/B params; kill+resume reproduces uninterrupted trajectory within 1e-6 | ✓ VERIFIED | `test_optimizer_state_scoped_to_lora_params` (`12 * n_layer` census), `test_adapter_kill_resume_identical_trajectory` (loss + `lora_B` within 1e-6 via deterministic vanilla→inject→freeze rebuild); both pass |
| 13 | Key-audited adapter apply: corrupted dict (key removed/renamed) raises `ValueError` before any weight loads | ✓ VERIFIED | `inject.py:76-91` exact key-set audit before `strict=False`; `test_load_adapter_weights_raises_before_loading` asserts model tensors bit-unchanged after failed audit; passes |

**Score:** 13/13 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `src/personacore/lora/config.py` | LoRAConfig + TARGET_PROJECTIONS | ✓ VERIFIED | 26 lines; contains `TARGET_PROJECTIONS` tuple + dataclass with r=8/alpha=16.0/dropout=0.0; imported across lora/ + 6 test files |
| `src/personacore/lora/layer.py` | LoRALinear wrapper + merge/unmerge | ✓ VERIFIED | 68 lines; `class LoRALinear`, `def merge`, `def unmerge`; `alpha / r` exactly once (grep count 1); no `register_buffer` |
| `src/personacore/lora/inject.py` | 11 injection/toggle/merge functions | ✓ VERIFIED | 201 lines; all five 09-01 + six 09-02 functions present; never imports checkpoint.py |
| `src/personacore/lora/__init__.py` | Public import surface | ✓ VERIFIED | 14-name `__all__`; full surface imports clean in `.venv` (verified in verifier's own process) |
| `src/personacore/checkpoint.py` | ADAPTER_SCHEMA_VERSION + export/load_adapter (additive) | ✓ VERIFIED | Choke-point grep count exactly 2 (load_slim + load_adapter); existing slim/checkpoint tests still green; never imports lora/ |
| `tests/test_lora_layer.py` | LORA-01 layer pins (min 60 lines) | ✓ VERIFIED | 119 lines, 8 tests, all pass |
| `tests/test_lora_inject.py` | Injection pins (min 80 lines) | ✓ VERIFIED | 178 lines, 9 tests, all pass |
| `tests/test_lora_toggle.py` | LORA-05 toggle pins (min 60 lines) | ✓ VERIFIED | 143 lines, 6 tests, all pass |
| `tests/test_lora_merge.py` | LORA-04 pins (min 70 lines) | ✓ VERIFIED | 171 lines, 7 tests, all pass |
| `tests/test_lora_artifact.py` | LORA-03 pins (min 90 lines) | ✓ VERIFIED | 249 lines, 9 tests (incl. real-13.9M skipif variant), all pass |
| `tests/test_lora_training.py` | LORA-02 pins (min 80 lines) | ✓ VERIFIED | 198 lines, 4 tests, all pass; `loop.py` byte-untouched across the phase (empty `git log` for training/ paths) |
| `scripts/train_adapter_smoke.py` | Real-weights smoke (contains `WEIGHT_DECAY = 0.0`) | ✓ VERIFIED | 168 lines; MPS env guard before torch import; produced `checkpoints/adapter.pt` (1,349,323 bytes ≈ 1.35 MB, within the 1.0–1.7 MB acceptance band), gitignored |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| `lora/inject.py` | `lora/layer.py` | `from .layer import LoRALinear` | ✓ WIRED | inject.py:26 |
| `lora/layer.py` | forward delta gating | `self.enabled and not self.merged` | ✓ WIRED | layer.py:40 |
| `tests/test_lora_inject.py` | seam-test allowlist | `TARGET_PROJECTIONS` cross-pin | ✓ WIRED | `test_allowlist_cross_pin` restates + asserts equality |
| `lora/layer.py` | merge delta | `self.scale * (self.lora_B @ self.lora_A)` | ✓ WIRED | layer.py:55 (single scale source, P3) |
| `lora/inject.py` | exception-safe re-enable | `finally:` in contextmanager | ✓ WIRED | inject.py:120 |
| `lora/inject.py` | training-mode merge guard | `model.training is False` | ✓ WIRED | inject.py:156 |
| `checkpoint.py` | safe-load bar (D-01) | `weights_only=True` choke point | ✓ WIRED | checkpoint.py:204; verbatim call expression count == 2 |
| `checkpoint.py` | D-02 warn-but-load | `warnings.warn` | ✓ WIRED | checkpoint.py:212 |
| `tests/test_lora_artifact.py` | `lora/inject.py` | `load_adapter_weights` key-audited apply | ✓ WIRED | artifact test lines 215, 243 |
| `scripts/train_adapter_smoke.py` | `training/loop.py` | keyword-only `train(` call, loop untouched | ✓ WIRED | smoke:118; git log shows zero loop.py edits in phase range |
| `scripts/train_adapter_smoke.py` | `checkpoint.py` | `export_adapter` with fingerprint from best.pt | ✓ WIRED | smoke:151-160; real artifact carries sha `3a46815…`/step 49000 read from best.pt |
| `tests/test_lora_training.py` | `lora/inject.py` | `snapshot_params` canary helper | ✓ WIRED | training test:91 |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `checkpoints/adapter.pt` | `adapter` dict (72 tensors) | `lora_state_dict(model)` after 50 real training steps on best.pt + TinyStories bins | Yes — verifier inspected: 72/72 tensors nonzero (all `lora_B` moved off zero init, which only training can do; no nudge call exists in the smoke script) | ✓ FLOWING |
| `load_adapter` consumers | `art["adapter"]`, `art["lora_config"]`, `art["base_fingerprint"]` | restricted unpickler load of the file | Yes — config reconstructs `LoRAConfig(r=8, alpha=16.0)`, fingerprint carries real provenance trio | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| All 43 phase tests pass | `.venv/bin/python -m pytest tests/test_lora_*.py -q` | 43 passed in 1.53s | ✓ PASS |
| Full suite regression | `.venv/bin/python -m pytest -q` | 180 passed, 1 skipped (matches SUMMARY claims) | ✓ PASS |
| Full lora + checkpoint import surface | `.venv/bin/python -c "from personacore.lora import …(14 names); from personacore.checkpoint import ADAPTER_SCHEMA_VERSION, export_adapter, load_adapter"` | imports clean | ✓ PASS |
| Real adapter.pt loads via choke point | `load_adapter('checkpoints/adapter.pt')` in verifier's process | exact 4-key set, 72 lora_ tensors, 1.35 MB | ✓ PASS |
| Lint | `.venv/bin/ruff check .` + `ruff format --check .` | All checks passed; 88 files formatted | ✓ PASS |
| All 13 claimed task commits exist | `git cat-file -t` on e0ec561…141b81e | all 13 resolve to commits | ✓ PASS |

Note: bare `make test` fails in a shell without the venv activated (PATH pytest resolves to pyenv 3.12 without torch) — a known environment artifact documented in project memory, not a code regression; the venv-invoked suite is fully green.

### Probe Execution

| Probe | Command | Result | Status |
| ----- | ------- | ------ | ------ |
| (none) | `find scripts -name 'probe-*.sh'` | no probe convention in this project; verification ran via pytest directly | N/A |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| LORA-01 | 09-01 | From-scratch LoRALinear (A-Gaussian/B-zero, α/r, configurable r/alpha/dropout) wraps six named projections via post-load injection, no HF PEFT | ✓ SATISFIED | layer.py + inject.py from scratch (zero new deps); truths 1, 6 |
| LORA-02 | 09-01, 09-04 | Frozen-base training: gradients only to A/B; base bit-untouched (test-verified) | ✓ SATISFIED | truths 2, 12; canary on tiny fixture + real-weights smoke evidence |
| LORA-03 | 09-03 | Adapter as separate small artifact, open-dict + `weights_only=True` compatible | ✓ SATISFIED | truths 3, 10, 11; real 1.35 MB artifact verified |
| LORA-04 | 09-02 | merge()/unmerge with fp32-tolerance equivalence; demo path stays unmerged | ✓ SATISFIED | truths 4, 9 |
| LORA-05 | 09-01, 09-02, 09-04 | Unit pins: zero-delta at init, round-trip bit-identity, param-count formula, tied-embedding data_ptr | ✓ SATISFIED | truths 1, 2, 5, 6 |

No orphaned requirements: REQUIREMENTS.md maps exactly LORA-01..05 to Phase 9, and all five are claimed across the four plans.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none) | — | grep for TBD/FIXME/XXX/TODO/HACK/placeholder across all 12 phase files: zero matches | — | — |

### Advisory Findings (from 09-REVIEW.md, assessed against the phase goal)

These were weighed against the success criteria as written; none falsifies a must-have truth, so none blocks the phase. They should be addressed before Phase 14 consumes these APIs.

| Finding | Goal Impact | Disposition |
| ------- | ----------- | ----------- |
| CR-01: `enabled` toggle × `merged` state mutually blind (toggle on merged model is a silent no-op; merging a disabled adapter folds it in) | SC1's round-trip is verified for the unmerged state, and SC4 locks "demo path stays unmerged" — the failure mode requires combining merge (an eval-only side utility) with the toggle path, which nothing in the codebase does | ⚠️ Warning — guard toggle×merge before Phase 14's live demo |
| CR-02: `load_adapter_weights` audit covers key sets but not shapes; a crafted same-keys/wrong-shape artifact partially mutates before raising | The pinned truth ("corrupted dict — key removed/renamed — raises before any weight loads") is verified exactly as worded; shape hardening is beyond the pinned contract | ⚠️ Warning — add shape/dtype audit before accepting foreign persona files |
| WR-01: smoke script's documented resume path not wired (`resume_from`/`checkpoint_interval` absent) | SUMMARY 09-04 explicitly documents this as a per-plan-spec decision; the smoke completed, so SC5 is met | ℹ️ Info |
| WR-03: corruption guards are `assert`s, stripped under `python -O` | All guards verified active under normal venv execution (tests pin them) | ℹ️ Info |

### Human Verification Required

None. This is a library/test phase with no UI, external services, or real-time behavior; every success criterion is programmatically pinned, and the verifier independently executed the test suite, loaded the real artifact, and confirmed the git history. No `<human-check>` blocks exist in any of the four plans.

### Gaps Summary

No gaps. The phase goal is achieved end-to-end and observable in the codebase:

- The from-scratch `LoRALinear` wraps exactly the six allowlisted projections via post-load injection, with the B=0 identity gate, tied-embedding safety, and the closed-form census all bit-level test-pinned (43 tests, run by the verifier, all green; full 180-test suite green — no regression).
- Correctness covers init identity, enable/disable exact round-trip, exception-safe scoped disable, full eject, fp32-tolerance merge with bit-exact unmerge, frozen-base training through the byte-untouched v1.0 `train()`, optimizer-state scope, and 1e-6 kill+resume.
- The adapter ships as a real, small, swappable artifact: `checkpoints/adapter.pt` (1.35 MB, gitignored) produced by a real 50-step run on the 13.9M `best.pt`, loads through the single `weights_only=True` choke point with exact key set, contains only trained (all-nonzero) `lora_` tensors, and carries the base provenance fingerprint. The D-03 two-artifact load reproduces exporter logits bit-identically.

---

_Verified: 2026-06-11T23:55:00Z_
_Verifier: Claude (gsd-verifier)_
