---
phase: 20-pre-registration-the-three-condition-gate
reviewed: 2026-08-21T00:00:00Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - scripts/phase20_gate_coverage.py
  - tests/test_phase20_correction.py
findings:
  critical: 3
  warning: 4
  info: 5
  total: 12
status: issues_found
---

# Phase 20 Gap Closure: Code Review Report

**Reviewed:** 2026-08-21T00:00:00Z
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Two new files: `scripts/phase20_gate_coverage.py` (the correction) and
`tests/test_phase20_correction.py` (the tripwires). The statistical core is sound — I verified the
load-bearing claims rather than reading them:

- **The mirror holds.** `wilson_lower_bound` shares `p`, `denom`, `centre`, `spread` with
  `erasure_gate.wilson_upper_bound:139-158` verbatim, clamp direction flipped. The
  `successes == 0` short-circuit is genuinely correct, not a comment over a bug: at `p = 0`,
  `spread = z*sqrt(z^2/4n^2) = z^2/2n = centre` identically, so the analytic lower bound is exactly
  `0` and the residue is what is wrong. The published survey **reconciles exactly** — over
  `n in 2..300` I measure **75** nonzero `centre - spread`, **20** negative and absorbed by the
  clamp, **55** leaking through, smallest `n = 11`. All four figures at `:155-159` are right.
- **The bound direction (D-37) is what the code does.** `mitigation_gate.py:756` decides (a) on
  `upper <= ceiling`; `:767-768` decide (b) on raw `>=`. `coverage_verdict:294-297` reads
  `v <= criterion` on extraction and `v >= criterion` on both recall legs. Criterion-matching, as
  documented.
- **Verdict precedence is coherent** and the sentinel provably neutralises
  `mitigation_gate.py:798-812` given the preconditions proved at `:536-552`.

What the review found is that **every guard on the retention leg and both Y legs is weaker than its
own docstring claims**, and each hole is reachable through `corrected_point_verdict` with a clean
call. Three of them yield a **PASS** off inputs the choke point was written to refuse. The extraction
leg — the one CR-01 was about — is validated three ways; the four axes added by this gap closure are
validated by a length check.

Reproductions below were executed against the committed tree with `.venv/bin/python`.

## Critical Issues

### GC-01: The borrowed-floor refusal is defeated by a one-ULP nudge, and the nudge buys a bit-identical cap

**File:** `scripts/phase20_gate_coverage.py:396-406`

**Issue:** The fourth refusal — the one with no counterpart on the extraction leg, and the one
T-20-19's whole closure rests on — is `retention_noise_floor != V20_RETENTION_NOISE_FLOOR`. Float
`!=` is bit-pattern inequality, not numeric distinguishability. Measured:

```
floor = V20_RETENTION_NOISE_FLOOR * (1 + 2**-50)   # 0.06893 + 1 ULP-ish
floor != V20_RETENTION_NOISE_FLOOR                 -> True   (refusal does not fire)
retention_cap(floor) == retention_cap(V20_...)     -> True   (BIT-IDENTICAL, both 4.029)
corrected_point_verdict(..., retention_noise_floor=floor)  -> 'PASS'
```

The guard's docstring at `:361-363` claims the value is "refused BY IDENTITY … so a caller that lies
about `regime` is still caught by the number itself." It is not. A caller who lies about `regime`
*and* perturbs the last bit gets the Phase 12 full-fine-tune cap, indistinguishable from the borrowed
one at every digit `retention_cap` produces, and a PASS verdict. The harm T-20-19 names is "the
looser cap a borrowing buys" — the guard blocks one bit pattern, not the cap.

This is the codebase's known float hazard in its dangerous direction: `!=` is *too fine*, so evasion
is a rounding error away, while the sibling comparison `3.9085032379884782 == 3.9085032379884783`
shows `==` is *too coarse* to be a value check either.

**Fix:** Refuse the *property*, not the bit pattern. One line, and it closes GC-02 too:

```python
_prove(
    retention_noise_floor <= _ADAPTER_REGIME_RETENTION_FLOOR * (1.0 + 1e-9),
    f"the retention noise floor {retention_noise_floor} is LOOSER than the measured "
    f"adapter-regime floor {_ADAPTER_REGIME_RETENTION_FLOOR} …"
)
```

