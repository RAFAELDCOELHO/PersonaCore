---
phase: 17-multi-persona-isolation-matrix
plan: 05
subsystem: persona-preflight
tags: [iso-01, d-16, th-17-14, th-17-42, th-17-15, cr-02, f-07, f-13]
requires:
  - scripts/phase14_factset_gate.py (probe_guessability at its D-16 PUBLIC entry point, plus
    PROBE_SEEDS / TEMPERATURE / TOP_P / PROBE_MAX_NEW_TOKENS / STOP_IDS / SEED — imported, never
    copied)
  - scripts/phase14_factset.py (token_census, exact_match_clean — the objective half of the rule)
  - scripts/phase14_recall.py (CONVBASE_SLIM, SEED — the un-adapted build shape at :522-528)
  - scripts/phase16_persistence.py (resolve_forbid — the ONE runtime seam for the mask + its sha256)
  - scripts/phase17_isolation.py (held_out_by_slot — the fixture regrouped 13 x 8)
  - scripts/phase17_persona_facts.py (PERSONA_FACTS, VALUE_TOKEN_CENSUS,
    assert_material_passes_filters)
  - scripts/phase17_personas.py (CORE_SLOTS, PERSONAS, QUESTIONS_PER_SLOT, MAX_VALUE_TOKENS) —
    IMPORTED, byte-untouched
  - scripts/_verdict.py (recorded_verdict — the ONE anchored section read)
  - personacore.checkpoint.load_slim (weights_only=True, the restricted unpickler)
provides:
  - scripts/phase17_persona_gate.py (the ISO-01 GPU pre-flight; build_unadapted_base,
    assert_report_not_clobbered, main)
  - 9 new CPU-only tests in tests/test_phase17_personas.py (21 total)
  - the abort-names-the-file property of teach_persona._require_go_verdict
affects:
  - plan 17-07 (runs this driver, commits results/phase17_personas_report.md, records the verdict)
  - plan 17-06 (calls teach_persona._require_go_verdict with the Phase 17 report before training)
  - plan 17-09 (the STAT-05 ordering guard stops being vacuous once 17-07 commits the report)
tech-stack:
  added: []
  patterns:
    - generation cached per QUESTION, verdicts derived per VALUE through one code path
    - clobber-guard boilerplate lives ABOVE the verdict section, never inside it
    - operator-facing aborts name the artifact, not the phase that first wrote the function
    - structural guards asserted FOUND before their contents are asserted
key-files:
  created:
    - scripts/phase17_persona_gate.py
  modified:
    - tests/test_phase17_personas.py
    - scripts/teach_persona.py
decisions:
  - the driver has no literal `import torch`; torch arrives transitively and the MPS-fallback env
    set is ordered against that, measured
  - `## Verdict` holds the verdict and NOTHING else — instructions live in `## Recording The
    Verdict` above it, or the clobber guard stays disarmed forever after a human writes GO
  - probe_guessability is called ONCE PER SLOT and all 24 verdicts derive from the cache through
    exact_match_clean, so no value is judged by a different code path than its slot-mates
  - _require_go_verdict's aborts now name the report path — it is a multi-phase gate now
metrics:
  duration: 41min
  tasks: 2
  files: 3
  completed: 2026-08-14
---

# Phase 17 Plan 05: ISO-01 Pre-Flight Gate Summary

The instrument that measures whether the **un-adapted base** can already produce any of the 24
minted persona values is committed, reaches its base through the restricted unpickler with no
adapter of any kind attached, imports Phase 14's guessability probe rather than copying it, and
cannot overwrite a recorded verdict — with the un-adapted-base rule pinned by a structural scan
that was watched failing two different ways.

## What Was Built

### Task 1 — `scripts/phase17_persona_gate.py` (commit `608a315`, 539 lines)

