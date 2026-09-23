---
phase: 21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus
verified: 2026-08-24T22:09:57Z
status: passed
score: 6/6 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: none
  previous_score: n/a
  gaps_closed: []
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Decide whether WR-03 closes before Phase 22: annotate scripts/teach_persona.py:162-163 in place, or accept the divergence."
    expected: "The live comment states '49.90% at n=64, because both sides scale with n_facts. Nothing re-tunes.' The phase's own committed artifact records documented_n64_claim_holds: false and measured_n64_share_at_the_pinned_constant: 0.44755244755244755. The file is editable and NOT ancestry-pinned, so the project's retract-in-place rule applies and nothing blocks the edit."
    why_human: "Whether a measured-false number may stand in live source while its correction lives only in a results/ artifact is a project-convention judgement, not a testable property. Both states are green today."
  - test: "Decide whether WR-04 closes before Phase 22: write the scripts/_addendum.py continuation exporting a validated privacy_n, or accept the pin's version."
    expected: "mitigation_unit.privacy_n is frozen and Phase 22's accountant imports it for N. Measured: privacy_n(7.9) -> 7 (silently drops a record), privacy_n('8') -> 8, privacy_n(0) -> 0 (delta*N == 0 then passes the ceiling), privacy_n(-3) -> -3. No Phase 21 addendum exists — grep of scripts/_addendum.py for phase21 / mitigation_unit / privacy_n returns nothing."
    why_human: "This is the wrong-unit defect class one level up, sitting in the module the NEXT phase consumes. Phase 21 computes no epsilon so nothing here is currently wrong; whether the continuation is owed by 21 or by 22 is a scope decision."
  - test: "Decide whether WR-06 closes: promote the `== 10` wall in scripts/phase21_filler.py:262 from `assert` to `raise SystemExit`."
    expected: "Confirmed live: `.venv/bin/python -O -c 'import phase21_filler'` imports cleanly with the assert stripped. The module's own comment on the line above says it 'joins the == 10 wall HERE, at the one file in the repo that could break it', and its sibling frozen pin (mitigation_unit.py:73-76) states the exact rule this violates. Every other refusal in the file (refuse_collisions, verify_round_trips) correctly raises SystemExit."
    why_human: "The repo does not run under -O today, so this is a latent robustness gap rather than a live failure. Whether it is worth a commit is a judgement."
  - test: "Decide whether the phase's own documentation ledger closes before Phase 22 — 21-VALIDATION.md, .planning/REQUIREMENTS.md and .planning/STATE.md."
    expected: "21-VALIDATION.md: every row still reads `TBD | TBD | TBD` / `pending`, and row :81's selector `-k phase21_glob_red_then_green` collects ZERO tests and exits 0 (measured: '22 deselected in 0.01s', exit 0). REQUIREMENTS.md: all six UNIT bullets still `- [ ]` and all six traceability Note cells EMPTY, against a convention where GATE-01..GATE-10 carry substantial evidence notes. STATE.md: reads 'Phase 21 EXECUTING — wave 1 (21-01, 21-02) in flight', 'Plan: 1 of 11', completed_plans: 17."
    why_human: "None of this affects code correctness. It affects whether Phase 22 can trust the ledger it reads. The gsd-sdk mutation handlers are known to corrupt this frontmatter, so the repair route is a human decision."
---

# Phase 21: The Privacy Unit, the DP Data Path, and the n=64 Corpus — Verification Report

**Phase Goal:** Fix what a "record" is and prove it structurally, because an ε computed against the
wrong unit is not a number that can be corrected by re-running.
**Verified:** 2026-08-24T22:09:57Z
**Status:** passed (was human_needed; all four human items resolved 2026-08-25)
**Re-verification:** No — initial verification
**Tree:** clean at `cf356a3`, 74 commits in the phase
**Suite:** `994 passed, 1 skipped` in 200.89s — the skip is `tests/test_train_loop.py:81`
(`fp16 AMP smoke needs a CUDA GPU`), platform-gated by design.

## Human items — RESOLVED 2026-08-25

