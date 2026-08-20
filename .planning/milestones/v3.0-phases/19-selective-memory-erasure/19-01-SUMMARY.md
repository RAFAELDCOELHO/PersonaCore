---
phase: 19-selective-memory-erasure
plan: 01
subsystem: testing
tags: [pre-registration, git-ancestry, lora, rank-1-ablation, erasure, stat-05]

requires:
  - phase: 18-black-box-adversarial-extraction-audit
    provides: the ancestry-guard twin pattern (`test_phase18_prereg_is_frozen_before_every_phase18_result`) copied line-for-line, and the one-file pin shape
  - phase: 09-lora-core
    provides: `LoRALinear` (`dW = scale * (B @ A)`), `inject_lora`, `load_adapter_weights`' key/shape/scale audits, `adapter_disabled`
  - phase: 15-visualization-honesty-pass
    provides: `scripts/extract_deltas.py::KEYS` — the committed 36-key (layer, projection, state_dict_key) enumeration
provides:
  - "scripts/phase19_erasure.py — the Phase 19 pre-registration file: ordering contract, MECHANISM_ID, MECHANISM_RULE, component_index(), ablate_components()"
  - "the Phase 19 git-ancestry guard, armed before any results/phase19_* artifact exists"
  - "A5 settled by measurement: rank-1 ablation is exactly representable in the shipped rank-8 artifact format"
affects: [19-02, 19-03, 19-04, 19-05, 19-06, 19-07, 19-09, 19-12]

tech-stack:
  added: []
  patterns:
    - "the pin's component index is DERIVED from two already-committed quantities (len(KEYS) x LoRAConfig().r); 288 is never typed"
    - "the ablation operator takes and returns an export_adapter-shaped ARTIFACT, so every application re-passes load_adapter_weights' scale audit"

key-files:
  created:
    - scripts/phase19_erasure.py
    - tests/test_phase19_erasure.py
  modified:
    - tests/test_phase16_prereg.py

key-decisions:
  - "ablate_components takes and returns the export_adapter-shaped ARTIFACT, not the bare lora_ tensor dict — the scale audit reads artifact['lora_config'], so a tensor-only operator could not be round-tripped through the audit it must survive"
  - "the Phase 19 pin is ONE file (Phase 18's shape), not Phase 17's two — Phase 19 has no ADAPT branch, so there is no sanctioned outcome in which a rule is replaced after a number exists and therefore no legitimate unpinned sibling"
  - "the plan's prescribed deliberate-RED was FALSIFIED by measurement: zeroing only lora_B[:, j] does NOT redden the dW==0 assertion, because scale * outer(0, A[j,:]) is zero whichever factor was cleared; a both-factors test was added because it is what actually bites"

patterns-established:
  - "Arm the ancestry guard in the FIRST plan of a phase, before any artifact exists — every pin commit is watched from the start rather than retro-fitted"
  - "A vacuous-by-construction guard states its vacuity in its own docstring and ties bool(checked) == bool(tracked_artifacts) so the vacuity cannot survive the artifacts' arrival"

requirements-completed: [ERASE-01, STAT-05]

duration: 55min
completed: 2026-08-17
---

# Phase 19 Plan 01: Open The Pin And Prove The Operator — Summary

**The Phase 19 pre-registration file and its git-ancestry guard landed in one commit before any
`results/phase19_*` artifact exists, and A5 — that a rank-1 ΔW component can be zeroed without
leaving the rank-8 artifact format — was settled by running it: 288 addresses ablated, ΔW exactly
zero in all 36 cells, adapter-off bit identity at max abs diff exactly 0.0.**

## Performance

- **Duration:** ~55 min
- **Started:** 2026-08-17T21:24:10Z
- **Completed:** 2026-08-17T22:19:23Z
- **Tasks:** 2 of 2
- **Files modified:** 3 (2 created, 1 modified)

## Accomplishments

