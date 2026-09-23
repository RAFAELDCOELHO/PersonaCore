---
phase: 25-frontier-sweep-and-the-existence-gate-verdict
plan: 04
subsystem: teaching-bins
tags: [ADVT-01, D-41, WR-01, WR-04, WR-06, WR-08, refusals, build_bins]
requires:
  - scripts/teach_persona.py::build_bins
  - scripts/teach_persona.py::_mix_adversarial
  - scripts/phase24_adversarial.py::_adversarial_pool
  - scripts/mitigation_budget.py::ADVERSARIAL_RATIO_GRID
provides:
  - "a single finite/non-negative ratio domain enforced before either branch of build_bins"
  - "flat-branch refusal of replay_ratio + adversarial_ratio, mirroring the aligned twin"
  - "one paired _adversarial_pool read in _mix_adversarial"
  - "proofs-before-bytes ordering on both bin-writing branches"
  - "WR-02 / WR-03 / WR-07 deferrals recorded in source with their arithmetic"
affects:
  - "every one of the 12 adversarial sweep points, which all route through build_bins"
  - "results/phase24_token_budget.json (provenance pin re-emitted; all 12 rows byte-identical)"
tech-stack:
  added: []
  patterns:
    - "math.isfinite as the one domain check that catches NaN and ±inf together"
    - "read-back proofs stay after the write they read; in-memory proofs move before it"
    - "deferral comments carry their own computed arithmetic"
key-files:
  created:
    - tests/test_phase25_wr.py
  modified:
    - scripts/teach_persona.py
    - results/phase24_token_budget.json
decisions:
  - "D-41's four fixes landed; the three deferrals are recorded in source, not silenced"
  - "the loop.py prose-vs-code count was left true by dropping a duplicated identifier from a new comment, rather than by churning a privacy-claim message"
metrics:
  duration: "~35 min"
  completed: 2026-08-31
  tasks: 3
  commits: 4
  tests_added: 12
---

# Phase 25 Plan 04: The Four Phase-24 Review Refusals Summary

Repaired WR-01, WR-04, WR-06 and WR-08 in `scripts/teach_persona.py` before any sweep point exists,
recorded WR-02/WR-03/WR-07 as deferred with their own arithmetic, and watched all four repairs fail
against a scratch copy of the pre-plan tree before they passed.

## All four defects REPRODUCED at HEAD — none was a false finding

The plan required each review finding to be treated as a hypothesis and reproduced before repair.
**4 of 4 reproduced.** Every site was resolved BY CONTENT; **no line number was copied from
`24-REVIEW.md`.**

| WR | Reproduction command | Output at HEAD (`4f9296b`) |
|----|----------------------|-----------------------------|
| WR-01 | `build_bins(tok, eps, …, adversarial_ratio=float("nan"))` on the flat branch, digested against a ratio-0.0 build | `nan stats has adversarial_ratio key: False` / `BYTE-IDENTICAL TO THE CONTROL: True` (token digest `f146d426`). The same value on the aligned branch: `REFUSED: [teach_persona] build_bins got adversarial_ratio=nan alongside 8 align_facts pairs…`. `-1.0` behaved identically. |
| WR-04 | `build_bins(…, replay_ratio=0.5, adversarial_ratio=0.25)` on the flat branch | `NO REFUSAL. stats replay_ratio = 0.5  replay_tokens = 3790  adversarial_tokens = 4106  total tokens = 15477` → replay is **0.2449** of the bin while the record says 0.5 |
| WR-06 | AST call census over `_mix_adversarial` | `AssertionError: ['adversarial_episodes', 'adversarial_episode_families', 'ceil', 'Random', 'shuffle', …]` — zero `_adversarial_pool` calls |
| WR-08 | AST ordering check over `build_bins` / `_build_aligned_bins` | `AssertionError: [('build_bins', [583, 584], [593]), ('_build_aligned_bins', [782, 783, 784], [794])]` — **exactly the tuple the plan quoted**. Behaviourally: `bin exists after a REFUSED build: True` |

## Sites edited, resolved by content (symbol + surrounding expression)

**No line number from `24-REVIEW.md` was used at any point.** Each site below is named by the symbol
that owns it and the expression it sits against.