This status was flipped by the ORCHESTRATOR after `/gsd-verify-work 21`, not by a fresh verifier
run. Stated so a reader knows the provenance. The 6/6 must-have score is the verifier's own; what
changed is that its four `human_verification` decisions are now made AND executed:

| item | decision | landed |
|------|----------|--------|
| WR-03 — 49.90% asserted in live source | retract in place | `c05880c` |
| WR-04 — `privacy_n` unvalidated in the frozen pin | write the continuation + AST guard | `9a407d6` |
| WR-06 — `== 10` wall as a bare `assert` | promote to `raise SystemExit` | `c552244` |
| ledger — `21-VALIDATION.md`, `REQUIREMENTS.md` | close both | `80b7e82` |

Three escalated beyond their original framing. WR-04 was recorded here as "nothing is wrong TODAY";
that was FALSE — `phase21_unit_record.py:1009` and `:1037` already reached the pin aliased as
`mu.privacy_n`, and `:1037` multiplies by `DELTA` against `DELTA_TIMES_N_CEILING`, so a zero N
there clears the published ceiling. Both were redirected rather than exempted.

This report's own "exit 0" claim for the vacuous `-k` selector is likewise FALSE and is corrected
here rather than left standing: a vacuous `-k` exits **5**, a wrong node id exits **4** and names
the missing id. The figure came from `$?` after a `| tail`, which reports `tail`.

Suite at closure: **1024 passed, 1 skipped**; ruff clean; frozen pin `45f37e15…` and both
`results/phase21_*` digests unchanged.

REMAINING OPEN, not closed by this pass: WR-05, WR-07, IN-01, IN-02, IN-04 in `21-REVIEW.md`.

## Method and its boundary

Every finding below is a measurement I took in this session, not a SUMMARY claim. Where I could
re-derive a number independently I did — the golden digests, the aligned bin geometry, the ancestry
`checked` count and the corpus geometry were all recomputed from scratch rather than read off an
artifact.

