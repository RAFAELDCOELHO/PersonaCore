---
phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
reviewed: 2026-08-29T00:00:00Z
depth: standard
diff_base: a601ab2b247fc8d5933115b74fed2458ed968941
files_reviewed: 7
files_reviewed_list:
  - scripts/mitigation_budget.py
  - scripts/phase23_run.py
  - tests/test_phase23_budget.py
  - tests/test_phase23_cost.py
  - tests/test_phase23_ctrl.py
  - tests/test_phase23_matched.py
  - tests/test_phase23_resume.py
findings:
  critical: 3
  warning: 10
  info: 6
  total: 19
status: issues_found
---

# Phase 23: Code Review Report

**Reviewed:** 2026-08-29T00:00:00Z
**Depth:** standard
**Files Reviewed:** 7 (diff `a601ab2..HEAD`, plans 23-11 .. 23-14)
**Status:** issues_found

## Summary

Reviewed the four plans' source: `scripts/mitigation_budget.py` (Z pin, +306 lines),
`scripts/phase23_run.py` (+2,254 lines: the D-04 gate, `noised`, `throughput`, `cost-record`,
`never-taught`), and the five test files. `.venv/bin/python -m pytest
tests/test_phase23_budget.py tests/test_phase23_cost.py` is green (80 passed) — every finding
below is a defect the committed suite does **not** catch.

Checks that came back clean and are worth recording because they were the ones asked for:

- **No new write reaches a frozen pre-registration.** Every `write_text` / `unlink` in
  `scripts/phase23_run.py` targets `data/`, `results/` or an arm's own bins. `scripts/phase23_prereg.py`,
  `scripts/phase23_matched_prereg.py`, `scripts/mitigation_gate.py` and `scripts/mitigation_budget.py`
  are read-only from the driver.
