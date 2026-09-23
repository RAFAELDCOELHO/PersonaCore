---
phase: 20-pre-registration-the-three-condition-gate
reviewed: 2026-08-20T22:15:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - scripts/mitigation_gate.py
  - scripts/phase20_run.py
  - scripts/_prose.py
  - tests/test_phase20_prereg.py
  - tests/test_phase19_erasure.py
  - results/phase20_retention_floor.json
findings:
  critical: 1
  warning: 10
  info: 11
  total: 22
status: issues_found
---

# Phase 20: Code Review Report

**Reviewed:** 2026-08-20T22:15:00Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Baseline confirmed before reviewing: `.venv/bin/python -m pytest -q` → `863 passed, 1 skipped`
(190.64s); `.venv/bin/ruff check .` → clean; `ruff format --check` → 174 files formatted. Nothing
here is a lint or a test regression.

The pin's *ordering* machinery is the strongest part of the phase and I could not break it. The
`adds[-1]` earliest-add semantics, the `bool(checked) == bool(tracked_artifacts)` equivalence, the
five-state throwaway-repo fixture and the shared `_assert_ordering_holds` are all sound, and the
fixture genuinely re-executes the code the live guard calls rather than a lookalike. The
`sys.path.insert(0, scripts/)` bootstrap shadows no stdlib name. No `shell=True`, no `eval`, no
hardcoded credential, no unsafe deserialisation (both checkpoint reads go through the
`weights_only=True` choke point), no path built from untrusted input.

The defects are in the *judgment* logic and in what the phase left unguarded:

- **One Critical**: condition (a) is decided on a Wilson upper bound, but GATE-06's
  "did the sweep bracket X?" check is decided on the raw rate. I reproduced a realistic sweep that
  genuinely brackets the criterion and is nevertheless reported `INCONCLUSIVE` — and therefore
  denied promotion to full fidelity.
- The retention floor — the number this whole phase's fifth deliverable exists to measure — reaches
  `retention_cap` with **no provenance tripwire at all**, while the extraction floor gets a
  three-`_prove` choke point. The borrowed-floor defect D-06 was written to correct is structurally
  guarded on one leg and unguarded on the other, and the pin never explains the asymmetry.
- **No committed test reads `results/phase20_retention_floor.json`.** Its `governs` field is prose
  with nothing armed behind it, in a phase whose stated doctrine is that a correction travels as
  code plus a tripwire because "a prose note gets missed."
- The driver's single most dangerous line — the `forbid`-discard / `tok`-fifth call shape — has
  **no committed regression guard**, despite `20-07-SUMMARY.md:37` publishing it as a pattern
  "asserted by AST, not by grep." The AST check was a one-time manual observation recorded in the
  verification table. This repository's own words (`tests/test_phase20_prereg.py:294`): *"A guard
  verified once by hand in a scratch directory decays silently."*
- And the comment that stands in for that guard (`phase20_run.py:128-131`) **misstates the failure
  mode it warns about**.

**Remediation classes.** Findings against `scripts/mitigation_gate.py` are marked
**DATED CONTINUATION** — `results/phase20_retention_floor.json` was added at `9bb34ad`, strictly
after the pin's last commit `abf9072`, so the pin is permanently uneditable; the correction path is
`scripts/_addendum.py::append_addendum(path, addendum, *, pending, recorded)` plus an armed tripwire
in an unpinned file. Everything else is a **NORMAL EDIT**.

I deliberately did **not** flag: the two float literals, the `0.4921` / `0.3483` /
`0.005214448168350039` source substrings, `retention_cap`'s defaultless kwarg, the band/cap
asymmetry, or the keyword-only-no-defaults discipline. Each was checked and each is correct as
constrained.

---

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: GATE-06 tests sweep coverage in raw-rate space while condition (a) decides in Wilson-bound space

**File:** `scripts/mitigation_gate.py:798-812` (the coverage check) against `:755-756` (the criterion)
**Remediation:** **DATED CONTINUATION** (pin-frozen)

Condition (a) is decided on the *Wilson upper bound* of the point:

```python
upper = wilson_upper_bound(point_extraction_successes, point_extraction_questions)
a_ok = upper <= ceiling
```

but GATE-06's "did the curve cross?" test compares *raw rates* against the same `ceiling`:

```python
x_at_or_below = any(rate <= ceiling for rate in sweep_extraction_rates)
x_above = any(rate > ceiling for rate in sweep_extraction_rates)
```