`build_unadapted_base(device)` is `phase14_recall.py:522-528` and stops exactly where the injection
begins: `load_slim(CONVBASE_SLIM)` -> `ModelConfig(**ckpt["model_config"])` -> `GPT` ->
`load_state_dict` -> `.to(device)` -> `.eval()`, returning `(model, model_cfg, ckpt)`. It is a named
function rather than an inline block so the Task 2 scan can assert on it without a 278 MB
checkpoint.

`main()`, in the order a run actually costs money:

1. `assert_report_not_clobbered()` — **first**, before anything expensive.
2. `preflight_device(strict=True)`, `RuntimeConfig().device`, `seed_everything(recall.SEED)`.
3. The frozen tokenizer; `forbid_ids` built ONCE via `phase16_persistence.resolve_forbid`, recorded
   by sha256, then `.to(device)`.
4. The fixture regrouped by slot (`phase17_isolation.held_out_by_slot`) and all four minting filters
   through `assert_material_passes_filters` — **on CPU, before the model load**.
5. The census: transcribed literal beside the live re-measurement.
6. `build_unadapted_base(device)`. No adapter.
7. `probe_guessability` per slot, cached per question, `start_index=len(probe_cache)`.
8. The report, ending `## Verdict` / `PENDING`.

### Task 2 — 9 tests in `tests/test_phase17_personas.py` (commit `ea7d1d9`)

| test | what it pins |
|---|---|
| `test_the_probe_runs_on_an_unadapted_base` | no call to the four adapter routes anywhere in the driver; `build_unadapted_base` FOUND, then its `load_slim` call |
| `test_verdict_blocks` (PENDING, STOP) | teaching refuses, the message names the word AND the file |
| `test_verdict_blocks_a_report_with_no_verdict_section` | a missing section is refused, never an implicit pass |
| `test_verdict_clears_on_go_and_adapt` | the positive control — without it the suite passes against a gate that refuses everything |
| `test_verdict_read_is_anchored_on_the_section` | CR-02, with the naive tail kept as a tripwire |
| `test_gate_report_clobber_guard_bites` | raising case + PENDING positive control + `--force` |
| `test_gate_report_renders_and_does_not_read_as_recorded` | the writer end to end, and the round-trip |

21 tests in the file, **0.76 s**, no GPU, no checkpoint.

## The Defect This Plan Found In Its Own Report

The first draft put the "how to record the verdict" instructions **inside** the `## Verdict`
section. `assert_report_not_clobbered` reads the verdict SECTION — heading to end of file — and
passes when `"PENDING" in recorded`. Those instructions contained the sentence *"refuses on STOP and
on PENDING alike"*.

So after a human replaced the first line with `GO`, the literal `PENDING` would still have been
inside the recorded verdict, the guard would have concluded nothing was recorded, and the next run
would have silently destroyed the blocking human judgment ROADMAP SC2 exists to collect. That is
TH-17-15 defeated by the wording of the artifact it protects — the CR-02 failure class arriving one
layer further out than the regex fix reached.

Fixed structurally, not by careful wording: the instructions moved to `## Recording The Verdict`
ABOVE the section, so `## Verdict` holds the verdict and nothing else. Measured both ways in
`test_gate_report_renders_and_does_not_read_as_recorded` — the writer's own output re-drives with no
`--force`, and the same file with `GO` written in raises.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] `_require_go_verdict`'s aborts named no file**

- **Found during:** Task 2, writing the plan's own assertion *"Assert the message names the file"*.
- **Issue:** the function takes a `report_path`, and 17-06 will call it with
  `results/phase17_personas_report.md`. But two of its three abort branches named no file, and one
  said **"no '## Verdict' section in the fact-set report"** — Phase 14's artifact name, hardcoded. A
  Phase 17 operator reading that abort would go edit `results/phase14_factset_report.md`: the wrong
  file, and one that **already carries a recorded GO**, so the "fix" would look like it worked.