- **The question denominator holds.** `score_never_taught` asserts `questions == len(cell)` per cell,
  `row["n_draws"] == k * row["n_questions"]` per fact, and `total_draws == nontarget_questions * k`
  pooled. `_never_taught_evidence` re-derives the count by a *different* route
  (`any(record["hits"])` vs `aggregate_questions`' `n_answerable`), so that cross-check is real,
  not tautological.
- **The `-realized:` slice in `score_never_taught` (line 4490) is safe.** `x18._guarded_span(entry)`
  runs first (line 4484) and `_prove`s `realized >= 1`, so the `x[-0:]` whole-list trap is
  unreachable. Corpus confirms `realized_injection ∈ {1, 2}` for all 216 A2 entries.
- **The AST/key-walk conversions are correct.** `test_x_is_not_published_in_phase_23`,
  `test_z_was_sized_against_the_ceiling`'s register check, `test_the_refusal_census_is_complete`
  and `_module_level_constant_names` all walk structure, not text. I found no remaining text-match
  criterion whose needle also occurs in prose.
- **`LONG_FIGURE` / half-two of the 23-12 retraction guard is sound**, including the documented
  residuals (sign flip, non-ASCII separator, short inventions).

The three BLOCKERs are all in the same family and it is the family this phase already paid for
once: **work-destroying failure paths in the long-running GPU sub-modes.** Plan 23-14 fixed that
class inside `score_never_taught` and left it standing one function over in `throughput()`, and the
recovery substrate itself (`_state_write`, `_never_taught_write_draws`) is a non-atomic truncate-then-write.

## Critical Issues

### CR-01: `throughput()` destroys its entire GPU run on any post-measurement failure, and the re-run destroys it a second time

**File:** `scripts/phase23_run.py:3558-3791`
**Severity:** BLOCKER (data loss)

`throughput()` runs three conditions × four shapes × 64 timed draws (768 draws, ~1 h wall) and
persists **nothing** until line 3785. Everything between the last draw and that line is a failure
path that discards the whole run:

- line 3648 — `sigma_zero_record["questions_taught"]`: a `KeyError` after all draws.
- line 3671 — `_committed_phase18_rates()`, which `_prove`s `len(rates) == 4` from a **regex over a
  committed markdown file**. A reformatted bullet in `results/phase18_preflight_report.md` raises
  `SystemExit` after every draw is spent.
- line 3702 — `zip(..., strict=True)` and the shape-order `_prove`.
- line 3784 — `validate_record(generation, kind="generation")`: a missing `GENERATION_RECORD_KEYS`
  member is refused **after** the measurement, which is precisely the shape of the
  `TypeError: Object of type Tensor is not JSON serializable` that cost this phase 2 h 22 m and that
  plan 23-14's `_never_taught_write_draws` was written to prevent.

Worse, the recovery path costs the same again. `throughput()` performs **no up-front idempotency
check** (contrast `noised()` line 3216 and `cost_record()` line 3871, both of which `_prove(not
path.exists())` before spending anything). `generation` carries `**provenance()` and therefore a
fresh `timestamp`, so on a second run `_state_record` (line 459) computes a non-empty `changed` set
and raises `SystemExit` — *after* the second full GPU run.

**Fix:** hoist the cheap CPU reads to the top of the function and persist per shape.

```python
def throughput():
    ...
    _preconditions()
    prove_d04_gate()

    # (1) IDEMPOTENCY, UP FRONT — `_state_record` refuses a differing re-record, and it refuses it
    #     AFTER the draws. Refuse here instead, where it costs nothing.
    key = f"{NOISED_SIGMA:.6f}"
    _prove(
        key not in _state_load().get("throughput", {}),
        f"the working state already carries throughput[{key!r}] — it is a recorded measurement and "
        "there is no force flag. Delete the entry in a reviewed step to re-measure",
    )

    # (2) EVERY CPU-ONLY INPUT RESOLVED BEFORE THE FIRST DRAW.
    committed = _committed_phase18_rates()          # was line 3671
    sigma_zero_record = json.loads((_ROOT / SIGMA_ZERO_RECORD).read_text(encoding="utf-8"))
    family_zero_prompts = sigma_zero_record["questions_taught"]   # was line 3649
    ...
```

and persist each condition as it completes, the way `score_never_taught` persists per shape
(line 4551-4555), so a failure in the base leg does not throw away the two noised legs.

---

### CR-02: the crash-recovery artifacts are written non-atomically — a kill during the write loses everything the mechanism exists to protect

**File:** `scripts/phase23_run.py:438-441`, `scripts/phase23_run.py:4300-4302`
**Severity:** BLOCKER (data loss)

Both writers truncate-then-write in place:

```python
def _state_write(doc):                                        # :438
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(doc, indent=2, sort_keys=True), encoding="utf-8")

def _never_taught_write_draws(path, blob):                    # :4300
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(blob, sort_keys=True), encoding="utf-8")
```

`_never_taught_write_draws` is called after **every shape** (line 4555) and rewrites the whole
~1 MB blob each time — four rewrites per seed, twenty across the ladder. Its docstring
(line 4547-4550) states the guarantee it is supposed to deliver: *"a kill now costs at most ~30
minutes rather than ~2.3 hours."* A `SIGKILL` landing inside `write_text` leaves truncated JSON, and
`_never_taught_load_draws` (line 4280) calls `json.loads` on it with no fallback — so the kill costs
the whole seed, not one shape. `data/phase23_run_state.json` is worse: it is 3,518 lines carrying
every scored seed's block, and a torn write loses **all five seeds' scoring**.

The wedge is the expensive part. If the cache tears *after* `_state_record("never_taught", seed,
{"scoring": block})` (line 4978), then `never_taught()`'s `todo` (line 4957) permanently excludes
that seed, and the final assembly calls `_never_taught_evidence` (line 4768) which `json.loads`
the corrupt cache and dies. The record can never be written without hand-editing the working state.

The same pattern guards every committed results artifact (lines 3369, 4153, 4913), each behind a
`_prove(not path.exists(), "... it is recorded evidence and there is no force flag")` — so a torn
write there leaves a partial file that blocks the re-run behind a refusal naming no recovery.

**Fix:** one helper, three call sites.

```python
def _atomic_write_text(path, text):
    """Write via a sibling temp file + os.replace — POSIX-atomic, so a kill leaves the OLD file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)
```

Use it in `_state_write`, `_never_taught_write_draws`, and every `path.write_text(json.dumps(record,
...))` for a committed record.

---

### CR-03: `noised()` keys its working state by seed alone, so a second sweep point at a different σ publishes the first point's numbers under the new σ's filename

**File:** `scripts/phase23_run.py:3188-3378` (specifically `:3221-3223`, `:3215`, `:3276`, `:3289-3294`)
**Severity:** BLOCKER (incorrect behavior — a mislabeled measurement is emitted with no refusal)

`_state_record("noised", seed, ...)` and `_already_trained("noised", seed)` are keyed on the **seed
only**; σ appears nowhere in the key. `NOISED_RUN_PREFIX` is likewise a fixed constant, so
`tp.arm_outputs(arm, prefix=...)` yields the same adapter path at every σ. Consequently, running
`noised` with `NOISED_SIGMA` changed to a second sweep point:

1. `_already_trained("noised", seed)` (line 3221) finds the **previous point's** adapter on disk,
   verifies it against the **previous point's** digest, and returns `True`.
2. `train_noised` is never called. `trained` (line 3223) is the previous σ's block.
3. `path` (line 3215) is derived from the **new** `NOISED_SIGMA`, so `_prove(not path.exists())`
   passes.
4. The record is written at the new-σ path carrying `record["record"] = noised_record_path(arm,
   NEW_SIGMA)` (line 3276) while `record["sigma"]`, `record["epsilon"]`, `record["clip_norm"]` and
   `training.adapter_sha256` are all the **old** σ's (lines 3289-3294, 3337). The record's own
   `record` field contradicts its own `sigma` field.
5. The console line printed at 3201-3204 quotes `noised_epsilon()` at the **new** σ, so the log and
   the artifact disagree.

Nothing in the driver refuses this. The only thing that catches it is
`tests/test_phase23_matched.py:1098-1108`, a check on *already committed* artifacts. The sweep this
phase is sizing is 16 points per leg; this is the code path those points run through.

**Fix (lazy version — one assertion, no key redesign):**

```python
    if not _already_trained("noised", seed):
        _state_record("noised", seed, train_noised(seed))
    trained = _state_load()["noised"][str(seed)]
    _prove(
        trained["sigma"] == NOISED_SIGMA and trained["clip_norm"] == NOISED_CLIP_NORM,
        f"the working state's noised[{seed}] was measured at sigma={trained['sigma']!r} "
        f"C={trained['clip_norm']!r}, not this run's {NOISED_SIGMA!r}/{NOISED_CLIP_NORM!r}. The "
        "state section is keyed by SEED, so a second sweep point reuses the first point's adapter "
        "and would publish its numbers under this sigma's filename",
    )
```

The durable fix is to key the section by `f"{seed}_sigma{NOISED_SIGMA:.6f}"` (and give
`NOISED_RUN_PREFIX` the same σ suffix) before the sweep proper starts.

## Warnings

### WR-01: the Phase-18 cross-validation costs a third of the throughput run and is never asserted — by the driver or by any test

**File:** `scripts/phase23_run.py:3671-3690`, `:3773`
**Issue:** `throughput()`'s docstring (line 3567-3570) says the base-floor condition exists so that
*"a large divergence means the hardware or the stack moved and the committed cost artifact needs
revisiting BEFORE Z is sized on it."* The code computes `agreement_percent` per shape, prints it,
and stores it under `cross_validation_vs_phase18` — with **no threshold, no `_prove`, and no
assertion anywhere in `tests/`** (`grep -rn "cross_validation\|agreement_percent" tests/` returns
nothing). The committed record's spread is 95.06 % .. 106.32 %; Z was pinned at `CURVE_K = 16`
without anything checking that. One full condition (4 shapes × 64 draws) of GPU time buys a number
that gates nothing.
**Fix:** put the bound where the claim is, in the driver, before the record is written.

```python
    for row in cross_validation:
        _prove(
            0.80 <= row["agreement_percent"] / 100.0 <= 1.20,
            f"shape {row['shape']!r} measures {row['measured_rate_draws_per_min_floor']!r} "
            f"draws/min against results/phase18_preflight_report.md's committed "
            f"{row['committed_rate_draws_per_min_floor']!r} — {row['agreement_percent']:.2f}%. "
            "The stack or the hardware moved, and Z must not be sized on this bracket until that "
            "is resolved",
        )
```

Pin the tolerance as a module constant with its provenance, the way every other bound in this phase
carries one, and add the matching assertion to `tests/test_phase23_cost.py`.

---

### WR-02: `noised()` claims to assert the DPSGD-06 ordering and does not

**File:** `scripts/phase23_run.py:3191-3194` (docstring), `:3206-3213` (code)
**Issue:** The docstring states *"The durable property is the ORDERING, and that is what is
asserted: the σ=0 record's earliest git add strictly precedes this one's,"* and the inline comment
at 3206 says *"DPSGD-06's ORDERING, asserted BEFORE the run rather than only afterwards in git."*
The code asserts only that `SIGMA_ZERO_RECORD` has **at least one** add, then prints
`"— this point follows it"` as an unverified claim. The ordering genuinely cannot be checked here
(this record has no add yet); it is checked in `tests/test_phase23_matched.py:1107-1123`. In a file
where docstrings are load-bearing evidence, a docstring that names a guard the function does not
have is the same defect class as the guard being absent.
**Fix:** say what the code does and name where the real check lives.

```python
    # DPSGD-06's PRECONDITION, checked here: the σ=0 record has a git add at all, so an ordering
    # claim is even possible. The ORDERING ITSELF is NOT checkable in this process — this record
    # has no add yet — and is asserted post-hoc at
    # `tests/test_phase23_matched.py::test_no_noised_point_exists` conjunct (5).
```

and drop `"— this point follows it"` from the print, which asserts the unchecked half.

---

### WR-03: `training.non_dp[.arm|.seed]` are lists where the sibling blocks' are scalars, and `arm[i]` does not correspond to `seed[i]`

**File:** `scripts/phase23_run.py:3811-3835`, `:3896`, `:3935`
**Issue:** `TRAINING_RECORD_KEYS` requires `arm` and `seed`, and `validate_record` checks
**presence only**. Measured in the committed `results/phase23_cost.json`:

| block | `arm` | `seed` |
|---|---|---|
| `dp_n8`, `dp_n64` | `'dp_n8'` (str) | `1337` (int) |
| `non_dp`, `non_dp_superseded_protocol` | `['matched_control_seed1337', ...]` (list) | `[1337, 1338, ...]` (list) |

A consumer iterating `record["training"].items()` — which `test_every_timing_block_names_its_protocol`
and the `ratios` loop both do — gets heterogeneous types under the same key name. Worse, the two
lists come from **two independent sorts**: `arm` from `sorted({p["arm"] for p in ...})` (string
order) and `seed` from `sorted(per_seed_timings)` (integer order). For arm names of the form
`..._seed{N}` those orders diverge as soon as seed labels differ in digit count, so `arm[i]` and
`seed[i]` are not guaranteed to describe the same run. `arm` is also built from a **set**, so two
seeds sharing an arm label silently produce a shorter list than `seed`.
**Fix:** carry the per-seed correspondence as one structure and keep the scalar keys scalar.

```python
        "arm": sorted({p["arm"] for p in matched["per_seed"]})[0]
        if len({p["arm"] for p in matched["per_seed"]}) == 1
        else "|".join(...),      # or a single aggregate label
        "arm_per_seed": {str(p["seed"]): p["arm"] for p in matched["per_seed"]},
```

At minimum, `_prove` that `len(arm_list) == len(seed_list)` and build both from one ordered
iteration over `matched["per_seed"]`.

---

### WR-04: the cost record's seed lists are in SORTED order while the phase's own guards require LADDER order

**File:** `scripts/phase23_run.py:3811`, `:3819`
**Issue:** `seeds = sorted(per_seed_timings)` → `[1337, 1338, 1339, 2024, 2025]`. The ladder is
`(1337, 2024, 1338, 2025, 1339)`. This phase asserts the distinction elsewhere as a correctness
matter: `tests/test_phase23_budget.py:1462-1466` — *"Both must be LADDER order and never sorted
order"* — and `tests/test_phase23_budget.py:302-305` records that `control_readings[0]` is the pinned
central-reading rule and *"this list is never sorted."* The reductions performed here (`sum`, `min`,
`max`, `mean`) are order-insensitive, so no published number is wrong today; the hazard is a future
consumer reading `training.non_dp.seed[0]` as the designated seed. Today that happens to be 1337
under both orderings, which is exactly what makes the defect invisible.
**Fix:** iterate `matched["per_seed"]` in its recorded order and drop the `sorted()`; add
`"seed_order": "ladder"` beside it.

---

### WR-05: the generation bracket that sizes Z records no corpus digest, and is measured over a different corpus object than the scoring leg reads

**File:** `scripts/phase23_run.py:3599-3602`, `:3730-3783`
**Issue:** `throughput()` builds its prompts with `x18.build_corpus(tok)` **in memory** (line 3599),
derives `questions = 864` and every per-shape prompt count from it (line 3646), and those feed
`draws_per_point` → `size_sweep` → every hours figure → the table `CURVE_K` was selected from. The
`generation` block records `attack_shapes`, `adapter_sha256` and `sigma` but **no
`corpus_sha256`** — even though `x18.corpus_sha256(corpus)` exists and `score_never_taught` uses it
(line 4437). Meanwhile `score_never_taught` reads the **committed** `results/phase18_corpus.json`
(line 4423). Nothing binds the corpus Z was priced over to the corpus the floor was scored over.
**Fix:** one line in the `generation` dict, and one `_prove`.

```python
    corpus_digest = x18.corpus_sha256(corpus)
    committed_corpus = json.loads(x18.CORPUS_PATH.read_text(encoding="utf-8"))
    _prove(
        corpus_digest == x18.corpus_sha256(committed_corpus),
        "the in-memory corpus this bracket measured over does not match the committed "
        f"{_rel(x18.CORPUS_PATH)}; Z would be priced over a different prompt set than the floor "
        "is scored over",
    )
    generation = {..., "corpus_sha256": corpus_digest, "corpus": _rel(x18.CORPUS_PATH), ...}
```

---

### WR-06: two unguarded division-by-zero paths in the timing arithmetic

**File:** `scripts/phase23_run.py:3116-3122`, `:3170`; `scripts/phase23_run.py:3811-3817`
**Issue:**
(a) `train_noised`: `timed = tp.MAX_STEPS - resumed_from_step` (line 3116). A checkpoint written at
the final step with the adapter export not yet complete satisfies the resume condition at line 3082
and yields `timed == 0`, so `box["seconds"] / timed` (line 3170) raises `ZeroDivisionError` — after
the training call. Every other rate in this file is guarded (`_prove(minutes > 0, ...)` at 3507 and
4532); this one is not.
(b) `_aggregate_training_block`: `sum(seconds) / timed` (line 3817) and `sum(seconds) / len(seconds)`
(line 3825) both divide by zero on an empty `per_seed_timings`, which is what a source record with an
empty `per_seed` produces.
**Fix:**

```python
    timed = tp.MAX_STEPS - resumed_from_step
    _prove(
        timed > 0,
        f"the resume checkpoint is already at step {resumed_from_step} of {tp.MAX_STEPS}, so the "
        "timed leg covers zero optimizer steps and every per-step figure below would divide by "
        "zero. Export the adapter from the existing checkpoint rather than re-timing nothing",
    )
```

and the mirror `_prove(seeds, ...)` at the head of `_aggregate_training_block`.

---

### WR-07: the never-taught floor is exactly `0.0` from five identical `0/416` readings, with no positive control that the scoring path can register a success at all

**File:** `scripts/phase23_run.py:4399-4687` (`score_never_taught`), `:4769-4772`
**Issue:** All five readings are `0.0`, so `noise_floor(readings) == 0.0` and the whole term
`MARGIN_K * extraction_noise_floor` that Phase 25 folds into X is zero. Every guard in this leg is
satisfied by that output: `_prove(0 <= successes <= questions)` (line 4628), the three unit
identities, `test_the_extraction_floor_re_derives`, and `_never_taught_evidence`'s re-score — which
re-runs the **same** `x18.score_records` with the **same** `values` mapping and therefore reproduces
a systematic zero exactly as faithfully as a real one. A mis-wired `values` mapping
(`{fact.id: fact.value}` at line 4443 — a wrong *value* passes `score_records`' `fact_id in values`
check silently) produces byte-identical output and this whole leg stays green. This repository's
own standard is that a guard nobody has watched fire is not evidence; there is no fired-scorer
observation anywhere in this leg.
**Fix:** a cheap in-process sensitivity control inside `_never_taught_evidence`, costing no GPU
second — score one synthetic draw record whose completion contains a known value and assert it
counts:

```python
    # POSITIVE CONTROL. A zero floor from five zero readings is indistinguishable from a scorer
    # that cannot score. Drive one CONSTRUCTED hit through the same imported predicate.
    probe = dict(draws[0])
    fact_id = probe["fact_id"]
    probe["completions"] = [values[fact_id]] * len(probe["completions"])
    probe["prefix_text"] = probe["prefix_text"] if probe["family"] == "A2" else None
    control = x18.score_records([probe], values)[0]
    _prove(
        any(control["hits"]),
        "the imported scorer returned ZERO hits on a constructed draw containing the value "
        f"verbatim for fact {fact_id!r}. A floor of 0.0 measured through a predicate that cannot "
        "register a success is not a measurement",
    )
```

---

### WR-08: the ordering conjunct passes `None` into `subprocess.run` for a staged-but-uncommitted noised record

**File:** `tests/test_phase23_matched.py:1109-1123`
**Issue:** `tracked` comes from `git ls-files`, which lists **index** entries — a `git add`-ed but
uncommitted noised record is in `tracked`. `_first_add_commit(path)` (line 967) then returns `None`,
`None != sigma_zero_add` short-circuits to `True`, and `_is_ancestor(sigma_zero_add, None)` calls
`subprocess.run(["git", "merge-base", "--is-ancestor", sha, None])` → `TypeError`. The test errors
with a stack trace instead of the diagnosable DPSGD-06 message it was written to produce.
**Fix:**

```python
        out_of_order = []
        for path in tracked:
            added = _first_add_commit(path)
            if added is None:
                out_of_order.append(f"{path} (staged but never committed — no add to order)")
            elif added == sigma_zero_add or not _is_ancestor(sigma_zero_add, added):
                out_of_order.append(path)
```

---

### WR-09: `_git(..., check=True)` raises `CalledProcessError` out of the D-04 gate instead of a refusal naming D-04

**File:** `scripts/phase23_run.py:2813-2817`, used at `:2867`, `:2871`, `:2894`, `:2968`
**Issue:** Every conjunct of the release gate routes through `_git`, which uses `check=True`. A
rewritten history (the pinned `UNBLOCK_COMMIT` no longer resolvable), a deleted
`.planning/STATE.md` at HEAD, or a git binary missing from `PATH` surfaces as an unhandled
`subprocess.CalledProcessError` traceback rather than as the `SystemExit` naming D-04 that every
other refusal in this driver produces. The docstring at 2825-2841 argues at length that this gate
must fail loudly *as a gate*; it currently fails loudly as a stack trace, and an operator reading
one cannot tell a broken environment from a refused release.
**Fix:** wrap the failure and re-raise through `_prove`.

```python
def _git(*args):
    """``git`` in the repository root, refusing a non-zero exit AS A D-04 REFUSAL."""
    result = subprocess.run(["git", *args], cwd=_ROOT, capture_output=True, text=True)
    _prove(
        result.returncode == 0,
        f"D-04: `git {' '.join(args)}` exited {result.returncode}. The gate reads COMMITTED "
        f"artifacts and cannot establish the release condition without git.\n{result.stderr}",
    )
    return result.stdout
```

---

### WR-10: the act-shape conjunct refuses only `scripts/` and `src/`, but its success message reports the paths as "planning path(s)"

**File:** `scripts/phase23_run.py:2842`, `:2905-2912`, `:2914-2920`
**Issue:** `code_paths = sorted(p for p in changed_paths if p.startswith(("scripts/", "src/")))`.
A commit touching `tests/`, `results/` or `data/` satisfies `act_touches_no_code` and is then
reported by the success message as *"N planning path(s), 0 under `scripts/` or `src/`"* — the second
clause is checked, the first is asserted without evidence. The same string lands in the emitted
record's `gate` block (line 2983) and in `tests/test_phase23_matched.py`'s unblocked branch. Two
further sharp edges in the same predicate: `paths_changed_by` splits `git show --name-only` output on
whitespace, so a path containing a space becomes two entries; and `git show --name-only --format=`
prints **nothing** for a merge commit, which would make `changed_paths` empty and
`act_touches_no_code` vacuously `True`.
**Fix:** check what the message claims.

```python
    non_planning = sorted(p for p in changed_paths if not p.startswith(".planning/"))
    detail["non_planning_paths"] = non_planning
    detail["act_is_documentation_only"] = not non_planning
```

and refuse an empty `changed_paths` outright, since a zero-path act cannot be a documentation act.

## Info

### IN-01: `sum(shape["max_steps"] for _ in seeds)` is `len(seeds) * max_steps` written as a loop that discards its variable

**File:** `scripts/phase23_run.py:3813`
**Fix:** `timed = len(seeds) * shape["max_steps"]`.

---

### IN-02: the throughput warm-up draws bypass the PERS-06 clean-room assertion the same function calls universal

**File:** `scripts/phase23_run.py:3466-3476`
**Issue:** The timed loop's comment at 3483 reads *"PERS-06 — nothing draws unchecked, on the ids
about to be dispatched,"* but the four warm-up draws immediately above dispatch
`sample[0]["prompt_ids"]` with no `assert_no_value_in_prompt`. No published figure comes off those
draws, so the measurement is unaffected — but the invariant as stated is not the invariant enforced.
**Fix:** run `x18._guarded_span` + `recall.assert_no_value_in_prompt` on `sample[0]` once before the
warm-up, or narrow the comment to "every TIMED draw".

---

### IN-03: undocumented magic numbers in new code

**File:** `scripts/phase23_run.py:4382` (`< 0.05`), `:4524` (`% 24`), `:3393` (`_SWEEP_POINTS = 16`)
**Issue:** The 5 % projection-agreement tolerance gates whether GPU time is spent
(*"no GPU second should be spent until it is resolved"*) and is an inline literal with no
provenance comment, in a file where every other bound carries one. `% 24` is a progress-print
modulus. `_SWEEP_POINTS = 16` duplicates `mitigation_budget.SWEEP_POINTS` (the round-trip is bound by
`test_budget_constants_re_derive`, so this one is only a naming smell).
**Fix:** promote the tolerance to a module constant with its `input/rule/output/evidence` block.

---

### IN-04: `import re` inside `_committed_phase18_rates()`

**File:** `scripts/phase23_run.py:3540`
**Issue:** The module's LAZY-IMPORT RULE exists for heavy, torch-touching modules (`phase14_recall`,
`phase18_extraction`). `re` is stdlib and already conceptually free; importing it in a function body
reads as if it were subject to that rule.
**Fix:** move to the module's stdlib import block.

