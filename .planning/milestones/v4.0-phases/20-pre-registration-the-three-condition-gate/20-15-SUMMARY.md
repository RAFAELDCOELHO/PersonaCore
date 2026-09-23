---
phase: 20-pre-registration-the-three-condition-gate
plan: 15
subsystem: gate-correction
tags: [pre-registration, gate-02, t-20-19, gap-closure-wave-2, watched-red, d-38, d-41]
requires:
  - "20-13 (D-38 and D-41, the two decisions this plan implements)"
  - "20-14 (the per-element Y-leg guards; this plan's base at 393d439)"
  - "20-REVIEW-GAP-CLOSURE.md GC-01, GC-02 (the magnitude bound) and GC-06 (the import census)"
provides:
  - "A MAGNITUDE bound on the retention floor — _MAX_ADMISSIBLE_RETENTION_FLOOR, derived from the governing floor times a separately-named tolerance, placed AFTER the != so the named-value refusal still fires first"
  - "The D-41 harness rewire: _corrected_call supplies the governing floor READ from results/phase20_retention_floor.json, because the frozen fixtures' fabricated 0.009 is the bound's first catch"
  - "Two D-38 tripwire cases driven THROUGH corrected_point_verdict, each asserting its harm as an inequality and asserting WHICH guard fired"
  - "An ast.ImportFrom census that no alias can hide, with a synthetic non-vacuity control because the real tree yields zero import hits"
  - "A tolerance pin closing the failure mode D-41 forbids, added because BREAK 2 measured the suite GREEN under a 5e7-fold widening"
  - "Three watched-RED breaks with byte-identical restores, for 20-SECURITY.md's Watched-RED table"
affects:
  - "20-17 — T-20-75..T-20-78 are discharged here; the re-close to threats_open: 0 is gated on this evidence"
  - "GC-07 (the module constant retyped from the artifact) remains OPEN; this plan's drift catch is one-directional and says so"
tech-stack:
  added: []
  patterns:
    - "Refuse by NAME and by PROPERTY as a PAIR, with the ordering stated in a comment because it is load-bearing: the name refusal publishes numbers the property refusal would pre-empt"
    - "A tolerance is a NAMED constant, never buried in an expression, so a widening shows up in a diff as its own line"
    - "A break that produces GREEN is a finding, not a non-event: close it with an assertion, then re-run the break"
    - "A matcher's non-vacuity control runs the SAME function over a synthetic tree, never a re-implementation of it"
key-files:
  created: []
  modified:
    - "scripts/phase20_gate_coverage.py"
    - "tests/test_phase20_correction.py"
decisions:
  - "The magnitude bound is placed AFTER the != refusal, not before, because V20_RETENTION_NOISE_FLOOR is itself a member of the looser class and a bound running first would swallow the message publishing the three numbers the suite asserts by repr"
  - "BREAK 2 was measured GREEN exactly as 20-13 predicted, so the plan's contingency became the expected path: a tolerance pin was ADDED and is this plan's third commit"
  - "The full-suite count stays at 876, not higher: pytest counts FUNCTIONS and every new case went INSIDE an existing function, which the plan's own acceptance criterion REQUIRES"
metrics:
  duration: "~45 min"
  tasks_completed: 3
  commits: 3
  completed: 2026-08-21
---

# Phase 20 Plan 15: The Magnitude Bound and the Aliased-Import Census Summary

Closed GATE-02's residual (T-20-19) and GC-06 by refusing the retention floor for what it IS as well
as for what it is NAMED, rewiring the sanctioned route's harness to supply the governing floor rather
than widening the bound to admit a fabricated one, censusing the import an alias cannot hide — and
watching all three guards fail before trusting any of them.

## What Was Built

**Task 1 — both files** (`f163b1c`, +102/-8). One task, two files, because the bound and the harness
default cannot be split across commits without leaving the suite red in between.

