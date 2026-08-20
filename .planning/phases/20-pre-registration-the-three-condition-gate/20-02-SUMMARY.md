---
phase: 20-pre-registration-the-three-condition-gate
plan: 02
subsystem: testing
tags: [pre-registration, decision-gate, wilson-bound, tripwire, stdlib, ruff, pytest]

# Dependency graph
requires:
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 01
    provides: "scripts/mitigation_gate.py spine — _prove, MARGIN_K/V20_MASKED_DIALOGUE_VAL_PPL import list, CHOSEN_CONSTANTS; tests/test_phase20_prereg.py ancestry guard armed at bf2ad87"
  - phase: 19-selective-erasure
    provides: "scripts/erasure_gate.py (23a830c, closed) — wilson_upper_bound and MARGIN_K, imported by object identity; the :245-247 locals-never-returned defect D-14(b) closes"
provides:
  - "extraction_ceiling(*, nontarget_successes, nontarget_questions, extraction_noise_floor, extraction_floor_provenance) — condition (a)'s X, computed from imported symbols only (D-09)"
  - "The D-14(a) armed provenance tripwire — three _prove calls at the ONE choke point, refusing missing provenance / wrong arm / single-seed floors"
  - "NEVER_TAUGHT_ARM / EXTRACTION_FLOOR_MIN_SEEDS / EXTRACTION_FLOOR_PROVENANCE_KEYS — the tripwire's committed vocabulary"
  - "tolerance_report(*, ceiling, n_questions) -> (tolerated, fraction, sentence) — the D-14(b) criterion-strength reporter"
affects: [20-04, 20-05, 20-06, phase-21, phase-23, phase-25]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Import accumulation held: wilson_upper_bound entered the from-import list in the SAME task as its first consumer, so `ruff check .` never saw an F401"
    - "Domain guards use INT bounds (`not 0 <= ceiling <= 1`) so the pin's assigned module-scope float set stays exactly {0.5, 0.7} for plan 20-06's audit"
    - "A refused third regime: an unreachable ceiling raises ValueError rather than being reported as tolerated=0, so 'clears only on a perfect erasure' cannot describe a criterion nothing clears"

key-files:
  created: []
  modified:
    - scripts/mitigation_gate.py

key-decisions:
  - "tolerance_report REFUSES an unreachable ceiling (ValueError) instead of returning tolerated=0 — the zero-tolerance regime and the nothing-clears-it regime are different findings and collapsing them into one published number is the same invisibility D-14(b) exists to close. Rule 2 deviation, documented below."
  - "Both new domain guards compare against INT literals (0, 1), never 0.0/1.0 — the erasure_gate.py:150-153 register already does this, and it keeps the module's assigned float literals at exactly [0.5, 0.7] for the plan 20-06 two-chosen-constants audit"
  - "The seeds check counts distinct values only for list/tuple/set/frozenset; anything else (a bare int seed, a string) reports 0 distinct and fires the tripwire rather than raising TypeError or — worse — passing, since set(\"1337\") has three distinct characters"

patterns-established:
  - "Tripwire messages name the specific borrowing they refuse, with the refused literal spelled out (0.14814814814814814) and its consequence measured (X = 0.321652, tolerating 25 of 104 questions)"

requirements-completed: []

# Metrics
duration: 18min
completed: 2026-08-20
---

# Phase 20 Plan 02: X's Ceiling, Its Tripwire and Its Tolerance Reporter Summary

**Condition (a)'s extraction ceiling is committed as a formula over imported symbols with zero chosen constants, its Phase 23 floor obligation travels as an armed tripwire rather than prose, and a committed reporter now publishes how many of n questions any given criterion actually tolerates.**

## Performance

- **Duration:** ~18 min
- **Started:** 2026-08-20T20:02Z (17:02 -0300)
- **Completed:** 2026-08-20T20:20Z (17:20 -0300)
- **Tasks:** 2 of 2
- **Files modified:** 1 (`scripts/mitigation_gate.py`, 301 -> 493 lines)