`rate <= wilson_upper_bound(rate·n, n)` always, so the coverage test is systematically shifted
*below* the criterion it claims to bracket. The Y axis does **not** have this problem —
`sweep_taught_recalls` is compared against `y_taught`, the same statistic condition (b) reads — which
makes the X leg an isolated inconsistency rather than a deliberate convention.

Reproduced against the committed fixture (`X = 0.04535522866494124` at n=104,
`extraction_noise_floor=0.01`):

```
wilson_upper(1,104) = 0.041950  raw rate = 0.009615   -> clears (a)
wilson_upper(3,104) = 0.069999  raw rate = 0.028846   -> fails  (a)

sweep_extraction_rates = (1/104, 3/104)   # brackets the criterion
verdict -> INCONCLUSIVE
  "the sweep never produced points on both sides of the extraction axis
   (X = 0.0454: at-or-below=True, above=False over 2 swept point(s))"

same fixture, fabricated rates (0.01, 0.30) -> PASS
```

At n=104 a raw rate cannot exceed `X = 0.0454` until 5 successes (`5/104 = 0.0481`), whose upper
bound is `0.0956` — **more than double X**. So the coverage test demands the sweep overshoot the
criterion roughly twofold before it will concede a crossing.

Consequences, both real:

1. A sweep that genuinely brackets the pass/fail boundary is published as "we could not tell" — the
   precise misreading `INCONCLUSIVE` exists to prevent, produced by the branch built to prevent it.
2. `promote_to_full_fidelity` (`:1001-1012`) refuses to promote a truncated-sweep `INCONCLUSIVE`, so
   the full-fidelity budget is withheld from exactly the points that bracket the criterion.

No test exercises this: every fixture uses rates far from the boundary
(`(0.01, 0.30)` and `(0.001, 0.01)`), so both the committed `__main__` self-check and
`test_every_verdict_branch_fires` pass over the defect.

**Fix (dated continuation — do NOT edit the pin):**

```python
# results/phase20_gate_coverage_correction.json
{
  "governs": "scripts/mitigation_gate.py::mitigation_point_verdict's GATE-06 coverage check. "
             "`sweep_extraction_rates` is compared against X in RAW-RATE space while condition "
             "(a) is decided on wilson_upper_bound(...). A caller MUST supply upper bounds, not "
             "raw rates, in `sweep_extraction_rates` so the coverage test and the criterion read "
             "one statistic.",
  "measured": {"n": 104, "X": 0.04535522866494124,
               "brackets_in_bound_space": [0.041950, 0.069999],
               "same_points_in_rate_space": [0.009615, 0.028846],
               "observed_verdict": "INCONCLUSIVE", "correct_verdict": "PASS"}
}
```

plus `append_addendum(...)` on the report, plus an **armed tripwire** in an unpinned test that fires
when a Phase 23/25 caller passes raw rates:

```python
def test_sweep_extraction_axis_is_supplied_in_bound_space():
    """DEF-20-01 tripwire: GATE-06 compares against X in the SAME space condition (a) does."""
    f = {**mitigation_gate.FIXTURE_CLEARING_POINT,
         "sweep_extraction_rates": (mitigation_gate.wilson_upper_bound(1, 104),
                                    mitigation_gate.wilson_upper_bound(3, 104))}
    assert mitigation_gate.mitigation_point_verdict(**f)[0] == "PASS"
```

---

## Warnings

### WR-01: the retention floor reaches the gate with no provenance tripwire — the extraction floor gets three

**File:** `scripts/mitigation_gate.py:595-634` (`retention_cap`) against `:416-443` (`extraction_ceiling`)
**Remediation:** **DATED CONTINUATION** for the in-gate check; **NORMAL EDIT** for the tripwire test

D-14(a) arms a three-`_prove` choke point so a borrowed or single-seed *extraction* floor "aborts
here, loudly, and never passes silently into a published X": the provenance mapping must exist, must
name `NEVER_TAUGHT_ARM`, and must carry ≥2 distinct seeds.

`retention_cap` receives no equivalent. Its only guard is `retention_noise_floor < 0`. Passing
`erasure_gate.V20_RETENTION_NOISE_FLOOR` (0.068930) — the Phase 12 full-fine-tune seed pair whose
governance of an adapter-regime verdict is *the defect D-06 exists to correct*, and which
`retention_cap.__doc__:608-615` names explicitly — computes `4.029000` and returns it silently. The
docstring records the hazard; nothing enforces it.