- **(a) `scripts/phase20_gate_coverage.py`.** `_RETENTION_FLOOR_RELATIVE_TOLERANCE = 1e-9` and
  `_MAX_ADMISSIBLE_RETENTION_FLOOR = _ADAPTER_REGIME_RETENTION_FLOOR * (1.0 + tolerance)`, plus a
  fifth `_prove` placed **after** the `!=`. The docstring's `FOUR refusals` became `FIVE`, and its
  measured-false sentence — "a caller that lies about `regime` is still caught by the number itself"
  — was replaced with what the pair actually proves.
- **(b) `tests/test_phase20_correction.py`.** `DEFAULT_RETENTION_FLOOR` read from
  `results/phase20_retention_floor.json` at module scope, and `"retention_noise_floor"` added to
  `_corrected_call`'s `base` dict. `base.update(overrides)` still runs after, so every existing
  `refused(retention_noise_floor=...)` override still wins; `_corrected_call` was not restructured.

**Task 2 — `tests/test_phase20_correction.py`** (`763fc36`, +96/-4). Two cases inside
`test_the_retention_floor_tripwire_is_the_only_route_to_a_verdict`, both through the existing
`refused(...)` helper so the claim proved is REACHABILITY; and the census extended with an
`imported_aliases(tree)` local plus a synthetic control. Test-function count unchanged at **13**.

**Task 3 — three watched-RED breaks** (`9b010c8`, +16). Two produced no diff. The third,
BREAK 2, produced a **finding** and therefore a commit — see below.

## The Numbers, Re-Derived Here Rather Than Transcribed

Every figure below was produced by calling the committed modules in this session.

```
artifact floor (results/phase20_retention_floor.json) = 0.008681618994239138
module _ADAPTER_REGIME_RETENTION_FLOOR                = 0.008681618994239138   (equal)
_MAX_ADMISSIBLE_RETENTION_FLOOR                       = 0.008681619002920757
V20_RETENTION_NOISE_FLOOR                             = 0.06893
V20 * (1 + 2**-50)                                    = 0.06893000000000006    (!= V20 -> True)
retention_cap(nudged) == retention_cap(V20)           = 4.029 == 4.029 -> True (BIT-IDENTICAL)
retention_cap(5.0)                                    = 13.89114
retention_cap(governing)                              = 3.9085032379884783
fixture floor (all three FIXTURE_* dicts)             = 0.009
0.009 / governing                                     = 1.0366729991228745
retention_cap(0.009)                                  = 3.90914
```

**Which guard fires, measured on the committed module:**

| input | refused by |
| --- | --- |
| `V20 * (1 + 2**-50)` — the one-ULP nudge | **MAGNITUDE** |
| `5.0` under clean adapter provenance | **MAGNITUDE** |
| `0.009` — the frozen fixtures' fabricated floor | **MAGNITUDE** |
| `V20_RETENTION_NOISE_FLOOR` | **IDENTITY (`!=`)** — fires FIRST, as designed |
| the governing floor `0.008681618994239138` | **ADMITTED** (`returns None`) — the bound is not vacuous |

The ordering claim is not asserted by reading the source; it is asserted by which message came back.
The borrowed value is a member of the looser class, so a bound running first would have swallowed it
and the three `repr` numbers would never have been published.

## D-41: Bit-Unchanged, Checked Rather Than Claimed

The plan's load-bearing claim is that the harness may supply the governing floor because every
published verdict survives it. Measured against `results/phase20_gate_coverage_correction.json`, with
the substitution live and the code committed:

| published entry | payload | harness | match |
| --- | --- | --- | --- |
| `direction_i` | `PASS` | `PASS` | **True** |
| `direction_ii` | `INCONCLUSIVE` | `INCONCLUSIVE` | **True** |
| `direction_ii_on_clearing_fixture` | `INCONCLUSIVE` | `INCONCLUSIVE` | **True** |
| `heldout_coverage` | `INCONCLUSIVE` | `INCONCLUSIVE` | **True** |

**What DOES move, measured and recorded rather than glossed.** Exactly one reason string changes per
case — condition (c)'s, which prints the cap:

```
fixture floor : (c) retention PPL 3.9000 <= cap 3.89114 + k=2 x 0.009000 = 3.9091
governing     : (c) retention PPL 3.9000 <= cap 3.89114 + k=2 x 0.008682 = 3.9085
```