| # | Symbol | Resolved against | Change |
|---|--------|------------------|--------|
| 1 | `build_bins` | immediately BEFORE the `if align_facts is not None:` dispatch | added the `math.isfinite` domain loop over both named ratios (WR-01) |
| 2 | `build_bins` | immediately AFTER the `return _build_aligned_bins(...)` dispatch, BEFORE `id_shards, mask_shards, lengths, fractions = [], [], [], []` | added the flat-branch replay+adversarial refusal (WR-04) |
| 3 | `_refuse_ambiguous_aligned_input` | the guard whose body raises `"…got replay_ratio=… alongside … align_facts pairs. D-10 puts replay OUTSIDE…"` | `if replay_ratio:` → `if replay_ratio > 0:` |
| 4 | `_refuse_ambiguous_aligned_input` | the guard whose body raises `"…The adversarial arm packs FLAT by the DP_ARMS name rule…"` | `if adversarial_ratio:` → `if adversarial_ratio > 0:` |
| 5 | `_mix_adversarial` | the two consecutive `pa.adversarial_episodes(tok)` / `pa.adversarial_episode_families(tok)` lines | replaced by `pool, families = pa._adversarial_pool(tok)` (WR-06) |
| 6 | `_mix_adversarial` | the `if len(families) != pool_size:` refusal reading `"read POSITIONALLY and paired by index"` | message rewritten to an invariant of ONE paired read |
| 7 | `_mix_adversarial` | immediately ABOVE `n_want = int(round(adversarial_ratio * n_clean))` | WR-02/WR-03 deferral with both computed products |
| 8 | `_mix_adversarial` | immediately ABOVE `family_counts = {family: selected_families.count(family) …}` | WR-07 deferral note |
| 9 | `build_bins` | `ids_all.tofile(bin_path)` / `mask_all.tofile(mask_path)` | moved from directly after `mask_all = np.concatenate(mask_shards)` to directly after `frac = _prove_floor_and_band(ids_all, mask_all)` (WR-08) |
| 10 | `_build_aligned_bins` | the three `tofile` calls after `fact_path = fact_bin_path(bin_path)` | moved to directly after `frac = _prove_floor_and_band(...)`, still BEFORE `read_facts = np.fromfile(fact_path, …)` (WR-08) |

Post-fix AST ordering check: `proofs precede bytes on both branches [('build_bins', [664, 665],
[652]), ('_build_aligned_bins', [877, 878, 879], [867])]`.

**Why proof 7 stays after the write on the aligned branch:** it re-reads the bins FROM DISK on
purpose, so a check re-deriving boundaries from the packer's own arithmetic cannot share the
packer's defect. A read-back proof cannot precede the write it reads. The two proofs that moved are
exactly the two that operate on the in-memory arrays, which is what the plan's AST criterion pins.

## The four watched REDs, verbatim

**Form used: a SCRATCH COPY of the pre-fix tree, for all four.** `git stash` was not used at any
point — its stack is shared across worktrees and this repository has been burned by that. The
scratch tree is `git archive 4f9296b | tar -x` into a scratchpad directory, with
`tests/test_phase25_wr.py` copied in and the two gitignored replay bins symlinked (see the
correction below). Pre-fix tally: **9 failed, 3 passed**. Post-fix: **12 passed, 0 skipped**.

| WR | Test | Verbatim pre-fix failure |
|----|------|--------------------------|
| WR-01 | `test_wr01_a_nan_ratio_is_refused_on_both_branches[flat]` | `E  Failed: DID NOT RAISE <class 'SystemExit'>` |
| WR-01 | `test_wr01_a_nan_ratio_is_refused_on_both_branches[aligned]` | `E  AssertionError: the aligned branch's refusal does not name the pinned legal domain: '[teach_persona] build_bins got adversarial_ratio=nan alongside 8 align_facts pairs. The adversarial arm packs FLAT by the DP_ARMS name rule and makes no formal privacy claim (Phase 25 SC4 pins accounting: null on it), so it has no home in the ragged fact-aligned layout: a fact-independent refusal episode has no fact shard, and giving it one would put a record in the accounting for a privacy record that does not exist.'` |
| WR-04 | `test_wr04_replay_and_adversarial_together_are_refused_on_the_flat_branch` | `E  Failed: DID NOT RAISE <class 'SystemExit'>` |
| WR-06 | `test_wr06_the_adversarial_pool_is_read_exactly_once` | `E  AssertionError: \`_mix_adversarial\` calls \`_adversarial_pool\` 0 times, expected exactly 1 — the whole census is ['adversarial_episodes', 'adversarial_episode_families', 'ceil', 'Random', 'shuffle', 'append', 'append', 'append', 'append', 'count', 'asarray', 'asarray', 'sum', 'mean']` |
| WR-08 | `test_wr08_no_bytes_land_when_a_proof_fails` | `E  AssertionError: flat.bin exists after a REFUSED build — a failed build left bytes that \`refuse_if_exists\` will treat as a completed point's evidence (WR-08)` |
| WR-08 | `test_wr08_the_same_holds_on_the_aligned_branch` | `E  AssertionError: aligned.bin exists after a REFUSED aligned build — proof 1 and the floor/band proof must both run before any of the THREE bins land (WR-08)` |
| deferrals | `test_wr02_wr03_wr07_are_recorded_as_deferred_with_their_reason` | `E  AssertionError: WR-02 is deferred by D-41 but is not RECORDED anywhere in …/scripts/teach_persona.py — a deferral that leaves no trace in the source is indistinguishable from a silencing` |

