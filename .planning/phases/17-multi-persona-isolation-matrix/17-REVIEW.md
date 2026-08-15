---
status: issues_found
phase: 17
depth: standard
files_reviewed: 11
files_reviewed_list:
  - scripts/phase17_isolation.py
  - scripts/phase17_persona_facts.py
  - scripts/phase17_persona_gate.py
  - scripts/phase17_personas.py
  - scripts/teach_persona.py
  - tests/test_lora_inject.py
  - tests/test_phase14_teaching.py
  - tests/test_phase16_prereg.py
  - tests/test_phase17_personas.py
  - tests/test_phase17_scoring.py
  - tests/test_phase17_stats.py
critical: 0
warning: 8
info: 6
total: 14
---

# Phase 17: Code Review Report

**Reviewed:** 2026-08-15T00:00:00Z
**Depth:** standard
**Files Reviewed:** 11
**Status:** issues_found

## Summary

Reviewed the Phase 17 isolation-matrix surface (~2.6k lines of new driver code, ~3.6k lines of new
tests) with an adversarial stance: assume the numbers are wrong until the code says otherwise.

**The gated result survives the review.** I traced the published verdict end to end —
`held_out_by_slot` → `score_completion` → `classify` → `assemble_matrix` → `cell_rates` →
`fact_signs` → `sign_test_exact` → `holm` → `gate_cleared` — and the question-unit rate, the
8-slot pairing, the six-comparison family, the Holm step alphas and the `0.0078125 < 0.0083333`
margin are all internally consistent and match `results/phase17_isolation_report.md`. Cell-blindness
is structural, not conventional. The ISO-04 two-layer digest proof and the ISO-03 `adapter_enabled`
argument are correct, including the non-obvious point that no weight digest can witness inertness.
The `weights_only=True` choke points hold; there is no direct `torch.load` on a shareable artifact,
no shell interpolation (`subprocess.run` is list-form everywhere), no path traversal reachable from
`--seed`/`--sweep` (both are `_prove`d against pre-registered tuples before reaching a path), and no
secrets. All 79 Phase 17 tests pass.

**What I found instead clusters in three places:** (1) one published table whose numbers are
structurally forced and therefore carry no information, presented beside measured numbers;
(2) three guards/assertions that cannot fail or are weaker than their own docstrings claim — the
exact defect class this phase spends most of its prose closing; (3) a family of "CPU-only, no torch"
claims that are measurably false, one of which is used as the stated justification for duplicating a
rule. Nothing here changes a gate result or a published rate.