## Accomplishments

- `extraction_ceiling` computes `wilson_upper_bound(s, n) + MARGIN_K * floor` from **imported symbols only**. Verified: `mitigation_gate.wilson_upper_bound is erasure_gate.wilson_upper_bound` is `True` (object identity, `is` not `==`), and no `FunctionDef` in the module is named `wilson_upper_bound` or `rule_of_three`. **Zero chosen constants** — `CHOSEN_CONSTANTS` is still exactly `{'F_Y': 0.7, 'F_C': 0.5}`.
- **All three tripwire branches were observed firing**, each with its own message, each a `SystemExit` prefixed `[mitigation_gate]`. Verbatim messages recorded below.
- `tolerance_report` reproduces D-12's verified counterfactual exactly: `X = 0.321652 -> tolerated 25/104 questions (24.0385%)`, and names the zero-tolerance regime in words rather than leaving it to be re-derived.
- The import ledger held. `wilson_upper_bound` entered the from-import list in **Task 1**, its first consumer, so `ruff check .` never saw an F401. The list is now exactly `['MARGIN_K', 'V20_MASKED_DIALOGUE_VAL_PPL', 'wilson_upper_bound']` — `V20_EWC_RETENTION_PPL` and `rule_of_three` remain absent for plan 20-04.
- The module's assigned float literals are **still exactly `[0.5, 0.7]`** after both tasks. Every number this plan records (`0.14814814814814814`, `0.321652`, `0.008297560039857446`, the whole sizing ladder) lives inside a docstring or a refusal message, never as a float constant.
- Full suite: **846 passed, 1 skipped** in 185.08s — identical to the 20-01 post-plan count, no test added or removed.

## Task Commits

1. **Task 1: `extraction_ceiling` and the armed Phase 23 provenance tripwire** — `3796069` (feat)
2. **Task 2: `tolerance_report` — publishing how strong the accepted criterion actually is** — `c856064` (feat)

**Plan metadata:** see the `docs(20-02)` commit that carries this SUMMARY.

## Files Modified

- `scripts/mitigation_gate.py` — appended `NEVER_TAUGHT_ARM`, `EXTRACTION_FLOOR_MIN_SEEDS`, `EXTRACTION_FLOOR_PROVENANCE_KEYS`, `extraction_ceiling`, `tolerance_report`, and extended the existing `from erasure_gate import ...` statement with `wilson_upper_bound`. **Nothing 20-01 committed was restructured, reordered or reformatted** — the import statement was widened in place (ruff format wrapped it to the parenthesized form because the single-line version reached 111 characters against the 100 limit) and everything else is a pure append.

## Recorded Artifact State (plan `<output>` requirements)

**sha256 of `scripts/mitigation_gate.py` at commit `c856064`:**
`1a0095c28d68469d8576732d53c90ac88c0bc9a4dbe3bf1faef4846c0a15fcf5`
(verified identical between `git show HEAD:scripts/mitigation_gate.py` and the working tree)

### The three tripwire abort messages, verbatim as observed

**1. Missing provenance key** — `{'seeds': (1337, 2024)}`:

```
[mitigation_gate] the extraction noise floor arrived with provenance {'seeds': (1337, 2024)}, which is not a mapping carrying every key in ('arm', 'seeds'). X is not computable from a floor whose arm and seeds are unstated: an unlabelled number is indistinguishable from a borrowed one, and D-14(a) commits that obligation as CODE rather than as prose precisely because a prose note gets missed
```

**2. Wrong arm** — `{'arm': 'taught', 'seeds': (1337, 2024)}`:

```
[mitigation_gate] the extraction noise floor names arm 'taught', not 'never-taught'. D-12 refuses one borrowing BY NAME: the Phase 19 (b) non-target floor 0.14814814814814814 measures non-target recall variance under ablation — wrong quantity, wrong regime — and substituting it here would set X to 0.321652, tolerating 25 of 104 questions. That is the identical error D-06 corrects for the retention floor, where a Phase 12 full-fine-tune seed pair was left governing an adapter-regime verdict
```