- `scripts/phase19_erasure.py` exists and carries the ORDERING CONTRACT verbatim, `MECHANISM_ID`,
  a five-clause `MECHANISM_RULE`, the derived 288-address `component_index()` and
  `ablate_components()`. It holds no floor constant, no target name and no measured number.
- `test_phase19_prereg_is_frozen_before_every_phase19_result` is armed and passing, with all four
  of its Phase 18 twin's protections carried unchanged, and `results/phase19_*` added to
  `V3_ARTIFACT_GLOBS` in the same commit.
- A5 is settled by measurement rather than by argument, including the property the plan's own
  prescribed mutation could not have caught.

## Task Commits

1. **Task 1: Open the pin and arm its ancestry guard in one commit** — `6fd1755` (feat)
2. **Task 2: Prove the ablation operator is exactly representable (A5)** — `a04067a` (test)

## Files Created/Modified

- `scripts/phase19_erasure.py` (created, 254 lines) — the pin. Module docstring states the three-part
  ordering contract; `_prove` raises `SystemExit` in `phase18_extraction._prove`'s register;
  `MECHANISM_ID = "M1-rank1-component-ablation"`; `MECHANISM_RULE` names M1 primary, M2 the ERASE-02
  reference arm and M3–M6 DECLINED-not-deferred, and pins the mechanism's parameters before the
  blind calibration; `component_index()` derives the addresses; `ablate_components()` is the operator.
- `tests/test_phase19_erasure.py` (created, 8 tests) — the CPU-only A5 proofs.
- `tests/test_phase16_prereg.py` (modified) — `results/phase19_*` appended to `V3_ARTIFACT_GLOBS`,
  `PHASE19_PREREG_ARTIFACT` added, and the Phase 19 ancestry twin appended.

## Evidence

### The derived component census — never typed

```
$ .venv/bin/python scripts/phase19_erasure.py
[phase19_erasure] mechanism M1-rank1-component-ablation, 5 rule clauses committed
[phase19_erasure] component index: 36 wrapped projections x rank 8 = 288 addressable rank-1 components
```

Both factors of that product are read, not written: `len(extract_deltas.KEYS) = 36` and
`LoRAConfig().r = 8`. Corroborated against the committed teaching run —
`results/phase14_teaching_run.log:12`: `[teach_persona] injected 36 wrappers, 331776 trainable params`.

### The ancestry guard's state at this commit, raw

```
prereg_commits      = ['6fd1755b788a49d0d5c4e22055b4d9256ed2e9b1']
tracked_artifacts   = []
checked             = 0
product assertion   = 0 == 0
non-vacuity tie     = bool(0) == bool([]) -> True
```

```
$ git log --format=%H -- scripts/phase19_erasure.py | wc -l
       1
$ git ls-files 'results/phase19_*'
(empty)
```

`checked == 0` with `tracked_artifacts == []` is the recorded, correct state: the guard is vacuous
by construction today, and the `bool(checked) == bool(tracked_artifacts)` tie is what stops that
surviving the first artifact.

**Watched RED for free.** Before the Task 1 commit the twin failed on its own
`assert prereg_commits` branch — `scripts/phase19_erasure.py has no commits` — so the
guard-scanning-a-nonexistent-pin branch has been observed biting, not merely written.

### Task 2 — the eight A5 proofs

```
$ .venv/bin/python -m pytest -q tests/test_phase19_erasure.py
........                                                                 [100%]
8 passed in 0.67s
```

### Full-plan verification

```
$ .venv/bin/python -m pytest -q tests/test_phase19_erasure.py tests/test_phase16_prereg.py tests/test_package.py -x
................                                                         [100%]
16 passed in 8.93s

$ .venv/bin/python -m pytest -q
740 passed, 1 skipped, 83 warnings in 147.98s (0:02:27)

$ .venv/bin/python -m ruff check . && .venv/bin/python -m ruff format --check .
All checks passed!
166 files already formatted
```

The single skip is the pre-existing CUDA-only fp16 AMP smoke.

## Deviations from Plan

### 1. [Rule 1 — Falsified premise] The prescribed deliberate-RED does not fire; the test that does was added