**What I did NOT check.** I did not train anything, so no claim about gradient behaviour under the
aligned loader is verified beyond the shapes and fact attribution it returns. I did not re-run the
multiplicity instrument end-to-end at SEED=1337 (I verified its inputs, its non-vacuity guard, its
conservation law and the corpus geometry it reports, and I rebuilt both corpora and matched the
recorded geometry exactly). I sampled 5 of the phase's guards for vacuity rather than all of them.
I read 21-REVIEW.md's remaining warnings and re-measured four of them; I did not independently
re-derive WR-05's arithmetic beyond confirming the fields it names are present.

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP Success Criteria) | Status | Evidence |
|---|---|---|---|
| 1 | `PRIVACY_UNIT = "one taught fact"` committed as a decision carrying its own arithmetic, incl. why example-level ε bounds nothing when `get_batch_memmap_masked` draws overlapping windows with replacement over a flat concatenated bin (UNIT-01) | VERIFIED | `scripts/mitigation_unit.py:85` + `PRIVACY_UNIT_ARITHMETIC:87-125`. Names `data.py:117`, `np.random.randint`, "with replacement", "flat concatenated bin", and writes the formula out with both denominators: `1,600 * (947.625 + 256) / (7,581 - 256 - 1) = 262.94`, plus the reading it is NOT (`1600*256/7581 = 54.03`). Pin sha256 `45f37e15…` matches the file on disk. Republished at `results/phase21_privacy_unit.json → unit`. |
| 2 | Fact-aligned batch path as a NEW function, `build_bins(..., align_facts=None)` byte-identical to v2.0 by default, and a structural check proving no `block_size`-aligned window contains ids from two fact shards → q=1, exact accountant (UNIT-02) | VERIFIED | Independently re-derived — see "Byte-identity, re-derived" and "SC2 structural probe" below. `SAMPLING_RATE_Q = 1.0` pinned with a module-scope `_prove`. |
| 3 | Effective per-fact multiplicity MEASURED after `build_bins` packing at the chosen `replay_ratio` and committed as a record — not inferred from the 22 rendered rows (UNIT-03) | VERIFIED | `results/phase21_multiplicity.json` — 5 rows at SEED=1337 / MAX_STEPS=200 / BATCH_SIZE=8, each carrying `bin_composition`, `attribution_rule`, `total_draws`, `bin_tokens`, `n_windows`, `n_facts`, per-fact `counts`, `min`/`max`/`mean`/`spread`. Instrument non-vacuity proven by `test_instrument_can_report_not_one` (parametrized on `rolled`, asserts the fixture really is corrupted FIRST, negative control through the same call). |
| 4 | Replay-in-lot a recorded decision with its ε consequence; δ pinned as literal `1e-5` with the rejected `1/N^1.1` self-contradiction at N=8 recorded (UNIT-04, UNIT-05) | VERIFIED | `REPLAY_OUTSIDE_N:144-165` states q=1, N=n_facts and the shrinks-q/flattering-ε consequence; artifact records `replay_in_lot: true` / `replay_inside_privacy_n: false`. `DELTA = 1e-5`, `DELTA_TIMES_N_CEILING = 0.01`, `rejected_delta(n) = n**-1.1` kept RUNNABLE, four module-scope `_prove` guards at N=8 AND N=64. N=8: `0.10153154954452942`, δ·N = `0.8122523963562354`, fails by 81.2×. |
| 5 | n=64 corpus from unscored filler facts, disturbing no published instrument — 8 `LOCKED_FACTS`, the 270-question fixture and ancestry-guarded `scripts/phase18_extraction.py` unchanged and green (UNIT-06) | VERIFIED | Measured: 56 filler + 8 locked = 64. Fact-id overlap with `all_pools()` (38 facts) = `[]`; SLOT overlap with the 11 published slots = `[]`; filler in `_BY_ID` = `[]`. `phase18_extraction.py` sha256 `d2b44806…` and `phase16_recall_sample.json` sha256 `407c4b93…` both match 21-09's pinned values. Zero filler values appear in the 270-question fixture text. `LOCKED_FACTS` = 8, `SOFT_TIER_FACTS` = 2. Corpus builds: 316 windows / 80,897 tokens. |
| 6 | The ancestry guard is LIVE rather than vacuous — `checked == len(pins) * len(artifacts)`, both non-zero, strict conjunct holds (21-11 must_have; the mechanism SC1/SC4 rest on) | VERIFIED | Recomputed independently: 1 pin commit `8d3beb4` × 2 tracked artifacts = **`checked = 2`**. `adds` for each artifact has exactly ONE entry (`c79b9bf`) — the CR-02 re-emit did not move the first-add. `8d3beb4 != c79b9bf` (conjunct 1) and `git merge-base --is-ancestor 8d3beb4 c79b9bf` exits 0 (conjunct 2). |

**Score:** 6/6 truths verified

### Byte-identity, re-derived (not read off a SUMMARY)

I rebuilt both golden captures from the fixture's own recipe and compared digests myself:

| Check | Result |
|---|---|
| `build_bins(...)` with `align_facts` OMITTED → `token_bin_sha256` | matches `91c25493…` |
| → `mask_bin_sha256` | matches `4a674423…` |
| → `repr(stats)` | matches `stats_repr` exactly |
| `artifacts/tokenizer.json` digest vs `meta.tokenizer_sha256` | matches `e82e8e83…` (fixture is not stale) |
| NON-VACUITY: `align_facts=<pairs>` → token digest | DIFFERS from the v2.0 golden |
| NON-VACUITY: third `*_fact.bin` appears | yes |
| `render_family` first-person, 8 families × 10 facts, 310 rows | matches `5f2b67ee…` |
| `render_family` second-person, 310 rows | matches `5e051c8f…` |

### SC2 structural probe — both arms, through the real CLI seam, bytes read back from disk

Built `dp_n8` and `dp_n64` via `teach_persona.build_arm_bins` (the one seam WR-02 was about), then
read `*_fact.bin` back with `np.fromfile` rather than trusting the packer's offsets:

| Property | `dp_n8` | `dp_n64` |
|---|---|---|
| whole-bin contract `(len-1) % 256 == 0` | True (8,449) | True (80,897) |
| **INPUT-space impure windows (SC2 verbatim)** | **`[]`** | **`[]`** |
| max distinct fact ids in ANY window | **1** | **1** |
| TARGET-space boundary rows | 7 (= n_facts−1) | 63 (= n_facts−1) |
| spans partition all windows, no gap/overlap | True (33) | True (316) |
| micro-steps == n_facts, all distinct | True (8) | True (64) |
| every micro-step serves the FULL span (CR-01) | True | True |
| ragged windows/fact (D-01, never a common W) | `4,4,4,4,4,5,4,4` | `4,4,4,4,4,5,4,4,5,5,…` |
| `replay_ratio` on the arm | 0.0 | 0.0 |

This reproduces `corpus_geometry` in the committed artifact exactly (33/8449 and 316/80897), so
that block is an observation I could re-take, not a recorded assertion.

### The 262.9437 vs 207.018 labelling question

The task flagged this as the most likely place for the artifact to be weaker than claimed. It is
not. `results/phase21_multiplicity.json` publishes BOTH on every row:

- `analytic_expectation.overlap_rule` = `262.9437465865647` (facts-only row)
- `analytic_expectation.first_token_rule` = `207.0180229382851`
- `rule_this_row_was_counted_under` = `"first-token-owns-draw"`
- `which_one_matches_this_row` = `"first_token_rule"`
- `gap_between_the_two_rules` = `55.92572364827963`
- a per-row `note` naming `overlap_rule` as "the REJECTED rule's closed form … the quantity
  `scripts/mitigation_unit.py`'s `PRIVACY_UNIT_ARITHMETIC` computes"
- a top-level `pin_discrepancy` block with both formulas and the exact reconciliation:
  `262.9437465865647 - 1600 * 256 / 7324 = 207.0180229382851`

A reader cannot mistake one for the other **in the artifact**. The frozen pin itself still says to
expect the difference "by sampling noise" — see WR-07 below.

### Gap-closure verification (the four already-closed findings)

| Finding | Claimed fix | My measurement | Verdict |
|---|---|---|---|
| CR-01 | root-caused into one `_window_count()` | `src/personacore/training/data.py:129`, 3 callers (`:216`, `:261`, `:387`). Direct call: `_window_count(16,4,…)` RAISES, `_window_count(17,4,…)` → 4. Every micro-step at both capacities served the FULL span. | CLOSED |
| WR-02 | `DP_ARMS` couples arm name to the aligned packer | `teach_persona.py:247` `DP_ARMS = ("dp_n8","dp_n64")`, read at `:342`, `:913`, `:1000`. Built both arms through the real `build_arm_bins`: the third `*_fact.bin` appeared for both, `phase21_` prefix, pure windows. | CLOSED |
| CR-02 | `refuse_if_dirty` + `scripts/phase21_emit.py`, re-emitted at `eba0571` | Made the guard FIRE with an untracked file (`REFUSING: the working tree is dirty`), then restored a clean tree. Both artifacts record `git_sha eba0571a…`; `git cat-file -p eba0571:scripts/phase21_unit_record.py` contains BOTH `def emit_privacy_unit` and `def emit_multiplicity`. First-add commit unchanged at `c79b9bf`. | CLOSED |
| WR-01 | flag computed, denominator reconciled | `phase21_unit_record.py:887` is now `all(round(_share_of_the_combined_lot(...), 4) == DOCUMENTED_N8_TABLE[str(w)] for w in (3,4,5))`. `test_the_n8_reproduction_claim_is_computed_and_could_have_been_false` recomputes it from the artifact's own rows AND asserts the same predicate returns False against the old tail-bearing denominator. | CLOSED |

### Vacuity sampling — 5 guards probed against wrong implementations