### One RED was initially FALSE and was corrected

The first pre-fix run of `test_wr04_…` failed with
`E  AssertionError: the refusal does not name replay's value: '[teach_persona] replay arm needs
…/data/dialog_train.bin and …/data/dialog_train_mask.bin — run \`python
scripts/prepare_dialog_corpus.py\` first.'` — the scratch tree came from `git archive`, so the
gitignored replay corpus was absent and the test went red on a **missing-fixture path, not on the
WR-04 defect**. That is the "planted RED lands on the wrong occurrence" failure mode. Corrected by
symlinking `data/dialog_train.bin` and `data/dialog_train_mask.bin` into the scratch tree, after
which the pre-fix run produced the true natural RED: `Failed: DID NOT RAISE <class 'SystemExit'>`.

### The three tests that passed pre-fix, and why that is correct

- `test_wr01_the_control_ratio_still_builds_and_is_not_caught_by_the_domain_check` — non-vacuity.
  `0.0` is `ADVERSARIAL_RATIO_GRID[0]`, the sweep's own control point; a domain check that refused
  it would make every refusal above green while the sweep could not run.
- `test_wr04_the_aligned_branch_refusal_of_the_pair_still_fires` — the aligned branch's
  **pre-existing** refusal. WR-04 is a missing mirror, so the mirrored-from side must still work.
- `test_wr06_family_labels_stay_paired_with_their_episodes` — the LOAD-BEARING companion, green on
  both trees **by design**: pre-fix, both thin views are themselves `_adversarial_pool` readers, so
  a patched pool reaches either call shape. A companion that looked RED pre-fix would be measuring
  the patch rather than the pairing. Stated in the module docstring so it cannot be mistaken for the
  refusal. It proves the pairing is load-bearing: rotating the family column by one moves the
  reported counts from `{'A1-mild': 15, 'A1-aggressive': 15, 'A3': 14}` to
  `{'A1-mild': 14, 'A1-aggressive': 15, 'A3': 15}` at an unchanged total.

## The 24-06 byte-identity baseline SURVIVED

A fresh `adversarial_ratio=0.0, replay_ratio=0.0` build emits:

```
token digest: f146d42637c69e9eb1e7ac2248c9056a7966aed48f6498fa9cdb6d3db02d147b
mask  digest: a2c4771f92aa4e03127e451b1de880b9386bee5164ee512d291467c1eb1e59a2
episodes: 176  tokens: 7581
```

These equal the pinned `f146d426…` / `a2c4771f…` over 176 episodes / 7,581 tokens. Independent
corroboration: re-emitting `results/phase24_token_budget.json` produced **every substantive figure
byte-identical** — all 12 rows, `band_corners`, `token_budget_disclosure` and `attack_corpus`
unchanged; only `git_sha`, `written_utc` and the `scripts/teach_persona.py` pin moved.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `results/phase24_token_budget.json`'s provenance pin went stale**

- **Found during:** Task 1 verification (`tests/test_phase24_record.py`)
- **Issue:** `provenance.module_sha256` pins `scripts/teach_persona.py`, so any repair turns
  `test_the_provenance_pins_match_the_live_module_bytes` RED:
  `assert not [('scripts/teach_persona.py', '82da6c3a…', '3c1e6c55…')]`.
- **Fix:** re-emitted by that test's **own prescribed procedure** — delete the artifact at a clean
  tree and run `python scripts/phase24_record.py`. `phase24_record._write` calls `refuse_if_dirty`
  over `scripts src results artifacts`, which forces the code commits to land first; the re-emit is
  therefore a third commit rather than part of Task 1 or Task 2. Verified before committing that
  every substantive figure was byte-identical.
- **Files modified:** `results/phase24_token_budget.json`
- **Commit:** `f968c39`
- **Transient window:** commits `61b6060` and `e42be57` each carry this one test RED. It is green at
  `f968c39` and at every commit after.

**2. [Rule 3 - Blocking] `test_phase22_wiring.py::test_the_prose_vs_code_measurement_is_still_true`**

- **Found during:** Task 1 full-suite run
- **Issue:** `src/personacore/training/loop.py`'s accum-agreement refusal tells a user debugging a
  privacy claim that `'grad_accum_steps' appears 14 times in scripts/teach_persona.py and exactly 1
  of them is CODE`. A cross-reference in my new WR-04 comment repeated the identifier, moving the
  measurement to 15/1: `AssertionError: … measured 15 textual / 1 code hits, message says 14 / 1`.