- **Found during:** Task 2
- **Plan text:** *"Watch the shape audit RED once by deliberately zeroing only `lora_B[:, j]` and
  leaving `lora_A[j,:]` non-zero, confirm the ΔW==0 assertion fails, then restore byte-identically."*
- **Measured:** the ΔW==0 assertion does **not** fail. The component's contribution is
  `scale · outer(B[:, j], A[j, :])`, so zeroing **either** factor already sends that outer product
  to exactly zero — a half-ablated adapter has `ΔW == 0` just as a fully-ablated one does. Under the
  mutation, the ΔW==0 test, the bit-identity control and the artifact round-trip all stayed **green**.
- **Raw per-test result under the mutation** (`lora_A[j, :]` line replaced by a comment):

```
tests/test_phase19_erasure.py::test_component_index_is_derived_and_addresses_only_wrapped_projections PASSED [ 12%]
tests/test_phase19_erasure.py::test_ablation_leaves_the_artifact_keys_shapes_and_scale_byte_identical PASSED [ 25%]
tests/test_phase19_erasure.py::test_ablation_zeroes_both_factors_and_leaves_every_other_component_alone FAILED [ 37%]
tests/test_phase19_erasure.py::test_ablate_components_does_not_mutate_its_input_adapter FAILED [ 50%]
tests/test_phase19_erasure.py::test_fully_ablated_artifact_round_trips_through_export_and_the_load_audits PASSED [ 62%]
tests/test_phase19_erasure.py::test_full_ablation_zeroes_delta_w_in_every_wrapped_projection PASSED [ 75%]
tests/test_phase19_erasure.py::test_full_ablation_preserves_the_adapter_off_bit_identity_control PASSED [ 87%]
tests/test_phase19_erasure.py::test_ablate_components_refuses_addresses_it_cannot_honour PASSED [100%]
========================= 2 failed, 6 passed in 0.97s ==========================
```

- **Fix:** `test_ablation_zeroes_both_factors_and_leaves_every_other_component_alone` was written
  because it is what actually bites, and its docstring records why the ΔW-based tests cannot. The
  second failure is the all-zeros tail of `test_ablate_components_does_not_mutate_its_input_adapter`.
  Had only the plan's prescribed observation been made, the conclusion would have been "the mutation
  is undetectable" and the operator would have shipped with a contract nothing enforced.
- **Why it matters beyond the test:** it is a fact about the mechanism, not only about the suite.
  `19-06`'s selection sweep ablates one component at a time and re-scores; a half-ablation would
  score identically to a full one, so the sweep would be blind to the difference while
  `lora_A[j, :]` still carried live values that any later write to `B` would resurrect. Zeroing both
  factors makes the component's absence a property of the file.
- **Restoration:** byte-identical. `sha256 9c49247b0a719bc66156139527445adb828effd0d9dc1a93b24680c0ef5fa737`
  before and after; `git diff scripts/phase19_erasure.py` empty against the committed pin.
- **Commit:** `a04067a`

### 2. [Clarification, not a behaviour change] `ablate_components` takes the artifact, not the bare tensor dict

- **Found during:** Task 1
- **Plan text:** *"returning a NEW state dict … leaving every key, shape and `scale` untouched"* —
  the two halves cannot both be true of a bare `lora_` tensor dict, which carries no `scale`.
- **Resolved as:** the operator takes and returns an `export_adapter`-shaped artifact
  (`adapter` / `lora_config` / `base_fingerprint`), whose `["adapter"]` is a new state dict. The
  reason is load-bearing rather than cosmetic: `load_adapter_weights`' scale audit reads
  `artifact["lora_config"]` (`inject.py:119-129`), so a tensor-only operator could not be
  round-tripped through the audit it has to survive, and 19-06's 288-step sweep can now write
  `load_adapter_weights(model, ablate_components(art, [addr]))` — every application re-passing the
  scale audit for free. Recorded here so a later reader does not read the plan's wording as a
  requirement that was dropped.