| Guard | Adversary I fed it | Result |
|---|---|---|
| `fact_window_impurities` (INPUT) | boundary shifted by 1 token | reported `[2]` — CAUGHT |
| `fact_window_impurities` (INPUT) | `np.roll` by 1 (invisible to an offset check) | reported `[0, 2]` — CAUGHT |
| `fact_window_impurities` / `_window_count` | tail truncated by 1 element | `ValueError` naming the remainder — CAUGHT |
| `refuse_if_dirty` | untracked file in the repo | `SystemExit` — CAUGHT |
| `n8_rows_reproduce_the_documented_table` | old tail-bearing denominator | test asserts the predicate returns False — NON-VACUOUS |
| **`21-VALIDATION.md:81` `-k phase21_glob_red_then_green`** | run as documented | **0 collected, "22 deselected", exit 0 — VACUOUS** |

25 of the 26 documented selectors collect ≥1 test. The one that does not is IN-03, still open. The
real test is `test_phase21_glob_sees_the_phase21_prefix_red_then_green` and it DOES run in the full
suite — the defect is in the documented command, not in the coverage.

### Denominators

`tests/test_phase18_docs.py::test_no_bare_zero_percent_in_docs` is GREEN (10 passed). The deferred
item `D-1` recorded at 21-03 (README bare `0%`) was **fixed inside this phase** at `e13d6cd`:
`against a 0% baseline` → `against a no-adapter control of exactly 0/104`. Grep for `\b0(\.0+)?%`
across `results/phase21_*.json`, `README.md`, `scripts/phase21_*.py` and `scripts/mitigation_unit.py`
returns nothing. Artifact figures carry explicit denominator fields (`pad_fraction_denominator`,
`ratio_denominator`, `draw_start_offsets_formula`, `total_tokens_formula`,
`conservation_pinned_mean_note`).

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `scripts/mitigation_unit.py` | PRIVACY_UNIT, q, δ, rejected recipe, module `_prove` guards | VERIFIED | Frozen, sha256 `45f37e15…`, zero imports (D-22 ceiling satisfied), 5 module-scope `_prove` guards |
| `scripts/phase21_unit_record.py` | multiplicity instrument, attribution rule, emitters | VERIFIED | 77 KB, `ATTRIBUTION_RULE`, `count_aligned` via shared `fact_window_span`, both emitters present at the recorded SHA |
| `scripts/phase21_emit.py` | clean-tree publication driver (CR-02) | VERIFIED | imports and calls `refuse_if_dirty` at `:77` |
| `scripts/phase21_filler.py` | 56 filler facts, disjoint slots, minting discipline | VERIFIED (1 warning) | 56 facts, 8 disjoint slots, `refuse_collisions`/`verify_round_trips` raise `SystemExit`; the `== 10` wall is a strippable `assert` (WR-06) |
| `scripts/phase21_golden_capture.py` | one-time v2.0 capture with git-cleanliness refusal | VERIFIED | `_refuse_if_dirty()` at module scope `:147`, BEFORE the sibling imports, and again at call time `:263` |
| `src/personacore/training/data.py` | `fact_window_impurities`, `get_batch_fact_aligned`, `fact_window_span`, `_window_count` | VERIFIED | All exported and wired; loader re-opens all three bins per call |
| `src/personacore/provenance.py` | `refuse_if_dirty` | VERIFIED | Proven to fire; raises rather than degrading when git is unavailable |
| `scripts/teach_persona.py` | `align_facts`, `fact_bin_path`, ragged packer, `DP_ARMS`, `replay_window_budget` | VERIFIED (1 warning) | All present and reached from the CLI seam; `:162-163` carries a measured-false comment (WR-03) |
| `src/personacore/training/loop.py` | additive replay seam | VERIFIED, ORPHANED | `replay_windows` seam exists and its off-path bit-identity is proven; no production caller (IN-04) — a declared Phase-22 seam |
| `results/phase21_privacy_unit.json` | SC1 + SC4's committed record | VERIFIED | 15.8 KB, all four sections + provenance |
| `results/phase21_multiplicity.json` | SC3's labelled measured rows + observed geometry | VERIFIED | 22.4 KB, 5 rows, 2 geometry blocks, `a3_discharge`, `pin_discrepancy`, `findings` |
| `tests/fixtures/golden_*_v2.json` | v2.0 byte-level baselines | VERIFIED | Both digests independently re-derived today |

