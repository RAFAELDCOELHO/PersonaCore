---
phase: 25-frontier-sweep-and-the-existence-gate-verdict
plan: 08
subsystem: instrumentation
tags: [record-schema, dp-sgd, mechanism-pin, ast, atomic-write, condition-c, refusal-column]

requires:
  - phase: 25-01
    provides: "scripts/phase25_prereg.py — POINT_RECORD_GLOB / point_record_path / prove_first_attempt (D-10's per-point one-attempt refusal, integrated rather than reimplemented), CANARY_RESERVATIONS, DISK_PRECHECK_BYTES"
  - phase: 25-03
    provides: "scripts/phase25_epsilon.py — CONTROL_EPSILON_FIELD_FORM (§C5's DECISION, since the cited sigma_zero precedent does not exist), dual_granularity_sentence, SELECTION_ACCOUNTED, point_epsilon_for_sigma"
  - phase: 25-21
    provides: "scripts/phase25_condition_c.py — CONDITION_C_FIELDS (the 11-name ordered contract), retention_floor_for_verdict(), gap_noise_floor(), counterfactual_fields(), RETENTION_LEG_BINDS_AT_ANCHOR, DIALOGUE_FLOOR_RECIPE_MISMATCH"
  - phase: 25-22
    provides: "scripts/phase25_gate05.py — prove_flag_is_a_bool, GATE05_SLOTS, GATE05_GOVERNS, REQUIRED_NLL_COLUMNS, and _committed_literal (the torch-free reader for phase18_extraction's frozen constants)"
provides:
  - "scripts/phase25_record.py — the per-point record builder; the module that OWNS results/phase25_frontier.json and the _PUBLICATION_PATHSPEC the write-once assembly refuses on"
  - "MECHANISM_PIN_FIELDS + prove_mechanism_matches_pin — D-34's five-field live halt, exact ==, no tolerance, fired BEFORE the record dict is returned"
  - "POINT_KEY_GRAMMAR / point_key / parse_point_key / ORDERED_POINT_KEYS() — the 44-key grammar, resolved LAZILY so waves 2-4 import cleanly while SIGMA_LADDER is still absent"
  - "epsilon_bearing_reading — D-21's inline k, with the k asserted equal to the mitigation_budget constant its source names"
  - "refusal_column / per_family_counts / canary_population / condition_c_group / retention_disclosure — D-39, D-36, D-37(ii), D-45 and D-48/D-49/D-50 as callable field groups"
  - "prove_names_are_outside_the_gate — a BUILD-TIME refusal of any reported field name that is one of the frozen verdict's 21 kwonly args"
  - "write_point_record — atomic tmp + fsync + os.replace, with prove_first_attempt and refuse_existing_artifacts both in front of the bytes"
affects: [25-10, 25-14, 25-16, 25-17, 25-19, 25-20]

tech-stack:
  added: []
  patterns:
    - "a phase-owned constant read from a FROZEN torch-pulling module by AST (_committed_literal) in the module, and by real import in the test that proves the two agree"
    - "serialise-before-open: json.dumps runs before the temp file exists, so a non-serialisable record leaves NO file rather than a truncated one"
    - "a reported column's disjointness from a verdict signature made true BY CONSTRUCTION at build time, with the test proving the refusal fires rather than only proving today's names happen not to collide"
    - "a lazily-resolved ordered pin: getattr at CALL time with a refusal naming its future producer, so a wave-2 module can name a wave-5 constant"

key-files:
  created:
    - scripts/phase25_record.py
    - tests/test_phase25_record.py
  modified: []