## Findings For Downstream Plans

1. **`ablate_components(artifact, addresses) -> artifact`.** Addresses are `(layer, projection, j)`.
   It refuses a duplicate address (a duplicate is silently idempotent and would make a reported
   prefix length `k` larger than the number of components actually removed), an out-of-range `j`
   checked against **the artifact's own** `lora_config["r"]`, an unwrapped `(layer, projection)`,
   and a non-artifact input. All four refusals are pinned by test.
2. **`component_index()` is ordered `(layer, projection, j)` with `j` innermost, following the
   committed `KEYS` order.** 19-06's tie-break "break on the `(layer, projection, j)` address" has a
   stable total ordering to address by position.
3. **`N_COMPONENTS` is a module constant computed at import**, so `len(component_index())` and the
   derived cap agree by construction; the derivation proof fires on any import of the pin.
4. **The pin is ONE file.** Every later Phase 19 rule — floor, target, denominator, estimators,
   report text — goes into `scripts/phase19_erasure.py`, and every such commit is watched by the
   armed guard. There is no unpinned sibling by design (see the twin's docstring for why Phase 17's
   split does not apply here).
5. **The toy fixture recipe for CPU-only Phase 19 tests:** `ModelConfig(block_size=32, n_layer=6,
   n_head=2, n_embd=16)` + bare `LoRAConfig()`. `n_layer=6` is mandatory — `extract_deltas.KEYS`
   enumerates `blocks.0..5`, so a shallower toy addresses projections the model does not have.
   `lora_B` starts at **zero** (the identity gate), so any test asserting "the adapter reproduces
   the base" is vacuous unless `lora_B` is nudged and the pre-ablation inequality asserted first.

## Known Stubs

None. Every function this plan added is fully implemented and exercised by a committed test.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema at a trust boundary. The
only file write introduced is `export_adapter` into pytest's `tmp_path` inside a test; the
`weights_only=True` choke points are untouched (T-19-04 accepted, unchanged) and no production
checkpoint is read anywhere in this plan.

## Threat Register Disposition

| Threat ID | Disposition | Status |
|-----------|-------------|--------|
| T-19-01 | mitigate | **Done** — `test_phase19_prereg_is_frozen_before_every_phase19_result` asserts every commit touching the pin is an ancestor of every artifact's earliest `--diff-filter=A` add via `git merge-base --is-ancestor`. No skip path, no force flag. |
| T-19-02 | mitigate | **Done** — the twin asserts `"results/phase19_*" in V3_ARTIFACT_GLOBS` as its first statement, so the test and the tuple cannot drift into naming two different path sets. |
| T-19-03 | mitigate | **Done** — `test_fully_ablated_artifact_round_trips_through_export_and_the_load_audits` runs `export_adapter` → `load_adapter` (`weights_only=True`) → `load_adapter_weights` into a *second, independently injected* model, with the key, shape and scale audits all unrelaxed. |
| T-19-04 | accept | **Unchanged** — no new load site; the toy model is built in-process and no checkpoint is read. |
| T-19-SC | mitigate | **Holds** — zero packages installed; `tests/test_package.py` green (`pyproject.toml` sha256 pin unmoved). |

## Verification Against Plan Success Criteria

- [x] The pin exists, carries the ordering contract, `MECHANISM_ID`, the derived component index and
      `ablate_components`, and holds no floor constant, no target name and no measured number.
- [x] The Phase 19 ancestry twin exists, passes, and is non-vacuously tied to the tracked artifact set.
- [x] A5 is proved: rank-1 ablation is exactly representable and the bit-identity control survives.
- [x] `results/phase19_*` is still empty (`git ls-files 'results/phase19_*'` → no output).

## Self-Check: PASSED

- `scripts/phase19_erasure.py` — FOUND
- `tests/test_phase19_erasure.py` — FOUND
- `tests/test_phase16_prereg.py` — FOUND (modified)
- commit `6fd1755` — FOUND
- commit `a04067a` — FOUND
