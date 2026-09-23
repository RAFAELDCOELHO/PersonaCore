---
phase: 27-relearning-attack
plan: 01
subsystem: testing
tags: [pre-registration, ancestry-guard, admission-gate, relearning, mitigation-gate, sha256-pins]

# Dependency graph
requires:
  - phase: 25-frontier-sweep-and-the-existence-gate-verdict
    provides: results/phase25_frontier.json (44 points, tallies PASS 0 / FAIL 32 / INCONCLUSIVE 6 / REFUSED 6), the sanctioned route phase20_gate_coverage.corrected_point_verdict
  - phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
    provides: results/phase23_never_taught_training.json (five never-taught adapters, seeds, sha256), phase23_prereg.noise_floor
provides:
  - scripts/phase27_prereg.py — the frozen pre-registration (admission gate, X by call, Z rule, rung ladder + cap, band, K, seven pinned baselines, attacker corpus + two sha256 pins, recovery gate)
  - tests/test_phase27_prereg.py — 23 test functions / 28 collected (ancestry guard, both-ways frontier pin, gate domain, 44-verdict route tripwire, re-derivations, signature pins, corpus re-render)
affects: [27-02, 27-03, 27-04, 27-05, 28]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pre-registration module CPU-only at import; torch-side originals asserted equal in tests only"
    - "Admission gate with INCONCLUSIVE precedence over total AND per-leg tally re-derivation"
    - "Budget symbols read from module globals at call time, so downstream tests can monkeypatch them"

key-files:
  created:
    - scripts/phase27_prereg.py
    - tests/test_phase27_prereg.py
  modified: []

key-decisions:
  - "recall_threshold = F_Y * (k / n), plan item 12 — bit-identical to the frontier pin's F_Y * control_taught_recall; the acceptance criterion's 0.7 * 790 / 1008 is 1 ulp away (measured)"
  - "Per-leg tallies_by_leg must re-derive too, or the gate reads INCONCLUSIVE — the MOOT reasons print those numbers as fact"
  - "Attacker bin sha256 measured invariant to arm name and seed (replay 0.0, adversarial 0.0, non-DP arm), so one digest pins every arm 27-03 builds"

patterns-established:
  - "Natural RED from the pre-paste placeholder: bin_sha256 written as a placeholder, test run RED, host digest pasted, GREEN"

# RELRN-01..05 in the plan's `requirements:` are the IDs this plan CONTRIBUTES to, not IDs it completes:
# per D-05 RELRN-01 is ticked only at plan 27-05, and RELRN-02..05 stay unticked by design.
requirements-completed: []

# Metrics
duration: 24min
completed: 2026-09-16
---

# Phase 27 Plan 01: Relearning Pre-Registration Summary

**Frozen pre-registration: `relearning_is_worth_attempting` reads MOOT on the committed frontier (0 of 44 PASS; cleared (a) 30 / (b) 4 / (c) 1 over 38 reached, 6 REFUSED). X is a call to `mitigation_gate.extraction_ceiling`. The module also freezes the Z rule on the 50..400-step ladder, the MARGIN_K × noise_floor band, the seven sha256-pinned baselines and the attacker corpus pinned by rows and bin sha256. It landed in ONE commit with its 28-test guard file, before any `results/phase27_*` exists.**

## Performance

- **Duration:** 24 min
- **Started:** 2026-09-16T15:40:29Z
- **Completed:** 2026-09-16T16:04:20Z
- **Tasks:** 2 of 2
- **Files:** 2 created (631 + 632 lines), 0 modified

## Accomplishments

- `scripts/phase27_prereg.py`: every symbol plans 27-02..27-05 name. A regex census of `phase27_prereg.<name>` across the four later PLAN.md files found 40 distinct names, 0 missing.
- The gate reads **MOOT** on `results/phase25_frontier.json`. Reasons are generated from counts, never copied: per-leg tallies plus cleared counts, then the total.
- The 44-verdict tripwire runs through the sanctioned route: 38 `(verdict, reasons, arm)` equal, 6 `SystemExit` equal to `reasons[0]`, and a perturbed deep copy disagrees.
- Ancestry guard is honest with zero tracked artifacts. The frontier is at exactly one commit in the absent-record state.

## Task Commits

The plan's commit boundary is ONE code commit carrying both files. Task 1 was not committed on its own.

1. **Task 1 + Task 2: prereg module + guard tests** - `916ad4d` (feat)

