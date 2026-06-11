---
phase: 09-lora-core
plan: 03
subsystem: checkpointing
tags: [pytorch, lora, adapters, weights-only, safe-load, persona-file]

# Dependency graph
requires:
  - phase: 09-lora-core (plan 01)
    provides: inject_lora / lora_state_dict / load_adapter_weights (the key-audited adapter seam) + LoRAConfig
  - phase: 08-slim-checkpoint
    provides: export_slim / load_slim safe-load template and the weights_only=True locked contract
provides:
  - ADAPTER_SCHEMA_VERSION + export_adapter/load_adapter in checkpoint.py (the persona-file artifact I/O)
  - weights_only=True single choke point for every adapter consumer (D-01, T-09-07)
  - D-02 base-fingerprint warn-but-load semantics (UserWarning naming both fingerprints)
  - D-03 two-artifact load proof: load_slim + load_adapter + inject + key-audited apply == exporter logits, bit-identical
  - 9 CPU-only artifact tests incl. a skipif-gated real-13.9M-base variant
affects: [09-04 training smoke (export_adapter tail), phase-14 persona adapter loads, phase-15 delta-w]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Adapter artifact I/O lives in checkpoint.py beside slim I/O; checkpoint.py takes plain dicts and never imports lora/ (locked dependency direction)"
    - "Safe-load choke point: torch.load(path, map_location=map_location, weights_only=True) at exactly one function per artifact type"
    - "Schema-version ValueError names actual value, expected value, and the re-export remedy"
    - "Fingerprint mismatch is a UserWarning naming BOTH fingerprints, never a hard error (D-02)"

key-files:
  created:
    - tests/test_lora_artifact.py
  modified:
    - src/personacore/checkpoint.py

key-decisions:
  - "Copied the gitignored real checkpoints/model_slim.pt into the worktree so the skipif-gated real-artifact test actually ran locally (it would otherwise skip; the file stays untracked/ignored)"
  - "Task 2 is a test-only integration pin over Task 1's implementation — its tests pass on first run by design (no new src code), so no conventional RED stage exists for it"

patterns-established:
  - "ADAPTER_KEYS exact key-set constant in the test module mirrors SLIM_KEYS (T-08-03 lineage)"
  - "The raw weights_only=True load succeeding IS the safe-load assertion (T-09-07, house idiom)"

requirements-completed: [LORA-03]

# Metrics
duration: 12min
completed: 2026-06-11
---

# Phase 9 Plan 03: Adapter Persona-File Artifact Summary

**export_adapter/load_adapter persona-file choke point under the locked weights_only=True bar, with schema-version raise, D-02 fingerprint warn-but-load, and a bit-identical two-artifact (slim + adapter) load proof**

## Performance

- **Duration:** 12 min
- **Started:** 2026-06-11T21:57:05Z
- **Completed:** 2026-06-11T22:09:43Z
- **Tasks:** 2 (Task 1 TDD RED→GREEN; Task 2 test-only pin)
- **Files modified:** 1 created, 1 modified

## Accomplishments

- `adapter.pt` — the swappable/shareable/deletable persona file — round-trips `torch.load(weights_only=True)` through the single `load_adapter` choke point with the exact key set `{schema_version, adapter, lora_config, base_fingerprint}` (D-01, T-09-07)
- `load_adapter` raises `ValueError` naming actual/expected schema version and the re-export remedy (verbatim `load_slim` discipline, T-09-08)
- Base-fingerprint mismatch emits a `UserWarning` naming BOTH fingerprints but still loads (D-02 locked: base evolves mid-milestone); a matching fingerprint is silent
- Two-artifact load (`load_slim` + `load_adapter` + `inject_lora` + key-audited `load_adapter_weights`) on fresh objects reproduces the exporting model's logits bit-identically (`torch.equal`) — the literal D-03 slim-contract compatibility, no merged-slim export anywhere
- No base weight ever enters the artifact: every adapter key contains `lora_`, none contains `.base.`, tensor census is `2 * 6 * n_layer` (T-09-10)
- The real-base variant ran locally (not skipped): real 13.9M `model_slim.pt` → inject (`6 * n_layer` wraps) → export/load through a tmp adapter → forward shape sanity on CPU
- checkpoint.py change is purely additive: `save_checkpoint`/`load_checkpoint`/`export_slim`/`load_slim` byte-untouched; full suite 176 passed, lint clean

## Task Commits

Each task was committed atomically:

1. **Task 1: export_adapter/load_adapter choke point + artifact contract tests**
   - `d54b9e1` (test) — 7 failing tests: exact key set, no-leak census, schema raise, warn-but-load, silent match, return-dict + config round-trip, provenance trio
   - `7569b20` (feat) — `ADAPTER_SCHEMA_VERSION`, `export_adapter`, `load_adapter`, `import warnings`
2. **Task 2: Two-artifact load end-to-end (D-03) + real-slim skipif variant** - `db3be39` (test)

_No refactor commits — implementations landed clean against the RESEARCH-verified reference._

## Files Created/Modified

- `src/personacore/checkpoint.py` — +1 constant (`ADAPTER_SCHEMA_VERSION`), +2 functions (`export_adapter`/`load_adapter`) mirroring the slim pair verbatim in style; never imports `lora/`
- `tests/test_lora_artifact.py` — 9 CPU-only LORA-03 pins (249 lines): weights_only round-trip, no-leak, schema raise, D-02 warn/silent, config + provenance round-trips, D-03 two-artifact bit-identity, real-base skipif variant

## Decisions Made

- Copied the gitignored real `checkpoints/model_slim.pt` (55.6 MB) from the main checkout into the worktree so the skipif-gated real-artifact test exercised the full flow locally instead of skipping — the file is gitignored and untracked, so nothing leaks into the repo
- Treated Task 2 as a test-only pin: its tests exercise the composition of Task 1's already-shipped functions with 09-01's injection seam, so they pass on first run by design (documented under TDD Gate Compliance)

## Deviations from Plan

None - plan executed exactly as written.

## TDD Gate Compliance

- RED gate: `d54b9e1` (test commit; verified failing with `ImportError: cannot import name 'export_adapter'` before implementation)
- GREEN gate: `7569b20` (feat commit; 7/7 green)
- Task 2 (`db3be39`) is a test-only task adding integration pins over the Task 1 implementation — no implementation step exists, so its tests passing immediately is the expected behavior, not a skipped RED: the feature deliberately already existed (Task 1 GREEN) and the new tests pin its composition with the 09-01 seam.

## Issues Encountered

- One ruff E501 (105 > 100 chars) on the `ADAPTER_SCHEMA_VERSION` inline comment during Task 1 — shortened before commit, not a deviation.
- Pre-existing, unrelated `UserWarning` in `tests/test_tokenizer_io.py` (corpus-exhaustion warning) is the full suite's single warning; out of scope (pre-dates this plan).

## Known Stubs

None — no placeholder values, TODO/FIXME markers, or unwired data paths in either file.

## Threat Model Compliance

| Threat | Disposition | Implemented |
|--------|-------------|-------------|
| T-09-07 (EoP via deserialization) | mitigate | `weights_only=True` single choke point; raw safe-load success IS a test assertion (test_artifact_safe_loads_with_exact_keys) |
| T-09-08 (schema/key smuggling) | mitigate | schema_version ValueError before any consumption (test_schema_version_mismatch_raises); downstream apply via 09-01's exact key-set audit (test_two_artifact_load_reproduces_logits) |
| T-09-09 (adapter on wrong base) | mitigate | D-02 fingerprint comparison, UserWarning names both fingerprints (test_fingerprint_mismatch_warns_but_loads / test_matching_fingerprint_is_silent) |
| T-09-10 (base-weight disclosure) | mitigate | lora_-only keys + no-`.base.` + 2*6*n_layer census (test_no_base_weight_leak) |
| T-09-SC (supply chain) | accept | zero packages installed |

No new security surface introduced beyond the plan's threat model.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `export_adapter`/`load_adapter` ready for 09-04's smoke-script tail (export the trained adapter, print the ~1.3 MB persona-file size)
- The two-artifact load flow is the exact pattern Phase 14 uses to load user-taught persona adapters
- No blockers

## Self-Check: PASSED

- Both key files exist on disk (`src/personacore/checkpoint.py`, `tests/test_lora_artifact.py` — 249 lines, min 90 satisfied)
- All 3 task commits present in git log (d54b9e1, 7569b20, db3be39)
- Plan verification re-run: 9/9 artifact tests green, `make test` 176 passed / 1 skipped, `make lint` clean, `from personacore.checkpoint import ADAPTER_SCHEMA_VERSION, export_adapter, load_adapter` imports in `.venv`, choke-point grep count == 2

---
*Phase: 09-lora-core*
*Completed: 2026-06-11*
