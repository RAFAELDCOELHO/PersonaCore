---
phase: 21
slug: the-privacy-unit-the-dp-data-path-and-the-n-64-corpus
status: closed
nyquist_compliant: true
wave_0_complete: true
created: 2026-08-22
closed: 2026-08-25
closed_by: gap closure, UAT decision 4 — the documentation ledger
commands_verified: 48/48 (every command below executed; exit 0 AND non-zero collection)
---

# Phase 21 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
>
> **Source of truth for the full requirement→test map:** `21-RESEARCH.md` §`## Validation
> Architecture` (`:175`), whose every command and timing is marked `[VERIFIED]` against a real run.
> This file is the execution-time contract; that file is the evidence.

> **CLOSED 2026-08-25.** The phase is EXECUTED and VERIFIED; this document is the ledger for it.
> **What "closed" does and does not mean:** every row below now carries a measured status and a
> command that was executed rather than typed. It is **not** a claim that the phase passed —
> `21-VERIFICATION.md` returned **`human_needed`**, not `passed`, and five review warnings plus
> three infos in `21-REVIEW.md` remain open (WR-03, WR-05, WR-06, WR-07 and IN-01…IN-04 as of this
> writing; WR-04 closed at `9a407d6`). See `## Closure` at the foot of this file.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Python** | 3.11.15 — **`.venv` only.** The dev box is 3.14 and is NOT a supported target (CLAUDE.md). Never validate there. |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (`:24-26`) — `testpaths = ["tests"]`, `pythonpath = ["."]` |
| **Quick run command** | `.venv/bin/python -m pytest -q tests/test_phase20_prereg.py tests/test_package.py tests/test_masked_batch.py tests/test_phase14_teaching.py` |
| **SC5 guard set** | `.venv/bin/python -m pytest -q tests/test_phase14_scoring.py tests/test_phase16_driver.py tests/test_phase16_ladder.py tests/test_phase18_corpus.py tests/test_phase18_prereg.py tests/test_phase19_erasure.py tests/test_phase14_factset.py tests/test_phase14_demo.py tests/test_phase21_filler.py tests/test_phase21_multiplicity.py` |
| **Full suite command** | `make test` (`pytest -q`) |
| **Measured runtime (2026-08-25)** | quick **70 passed** · SC5 guard set **364 passed** · full **≈199s, 1,025 collected** |

**The SC5 guard set grew from 8 files to 10 during execution**, and the growth is not editorial:
`tests/test_phase21_filler.py` and `tests/test_phase21_multiplicity.py` were added because both hold
`== 10` wall sites (see the census below). The membership is now checkable rather than promised —
`tests/test_phase21_sc5.py:291-302` holds `SC5_GUARD_SET` as a tuple and
`tests/test_phase21_sc5.py:286` asserts every file the census discovers is a member of it, so a wall
site landing in a file the guard set does not run turns the census RED.

**The "one skip" named here was wrong, and is corrected.** This file claimed the single skip was
`test_loop_penalty_fn::test_golden_trajectory_bit_identity`. 21-10 measured that that test does not
skip. The real platform-gated skip is **`tests/test_train_loop.py:81`** — a CUDA-only fp16 AMP
smoke, which skips on MPS, on CPU and in CI alike.

**Suite figures — the binding number and the worktree number are different, deliberately.**

| Figure | Value | Where it holds |
|---|---|---|
| **Binding (full checkout)** | **`1024 passed, 1 skipped`** = 1,025 collected | `main` with `data/` and the gitignored artifacts present. This is the GREEN definition. |
| Measured here (gap-closure worktree, literal) | `1018 passed, 7 skipped` in 201.72s, exit 0 | A worktree lacks the gitignored `artifacts/`; **6 of the 7 skips are those absent artifacts** and 1 is the CUDA gate. |

**The two reconcile exactly.** Restore the 6 gitignored artifacts and those 6 skips pass:
`1018 + 6 = 1024` passed, `1` skipped. Collection is `1,025` either way, independently confirmed by
`pytest -q -k <non-matching>` reporting `1025 deselected`. Skip reasons enumerated with `-rs` in
`21-REVIEW.md` → `## Ledger — CLOSED`, so "environmental" is a reading rather than an assertion.

The stale `877 passed, 1 skipped` this file carried predates the phase's own 30 new tests and every
Phase-20 correction test; it is superseded, not merely out of date.

> A worktree run that reports `1 failed` on `tests/test_phase21_unit_record.py::test_driver_refuses_to_rerun`
> is an **environment** result, not a regression: the test reaches `_prepend_replay`, which needs
> `data/dialog_train.bin` and `data/dialog_train_mask.bin`. Copy those two files (≈16 MB of the 4.8 GB
> `data/`) and it passes. Verified both ways during this closure.

**CI prerequisite that is load-bearing here:** `.github/workflows/ci.yml:21` sets `fetch-depth: 0`.
`_assert_ordering_holds` asserts `rev-parse --is-shallow-repository == "false"` and refuses to skip
(`tests/test_phase20_prereg.py:136-141`) — a shallow clone turns the ancestry guard into an error,
not a silent pass.

---

## Sampling Rate

- **After every task commit:** the **quick run command** + every `tests/test_phase21_*.py` that
  exists at that point. ~3.5s.
- **After every plan wave:** the **SC5 guard set** + all `tests/test_phase21_*.py`. ~36s.
- **Before the first `results/phase21_*` COMMIT:** `pytest -q tests/test_phase20_prereg.py` must be
  **armed and green first** (1.86s / 21 tests). `git ls-files` is the guard's input, so an artifact
  becomes watched when it is **committed**, not when it is written. Arm-then-write is an ordering
  constraint on commits, and `:157` (`adds[-1]`, the earliest add) makes it irrevocable.
- **Before `/gsd:verify-work`:** full suite green — `1024 passed, 1 skipped` on a full checkout.
- **Max feedback latency:** 36s at wave granularity; 3.5s at task granularity.

**OBSERVED, and it is the one sampling rule this phase had to change mid-flight:** plan-check pass 3
found six per-plan bare `pytest -q` invocations in waves 3's plans (21-06 / 21-07 / 21-08). Because
`testpaths = ["tests"]`, a bare run collects a *sibling's* live deliberate-RED. They were replaced
with explicit file lists; the full suite stayed a WAVE-CLOSE gate, which is what `:47` and `:52`
already said. Recorded here because it is a fact about how the sampling rate was actually applied.