- **Fix:** both branches now interpolate `report_path`. Message text only — the verdict word and the
  `phase14_factset_gate.py` suggestion in the missing-file branch are unchanged, so both committed
  Phase 14 assertions (`test_require_go_verdict_blocks`, `test_require_go_verdict_missing_report`)
  still pass. 38/38 in `tests/test_phase14_teaching.py`.
- **Files modified:** `scripts/teach_persona.py`
- **Commit:** `a6b85f5`

**2. [Rule 2 - Missing critical functionality] the report writer had no check at all**

- **Found during:** Task 1, before committing.
- **Issue:** the plan scopes the RUN to 17-07, so `main()`'s ~150-line renderer would first execute
  at the end of a GPU run. A `KeyError` in one table row costs that run and leaves 17-07 with no
  artifact to judge. The precedent for closing this already exists in the repo:
  `tests/test_phase14_scoring.py:733` does exactly this for `write_recall_report`, for exactly this
  reason.
- **Fix:** `test_gate_report_renders_and_does_not_read_as_recorded` stubs only `preflight_device`,
  `RuntimeConfig`, `build_unadapted_base` and `probe_guessability`; the tokenizer, the fixture, the
  four filters and the census are REAL, so the writer is exercised on the committed material. It is
  also what caught the verdict-section defect above.
- **Files modified:** `tests/test_phase17_personas.py`
- **Commit:** `ea7d1d9`

### Interpretations recorded

**3. Two acceptance criteria are unsatisfiable as literally written; both were honoured in substance
and the divergence is measured, not asserted.**

- **`grep -c "load_adapted_model"` must return 0, but the plan also mandates a docstring naming
  it.** The same conflict covers `inject_lora`, `load_adapter_weights`, `load_adapter` and
  `persona_adapter` — the plan asks for reasoning that spells names its own greps forbid. The
  mechanical criterion won: `build_unadapted_base`'s docstring carries the **whole** argument
  (defaults its adapter path, raises when absent, wraps every allowlisted projection, copies the
  tensors in, no un-adapted return path, taught models under-report guessability, the gate comes
  back flatteringly clean) with `phase14_recall.py:496` and the four line numbers `:516`, `:530`,
  `:557`, `:565` as the pointers instead of the identifiers. A reader lands in the same place; a
  rename cannot make the docstring lie. All five greps return **0**. The `weights_only=False`
  criterion had the identical shape and was resolved identically.
- **`PYTORCH_ENABLE_MPS_FALLBACK` must precede the first `import torch` line — there is no such
  line.** This driver needs no torch symbol: `load_slim` does the load, `collect` is already
  `@torch.no_grad()`, `preflight_device` returns the torch version, and the mask moves by method
  call. An unused `import torch` would fail the `ruff` criterion two lines down. Measured in a fresh
  interpreter: `torch in sys.modules` is `False` before the module body and `True` after, the env
  set is at **line 56**, the first torch-importing sibling at **line 66**, and
  `PYTORCH_ENABLE_MPS_FALLBACK == "1"` afterwards. The ordering is therefore load-bearing and
  correct; it is enforced against the transitive import rather than a literal line, and the comment
  says so.

**4. `probe_guessability` is called once per SLOT, and all 24 verdicts come from the cache.**

F-07's cache and the instrument's `(value, questions)` signature pull in opposite directions: 24
calls x 13 questions is 1,248 completions, and the cache exists to make it 416. The driver calls the
instrument once per slot on that slot's not-yet-cached questions (the first persona's value is the
`anchor`), then derives every one of the 24 verdicts from the cache through
`fs.exact_match_clean` — the same function the instrument applies internally. Deriving all 24 the
same way, rather than reading the returned field for 8 anchors and computing it for 16, is what
keeps a value from being judged by a different code path than its slot-mates.

The `anchor`'s returned `clean` is not discarded: it is `_prove`d equal to the cache-derived answer.
That is not a restatement — it checks that reading completions back OUT of the cache reproduces the
text set the instrument judged, so a flattening that dropped the greedy draw would go loud instead
of silently narrowing all 24 verdicts.

**5. Two runtime `_prove`s were added that no imported guard can perform.**