### Key Link Verification

| From | To | Via | Status |
|---|---|---|---|
| `teach_persona.build_bins` | `data.fact_window_impurities` | build-time proof 7, same predicate as loader + tests | WIRED |
| `data.get_batch_fact_aligned` | `data.fact_window_impurities` | run-time INPUT-space purity on the drawn slice (`:407`) | WIRED |
| `data.get_batch_fact_aligned` | `data.fact_window_span` | the one place a fact's window range is computed | WIRED |
| `phase21_unit_record.count_aligned` | `data.fact_window_span` | shared arithmetic, `strict=False` route | WIRED |
| `teach_persona.build_arm_bins` | `DP_ARMS` → aligned packer | arm-name coupling (WR-02 fix) | WIRED — measured on both arms |
| `phase21_filler` | `phase14_factset.render_family(forms=…)` | additive kwarg from 21-05 | WIRED |
| `phase21_unit_record` | `scripts/mitigation_unit.py` | imports frozen constants, retypes nothing | WIRED — `test_artifact_values_come_from_the_pin` |
| `results/phase21_*` | `test_phase21_prereg_is_frozen_before_every_phase21_result` | `git ls-files` now matching | WIRED — `checked = 2` |
| `phase21_emit` / `phase21_unit_record` / `phase21_golden_capture` | `provenance.refuse_if_dirty` | pre-publication refusal | WIRED — proven to fire |
| `loop.train(replay_*)` | any production caller | — | **NOT WIRED** (IN-04, declared Phase-22 seam) |

### Data-Flow Trace (Level 4)

| Artifact | Data | Source | Real data? | Status |
|---|---|---|---|---|
| `results/phase21_multiplicity.json` rows | per-fact counts | instrumented `get_batch_memmap_masked` / `get_batch_fact_aligned` at SEED=1337 | Yes — counts vary per fact (143..229, 14..36) with non-trivial spread; a constant would show spread 0 | FLOWING |
| `results/phase21_multiplicity.json` corpus_geometry | windows/tokens per fact | `build_bins` output | Yes — I rebuilt both corpora and matched exactly | FLOWING |
| `results/phase21_privacy_unit.json` | δ, q, replay volume | imported from the frozen pin + `replay_window_budget` | Yes — `test_artifact_values_come_from_the_pin` asserts equality against the module | FLOWING |
| `d24_candidate_table_reproduced` | share rows + flag | `_share_of_the_combined_lot` over observed geometry | Yes — flag recomputed with a False control (WR-01 fix) | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Full suite | `.venv/bin/python -m pytest -q tests/` | `994 passed, 1 skipped` in 200.89s | PASS |
| Phase-21 identity + SC5 tests | `pytest -q test_phase21_{aligned_bins,filler,sc5,unit_pin,unit_record}.py` | 68 passed | PASS |
| Multiplicity + loader + replay | `pytest -q test_phase21_{multiplicity,aligned_loader,replay_volume}.py` | 41 passed | PASS |
| Docs denominator guard | `pytest -q tests/test_phase18_docs.py` | 10 passed | PASS |
| Build `dp_n8` through the CLI seam | `build_arm_bins("dp_n8", …)` | 8 records, 33 windows, 867 pad, third bin written | PASS |
| Build `dp_n64` through the CLI seam | `build_arm_bins("dp_n64", …)` | 64 records, 316 windows, 8,803 pad, third bin written | PASS |
| Golden digests re-derived | manual `build_bins` + `sha256` | all 4 digests + `stats_repr` match | PASS |
| Ancestry `checked` recomputed | `git log` / `ls-files` / `merge-base` | `checked = 2`, both conjuncts hold | PASS |
| Dirty-tree refusal fires | untracked file + `refuse_if_dirty` | `SystemExit` raised; tree restored clean | PASS |
| `-O` strips the `== 10` wall | `python -O -c 'import phase21_filler'` | imports cleanly, assert stripped | FAIL (WR-06) |
| Documented selector `-k phase21_glob_red_then_green` | as written in 21-VALIDATION.md | 0 collected, 22 deselected, exit 0 | FAIL (IN-03) |