Keep the existing `!=` check as the named-value refusal (its message is the argument), but do not let
it be the only thing standing between a caller and a looser cap.

---

### GC-02: Any arbitrarily looser retention floor reaches a v4.0 PASS through the choke point

**File:** `scripts/phase20_gate_coverage.py:353-406`

**Issue:** `_prove_retention_floor` refuses four things: a floor with no provenance mapping, the wrong
regime string, fewer than two distinct declared seeds, and one specific literal value. It never
constrains the floor's *magnitude*. Provenance here is a caller assertion, so a caller who declares
`{"regime": "adapter", "seeds": (1337, 2024)}` may pass any positive number at all. Measured:

```
corrected_point_verdict(..., retention_noise_floor=5.0)  -> 'PASS'
retention_cap(retention_noise_floor=5.0) == 13.89114     # governing cap is 3.9091
```

A cap of 13.89 against a governing 3.91 tolerates a ~3.5x retention blow-out. That is a far easier
pass than the borrowed 0.06893 the module spends two paragraphs refusing. The module's own framing at
`:401-405` — "the looser cap is the one a borrowing buys" — identifies looseness as the harm, then
guards a name.

The brief asks whether there is a path around the choke point. There is no path around it; the choke
point itself is the path. Nothing else in the route re-reads the floor.

**Fix:** As GC-01. The bound `retention_noise_floor <= _ADAPTER_REGIME_RETENTION_FLOOR * (1 + 1e-9)`
admits any *tighter* floor a later phase measures (strictly conservative) and refuses the entire
looser class, of which `V20_RETENTION_NOISE_FLOOR` is one member rather than the definition.

---

### GC-03: The two Y sweep legs accept any values at all, and a NaN silently manufactures coverage

**File:** `scripts/phase20_gate_coverage.py:241-247` (validation), `:285-297` (consumption)

**Issue:** `sweep_taught_recalls` and `sweep_heldout_recalls` are validated for **length only**. Their
values are consumed raw at `:296-297`. The extraction axis by contrast gets three `_prove` calls
(positive `n`, integral in-range `k`, positive ceiling), justified at `:274-276` on the grounds that a
"coverage finding attributed to the data when it was produced by the criterion" is unacceptable. The
Y legs are held to no such standard. Measured:

```
corrected_point_verdict(
    ..., sweep_taught_recalls=(-99.0, 42.0),
         sweep_heldout_recalls=(float("nan"), 42.0))   -> 'PASS'
```

Two independent failure modes, both producing **false coverage**, which is direction (ii) — the
defect this file exists to correct — reintroduced on the axes this file adds:

1. **NaN reads as a failing point.** `nan >= criterion` is `False`, so a NaN falls into
   `failing = len(values) - clearing`. A sweep of `(nan, 0.9)` therefore counts one clearing and one
   failing, the axis reads **bracketed**, and the correction publishes a decisive verdict off a leg
   that never crossed. A NaN recall is not exotic — it is what `0/0` produces upstream.
2. **Out-of-range values read as real points.** `42.0` and `-99.0` straddle any floor in `(0, 1]`, so
   any garbage pair certifies coverage.

WR-09's closure — "both legs of Y are decided in one body against one rule" (`:223-226`) — is only as
strong as the values fed to that body, and nothing checks them.

**Fix:** Give the Y legs the extraction leg's discipline, once, covering both legs:

```python
for leg, values in (("taught", sweep_taught_recalls), ("held-out", sweep_heldout_recalls)):
    _prove(
        all(isinstance(v, (int, float)) and 0.0 <= v <= 1.0 for v in values),
        f"the {leg} recall sweep carries {tuple(values)!r}; every point must be a recall in "
        "[0.0, 1.0]. A NaN compares False against the floor and is counted as a FAILING point, so "
        "one NaN beside one clearing point makes a truncated axis read as bracketed — direction "
        "(ii)'s false-coverage defect, on the axis WR-09 exists to cover",
    )
```

