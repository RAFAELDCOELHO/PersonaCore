---
phase: 35-v6-0-pre-registration-and-the-research-it-rests-on
plan: 04
subsystem: prereg
tags: [prereg, slot-census, git-ordering, d-02, d-13, prereg-08]

requires:
  - phase: 35-03
    provides: SLOTS (17), fill(), owner_prereg_glob(), V6_RESULT_PATHS, _git_in/_planted_repo, _planted, _module_targets, _replace_lines, _function, _is_attribute
provides:
  - _fill_calls / _scanned_sources / _slot_census_failures (D-02 checks 1-3)
  - _dispatch_failures (fill dispatches only SLOTS[slot]['rule'])
  - _fill_sites / _slot_ordering_failures / _ordering_after_every_commit (per-fill-file legs (a)/(b)/(c), W20 guard)
  - _untested_functions (D-13 / PREREG-08 census)
affects: [35-05, phases 36-43 (every owner fill file is policed by these tests)]

tech-stack:
  added: []
  patterns:
    - "Owner fill files are policed by AST census over scripts/ + src/ and by a per-fill-file git ordering check, each watched RED"
    - "Ordering sequences are judged after EVERY commit (detached checkout on throwaway repos only, refused on the real repo by code)"

key-files:
  created: []
  modified:
    - tests/test_phase35_prereg.py

key-decisions:
  - "The shallow-clone refusal in _slot_ordering_failures carries the marker '(shallow)', not (a)/(b)/(c): it is a precondition of all three legs, not a leg"
  - "Fill-call bindings are matched by source span (lineno, col, end_lineno, end_col), because _fill_calls parses its own tree and node ids differ across parses"

requirements-completed: []
# The orchestrator ticks requirements at phase close; this plan's `requirements:` list
# (PREREG-05, PREREG-08) names IDs it contributes to, not IDs it closes.

duration: 9min
completed: 2026-10-01
---

# Phase 35 Plan 04: Slot census, per-fill-file ordering, every-function-has-a-test Summary

**D-02's three red cases and its ordering rule are now tests. An AST census covers every scripts/*.py and src/**/*.py file. A per-fill-file git ordering check runs on throwaway repos with legs (a), (b) and (c), and the green sequences are judged after every commit. A registry test checks that every slot input is declared, and a census checks that every function in the prereg has a CPU test. All of it is green on the real tree today and was watched RED on planted files. Only tests/test_phase35_prereg.py changed.**

## Performance

- **Duration:** about 9 min (base 525009e at 18:46:14 -0300; last task commit 5030c95 at 18:55:18 -0300)
- **Tasks:** 2, each in its own test commit
- **Files modified:** 1 (`tests/test_phase35_prereg.py`; test count 59 -> 68)

## The owner convention the census enforces (Phases 36-43 follow this)

1. **Where.** A slot X is filled only from a file matching `phase35_prereg.owner_prereg_glob(X)`, which is `scripts/phase{owner}_*prereg.py`. An owner may have several such files, for example `scripts/phase41_prereg.py` and `scripts/phase41_floors_prereg.py`. A fill in any other file is RED ("outside its owner"), and so is one in a non-`*prereg.py` file such as `scripts/phase40_driver.py`.
2. **How.** Use a plain `import phase35_prereg`, then a module-level `X.upper() = phase35_prereg.fill("X", ...)`, for example `E2_S = phase35_prereg.fill("e2_S", s=..., input_records=..., derivation=...)`. Each of these is RED:
   - the slot argument is not a str constant ("non-constant"), or names an undeclared slot ("undeclared");
   - the fill call is not the whole value of the single-target binding named `X.upper()`;
   - the name `X.upper()` is bound to anything other than that fill, such as a literal or a direct `_rule_*` call ("different rule");
   - any `phase35_prereg._rule_*` reference or `from phase35_prereg import _rule_*` ("_rule_ reference" / "_rule_ import");
   - `from phase35_prereg import fill`, `from phase35_prereg import *`, or `import phase35_prereg as x` ("alias");
   - a store or del on `phase35_prereg.SLOTS[...]` / `.SLOTS`, or `from phase35_prereg import SLOTS` ("registry write").