**Plan metadata:** this SUMMARY's own commit (docs).

## Evidence

### Single commit, nothing under `results/phase27_*`

```
$ git log --format=%H -- scripts/phase27_prereg.py
916ad4d48d8ee9e79bfdb2aa4a16ba934d048d72
$ git show --name-status --format= 916ad4d
A	scripts/phase27_prereg.py
A	tests/test_phase27_prereg.py
$ git ls-tree -r --name-only 916ad4d -- results | grep '^results/phase27_'   -> (nothing)
$ git ls-files 'results/phase27_*'                                          -> (nothing)
$ git diff --diff-filter=D --name-only HEAD~1 HEAD                          -> (nothing)
```

### Task 1 verify (`<automated>`) and acceptance criteria

```
$ .venv/bin/python -c "...relearning_is_worth_attempting(f)...print('OK')" && ruff check && ruff format --check
OK
All checks passed!
1 file already formatted
```

Criteria script (`scratchpad/27-01/task1_criteria.py`), raw output:

```
C1 torch/teach_persona/phase18_extraction absent after import: PASS
C4a gate MOOT + '0 of 44' + per-leg tallies + total '(a) 30 / (b) 4 / (c) 1': PASS
C4b cleared_counts: PASS {'a': 30, 'b': 4, 'c': 1, 'reached': 38, 'refused': 6, 'by_leg': {'dp_n8': {'a': 15, 'b': 1, 'c': 1}, 'dp_n64': {'a': 15, 'b': 1, 'c': 0}, 'adv_n8': {'a': 0, 'b': 2, 'c': 0}, 'adv_n64': {'a': 0, 'b': 0, 'c': 0}}}
C5 X by call == frontier X == 0.006461685297443485: PASS 0.006461685297443485
C6 LITERAL criterion recall_threshold == (0.7 * 790 / 1008, 790, 1008): FAIL | (0.7 * 87 / 1008, 87, 1008): FAIL
C6 as-measured recall_threshold == (F_Y * (k / n), k, n): PASS (0.548611111111111, 790, 1008) (0.06041666666666666, 87, 1008)
C7 recovery_gate baseline KEYWORD_ONLY/no default; made_up SystemExit; 1/416 FAIL; z=None INCONCLUSIVE; True SystemExit: PASS
C8 band: PASS
C9 scored_tokens: PASS
C10 ATTACKER_CORPUS 64-hex digests, n_rows int in 150..200, rows sha re-renders: PASS 176
C2 grep -c mitigation_point_verdict: 0
C2 grep -c train_arm(: 0
C3 grep -E 0\.00646 (expect nothing):
(end C3, grep exit=1)
C11 git ls-files results/phase27_*: []
```

C6's literal spelling is Deviation 1 below.

The gate's MOOT output on the committed frontier, verbatim:

```
MOOT
   0 of 44 points PASS; tallies {'PASS': 0, 'FAIL': 32, 'INCONCLUSIVE': 6, 'REFUSED': 6}
   dp_n8: PASS 0 / FAIL 16 / INCONCLUSIVE 0 / REFUSED 0; cleared (a) 15 / (b) 1 / (c) 1 of 16 reached point(s)
   dp_n64: PASS 0 / FAIL 16 / INCONCLUSIVE 0 / REFUSED 0; cleared (a) 15 / (b) 1 / (c) 0 of 16 reached point(s)
   adv_n8: PASS 0 / FAIL 0 / INCONCLUSIVE 6 / REFUSED 0; cleared (a) 0 / (b) 2 / (c) 0 of 6 reached point(s)
   adv_n64: PASS 0 / FAIL 0 / INCONCLUSIVE 0 / REFUSED 6; cleared (a) 0 / (b) 0 / (c) 0 of 0 reached point(s)
   cleared (a) 30 / (b) 4 / (c) 1 of 38 reached points; 6 REFUSED never reached (a)
   MOOT: no point cleared the frontier — nothing survived the mitigation, so there is nothing to relearn
```

### Pinned inputs read from their sources, never retyped

- **Five never-taught digests:** printed programmatically from `results/phase23_never_taught_training.json::adapters` into the module literal. `seeds [1337, 2024, 1338, 2025, 1339]`.
- **Two control digests:** read from `results/phase25_frontier.json` points `dp_n{8,64}_sigma0p000000`, then cross-checked:

```
n8 frontier sha == interfaces: True | source record exists: True | source adapter_sha256 == frontier: True | source adapter_path == frontier: True | source seed: 1337
n64 frontier sha == interfaces: True | source record exists: True | source adapter_sha256 == frontier: True | source adapter_path == frontier: True | source seed: 1337
```

- **On-host hashes:** `test_pinned_adapters_hash_on_host` RAN here (PASSED, not skipped). All seven adapters hash to their pins.

### ATTACKER_CORPUS digests: computed once, under a redirected `teach_persona._REPO_ROOT`

Scratch script `scratchpad/27-01/corpus_digests.py` ran into two independent temp roots (`rootA`, `rootB`) under the session scratchpad:

```
BEFORE find:
(end before)
row type list tuple 2
bin path /private/tmp/claude-501/.../scratchpad/27-01/rootA/data/persona_relearn_attacker_train.bin
bin under root True
n_facts 8 families ['F1', 'F2', 'F4', 'F5', 'F6']
n_rows 176
rows_sha256 24e96fa6a3714e02ec3e8239c8d160befa769561067b93151d9b654be7b72fcf
bin_sha256 f146d42637c69e9eb1e7ac2248c9056a7966aed48f6498fa9cdb6d3db02d147b
stats episodes 176 tokens 7581
--- rootB (determinism) ---
bin under root True
n_rows 176
rows_sha256 24e96fa6a3714e02ec3e8239c8d160befa769561067b93151d9b654be7b72fcf
bin_sha256 f146d42637c69e9eb1e7ac2248c9056a7966aed48f6498fa9cdb6d3db02d147b
```

Arm-name and seed invariance, measured because 27-03 compares its per-arm bins against this one pin:

```
relearn_attacker_n8_fresh_seed2024 2024 f146d42637c69e9eb1e7ac2248c9056a7966aed48f6498fa9cdb6d3db02d147b True
relearn_attacker_n64_control_seed1337 1337 f146d42637c69e9eb1e7ac2248c9056a7966aed48f6498fa9cdb6d3db02d147b True
```

Nothing landed in the real tree. Output after the renders, re-run after the commit:

```
$ find data -maxdepth 1 \( -name 'persona_relearn_attacker_*' -o -name 'phase27_*' \)
(end after)                      <- prints nothing
$ git status --short             (after the renders, before the commit)
 D .claude/scheduled_tasks.lock
?? scripts/phase27_prereg.py
?? tests/test_phase27_prereg.py
```

The lock deletion pre-dates this session and was never staged.

### Natural RED (plan Task 2) and GREEN

This was a two-step write: the module was first written with `"bin_sha256": "PENDING-HOST-RENDER"`, the host digest was pasted only after the test had run. The scratchpad render did happen before the module was written, so the placeholder was a deliberate first draft following the plan's sequence, not an accident of timing. The digest was never in the module before this RED.

```
$ grep -n '"bin_sha256"' scripts/phase27_prereg.py
204:    "bin_sha256": "PENDING-HOST-RENDER",
$ .venv/bin/pytest -q "tests/test_phase27_prereg.py::test_attacker_corpus_sha_re_renders"
>       assert hashlib.sha256(paths["bin"].read_bytes()).hexdigest() == p.ATTACKER_CORPUS["bin_sha256"]
E       AssertionError: assert 'f146d42637c6...b6d3db02d147b' == 'PENDING-HOST-RENDER'
E         - PENDING-HOST-RENDER
E         + f146d42637c69e9eb1e7ac2248c9056a7966aed48f6498fa9cdb6d3db02d147b
tests/test_phase27_prereg.py:629: AssertionError
1 failed in 0.88s
```

The rows-sha and `n_rows` assertions above that line passed, and the bin was built under `tmp_path`. After pasting the digest:

```
1 passed in 0.82s
```

### Task 2 verify (`<automated>`), after the commit

```
$ .venv/bin/pytest -q tests/test_phase27_prereg.py -x
28 passed in 3.37s
$ ruff check tests/test_phase27_prereg.py && ruff format --check tests/test_phase27_prereg.py scripts/phase27_prereg.py
All checks passed!
2 files already formatted
$ .venv/bin/pytest -q tests/test_phase25_close.py tests/test_phase20_correction.py tests/test_phase23_resume.py -x
49 passed in 103.07s (0:01:43)
verify exit=0
```