key-decisions:
  - "phase18_extraction's GATED_TIER / REPORTED_TIER / ATTACK_FAMILIES / FAMILY_ZERO are read through phase25_gate05._committed_literal rather than imported: MEASURED, that import puts torch in sys.modules, and the plan's own acceptance gate requires the record builder to stay torch-free. The TEST imports the real module and asserts the two agree, which is where a two-second torch import belongs."
  - "write_point_record's `tracked` is a REQUIRED keyword, not an optional one. prove_first_attempt is D-10's rule and an optional argument is a rule a driver can forget; phase25_prereg deliberately runs no subprocess, so the git ls-files result stays the caller's to produce and the write path stays unit-testable without a repository."
  - "point_key REFUSES a non-finite or negative axis value. Both would render a charset-legal key (`sigmanan`, `ratio-1p000000`) and file a nonsense point inside a pre-registered ordered set — 24-REVIEW WR-01's defect one layer up, and the 'guard refuses a NAME where the harm is a PROPERTY' class Phase 20 recorded twice."
  - "The point-key value is rendered at SIX DECIMALS with the point written `p`, inherited from Phase 23's own `phase23_noised_dp_n64_sigma0p500000.json` and forced by phase25_prereg.point_record_path's charset refusal. The KEY round-trips; the FLOAT does not (1.9090909090909092 renders 1.909091), so the record's own `sigma` / `ratio` field is authoritative and the key is a label."
  - "The record's condition-(c) group is asserted set-equal to phase25_condition_c.CONDITION_C_FIELDS at BUILD time, so a dropped field is a halt rather than an uncomputable verdict discovered at assembly."

patterns-established:
  - "Five separately NAMED halt tests kept in step with a five-member pin by an AST walk over the test file itself — a hand-written parametrization that goes RED when a sixth field arrives unwatched."
  - "A plan-time figure re-measured and corrected in the module docstring rather than inherited (37 top-level keys, not 35), with the load-bearing half of the claim shown to reproduce exactly."
  - "The atomicity proof is a NEGATIVE observation: after a failed write the destination is absent AND the directory holds no temp residue."

metrics:
  duration: "~35 min (first commit 20:52:56-03:00, SUMMARY commit same session; full-suite verification 1194 s of it)"
  completed: 2026-08-31
  tasks: 2
  files_created: 2
  lines: 1824
  tests_added: 37
---

# Phase 25 Plan 08: The Per-Point Record and D-34's Live Halt — Summary

A per-point record that **cannot be constructed in a diverged state**: five mechanism fields read
live and compared under exact `==` before the dict exists, `q` sourced from the frozen
`mitigation_unit.SAMPLING_RATE_Q`, and an atomic write behind both per-point refusals.

## What Was Built

**`scripts/phase25_record.py`** (945 lines) — the unit that is simultaneously D-10's one-attempt
evidence, D-09's resume boundary and D-31's assembly input.