The governing cap is **TIGHTER** (3.9085 < 3.9091), so the substitution cannot buy a pass the fixture
floor would have withheld — it is strictly conservative, which is the only direction that makes the
rewire admissible. No committed artifact publishes the superseded string: `grep` for `3.9091` /
`0.009000` across `results/phase20_gate_coverage_correction.{json,md}` returns nothing (the one
`0.009…` hit is `raw_rate 0.009615384615384616`, i.e. 1/104, unrelated). `reasons[-1]` is identical
for the one case that asserts on it (`heldout_coverage`); it differs only for `direction_i`, where
condition (c) happens to be the last reason and no test reads it.

## Watched-RED Evidence — Three Breaks, All OBSERVED

Pre-break digests, recorded before any break:

```
962b1a26d5088238ce4eccd8241353efe98e29643c4928534b1052b7af29b5af  scripts/phase20_gate_coverage.py
be8f734d11c45403a569c2fa0c7cd0fd7c4b1dd17a27742d02c2cce1c82cebbf  tests/test_phase20_correction.py
```

| # | What was broken | Command | Observed output | Restore proof |
|---|---|---|---|---|
| 1 | The fifth `_prove` neutered (`_prove(` → `_BREAK_1_DELETED = (`) in `_prove_retention_floor` | `.venv/bin/python -m pytest tests/test_phase20_correction.py -q` | `FAILED …::test_the_retention_floor_tripwire_is_the_only_route_to_a_verdict` — `E Failed: DID NOT RAISE <class 'SystemExit'>` at `tests/test_phase20_correction.py:949`, reached from `message = refused(retention_noise_floor=nudged)` at `:1010`, with `overrides = {'retention_noise_floor': 0.06893000000000006}` in the frame. **`1 failed, 12 passed in 0.40s`** | `shasum -a 256` → `962b1a26…9b5af` (**equal**); `git diff --exit-code -- scripts/phase20_gate_coverage.py` → **0** |
| 2a | `_RETENTION_FLOOR_RELATIVE_TOLERANCE` widened `1e-9` → `0.05` (**before** the pin existed) | same | **`13 passed in 0.61s`** — NOTHING reddened. Ceiling became `0.009115699943951094`, which ADMITS the fabricated `0.009` while still refusing both tripwire cases | n/a — this state is the FINDING |
| 2b | The same widening, **after** adding the tolerance pin | same | `FAILED …::test_the_retention_floor_tripwire_is_the_only_route_to_a_verdict` — `E AssertionError: the admissible ceiling 0.009115699943951094 now ADMITS the fabricated fixture floor 0.009. …` / `E assert 0.009115699943951094 < 0.009` at `tests/test_phase20_correction.py:1028`. **`1 failed, 12 passed in 0.63s`** | `shasum -a 256` → `962b1a26…9b5af` (**equal**); `git diff --exit-code` → **0** |
| 3 | Scratch `scripts/_wr07_probe.py` with `from mitigation_gate import mitigation_point_verdict as mpv` and `mpv(arm="dp")` | `.venv/bin/python -m pytest "tests/test_phase20_correction.py::test_mitigation_point_verdict_has_no_caller_outside_this_module" -q` | `E AssertionError: 1 call site(s) or import(s) reach a v4.0 verdict through the frozen pin directly … ['scripts/_wr07_probe.py:3 (imported as mpv)']` at `:1198`. **`1 failed in 0.26s`** | Probe deleted; `test ! -e scripts/_wr07_probe.py` **succeeds**; `git status --porcelain scripts/` **empty** |

**BREAK 3's control — would it have reddened at HEAD?** No, and that is the point of the half GC-06
asked for. Run over the probe's own AST:

```
call nodes          : [('Name', 'mpv', 7)]
call matcher hits   : []            <- the pre-existing .id/.attr matcher sees NOTHING
import matcher hits : [(3, 'mpv')]  <- the new ImportFrom matcher sees it
```

**Failure attribution, checked rather than assumed** — the sibling-plan failure mode where a break
reddens a *pre-existing* assertion and Python never reaches the intended one:

- **BREAK 1** failed at the THIRD statement of the new CASE 1. The two assertions above it —
  `nudged != V20` and `nudged_cap == borrowed_cap` — both **evaluated and passed** first (visible in
  the quoted traceback), which is correct: neither depends on the deleted `_prove`. Every case above
  CASE 1, including the borrowed-value block and its three `repr` assertions, also passed. The
  `DID NOT RAISE` is the new magnitude refusal and nothing else.
- **BREAK 2b** failed at the new tolerance pin itself, by line number (`:1028`) and by message text.
- **BREAK 3** failed on the new `(imported as mpv)` entry, which only the new matcher can produce.

Neither break was ever staged: `git status --porcelain scripts/` measured **empty** at commit time,
and `git diff f163b1c~1..HEAD --stat -- scripts/mitigation_gate.py scripts/erasure_gate.py` is
**empty** across all three commits.

## Verification Evidence — Every Must-Have, By A Command Actually Run

| Must-have | Command output |
|---|---|
| one-ULP nudge raises `SystemExit` | `nudge -> refused by MAGNITUDE` |
| `5.0` under clean provenance raises | `5.0 -> refused by MAGNITUDE` |
| fixture `0.009` raises (D-41) | `fixture 0.009 -> refused by MAGNITUDE` |
| borrowed value raises via `!=` FIRST, message carries all three `repr` numbers | plan's Task-1 verify script → `ok` (the script raises `AssertionError('the named-value refusal did not fire…')` if it does not) |
| governing floor ADMITTED — bound not vacuous | `_prove_retention_floor(...) is None` → **True**; `DEFAULT_RETENTION_FLOOR <= _MAX_ADMISSIBLE_RETENTION_FLOOR` → **True** |
| `_MAX_ADMISSIBLE_RETENTION_FLOOR` derived, not typed | `== _ADAPTER_REGIME_RETENTION_FLOOR * (1.0 + _RETENTION_FLOOR_RELATIVE_TOLERANCE)` → **True** |
| no published number typed in either file | `grep -n '0\.008681619002920757\|13\.89114\|3\.90914'` on both → **no hits** |
| census flags the aliased import in a synthetic tree | `imported_aliases(ast.parse("from mitigation_gate import mitigation_point_verdict as mpv\n"))` → `[(1, 'mpv')]` |
| zero real bypassing imports | `bypassing == []` on the real `scripts/` + `src/` walk → **passes** |
| `ast.ImportFrom` present in the test file | AST audit → `ast.ImportFrom present` |
| `grep -c '2\*\*-50' tests/test_phase20_correction.py` | **1** (≥1 required) |
| test-function count still 13 | AST count → **13** |
| both guards observed RED, module restored byte-identically | Watched-RED table — digest equal **twice**, `git diff --exit-code` → 0 **twice** |
| frozen pins untouched | `git diff --exit-code -- scripts/mitigation_gate.py scripts/erasure_gate.py` → **0**; `git diff f163b1c~1..HEAD --stat` on the same two paths → **empty** |
| probe gone at commit time | `test ! -e scripts/_wr07_probe.py` → succeeds; `git status --porcelain scripts/ tests/` → **empty** |
| phase-20 pair | **`31 passed in 2.01s`** — no `skipped`, no `xfail` |
| the two extended tests by explicit node id | **`2 passed in 0.27s`** |
| ancestry guard by its REAL node id | `test_phase20_prereg_is_frozen_before_every_phase20_result` → **`1 passed in 0.84s`** |
| all four published verdicts bit-unchanged | 4/4 `match=True` (table above) |
| lint | `All checks passed!` / `176 files already formatted` |
| **full suite** | **`876 passed, 1 skipped, 83 warnings in 202.09s`** |

## The Full-Suite Number, Reconciled Honestly

**Measured: 876 passed / 1 skipped. The baseline at `393d439` was 876 passed / 1 skipped. The number
did not move, and that is the CORRECT outcome — not a shortfall.**