(`0.0 <= v <= 1.0` is `False` for NaN, so the range check subsumes the NaN check.)

## Warnings

### GC-04: Integral raw rates pass the RATE-vs-COUNT guard, including this module's own sentinel

**File:** `scripts/phase20_gate_coverage.py:256-270`

**Issue:** The guard accepts `isinstance(k, float) and k.is_integer()`. Raw rates that happen to be
integral are therefore admitted as counts. `SUPERSEDED_SWEEP_SENTINEL = (0.0, 1.0)` — a rate-space
constant defined 190 lines below in this same file — is exactly such a pair. Measured:

```
corrected_point_verdict(..., sweep_extraction_successes=(0.0, 1.0),
                             sweep_extraction_questions=(104, 104))  -> 'INCONCLUSIVE'
```

read as 0 and 1 successes out of 104, both clearing X, axis truncated, spurious GATE-06 demotion —
which is precisely the outcome the guard's own message says it exists to prevent: "conservative in
direction, silent in operation." `corrected_point_verdict`'s docstring at `:461-465` states raw-rate
space is unreachable because "a raw rate smuggled into `sweep_extraction_successes` is refused …
by name." True for fractional rates, false for `0.0` and `1.0`.

Secondary: `isinstance(True, int)` is `True`, so `(True, False)` also passes as counts.

Never produces a false PASS — the route only ever demotes — so this is a WARNING, not a BLOCKER.

**Fix:** The message already says the unit is a count. Enforce it by type and drop the float
acceptance:

```python
whole = isinstance(k, int) and not isinstance(k, bool)
```

This refuses `(0.0, 1.0)` structurally and needs no new message.

---

### GC-05: The verdict is overridden to INCONCLUSIVE while the pin's decisive clearing reasons are returned verbatim

**File:** `scripts/phase20_gate_coverage.py:588-602`

**Issue:** On `not covered` the route returns `"INCONCLUSIVE"` with `[*reasons, corrected_gate06]`.
The pin's reasons were produced under the neutralising sentinel, so they are a full, decisive
reading — and they are returned unaltered under a verdict that contradicts them. Measured, on the
third case the file itself documents (`FIXTURE_CLEARING_POINT` at the `(3, 11)` sweep):

```
verdict: INCONCLUSIVE
  0 (a) extraction upper bound 0.0420 over 104 questions <= X = 0.0454 …
  1 (b) taught recall 0.4000 >= … held-out recall 0.2600 >= …
  2 (c) dialogue on-off gap 1.000000 inside the band …
  3 (c) retention PPL 3.9000 <= cap …
  4 INCONCLUSIVE (GATE-06, CORRECTED — supersedes …)
```

Four reason lines asserting a cleared point inside an INCONCLUSIVE verdict. The frozen pin never
produces this shape: its GATE-06 branch returns at `mitigation_gate.py:820` *before* the conditions
are evaluated, so a pin INCONCLUSIVE never carries clearing reasons. Reason-string consumption is an
established pattern in this codebase (`REPLICATION_PENDING_MARKER` is shipped as a reason marker, and
`_names_gate06` in the test file scans reasons for a substring), so a downstream reader that scans
reasons rather than the verdict reads a cleared point here.

The docstring at `:479-495` names **two** divergences from the pin's contract. This is a third, and
it is the one that changes the meaning of the returned payload rather than its strictness. No test
covers it: `test_direction_ii…:286-302` discards `_c_reasons` on exactly this case.

**Fix:** Do not silently pass through a contradictory record. Either prefix the superseded lines, or
state the divergence in the reason the route appends:

```python
f"… Truncated axes: {truncated_axes}. The reason line(s) above this one are the pin's own "
"reading under the neutralising sentinel and are SUPERSEDED by this verdict: they describe the "
"point, not the sweep. A curve that never crossed cannot refute existence …"
```

and assert it in `test_direction_ii…` on the third case's currently-discarded reasons.

---

### GC-06: The AST caller census — the sole enforcement of the choke point — is blind to aliased imports

**File:** `tests/test_phase20_correction.py:925-936`