---

## Per-Task Verification Map

**Every command in this table was EXECUTED during closure, not typed.** Ownership (`Plan`, `Wave`,
`Shipped`) is resolved from `git log --diff-filter=A` on each artifact, not from the plan set.

### Why these are node ids and not `-k` selectors

The planning-time table addressed every single-test row as `-k <substring>`. That is the weaker
form, and this phase produced the proof: `-k phase21_glob_red_then_green` matched **nothing** for
the whole phase because the real test is `test_phase21_glob_sees_the_phase21_prefix_red_then_green`
— `-k` is substring matching and `glob_red_then_green` is not a substring of it.

**The reason to prefer node ids is NOT that a bad `-k` "silently exits 0". That framing is false and
this file will not repeat it.** Measured here, with the exit code taken from the pytest process
itself (`OUT=$(...)` then `E=$?`) rather than through a pipe:

| invocation | output | EXIT |
|---|---|---|
| mistyped `-k` | `4 deselected in 0.72s` | **5** (`NO_TESTS_COLLECTED`) |
| wrong node id | `ERROR: not found: …::test_instruments_unchanged` + `no tests ran` | **4** (`USAGE_ERROR`) |
| correct node id | `1 passed` | **0** |

Neither form passes silently. **The node id is still strictly better** — exit 4 *and* the error
NAMES the id that is missing, where exit 5 only says "deselected" and never says what was expected.

**Where the false "exit 0" came from, reproduced exactly.** `pytest … | tail -1` then `$?` reports
**tail's** status, not pytest's:

```
$ .venv/bin/python -m pytest -q tests/test_phase21_sc5.py -k frozen_instruments_are_byte_unchanged | tail -1
4 deselected in 0.49s
$ echo $?
0            # <-- tail's exit status
```
```
$ OUT=$(.venv/bin/python -m pytest -q tests/test_phase21_sc5.py -k frozen_instruments_are_byte_unchanged 2>&1); echo $?
5            # <-- pytest's actual exit status
```

That artifact produced the same wrong claim in **four** places in this phase: `21-VERIFICATION.md:24`
and `:211`, `21-REVIEW.md` IN-03 (`:481`), and — the one nobody had caught — a **shipped source
docstring** at `tests/test_phase21_sc5.py:317`. All four are corrected; see `## Closure`.

### The map

`Command` is the exact argv after `.venv/bin/python -m pytest -q`. `Ran` is the number of tests that
actually executed. All 48 returned **exit 0 with `Ran > 0`**.