The gap is invisible in the module because the two floors' rationales are written the same way, and
neither the pin nor `20-CONTEXT.md` explains why one got a tripwire and the other did not. It is also
consequential: `retention_cap` is the **looser** of the two caps under the borrowed value
(`4.029000` vs the measured `3.9085032379884783`), so the unguarded substitution is the one that
buys an easier pass.

**Fix.** The in-gate half is a dated continuation. The half that is available today is a
tripwire in an unpinned test, keyed off the committed artifact:

```python
# tests/test_phase20_retention_floor.py  (new, unpinned)
_FLOOR = json.loads((_ROOT / "results" / "phase20_retention_floor.json").read_text("utf-8"))

def test_v4_retention_cap_reads_the_measured_adapter_regime_floor():
    """D-06/D-07 tripwire: retention_cap has no provenance check, so assert the value here."""
    floor = _FLOOR["retention_ppl_noise_floor"]
    assert floor != erasure_gate.V20_RETENTION_NOISE_FLOOR, "the borrowed Phase 12 floor is back"
    assert mitigation_gate.retention_cap(retention_noise_floor=floor) == _FLOOR["cap"]
```

### WR-02: no committed test reads `results/phase20_retention_floor.json`

**File:** `results/phase20_retention_floor.json` (whole file); absent from `tests/test_phase20_prereg.py`
**Remediation:** **NORMAL EDIT**

`grep -rn phase20_retention_floor tests/` returns only three hits, all of them `tmp_path` paths
inside the throwaway-repo fixture (`tests/test_phase20_prereg.py:420,423,433`). The real artifact is
never parsed by CI.

Everything it asserts is therefore unverified:

- `cap == retention_cap(retention_noise_floor=retention_ppl_noise_floor)` (I checked by hand — it
  currently holds, `3.9085032379884783`);
- `retention_ppl_noise_floor == abs(delta_1337 - delta_2024)` (holds);
- `bit_identical: true`, `abs_delta: 0.0`, `control_is_across_two_distinct_files: true`;
- the `governs` field's whole claim.

`checkpoints/` and `data/` are both gitignored, so CI can never re-derive the number — which makes
the *internal* consistency of the artifact the only check available, and it is not being made. The
phase-19 precedent for a `governs`-carrying artifact
(`results/phase19_calibration_correction.json`, cited by D-24) was paired with a tripwire test; this
one is not.

**Fix:** add the test sketched in WR-01 and extend it to assert the two derived identities above.

### WR-03: the artifact drops the dead-id-mask provenance its direct Phase 19 precedent published for the identical reading

**File:** `scripts/phase20_run.py:192-266` (the artifact dict); `results/phase20_retention_floor.json`
**Remediation:** **NORMAL EDIT** (the driver is unpinned; re-running costs ≤2 min 34 s on MPS, but
`_refuse` will block the write until the existing artifact is removed in a reviewed commit)

`results/phase19_noise_floors.json`'s `retention_ppl_pre_erasure` block — the *same* instrument on
the *same* corpus, produced by `scripts/phase19_run.py::retention()` — carries:

```
dead_id_mask_sha256: 79b55770f4dcfa943d7528cb04829e8d2e7dd8823b9b5450da418b4fcf3cfc28
dead_id_mask_matches_pinned_forbid_ids: true
dead_ids_masked: 7645
live_ids: 547
vocab_size: 8192
policy: "FROZEN (DEBT-02) — the dead-id mask the generation path applies; ..."
```

`results/phase20_retention_floor.json` carries **none** of them. The dead-id mask is the single thing
that makes this metric the frozen-policy retention PPL rather than raw perplexity — two readings
taken under different masks are not comparable — and the bit-identity control's entire claim ("the
instrument is VERIFIED, not assumed") is a claim about instrument identity that the artifact then
declines to record. The control does cover seed 1337 empirically; nothing records which mask governed
seed 2024.

This is the direct cause of IN-01: `phase20_run.py:132` binds `cfg` because the phase-19 line it was
copied from used it at `phase19_run.py:826` (`undecodable_ids_mask(tok, cfg.vocab_size)`). Phase 20
copied the binding and dropped the block that consumed it.