- **D-34's live halt.** `MECHANISM_PIN_FIELDS = ("composed_steps", "composed_lot_sizes",
  "records_per_lot", "q", "clip_norm")` and `prove_mechanism_matches_pin(live, pinned, *,
  point_key)`. Exact `==` on all five including the float `clip_norm`; an absent field is treated
  as a divergence, not a match. `SystemExit` names the field, both values, the point key and the
  whole-sweep halt. `build_point_record` calls it **before any other work**, so no record object
  exists in a diverged state.
- **`q`, the one genuinely new field**, read live from `mitigation_unit.SAMPLING_RATE_Q = 1.0`,
  with D-26's reason quoted at the definition site.
- **The paths (D-31).** `FRONTIER_RECORD = results/phase25_frontier.json` — this module owns the
  name, nothing else spells it. `point_record_path` **delegates** to
  `phase25_prereg.point_record_path` and the writer/glob agreement is proved by `fnmatch` **at
  import**. `_PUBLICATION_PATHSPEC` in `phase24_record.py`'s shape, frontier artifact excluded.
- **The key grammar.** `point_key` / `parse_point_key` / `ORDERED_POINT_KEYS()`, the last resolving
  `SIGMA_LADDER` by `getattr` at **call** time with a refusal naming plan 25-12 as its producer.
- **The field groups.** D-21's `epsilon_bearing_reading` (k asserted equal to the constant its
  source names), D-05's two tiers, D-36's `per_family_counts`, D-39's `refusal_column` (wiring both
  orphans), D-37(ii)'s `canary_population`, D-45's `condition_c_group`, D-48/D-49/D-50's
  `retention_disclosure`.
- **`write_point_record`** — `prove_first_attempt` then `refuse_existing_artifacts` then serialise
  then tmp + `fsync` + `os.replace`, with `refuse_if_dirty` deliberately **not** called and the
  reason stated in the docstring.

**`tests/test_phase25_record.py`** (879 lines, **37 tests, 0 skipped**).

## Verification

| Check | Result |
|-------|--------|
| `.venv/bin/pytest tests/test_phase25_record.py -q` | **37 passed** in 1.00 s, **0 skipped** |
| `-k "halts_the_whole_sweep"` | **5 passed**, 32 deselected — exactly one per pinned field |
| `-k "refusal"` | 4 passed, 33 deselected |
| `-k "condition_c or retention or counterfactual or nll_flag"` | **7 passed**, 30 deselected (≥ 6 required) |
| AST test-function count | **37** (≥ 21 required) |
| `pytest tests/test_phase20_prereg.py -k import_graph` | 1 passed |
| `pytest tests/ -q` | **1847 passed, 1 skipped**, 1194.22 s |
| `make lint` | All checks passed, 248 files already formatted |
| `git diff --exit-code` on the four frozen modules + `pyproject.toml` | clean |

**Full-suite delta vs. the 1810 passed / 1 skipped baseline: `+37 passed, +0 skipped`** — exactly
the 37 tests this plan adds. **Zero regressions.** The known-flaky
`test_phase23_resume.py::test_production_resume_epsilon_bit_identical` passed in the same run and
needed no isolated re-run.

### Natural RED

Taken from the file's **natural intermediate state**, never a planted-then-reverted probe:
`git archive a1cff8e` (the tree immediately before the Task 1 commit) into the scratchpad, the new
test file dropped in, run.

```
tests/test_phase25_record.py:52: in <module>
    import phase25_record as rec  # noqa: E402  (same)
E   ModuleNotFoundError: No module named 'phase25_record'
1 error in 0.23s
```

Every other Phase-25 sibling the file imports (`phase25_condition_c`, `phase25_epsilon`,
`phase25_gate05`, `phase25_prereg`) is already present in that tree, so the RED isolates exactly
the module this plan adds. **What it does not prove:** it does not prove each individual halt,
because the module has no natural intermediate state in which one of the five was missing. The
five halts are instead each watched firing on their own perturbation, and
`test_every_pinned_field_has_its_own_watched_halt` walks the test file by AST so a sixth pinned
field with no watched halt goes RED.

### The five verbatim `SystemExit` messages, one per pinned mechanism field

Each is quoted up to the per-field `Its source is …` clause; every message continues with
`MECHANISM_PIN_SOURCES[field]` and the full `MECHANISM_HALT_GOVERNS` paragraph.

```
[phase25_record] THE WHOLE SWEEP HALTS. Point 'dp_n8_sigma0p000000': the live mechanism field
'composed_steps' reads 199 while the pin is 200.

[phase25_record] THE WHOLE SWEEP HALTS. Point 'dp_n8_sigma0p000000': the live mechanism field
'composed_lot_sizes' reads [7] while the pin is [8].

[phase25_record] THE WHOLE SWEEP HALTS. Point 'dp_n8_sigma0p000000': the live mechanism field
'records_per_lot' reads 7 while the pin is 8.

[phase25_record] THE WHOLE SWEEP HALTS. Point 'dp_n8_sigma0p000000': the live mechanism field
'q' reads 0.9999999999 while the pin is 1.0.

