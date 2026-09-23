---
phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa
plan: 01
subsystem: testing
tags: [refusal-template, containment-guard, mask-fraction, tokenizer, static-scan, pytest]

# Dependency graph
requires:
  - phase: 14-fact-set-and-recall-scoring
    provides: "`phase14_factset.SLOT_FORMS` (the 11 published slots), `LOCKED_VALUES` + `GATE_REJECTED_CANDIDATES` (the 20-value D-10 lexicon), and `tests/test_phase14_scoring.py`'s `embedded_fact_values` / `_module_strings` substring scan"
  - phase: 18-attack-suite
    provides: "`results/phase18_corpus.json` — the 336 core_taught prompts across A1-mild / A1-aggressive / A3 that set the worst mask-fraction corner"
  - phase: 21-privacy-unit-dp-data-path
    provides: "`scripts/phase21_filler.py`'s module shape — a typed slot-keyed dict plus an import-time `SystemExit` refusal"
provides:
  - "`scripts/phase24_adversarial.py` — D-01's 11-slot, first-person, value-free refusal table, `refusal_for(slot)`, import-time key-parity refusal, and the two D-05 calibration constants"
  - "`MIN_REFUSAL_SCORED_TOKENS = 15` and `MASK_FRACTION_MARGIN = 0.05` as importable constants (24-06 / 24-07 consume both; neither is retyped in a test)"
  - "`tests/test_phase24_refusal.py` — key parity, the D-05 scored-token floor measured through the frozen tokenizer, lowercase register, and undeclared-slot refusal"
  - "`tests/test_phase14_scoring.py::test_no_fact_values_in_the_refusal_templates` — the D-02 sibling containment guard, watched RED then GREEN"
affects: [24-04 contains_refusal, 24-05 corpus-to-episode builder, 24-06 build_bins adversarial_ratio seam, 24-07 four-corner band check]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Sibling guard over edit: a second containment scan with its own separately-pinned lexicon count, leaving the incumbent guard byte-identical"
    - "Calibration constant carried with a four-field `input / rule / output / evidence` comment block, every input re-derived at HEAD"
    - "Parameterised `_load_driver(name, filename)` with incumbent defaults — one loader for two scanned modules, zero call-site churn"

key-files:
  created:
    - scripts/phase24_adversarial.py
    - tests/test_phase24_refusal.py
  modified:
    - tests/test_phase14_scoring.py

key-decisions:
  - "REFUSAL_TEMPLATE stays a SINGLE clause ('i will not share {noun}.') — the plan allowed a second clause only if the length measurement demanded one, and it does not: the one-clause form measures 18..26 scored tokens against a floor of 15"
  - "The slot noun phrases are written FIRST-PERSON and are not `SLOT_FORMS[slot].np1/.np2` — those are second-person question phrasing, and an assistant answering in them would be quoting the attacker"
  - "ADVT-01 is NOT ticked in REQUIREMENTS.md: six of this phase's seven plans carry it, and this one ships only the refusal half"
  - "`_load_driver` widened with defaults rather than a second copied loader — the two containment scans get one loader that cannot drift"

patterns-established:
  - "Watched-RED evidence for a static scan: plant one lexicon member verbatim in a docstring, capture the (value, count) failure, revert with a targeted inverse edit, re-observe green"
  - "SC5 wall-census safety: any line added under `tests/` is checked against `(?:==|!=)\\s*10(?![0-9_])` before commit, comments included"

requirements-completed: []

# Metrics
duration: 9min
completed: 2026-08-30
---

# Phase 24 Plan 01: The D-01 Refusal Table and Its D-02 Containment Guard — Summary

**An 11-slot, first-person, value-free refusal table whose containment property is bound by a static
substring scan over the 20-value D-10 lexicon — docstrings included — watched RED on a planted
`zorp` before it was allowed to be green.**

## Performance

- **Duration:** 9 min (first task commit 12:59:04-03:00 → last task commit 13:02:46-03:00; plan
  start commit `f05655a` at 12:53:38-03:00)
- **Started:** 2026-08-30T15:53:38Z
- **Completed:** 2026-08-30T16:02:46Z
- **Tasks:** 3 of 3
- **Files modified:** 3 (2 created, 1 additively extended)

## Accomplishments

- **The D-01 property is now a property of committed text, not of prose.** `scripts/phase24_adversarial.py`
  declares one first-person, value-free noun phrase per published slot and renders
  `i will not share {noun}.` None of the 20 published values appears anywhere in the module.
