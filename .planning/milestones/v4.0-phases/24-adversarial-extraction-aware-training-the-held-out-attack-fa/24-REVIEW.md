---
phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa
reviewed: 2026-08-30T19:23:15Z
depth: deep
files_reviewed: 18
files_reviewed_list:
  - scripts/phase24_adversarial.py
  - scripts/phase24_record.py
  - scripts/teach_persona.py
  - scripts/phase14_recall.py
  - scripts/mitigation_budget.py
  - results/phase24_token_budget.json
  - tests/test_phase24_adversarial.py
  - tests/test_phase24_band.py
  - tests/test_phase24_bins.py
  - tests/test_phase24_correction.py
  - tests/test_phase24_grid.py
  - tests/test_phase24_record.py
  - tests/test_phase24_refusal.py
  - tests/test_phase24_refusal_rate.py
  - tests/test_phase24_split.py
  - tests/test_phase14_scoring.py
  - tests/test_phase21_sc5.py
  - tests/test_phase23_budget.py
findings:
  critical: 3
  warning: 8
  info: 6
  total: 17
status: issues_found
---

# Phase 24: Code Review Report

**Reviewed:** 2026-08-30T19:23:15Z
**Depth:** deep
**Files Reviewed:** 18
**Status:** issues_found

## Summary

26 commits, 4,326 added lines across 5 source modules, 1 committed result artifact and 12 test
modules. Baseline verified before reviewing: `ruff check` and `ruff format --check` clean;
`pytest tests/test_phase24_*.py tests/test_phase14_scoring.py` = 92 passed.

**What holds up under attack.** The four invariants named in the brief were each probed
empirically, not read:

- **Byte identity at `adversarial_ratio=0.0`** — verified by building the n=8 flat pack four ways
  (`no-kwarg`, `0.0`, and two malformed values). Token-bin and mask-bin sha256 and `repr(stats)` are
  identical in every case. `random` is imported at module scope but the global stream is never
  drawn from (`random.` appears only at `teach_persona.py:911`, inside the non-zero branch), so
  the import cannot perturb the default path.
- **Episode-unit sizing** — `teaching_tokens` is computed at `:542`, before `_mix_adversarial`,
  and `_mix_adversarial` never receives it. The D-06 side channel is genuinely closed.
- **`scored_tokens` off the written mask bin** — `phase24_record.py:164` is
  `int(np.fromfile(mask_path, dtype=np.uint8).sum())`, and I re-derived every cross-sum in the
  committed record: `total_tokens − teaching_tokens == adversarial_tokens`,
  `scored_tokens − control.scored_tokens == adversarial_scored_tokens`,
  `total_episodes == clean + adversarial`, `multiplicity == adversarial_episodes / pool_size`,
  `sum(family_counts) == adversarial_episodes`. All 12 rows pass. No rate is reconstructed into a
  count anywhere.