The executor prompt asserted: *"your four tripwire cases plus the import census must push it
HIGHER."* That expectation is falsified by the plan's own Task-2 acceptance criterion, which
**requires** `13` test functions and states the reason: *"the two retention cases went INSIDE the
existing function and the census was EXTENDED, not duplicated."* pytest counts **functions**, not
assertions. Every new case in this plan is an assertion inside a pre-existing function, by design —
because the two names being extended are cited verbatim in two shipped docstrings
(`scripts/phase20_gate_coverage.py`) and in `20-SECURITY.md`'s T-20-48 row, so creating new functions
would have orphaned those citations.

A number **above** 876 would therefore have been evidence that the plan's structural requirement was
violated. The real growth is measurable and is reported instead: the tripwire function went from
**8 to 10 runtime refusals** (8 static `refused()` call sites, two of which are loops), and the
census gained a second matcher plus its own non-vacuity control.

## Deviations from Plan

### Auto-fixed Issues

None. No bug, no missing critical functionality and no blocking issue. Two `ruff` E501 line-length
errors were produced by my own first draft of the refusal message and the CASE-1 assertion, and
re-wrapped in place (the second by hoisting `nudged_cap` / `borrowed_cap` into locals, which is
shorter than wrapping). Not deviations — draft mechanics.

### Plan-vs-Reality Mismatches Recorded, Not Amended

1. **Every line anchor the plan gives into `tests/test_phase20_correction.py` is stale, and one into
   `scripts/phase20_gate_coverage.py` is too.** Measured at base `393d439` before any edit:

   | plan cites | measured at base | what it is |
   | --- | --- | --- |
   | `phase20_gate_coverage.py:353-406` | **`:384-437`** | `_prove_retention_floor` |
   | `test_phase20_correction.py:759` | **`:896`** | the retention tripwire |
   | `:776-786` | **`:913-923`** | its `refused()` helper |
   | `:804-816` | **`:938-953`** | the borrowed-value block |
   | `:810-816` | **`:947-953`** | the three-number `repr` assertion |
   | `:824-835` | **`:961-972`** | WR-08 at both magnitudes |
   | `:840-847` | **`:974-984`** | the positive control |
   | `:901` | **`:1038`** | the census |
   | `:920-921` | **`:1057-1058`** | `definition` / `sanctioned` |
   | `:925-936` | **`:1060-1073`** | the walk |
   | `:952-957` | **`:1089-1094`** | the non-vacuity assertion |

   Only `_corrected_call`'s `base` at `:136-139` matched. Both files are **unpinned**, so this is the
   same anchor-rot `20-13` recorded five instances of; every anchor above was re-measured in this
   session and none is written into code. The plan was **not** amended.