| Plan | Wave | Requirement | Secure behavior | Type | Command (node id unless marked PREFIX) | Ran | Shipped | Status |
|------|------|-------------|-----------------|------|----------------------------------------|-----|---------|--------|
| 21-04 | 2 | UNIT-02 | N/A | golden fixture | `tests/test_phase21_aligned_bins.py::test_build_bins_byte_identity_default_matches_the_v2_golden` | 1 | `a3fe2ab` | ✅ green |
| 21-04 | 2 | UNIT-02 | N/A | golden fixture | `tests/test_phase21_aligned_bins.py::test_build_bins_byte_identity_omitted_equals_align_facts_none` | 1 | `a3fe2ab` | ✅ green |
| 21-04 | 2 | UNIT-02 | identity claim cannot be vacuous | unit (non-vacuity) | `tests/test_phase21_aligned_bins.py::test_align_facts_is_wired` | 1 | `a3fe2ab` | ✅ green |
| 21-04 | 2 | UNIT-02 | `space="input"` is the DEFAULT (no union mode) | content | `tests/test_phase21_aligned_bins.py::test_window_purity_input_is_the_default` | 1 | `a3fe2ab` | ✅ green |
| 21-04 | 2 | UNIT-02 | `n_facts − 1` boundary rows, stated POSITIVELY | content | `tests/test_phase21_aligned_bins.py::test_window_purity_target_boundary_rows_are_a_positive_claim` | 1 | `a3fe2ab` | ✅ green |
| 21-04 | 2 | UNIT-02 | A0–A5 adversaries caught | adversarial | `tests/test_phase21_aligned_bins.py::test_window_purity_adversaries_input_space` | 5 | `a3fe2ab` | ✅ green |
| 21-04 | 2 | UNIT-02 | A4 length violation RAISES | adversarial | `tests/test_phase21_aligned_bins.py::test_window_purity_adversaries_a4_raises_on_length` | 1 | `a3fe2ab` | ✅ green |
| 21-04 | 2 | UNIT-02 | token/mask/fact bins 1:1 | unit | `tests/test_phase21_aligned_bins.py::test_three_bin_alignment_is_1to1` | 1 | `a3fe2ab` | ✅ green |
| 21-04 | 2 | UNIT-02 | truncation refused in BOTH spaces | unit | `tests/test_phase21_aligned_bins.py::test_three_bin_alignment_truncation_raises_in_both_spaces` | 1 | `a3fe2ab` | ✅ green |
| 21-06 | 3 | UNIT-02 | `grad_accum_steps == n_facts` OBSERVED, not configured | integration | `tests/test_phase21_aligned_loader.py::test_grad_accum_steps_equals_n_facts` | 1 | `ef2dd4a` | ✅ green |
| 21-06 | 3 | UNIT-02 (D-06) | fact map read on EVERY access | adversarial | `tests/test_phase21_aligned_loader.py::test_fact_map_is_consumed_at_runtime` | 1 | `ef2dd4a` | ✅ green |
| 21-06 | 3 | UNIT-02 (D-06) | loader RAISES on missing/truncated fact bin, **distinguishably** | unit | `tests/test_phase21_aligned_loader.py::test_fact_bin_required_raises_distinguishably` | 2 | `ef2dd4a` | ✅ green |
| 21-06 | 3 | UNIT-02 (**CR-01**) | whole-bin length contract enforced at DRAW time | adversarial | `tests/test_phase21_aligned_loader.py::test_n7_all_three_bins_truncated_together_is_refused` | 1 | CR-01 fix | ✅ green |
| 21-10 | 4 | UNIT-03 | counts conserve against their own denominator | unit | `tests/test_phase21_multiplicity.py::test_conservation` | 3 | `f1e8677` | ✅ green |
| 21-10 | 4 | UNIT-03 | conserves at the REAL budget too | unit | `tests/test_phase21_multiplicity.py::test_conservation_holds_at_the_real_budget_denominator` | 1 | `f1e8677` | ✅ green |
| 21-10 | 4 | UNIT-03 | aligned branch conserves | unit | `tests/test_phase21_multiplicity.py::test_aligned_conservation` | 1 | `f1e8677` | ✅ green |
| 21-10 | 4 | UNIT-03 | instrument CAN report ≠ 1 (with a negative control) | adversarial | `tests/test_phase21_multiplicity.py::test_instrument_can_report_not_one` | 2 | `f1e8677` | ✅ green |
| 21-10 | 4 | UNIT-03 | SEED=1337 reproduces | unit | `tests/test_phase21_multiplicity.py::test_seed_reproducible` | 1 | `f1e8677` | ✅ green |
| 21-10 | 4 | UNIT-03 | every row carries its OWN denominator | content | `tests/test_phase21_multiplicity.py::test_row_carries_its_denominator` | 1 | `f1e8677` | ✅ green |
| 21-10 | 4 | UNIT-03 | validated against 4 independent oracles | oracle — **PREFIX**, means all 4 oracle tests | `tests/test_phase21_multiplicity.py -k oracle` | 4 | `f1e8677` | ✅ green |
| 21-08 | 3 | UNIT-04 (D-11) | replay volume independent of private fact VALUES | differential | `tests/test_phase21_replay_volume.py::test_side_channel_closed` | 1 | `f756474` | ✅ green |
| 21-08 | 3 | UNIT-04 (D-11) | the differential's live negative control | differential | `tests/test_phase21_replay_volume.py::test_side_channel_negative_control` | 1 | `f756474` | ✅ green |
| 21-08 | 3 | UNIT-04 (D-24) | budget quantized to whole windows at n=8 AND n=64 | unit | `tests/test_phase21_replay_volume.py::test_window_quantized` | 2 | `f756474` | ✅ green |
| 21-01 | 1 | UNIT-01/04/05 | δ clears its own ceiling at N=8 and N=64 | unit | `tests/test_phase21_unit_pin.py::test_prove_guards_pinned_delta_clears_the_ceiling` | 2 | `7347472` | ✅ green |
| 21-01 | 1 | UNIT-05 | the REJECTED `1/N^1.1` recipe fails its own ceiling | unit | `tests/test_phase21_unit_pin.py::test_prove_guards_rejected_recipe_fails_its_own_ceiling` | 2 | `7347472` | ✅ green |
| 21-01 | 1 | UNIT-05 | the rejection ratio is published, not asserted | unit | `tests/test_phase21_unit_pin.py::test_prove_guards_rejected_ratio_to_ceiling` | 2 | `7347472` | ✅ green |
| 21-01 | 1 | UNIT-01 | frozen module imports ⊆ `{pathlib, sys, erasure_gate}` | AST | `tests/test_phase21_unit_pin.py::test_pin_imports_nothing` | 1 | `7347472` | ✅ green |
| 21-01 | 1 | UNIT-01 | the same AST rule on the gate module | AST | `tests/test_phase20_prereg.py::test_mitigation_gate_import_graph_is_stdlib_and_erasure_gate_only` | 1 | pre-existing | ✅ green |
| 21-01 / 21-11 | 1 / 6 | UNIT-01/04/05 (D-20) | guard armed BEFORE the first artifact | git history | `tests/test_phase20_prereg.py::test_phase21_prereg_is_frozen_before_every_phase21_result` | 1 | `21ed755` → `d32b51a` | ✅ green |
| 21-03 | 2 | UNIT-01/04/05 | the guard is LIVE — `checked == 2`, both non-zero | git history | `tests/test_phase20_prereg.py::test_phase21_guard_is_now_live` | 1 | `76926ef` | ✅ green |
| 21-03 | 2 | UNIT-01/04/05 | guard proven non-vacuous, RED then GREEN | git fixture | `tests/test_phase20_prereg.py::test_phase21_glob_sees_the_phase21_prefix_red_then_green` | 1 | `76926ef` | ✅ green — **selector corrected, see IN-03** |
| gap `9a407d6` | — | UNIT-01 (**WR-04**) | `privacy_n` refuses float / str / 0 / negative / bool | unit | `tests/test_phase21_unit_continuation.py::test_the_continuation_refuses_what_the_pin_admits` | 3 | `9a407d6` | ✅ green |
| gap `9a407d6` | — | UNIT-01 (**WR-04**) | no module reaches the pin's `privacy_n` — AST census | AST | `tests/test_phase21_unit_continuation.py::test_privacy_n_has_no_route_through_the_pin_outside_this_module` | 1 | `9a407d6` | ✅ green |
| 21-05 | 2 | UNIT-06 (D-16) | `render_family` byte-identical, both registers | golden fixture | `tests/test_phase21_filler.py::test_render_family_byte_identity` | 2 | `ab81800` | ✅ green |
| 21-05 | 2 | UNIT-06 (D-16) | `forms=` is READ — the identity claim is falsifiable | unit (non-vacuity) | `tests/test_phase21_filler.py::test_forms_is_wired` | 2 | `ab81800` | ✅ green |
| 21-07 | 3 | UNIT-06 (D-16) | filler slots DISJOINT from the 11 published slots | unit | `tests/test_phase21_filler.py::test_slots_disjoint` | 1 | `fe9cabe` | ✅ green |
| 21-07 | 3 | UNIT-06 (D-17) | collision refusal vs the 10, the 28, and each other | unit | `tests/test_phase21_filler.py::test_minting_discipline` | 1 | `fe9cabe` | ✅ green |
| 21-07 | 3 | UNIT-06 (D-13) | filler OUTSIDE `all_pools()`; `_BY_ID` gains no keys | unit | `tests/test_phase21_filler.py::test_outside_all_pools` | 1 | `fe9cabe` | ✅ green |
| 21-07 | 3 | UNIT-06 | render order stable ACROSS PROCESSES (frozenset fix) | unit | `tests/test_phase21_filler.py::test_render_filler_episodes_is_order_stable` | 1 | `fe9cabe` | ✅ green |
| 21-09 | 5 | UNIT-06 / SC5 (D-18) | no filler value reaches any published instrument | content | `tests/test_phase21_sc5.py::test_no_filler_leak` | 1 | `3941236` | ✅ green |
| 21-09 | 5 | UNIT-06 / SC5 | `scripts/phase18_extraction.py` **and** the 270-question fixture byte-unchanged — BOTH sha256 pins are in this one test | sha256 | `tests/test_phase21_sc5.py::test_instruments_unchanged_byte_for_byte` | 1 | `3941236` | ✅ green |
| 21-09 | 5 | UNIT-06 / SC5 | the `== 10` wall census is the MEASURED set, mechanically | census | `tests/test_phase21_sc5.py::test_wall_census_is_the_measured_set` | 1 | `3941236` | ✅ green |
| 21-09 | 5 | UNIT-06 / SC5 | tier composition pinned by EQUALITY, not `<=` | unit | `tests/test_phase21_sc5.py::test_locked_and_soft_tiers_are_unmoved` | 1 | `3941236` | ✅ green |
| 21-09 | 5 | UNIT-06 / SC5 | all **11** `== 10` wall sites still green | existing | the **SC5 guard set** command above | 364 | pre-existing | ✅ green |
| — | — | UNIT-06 / SC5 | `len(LOCKED_FACTS) <= 8`, `len(SOFT_TIER_FACTS) <= 3` | existing | `tests/test_phase14_factset.py::test_composition_targets` | 1 | pre-existing | ✅ green |
| — | — | all (RPT-03) | `pyproject.toml` untouched — zero new deps | sha256 | `tests/test_package.py` | 3 | pre-existing | ✅ green |
| — | — | sampling | the quick run | suite | `tests/test_phase20_prereg.py tests/test_package.py tests/test_masked_batch.py tests/test_phase14_teaching.py` | 70 | — | ✅ green |
| — | — | sampling | the SC5 guard set (10 files) | suite | see Test Infrastructure above | 364 | — | ✅ green |
| — | — | sampling | the whole Phase-21 family — **PREFIX**, means every test whose id contains `phase21` | suite | `-k phase21` | 142 | — | ✅ green |