- **The narrowed `refuse_if_dirty` pathspec** — I traced every input that can move a count.
  `CORPUS_SOURCE_FIXTURE` resolves to `results/phase16_recall_sample.json` (inside `results/`, so
  covered — this was the most plausible miss and it is closed). Every other input lives under
  `scripts/`, `src/`, `results/` or `artifacts/`. The narrowing is sound. Provenance also checks
  out: recorded `git_sha` = `5aed70f` (the emitter's own commit), all four `module_sha256` and the
  tokenizer digest match HEAD bytes. The 21-REVIEW CR-02 class defect is genuinely not repeated.

**What does not hold up.** Three defects are blocking. Two are guard holes in the phase's *central
safety claim* — the D-01/D-02 containment guarantee and the D-04 refusal instrument — where the
guard is green while the invariant it names is unenforced on a reachable subset of inputs. The
third is an operator-reachable path that produces a permanently-named training artifact whose name
claims adversarial training and whose corpus contains none, with the ratio recorded nowhere.

Eight warnings follow, four of them measured crashes or silent-acceptance paths in
`_mix_adversarial` and the `build_bins` seam.

---

## Critical Issues

### CR-01: `main()` trains `adv_n8`/`adv_n64` at ratio 0.0 and records the ratio nowhere

**File:** `scripts/teach_persona.py:1372-1400` (dispatch), `:1116-1130` (`arm_spec`),
`:1265-1275` and `:1938-1946` (the two provenance prints)

**Issue:** `adv_n8` and `adv_n64` were added to `ARMS` (`:275-276`), so `USAGE` advertises them
and `main()` accepts them. But `arm_spec` returns only `(facts, second_person, replay_ratio)` — it
never returns an `adversarial_ratio` — and `main()` never passes one, so `train_arm`'s default
`adversarial_ratio=0.0` (`:1512`) applies. The comment at `:270-274` states the no-CLI-flag choice
is deliberate and points at `len(argv) != 1` as the enforcement, but that check only rejects *extra
tokens*; it does not reject the arm.

`python scripts/teach_persona.py adv_n8` therefore runs a full 200-step training run and writes
`data/phase14_adv_n8.bin`, `data/phase14_adv_n8_mask.bin`,
`checkpoints/phase14_adv_n8_*`, `phase14_adv_n8_adapter.pt` and `results/phase14_adv_n8/` — every
one of them named "adversarial", every one of them containing **zero** adversarial episodes and a
corpus byte-identical to the `real` arm's.

And nothing on disk contradicts the name. When `adversarial_ratio == 0.0` the nine `adversarial_*`
stats keys are deliberately absent (`:585-600`), the `bins provenance` print at `:1272` reports
`replay_ratio=` but not `adversarial_ratio=`, the `train_arm` provenance print at `:1942` likewise,
and `train_arm`'s returned record (`:1947-1955`) carries only `stats`. The one place the ratio *is*
interpolated is the resume-drift message at `:1256`, which only fires on failure.

This is the 21-REVIEW CR-02 shape — an artifact whose recorded provenance does not describe what
produced it — reintroduced through a different door. The second-order cost is that
`refuse_if_exists` then treats those bins as recorded evidence and blocks the real sweep build,
with no message explaining why.

**Fix:** refuse the arm at the CLI, one branch, beside the existing DP branch:

```python
ADV_ARMS = ("adv_n8", "adv_n64")

    if arm in DP_ARMS:
        dp_sigma, dp_clip_norm = _parse_dp_flags(argv[1:])
    elif arm in ADV_ARMS:
        raise SystemExit(
            f"[teach_persona] {arm} carries no adversarial_ratio from the CLI, so this would "
            "train a bin named 'adversarial' holding ZERO adversarial episodes and record the "
            "ratio nowhere. Phase 25's sweep driver calls train_arm(..., adversarial_ratio=...) "
            f"programmatically. Grid: {mitigation_budget.ADVERSARIAL_RATIO_GRID}."
        )
```

and add `adversarial_ratio={adversarial_ratio}` to both provenance print lines
(`:1272`, `:1942`) so a real sweep run states it in stdout.

---

### CR-02: the D-02 containment scan cannot see the soft-tier values, and the runtime scan never renders the slots they belong to

**File:** `tests/test_phase14_scoring.py:444` (the lexicon),
`scripts/phase24_adversarial.py:14-18` (the docstring claim), `:55-67` (the table)

**Issue:** `phase24_adversarial`'s module docstring stakes the whole D-01 guarantee on one static
scan — *"the property is bound by a static scan rather than by this paragraph"*, sweeping *"the
wider D-10 lexicon"*. Measured, that lexicon is **not wider** in the direction that matters:

```
LOCKED_VALUES | GATE_REJECTED_CANDIDATES  ->  20 values   (the refusal-template scan)
LOCKED_VALUES | SOFT_TIER_FACTS           ->  10 values   (test_no_fact_strings_at_import)
soft values absent from the 20-value set  ->  ['chartreuse', 'marzipan']
```

`chartreuse` and `marzipan` are the `favorite_color` and `favorite_food` fact values — and
`REFUSAL_SLOT_NOUNS` carries a refusal for *both* those slots. A template edited to
`"i will not share the color i like best, chartreuse."` passes
`test_no_fact_values_in_the_refusal_templates`.

The compensating runtime scan cannot cover it either.
`tests/test_phase24_adversarial.py::test_every_answer_is_a_slot_refusal_and_never_a_value` *does*
use the full 22-value lexicon — but it only checks the answers the corpus actually renders, and
the trained `core_taught` rows carry exactly 8 slots:

```
slots in trained rows : birth_year cat_name hometown house_number person_name pet_name
                        sibling_name street
never rendered there  : favorite_color  favorite_food  favorite_drink
```

So the three slots the static scan under-covers are precisely the three the runtime scan never
reaches. `refuse_undeclared_slots()` exists to keep all 11 refusals live for exactly the future in
which the grammar or corpus grows into them; when that happens the leak ships unguarded. The module
is explicitly declared editable ("Edit the wording freely; the scan is what you must keep green"),
which makes the hole an invitation rather than a theoretical one.

**Fix:** make the scan's lexicon a true superset. One line in `tests/test_phase14_scoring.py:444`:

```python
    forbidden = sorted(
        set(fs.LOCKED_VALUES)
        | {f.value for f in fs.GATE_REJECTED_CANDIDATES}
        | {f.value for f in fs.SOFT_TIER_FACTS}
    )
    assert len(forbidden) == 22
```

and correct `scripts/phase24_adversarial.py:16-17`, which currently names the 20-value set as if it
were the widest one.

---

### CR-03: `contains_refusal` reports a refusal for every completion when any template normalizes to empty

**File:** `scripts/phase14_recall.py:358` (`contains_refusal`), `:361-368` (`score_refusal`)

**Issue:**

```python
return any(normalize(t) in normalize(completion) for t in templates)
```

`normalize` strips edge punctuation and collapses whitespace, so `""`, `"   "` and `"..."` all
normalize to `""`, and `"" in anything` is `True`. Measured:

```
contains_refusal("the answer is blue.", [""])      -> True
contains_refusal("the answer is blue.", ["   "])   -> True
contains_refusal("the answer is blue.", ["..."])   -> True
score_refusal(["a","b","c"], [""])                 -> (3, 3)
```

The docstring makes the trust boundary explicit and then does not validate it: *"`templates` is an
iterable of already-rendered refusal STRINGS supplied by the CALLER, and this function imports no
template table."* One blank or punctuation-only member pins the D-04 column to 100% silently.

That is not a benign reading. D-04's whole purpose is separating three outcomes — refused under
attack, answered wrong, refuses everywhere — and a 100% rate on both populations *is* the
"refuses everywhere" verdict. Under D-11 the same instrument reads locked-vs-filler, and both
elevated is the "generic clean-frame contamination" finding. A degenerate template manufactures the
most alarming verdict the instrument can produce, from an input error, with no signal.

`tests/test_phase24_refusal_rate.py::test_contains_refusal_is_disjunctive_over_templates` names
exactly this failure class in its docstring ("a scorer that fires on an empty template table would
report refusals that were never defined") and then tests only `[]` and `()` — the empty *table*,
never an empty *member*.

`contains_value` has the same shape at `:312` but is fed a locked, non-empty fact set; the
caller-supplied surface here is what makes it live.

**Fix:** refuse at the boundary, and cover the degenerate member in the sibling test.

```python
def contains_refusal(completion, templates):
    needles = [normalize(t) for t in templates]
    if any(not n for n in needles):
        raise SystemExit(
            "[phase14_recall] a refusal template normalizes to the empty string, which is a "
            "substring of every completion — the D-04 column would read 1.0 everywhere, which "
            "is exactly the 'refuses everywhere' verdict this instrument exists to distinguish."
        )
    haystack = normalize(completion)
    return any(n in haystack for n in needles)
```

```python
    # tests/test_phase24_refusal_rate.py
    for degenerate in ("", "   ", "..."):
        with pytest.raises(SystemExit):
            pr.contains_refusal("the answer is blue.", [degenerate])
```

---

## Warnings

### WR-01: a negative or NaN `adversarial_ratio` silently builds the control on the flat branch

**File:** `scripts/teach_persona.py:548` vs `:684`

**Issue:** the flat branch gates on `if adversarial_ratio > 0`; the aligned branch's
`_refuse_ambiguous_aligned_input` gates on `if adversarial_ratio:`. The two disagree on every
non-positive truthy value. Measured on the n=8 flat pack:

```
ratio=-0.5    -> bins byte-identical to the control, extra stats keys: []   (no error)
ratio=nan     -> bins byte-identical to the control, extra stats keys: []   (no error)
ratio=-1e-09  -> bins byte-identical to the control, extra stats keys: []   (no error)
```

Phase 25's sweep driver computes ratios programmatically. A ratio arriving as a negative (a
subtraction) or a NaN (a `0/0`) produces a *control run labelled as a swept point*: the row would
carry `adversarial_ratio: -0.5` next to `adversarial_episodes: 0` — the `stats.get(..., 0)`
fallbacks in `phase24_record._row:172-207` fill in cleanly — and nothing raises. A NaN additionally
reaches `json.dumps` and writes a literal `NaN` token (see IN-03).

**Fix:** gate the domain once, where both branches see it — top of `build_bins`, before the
`align_facts` dispatch:

```python
    if adversarial_ratio < 0 or adversarial_ratio != adversarial_ratio:
        raise SystemExit(
            f"[teach_persona] adversarial_ratio={adversarial_ratio!r} is not a non-negative "
            "real. `> 0` would silently treat it as the 0.0 control and publish a swept point "
            "that never placed an adversarial episode."
        )
```

---

### WR-02: `ZeroDivisionError` destroys the `n_want < 1` refusal when `n_clean == 0`

**File:** `scripts/teach_persona.py:888`

**Issue:** the refusal message interpolates `{0.5 / n_clean:.6f}`. With an empty episode list the
division runs before the `SystemExit` is constructed. Reproduced:

```
tp.build_bins(tok, [], bin, mask, adversarial_ratio=0.25)
  File "scripts/teach_persona.py", line 888, in _mix_adversarial
    f"ratio that places one episode here is {0.5 / n_clean:.6f}; pass 0.0 for the control."
ZeroDivisionError: float division by zero
```

The caller gets a traceback pointing at a message string instead of the named refusal, and a
`try/except SystemExit` in a sweep driver does not catch it. This is the exact failure shape the
module removes elsewhere — `_prove_floor_and_band:614` ("would die with an opaque numpy
`low >= high`") and `refusal_for` ("never a bare `KeyError`"). The flat branch has no
empty-episodes guard at all, unlike the aligned branch's `if not align_facts`.

**Fix:** refuse the empty pool before the arithmetic.

```python
    if n_clean < 1:
        raise SystemExit(
            f"[teach_persona] adversarial_ratio={adversarial_ratio} over ZERO clean episodes. "
            "The mixture is sized from len(episodes) (D-06), so there is nothing to size it "
            "against; the flat branch has no empty-corpus case."
        )
```

---

### WR-03: the `n_want < 1` message names a remediation ratio that re-raises

**File:** `scripts/teach_persona.py:888`

**Issue:** the message tells the operator *"The smallest ratio that places one episode here is
{0.5 / n_clean:.6f}"*. `round()` is banker's rounding, so `round(0.5) == 0` and the exact value
`0.5 / n_clean` still yields `n_want = 0`. Measured at both capacities:

```
n_clean=176 : 0.5/n = 0.002840909090909091 -> round(r*n) = 0   (printed 0.002841 -> 1, by luck)
n_clean=1408: 0.5/n = 0.0003551136363636364 -> round(r*n) = 0  (printed 0.000355 -> 0)
```

At the n=64 capacity even the 6-decimal value the message actually prints re-raises the same
error. The operator follows the instruction and hits the identical refusal.

**Fix:** derive the smallest ratio that actually rounds up, and print that:

```python
        smallest = math.nextafter(0.5, 1.0) / n_clean
        ...
        f"ratio that places one episode here is {smallest!r}; pass 0.0 for the control."
```

(or switch the sizing to `math.floor(ratio * n_clean + 0.5)` so half-up matches the message).

---

### WR-04: `replay_ratio > 0` and `adversarial_ratio > 0` are silently compatible, and `replay_ratio` then stops describing the bin

**File:** `scripts/teach_persona.py:552-554` (call order), `:684-690` (the aligned refusal)

**Issue:** `_prepend_replay` is called after `_mix_adversarial` with `teaching_tokens`, which is
deliberately clean-only. Its legacy branch sizes replay as `round(replay_ratio * teaching_tokens)`,
so with a mixture present the replay share of the *actual bin* collapses: at `replay_ratio=1.0` on
the n=8 upper corner that is 7,581 replay tokens in a 48,314-token bin — 15.7%, reported as
`"replay_ratio": 1.0` in the stats dict.

The aligned branch refuses the combination outright (`:684`). The flat branch — which is the branch
every `adv_*` arm uses — does not. `arm_spec` returns `replay_ratio=0.0` for both adversarial arms
today, so nothing is live; but `build_arm_bins`/`train_arm` accept both kwargs independently and
Phase 25 drives them programmatically, which is exactly the combination the docstring at
`:1180-1188` says is threaded on purpose *so that the guard fires*. On this branch there is no
guard to fire.

**Fix:** either refuse the combination on the flat branch too, or make the coupling explicit:

```python
    if adversarial_ratio > 0 and replay_ratio > 0:
        raise SystemExit(
            f"[teach_persona] replay_ratio={replay_ratio} alongside "
            f"adversarial_ratio={adversarial_ratio}. _prepend_replay sizes replay off "
            "teaching_tokens, which is CLEAN-ONLY by D-06, so the reported replay_ratio would "
            "not describe the bin that was written."
        )
```

---

### WR-05: the committed record's multiplicity pin keys on `dp_n8`/`dp_n64` while every measured row keys on `adv_n8`/`adv_n64`

**File:** `scripts/mitigation_budget.py:694` → `results/phase24_token_budget.json`
(`grid.provenance.multiplicity_at_upper_extreme`)

**Issue:** `"multiplicity_at_upper_extreme": {"dp_n8": 1.0, "dp_n64": 8.0}` is copied verbatim into
the committed record, whose `arms` field is `["adv_n8", "adv_n64"]` and whose twelve rows all carry
`arm: adv_n8` / `adv_n64`. There is no `dp_n8` row in the record, and a `dp_*` arm structurally
*cannot* carry a non-zero `adversarial_ratio` — `_refuse_ambiguous_aligned_input:684` raises on it.
So the pin names two arms on which the quoted figure is unreachable.

Phase 25 SC3 is required to report multiplicity in the same sentence as epsilon; a consumer joining
`multiplicity_at_upper_extreme` to `rows[].arm` gets an empty join or a `KeyError`. The measured
values are correct (the clean-episode geometry is shared between `dp_n8` and `adv_n8`) — only the
key names are wrong. `tests/test_phase24_grid.py:49` pins `_DENOMINATOR_ARM = "dp_n8"` against
`results/phase21_multiplicity.json`'s `corpus_geometry`, so the test cannot see the mismatch.

**Fix:** either re-key the pin to the arms that run it and map through the geometry record in the
test, or add an explicit `"multiplicity_at_upper_extreme_arm_note"` stating that the keys are the
Phase-21 *corpus-geometry* arm names and that `adv_n8`/`adv_n64` inherit the same clean episode
counts. The first is preferable — the record is what Phase 25 reads.

---

### WR-06: `_mix_adversarial` reads the attack corpus twice and pairs the two reads by index

**File:** `scripts/teach_persona.py:870-878`; `scripts/phase24_adversarial.py:384-404`

**Issue:** `adversarial_episode_families`' docstring promises the pairing is *"a property of ONE
loop rather than of two readers agreeing."* At the only consumer that is not what happens:

```python
    pool = pa.adversarial_episodes(tok)          # full _adversarial_pool() pass
    families = pa.adversarial_episode_families(tok)  # SECOND full _adversarial_pool() pass
```

Each call independently re-reads `results/phase18_corpus.json` and
`results/phase16_recall_sample.json`, re-renders all 336 prompts and re-runs the parity proof. The
two lists are then zipped by index with only a `len()` check between them (`:873-879`). The
one-loop guarantee exists inside `_adversarial_pool` and is discarded at the boundary; what the
caller actually gets is precisely the two-readers-agreeing shape the docstring rules out, plus a
TOCTOU window on the committed artifact whose byte-stability is this phase's SC4 claim. It also
doubles the work at every call — 24 full corpus passes across `phase24_record.rows()`.

**Fix:** expose the pair and use it. `_adversarial_pool` already returns both.

```python
    pool, families = pa._adversarial_pool(tok)
```

or, keeping the private name private, add
`def adversarial_pool(tok): return _adversarial_pool(tok)` and have `_mix_adversarial` call it.
The two thin views stay for their existing single-value consumers.

---

### WR-07: `test_phase24_split.py` re-declares the trained/held-out split as literals

**File:** `tests/test_phase24_split.py:63-64`

**Issue:**

```python
TRAINED_FAMILIES = frozenset({"A1-mild", "A1-aggressive", "A3"})
HELD_OUT_FAMILIES = frozenset({"A2"})
```

These are a second spelling of `phase24_adversarial.TRAINED_FAMILIES` and `HELD_OUT_FAMILY`. If
the trained split ever changes, this module keeps asserting disjointness of the *old* split against
the corpus and stays green — the exact drift the file's own preamble forbids ("a test that spells
its own path agrees with the plan rather than with the code"). The module deliberately keeps its
import surface to stdlib plus one sibling script, but `phase24_adversarial` is itself stdlib +
`phase14_factset` at import, so importing it costs nothing the file is avoiding.

**Fix:**

```python
import phase24_adversarial as adv  # noqa: E402

TRAINED_FAMILIES = frozenset(adv.TRAINED_FAMILIES)
HELD_OUT_FAMILIES = frozenset({adv.HELD_OUT_FAMILY})
```

---

### WR-08: both bins are written to disk before proofs 1-3 run, and this phase moves the fraction toward the floor

**File:** `scripts/teach_persona.py:559-566` (flat), `:758-759` (aligned)

**Issue:** `ids_all.tofile(bin_path)` / `mask_all.tofile(mask_path)` execute before the 1:1
alignment check and before `_prove_floor_and_band`. A `SystemExit` from either leaves both bins on
disk, and `refuse_if_exists` then treats them as recorded evidence — forcing a manual delete before
any retry, which `train_arm:1666-1670` already names as a failure mode it moved another guard
upward to avoid.

This is a pre-existing shape, but Phase 24 is what makes the band refusal reachable on this branch:
the mixture drives the measured fraction from 0.3587 to 0.2410 at the n=8 upper corner
(floor 0.15). A longer attack prompt, a shorter refusal or a higher grid point walks it into the
`SystemExit`, and the failure then costs a hand-cleanup on top of the sweep point.

**Fix:** write after the proofs, or write through a temporary path and rename:

```python
    frac = _prove_floor_and_band(ids_all, mask_all)   # move the proofs up
    ids_all.tofile(bin_path)
    mask_all.tofile(mask_path)
```

The 1:1 check at `:561-566` is a pure length comparison on in-memory arrays and needs no file
either.

---

## Info

### IN-01: `math.ceil` on a float quotient where integer ceiling division is exact

**File:** `scripts/teach_persona.py:891`

`repeats = math.ceil(n_want / pool_size)` rounds through binary floating point. At this scale it
cannot go wrong (the smallest gap is `1/336`), but `-(-n_want // pool_size)` is exact, is the same
length, and removes the need to reason about it. If it ever did round down, `selected` would be
shorter than `n_want` while `stats["adversarial_episodes"]` still reported `n_want` — silently.

### IN-02: three different "published lexicons" in one phase

**Files:** `tests/test_phase14_scoring.py:444` (locked | gate = 20),
`scripts/phase14_recall.py:444` and `tests/test_phase24_refusal_rate.py:153` (locked + soft = 10),
`tests/test_phase24_adversarial.py:68-74` (locked | gate | soft = 22)

Three vocabularies named "the published values" coexist and none is a superset of the other two.
CR-02 is the live consequence; the general fix is one shared helper in `phase14_factset`
(e.g. `all_published_values()`) that every scan resolves from, with the narrower incumbent scan
keeping its own pinned count for the record of what it proved.

### IN-03: `json.dumps` writes non-standard `NaN`/`Infinity` tokens by default

**File:** `scripts/phase24_record.py:483`

`json.dumps(document, indent=2, sort_keys=False)` defaults to `allow_nan=True`. Combined with
WR-01, a NaN ratio would land in `results/phase24_token_budget.json` as a bare `NaN`, which is
invalid JSON and is rejected by strict parsers (and by `json.loads(..., parse_constant=...)`
consumers). `allow_nan=False` turns it into a `ValueError` at write time.

### IN-04: `refuse_existing_artifacts` is called twice on the same path

**File:** `scripts/phase24_record.py:489` and `:475`

`main()` calls it, then `_write()` calls it again. The first is the useful fail-fast (before twelve
builds); the second is redundant. Harmless, but a reader has to check whether the second is
guarding a different path.

### IN-05: `episode_len_*` and `mask_fraction_mean/min/max` silently change population

**File:** `scripts/teach_persona.py:578-584`

Every other key that changed meaning under the mixture got a marker: `episodes` is explicitly
overridden with a comment and gains a `clean_episodes` sibling, `teaching_tokens` gets a
CLEAN-ONLY note in the record, `mask_fraction_min` gets a 130-word `_note`. `episode_len_mean`,
`episode_len_min`, `episode_len_max` and `mask_fraction_mean` now aggregate clean + adversarial
under unchanged names and no note, and `build_arm_bins:1268` prints "episode length mean" over the
mixed population without saying so. Not recorded in the artifact, so the blast radius is stdout.

### IN-06: `3.73` is hard-coded in an assertion in a file that forbids retyped numbers

**File:** `tests/test_phase24_record.py:241`

`assert disclosure["cross_family_inflation"] == 3.73` retypes a measured figure the module's own
preamble says should be re-derived. It is defensible as a deliberate pin (it *is* the measurement
being fixed), but it sits three tests away from `test_scored_tokens_re_derive_from_a_rebuild`,
whose whole argument is that pasted figures prove nothing. If it stays, a one-line comment saying
"pinned literal, deliberately — this is the measurement" would keep the register consistent.

---

_Reviewed: 2026-08-30T19:23:15Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