Before the commit, the same file ran `27 passed, 1 failed`. The one failure was the ancestry guard, which cannot pass before its own commit exists: `AssertionError: scripts/phase27_prereg.py has no commits — green and blind`.

Named node ids, after the commit (`-v`):

```
tests/test_phase20_correction.py::test_mitigation_point_verdict_has_no_caller_outside_this_module PASSED
tests/test_phase23_resume.py::test_resume_from_none_is_inert PASSED
tests/test_phase27_prereg.py::test_pinned_adapters_hash_on_host PASSED
tests/test_phase27_prereg.py::test_phase27_prereg_is_frozen_before_every_phase27_result PASSED
tests/test_phase27_prereg.py::test_every_frontier_verdict_re_derives_through_the_route PASSED
tests/test_phase27_prereg.py::test_the_record_is_pinned_to_the_frontier_both_ways PASSED
```

- **Test functions:** `grep -c "def test_" tests/test_phase27_prereg.py` → `23` (≥ 22).
- **Grep criteria:** `grep -rn "train_arm(" scripts/phase27_prereg.py tests/test_phase27_prereg.py` → nothing (exit 1).

### Collected tests

```
$ .venv/bin/pytest --collect-only -q | tail -1
2830 tests collected in 2.94s
$ .venv/bin/pytest --collect-only -q tests/test_phase27_prereg.py | tail -1
28 tests collected in 0.22s
```

Delta **+28** over the 2802 baseline: 2802 + 28 = 2830. The file ran 28 passed, 0 failed, 0 skipped.

### Scripts/tests-walking guards, run before the commit (a frozen file can't be fixed after it)

Pre-commit run over 15 guard files plus the Phase-19 census node:

```
$ .venv/bin/pytest -q tests/test_phase25_close.py tests/test_phase20_correction.py tests/test_phase23_resume.py tests/test_lora_inject.py tests/test_phase14_scoring.py tests/test_phase21_unit_continuation.py tests/test_phase21_sc5.py tests/test_phase23_ctrl.py tests/test_phase25_driver.py tests/test_phase25_epsilon.py tests/test_phase25_plots.py tests/test_phase25_watch.py tests/test_phase25_prereg.py tests/test_phase25_probe2.py tests/test_phase25_grid.py "tests/test_phase19_erasure.py::test_retention_measurement_pins_a_new_call_site_with_no_adapted_precedent"
9 failed, 271 passed in 124.02s (0:02:04)
```

All 9 failures were clean-tree porcelain probes. Every assertion names only the two untracked new files:

- `?? scripts/phase27_prereg.py` (7 probes):
  - `test_phase25_driver.py::test_the_git_surface_gate_fires_on_a_planted_push`
  - `test_phase25_epsilon.py::test_the_epsilon_gate_fires_on_a_planted_bare_print`
  - `test_phase25_plots.py::test_the_torch_guard_fires_on_a_planted_import`
  - `test_phase25_plots.py::test_the_checkpoint_literal_guard_fires_on_a_planted_pt_literal`
  - `test_phase25_plots.py::test_the_fresh_interpreter_probe_fires_on_a_planted_torch_import`
  - `test_phase25_plots.py::test_the_allow_list_clause_fires_on_a_planted_second_read`
  - `test_phase25_watch.py::test_the_never_act_guard_fires_on_a_planted_action`
- `?? tests/test_phase27_prereg.py` (2 probes):
  - `test_phase25_probe2.py::test_a_planted_bit_identity_assertion_here_would_fire`
  - `test_phase25_grid.py::test_the_from_import_variant_is_invisible_to_the_register_walk`

Example message: `AssertionError: watching the RED must leave no residue in scripts/: '?? scripts/phase27_prereg.py\n'`.

After the commit, all 9 plus `test_phase25_frontier.py::test_a_perturbed_per_point_count_breaks_the_aggregate` were re-run by node id: `16 passed in 4.11s`. Every census that walks `scripts/` or `tests/` was green with both new files present: the pin census, the `train_arm(` register, the D-21 LoRA and scoring censuses, the `privacy_n` route, the `== 10` wall census, `train_never_taught`, `os.replace`, and the bit-identity tripwire.

### Plan-level `<verification>`

```
$ git diff --stat HEAD~1 HEAD -- scripts/teach_persona.py scripts/mitigation_gate.py scripts/erasure_gate.py scripts/phase26_prereg.py scripts/phase25_prereg.py results/phase25_frontier.json pyproject.toml
(nothing)
$ git diff --stat HEAD -- <same seven> src results
(nothing)
```