**Issue:** Both modules' docstrings state that nothing in Python stops a Phase 23/25 bypass and that
"what stops it is an AST CALLER CENSUS". The census matches on
`getattr(node.func, "id", None) or getattr(node.func, "attr", None)` against the literal string
`"mitigation_point_verdict"`. Two bypasses are invisible to it:

```python
from mitigation_gate import mitigation_point_verdict as mpv
mpv(...)                                            # ast.Name(id='mpv')  -> missed
getattr(mitigation_gate, "mitigation_point_verdict")(...)   # ast.Call func -> missed
```

The docstring at `:909-912` correctly identifies and closes `tests/test_phase19_erasure.py:1389`'s
`.id`-only hole, then leaves the alias hole open one line later. An alias is not an obscure
construct — it is the ordinary way a driver shortens a 24-character name.

Scope is also narrower than the claim: the walk covers `scripts/` and `src/` only (`:925`), so a
driver at the repo root, in `tools/`, or in a notebook is unpoliced. That is stated in the docstring
but not in `phase20_gate_coverage.py:497-506`, which presents the census as the thing that stops a
bypass full stop.

**Fix:** Census the **import**, which no alias can hide, in the same walk:

```python
for node in ast.walk(tree):
    if isinstance(node, ast.ImportFrom) and node.module == "mitigation_gate":
        for alias in node.names:
            if alias.name == "mitigation_point_verdict" and path not in (sanctioned, definition):
                bypassing.append(f"{path.relative_to(_ROOT)}:{node.lineno} (imported as "
                                 f"{alias.asname or alias.name})")
```

---

### GC-07: `_ADAPTER_REGIME_RETENTION_FLOOR` is retyped from a committed JSON artifact, against this module's own stated discipline

**File:** `scripts/phase20_gate_coverage.py:339`

**Issue:** `_ADAPTER_REGIME_RETENTION_FLOOR = 0.008681618994239138` is a hand-copy of
`results/phase20_retention_floor.json::retention_ppl_noise_floor` (verified equal today). The
comment block twelve lines below it states the module's discipline: "computed from imported
constants, never retyped … exactly how a refusal message acquires a wrong number." Two derived
module constants — `_GOVERNING_CAP:347` and `_BORROWED_FLOOR_RATIO:350` — are computed from this
literal and published inside both refusal messages.

The T-20-53 tripwire that exists for this defect class
(`test_wilson_bounds_are_exact_mirrors:464-490`) checks the imported-not-assigned property for
`MARGIN_K` and `EXTRACTION_FLOOR_MIN_SEEDS` — the two constants that were *not* retyped — and does
not look at the one that was. Drift is caught, but only incidentally and at a distance: by the
`repr(number) in borrowed` substring assertion at `:810-816` of the tripwire test, which derives its
numbers from the artifact. That is a substring check standing in for an invariant.

The stated reason for the literal is the module's "no file I/O" posture (`:87`). That posture is a
choice, and it is the reason the one number this module introduces is the one number it cannot
verify.

**Fix:** Assert the invariant directly where the other T-20-53 assertions live:

```python
assert coverage._ADAPTER_REGIME_RETENTION_FLOOR == json.loads(
    RETENTION_FLOOR_PATH.read_text(encoding="utf-8"))["retention_ppl_noise_floor"], (
    "scripts/phase20_gate_coverage.py's retyped adapter floor has drifted from "
    f"{RETENTION_FLOOR_REL}, so every number in its refusal messages is stale")
```

## Info

### GC-08: Three refusal cases assert only that *some* `SystemExit` escaped

**File:** `tests/test_phase20_correction.py:790-792`, `:352-363`

**Issue:** `refused(retention_floor_provenance={})`, `{"seeds": …}` and `{"regime": "full-finetune", …}`
discard the returned message, and the two malformed-count cases at `:356-363` use a bare
`pytest.raises(SystemExit)`. Any `_prove` anywhere earlier in the route satisfies them. The seed
cases and the borrowed case immediately below *do* assert on the message, so the discipline exists
and three cases opt out of it.

**Fix:** Assert a distinguishing substring per case, as the seed case already does — e.g. `"regime"`
for the wrong-regime case, `RETENTION_FLOOR_PROVENANCE_KEYS` names for the missing-key cases.