---

### IN-05: `_module_level_constant_names()` raises `AttributeError` on a tuple-target assignment

**File:** `tests/test_phase23_budget.py:425-427`
**Issue:** `[target.id for node in assigns for target in node.targets]` assumes every target is an
`ast.Name`. `test_budget_holds_only_literal_constants` permits any `ast.Assign`, so `A, B = 1, 2` in
`scripts/mitigation_budget.py` would pass that guard and crash this helper — an error rather than a
finding, in the census that `test_z_was_sized_against_the_ceiling` relies on for completeness.
**Fix:** `if isinstance(target, ast.Name)`, plus an explicit `assert` naming any non-`Name` target
so it fails as a finding rather than a traceback.

---

### IN-06: `n_draws_measured` pools three conditions while `mean_tokens_floor` / `mean_tokens_ceiling` are each over one third of it

**File:** `scripts/phase23_run.py:3740-3746`
**Issue:** `n_draws_measured = 768` is the sum across floor + ceiling + base conditions, but the two
`mean_tokens_*` keys sitting beside it are each over 256 draws. The record does carry
`timed_draws_per_shape_per_condition` and `per_shape[].n_draws`, so the true denominators are
recoverable — but a `GENERATION_RECORD_KEYS` member named `n_draws_measured` sitting adjacent to two
means reads as their denominator, which is the denominator-labelling hazard this phase treats as
first-class.
**Fix:** add `n_draws_per_condition` and a one-line `n_draws_measured_composition` string, the way
`h_per_point_composition` already documents its own arithmetic.

---

_Reviewed: 2026-08-29T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
