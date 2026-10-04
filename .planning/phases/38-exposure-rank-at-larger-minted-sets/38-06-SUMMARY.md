---
phase: 38-exposure-rank-at-larger-minted-sets
plan: 06
subsystem: e5-driver
tags: [rank-02, rank-03, e5, ledger, gate, sidecars, cpu-rehearsal]
requires: [results/phase38_minting.json (7357577), scripts/phase38_prereg.py, scripts/phase38_sizes_prereg.py, scripts/phase36_ledger.py, scripts/phase36_probe.py]
provides: [scripts/phase38_rank.py part 1 (preflight, run), tests/test_phase38_rank.py part 1]
affects: [38-07 (crosscheck/emit/report/CLI build on run's sidecars), 38-08 (the real MPS run)]
tech-stack:
  added: []
  patterns: [phase37_r1b driver template, write-once per-reading sidecars, fake-model rig, AST instrument gate]
key-files:
  created: [scripts/phase38_rank.py, tests/test_phase38_rank.py]
  modified: []
key-decisions:
  - "phase38_sizes_prereg is imported lazily (inside scoring_plan/preflight), not at module level as the plan's action text says, because importing it loads torch (38-05). This keeps the plan's own acceptance line `v6/38/E5/rank E5 False` true."
  - "Any root inside the repository counts as the real root (full shape, MPS only). Only a root outside the repo is a rehearsal root."
requirements-completed: []  # the orchestrator owns the RANK-02/RANK-03 ticks at phase close
duration: ~40 min
completed: 2026-10-04
---

# Phase 38 Plan 06: E5 rank driver part 1 (preflight + run) Summary

`scripts/phase38_rank.py` now has everything up to and including the MPS run under the ledger. Every
refusal comes before the start line. Preflight proves the three D-20 digests. The D-18 gate checks
all 64 committed ranks before any minted value is scored. Then one scoring pass covers each maximum
set under the eight readings, writing a write-once NLL sidecar per reading. Nothing ran on MPS and
nothing was written to the real ledger/, results/ or data/.

## Commits

| Task | Commit | What |
|------|--------|------|
| 1 | d379fd1 | feat: constants, sidecars, run_inputs, adapter_digests, reconstruction_checks, scoring_plan, reading_model, score_values, gate_reading, preflight + 43 tests |
| 2 | a5d5ae8 | feat: run() + the run/GATE_FAILED/partial-shape/head-moved/crash tests, the RANK-03 AST gate, the no-skips and every-function censuses (56 tests) |

## RED outputs

- Task 1, before the module existed: `1 error in 0.95s` (`ModuleNotFoundError: No module named 'phase38_rank'`).
- Task 2, before `run()` existed: `8 failed, 48 passed in 6.33s`. The failures were the 7 run tests
  plus `test_no_in_run_stop_rule_and_no_ruling_writes` (no `phase36_ledger.append` call yet). The
  RANK-03 gate was green against the existing code and reds only on its planted copies.
- First GREEN attempt for Task 2: 2 failures. `atomic_write_json` sorts keys, so the order-based
  assertions on `rows` and `slots` became set comparisons. `_write_once` also had no test yet, so the
  every-function census caught it and a test was added.

## Verify (real output, after both commits)

- `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase38_rank.py tests/test_phase38_prereg.py tests/test_phase21_sc5.py tests/test_lora_inject.py tests/test_phase36_ledger.py` → `171 passed in 24.01s`
- `tests/test_phase21_sc5.py::test_instruments_unchanged_byte_for_byte tests/test_phase35_prereg.py tests/test_phase38_sizes_prereg.py` → `99 passed in 27.24s`
- `tests/test_phase25_driver.py` (after the commit) → `24 passed in 1.71s`. Before the Task 2 commit it
  had 1 expected red: the clean-tree probe `test_the_git_surface_gate_fires_on_a_planted_push` saw
  ` M scripts/phase38_rank.py`.
- `ruff check .` → `All checks passed!`; `ruff format --check .` → `354 files already formatted`
- `.venv/bin/python -c "import sys; sys.path[:0]=['scripts','src']; import phase38_rank as r; print(r.RUN_ID, r.FRONT, 'torch' in sys.modules)"` → `v6/38/E5/rank E5 False`
- `git status --porcelain -- scripts tests results ledger` → empty. `find results -maxdepth 1 -name 'phase38_rank*'` → nothing; `find data -maxdepth 1 -name 'phase38_rank_*'` → nothing.
- `tests/test_lora_inject.py` passes with no new register line (the driver has no `inject_lora` and no `LoRAConfig`).
- `== 10` / `train_arm(` / `train_never_taught` / `LoRAConfig` grep over both new files: no hits.

## Fake-run rehearsal (tmp root, tmp ledger, real digests)

`/private/tmp/claude-501/p38_06_rehearsal/rehearse.py` ran `run()` at the full shape, device `cpu`,
on a tmp root. `reading_model` and `value_span_nll_mean` were the test rig's fakes. Everything else
was real: refuse_if_dirty on the real tree, require_launch("E5") on the tmp ledger, and the D-20
digests read from the real checkpoints on this box.

```
PREFLIGHT OK a5d5ae84ac99eabb842bdb1644d4220cbbb04fd8 device=cpu readings=8 projection_h=0.467956566879681 stop_h=0.5418565110509128 spent_E5_s=0.0
RUN SCORED — next: crosscheck, then emit
LEDGER {'event': 'start', 'run_id': 'v6/38/E5/rank', 'phase': 38, 'front': 'E5', 'record': None}
LEDGER {'event': 'end', 'run_id': 'v6/38/E5/rank', 'phase': 38, 'front': 'E5', 'record': 'results/phase38_rank.json'}
SIDECARS ['phase38_rank_gate.json', 'phase38_rank_nll_M2.json', 'phase38_rank_nll_adapter_off.json', 'phase38_rank_nll_k0.json', 'phase38_rank_nll_k16.json', 'phase38_rank_nll_k32.json', 'phase38_rank_nll_k64.json', 'phase38_rank_nll_k78.json', 'phase38_rank_nll_k8.json', 'phase38_rank_run.json']
RUN {'status': 'SCORED', 'device': 'cpu', 'head_moved_during_run': False, 'sizes': {'birth_year': 220, 'cat_name': 512, 'hometown': 512, 'house_number': 512, 'person_name': 512, 'pet_name': 512, 'sibling_name': 512, 'street': 512}}
RECON {'components_sha256': 'a7cc22715d64def87795d730a69698206294963b2ed15b9badef495c82effda7', 'm2_adapter': '22e66552e92ec7d5f853a6b8d15f350cfc0f127f20ee85aaec1967147c375b57', 'persona_adapter': '226f2ae59938e389b396d999bc5f3e1e464874db5f3352d513dc5cd85984ebfb'}
BEATS 1
```

The plan's measured digests (226f2ae5 / a7cc2271 / 22e66552) match the real checkpoints and records,
and the committed gate ranks read back as the plan expects (k0..k64 all rank 1; k78 and M2 pet_name 2;
adapter_off 3-5). No false premise in the measured values.

## What the tests prove (tests/test_phase38_rank.py, 56 tests)

- 26 preflight refusals, each pinned to its own reason, with the tmp ledger and heartbeat absent:
  12 outputs, dirty tree, unknown HEAD, require_launch PAUSE, D-21 approval (7), committed cap ≠ 6,
  cpu on the real root, an untracked input, a missing CONVBASE / M2 / tracked JSON, and each of the
  three digests. An open attempt refuses and a closed one does not. The real require_launch passes on
  an empty tmp ledger.
- D-18 order: the order log is exactly every reading × slot × reference_set_for value, then exactly
  every reading × slot × [taught, *minted], so each value is scored once.
- GATE_FAILED (one flipped NLL at k32/street): no minted value, no NLL sidecar, and the run sidecar and
  end line are still written. A partial shape on the real root, or on any root inside the repo,
  refuses before any ledger line. The rehearsal partial shape gives two sidecars with 7 minted values
  each. A head move is named. A crash at k16 leaves k0/k8 intact, and reconcile turns the open start
  into a lost line.
- RANK-03: an AST gate over scripts/phase38_*.py checks for no own `exposure_rank`, `_rank_of`,
  `reference_set_for`, `value_span_nll` or `value_span_nll_mean`; no `exposure_rank`, `_rank_of` or
  `inject_lora` call; no `os.replace`; and the pinned calls only as module attributes. A non-vacuity
  check confirms both pinned calls are present. Five planted copies make it fail. The driver calls
  only `run_id`, `read_ledger`, `open_runs`, `require_launch` and `append` on phase36_ledger: no
  `rule`, and no `prefixes=`.
- The file has zero skips, and every function in phase38_rank is called by a test
  (`_untested_functions` census). Plan 07's new functions will need their own tests to keep it green.

## Deviations from Plan

**1. [Rule 3 - false premise in the plan text] Lazy import of phase38_sizes_prereg.**
The action text puts `import phase38_sizes_prereg as sizes_prereg` at module level. Measured:
`import phase38_sizes_prereg` → `'torch' in sys.modules` True (all other driver imports False), so
that import would make the plan's own acceptance line print `True`. The import moved inside
`scoring_plan` and `preflight`. That matches the plan's own rule that torch-importing modules are
imported only inside functions. `sizes_prereg.E5_SET_SIZES` is still always read through the module,
with no alias. Commit d379fd1.

**2. [Rule 2] A root inside the repository counts as the real root.** Truth 6 says a partial shape is
accepted only for a rehearsal root *outside the repo*. `_is_real(root)` is true for `_ROOT` and for
any path under `_REPO`. Such a root refuses a partial shape and a non-MPS device as the first I/O-free
checks. Tested with `_REPO / "scratch"` and `_REPO / "scratch_inside_repo"`.

**3. Small additions.** `TRACKED_INPUTS` and `SIZES_FILE` are module constants, so the untracked-input
refusal can be tested without patching `_REPO`. Neither is an upper-cased slot name, and the slot
census is green. The `_write_once` helper refuses an existing sidecar. The NLL sidecars also carry
the `minted` value list, so plan 07 can cross-check value by value. The run sidecar's `nll_sha256`
is `{}` on GATE_FAILED.

## Known Stubs
None. crosscheck, emit, report and the CLI dispatch belong to plan 07 by design. The docstring usage
lists them as "(plan 38-07)".

## Threat Flags
None beyond the plan's register: no new network, auth or schema surface. T-38-23..27 are mitigated
as the plan specifies.

## Self-Check: PASSED
- FOUND: scripts/phase38_rank.py, tests/test_phase38_rank.py
- FOUND: d379fd1, a5d5ae8
- Untouched: phase38_prereg.py, phase38_mint.py, phase38_sizes_prereg.py, results/phase38_minting.json,
  phase36_ledger.py, phase36_caps.py, phase18_extraction.py and STATE/ROADMAP/REQUIREMENTS. No gsd-sdk
  mutation handler was called. ` D .claude/scheduled_tasks.lock` was left alone.