3. **Once.** A slot is filled exactly once across all scanned files ("filled twice").
4. **Ordering, per fill file F of owner O** (git, full clone; a shallow clone FAILS):
   - **(a)** Every commit of F strictly precedes the first add of every tracked `results/phase{O}_*` record. F's declared inputs are exempt ONLY when every slot F fills has a declared `results/phase{O}_*` input. One no-input slot in F (B7) strips the exemption from the whole file. So put a no-input design slot (`e5_minting_rule`, `e1_alternative_ordering`) in a fill file committed before the record it must precede. Never bundle it with an input-consuming slot.
   - **(b)** Whenever F is tracked, every tracked declared input of F's slots was first added strictly before F's first commit (B2). A record committed together with F fails.
   - **(c)** Once a phase-O record that is not a declared input of ANY phase-O slot is tracked, every phase-O slot must be filled (B6).

## Acceptance results (tool output)

- **Task 1 verify** (`-k "slot_census or slot_fill"`) gave 4 passed, 58 deselected, 0 skipped. Ruff check reported "All checks passed!" and format reported "1 file left unchanged".
- **Real-tree census.** `_scanned_sources(_ROOT)` scanned 140 files, 40 of them under src/, and `_slot_census_failures` returned `[]`.
- **The 12 plants, as measured.** Each one fired its expected phrase:
  - undeclared: `undeclared slot 'e9_undeclared'`
  - non-constant: `non-constant slot argument`, plus `different rule`
  - in phase41_prereg: `fills e2_S outside its owner (scripts/phase40_*prereg.py)`
  - in phase40_driver: the same "outside its owner" message
  - two files: `slot e2_S filled twice: scripts/phase40_prereg.py:2, scripts/phase40_seeds_prereg.py:2`
  - twice in one file: `filled twice`, plus `different rule` for E2_S_AGAIN
  - `E2_S = 5`: `different rule`
  - direct `_rule_e2_S` call: `different rule`, plus `_rule_ reference phase35_prereg._rule_e2_S`
  - `_rule_` import: `_rule_ import _rule_e2_S from phase35_prereg`
  - `S = fill("e2_S")`: `different rule`
  - SLOTS store: `registry write to phase35_prereg.SLOTS`
  - fill alias: `alias: from phase35_prereg import fill`, plus `different rule`

  Both positive controls returned `[]`: the single e2_S file, and the Phase 41 two-file owner in one census call.
- **Dispatch check.** It is `[]` on the real module. The AST-anchored plant replaced the single `ast.Return` of `fill` with `return _rule_e2_S(**inputs)` at its `col_offset`, and the planted copy reddens. The real file's bytes were unchanged.
- **Ordering on the real repo:** `([], 0)`. That is honest-green: there is no fill file and no v6.0 record.
- **GREEN sequences.** Each one was judged after EVERY commit, listed as (failure count, pairs):
  - g36: `[(0,0),(0,1),(0,2)]`
  - g41: `[(0,0),(0,1),(0,2),(0,4),(0,6)]`
  - g42: `[(0,0),(0,1),(0,2),(0,4)]`
  - g38: `[(0,0),(0,1),(0,2),(0,4)]`

  So there were zero failures at every commit, and pairs > 0 at the last commit.
- **RED scenarios, as measured.** Each scenario's failures carry only its own marker:
  - c40: two `(c)` failures, for e2_S and e2_noise_floor_estimator.
  - c41: two `(c)` failures, naming `e1_condition_a_floors` and `e1_condition_c_band_inputs` against `results/phase41_erasure_a.json`.
  - a40 and a40_same: one `(a)` failure each, `... (slots e2_S, e2_noise_floor_estimator have no phase-40 input)`.
  - b36: one `(b)`, `declared input results/phase36_probe_a.json of scripts/phase36_prereg.py is not first added strictly before ...`. No `(a)` or `(c)` fired (B2).
  - a41: one `(a)`, naming `scripts/phase41_prereg.py` and `phase41_calibration_a.json`.
  - b7_38: one `(a)`, naming `scripts/phase38_prereg.py` and `phase38_minting.json` `(slots e5_minting_rule, e5_rank_moves_and_generation_collapses have no phase-38 input)`.
  - b7_41: two `(a)` failures, naming `scripts/phase41_floors_prereg.py` against `phase41_band_inputs_a.json` and `phase41_calibration_a.json` `(slots e1_alternative_ordering have no phase-41 input)`.