[phase25_record] THE WHOLE SWEEP HALTS. Point 'dp_n8_sigma0p000000': the live mechanism field
'clip_norm' reads 999999.0 while the pin is 1000000.0.
```

The `q` message continues `Its source is mitigation_unit.SAMPLING_RATE_Q — THE ONE FIELD THE PHASE
23 SCHEMA LACKS (D-26)`, which is asserted in `test_a_diverged_q_halts_the_whole_sweep`.

## Measured corrections to plan-time prose

**1. `results/phase23_noised_dp_n64_sigma0p500000.json` has 37 top-level keys, not 35.**
The plan's `must_haves.truths` §R3 line and the plan's `read_first` both state **35**. Measured
with `len(json.loads(path.read_text()))`: **37**. The eleven keys the plan does not list are
`clip_bind_count`, `clip_bind_count_covers_steps`, `clip_is_binding`, `exports_adapter`,
`ppl_adapter_off`, `ppl_adapter_on`, `ppl_scored_targets`, `seed`, `t_matches_across_capacities`,
`t_n64`/`t_n8` and their two source fields.

**The conclusion survives, and its load-bearing half reproduces exactly.** Four of D-34's five
fields are present (`composed_steps`, `composed_lot_sizes`, `records_per_lot`, `clip_norm`) and
there is **no `q` key at all**, at either capacity — verified with `'q' in record`, not with
`.get('q')`, because `.get` returns `None` for both an absent key and a null one. Both readings are
published in the module docstring. This is the same shape `phase25_epsilon` already carries for its
own §C5 claim (43 stated, 51 measured, absent key reproducing).

**2. The field is `draws_per_question_source`, not `k_source`.** The plan's action (d) writes
"`k_source` naming `mitigation_budget.CURVE_K` or `FULL_FIDELITY_K`". The precedent D-21 itself
cites — `results/phase23_never_taught.json` — spells it `draws_per_question_source`, and that
spelling is used here so the sweep's records and Phase 23's read alike. `k_source` appears nowhere
in the repository.

## Deviations from Plan

### Auto-fixed / structurally strengthened

**1. [Rule 2 — missing critical functionality] `phase18_extraction`'s constants are read by AST,
not by import.**
- **Found during:** Task 1.
- **Issue:** The plan's action (d) says to read `gated_tier` / `reported_tier` from
  `phase18_extraction`, while the plan's own acceptance criterion requires the module to import
  neither torch nor numpy. Measured: `import phase18_extraction` puts torch in `sys.modules`.
- **Fix:** the four constants are read through `phase25_gate05._committed_literal`, the reader this
  phase already uses on the same frozen file for the same recorded reason. The **test** imports the
  real `phase18_extraction` and asserts `rec.GATED_TIER == p18.GATED_TIER` etc., so "both imported"
  is satisfied where the import costs nothing.
- **Files:** `scripts/phase25_record.py`, `tests/test_phase25_record.py`. **Commits:** 8c42bd6, 3aefc5e.

**2. [Rule 2 — security/correctness] `point_key` refuses a non-finite or negative axis value.**
- **Issue:** `phase25_prereg.point_record_path` refuses by CHARSET, and `sigmanan` /
  `ratio-1p000000` are both charset-legal. A NaN or negative ratio would file a nonsense point
  inside a pre-registered ordered key set — 24-REVIEW WR-01's defect (fixed under D-41) one layer
  up, and the "guard refuses a NAME where the harm is a PROPERTY" class PROJECT.md records Phase 20
  hitting twice.
- **Fix:** two `_prove`s on the property, watched RED in
  `test_the_point_key_grammar_round_trips_and_orders`. **Commit:** 8c42bd6.

**3. [Rule 2] The reported-column disjointness is enforced at BUILD time, not only asserted in the
test.**
- **Issue:** The plan asks the test to prove the refusal column and `gate05_reported` are disjoint
  from the verdict's 21 kwonly args. A test proves today's names do not collide; it does not stop
  tomorrow's from colliding.
- **Fix:** `prove_names_are_outside_the_gate` runs inside `refusal_column` and inside
  `build_point_record`, resolving the 21 names through `inspect.signature` (never grep — that file
  discusses every one of them in its own prose). The test asserts both halves: today's names are
  disjoint, **and** a planted `{"control_gap"}` / `{"point_retention_ppl"}` raises `SystemExit`.
- **Commit:** 8c42bd6.

**4. [Rule 2] `write_point_record`'s `tracked` argument is REQUIRED.**
- **Issue:** The plan's action (e) names only `refuse_existing_artifacts` in the write path while
  stating the per-point refusal is that **plus** `phase25_prereg.prove_first_attempt`. An
  un-invoked rule is not a rule.
- **Fix:** `prove_first_attempt` is called first, from a required keyword argument, so a driver
  cannot omit it. `phase25_prereg` still runs no subprocess — the `git ls-files` result stays the
  caller's to produce, which is also what keeps the write path testable without a repository.
- **Commit:** 8c42bd6.

**5. [Rule 2] `epsilon_bearing_reading` asserts `k == K_SOURCES[source]`.**
- **Issue:** D-21 requires the source string beside the number. Nothing in the plan stops a reading
  claiming `mitigation_budget.CURVE_K` while carrying 48 — the attribution that was supposed to
  prevent the confusion, wearing it instead.
- **Fix:** the k is checked against the constant its source names; watched RED in
  `test_a_k16_and_a_k48_reading_are_distinguishable`. **Commit:** 8c42bd6.

**6. Field-naming choices left to discretion.** `POINT_KEY_GRAMMAR` at six decimals with `p`
(inherited from Phase 23's own filenames and forced by the prereg charset rule); the retention
disclosure carried as flat top-level `retention_*_governing` / `retention_*_borrowed` fields beside
the `condition_c` group, with `verdict_reads` naming which one the verdict consumes.

### Not fixed — recorded

**`build_point_record` is a pure assembler; it measures nothing.** Every reading (per-question
rows, per-family counts, refusal completions, the capability pair, the exposure blocks, the
adapter digest) arrives as a caller-supplied argument. That is the interface this plan was asked to
build, and the measurement wiring lands in plans 25-10 (driver), 25-14 (launch) and 25-16/25-17
(the real runs). It is named here so nobody reads the green test file as evidence that any of those
quantities has been measured.

## Phase 24 HUMAN-UAT item 3 is **NOT** closed

`test_the_refusal_wiring_calls_the_orphaned_helpers` proves the **wiring half only**:
`score_refusal` and `clean_frame_probe_populations` appear as calls in `scripts/phase25_record.py`,
and `refusal_column` returns integer `(k, n)` per family with a total and a denominator
provenance. **A wired column proves the schema, not that any refusal was ever counted.** Item 3
closes only when the criterion over `results/phase25_point_adv_*.json` — integer `k` and `n` per
family across all four `ATTACK_FAMILIES`, non-zero denominators, totals re-deriving from their own
rows — passes on **real trained adapters**, in plan **25-16** (wave 9), and again across all 44
records in **25-17** (wave 10).

## Known Stubs

None. Every value the module computes is read from a committed record (`phase19_arm_erased.json`,
`phase19_noise_floors.json`, `phase20_retention_floor.json`, `phase21_multiplicity.json`), computed
from a frozen module (`mitigation_gate.retention_cap`, `mitigation_budget.CURVE_K`,
`mitigation_unit.SAMPLING_RATE_Q`), or hashed from bytes on disk. No hardcoded empty collection, no
placeholder string, no `TODO`/`FIXME`. The caller-supplied arguments listed under *Not fixed* are
an interface, not a stub — the plan scopes measurement to later waves.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema change at a trust
boundary. The two new write surfaces are `results/phase25_point_*.json` (behind two refusals and an
atomic replace) and nothing else; the module opens no checkpoint and imports no framework.

## Self-Check: PASSED

```
FOUND: scripts/phase25_record.py
FOUND: tests/test_phase25_record.py
FOUND: .planning/phases/25-frontier-sweep-and-the-existence-gate-verdict/25-08-SUMMARY.md
FOUND: 8c42bd6  feat(25-08): per-point record schema with D-34's five-field live halt
FOUND: 3aefc5e  test(25-08): five watched halts, and every reported column proved outside the gate
UNTOUCHED: .planning/STATE.md, .planning/ROADMAP.md
UNTOUCHED: the four ancestry-guarded modules and pyproject.toml (git diff --exit-code clean)
```