**48 commands · 48 PASS (exit 0 AND `Ran > 0`) · 0 FAIL.** Executed 2026-08-25 by a mechanical loop
that took each exit code from `subprocess.returncode` and parsed the ran-count out of pytest's own
summary line; a command that collected zero tests would have been recorded FAIL even at exit 0.

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

### The `== 10` wall is 11 sites across 8 files — every earlier figure in this file was low

This file previously claimed **8 across 7**. That is superseded. 21-07 censused the wall
mechanically with **three independent grep patterns** (a bare `== 10\b` sweep plus two
variable-shaped patterns) and measured **11 sites across 8 files** — and, unlike every prior count,
that census is now a **shipped, executable test** rather than a table in a document:
`tests/test_phase21_sc5.py::test_wall_census_is_the_measured_set`, whose `_EXPECTED_WALL` at
`tests/test_phase21_sc5.py:217-231` is the list below. Confirmed independently during this closure
by `grep -n "== 10" tests/*.py`.

| # | Site | Assertion |
|---|------|-----------|
| 1 | `tests/test_phase14_scoring.py:405` | `len(forbidden) == 10` |
| 2 | `tests/test_phase14_demo.py:394` | `len(values) == 10` |
| 3 | **`tests/test_phase14_demo.py:568`** | `len(result["values"]) == 10` |
| 4 | `tests/test_phase16_driver.py:313` | `len(forbidden) == 10` |
| 5 | `tests/test_phase16_ladder.py:443` | `len(forbidden) == 10` |
| 6 | `tests/test_phase16_ladder.py:711` | `len(forbidden) == 10` |
| 7 | `tests/test_phase18_prereg.py:127` | `len(forbidden) == 10` |
| 8 | `tests/test_phase18_corpus.py:430` | `len(values) == 10` |
| 9 | `tests/test_phase19_erasure.py:625` | `len(forbidden) == 10` |
| 10 | **`tests/test_phase19_erasure.py:1689`** | `taught == 10` |
| 11 | **`tests/test_phase21_filler.py:165`** | `len(fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS) == 10` (added by 21-05) |

**How the figure drifted, and the correction to the correction.** The trail is
`21-CONTEXT.md` D-18 → **4**; `21-RESEARCH.md` → **7 across 6**; plan-check pass 1 → **8 across 7**
(the table this section replaces); plan-check pass 3 → **9**; 21-07's mechanical census → **11
across 8**.

> **One claim carried into this closure task was falsified and is not passed through.** The two sites
> said to "appear in no document" were `tests/test_phase16_ladder.py:711` and
> `tests/test_phase19_erasure.py:625`. Both were already rows 4 and 6 of *this file's own* superseded
> 8-site table. The three sites genuinely absent from it are the **bolded** rows above —
> `test_phase14_demo.py:568`, `test_phase19_erasure.py:1689` and `test_phase21_filler.py:165`.
> Recorded rather than quietly fixed, because "a documented figure is low" is the finding, and
> replacing one wrong attribution with another would be the same defect.

`test_phase14_demo.py:568` deserves its own line: this file previously recorded it as "a ninth
`== 10` assertion … it matches NEITHER census grep pattern, so the 8/7 count stays internally
consistent." The three-pattern census **does** match it, so that consistency argument is void — the
site was always part of the wall and the old two-pattern census simply could not see it.

**Three further sites of the same class exist and are deliberately outside the census, each for a
stated reason** — recorded so the next reader meets them as known facts rather than as regressions:

| Site | Why excluded |
|---|---|
| `tests/test_phase21_sc5.py:100` (`len(scored) == 10`) | the census's OWN file, excluded by a mechanical `__file__` check so it cannot discover itself |
| `scripts/phase21_filler.py:262` (`len(FORBIDDEN_SCORED_VALUES) == 10`) | outside `tests/`; the census walks `tests/` only. **This one is WR-06 and is still OPEN:** it is a strippable `assert`, verified live — `python -O -c 'import phase21_filler'` imports clean |
| `tests/test_phase16_ladder.py:232`, `test_phase15_stats.py:127`, `test_phase21_multiplicity.py:298` | `== 10` matches that are not leak-vocabulary claims; listed with their reasons in `_NOT_WALL_SITES` (`tests/test_phase21_sc5.py:202-213`) |

`tests/test_phase14_demo.py`, `tests/test_phase21_filler.py` and `tests/test_phase21_multiplicity.py`
are therefore all in the SC5 guard set above, and `tests/test_phase21_sc5.py:286` asserts that
membership mechanically.