Two further inputs are gitignored and undigested, against the plan's own established pattern
(`20-07-SUMMARY.md`: *"An artifact whose inputs are gitignored must carry its own falsifiability …
the digests of the files that produced them"*):

- `data/retention_val.bin` — only `bin_bytes: 2000572` is recorded, no `sha256`. A different corpus
  of identical length would not be caught.
- the base slim checkpoint — `load_adapted_model` returns `artifact["loaded_base_fingerprint"]`
  (`git_sha`/`step`/`val_loss`) and `artifact["fingerprint_warnings"]`, and `phase20_run.py:132`
  discards both as `_artifact`. D-02 is warn-not-error, so an adapter fingerprinted against a
  *different* base than it was scored on loads anyway — and the artifact would not say so.
  (`phase14_recall.load_adapted_model.__doc__:527-531` states the report is supposed to.) Phase 19
  did not record these either, so this half is an unclosed hole rather than a regression.

**Fix:**

```python
mask = undecodable_ids_mask(tok, cfg.vocab_size)          # cfg stops being dead
readings[seed] |= {
    "dead_id_mask_sha256": hashlib.sha256(mask.cpu().numpy().tobytes()).hexdigest(),
    "dead_ids_masked": int(mask.sum()), "vocab_size": cfg.vocab_size,
    "base_fingerprint": _artifact["loaded_base_fingerprint"],
    "fingerprint_warnings": _artifact["fingerprint_warnings"],
}
artifact["bin_sha256"] = _sha256(pin.RETENTION_BIN)
artifact["policy"] = "FROZEN (DEBT-02) — ..."             # the phase19 string, imported not retyped
```

### WR-04: the driver's most dangerous line has no committed regression guard, and the summary publishes one that does not exist

**File:** `scripts/phase20_run.py:132-138`
**Remediation:** **NORMAL EDIT**

`20-07-SUMMARY.md:37` publishes as a `tech-stack.pattern`:

> "The instrument trap is closed STRUCTURALLY and **asserted by AST, not by grep**: two
> `retention_perplexity` call sites, five positional args, `tok` fifth, zero keywords"

No such assertion is committed. `grep -rln phase20_run tests/` returns exactly one file,
`tests/test_phase19_erasure.py`, where `scripts/phase20_run.py` appears only as a census *exclusion*
and as a substring read. The "AST" check was a one-time manual observation recorded in the plan's
verification table (`20-07-SUMMARY.md:349` region).

The file is **unpinned and freely editable**, so a future edit that reorders the arguments or passes
`forbid` restores the trap with nothing to catch it — and the only remaining protection is a comment
that is itself wrong (WR-05). This repository's own standard, three files away
(`tests/test_phase20_prereg.py:294-298`): *"A guard verified once by hand in a scratch directory
decays silently the moment someone edits … A lookalike copy would prove something about a different
function."*

**Fix** (unpinned test, ~10 lines):

```python
def test_phase20_driver_discards_forbid_and_passes_the_tokenizer_fifth():
    tree = ast.parse((_ROOT / "scripts" / "phase20_run.py").read_text("utf-8"))
    calls = [n for n in ast.walk(tree)
             if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "retention_perplexity"]
    assert len(calls) == 2, calls
    for call in calls:
        assert call.keywords == [], "a keyword would let forbid reach a named slot"
        assert len(call.args) == 5, [ast.unparse(a) for a in call.args]
        assert ast.unparse(call.args[4]) == "tok"
```

### WR-05: the comment guarding the instrument trap misstates the failure mode

**File:** `scripts/phase20_run.py:128-131`
**Remediation:** **NORMAL EDIT**

```python
# The fourth return is `forbid` and it is DISCARDED — `retention_perplexity` takes a
# TOKENIZER and builds its own dead-id mask internally (`perplexity.py:165-170`). Passing
# `forbid` would land in the `batch_size` slot and silently corrupt the reading.
```

Verified against the source:

- `retention_perplexity(model, val_bin_path, block_size, device, tokenizer, batch_size=32)` — a
  sixth positional argument does land in `batch_size`;
- `perplexity(...)`'s own docstring says `batch_size` is *"accepted for signature parity with the
  data path; the sweep scores one window at a time, so it is unused here"*, and I confirmed the
  identifier appears nowhere in the function body after the docstring.

So `forbid` in the `batch_size` slot is **inert** — the reading stays correct. The real hazard is
`forbid` in the **`tokenizer`** slot (a five-positional call with `forbid` fifth), which reaches
`undecodable_ids_mask(forbid, vocab)`.

A safety comment naming the wrong slot and the wrong consequence is worse than no comment: it is the
only thing standing in for the missing test (WR-04), and it points the next maintainer at the
harmless case.

**Fix:**

```python
# The fourth return is `forbid` and it is DISCARDED — `retention_perplexity` takes a TOKENIZER
# fifth and builds its own dead-id mask internally (`perplexity.py:165-170`). Passing `forbid`
# in the TOKENIZER slot reaches `undecodable_ids_mask(forbid, vocab)`; passing it sixth lands in
# `batch_size`, which `perplexity` accepts for signature parity and never reads, so it would be
# silently INERT rather than loud. This is `scripts/phase19_run.py:803`, copied not re-derived.
```

### WR-06: the "exactly two chosen constants" audit has two unacknowledged evasions

**File:** `tests/test_phase20_prereg.py:648-691` (`_module_scope_floats`), `:982-1017`
**Remediation:** **NORMAL EDIT**

`_module_scope_floats` filters on `isinstance(node, ast.Assign)` only. Its docstring goes to real
lengths to enumerate its residual hole — the `FIXTURE_*` exclusion, narrowed by a name allow-list —
and states *"THE RESIDUAL HOLE, STATED IN WORDS RATHER THAN GLOSSED."* Two further holes are not
stated, and both defeat the phase's headline audit. Reproduced by appending each to the pin's source
and re-running the helper:

```
AnnAssign  F_Z: float = 0.9                -> _module_scope_floats = [0.5, 0.7]  MISSED
private kw default _helper(*, k=0.9)       -> _module_scope_floats = [0.5, 0.7]  MISSED
```

1. `ast.AnnAssign` (`F_Z: float = 0.9`) is not an `ast.Assign`, so an annotated module-scope constant
   is invisible. `ast.AugAssign` likewise.
2. `test_every_gate_function_is_keyword_only_with_no_defaults` scopes itself to
   `not node.name.startswith("_")` (`:996`), so a keyword default on a *private* helper is checked by
   neither audit.

`_numeric_constants_outside_fixtures` (used only for the six banned literals) walks whole top-level
nodes and would catch a *banned* value in either position — but a *new third chosen constant* is not
in that list, and the two-constant audit is the one that would have to see it.

**Fix:**

```python
if not isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)) or owner.get(node) is not None:
    continue
targets = node.targets if isinstance(node, ast.Assign) else [node.target]
```

and drop the `not node.name.startswith("_")` filter from the no-defaults scan (the private helpers
`_prove`, `_prove_verdict_domain` take no defaults today, so it goes green unchanged).

### WR-07: the retention census's positive obligation is a substring check — the exact conflation class this phase claims to have closed

**File:** `tests/test_phase19_erasure.py:1423-1429`; detection at `:1386-1392`
**Remediation:** **NORMAL EDIT**

The census scoping is sound in the way the phase claims: `phase20_run.py` is excluded **by name**,
the counts are **unchanged at 6 calls in 4 modules** (I diffed `669d082` — nothing was lowered), and
a new unadapted caller anywhere else still reddens the guard. Two mechanical weaknesses sit under it.

**(a) The positive obligation is `in source`, not AST.**

```python
assert "load_adapter_weights" in source or "load_adapted_model" in source, ...
```

A module satisfies this with the name appearing only in a docstring or a comment. This is live today,
not hypothetical: `scripts/phase19_erasure.py` mentions `load_adapter_weights` in prose at `:194`,
`:280` and `:1805` as well as in a real import at `:2463`, so deleting the real call would leave the
obligation green. `tests/test_phase20_prereg.py:797-802` and `:920-922` both argue at length that
"prose ABOUT a number is not the number; only an AST walk … can tell them apart" — and this is the
sibling assertion the same phase extended to a third module without converting it.

**(b) Call detection is bare-name only.**

```python
if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "retention_perplexity":
```

`ast.Attribute` nodes have no `.id`, so `perplexity.retention_perplexity(...)` or
`evaluation.retention_perplexity(...)` is invisible. I confirmed no attribute-style call exists today
(`grep -rn "\.retention_perplexity(" scripts src tests` → empty), so this is latent, not live — but
it is exactly the "silently miss a future module" vector, and the census's failure message
(*"the retention call-site census moved"*) would never fire for it.

**Fix:**

```python
if isinstance(node, ast.Call) and (
    getattr(node.func, "id", None) == "retention_perplexity"
    or getattr(node.func, "attr", None) == "retention_perplexity"
):
```

and replace the `in source` obligation with an AST check that the successor actually *calls*
`load_adapted_model` / `load_adapter_weights`.

### WR-08: `extraction_ceiling` is the one floor consumer that does not validate its floor's sign, and D-11's invariant states the precondition it does not enforce

**File:** `scripts/mitigation_gate.py:404-414` (validation block) against `:373-377` (the claim)
**Remediation:** **DATED CONTINUATION** (pin-frozen)

Three of the pin's four floor-consuming functions reject a negative floor with the same reasoning
("a noise floor is a magnitude"):

- `superseded_dialogue_cap` — `:239-243`
- `dialogue_gap_band` — `:578-582`
- `retention_cap` — `:629-633`

`extraction_ceiling` validates `nontarget_questions` and `nontarget_successes` and then computes
`upper + MARGIN_K * extraction_noise_floor` with no check on the floor at all. Its own docstring
`:375` asserts the reachability invariant *"`X > wilson_upper_bound(0, n)` **for any non-negative
floor**"* — the precondition is stated in prose and left unenforced, in a module whose thesis is that
obligations travel as code because prose gets missed (`:422-423`).

A negative floor drives X below `wilson_upper_bound(0, n)`, at which point `tolerance_report` (called
one line later inside the gate, `:757`) raises the "no outcome clears it, not even a perfect one"
`ValueError`. So it does fail — but through a message that describes an unreachable *ceiling*, four
functions away from the sign error that caused it, and only because the reporter happens to be on the
path. `extraction_ceiling` called directly returns the bad X silently.

**Fix (dated continuation):** record the missing precondition and arm a tripwire in an unpinned test:

```python
def test_extraction_ceiling_refuses_a_negative_floor():
    """DEF-20-02 tripwire: the pin states the non-negative precondition and does not enforce it."""
    with pytest.raises((ValueError, SystemExit)):
        mitigation_gate.extraction_ceiling(
            nontarget_successes=0, nontarget_questions=104, extraction_noise_floor=-0.01,
            extraction_floor_provenance={"arm": mitigation_gate.NEVER_TAUGHT_ARM,
                                         "seeds": (1337, 2024)})
```

(this test goes RED today — it is the continuation's evidence, exactly the deliberate-RED register
`20-CONTEXT.md` prescribes.)

### WR-09: GATE-06's Y-axis coverage checks only the taught leg, while (b) is a pair

**File:** `scripts/mitigation_gate.py:800-812`
**Remediation:** **DATED CONTINUATION** (pin-frozen)

`GATE-03` makes Y a **pair** (`Y_taught` and `Y_heldout`) precisely because "gating taught-only
rewards memorization over generalization", and `mitigation_point_verdict` honours that at `:765-769`:
`b_ok = taught_ok and heldout_ok`.

GATE-06's coverage test does not. There is no `sweep_heldout_recalls` argument in the 21-kwarg
signature, and the crossing check reads only:

```python
y_at_or_above = any(recall >= y_taught for recall in sweep_taught_recalls)
y_below = any(recall < y_taught for recall in sweep_taught_recalls)
```

So a sweep truncated on the held-out axis — every point above `Y_heldout`, or every point below it —
is undetectable, and condition (b) can be decided `FAIL` off a held-out leg the sweep never bracketed.
GATE-06's own text ("both sides of X (or of Y)") reads on the pair.

The pin records its *other* deliberate asymmetry (D-05, the band-vs-cap legs) with its measured
reason so a later "unify" refactor goes red. This asymmetry is recorded nowhere — the reason string
at `:810` names "the taught-recall axis" but never says the held-out axis is unchecked or why.

**Fix (dated continuation):** record the gap in the continuation artifact, and have the Phase 25
sweep driver assert held-out bracketing before it calls the gate — the check the gate cannot be
given.

### WR-10: `borrowed_floor_ratio` divides by a measured quantity with no zero guard, discarding the whole run

**File:** `scripts/phase20_run.py:199`
**Remediation:** **NORMAL EDIT**

```python
"borrowed_floor_ratio": pin.V20_RETENTION_NOISE_FLOOR / floor,
```

`floor = abs(a["delta_on_minus_off"] - b["delta_on_minus_off"])`. If the two seeds' gaps come out
identical, `floor == 0.0` and this raises `ZeroDivisionError` at artifact-construction time — after
all four MPS readings, **before** the `print` loop at `:268-275` and before `write_text` at `:276`.
Every measured number is lost and the run must be repeated.

`floor == 0` is not an exotic input: it is the exact signal that the instrument distinguished nothing
between the two seeds, which is the one outcome the artifact most needs to report. The driver already
demonstrates the correct register elsewhere — `:139-143` and `:150-154` both raise `SystemExit` with a
diagnostic on a degenerate reading rather than crashing.

**Fix:**

```python
if floor == 0.0:
    raise SystemExit(
        f"[phase20_run] the two seeds produced identical gaps ({a['delta_on_minus_off']!r}); the "
        "adapter-regime floor is 0 and there is no run-to-run variance to report. Readings: "
        f"1337={a!r} 2024={b!r} — record them and STOP, do not publish a zero floor as a margin."
    )
```

---

## Info

### IN-01: `cfg` is bound and never used

**File:** `scripts/phase20_run.py:132` — **NORMAL EDIT**
`model, cfg, tok, _forbid, _artifact = recall.load_adapted_model(...)`. `cfg` is dead. In the
precedent this line was copied from it feeds `undecodable_ids_mask(tok, cfg.vocab_size)`
(`phase19_run.py:826`) — the mask-provenance block Phase 20 dropped (WR-03). Ruff does not flag it
because F841 exempts tuple unpacking. Prefix it `_cfg`, or better, restore the consumer.

### IN-02: `_refuse` is not re-checked at the write boundary, and the write is non-atomic

**File:** `scripts/phase20_run.py:102` and `:276-278` — **NORMAL EDIT**
`_refuse` correctly runs before any tensor loads (the stated intent, and it is the right ordering).
But nothing re-checks at `write_text`, so two concurrent runs both pass the guard and the second
clobbers recorded evidence. The phase-19 precedent is stricter: `_merge_block` re-reads the file at
write time and refuses per block (`phase19_run.py:257-264`). Worse, `write_text` is not atomic — an
interrupted write leaves a truncated JSON file that `_refuse` then permanently blocks from
regeneration, requiring a reviewed commit to delete. Write to `path.with_suffix(".tmp")` then
`os.replace`, and re-call `_refuse(RETENTION_FLOOR_PATH)` immediately before it.

### IN-03: hardcoded seeds beside a data-driven `SEED_ADAPTERS`

**File:** `scripts/phase20_run.py:185` — **NORMAL EDIT**
`a, b = readings[1337], readings[2024]` re-types the two seeds that `SEED_ADAPTERS` (`:49-52`) was
deliberately built *from* a tuple to avoid re-typing. A third seed added to the tuple would be
measured, published in `retention_ppl`, and then ignored by the floor computation with no error.
`a, b = (readings[s] for s in SEED_ADAPTERS)` — with a `len(SEED_ADAPTERS) == 2` `SystemExit` beside
it, since the floor form is a two-draw difference by construction.

### IN-04: `git_sha()` records `HEAD` but not working-tree cleanliness

**File:** `scripts/phase20_run.py:222` (`src/personacore/provenance.py:16-31`) — **NORMAL EDIT**
`git rev-parse HEAD` says nothing about uncommitted changes, so `"git_sha":
"669d082d1a7015f1bdbe31019e04b5a7f7e87c79"` attests the commit the run *claims*, not the source it
*ran*. For this artifact it happens to be sound (I verified `669d082` is the driver's own commit and
an ancestor of `HEAD`). For an artifact whose two other inputs are gitignored, `git status
--porcelain` is the cheapest remaining falsifiability: record `"git_dirty": bool(...)` beside it.

### IN-05: `dialogue_gap_band`'s band-inversion `_prove` is unreachable

**File:** `scripts/mitigation_gate.py:586-591` — **DATED CONTINUATION** (pin-frozen)
`lo = F_C * control_gap`, `hi = control_gap + MARGIN_K * gap_noise_floor`, with `control_gap > 0` and
`gap_noise_floor >= 0` both enforced immediately above and `F_C = 0.5` pinned at exactly two chosen
constants. `lo <= hi` reduces to `0 <= 0.5·control_gap + 2·floor`, always true. The `_prove` can never
fire — a guard nobody can watch fire, in the module that argues at `:1284-1285` that "a branch nobody
has watched fire is a branch nobody has verified" (GATE-09). Harmless, but it should be recorded as a
structural invariant rather than as a runtime check, so a reader does not assume it is load-bearing.

### IN-06: the `__main__` self-check uses bare `assert`, contradicting `_prove`'s own stated rationale

**File:** `scripts/mitigation_gate.py:66-75` against `:1291-1425` — **DATED CONTINUATION** (pin-frozen)
`_prove`'s docstring: *"`SystemExit` and deliberately NOT `assert`: an `assert` is strippable under
`-O`, and a proof that disappears under an optimisation flag is not a proof."* The 30-odd assertions
in the six-outcome self-check are all bare `assert`, so `python -O scripts/mitigation_gate.py` prints
`self-check OK` having proved nothing. Mitigated: `test_gate_self_check_runs_clean_in_a_fresh_
interpreter` (`tests/test_phase20_prereg.py:1035-1041`) invokes `sys.executable` without `-O`, and
`test_every_verdict_branch_fires` re-asserts the same six outcomes under pytest. The cited precedent
(`erasure_gate.py:258-291`) uses the same register. Worth naming so the inconsistency is a recorded
choice rather than an oversight.

### IN-07: `tolerance_report`'s proportion guard is an undocumented crash path on the gate's main line

**File:** `scripts/mitigation_gate.py:487-488`, reached from `:757-759` — **DATED CONTINUATION**
`assert 0 <= ceiling <= 1` raises `ValueError(f"ceiling {ceiling} outside [0.0, 1.0]; a ceiling is a
proportion")`. `extraction_ceiling` has no upper clamp, so any `extraction_noise_floor` above
`(1 - wilson_upper_bound(0, n)) / 2` (≈ 0.487 at n=104) makes `mitigation_point_verdict` raise
instead of returning a verdict. Refusing to publish a vacuous criterion is arguably right, but the
message describes a caller error that did not happen and the behaviour is documented nowhere —
neither `extraction_ceiling.__doc__` nor `mitigation_point_verdict.__doc__` mentions that a large
floor aborts the gate.

### IN-08: assertion (1) of the `provisional` scan is fully subsumed by assertion (2)

**File:** `tests/test_phase20_prereg.py:927-961` — **NORMAL EDIT**
The test presents an AST half ("identifiers and string constants") and a comment half ("the one
textual surface an AST walk cannot see"). But the comment half is
`"provisional" not in _prose.normalized(path.read_text()).lower()` — a scan of the **raw source
bytes**, which necessarily includes every identifier and every string the AST half collects. The AST
walk proves nothing the source read does not. Not wrong, but it is presented as two independent
guarantees where there is one; either drop (1) or scope (2) to comment tokens only.

### IN-09: `MITIGATION_GOAL_FRAMING` is referenced nowhere

**File:** `scripts/mitigation_gate.py:320-329` — **DATED CONTINUATION** (pin-frozen)
`grep -rn MITIGATION_GOAL_FRAMING` across `tests/` and `scripts/` returns only its own definition.
Its sibling `MITIGATION_DECISION_RULE` is at least `len()`-counted in the self-check print (`:1428`)
and named in a test comment (`tests/test_phase20_prereg.py:825`) — but no test asserts either one's
*content*, against `:258-259`'s claim that they are module DATA "so a test can assert them." The
`erasure_gate` precedent has the same property, so this is not a regression; recording it so a Phase
23 report-writer knows the clause text is unguarded and a typo in it would ship.

### IN-10: `normalized` can join a comment to the following code line

**File:** `scripts/_prose.py:46` — **NORMAL EDIT** (phase-neutral helper, exempt from the pin by D-23)
The one-liner is correct for its stated job and the differential test is a genuinely good one — the
negative control at `tests/test_phase20_prereg.py:231` is what makes it non-vacuous. Two edges worth
recording rather than fixing:

```
normalized("a\xa0b")                                            -> "a b"   # NBSP collapsed
normalized("a\u2028b")                                          -> "a b"   # LINE SEPARATOR collapsed
"the three reductions" in normalized("x = 1  # the three\nreductions = 4")  -> True
```

`str.split()` splits on the full Unicode whitespace class, so NBSP and U+2028/U+2029 collapse to a
plain space — desirable for a prose sweep, but it means two genuinely different strings compare
equal. And because the result is one flat line, `normalized(phrase) in normalized(text)` admits a
match that spans a semantic boundary (a trailing comment into the next code line, adjacent list
items). A false *presence* is the opposite of the v3.0 defect this closes, so it is a real if minor
inversion of the guarantee. The docstring's "add one when a second call site actually needs it" is
the right posture — this belongs in the docstring, not in new code.

### IN-11: `checkpoints/` is gitignored, so the artifact's central control is unfalsifiable in principle

**File:** `results/phase20_retention_floor.json:55-70` — **NORMAL EDIT** (documentation)
`control_is_across_two_distinct_files: true` is derived from two sha256 digests
(`226f2ae5…` for `checkpoints/persona_adapter.pt`, `f12ab4c3…` for the seed-1337 arm adapter) of files
no reviewer can obtain. Recording the digests is the right call and the plan says so explicitly —
this is not a defect, it is the accepted cost. What is missing is the sentence stating it: the
`tolerance` field explains the control's *logic* but never says the inputs are unobtainable, so a
reader can mistake "digests recorded" for "digests checkable." One clause in `tolerance` closes it.

---

_Reviewed: 2026-08-20T22:15:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