## Files Created/Modified

- `scripts/phase27_prereg.py` (631 lines) — the pre-registration:
  - `COMMITTED = "2026-09-16"`, `RECORDS_AT_COMMIT = 0`, `ARTIFACT_GLOB`
  - by-reference `MARGIN_K / CURVE_K / FULL_K / F_Y / V4_VERDICTS / NEVER_TAUGHT_ARM / GATED_TIER / ATTACK_FAMILIES / HELD_OUT_FAMILY / TRAINED_FAMILIES / FRONTIER_RECORD`
  - budget ints `MAX_STEPS / CHECKPOINT_INTERVAL / DESIGNATED_SEED / RELEARN_CAP / RUNGS / FRESH_SEEDS / POOLED_SEED_INDEX`
  - domains; `PINNED_BASELINES` (7) + `BASELINE_KEYS`; `ATTACKER_*` + `attacker_corpus_rows[_sha256]`
  - gate functions: `point_verdict_string`, `cleared_abc`, `extraction_ceiling_x`, `leg_of`, `arm_of`, `relearning_is_worth_attempting`, `admitted_point_keys`, `cleared_counts`, `recall_threshold`, `_prove_count`, `first_clear`, `z_rule`, `band`, `scored_tokens`, `recovery_gate`, `promote_at_z`
  - disclosures: `NOT_EXERCISED`, `FRESH_CURVE_DISCLOSURE` (renders byte-equal to the plan's literal, measured True)
- `tests/test_phase27_prereg.py` (632 lines) — the 23 test functions the plan names, 28 collected: `test_z_rule_table` is parametrized ×6, with the `first_clear` checks inside it.

## Decisions Made

- `F_Y * (k / n)` for the recall threshold, matching the pin's own Y bit for bit (Deviation 1).
- Per-leg tally re-derivation belongs to the INCONCLUSIVE precedence (Deviation 3).
- All budget and pin symbols are read from module globals at call time, never bound as defaults. Plan 27-04's interfaces list them as monkeypatch targets.

## Deviations from Plan

### Plan text falsified by measurement (followed the code/measurement)

**1. Acceptance criterion `recall_threshold(frontier, "n8") == (0.7 * 790 / 1008, 790, 1008)` contradicts plan item 12 (`threshold = F_Y * (k / n)`)**
- **Found during:** Task 1, before writing the code.
- **Evidence:**
  ```
  790 1008 0.548611111111111 0.5486111111111112 False     # F_Y*(k/n) vs F_Y*k/n
  87 1008 0.06041666666666666 0.06041666666666667 False
  dp_n8_sigma0p000000 k/n == stored rate: True | F_Y*(k/n) == F_Y*stored: True | F_Y*k/n == F_Y*stored: False
  dp_n64_sigma0p000000 k/n == stored rate: True | F_Y*(k/n) == F_Y*stored: True | F_Y*k/n == F_Y*stored: False
  ```
- **Resolution:** item 12's `F_Y * (k / n)` equals the frontier pin's `F_Y * control_taught_recall` exactly. That is D-24's "clear means what it meant on the frontier". The criterion's left-to-right spelling is 1 ulp away.
- **Test:** `test_recall_threshold_reads_counts_not_rates` asserts `(F_Y * (790 / 1008), 790, 1008)`, plus bit-identity with `F_Y * control_taught_recall` for both legs.
- **Files:** `scripts/phase27_prereg.py`, `tests/test_phase27_prereg.py`. **Commit:** `916ad4d`.

**2. Task 2 spec `collections.Counter(...) == verdicts.tallies` is always False on this frontier**
- **Evidence:** `Counter == dict(with PASS:0): False | Counter == Counter(dict): True`. `Counter.__eq__` returns NotImplemented for a plain dict, so dict equality applies and the absent `PASS: 0` key differs.
- **Fix:** `test_the_tally_re_derives_from_the_entries` compares Counter to Counter, which treats missing keys as zero. A comment in the test says why. **Commit:** `916ad4d`.

### Auto-added (Rule 2 — correctness of what the record will say)

**3. Per-leg tallies must re-derive, or the gate reads INCONCLUSIVE**
- **Issue:** the MOOT reasons print `verdicts.tallies_by_leg` numbers as fact (D-07). The plan's gate checked only the total tally, so an inconsistent per-leg tally would have published wrong numbers under MOOT.
- **Fix:**
  - The gate re-derives per-leg tallies from the 44 strings and reads INCONCLUSIVE on mismatch. That is D-03's "a tally that does not re-derive".
  - The forged copies in `test_the_gate_admits_only_pass` move both tallies (`_forge`), so the only thing a forgery changes is the verdict under test.
  - `test_partial_or_inconsistent_frontier_is_inconclusive` gained a per-leg-mismatch case.
- **Scope:** no downstream plan forges frontier verdicts without its tallies. 27-03's `build_record` already `_prove`s per-leg equality at the write.
- **Commit:** `916ad4d`.

**4. Small hardening inside the plan's intent**
- `leg_of` `_prove`s the key names the leg it returns.
- `first_clear` also refuses non-ascending rungs and counts outside `0 <= k <= n > 0`.
- `z_rule` `_prove_count`s non-None inputs and checks them against `RUNGS`.
- `recall_threshold` `_prove`s the leg and the counts.
- `test_the_prereg_imports_without_torch` also checks `phase18_extraction`.
- `test_the_curve_cannot_reach_the_verdict` also pins the exact five-name parameter set.
- `test_x_is_the_frontier_ceiling_by_call_not_literal` also refuses two controls that disagree on X.
- None of these changes a verdict on the committed frontier or on any input the later plans describe. **Commit:** `916ad4d`.

---

**Total deviations:** 2 plan-text falsifications followed by measurement, 2 correctness additions (Rule 2).
**Impact on plan:** no scope creep. Every acceptance criterion holds, except C6's literal float spelling, replaced by the measured form above.

## Issues Encountered

- The first Bash call with `rm -rf` on the scratch roots hit the Fact-Forcing Gate. The roots did not exist, so the `rm` was dropped.
- `echo ====` is a command lookup under zsh; the separator was quoted.
- Neither affected any artifact.

## Forward notes for later plans — the prereg is frozen, so these fixes belong in THOSE plans

1. **27-04 promotion will refuse the planned tiny K.**
   - 27-04 Task 1 (e) monkeypatches `phase27_prereg.CURVE_K = 2` and `FULL_K = 4`.
   - `promote_at_z` routes through `mitigation_gate.promote_to_full_fidelity` → `ratchet_k`, which only accepts `K_RUNGS = (48, 24, 16, 8)`.
   - Measured: `mitigation_gate.ratchet_k(fixed_k=2, proposed_k=4) -> SystemExit: [mitigation_gate] fixed_k 2 is not a member of the closed menu K_RUNGS (48, 24, 16, 8)`.
   - 27-04 must also monkeypatch `mitigation_gate.K_RUNGS` (read at call time) or use menu values (e.g. 8 → 16). The prereg cannot change this without breaking D-21.
2. **Counts must be Python ints.**
   - `_prove_count` refuses numpy integers. Measured: `isinstance(np.int64(1), int): False | numpy 2.4.6`, and `scored_tokens(mask_ones=np.int64(7581), steps=50)` → `SystemExit`.
   - 27-03 must cast with `int(...)` before `first_clear` / `scored_tokens` / `recovery_gate`.
3. **Seven more clean-tree probes than the orchestrator's list.** They watch `scripts/`, not only `results/` and `tests/`, and go RED while any file under `scripts/` is untracked. This matters for 27-03's pre-commit runs (new `scripts/phase27_relearn.py`). See the list above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 27-02 (`on_draw` capture) is independent of this module.
- 27-03 can import every symbol it names (40/40 present).
- The ancestry guard becomes a real ordering check from 27-05 Task 2, when the operator commits `results/phase27_admission.json`.
- No gsd-sdk mutation handler was called. STATE.md, ROADMAP.md and REQUIREMENTS.md are untouched, and no RELRN checkbox was ticked (D-05, D-38).

## Self-Check: PASSED

- `scripts/phase27_prereg.py` FOUND; `tests/test_phase27_prereg.py` FOUND
- commit `916ad4d` FOUND (`git log --format=%H -- scripts/phase27_prereg.py` → exactly `916ad4d48d8ee9e79bfdb2aa4a16ba934d048d72`)
- `git ls-files 'results/phase27_*'` empty at `916ad4d`

---
*Phase: 27-relearning-attack*
*Completed: 2026-09-16*