---

## Wave 0 Requirements

**All ten landed.** `Shipped` is the commit that ADDED the file, from `git log --diff-filter=A`.

- [x] `tests/test_phase21_aligned_bins.py` — UNIT-02 content proofs + `build_bins` golden fixture — `a3fe2ab` (21-04), 23 tests
- [x] `tests/test_phase21_aligned_loader.py` — UNIT-02 / D-06 run-time consumption proofs — `ef2dd4a` (21-06), 11 tests
- [x] `tests/test_phase21_multiplicity.py` — UNIT-03 instrument validation — `f1e8677` (21-10), 17 tests
- [x] `tests/test_phase21_replay_volume.py` — UNIT-04 / D-11 / D-24 side-channel differential — `f756474` (21-08), 13 tests
- [x] `tests/test_phase21_unit_pin.py` — the frozen module's `_prove` guards — `7347472` (21-01), 11 tests
- [x] `tests/test_phase21_filler.py` — UNIT-06 corpus + `render_family` golden fixture — `ab81800` (21-05), 13 tests
- [x] `tests/test_phase21_sc5.py` — SC5 non-disturbance — `3941236` (21-09), 4 tests
- [x] `tests/fixtures/golden_build_bins_v2.json` — captured from a **git-clean, pre-edit**
      `teach_persona.py` — `a18f675` (21-02). The pre-edit constraint was enforced mechanically, not
      by convention: `scripts/phase21_golden_capture.py` calls `_refuse_if_dirty()` at module scope
      (`:147`, BEFORE the sibling imports) and again at call time (`:263`).
- [x] `tests/fixtures/golden_render_family_v2.json` — captured pre-edit from `phase14_factset.py` —
      `4e2ce1a` (21-02), same refusal.
- [x] **Two additive edits to `tests/test_phase20_prereg.py`** (D-20) — `V4_ARTIFACT_GLOBS` at
      `tests/test_phase20_prereg.py:130` **and** the `artifact_glob="results/phase21_*"` ordering
      call. Both landed at `21ed755` (21-01); `76926ef` (21-03) proved the glob non-vacuous and
      `d32b51a` (21-11) closed the reflexivity gap.

**Held: no new framework, no new fixture infrastructure, no conftest change, no new dependency.**
`tests/test_package.py` (3 tests, exit 0) pins `pyproject.toml` by sha256 — RPT-03 makes four
milestones.