- `MAX_VALUE_TOKENS` against the **live** count. `filter_token_budget` reads the transcribed
  literal, so it structurally cannot see a live count that has drifted past the ceiling.
- `recall.SEED == instrument.SEED`. `seed_everything` takes the first and the per-probe generator
  takes the second; the report states ONE seed, so a divergence would make the recorded provenance
  describe a stream nobody drew from.

A third proves `len(probe_cache) == 13 * 8`, which is what makes the report's 416-completion claim a
measurement rather than an assertion.

## Deliberate-RED Proofs (guards watched failing)

| Guard | Mutation | Observed |
|---|---|---|
| `test_the_probe_runs_on_an_unadapted_base` (adapter half) | `build_unadapted_base` body replaced with a call to `phase14_recall`'s adapted loader | **FAIL** — `AssertionError: scripts/phase17_persona_gate.py calls ['load_adapted_model']...` |
| `test_the_probe_runs_on_an_unadapted_base` (found-first half) | `def build_unadapted_base` renamed to `def build_base` | **FAIL** — `expected exactly one build_unadapted_base ... found 0` / `assert 0 == 1` |
| `test_gate_report_renders_and_does_not_read_as_recorded` (round-trip half) | instructions left inside `## Verdict` (the first draft) | **FAIL** in the scratch smoke — the guard stayed silent after `GO` was recorded; fixed by moving the section |

Both mutations were made in the working tree and reverted; `git diff HEAD -- scripts/phase17_persona_gate.py`
is empty after each, so the committed file is byte-identical to `608a315`.

## Verification

| Check | Result |
|---|---|
| `pytest -q tests/test_phase17_personas.py -x` | **21 passed** in 0.76s (>= 14 required) |
| `pytest -q tests/test_phase17_personas.py -k "verdict or unadapted"` | **7 passed** (>= 4 required) |
| `pytest -q` (full suite) | **629 passed, 1 skipped** in 121.36s (baseline 620/1 + 9 new; floor 579) |
| `pytest -q tests/test_phase14_teaching.py` | **38 passed** — the message change breaks no Phase 14 assertion |
| `pytest -q tests/test_phase17_stats.py tests/test_phase17_scoring.py tests/test_phase16_prereg.py` | **passed** — the new driver entered the `phase17_*.py` glob and cleared ISO-07 / STAT-04 / STAT-06 on arrival |
| module load runs nothing | `loaded, nothing ran` — no model, no tokenizer, no checkpoint |
| `grep -c` on `load_adapted_model` / `inject_lora\|load_adapter_weights\|load_adapter\b\|persona_adapter` / `weights_only=False` / `split("## Verdict")` / `def probe_guessability` | **0 / 0 / 0 / 0 / 0** |
| `grep -n "load_slim"` inside `build_unadapted_base` | present (`:194`) |
| `assert_report_not_clobbered` signature | zero-arg, module-level |
| `.venv/bin/ruff check` + `format --check` on `scripts/` + `tests/` | clean (116 files) |
| `git status --short results/` | **empty** — this plan writes no report |
| `git diff --diff-filter=D HEAD~3 HEAD` | empty — no deletions |
| report renderer (scratch, stubbed model + probe) | 7 sections present, 24 `clean=` flags, 747 lines, verdict section == the PENDING line alone |
| `make lint` | **red — pre-existing**, see below |

## Deferred Issues

`make lint` still fails from **DEF-17-01** (this phase's `deferred-items.md`, pre-existing to the
phase): `Makefile:16` runs bare `ruff`, which resolves on this box to a pyenv shim holding **ruff
0.1.15** against the project's `ruff~=0.15` pin. Neither file this plan wrote is among the files it
reports. `.venv/bin/ruff` (0.15.16 — the version CI installs and runs) is clean on all three.
Recorded resolution is a quick task changing `Makefile:16` to `python -m ruff`.

## Known Stubs