### Probe Execution

No `scripts/*/tests/probe-*.sh` files exist in this repository and no PLAN or SUMMARY declares one.
This project's equivalent discipline is the pytest suite plus the deliberate-RED protocol, both of
which I executed above.

| Probe | Command | Result | Status |
|---|---|---|---|
| — | `find scripts -path '*/tests/probe-*.sh'` | no matches | N/A — convention not used here |

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|---|---|---|---|---|
| UNIT-01 | 21-01, 21-03, 21-11 | Privacy unit is the fact, recorded as a decision with its arithmetic | SATISFIED | `mitigation_unit.py:85-125`, frozen at `45f37e15…`; republished in `results/phase21_privacy_unit.json → unit` |
| UNIT-02 | 21-02, 21-04, 21-06 | Fact-aligned batching, `grad_accum_steps = n_facts`, q=1, exact accountant | SATISFIED | Byte-identity re-derived; `[]` impure windows and `max distinct == 1` measured at 33 and 316 windows; `n_facts` micro-steps observed from the loader |
| UNIT-03 | 21-10, 21-11 | Per-fact multiplicity MEASURED, not inferred | SATISFIED | 5 measured rows with full denominators; instrument proven able to report ≠ 1 |
| UNIT-04 | 21-01, 21-03, 21-08, 21-11 | Recorded decision on replay in the DP lot with its ε consequence | SATISFIED | `REPLAY_OUTSIDE_N`; `replay_window_budget` side-channel closure proven by differential with a live negative control |
| UNIT-05 | 21-01, 21-03, 21-11 | δ pinned as literal 1e-5; `1/N^1.1` self-contradiction recorded | SATISFIED | Four runnable `_prove` guards at N=8 and N=64; N=8 gives 0.10153…, δ·N = 0.81225, 81.2× over the 0.01 ceiling |
| UNIT-06 | 21-02, 21-05, 21-07, 21-09, 21-11 | n=64 corpus from unscored filler touching no ancestry-pinned fixture | SATISFIED | 56 filler, disjoint ids and slots, both SC5 sha256 pins hold, zero filler values in the 270-question fixture, corpus builds to 316 windows |

**Orphaned requirements:** none. REQUIREMENTS.md maps exactly UNIT-01..UNIT-06 to Phase 21 and all
six appear in plan frontmatter.

**Ledger gap (not a coverage gap):** all six bullets in REQUIREMENTS.md are still `- [ ]` and all
six traceability Note cells are EMPTY, against a convention where GATE-01..GATE-10 carry detailed
evidence notes. The requirements are satisfied in the codebase; the ledger does not say so.

### Anti-Patterns Found

Scanned all 24 non-planning files touched in the phase.

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| — | — | `TBD` / `FIXME` / `XXX` in code | — | **NONE FOUND** — the debt-marker gate is clean |
| — | — | `TODO` / `HACK` / `PLACEHOLDER` | — | NONE FOUND |
| — | — | "not yet implemented" / "coming soon" / "placeholder" | — | NONE FOUND |
| `scripts/teach_persona.py` | 162-163 | live comment states a figure the phase's own artifact records as false (WR-03) | WARNING | A reader of the source has no signal that `documented_n64_claim_holds: false` |
| `scripts/phase21_filler.py` | 262 | strippable `assert` on the load-bearing `== 10` wall (WR-06) | WARNING | Under `-O` a filler value colliding with a new scored value could be minted without refusal |
| `scripts/mitigation_unit.py` | 134-141 | `privacy_n` silently truncates float, admits `str`/`0`/negative (WR-04) | WARNING | Frozen; Phase 22's accountant imports it for N |
| `scripts/mitigation_unit.py` | 119-124 | tells the reader to attribute a systematic rule gap to "sampling noise" (WR-07) | WARNING | Frozen; corrected only inside the artifact, no `_addendum.py` continuation exists |
| `scripts/mitigation_unit.py` | 246-252 | `_prove(SAMPLING_RATE_Q == 1.0)` is a tautology (IN-01) | INFO | Inflates the guard count by one of five; 4 are load-bearing |
| `scripts/mitigation_unit.py` | 96-97 | stale line anchors (`:523`/`:517`, now `:955`/`:949`) (IN-02) | INFO | Frozen |
| `21-VALIDATION.md` | 81 | `-k` selector collects zero tests, exits 0 (IN-03) | WARNING | Confirmed live by measurement |
| `src/personacore/training/loop.py` | 199-201, 456-476 | replay seam has no production caller (IN-04) | INFO | Declared Phase-22 seam; off-path bit-identity is proven |
| `.planning/STATE.md` | frontmatter | stale — "wave 1 in flight", "Plan: 1 of 11", `completed_plans: 17` | WARNING | Phase 22 reads this |