**Two files were added beyond the ten, both recorded rather than smuggled in:**
`tests/test_phase21_unit_record.py` (`17b3c85`, 21-11 — the emitters, 17 tests) and
`tests/test_phase21_unit_continuation.py` (`9a407d6` — WR-04's dated continuation, 30 tests).

Per-file counts measured by `pytest --collect-only -q`, not hand-counted: **139 tests** across the
nine `tests/test_phase21_*.py` files. The `-k phase21` PREFIX row in the map reports **142**, and
the difference is not slack — it is the 3 `test_phase21_*` tests that live in
`tests/test_phase20_prereg.py` (`test_phase21_prereg_is_frozen_before_every_phase21_result`,
`test_phase21_guard_is_now_live`, `test_phase21_glob_sees_the_phase21_prefix_red_then_green`),
enumerated to confirm the decomposition rather than assumed from the totals matching.

### The governing rule for every byte-identity proof in this phase

> **A byte-identity assertion with no paired non-identity assertion is vacuous.** `X=None` is
> trivially satisfied by a kwarg that is never read.

Every `*_byte_identity` row above is therefore paired with an `*_is_wired` row that fails if the
kwarg is inert. This is not redundancy — it is the only thing that makes the identity claim mean
anything. **RESEARCH.md Open Question 1 is a live instance:** `render_family(...,
question_bank=None)` appears **unfalsifiable as sited** — `SLOT_QUESTION_BANK` is read only at
`phase14_factset.py:279` inside `_assign_probes()`, and `_render_family:690` reads only
`SLOT_FORMS`, so no value of that kwarg can change `render_family`'s output. The planner must
either re-site the kwarg or drop it; it must not ship a guard that cannot fail.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions | OUTCOME (measured 2026-08-25) |
|----------|-------------|------------|-------------------|-------------------------------|
| Arm-then-write commit ORDER for the ancestry guard | UNIT-01/04/05 (D-20) | The property is over **git history**, not over a working tree. A test can assert the ordering holds, but only the operator controls which commit lands first — and `:157` (`adds[-1]`) makes a wrong order permanent. | Land the two `test_phase20_prereg.py` edits GREEN in a commit that is a strict ancestor of the first `results/phase21_*` commit. Verify with `git merge-base --is-ancestor <pin-commit> <artifact-commit>` before committing any artifact. Note `:300-304`: `--is-ancestor X X` exits 0, so same-commit PASSES the mechanism — "strictly after" is a tighter discipline than the guard enforces, and it is deliberate. | ✅ **HELD, and STRICTLY.** Pin `scripts/mitigation_unit.py` added at **`8d3beb4`**; both artifacts first added at **`c79b9bf`**. `git merge-base --is-ancestor 8d3beb4 c79b9bf` → **exit 0**, and `8d3beb4 != c79b9bf`, so BOTH conjuncts hold — the order is strictly-after, not merely same-commit. The guard is LIVE, not vacuous: 1 pin × 2 tracked artifacts = **`checked = 2`**, both non-zero. `adds` has exactly ONE entry per artifact, so the CR-02 re-emit at `eba0571` did not move the first-add and no delete-and-re-add laundering occurred. Independently recomputed by `21-VERIFICATION.md:65` and again during this closure. |
| `results/phase21_*` artifacts are COMMITTED, not merely written | UNIT-03 (D-26) | `git ls-files` is the guard's input. `results/` is not gitignored, but an uncommitted artifact is invisible to the guard — a silent no-op, not a failure. | After the driver writes, confirm `git ls-files results/phase21_*` is non-empty before claiming the guard covers them. | ✅ **HELD.** `git ls-files 'results/phase21_*'` returns both `results/phase21_multiplicity.json` and `results/phase21_privacy_unit.json` — non-empty, so the guard has real input. Belt-and-braces added during execution: `provenance.refuse_if_dirty` (`scripts/phase21_emit.py:77`) makes a dirty-tree publication a `SystemExit` rather than a `git_sha` the tree cannot reproduce — that was CR-02, and the guard was **watched firing** on an untracked file. |
| CI is not shallow | UNIT-01/04/05 (D-20) | `_assert_ordering_holds` asserts `rev-parse --is-shallow-repository == "false"` and REFUSES to skip (`tests/test_phase20_prereg.py:136-141`), so a shallow clone turns the guard into an error rather than a silent pass. Whether CI checks out deep is a workflow-file property. | `.github/workflows/ci.yml:21` must set `fetch-depth: 0`. | ✅ **HELD.** `git rev-parse --is-shallow-repository` → `false` here. Row added during closure because the prerequisite was stated in prose at `## Test Infrastructure` but had no row of its own. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies — **29/29 tasks; zero MISSING markers**
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references — all 10 artifacts owned by a named plan (aligned_bins→21-04, aligned_loader→21-06, multiplicity→21-10, replay_volume→21-08, unit_pin→21-01, filler→21-05/21-07, sc5→21-09, both goldens→21-02, both `test_phase20_prereg.py` edits→21-01)
- [x] Every `*_byte_identity` test is paired with a non-vacuity `*_is_wired` test — `question_bank` was **dropped** rather than shipped unfalsifiable (21-05)
- [x] Every new guard proven **deliberate-RED then byte-identically restored**
- [x] No watch-mode flags — task-granularity commands run 1.9s–36s
- [x] Feedback latency < 36s
- [x] `nyquist_compliant: true` set in frontmatter

`wave_0_complete` was **false** by design at planning time: the ten Wave 0 files were *planned and
owned*, not yet written. **It is now `true`** — all ten landed, each with the commit that added it
recorded above. It flipped during execution, exactly as this line said it would.

### Wave structure — SIX waves, not five

Plan 21-09 was moved from wave 4 to **wave 5**, and 21-11 from wave 5 to **wave 6**. Reason, recorded
here because it is a validation-integrity fact and not a scheduling preference: 21-09's three
deliberate-REDs transiently mutate WORKING-TREE files it does not own — `scripts/phase14_factset.py`
(21-05's), `scripts/phase21_filler.py` (21-07's) and the ancestry-guarded
`scripts/phase18_extraction.py` (nobody's). Same-wave 21-10 runs the FULL SUITE and
`git diff --exit-code scripts/phase18_extraction.py` in its `<verification>` block. A canary live
during a concurrent reader is a flake attributed to the innocent plan, and `files_modified` cannot
prevent it because the plan that READS a file need not DECLARE it. An explicit `depends_on: 21-10`
edge on 21-09 serializes them; the three guarded/non-owned paths were removed from 21-09's
`files_modified` so that listing them can no longer read as permission to edit.

| Wave | Plans |
|------|-------|
| 1 | 21-01, 21-02 |
| 2 | 21-03, 21-04, 21-05 |
| 3 | 21-06, 21-07, 21-08 |
| 4 | 21-10 |
| 5 | 21-09 |
| 6 | 21-11 |

---

## Approval

**RE-VERIFIED 2026-08-22**, against the plan set produced by the blocker-fix revision on top of
`9cc2c94`. This is the CURRENT set and it is the one this document covers.

**The earlier line is superseded and was stale.** It read *"approved 2026-08-22 — plan set `fc2e6dc`,
verified by `gsd-plan-checker` (0 blockers)"*. Six plans — 21-04, 21-06, 21-08, 21-09, 21-10, 21-11 —
changed after `fc2e6dc` (`git diff --stat fc2e6dc..HEAD`), so that approval never covered the set
subsequently reviewed. It is retained here as a corrected record rather than deleted, because a
sign-off quietly overwritten is indistinguishable from one that was always right.

**And the "0 blockers" claim was false of the set it was later read against.** A `gsd-plan-checker`
pass over the post-`fc2e6dc` set returned **1 blocker and 7 warnings**. All eight were closed by this
revision:

| # | Severity | Finding | Closed by |
|---|----------|---------|-----------|
| 1 | **BLOCKER** | `fact_window_impurities` defaulted to `space="both"` (the UNION), which refuses every CORRECTLY built bin — measured `[]` in input space but `[1, 2]` in target space on the plan's own A0 fixture, so proof-7 would abort every aligned build. The stated padding justification was also false: the boundary crossing is a property of the +1 label shift, not of padding. | 21-04, 21-06 — default is `space="input"` (SC2's own wording), no union mode; the target-space claim is restated POSITIVELY as `n_facts - 1` boundary rows with every boundary token's mask asserted 0 |
| 2 | warning | 21-09's transient mutation of ancestry-guarded / non-owned files could flake same-wave 21-10 | 21-09 → wave 5 behind 21-10; guarded paths removed from `files_modified`; 21-11 → wave 6 |
| 3 | warning | `count_aligned` could not obtain `per_step_distinct_facts` — the loader raises first, and neither offered route was pinned | 21-10 pins `strict=True` in the signature; `strict=False` reuses 21-06's newly EXPORTED `fact_window_span`, so it is not a re-implementation |
| 4 | warning | `render_filler_episodes` omitted `sorted()` over a frozenset — measured three different orders in three processes | 21-07 mirrors `teach_persona.py:251`; a cross-process digest test and a deliberate-RED were added |
| 5 | warning | 21-07 asserted an unmeasured `56 * 22 == 1232` | 21-07 marks it an ESTIMATE with a record-and-STOP clause; the binding assertion is EQUALITY with a scored fact's observed count inside `PARAPHRASES_PER_FACT_TARGET` |
| 6 | warning | 21-04's aligned branch left `episodes` undefined while `stats["episodes"]` still reported it | 21-04 pins `episodes=[]` on the aligned branch, raises on ambiguous non-empty input, and defines the key as the pairs' row total |
| 7 | warning | five stale line references | corrected in 21-02, 21-05, 21-07, 21-09 — every one re-verified against the repo before writing |
| 8 | warning | this sign-off was stale | this section |

### Re-check pass 2 — the blocker CLOSED, three regressions found and fixed

The revision above was re-checked. The blocker is **closed and independently confirmed**: the
checker rebuilt the real 8-fact bin at `block_size = 256` and measured input space `[]`, target space
`[3, 7, 11, 15, 19, 24, 28]` = exactly 7 = `n_facts - 1`, `fact_ids[(k+1)*256] == fact_ids[k*256] + 1`
at all seven, and `serialize.py:81` verbatim. W2 and W4-W8 all confirmed closed.

That pass found **three NEW warnings, every one introduced by the revision itself**. Recorded here
rather than silently repaired, because a revision that fixes a blocker and quietly adds three
regressions is the failure mode this phase exists to make visible:

| # | Severity | Regression the revision introduced | Closed by |
|---|----------|------------------------------------|-----------|
| A | blocker-adjacent | The W3 fix put only the LOADER call inside `try/except`, but plan 21-06 requires `fact_window_span` to raise on non-contiguous rows — and task 3's roll-by-1 makes fact index 7 non-contiguous (measured: rows `[0, 30, 31, 32]`). `count_aligned(strict=False)` therefore aborted out of the SPAN call at step 7, i.e. on any run with `steps >= n_facts`, which is exactly the full lot task 3 runs. The fix aborted on the very adversary it was written to observe. | 21-10 — BOTH calls in ONE `try/except ValueError`; `per_step_raised` records `"span"` as its own outcome class; task 3 pins `steps >= n_facts` and asserts a `"span"` entry is present. `fact_window_span`'s contiguity raise is explicitly NOT relaxed |
| B | warning | Five threat IDs minted by the revision (T-21-50…54 in 21-04 / 21-06 / 21-10) each collided with an unrelated threat plan 21-11 already held, breaking the register's own convention that a shared ID means the SAME threat | renumbered to **T-21-59…63**; 21-11 untouched. The separately double-booked pre-existing **T-21-49** was also fixed: 21-10's became **T-21-64** (21-11 keeps T-21-49), stated in 21-10's register |
| C | warning | A stray duplicate `</output>` closing tag in five plans | deleted from 21-04, 21-06, 21-07, 21-09, 21-10; the six already-balanced plans untouched. All 11 now 1/1 |

Two non-blocking notes were also addressed: every downstream plan citing a file plan 21-04 or 21-08
rewrites (**21-06, 21-08, 21-09, 21-10**) now carries a `LINE ANCHORS: resolve BY SYMBOL` paragraph,
because those anchors are correct only against the PRE-wave-2 tree; and 21-06 task 1's acceptance
criterion now says out loud that `tests/test_phase21_aligned_loader.py` is created in task 2 and the
criterion closes there.

**Threat register invariant, stated precisely — the earlier wording here was overstated and is
corrected.** It read *"across all 11 plans, every `T-21-NN` denotes exactly one threat"*, which is
false at the literal level for two pre-existing IDs. The accurate claim: **every ID denotes one
threat CLASS, instantiated per component.** Shared IDs and their classes:

| ID | Class | Sites |
|----|-------|-------|
| T-21-03 | the pin is not actually in force when an artifact lands | 21-01 (post-hoc edit), 21-03 (glob silently reverted), 21-11 (artifact committed before the pin) |
| T-21-04 | a value or edit moves a published instrument | 21-05 (edit moves a row), 21-07 / 21-09 (filler value enters the leak vocabulary) |
| T-21-05 | a guard that cannot fail | 21-01, 21-02, 21-03, 21-04, 21-05 |
| T-21-06 | ancestry laundering by delete-and-re-add | 21-01, 21-03, 21-11 |
| T-21-08 | an edit reaches a frozen file | 21-05, 21-07, 21-09 |
| T-21-11 | supply chain | all 11 |
| T-21-15 | a test depends on machine-local `data/` | 21-02, 21-08 |
| T-21-20 | correct offsets over wrong bytes | 21-04, 21-06 |
| T-21-24 | a test writes into `data/` | 21-04, 21-06 |

T-21-03 and T-21-04 are the two the earlier sentence got wrong; both patterns are identical at HEAD,
i.e. pre-existing convention rather than anything this revision introduced. What IS newly true and
was the actual defect fixed in pass 2: no ID denotes two UNRELATED threats. High-water mark:
**T-21-65**.

### Re-check pass 3 — VERIFICATION PASSED, then four warnings closed

Check 3 returned **`## VERIFICATION PASSED`, 0 blockers, and no third generation of regressions.**
W-A, W-B, W-C and both notes were confirmed closed against the files rather than against the summary;
both sha256 pins re-verified live; the δ arithmetic re-run in `.venv`; the 7-boundary target-space
count re-derived from D-01's geometry; waves, graph, collisions, UNIT-01…06, D-01…D-26 and Nyquist
all clean.

Four warnings survived that pass and were closed afterward. **Two were pre-existing at HEAD and two
came from the revisions** — recorded that way because which is which is the only part a reader
cannot reconstruct later:

| # | Origin | Finding | Closed by |
|---|--------|---------|-----------|
| W1 | **introduced by revision 2** | `count_aligned(strict=False)` never pinned that `np.unique` must run BEFORE the loader call, and one `try` gave no way to tell `"span"` from `"loader"`. MEASURED on the rolled bin: **all 8 steps raise** — the loader raises impurity at steps 0-6 (fact 0 owns rows `[1,2,3,4]`; row 4 = `rolled[1024:1280]` = `original[1023:1279]` carries facts 0 and 1) and the span raises at step 7. Unique-after-loader ⇒ `per_step_distinct_facts == [None]*8` ⇒ task 3's `max(...)` dies with `max() arg is an empty sequence`, i.e. the non-vacuity test ERRORS. | 21-10 task 1 — order pinned (`np.unique` immediately after `fact_window_span`, strictly before the loader) plus a `stage` local (`"span"`→`"loader"`) that the single `except` records as `per_step_raised` |
| W2 | **hazard fixed twice, missed here** | Wave 3 carried the exact hazard 21-09 was serialized out of wave 4 to remove: all three of 21-06 / 21-07 / 21-08 ran a bare `pytest -q` (`testpaths = ["tests"]`) while each held a live working-tree deliberate-RED a sibling's run would collect — including 21-06's full suite collecting `tests/test_phase21_replay_volume.py`, which 21-08 is deliberately reddening | scoped, not serialized: the six per-plan full-suite invocations in 21-06 / 21-07 / 21-08 were replaced with explicit file lists plus a note that the full suite is a WAVE-CLOSE / `/gsd:verify-work` gate — which `:47` and `:52` above already said. **Wave 3 stays parallel; no `depends_on`, `wave` or ROADMAP change.** Waves 1 and 2 were audited for the same pattern and are clean (transient mutations, zero full-suite runs); waves 4-6 are single-plan |
| W3 | **pre-existing at HEAD** | `test_wall_census_is_eight_sites` was specified to FAIL: the same task requires `test_phase21_sc5.py` to carry `len(forbidden) == 10`, while the census greps for exactly that and asserts 8 sites / 7 files with an explicit instruction not to adjust the number. Measured: 8/7 today, 9/8 with the new file | 21-09 — mechanical `__file__` exclusion in the walk (not a comment), with the reason stated: the census measures the PRE-EXISTING wall. The re-siting alternative (21-05's non-matching `len(fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS) == 10` form) was rejected for dodging the grep by accident of phrasing |
| W4 | **pre-existing convention, overstated by revision 2** | The pass-2 paragraph claimed every `T-21-NN` denotes exactly one threat. False for `T-21-03` (three sites) and `T-21-04` (two) | the paragraph above, rewritten as a threat-CLASS table naming all nine shared IDs. Nothing renumbered |

~~**A ninth `== 10` assertion exists and is now recorded** (INFO, surfaced by check 3):
`tests/test_phase14_demo.py:568` — `assert len(result["values"]) == 10`. It matches NEITHER census
grep pattern, so the 8/7 count stays internally consistent, and it IS executed because the SC5 guard
set runs that whole file.~~

> **SUPERSEDED 2026-08-25 — struck through rather than deleted.** The site is real and the guard-set
> half is right, but the "matches NEITHER census grep pattern, so 8/7 stays internally consistent"
> reasoning is **void**: 21-07's three-pattern census DOES match it. It is site 3 of 11 in the
> measured wall (`### The == 10 wall is 11 sites across 8 files` above). The 8/7 figure was low, not
> internally consistent — it was consistent only with a census that could not see this row. It is
> written into 21-09's census docstring and, better, into the executable `_EXPECTED_WALL`.

~~**Status: revised three times, awaiting re-check.**~~ Superseded by `## Closure` below: the phase
executed and was verified, so the plan set is no longer the thing awaiting a check.

---

## Closure

**Closed 2026-08-25** as UAT decision 4 (the documentation ledger). `status:` in the frontmatter is
now `closed` and refers to THIS DOCUMENT, not to the phase.

### What was actually verified

| Check | Result |
|---|---|
| Commands in this file executed, not typed | **48 / 48 PASS** — exit 0 AND non-zero collection, every one |
| Single-test rows converted to explicit node ids | 45 of 48; the 3 exceptions are marked **PREFIX** in the map and say what family they mean |
| Every node id cited across this file, `21-REVIEW.md` and `REQUIREMENTS.md`, re-extracted **from the documents** and run | **62 / 63 PASS**; the 1 FAIL is the deliberate wrong-node-id example above, which is *supposed* to exit 4 — it is the sweep's own negative control |
| Full suite | `1024 passed, 1 skipped` binding on a full checkout; `1018 passed, 7 skipped` here — **1,025 collected either way** |
| `ruff check .` / `ruff format --check .` | clean |
| `scripts/mitigation_unit.py` (frozen pin) | `sha256 45f37e15…` — **unchanged** |
| `results/phase21_privacy_unit.json` | `sha256 84d8f3bd…` — **unchanged** |
| `results/phase21_multiplicity.json` | `sha256 e9e3b9bf…` — **unchanged** |
| `.planning/STATE.md`, `.planning/ROADMAP.md` | untouched |

### What this closure does NOT claim

**The phase is not complete and did not pass.** `21-VERIFICATION.md` returned **`human_needed`** at
6/6 must-haves — the goal is achieved and the evidence is reproducible, but the report withheld
`passed` deliberately. Still open from `21-REVIEW.md`, unchanged by this closure:

| ID | Severity | Still open? | One line |
|---|---|---|---|
| CR-01, CR-02, WR-01, WR-02 | critical / warning | **CLOSED** | closure records in `21-REVIEW.md`, re-measured by the verifier |
| WR-04 | warning | **CLOSED** at `9a407d6` | `privacy_n` validated in a dated continuation + an AST import census |
| WR-03 | warning | **OPEN** | `scripts/teach_persona.py:162-163` states 49.90% at n=64; the phase's own artifact records `documented_n64_claim_holds: false` and `0.44755244755244755` |
| WR-05 | warning | **OPEN** | a headline artifact "finding" is an arithmetic identity the same artifact elsewhere disclaims |
| WR-06 | warning | **OPEN** | `scripts/phase21_filler.py:262`'s `== 10` wall is a strippable `assert`; `python -O` imports it clean |
| WR-07 | warning | **OPEN** | the frozen pin attributes a systematic rule gap to "sampling noise" |
| IN-01, IN-02 | info | **OPEN** | a tautological `_prove`; stale line anchors — both inside the frozen pin |
| IN-03 | info | **CLOSED here** | the dead `-k` selector: this document was its only home |
| IN-04 | info | **OPEN** | the replay seam has no production caller — a declared Phase-22 seam |

Nothing above was closed by writing this document except IN-03, which was a defect *in* this
document.

### IN-03 — closed, and the framing corrected

The finding is real: `-k phase21_glob_red_then_green` collects **zero** tests, because the real name
is `test_phase21_glob_sees_the_phase21_prefix_red_then_green`. The row now names that node id and it
runs (1 passed, exit 0).

**But IN-03's stated mechanism was wrong, and so was the same claim in `21-VERIFICATION.md:24` and
`:211`.** All three recorded "exit 0". Measured correctly, a dead `-k` exits **5**. The wrong number
came from reading `$?` after a pipe. Full reproduction in `### Why these are node ids` above.

**A fourth instance, in shipped source, was found during this closure and is corrected in place:**
`tests/test_phase21_sc5.py:317` claimed a dead `-k` "exited **0**". It exits 5. Corrected under the
project's retract-in-place rule; the file is neither frozen nor ancestry-pinned.

**A fifth was found in the wall-census provenance and is recorded above** rather than passed
through: the two sites said to appear in no document were already rows 4 and 6 of this file's own
superseded table.

### The pattern, stated once

Five documents in this phase carried a claim that measurement falsified, and in every case the
measurement was right and the document was wrong. The wall count went 4 → 7 → 8 → 9 → **11**, each
step a document copying the last document. It stopped moving when 21-09 made it an **executable
test** instead of a table. That is the transferable lesson and it is why this closure verified every
command by running it rather than by reading it.