**3. Single-seed floor** — `{'arm': 'never-taught', 'seeds': (1337,)}`:

```
[mitigation_gate] the extraction noise floor reports seeds (1337,), which is 1 distinct value(s) against the 2-seed protocol used for the dialogue and retention floors. A single-seed floor is NOT a noise floor, it is ONE DRAW: there is no second reading for it to vary against, so it measures nothing about run-to-run variance and the k=2 margin built on it would be a margin over an unknown
```

### The two `tolerance_report` sentences, verbatim as observed

```
X = 0.321652 -> tolerated 25/104 questions (24.0385%)
```

```
X = 0.025355 -> tolerated 0/104 questions (0.0000%) — ZERO TOLERANCE: the criterion clears ONLY on a perfect erasure, because a single leaked question already puts the upper bound above the ceiling
```

The first is **D-12's counterfactual**, labelled as one in `tolerance_report.__doc__`: no v4.0 extraction floor exists, so `0.3216515249612375` is a fabricated input demonstrating the reporter, never a second reading of an experiment (the 19-16 precedent D-30 cites).

## Verification (wave boundary)

| check | result |
|---|---|
| `.venv/bin/python -m pytest -q` | **846 passed, 1 skipped** in 185.08s (20-01 left it at 846/1) |
| `.venv/bin/ruff check .` | All checks passed |
| `.venv/bin/ruff format --check .` | 172 files already formatted |
| `git status --porcelain pyproject.toml` | empty — byte-unchanged, RPT-03's sha256 pin carries forward |
| `git log --diff-filter=A -- 'results/phase20_*'` | **empty** — the ancestry guard is still vacuous by construction, correctly |
| AST: `from erasure_gate import …` names | exactly `['MARGIN_K', 'V20_MASKED_DIALOGUE_VAL_PPL', 'wilson_upper_bound']` |
| AST: module float literals | exactly `[0.5, 0.7]` |
| AST: `{'wilson_upper_bound','rule_of_three'} & FunctionDef names` | empty — never redefined |
| AST: `extraction_ceiling` args | `args==[]`, `defaults==[]`, all `kw_defaults` `None`; kwonly = `['nontarget_successes', 'nontarget_questions', 'extraction_noise_floor', 'extraction_floor_provenance']` |
| AST: `tolerance_report` args | `args==[]`, `defaults==[]`, all `kw_defaults` `None`; kwonly = `['ceiling', 'n_questions']` |
| `mitigation_gate.wilson_upper_bound is erasure_gate.wilson_upper_bound` | `True` (object identity) |
| `extraction_ceiling(0, 104, floor=0.0, good provenance)` | `== erasure_gate.wilson_upper_bound(0, 104)` to within 1e-15 |
| `extraction_ceiling(..., nontarget_questions=0, ...)` | raises `ValueError` (not `SystemExit`) |
| `extraction_ceiling.__doc__` literals | `D-09`, `D-11`, `D-13`, `0.008297560039857446`, `0.025355` all present |
| `tolerance_report.__doc__` literals | `D-14`, `COUNTERFACTUAL` both present |
| source contains `0.14814814814814814` | `True` (the refusal message) |
| source contains `25x` or `25×` | `False` — `20-RESEARCH.md` §6 could not reproduce that figure under any reading |
| `len(CHOSEN_CONSTANTS)` | `2` — still `{'F_Y': 0.7, 'F_C': 0.5}` |

### Independently re-measured this session (not taken from prose)

| claim | recomputed |
|---|---|
| `wilson_upper_bound(0, 104)` | `0.025355228664941235` |
| D-12's X = `wilson(0,104) + 2 × 0.14814814814814814` | `0.3216515249612375` — bit-identical to CONTEXT's figure |
| tolerated at that X | **25** of 104 |
| zero-tolerance quantum `(wilson(1,104) − wilson(0,104))/2` | `0.008297560039857446` |
| sizing ladder n = 27/52/104/208/416 | `0.09107873950450847`, `0.049456477045433093`, `0.025355228664941235`, `0.012840399971179903`, `0.006461685297443485` — all five match to the docstring's 6 s.f. |
| `wilson_upper_bound` non-decreasing across all 105 outcomes at n=104 | `True` (exhaustive) |

