---
phase: 01-scaffolding-reproducible-environment
plan: 03
subsystem: infra
tags: [makefile, github-actions, ci, ruff, pytest, kaggle, documentation]

# Dependency graph
requires:
  - phase: 01-01
    provides: pyproject.toml with [cpu]/[dev] extras and [tool.ruff] config (the tooling this plan drives)
  - phase: 01-02
    provides: checkpoint/seeding/provenance modules referenced in the reproducibility docs
provides:
  - Makefile with install/test/lint/format targets (D-12)
  - CPU-only GitHub Actions CI pinned to Python 3.11 (ruff + pytest, no GPU, no training)
  - ENV-06 CLAUDE.md section documenting structure + Kaggle-train / laptop-CPU-infer workflow
affects: [all-future-phases, kaggle-training, ci-gate]

# Tech tracking
tech-stack:
  added: [GitHub Actions CI, GNU Make]
  patterns:
    - "CI pins Kaggle-target Python 3.11 (never the local 3.14 dev box) for true install-parity"
    - "Makefile install routes torch through the CPU wheel index; never used on Kaggle"
    - "ENV-06 docs appended OUTSIDE GSD marker blocks so GSD-managed regions are preserved"

key-files:
  created: [Makefile, .github/workflows/ci.yml]
  modified: [CLAUDE.md]

key-decisions:
  - "CI pins python-version 3.11 (Kaggle parity), not the local 3.14 box (D-12 + research Environment Availability flag)"
  - "Used actions/checkout@v4 + actions/setup-python@v5 (current major tags) as flagged for verification in research"
  - "ENV-06 content appended after <!-- GSD:profile-end --> to keep all GSD marker regions intact"

patterns-established:
  - "Pattern: dev-tooling layer (Makefile + CI) consumes the package contract from 01-01 with zero pyproject edits"
  - "Pattern: CI is CPU-only — no GPU runner, no training step, torch only via the CPU index"

requirements-completed: [ENV-06, ENV-01, ENV-02]

# Metrics
duration: 4min
completed: 2026-06-04
---

# Phase 1 Plan 03: Dev Tooling & Reproducibility Docs Summary

**Makefile (install/test/lint/format) + a CPU-only GitHub Actions CI pinned to Python 3.11 (ruff + pytest, no GPU/training) + an ENV-06 CLAUDE.md section documenting structure and the Kaggle-train / laptop-CPU-infer workflow.**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-06-04T18:17:48Z
- **Completed:** 2026-06-04T18:18:31Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- `Makefile` drives `install` (CPU torch index), `test` (`pytest -q`), `lint` (`ruff check . && ruff format --check .`), and `format` (auto-fix).
- `.github/workflows/ci.yml` pins `python-version: "3.11"` (Kaggle parity), installs `.[cpu,dev]` via the CPU torch index, and runs ruff + pytest — no GPU runner, no training step. This is the automated install-parity gate that re-validates ENV-01/ENV-02 on a fresh runner.
- `CLAUDE.md` gained an ENV-06 section: Phase-1 structure (no stub dirs, D-11), the mandatory 3.11-venv local workflow, the Kaggle `git clone` + `pip install -e .` workflow with the never-`pip install torch` rule (D-10), both Kaggle run modes (headless commit vs interactive, D-08), the SHA-record + pin option (D-06), and the seed+SHA+config reproducibility discipline — all appended outside the GSD marker blocks.

## Task Commits

Each task was committed atomically:

1. **Task 1: Makefile + CPU-only GitHub Actions CI (Python 3.11)** - `c6607fc` (feat)
2. **Task 2: Extend CLAUDE.md — structure + Kaggle/local workflow (ENV-06)** - `5e851f7` (docs)

**Plan metadata:** committed separately with SUMMARY.md + STATE.md + ROADMAP.md + REQUIREMENTS.md.

## Files Created/Modified
- `Makefile` - install/test/lint/format targets; install routes torch through the CPU wheel index.
- `.github/workflows/ci.yml` - CPU-only CI: checkout@v4 → setup-python@v5 (3.11) → install .[cpu,dev] → ruff → pytest.
- `CLAUDE.md` - appended ENV-06 section (structure + Kaggle/local workflow + 3.11 mandate + no-torch-on-Kaggle rule); GSD marker blocks preserved.

## Decisions Made
- CI pins **Python 3.11**, not the local 3.14 dev box, so install-parity is validated against the real Kaggle target (research Environment Availability flag).
- Used `actions/checkout@v4` and `actions/setup-python@v5` — current major tags (flagged `[ASSUMED]` in research, confirmed current).
- ENV-06 content appended after `<!-- GSD:profile-end -->`, fully outside every GSD-managed region.

## Deviations from Plan

None - plan executed exactly as written.

(Note on verification mechanics: the Task 1 `<verify>` block used `python -c "import yaml; ..."` to assert the CI 3.11 pin, but PyYAML is not installed in `/tmp/pc-venv`. Per the Rule 3 package-manager exclusion, no package was installed; the same assertion — `python-version: "3.11"`, `[cpu,dev]` extras, ruff+pytest present, no GPU/CUDA — was performed with a stdlib-only regex check, which passed. This is a verification-tooling substitution, not a change to the artifact or plan.)

## Issues Encountered
None. Lint clean, format clean, full `pytest -q` green (20 passed). No file deletions. `pyproject.toml` is NOT in this plan's diff (owned by 01-01).

## User Setup Required
None - no external service configuration required. (After push, confirm the GitHub Actions run is green on a fresh 3.11 runner — this re-validates ENV-01/ENV-02 install-parity.)

## Next Phase Readiness
- Phase 1 dev-tooling + reproducibility-docs layer complete. Makefile and CI gate are in place for all future phases.
- CI green-on-push is the phase gate before `/gsd:verify-work`; verify the first Actions run after the next push.
- No blockers.

## Self-Check: PASSED

- FOUND: Makefile
- FOUND: .github/workflows/ci.yml
- FOUND: CLAUDE.md
- FOUND: .planning/phases/01-scaffolding-reproducible-environment/01-03-SUMMARY.md
- FOUND: commit c6607fc (Task 1)
- FOUND: commit 5e851f7 (Task 2)
- FOUND: GSD:project-start marker intact

---
*Phase: 01-scaffolding-reproducible-environment*
*Completed: 2026-06-04*