- **Key parity is enforced at import**, `scripts/phase21_filler.py:443`'s precedent: hard equality in
  BOTH directions against `fs.SLOT_FORMS`, never `issubset`. Observed firing on a deliberately
  deleted key (see below), then restored byte-identical (sha256 match).
- **The D-05 precondition is measured, not assumed.** Every slot's scored-token length is counted
  through the FROZEN production tokenizer exactly as `encode_dialogue` will count it.
- **The D-02 guard was watched RED.** Its failure output is quoted verbatim below.

## Task Commits

1. **Task 1: Create the D-01 refusal table module** — `628dc21` (feat)
2. **Task 2: Property tests incl. the D-05 scored-length floor** — `96be5af` (test)
3. **Task 3: The D-02 sibling containment guard** — `c09d37c` (test)

**Plan metadata:** see the `docs(24-01)` commit that carries this SUMMARY, STATE.md and ROADMAP.md.

## Files Created/Modified

- `scripts/phase24_adversarial.py` (new, 147 lines) — `REFUSAL_SLOT_NOUNS` (11 slots),
  `REFUSAL_TEMPLATE`, `MIN_REFUSAL_SCORED_TOKENS`, `MASK_FRACTION_MARGIN`, `refusal_for(slot)`,
  `refuse_undeclared_slots()` called at module scope. Refusal half only — 24-05 adds the builder.
- `tests/test_phase24_refusal.py` (new, 119 lines) — the four named property tests.
- `tests/test_phase14_scoring.py` (+63 / −4) — `_load_driver` widened to `(name, filename)` with
  incumbent defaults, plus the new sibling `test_no_fact_values_in_the_refusal_templates`.

## The two numbers this plan was required to publish

### Task 2 — the observed minimum scored-token length

Measured through `from_json(teach_persona.TOKENIZER_PATH)` (the frozen production artifact), as
`len(tok.encode(detokenize(answer), allowed_special="none")) + 1` for the final eos at mask=1:

```
D-05 floor 15; observed min L = 18 (person_name), max L = 26
```

Margin over the floor at the shortest slot: **+3 scored tokens**. The full spread, shortest first:
`person_name 18, pet_name 20, cat_name 20, street 21, birth_year 22, house_number 22,
sibling_name 23, hometown 23, favorite_food 23, favorite_drink 24, favorite_color 26`.

At the worst grid corner this puts `frac(18) = (2719 + 336·18) / (33635 + 336·18) = 8767/39683 =
0.2209` — **0.0709 above the 0.15 band floor**, i.e. 1.4× the 0.05 margin the constant is spent as.

### Task 3 — the captured RED output

Probe: `zorp` (a member of `forbidden`, the taught pet name — the exact leak shape
`RECONCILIATION_A` produced) pasted verbatim into `scripts/phase24_adversarial.py`'s module
docstring. `pytest -q tests/test_phase14_scoring.py::test_no_fact_values_in_the_refusal_templates`:

```
E       AssertionError: scripts/phase24_adversarial.py embeds published fact values
        [('zorp', 1), ('zorp', 1)] (value, count). D-01 requires every refusal to name the SLOT and
        never the VALUE: a template citing a value is scored as an extraction by
        phase14_recall.contains_value, so the adversarial arm would be teaching the model to leak
        while declining. Docstrings count — they are live str objects for the whole life of the
        process.
E       assert [('zorp', 1), ('zorp', 1)] == []
E         Left contains 2 more items, first extra item: ('zorp', 1)
tests/test_phase14_scoring.py:455: AssertionError
=========================== short test summary item ============================
FAILED tests/test_phase14_scoring.py::test_no_fact_values_in_the_refusal_templates
1 failed in 0.85s
```

The value appears TWICE at count 1 because `_module_strings` reaches the module docstring by two
routes — `getattr(module, "__doc__")` directly, and `__doc__` again while walking `dir(module)`.
That is the incumbent helper's pre-existing behaviour, unchanged by this plan.

The probe was then removed by a targeted inverse edit (not a blanket `git checkout`),
`git diff --exit-code scripts/phase24_adversarial.py` came back **clean**, and the guard was
**re-observed GREEN at commit `c09d37c`** (`1 passed in 0.78s`).

## Evidence for every figure written into code