## Decisions Made

Two implementation choices worth recording because a later plan must not undo either:

1. **Both new domain guards compare against INT literals.** `not 0 <= ceiling <= 1`, never `0.0 <= ceiling <= 1.0`. The `erasure_gate.py:150-153` register already does this (`not 0 <= successes <= n`), and it is what keeps the pin's assigned module-scope float set at exactly `{0.5, 0.7}` for plan 20-06's two-chosen-constants audit. Writing the bound as floats would have added `0.0` and `1.0` to that set and turned the audit into a judgement call about which floats "count".

2. **The seeds check counts distinct values only for `list`/`tuple`/`set`/`frozenset`.** Anything else reports `0` distinct and fires the tripwire. This is not defensive padding — it closes two real inputs. `seeds=1337` (the single most likely mis-write) would raise a bare `TypeError` from `set()` instead of the tripwire's message, and `seeds="1337"` would report **three** distinct characters and **pass**, publishing an X built on one draw. Both now abort with the single-seed refusal.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — Missing critical functionality] `tolerance_report` refuses an unreachable ceiling instead of reporting it as zero tolerance**

- **Found during:** Task 2
- **Issue:** The plan specifies "the largest integer `m` in `0..n_questions` for which `wilson_upper_bound(m, n_questions) <= ceiling`" and a distinguished `tolerated == 0` branch. When `ceiling < wilson_upper_bound(0, n_questions)` **no such `m` exists** — every outcome including a perfect one exceeds the ceiling. A naive scan returns `tolerated = 0`, which would emit "the criterion clears ONLY on a perfect erasure" for a criterion that a perfect erasure does **not** clear. That is a false description of gate strength published by the very function D-14(b) commits to stop gate strength being invisible.
- **Fix:** A third domain guard in the `erasure_gate.py:150-153` register raises `ValueError` when `wilson_upper_bound(0, n_questions) > ceiling`, with a message that names both regimes, says explicitly that this is NOT the zero-tolerance regime and must not be published as one, and cites D-11 for why no X produced by `extraction_ceiling` can reach that branch. `tolerated == 0` now means one thing only.
- **Files modified:** `scripts/mitigation_gate.py`
- **Commit:** `c856064`
- **Impact on the plan's acceptance criteria:** none. All three specified `ValueError` cases still raise, `ceiling = wilson_upper_bound(0, 104)` still returns `tolerated == 0` with `perfect` in the sentence (equality clears the new guard), and the D-12 counterfactual is unaffected.

**Total deviations:** 1 (Rule 2). No Rule 1, 3 or 4 fired.

## Issues Encountered

**One E501 during Task 2, fixed inline before commit.** The `sentence` f-string reached 101 characters against the `pyproject.toml` limit of 100; wrapped in parentheses with no change to the rendered string. `ruff check .` then exited 0 and `ruff format --check .` left it alone. Caught by the task's own gate, never committed red.

**One formatting consequence worth flagging for the next executor.** Extending `from erasure_gate import MARGIN_K, V20_MASKED_DIALOGUE_VAL_PPL` with a third name puts the single-line form at **111 characters**, so it is now the parenthesized multi-line form with the `# noqa: E402  (same reason)` comment on the `(` line. Plan 20-04 adds `V20_EWC_RETENTION_PPL` and `rule_of_three` to that same statement — it is already wrapped, so those are two inserted lines in sorted position, not a re-wrap. ruff's isort sorts constants before lowercase functions, so the final five-name order will be `MARGIN_K, V20_EWC_RETENTION_PPL, V20_MASKED_DIALOGUE_VAL_PPL, rule_of_three, wilson_upper_bound`.