2. **`20-SECURITY.md:39` and `:33`, cited in this plan's `<threat_model>`, are stale.** Per `20-13`'s
   drift map they are now `:43` and `:37`. No stale anchor is written anywhere in this SUMMARY — the
   two trust boundaries are referred to by **text** ("a plan that says a thing will be done ↔ a guard
   that proves it was"; "measured floor ↔ borrowed floor").

3. **BREAK 2's "contingency" was the expected path, exactly as `20-13` measured.** The plan hedged
   *"adding one if none does"*. None did: the suite was **`13 passed`** under a widening of
   `1e-9` → `0.05`, a factor of **5×10⁷**, which admits the fabricated `0.009` while still refusing
   both tripwire cases. So this plan lands **three** commits, and the third is the pin. Recorded as a
   finding because it is one: before it, the tolerance was a rubber stamp that no committed test
   could distinguish from a real bound.

4. **Six new module constants, not two.** The plan names two (`_RETENTION_FLOOR_RELATIVE_TOLERANCE`,
   `_MAX_ADMISSIBLE_RETENTION_FLOOR`) and separately requires *"Compute every number by calling the
   frozen `retention_cap` and the module constants; type none of them."* Satisfying both needs four
   more: `_LOOSE_FLOOR_REPRODUCTION`, `_LOOSE_FLOOR_REPRODUCTION_CAP`, `_FIXTURE_RETENTION_FLOOR`,
   `_FIXTURE_FLOOR_RATIO`. They are precomputed at module scope in the existing register of
   `_BORROWED_CAP` / `_GOVERNING_CAP` / `_BORROWED_FLOOR_RATIO` — and precomputed rather than inlined
   because `_prove`'s message argument is an f-string evaluated **eagerly on every call**, including
   passing ones, so a `retention_cap` call inside it would run on every verdict.

5. **`_FIXTURE_RETENTION_FLOOR` is read from `FIXTURE_CLEARING_POINT`, and only two of the three
   fixtures carry the literal.** `grep -n "0\.009" scripts/mitigation_gate.py` returns exactly two
   sites — `:1237` (annotated `# fabricated`) and `:1267`; the third fixture inherits. Reading rather
   than retyping means the refusal message and the test pin both travel if that value ever moved
   (it cannot — the pin is frozen — but the discipline is the point).

6. **The `bypassing == []` message was widened to "call site(s) or import(s)".** The list can now
   contain import entries, and a message that says "call site(s)" while listing an import is a
   message that misdirects its reader.

### Not Touched, Deliberately

`STATE.md`, `ROADMAP.md` and `REQUIREMENTS.md` are absent from the plan's `files_modified`, so no
`gsd-sdk` `state.*` or `roadmap.*` mutation handler was invoked and `GATE-02` was **not** marked
complete. `20-SECURITY.md` remains `status: blocked` / `threats_open: 1` with T-20-19 open — correct
for this wave; `20-17` owns the re-close. `.planning/` is untouched by all three task commits.

## Threat Flags

None. No network endpoint, no auth path, no new file access on the module side (it remains stdlib
plus two sibling scripts — its docstring's "no file I/O" claim still holds, since the artifact read
lives in the test file), no schema, and no package-manager install. `pyproject.toml` untouched, so
T-20-SC (accepted) holds. This plan's own register is discharged rather than deferred:

- **T-20-75** (a looser floor reaching a v4.0 cap under clean provenance) — mitigated. The bound is
  called FIRST in `corrected_point_verdict`, before any compute, and both cases are asserted THROUGH
  the route via `refused(...)`, so the claim proved is reachability rather than helper existence.
- **T-20-76** (the tolerance widened until a value already in hand passes) — mitigated, and it needed
  to be: BREAK 2 measured the suite green under exactly that widening. `_RETENTION_FLOOR_RELATIVE_TOLERANCE`
  is a named constant, and the pin at `test_..._is_the_only_route_to_a_verdict` reddens on any
  widening that reaches the fabricated `0.009`.
- **T-20-77** (an aliased import bypassing the choke point invisibly) — mitigated for the IMPORT.
  The two residuals are **RECORDED IN THE DOCSTRING, not implied closed**: `getattr(mitigation_gate,
  "mitigation_point_verdict")(...)` is invisible to both matchers, and the walk is scoped to
  `scripts/` + `src/`, so a driver at the repo root or under `tools/` is unpoliced.
- **T-20-78** (the harness's substituted floor drifting from the artifact) — mitigated, **partially
  and named as partial**. `DEFAULT_RETENTION_FLOOR` is READ, never retyped. But
  `coverage._ADAPTER_REGIME_RETENTION_FLOOR` is still a transcription of the same number (GC-07, out
  of scope here), so the catch is **one-directional**: a drift making the module constant TIGHTER
  than the artifact reddens every call; a drift making it LOOSER is not caught here at all. This is
  stated in `_corrected_call`'s docstring rather than claimed as GC-07's closure.

## Known Stubs

None.

## Self-Check: PASSED

- `scripts/phase20_gate_coverage.py` — FOUND, contains `_MAX_ADMISSIBLE_RETENTION_FLOOR`, digest
  `962b1a26d5088238ce4eccd8241353efe98e29643c4928534b1052b7af29b5af`
- `tests/test_phase20_correction.py` — FOUND, contains `DEFAULT_RETENTION_FLOOR`, 13 test functions,
  digest `0a76832d2f7ca6999097f040e55201b5187d6587ab2fee00d6b25daa3a9524c4`
- `scripts/_wr07_probe.py` — CORRECTLY ABSENT
- `f163b1c` — FOUND
- `763fc36` — FOUND
- `9b010c8` — FOUND