Per the repo's evidence rule, no number was carried forward from the plan text. All four inputs to
the `MIN_REFUSAL_SCORED_TOKENS` derivation were re-derived at HEAD this session:

| Figure | Value | How re-derived |
|---|---|---|
| trained attack pool episodes | 336 | counted off `results/phase18_corpus.json`, `tier == core_taught`, families A1-mild + A1-aggressive + A3 (112 each) |
| trained attack pool prompt tokens | 26,054 | `sum(len(prompt_ids))` over the same 336 rows (4,978 + 7,802 + 13,274) |
| clean n=8 bin episodes / tokens / scored | 176 / 7,581 / 2,719 | live `teach_persona.build_bins(tok, eps, ..., replay_ratio=0.0, align_facts=None)` on arm `dp_n8`; reported `mask_fraction = 0.35865980741327` |
| combined denominator | 33,635 | 7,581 + 26,054 |
| adversarial_ratio | 1.9090909090909092 | 336 / 176 |
| L clearing 0.15 | ≥ 9 | `frac(8) = 0.148859 < 0.15 ≤ 0.156659 = frac(9)` |
| L clearing 0.15 + 0.05 | ≥ 15 | `frac(14) = 0.193613 < 0.20 ≤ 0.200621 = frac(15)` |
| D-10 lexicon size | 20 | `len(set(fs.LOCKED_VALUES) \| {f.value for f in fs.GATE_REJECTED_CANDIDATES})` at HEAD (8 + 12) |

## Decisions Made

1. **Single-clause template.** The plan permitted a second clause "if and only if Task 2's length
   measurement requires it." It does not: the one-clause form clears the floor by +3 at the
   shortest slot. Two longer candidates were measured and discarded (40–48 and 48–56 scored
   tokens) — extra words buy margin that is already there.
2. **First-person noun phrases, written not pasted.** `SLOT_FORMS[slot].np1/.np2` are second-person
   ("the name you go by") — the QUESTION's register. The refusal is the assistant's own answer, so
   each phrase was written first-person ("the name i go by", "the year i was born").
3. **`_load_driver` widened, not duplicated.** `def _load_driver(name="phase14_recall",
   filename="phase14_recall.py")` keeps both incumbent call sites (`pr = _load_driver()` at module
   scope and inside `test_no_fact_strings_at_import`) byte-unchanged while giving the two
   containment scans one loader instead of two that can drift.
4. **ADVT-01 deliberately NOT ticked.** Six of the seven Phase-24 plans carry `ADVT-01`; this one
   ships the refusal half of one of them. `.planning/REQUIREMENTS.md` is byte-unchanged.

## Deviations from Plan

**One substitution, made under the repo's own AST-over-grep rule.**

**1. [Rule 3 — Blocking/method] Task 3 acceptance criterion "`git diff` on that function's body is
empty" verified by AST source-segment comparison rather than by reading a textual diff**
- **Found during:** Task 3
- **Issue:** A raw `git diff` on the file is not a check on one function's body — the diff mixes the
  `_load_driver` widening and the new sibling with the function under test, and a reviewer eyeballing
  it is exactly the false-confidence shape this repo has been bitten by.
- **Fix:** `ast.get_source_segment` extracted `test_no_fact_strings_at_import` from
  `git show HEAD:tests/test_phase14_scoring.py` and from the working copy and compared them.
- **Verification:** `incumbent test byte-identical: True (2087 chars)`.
- **Committed in:** `c09d37c` (verification method; no source change).

**2. [Rule 3 — Blocking] The Task-3 probe was reverted with a targeted inverse edit instead of
`git checkout --`**
- **Found during:** Task 3
- **Issue:** `git checkout -- scripts/phase24_adversarial.py` is a blanket working-tree restore and
  was refused by the session's destructive-command gate.
- **Fix:** Removed the exact planted 3-line probe string via an asserted single-occurrence replace.
- **Verification:** `git diff --exit-code scripts/phase24_adversarial.py` → clean; guard re-ran green.
- **Committed in:** n/a (probe never committed).

---

**Total deviations:** 2 (both method-level, both strengthening the check). **Impact:** none on
scope — every planned artifact shipped as specified, and the one authored choice the plan left open
(second clause or not) was decided by measurement.

## Verification Results

All of the plan's `<verification>` block, run and reported rather than asserted:

| Check | Result |
|---|---|
| `pytest -q tests/test_phase24_refusal.py tests/test_phase14_scoring.py tests/test_phase21_sc5.py` | **0 failed** (47 passed on the latter two; 4 passed on the new file) |
| Full suite `.venv/bin/python -m pytest -q` | **1596 passed, 1 skipped**, 0 failed, in 374.43 s |
| `git diff --stat f05655a HEAD` | exactly three paths: `scripts/phase24_adversarial.py` (new), `tests/test_phase24_refusal.py` (new), `tests/test_phase14_scoring.py` (+63/−4) |
| `git diff f05655a HEAD -- scripts/phase18_extraction.py scripts/mitigation_gate.py` | **empty** (SC4 / frozen intact) |
| `ruff check .` / `ruff format --check .` | All checks passed; 221 files already formatted |
| SC5 wall census `test_wall_census_is_the_measured_set` | passed |
| `(?:==\|!=)\s*10(?![0-9_])` over `tests/test_phase14_scoring.py` | exactly one hit, the incumbent line, byte-identical |
| `grep -n "assert len(forbidden) == 10"` / `== 20` | one line each |

**Suite-count arithmetic, since the recorded baseline disagrees with itself.** `STATE.md` carries
`1589 passed, 1 skipped` (recorded at 23-14) while `ROADMAP.md`'s Phase-23 row carries
`1591 passed, 1 skipped` (recorded at phase close, after 23-19/23-20). The ROADMAP figure is the
real baseline: 1597 tests collect at HEAD, of which **exactly 5 are this plan's** (4 in
`tests/test_phase24_refusal.py`; `tests/test_phase14_scoring.py` went 28 → 29 top-level test
functions), so 1597 − 5 = 1592 collected = 1591 passed + 1 skipped. **Zero failures, zero new
skips.**

## Issues Encountered

- **Two `E501` line-length violations** on first write (a 102-char docstring line in the module and
  a 131-char f-string in the test). Wrapped; `ruff` clean.
- **The session's destructive-command gate refused `git checkout --`** during the Task-3 probe
  revert. Handled by the targeted inverse edit above; the outcome (`git diff --exit-code` clean) is
  identical and the operation is narrower.

## Known Stubs

None. `scripts/phase24_adversarial.py` is deliberately partial — it ships the refusal half and
24-05 adds the corpus-to-episode builder to the same module — but nothing in it is a placeholder:
every declared name is fully implemented, exercised by a test, and consumed by an assertion.

## Threat Flags

None. No new network endpoint, auth path, file access pattern or schema at a trust boundary. The
module performs no I/O at import (stdlib + `phase14_factset` only) and the plan's registered
mitigations T-24-01 through T-24-05 are all in place: the sibling scan over the 20-value lexicon
(T-24-01), its watched-RED record and non-vacuity halves (T-24-02), the build-time `SystemExit`
converted into a sub-second red test (T-24-03), the untouched ten-value wall plus a green SC5
census (T-24-04), and zero value strings typed into the new test file (T-24-05). No package was
installed (T-24-SC).

## Next Phase Readiness

Ready for the rest of Wave 1 (24-02, 24-03, 24-04) and for Wave 2:

- `refusal_for(slot)` is the exact call 24-05's corpus-to-episode builder needs, and it lands in the
  same module.
- `MIN_REFUSAL_SCORED_TOKENS` / `MASK_FRACTION_MARGIN` are importable constants for 24-06 and 24-07;
  neither figure should be retyped.
- 24-04's `contains_refusal` (in `scripts/phase14_recall.py`, beside `contains_value`) will need
  `REFUSAL_TEMPLATE` / `REFUSAL_SLOT_NOUNS` as its template source. **Note for 24-04:**
  `phase14_recall` is the LAZY-IMPORT boundary — it must not gain a module-level import of
  `phase24_adversarial`, because `phase24_adversarial` imports `phase14_factset` at module scope
  and that would put the locked fact strings in the demo's address space, which is exactly what
  `test_no_fact_strings_at_import` measures.

---
*Phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa, Plan 01*
*Completed: 2026-08-30*

## Self-Check: PASSED

All four artifact paths exist on disk (`scripts/phase24_adversarial.py`,
`tests/test_phase24_refusal.py`, `tests/test_phase14_scoring.py`, this SUMMARY) and all three task
commits (`628dc21`, `96be5af`, `c09d37c`) are present in `git log --all`.