---

### GC-09: "Proved EXACTLY" is carried by `abs_tol=1e-12`, and two different residues are both called "the residue"

**File:** `tests/test_phase20_correction.py:402-451`, `scripts/phase20_gate_coverage.py:151`

**Issue:** Three small reconciliation gaps in a phase whose stated rule is that a number must
reconcile to its own definition:

- The test docstring says the mirror is "proved EXACTLY"; the assertion that actually pins
  `wilson_lower_bound` to the frozen upper bound is `math.isclose(..., abs_tol=1e-12)` at `:448`.
  It does pin the value (given the upper bound, the midpoint determines the lower uniquely), but to
  1e-12, not exactly. Both the docstring's "no tolerance appears on any bracketing assertion" and the
  headline claim are true only under a reading the reader has to construct.
- The module says the residue survey ran over `2..300` (`:155`); the test asserts over
  `range(2, 401)` (`:431`). Neither cites the other's span.
- `scripts/phase20_gate_coverage.py:151` publishes `+1.734723475976807e-18`; the test comment at
  `:428-429` publishes `1.69e-18`. Both are correct and they are **different quantities** — the
  former is `centre - spread`, the latter is `(centre - spread) / denom`, the value the naive mirror
  would return (verified: `1.734723475976807e-18 / 1.026014… = 1.6907391655729735e-18`). Nothing says
  so, and a reader reconciling the two finds a 2.5% discrepancy in a phase that treats exactly that
  as a defect signature.

**Fix:** Name the quantity at `:151` (`centre - spread` before the `denom` division) and align the
two spans.

---

### GC-10: The `z` default is captured by value, not "BY REFERENCE", and nothing asserts the two defaults agree

**File:** `scripts/phase20_gate_coverage.py:124`, `:129-130`

**Issue:** The docstring states `z` defaults to `erasure_gate._Z_ONE_SIDED_95` "BY REFERENCE, so the
two bounds cannot drift to different confidence levels." Python evaluates default arguments once, at
function-definition time, and binds the resulting float — there is no reference. The invariant holds
today only because both snapshots are taken from the same module-level object; it is asserted by no
test. `test_wilson_bounds_are_exact_mirrors` proves same-*value* symmetry at `n = 104`, not
same-default.

**Fix:** One line in the mirror test:

```python
assert (inspect.signature(coverage.wilson_lower_bound).parameters["z"].default
        == inspect.signature(erasure_gate.wilson_upper_bound).parameters["z"].default)
```

---

### GC-11: Unhashable `seeds` raises `TypeError` from inside the choke point instead of a refusal

**File:** `scripts/phase20_gate_coverage.py:386-387`

**Issue:** `len(set(seeds))` on a list of unhashables (`{"regime": "adapter", "seeds": [[1], [2]]}`)
raises `TypeError` before the `_prove` can produce its refusal. The `isinstance` ternary already
routes non-sequences to `distinct = 0` so they refuse cleanly; only unhashable elements leak a
traceback out of a function whose "whole output is the refusal" (`:355`).

**Fix:** `distinct = len({repr(s) for s in seeds}) if isinstance(seeds, (list, tuple, set, frozenset)) else 0`,
or wrap the `set()` in a `try`.

---

### GC-12: The question-count refusal argues about a failure mode its predicate cannot detect

**File:** `scripts/phase20_gate_coverage.py:248-255`

**Issue:** The `_prove` checks `all(n > 0 …)`. Its message spends four lines on draw-denominated
counts — "both deflates the rate and narrows the bound, in the same direction, so the error is
invisible in the output." It remains invisible: a draw-denominated `n` is positive and passes.
A caller who trips this guard is told about a defect they do not have; a caller who has that defect
is not told at all. `n` is also never checked for integrality, so `n = 104.5` computes a Wilson bound
without complaint.

**Fix:** Either scope the message to what the predicate proves, or strengthen the predicate —
`all(isinstance(n, int) and n > 0 …)` at least refuses a non-integral denominator, which no count of
questions can be.

---

_Reviewed: 2026-08-21T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