- **Fix:** the repetition was **decorative** — `_refuse_ambiguous_aligned_input`, referenced by name
  three lines below, already spells the identity in full. Dropped the duplicate and replaced it with
  a named pointer to that function plus a note recording why the identifier is not repeated there.
  Deliberately did **not** bump the number in `loop.py`: the count's substantive claim (exactly 1 is
  CODE) never moved, and churning a privacy-claim message for a duplicated identifier trades a true
  statement for a re-typed one. Zero out-of-plan files touched.
- **Files modified:** `scripts/teach_persona.py`
- **Commit:** `61b6060`

### Observations, not fixed (out of scope)

**`tests/test_phase25_epsilon.py::test_the_epsilon_gate_fires_on_a_planted_bare_print`** asserts
`git status --porcelain scripts/` is empty and therefore fails for **any** uncommitted change under
`scripts/`, including a legitimate in-progress edit. It was RED mid-task purely for that reason
(`watching the RED must leave no residue in scripts/: ' M scripts/teach_persona.py\n'`) and is green
at every commit. Not repaired — it is plan 25-03's file and outside this plan's scope — but it makes
`make test` unusable as a mid-edit signal for anyone touching `scripts/`.

## Deferrals recorded, not silenced (D-41)

- **WR-02 / WR-03** — recorded in `_mix_adversarial` immediately above `n_want`, carrying their own
  arithmetic: `round(0.25 * 176) = 44` at n=8 and `round(0.25 * 1408) = 352` at n=64, both far above
  the `n_want < 1` branch, using `ADVERSARIAL_RATIO_GRID`'s smallest non-zero entry. The test
  recomputes both products from the grid and the committed multiplicity geometry (keyed by
  `n_facts`, never by arm name — WR-05's key mismatch is not this plan's) and asserts each is `>= 1`,
  so a shrunken corpus or a new smaller grid entry re-opens the deferral on sight.
- **WR-07** — recorded at the `family_counts` boundary. Hygiene only; no sweep number moves.

## Verification

```
.venv/bin/python -m pytest tests/test_phase25_wr.py -v      12 passed, 0 skipped
.venv/bin/python -m pytest tests/test_phase25_wr.py -k wr01  5 passed, 7 deselected  (>= 4 required)
.venv/bin/python -m pytest tests/test_phase24_grid.py tests/test_phase24_split.py \
                          tests/test_phase24_record.py -q   0 failed
.venv/bin/python -m pytest tests/ -q                        1684 passed, 1 skipped
make lint                                                    All checks passed! 235 files formatted
git diff --exit-code -- scripts/mitigation_gate.py scripts/mitigation_accountant.py \
        scripts/mitigation_unit.py scripts/phase18_extraction.py pyproject.toml   exit 0
```

**Full-suite delta: 1672 → 1684 passed (+12), skipped unchanged at 1.** The +12 are exactly the new
`tests/test_phase25_wr.py` cases. No pre-existing test moved.

`.planning/STATE.md` and `.planning/ROADMAP.md` were not touched. The pre-existing uncommitted
`.gitignore` modification was left alone.

## Commits

| Hash | Message |
|------|---------|
| `61b6060` | `fix(25-04): WR-01 and WR-04 — one ratio domain, both branches, and the flat pair refused` |
| `e42be57` | `fix(25-04): WR-06 and WR-08 — one paired pool read, and proofs before bytes` |
| `f968c39` | `chore(25-04): re-emit the phase-24 token budget record after the WR repairs` |
| `f91bd61` | `test(25-04): four watched refusals for WR-01, WR-04, WR-06 and WR-08` |

## Known Stubs

None. Every path this plan touched is wired and exercised by a test.

## Threat Flags

None. This plan added refusals and moved a write; it opened no new network endpoint, auth path,
file-access pattern or schema at a trust boundary. All five mitigate-disposition threats in the
plan's register (T-25-16 … T-25-20) are discharged: T-25-16 by the `math.isfinite` domain check plus
the NaN-disagreement test, T-25-17 by the flat-branch pair refusal naming D-34, T-25-18 by the AST
census plus the permutation companion, T-25-19 by the proofs-before-bytes move asserted on both
branches, and T-25-20 by the re-measured `f146d426…` / `a2c4771f…` digests and the green
`tests/test_phase24_*` battery. T-25-SC holds: zero installs, `pyproject.toml` byte-unchanged.

## Self-Check: PASSED

All four artifact paths exist on disk (`scripts/teach_persona.py`,
`tests/test_phase25_wr.py`, `results/phase24_token_budget.json`,
`25-04-SUMMARY.md`) and all five commit hashes resolve in `git log`
(`61b6060`, `e42be57`, `f968c39`, `f91bd61`, `22a67ff`). `.planning/STATE.md`
and `.planning/ROADMAP.md` are byte-unchanged; the only working-tree
modification is the pre-existing, untouched `.gitignore`.