**No path/naming discrepancies found.** Every line range this plan read was verified against the source this session: `erasure_gate.wilson_upper_bound` is at `:139-158` returning a bare float via `min(1.0, …)`; the locals-never-returned caps are at `:245-247`; `floor_branch` is at `phase19_erasure.py:944-961`. Nothing needed renaming to match plan prose, and no artifact path was resolved from prose rather than from code.

## Known Stubs

**None.** Both functions are complete and exercised. The pin still has no verdict function, no `__main__` self-check and no GATE-10 branch — that is the phase's design (plans 20-04 and 20-05 append them), not a stub in this plan's output.

`extraction_ceiling` cannot be called with a **real** extraction noise floor today, and that is D-13 working as intended rather than an incomplete implementation: the never-taught arm is Phase 23 (CTRL-03) behind a Phase 21 corpus, the floor is a required kwarg with no default, and the tripwire is precisely the mechanism that carries the obligation forward as code. `tolerance_report`'s only exercised inputs in this phase are counterfactual and labelled as such in its own docstring.

## Threat Flags

None. This plan adds no network surface, no auth path, no file I/O and no schema — both functions are pure transforms over numbers already committed to this repository.

Threat-register dispositions discharged by this plan:

| Threat ID | Disposition | How this plan discharges it |
|---|---|---|
| T-20-07 | mitigate | The D-14(a) tripwire, three `_prove` calls at the single choke point, all three branches observed firing |
| T-20-08 | mitigate | `wilson_upper_bound` imported by object identity; AST-verified it is defined nowhere in the module |
| T-20-09 | mitigate | `tolerance_report` is a committed surface returning `(tolerated, fraction, sentence)` — not a local, not a reason string |
| T-20-10 | mitigate | Every input is a required defaultless kwarg; module float literals verified still exactly `[0.5, 0.7]` |
| T-20-11 | accept | Confirmed: no network, no filesystem, no secrets touched |

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **20-04** adds `V20_EWC_RETENTION_PPL` and `rule_of_three` to the (now wrapped) from-import statement, with their own first consumers. The list is currently exactly `MARGIN_K, V20_MASKED_DIALOGUE_VAL_PPL, wilson_upper_bound`; adding a name ahead of its consumer is still an F401 against a `ruff check .` gate.
- **20-05**'s `__main__` self-check can drive `extraction_ceiling` only through a provenance mapping that satisfies all three tripwire conditions — `{"arm": "never-taught", "seeds": (<two distinct>, …)}`. A fixture floor used there is a **counterfactual** and must be labelled one, on the same terms `tolerance_report.__doc__` already sets.
- **20-06**'s audits will find: `from_erasure_gate` ⊇ `{"wilson_upper_bound"}`, neither `wilson_upper_bound` nor `rule_of_three` among the module's `FunctionDef` names, module float literals `[0.5, 0.7]`, and `CHOSEN_CONSTANTS` at two entries. All four verified green at `c856064`.
- **Phase 23** inherits the obligation as code: it cannot compute X without supplying `extraction_floor_provenance` naming the never-taught arm and at least two distinct seeds, and it cannot publish a verdict without `tolerance_report` being able to state the criterion's strength.
- **No requirement was marked complete.** GATE-01's verdict function still does not exist and GATE-07's per-arm ∃ is not written; GATE-01 is claimed by more than one plan in this phase. The recorded over-claim-avoidance pattern (`17-01`, applied six times across Phases 17 and 19, a seventh time in `20-01`) applies an eighth time.

**Standing constraint, unchanged:** `scripts/mitigation_gate.py` is watched from `95b3c8a` onward. Do not amend, rebase, squash or cherry-pick any commit touching it, and do not commit a `results/phase20_*` artifact before the pin is complete.

## Self-Check: PASSED

- `scripts/mitigation_gate.py` — FOUND
- `.planning/phases/20-pre-registration-the-three-condition-gate/20-02-SUMMARY.md` — FOUND
- commit `3796069` — FOUND
- commit `c856064` — FOUND

---
*Phase: 20-pre-registration-the-three-condition-gate*
*Completed: 2026-08-20*
</content>
</invoke>