**Explicitly checked and found sound** (not reported as defects): `phase17_personas.py`'s
pre-registration constants, the `frozenset` dedup in `base_prior_anchor` (call sites keep the units
separate, and the report's D-13 addendum labels them), `classify` taking no column index,
the base row's exclusion from the Holm family, the lazy-import discipline as it applies to *value
strings*, and the deliberate non-refactor of `_question_triples`.

---

## Warnings

### WR-01: The base row's `Categories` line is structurally forced and cannot vary — but is published beside measured counts

**File:** `scripts/phase17_isolation.py:411-415`, rendered at `:1682-1684`; artifact
`results/phase17_isolation_report.md` §Categories

**Issue:** For the adapter-off row, `own is None`, so `classify` can only return `base_prior`:

- branch 1 needs `own is not None` — unreachable;
- branch 2 catches every non-empty `labels` → `base_prior`;
- branch 4 tests `normalize(completion) in base_texts[slot]`, and `base_texts_by_slot` built that
  set from **the same record's own completions** (`:288-291`), so the membership test is always
  `True` → `base_prior`;
- branch 5 (`confabulation`) is therefore unreachable for the base row.

The base row's four counts are `(diagonal=0, leak=0, base_prior=n_questions, confabulation=0)` for
*any* input data. Verified by execution against a deliberately hostile base record (junk strings,
empty strings, other personas' values, non-repeating text): result
`{'diagonal': 0, 'leak': 0, 'base_prior': 24, 'confabulation': 0}` over 24 questions.

`BASE_PRIOR_DERIVATION_NOTE` (`:1462-1469`) tells the reader that `leak` and `diagonal` are zero
**by construction** — and says nothing about the other two. A reader therefore reads
`| base | 0 | 0 | 104 | 0 |` beside `| persona_b | 103 | 0 | 0 | 1 |` and concludes the un-adapted
base produced zero confabulations while adapter B produced one. The data cannot support that: the
base row's `confabulation` is 0 because the category is unreachable, not because none occurred.

**Failure scenario:** a reviewer of the portfolio artifact quotes "the adapter-off column confabulated
0/104 while the adapters confabulated 1/104" — a comparison the instrument structurally cannot make.
This is the same defect class the phase names repeatedly ("a category that reads zero because nothing
ever wrote to it is indistinguishable in the report from a category that genuinely never occurred",
`:56-58`) arriving in the one row nobody checked it against.

**Fix:** render the base row's category cells as a sentinel rather than counts, and state the
reachability fact where the reader meets it:

```python
CATEGORY_ROW_PROPERTY_NOTE = (
    ...
    "**The adapter-off row's four counts are FORCED, not measured.** With `own=None` branch 1 is "
    "unreachable, branch 2 catches every non-empty label set, and branch 4's membership test is "
    "against that row's OWN completions — so `base_prior` is always the full question count and "
    "`confabulation` is always 0, whatever the base produced. They are printed as `n/a`."
)
# in render_report:
for row in rows:
    if row == personas.BASE_ROW:
        blocks.append(f"| `{row}` | " + " | ".join("n/a (forced)" for _ in CATEGORIES) + " |")
        continue
    entry = matrix[(row, personas.PERSONAS[0])]
    blocks.append(f"| `{row}` | " + " | ".join(str(entry[name]) for name in CATEGORIES) + " |")
```

Note the committed report is protected by `assert_isolation_report_not_clobbered` and
`test_report_addendum_is_additive`, so this is a fix for the *writer* plus a dated addendum on the
artifact — not a regeneration.

---

### WR-02: `assemble_matrix` crashes with a bare `IndexError` on a zero-completion question; the guard that would name the contract runs afterwards

**File:** `scripts/phase17_isolation.py:411-415`; ordering at `:1921-1923` and `:2194-2195`

**Issue:** `drawn = [classify(...) for done in completions]`, then
`categories["base_prior" if "base_prior" in drawn else drawn[0]] += 1`. When one recorded entry has
`"completions": []`, `frozenset().union(*())` yields an empty frozenset (fine) but `drawn` is `[]`
and `drawn[0]` raises. Every other failure in this module exits through `_prove` with a message
naming the violated contract and the consequence for the resulting number; this one produces a raw
traceback pointing at a list index.

`draws_per_question` (`:1237-1247`) *would* catch it with a proper message — it proves all recorded
questions carry one draw budget — but it is called at `:1923`, **after** `assemble_matrix` at
`:1921`. Same inversion in `replication_payload` (`:2194` then `:2195`).

**Failure scenario:** verified by execution. A four-record fixture where exactly one `persona_a`
entry carries `"completions": []` produces `IndexError: list index out of range` instead of a named
abort. Reachable from `--report`/`--replicate`, which read arbitrary JSON off disk; `run_one_sweep`
guards its own writes (`:1064-1070`) but the report path does not re-derive that.

**Fix:** hoist the budget proof, and give the empty case its own `_prove`:

```python
# in run_report_mode / replication_payload — before assemble_matrix
n_draws = draws_per_question(records)
matrix = assemble_matrix(records, values_by_slot(), base_texts)
described = describe_matrix(matrix, n_draws, resamples=resamples)
```

```python
# in assemble_matrix, inside the entry loop
completions = entry["completions"]
_prove(
    completions,
    f"sweep record {row!r} carries a question at slot {slot!r} / seed_index "
    f"{entry['seed_index']} with NO completions — that question contributes a row to the "
    "denominator while contributing no draw to the numerator, so the cell rate would be "
    "computed over more questions than were ever answered",
)
```

---

### WR-03: `append_addendum`'s closing `_prove` is a tautology — it cannot fail, and its message claims otherwise

**File:** `scripts/phase17_isolation.py:2399-2415`

**Issue:**

```python
before, after = text.split(REPLICATION_PENDING_LINE)
updated = before + REPLICATION_MEASURED_LINE + after
if not updated.endswith("\n"):
    updated += "\n"
updated = updated + "\n" + addendum.rstrip("\n") + "\n"
...
_prove(
    updated.startswith(before) and addendum.rstrip("\n") in updated,
    "... the append-only property is the whole guarantee this helper offers and it is checked "
    "on the produced bytes, not assumed from the construction",
)
```

`updated` is built by concatenating `before` as the leftmost operand, so `updated.startswith(before)`
is true for every possible input, including `before == ""`. `addendum.rstrip("\n") in updated` is
likewise true by the last concatenation. The message asserts the check is "on the produced bytes,
not assumed from the construction" — but it is precisely an assumption from the construction. This
is a `_prove` nobody can watch fail, which `assert_phase17_family_closed:254-256` in this same phase
correctly identifies as a defect ("a `_prove` that can never fire is a `_prove` nobody can watch
fail").

The real append-only guarantee is delivered by `test_addendum_writer_is_append_only` and
`test_report_addendum_is_additive`, which compare against an *independently obtained* `before`
(the on-disk text and the git blob respectively). Those are sound. This runtime one is decoration.

**Fix:** compare against a re-read of the file rather than against the local it was built from, or
delete it and let the tests carry the claim:

```python
path.write_text(updated, encoding="utf-8")
written = path.read_text(encoding="utf-8")
_prove(
    written[: len(before)] == before and written.endswith(addendum.rstrip("\n") + "\n"),
    f"{path} on disk does not carry its original prefix byte-identically, or lost the addendum "
    "— the append-only property is checked against the bytes that actually landed, and an "
    "encoding or newline transform between here and the filesystem is exactly what a check "
    "against the in-memory string cannot see",
)
```

---

### WR-04: `--replicate` writes `phase17_replication.json` before the addendum's own guards run, so a refused append leaves a stale artifact that blocks every retry

**File:** `scripts/phase17_isolation.py:2461-2466` (the exists-guard), `:2509-2513` (write, then append)

**Issue:** `run_replicate_mode` refuses to clobber `REPLICATION_RECORD_PATH` at the top, then writes
it at `:2509`, and only then calls `render_replication_addendum` (two `_prove`s at `:2354-2365`) and
`append_addendum` (the placeholder-count `_prove` at `:2391-2398`). If any of those three fires, the
JSON is already on disk and the report is un-appended. A retry then aborts on
*"`phase17_replication.json` already exists — it is recorded ISO-05 evidence and this mode will not
overwrite it. If it genuinely must be regenerated, delete it in a reviewed commit"* — recovery
guidance written for a *successful* run's artifact, now demanded for a half-finished one.

This inverts the module's own stated discipline, applied correctly three times elsewhere:
`run_one_sweep` step 1 (`:939-941` "Refuse to clobber the record FIRST, before anything expensive"),
`run_report_mode` step 1 (`:1889`), and `phase17_persona_gate.main:205-207`.

**Failure scenario:** verified by execution. Run `--replicate` against a report whose placeholder was
already replaced (0 occurrences — e.g. a re-run after a partial success):
`append_addendum` refuses, and `iso.REPLICATION_RECORD_PATH.exists()` is `True` afterwards. Every
subsequent `--replicate` now aborts at the exists-guard until a human deletes the file.

**Fix:** validate the report's shape before writing anything, at the same point the other
preconditions are checked:

```python
    _prove(
        not REPLICATION_RECORD_PATH.exists(), ...
    )
    report_text = ISOLATION_REPORT_PATH.read_text(encoding="utf-8")
    found = report_text.count(REPLICATION_PENDING_LINE)
    _prove(
        found == 1,
        f"{ISOLATION_REPORT_PATH} carries {found} occurrence(s) of the placeholder line — "
        "checked HERE, before the payload is written, so a refusal leaves no half-finished "
        "phase17_replication.json that the exists-guard above would then refuse to replace",
    )
```

(`append_addendum` keeps its own check — this is a cheap precondition, not a replacement.)

---

### WR-05: `--report --seed N` silently ignores the seed, in a driver that refuses the identical mistake for `--replicate`

**File:** `scripts/phase17_isolation.py:915-920` (parser), `:2546-2549` (dispatch), contrast
`:2550-2562`

**Issue:** `--seed` sits outside the mutually exclusive group and applies to any mode. The
`--replicate` branch refuses a stray `--seed` with an explicit and correct rationale:

> a silently ignored flag would let them keep believing [a scoping that did not happen]

The `--report` branch has exactly the same property — `read_sweep_records` reads the four *unscoped*
records by name (`:1199-1200`), so any `--seed` is dropped — and no refusal. Verified:
`build_parser().parse_args(["--report", "--seed", "9999"])` parses cleanly and `main()` never reads
`args.seed` on that branch.

**Failure scenario:** an operator who has just run `--sweep persona_a --seed 1437` types
`--report --seed 1437` expecting a seed-scoped matrix, gets the unscoped four-record matrix, and has
no signal that the flag did nothing. The generated report carries no seed in §Provenance to
contradict them.

**Fix:** apply the same refusal, with the mode-specific reason:

```python
    elif args.report:
        _prove(
            args.seed is None,
            f"--report was given --seed {args.seed}. The report assembles the four UNSCOPED sweep "
            "records by name (17-11's seed-scoped replicates are structurally unreachable from "
            "read_sweep_records), so there is no seed to select: a seed here would be silently "
            "ignored and the operator would believe a scoping that did not happen",
        )
        result = run_report_mode()
```

---

### WR-06: `run_replicate_mode`'s "recorded verdict" precondition accepts `PENDING`, contradicting both its own docstring and the sibling guard 1200 lines above it

**File:** `scripts/phase17_isolation.py:2453-2460`; contrast `:1171-1181`

**Issue:** two guards in one file use opposite definitions of "recorded":

```python
# assert_isolation_report_not_clobbered:1173-1174 — PENDING is NOT recorded
recorded = _verdict.recorded_verdict(ISOLATION_REPORT_PATH.read_text(encoding="utf-8"))
if recorded is None or "PENDING" not in recorded:
    raise SystemExit(...)

# run_replicate_mode:2453-2455 — any non-empty body IS recorded
recorded = _verdict.recorded_verdict(ISOLATION_REPORT_PATH.read_text(encoding="utf-8"))
_prove(recorded is not None and recorded.strip(), ...)
```

`run_replicate_mode`'s docstring (`:2426-2428`) states the requirement as *"The report must exist AND
carry a recorded verdict ... running it against a missing or unrecorded report would be writing a
conclusion before there is one to append it to."* Under this phase's own definition of "recorded"
(the one at `:1174`, and the one `phase17_persona_gate.assert_report_not_clobbered:152` and
`teach_persona._refuse_clobber` also use), a `PENDING` body is *unrecorded* — and the check passes on
it.

**Failure scenario:** an isolation report whose `## Verdict` section reads
`PENDING — awaiting review` and which still carries `REPLICATION_PENDING_LINE`. `--replicate` accepts
it, appends the ISO-05 addendum and writes `phase17_replication.json`, publishing a replication
addendum beside a verdict that was never recorded. (Low likelihood — `render_report` never emits
PENDING for this report, so the state requires a hand-written file — but the guard is weaker than the
sentence that describes it, and this phase treats that gap as a defect everywhere else.)

**Fix:** use the same predicate as the sibling guard:

```python
    _prove(
        recorded is not None and recorded.strip() and "PENDING" not in recorded,
        f"{ISOLATION_REPORT_PATH} carries no RECORDED `## Verdict` section — PENDING is not a "
        "recorded verdict, which is exactly how assert_isolation_report_not_clobbered above "
        "reads the same field. The replication describes the spread around a result that has "
        "already been recorded",
    )
```

---

### WR-07: The "CPU-only / no torch" claim is repeated four times in `phase17_isolation.py` and is measurably false — and one instance is the stated justification for duplicating a rule

**File:** `scripts/phase17_isolation.py:11`, `:1885`, `:2032-2035`, `:2422`; root cause at `:41`

**Issue:** `phase17_isolation.py:41` does `import phase16_persistence as persistence` at **module
scope**. `phase16_persistence.py:40` imports `phase14_recall`, and `phase14_recall.py:60` imports
`torch` at module scope. Verified by execution:

```
torch in sys.modules after importing phase17_isolation: True
phase14_recall in sys.modules: True
```

So every one of these is false as written:

- `:11` — *"Everything in THIS plan is pure CPU: no torch, no I/O beyond reading recorded JSON."*
- `:1885` — `run_report_mode`: *"Pure CPU: no torch, no model, no tokenizer, no generation."*
- `:2422` — `run_replicate_mode`: *"CPU-only: no torch, no model, no tokenizer, no generation."*
- `:2032-2035` — `replicate_record_path`: *"`resolve_seed` ... is deliberately not called here: it
  resolves an adapter path through `teach_persona.arm_outputs`, which imports torch at module scope,
  and this mode is CPU-only by construction — no torch, no model, no generation."*

The repository already knows this fact and states it correctly elsewhere:
`scripts/phase17_persona_facts.py:20-24` — *"the pre-registration imports `phase16_persistence`,
which imports `phase14_recall`, which puts `torch` in `sys.modules`."* Two committed files assert
opposite things about the same import chain.

The fourth instance is load-bearing rather than cosmetic: it is the stated reason
`replicate_record_path` re-implements the `seed != PERSONA_SEEDS[persona]` rule (`:2049-2050`)
instead of calling `resolve_seed` (`:858`). The premise is false, so the duplication has no stated
justification left (see IN-06 for the drift risk it creates). The corresponding lazy `from
phase14_recall import ...` inside `score_completion`/`classify`/`base_texts_by_slot` are
`sys.modules` cache hits that buy nothing with respect to torch — they remain correct as a
*value-string* discipline, which is what the LAZY-IMPORT RULE at `:13-19` actually says.

**Fix:** state what is true, and separate the two claims:

```
Everything in THIS plan is pure-CPU AT RUNTIME: no model load, no tokenizer load, no generation,
no tensor allocated and no I/O beyond reading recorded JSON. It is NOT torch-free at IMPORT —
`import phase16_persistence` above reaches `phase14_recall`, which imports torch at module scope
(measured; `scripts/phase17_persona_facts.py:20-24` records the same chain). The LAZY-IMPORT RULE
below is about keeping VALUE STRINGS off this module's import surface, which it does; it has never
been about torch and must not be read as such.
```

and re-justify `replicate_record_path` on the real ground (it needs no adapter path at all), or
simply call `resolve_seed`.

---

### WR-08: `test_phase16_prereg.py`'s product assertion is a tautology, and its failure message names a failure mode it structurally cannot catch

**File:** `tests/test_phase16_prereg.py:187-207`

**Issue:**

```python
checked = 0
for artifact in tracked_artifacts:
    ...
    for prereg in prereg_commits:
        subprocess.run(("git", "merge-base", "--is-ancestor", prereg, first_add), check=True)
        checked += 1

assert checked == len(prereg_commits) * len(tracked_artifacts), (
    "... a `git ls-files` pattern that matches nothing while artifacts sit on disk would "
    "otherwise make this green having checked nothing."
)
```

`checked` is incremented exactly once per `(artifact, prereg)` pair, so it equals
`len(prereg_commits) * len(tracked_artifacts)` on every path that reaches the assertion (any
`merge-base` failure raises `CalledProcessError` first). The assertion can never fail. Worse, its
message claims it catches an empty match set — it cannot: `0 == n * 0` passes, which the very next
comment concedes (`:208-209`). The failure mode is genuinely closed by `assert checked` at `:212`,
which is correct.

This matters because it sits inside the phase's single most load-bearing test — the STAT-05 ancestry
guard on which the whole "pre-registered, not chosen after the numbers" claim rests. A reader
auditing that claim counts two assertions defending it and finds one is scenery.

**Fix:** either delete the product assertion (it is fully subsumed by `assert checked`), or make it
non-tautological by counting the pairs independently of the loop that performs them:

```python
    expected_pairs = {
        (artifact, prereg) for artifact in tracked_artifacts for prereg in prereg_commits
    }
    assert verified == expected_pairs, (
        f"{sorted(expected_pairs - verified)} ancestry pair(s) were never asked of git — the "
        "loop skipped work it was supposed to do"
    )
```

(where `verified` is a set the loop adds `(artifact, prereg)` to after each successful
`merge-base`). Also note the related `adds[-1]` gap at `:192` — see IN-02.

---

## Info

### IN-01: `read_replicate_records` never checks the record's own `seed` field against the path it was read from

**File:** `scripts/phase17_isolation.py:2080-2099`

**Issue:** `run_one_sweep` records `"seed": resolved["seed"]` (`:1086`), but the replicate reader
validates only the label (`:2093-2098`), the pid/digest distinctness (`:2102-2125`), the
`adapter_enabled` flag and the question triples. Swapping the *contents* of
`phase17_sweep_persona_a_seed1437.json` and `..._seed1537.json` passes every one of those checks —
labels match, digests stay pairwise distinct, triples are identical — while
`pair_mean_off_diagonal_by_seed_index` and the addendum's per-cell provenance table attribute each
rate to the wrong seed. The recorded `seed` field is the available cross-check and is not used.

**Fix:** one line beside the label proof:

```python
            _prove(
                record.get("seed") == seed,
                f"{path} records seed {record.get('seed')!r} but was read as {persona!r}'s seed "
                f"{seed} — the per-seed spread would attribute each rate to the wrong "
                "initialization, and every other proof here passes on a pair of swapped files",
            )
```

### IN-02: `adds[-1]` without an empty guard, where the sibling loop in the same file guards it

**File:** `tests/test_phase16_prereg.py:189-192`; contrast `:91-95`

**Issue:** `test_prereg_commit_precedes_every_v3_results_artifact` handles `if not adds:` by
recording the path as untracked. `test_phase17_prereg_is_frozen_before_every_phase17_result` indexes
`adds[-1]` directly. `git ls-files` lists index entries, so a `results/phase17_*` file that has been
`git add`ed but not committed yields `adds == []` → `IndexError` instead of a named assertion.
Red either way, but with a message that sends the reader to the wrong place.

**Fix:** mirror the sibling's `if not adds: untracked.append(artifact); continue`.

### IN-03: the "committed before the four sweeps run" comment is now false for the constant directly below it

**File:** `scripts/phase17_isolation.py:1429-1432`, applying to `:1471-1487` and the rendered verdict
literal at `:1698-1699`

**Issue:** `BASE_PRIOR_SEED_ANCHOR_NOTE` and the table-cell verdict string were rewritten in
`6619677` (plan 17-11), *after* `68033ab` (plan 17-09) published
`results/phase17_isolation_report.md`. The block comment above them still reads *"Every framing
string below is a module-level constant committed before the four sweeps run: a report whose text is
written AFTER the numbers is a report written to fit them."*

The exception is properly disclosed in `17-11-SUMMARY.md:182-202` and inside the constant's own body
(`:1476-1486`) and `base_prior_anchor`'s docstring (`:1391-1405`) — this is not an undisclosed
post-hoc edit. What is left un-updated is the unqualified comment that governs the block, and the
resulting divergence between the source constants and the published artifact (the report still reads
*"investigate this sweep"*; the source now renders *"the known cause is upstream"*). A regeneration
would silently change the artifact's prose; `test_report_addendum_is_additive` is what makes that
visible.

**Fix:** amend `:1429-1432` to carry the named exception and its date, so the comment and the
SUMMARY agree without a reader having to find the SUMMARY.

### IN-04: the report prints Phase 16's `SIGN_TEST_N` labelled as "slots", with no assertion tying it to `SLOTS_EXPECTED`

**File:** `scripts/phase17_isolation.py:1627-1630`

**Issue:** `f"all {family * persistence.SIGN_TEST_N} slot-level observations ({family} comparisons x
{persistence.SIGN_TEST_N} slots)"` reads Phase 16's constant and calls it Phase 17's slot count. The
phase guards the *other* half of this coincidence explicitly —
`assert_family_length_matches_phase16` exists precisely because `C(4,2) == 3x2` is luck — but
`SIGN_TEST_N == 8` and `SLOTS_EXPECTED == 8` is the same class of coincidence and has no twin
assertion. A divergence aborts loudly inside `fact_signs` (`:1077-1081`) before any number is
printed, so this cannot publish a wrong figure; it is a coupling smell in an area where the phase
otherwise refuses coincidences.

**Fix:** add `_prove(persistence.SIGN_TEST_N == personas.SLOTS_EXPECTED, ...)` in `compare_cells`
beside the existing `assert_family_length_matches_phase16` call, or render
`personas.SLOTS_EXPECTED` in the report text.

### IN-05: `phase17_persona_gate` reads ambient `sys.argv` for `--force` and has no argument parser at all

**File:** `scripts/phase17_persona_gate.py:150`, `:204`, `:538-539`

**Issue:** `assert_report_not_clobbered` disarms on `"--force" not in sys.argv[1:]`. The driver
defines no `argparse` surface, so `python scripts/phase17_persona_gate.py --anything-at-all` runs a
full GPU pre-flight with the typo silently accepted, and any ambient argv carrying the exact token
`--force` (a wrapper, a test runner) disarms the clobber guard. The docstring justifies the
module-level, zero-arg shape on monkeypatchability grounds, which is a good reason for the *shape*
but not for reading the global.

**Fix:** take `argv` as a defaulted parameter (`def assert_report_not_clobbered(argv=None): argv =
sys.argv[1:] if argv is None else argv`) — monkeypatchable and no longer coupled to the ambient
process state — and add a two-line parser that rejects unknown flags.

### IN-06: the "is this the default seed?" rule is implemented twice

**File:** `scripts/phase17_isolation.py:858` and `:2049-2050`

**Issue:** `resolve_seed` computes `replicate = seed != default` to decide whether the record path is
scoped; `replicate_record_path` re-derives the same decision independently. The docstring at
`:2033-2035` acknowledges the duplication and justifies it on a premise that is false (see WR-07).
If the rule ever changes on one side, `--sweep` writes a path `--replicate` does not look for; the
failure is loud (`"... is missing"`) but the diagnosis points at a missing sweep rather than at a
divergent rule.

**Fix:** have `replicate_record_path` call `sweep_record_path(persona, seed=None if seed ==
personas.PERSONA_SEEDS[persona] else seed)` through a single shared helper that both `resolve_seed`
and this function use, e.g. `_scoped_seed(persona, seed)`.

---

_Reviewed: 2026-08-15_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