- **W20.** `_ordering_after_every_commit(_git_in(_ROOT))` raises SystemExit matching "real repository", and HEAD is unchanged. The test asserts this.
- **`_untested_functions` on the real files, before the helpers test.** It reported 13 names: `_binom_pmf, _p_value, _prove_count, _prove_entries, _prove_finite, _prove_one_run_inputs, _prove_real, _prove_slots`, plus five design rules (`_rule_e2_noise_floor_estimator, _rule_e5_minting_rule, _rule_e5_rank_moves_and_generation_collapses, _rule_e6_decomposition_rule, _rule_r1b_tolerance_and_replicated`). The five rules were reported because the parametrized design test calls `fill(slot, ...)` with a variable. `test_prereg_helpers_behave` now asserts each of the 13 directly, and the rules go through literal `fill("<slot>", ...)` calls. The census is `[]` on the real files. The planted `def _rule_planted_untested(*, entry):` gives `["_rule_planted_untested"]`.
- **Task 2 verify.** `tests/test_phase35_prereg.py tests/test_phase29_prereg.py` gave 148 passed, exit 0. `ruff check .` reported "All checks passed!" and `ruff format --check .` reported "327 files already formatted".
- `-k "slot_ordering or v6_path_or_a_v5 or every_rule"` gave 5 passed, 63 deselected, 0 skipped.
- `PERSONACORE_SWEEP_ACTIVE=1 .venv/bin/pytest -q -p no:cacheprovider -rs tests/test_phase35_prereg.py` gave 68 passed, exit 0, 0 skipped.
- `-k slot --collect-only -q` gave `tests/test_phase35_prereg.py: 20`, exit 0, which meets the ≥ 8 requirement.
- After each commit, `git status --porcelain -- scripts/ tests/ results/` was empty. `find results ( -name 'phase3[5-9]_*' -o -name 'phase4[0-5]_*' )` and the matching `git ls-files` printed nothing.
- The census grep over the test file printed nothing. It searched for `== 10`/`!= 10`, sigma0/sigma_zero/seam_off/dp_fn, `os.replace`, `inject_lora`, `train_arm(`, `train_never_taught` and `privacy_n`. No K literal was added.

## Task Commits

1. **Task 1: slot census (undeclared, outside owner, different rule)** is `d150dbb` (test). It touches only `tests/test_phase35_prereg.py`.
2. **Task 2: per-fill-file ordering, input-record registry, every-function census** is `5030c95` (test). It touches only `tests/test_phase35_prereg.py`.

## Deviations from Plan

1. **[Rule 1 - Bug, caught before commit] Matching bindings by span instead of `id()`.** The first run of the positive control reddened with `different rule: fill('e2_S') is not the whole value of the module-level binding E2_S`. The cause: `_fill_calls(source)` parses its own tree, so its Call node ids never match the census tree's Assign values. The binding map is now keyed by `(lineno, col_offset, end_lineno, end_col_offset)`, and the positive controls pass. This is part of commit d150dbb.
2. **The shallow-clone failure marker is `(shallow)`.** The plan says every failure starts with `(a)`, `(b)` or `(c)`. The shallow refusal is a precondition of all three legs, so it carries `(shallow)` instead. It never fires on a full clone or on the planted repositories, so no "all start with" assertion is affected.
3. **The census rejects a little more than the plan lists.** `from phase35_prereg import *` counts as an alias, `from phase35_prereg import SLOTS` counts as a registry import, and rebinding `phase35_prereg.SLOTS` itself counts as a registry write. These are the same rules applied to the obvious neighbouring spellings.
4. **Planted owner files go through `_planted(tmp_path, "", text, "<n>.py")`.** Each one is a flat file under tmp_path, read back and paired in memory with its logical relpath (for example `scripts/phase40_prereg.py`). Nothing is written under scripts/.
5. **One extra helper assertion.** `test_prereg_helpers_behave` (written before `test_every_rule_has_a_cpu_test`, as the plan asks) also checks that `_prove_entries` refuses a monkeypatched bad entry, beyond the plan's "at least" list.
6. **A hook interaction outside the repository.** A local `rm -rf` of a scratchpad directory was blocked by a user hook (the Fact-Forcing Gate). I used a fresh `mktemp -d` under the scratchpad instead, and nothing was deleted. No git hook interfered with the throwaway repos.

No premise was falsified. Plan 03's slot inputs, the owner globs, and the absence of any phase36-45 file in scripts/ or results/ all held when measured.

## Known Stubs

None.

## Threat Flags

None. The only new git mutation is `checkout --detach` inside `_ordering_after_every_commit`. It runs on throwaway repos under tmp_path, and a `_prove` guard that compares `rev-parse --show-toplevel` with `_ROOT` refuses the real repository in code (T-35-20/W20, as planned).

## Self-Check: PASSED

- FOUND: tests/test_phase35_prereg.py (modified in d150dbb, 5030c95)
- FOUND commits: d150dbb, 5030c95