### Human Verification Required

Four decisions, all listed in the frontmatter with their measurements. In priority order:

**1. WR-04 — `privacy_n` is unvalidated inside the frozen module Phase 22 imports for N.**
This is the wrong-unit defect class one level up: `privacy_n(7.9) -> 7` silently drops a record,
`privacy_n(0) -> 0` makes `δ·N == 0` pass the ceiling trivially. Phase 21 computes no ε so nothing
is currently wrong, and the neighbouring `_prepend_replay` guard already gets this right for the
same quantity. No `scripts/_addendum.py` continuation exists. Decide whether the continuation is
owed by 21 or by 22 — but decide it before an accountant imports the name.

**2. WR-03 — a measured-false number stands in live, editable source.**
`teach_persona.py:162-163` says "49.90% at n=64 … Nothing re-tunes"; the phase's own committed
artifact says `documented_n64_claim_holds: false` and `0.44755244755244755`. The file is not
ancestry-pinned, so retract-in-place is available and cheap. D-24 itself is NOT reopened —
`REPLAY_WINDOWS_PER_FACT = 4` was chosen on the n=8 table, which reproduces exactly.

**3. WR-06 — the `== 10` wall is strippable under `-O`.** Confirmed by running it.

**4. The ledger — `21-VALIDATION.md`, `REQUIREMENTS.md`, `STATE.md`.** One documented selector is
provably vacuous, the validation table was never filled in, all six requirement Notes are empty,
and STATE.md still says wave 1 is in flight.

### Gaps Summary

**There are no gaps in the phase goal.** All six success criteria are true in the codebase, and I
verified the two that were most likely to be softer than claimed by re-deriving them myself rather
than reading them: the v2.0 byte-identity (four digests plus `stats_repr`, all matching) and the
SC2 structural claim (`[]` impure windows and `max distinct fact ids == 1` at both 33 and 316
windows, read back as bytes from bins built through the real CLI seam). The ancestry guard is LIVE
at `checked = 2` with both conjuncts holding, and the four already-closed review findings are
genuinely closed — I made three of the four fixes fire or fail on demand rather than accepting the
closure record.

The phase also passes its own hardest test: its guards can fail. Five sampled guards were fed wrong
implementations and four caught them. The fifth — a documented `-k` selector — is the one that
cannot, and it is a line in a planning document, not in the shipped mechanism.

**What remains is a decision, not a repair.** Five review warnings are open. Two of them
(WR-03, WR-04) are instances of the exact discipline this phase was built to enforce, pointed at
the phase itself: a number measured false left standing in live source, and a declared invariant
that is unenforced in the module the next phase consumes. Neither invalidates anything Phase 21
published. Both are cheap now and expensive after Phase 22 imports `privacy_n`.

That is why this is `human_needed` rather than `passed`: the goal is achieved and the evidence is
reproducible, but the phase's ledger does not yet say so, and two known defects sit on the seam the
next phase reaches through.

---

_Verified: 2026-08-24T22:09:57Z_
_Verifier: Claude (gsd-verifier)_