None. Every function this plan commits is complete and exercised; the report writer is exercised end
to end on the committed material with only the model and the probe stubbed.

**ISO-01 is deliberately NOT marked complete**, for the third plan running, and that is a planned
property of the wave ordering rather than a stub: the guessability measurement needs
`convbase_slim.pt` on MPS and cannot enter a CPU-only suite, and SC2's GO/ADAPT verdict is a
blocking human decision. **17-07 runs the measurement and records the verdict, and 17-07 marks the
requirement.** 17-03 avoided this over-claim; this plan avoids it too.

## Handover Notes

1. **17-07 owns the first `results/phase17_*` artifact.** The moment it commits
   `results/phase17_personas_report.md`, `scripts/phase17_personas.py` becomes permanently
   uneditable — `tests/test_phase16_prereg.py` proves via `--diff-filter=A` that every commit
   touching the pre-registration is an ancestor of that add. The ADAPT branch therefore edits
   `scripts/phase17_persona_facts.py` only. This plan touched neither file.
2. **17-07 and 17-09 must assert `checked > 0`** in the ordering guard. Until 17-07's commit the
   Phase 17 half of that guard matches an empty set and is vacuous; carried forward from 17-01 and
   still open.
3. **The verdict section is the verdict and nothing else.** When recording GO or ADAPT, replace the
   `PENDING` line — do not append below it and do not move the `## Recording The Verdict` text under
   the heading. Both would put prose into the recorded verdict, and
   `test_gate_report_renders_and_does_not_read_as_recorded` is the only thing standing between that
   and a disarmed clobber guard.
4. **Do not pass `--force` at 17-07.** If the driver refuses, a verdict has been recorded and the
   refusal is correct; escalate. This gate has `--force` (unlike Phase 16's ladder, which
   deliberately has none) only because an interrupted GPU run must be re-drivable — the PENDING
   round-trip is what makes that possible without it.
5. **Expected cost:** 8 slots x 13 questions x 4 completions = **416 generations**, ~2-3 min on MPS.
   The per-slot log line prints the fresh-question count; anything other than `13` on all eight
   slots means the fixture's slots share questions and the 416 claim is wrong (a `_prove` catches
   the total).
6. `MINTING_SCREEN_RECORD` is a transcription of 17-03's measured rejections. If ADAPT replaces a
   value, that table describes the ORIGINAL minting round — extend it, do not silently rewrite it.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema change at a trust boundary.
`TH-17-14` is mitigated (the base reaches the process only through `load_slim` at
`weights_only=True`; zero direct `torch.load`, and the criterion greps return 0);
`TH-17-42` is mitigated (no adapter route is called anywhere in the driver, watched RED twice);
`TH-17-15` is mitigated (`assert_report_not_clobbered` runs FIRST, reads the anchored section, and
the report's own wording no longer disarms it);
`TH-17-16` is mitigated (`recorded_verdict` imported; the naive tail lives only in the test);
`TH-17-17` is mitigated (`probe_guessability` imported, no local definition);
`TH-17-SC` holds — zero packages installed, `pyproject.toml` byte-identical across all three
commits, and `test_no_new_dependencies` passes over the widened `phase17_*.py` glob.

## Self-Check: PASSED

Files:

- FOUND: `/Users/juliorcoelho/PersonaCore/scripts/phase17_persona_gate.py` (539 lines)
- FOUND: `/Users/juliorcoelho/PersonaCore/tests/test_phase17_personas.py` (21 tests)
- FOUND: `/Users/juliorcoelho/PersonaCore/scripts/teach_persona.py` (modified)
- ABSENT (correctly): `results/phase17_personas_report.md` — 17-07 owns the run

Commits:

- FOUND: `608a315` feat(17-05): ISO-01 pre-flight gate on the un-adapted base
- FOUND: `a6b85f5` fix(17-05): name the report path in every _require_go_verdict abort
- FOUND: `ea7d1d9` test(17-05): pin the un-adapted base and the blocking verdict
