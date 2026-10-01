# Phase 35: v6.0 Pre-Registration and the Research It Rests On - Pattern Map

**Mapped:** 2026-10-01
**Files analyzed:** 3 new, 0 modified (plus 1 file that must stay unmodified: `tests/test_phase25_venue.py`)
**Analogs found:** 3 / 3. Two are exact; the research note has only a partial analog.

D-14..D-17 override the research everywhere it disagrees. No entry carries `proposer` or
`adopted_by`. Each entry is exactly `{value, derivation, kind, source}`.

Every path and constant below was resolved from live code or a `.venv` 3.11 probe on 2026-10-01,
not from plan prose.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `scripts/phase35_prereg.py` (NEW) | config / rule module (frozen pre-registration) | transform (pure rules + read-at-use of committed JSON records; writes nothing) | `scripts/phase29_prereg.py`; slot→fill shape from `scripts/phase25_prereg.py:496` + `scripts/phase26_prereg.py:79-107`; basic composition from `scripts/phase25_epsilon.py:271-294` | exact |
| `tests/test_phase35_prereg.py` (NEW) | test (git ancestry + AST census + unit) | batch (reads git history and tracked files) | `tests/test_phase29_prereg.py` | exact |
| `.planning/research/V6-PREREG-09.md` (NEW) | doc (research note with verified citations) | n/a | `.planning/research/PITFALLS.md` (citation register only) | partial |
| `tests/test_phase25_venue.py` | test (skip-count pin) | — | — | **must NOT change** (the new test adds zero skips) |

Live-tree facts (measured):
- No `scripts/phase3[5-9]*`, `scripts/phase4*` or `tests/test_phase3[5-9]*` file exists.
- `.planning/research/` holds only ARCHITECTURE/FEATURES/PITFALLS/STACK/SUMMARY.
- Tags `v4.0` and `v5.0` exist.
- `git log --diff-filter=A -- scripts/phase23_run.py` returns `5303819`.

## Pattern Assignments

### `scripts/phase35_prereg.py` (rule module, transform)

**Analog:** `scripts/phase29_prereg.py` (662 lines)

**Docstring register** (`phase29_prereg.py:1-43`). Use these headings:
- WHAT THIS FREEZES
- ANCESTRY-GUARDED, naming the test function and `scripts/_addendum.py` as the only correction route
- CPU-ONLY AT IMPORT, which must name every lazy import and every transitive load honestly
- Threats mitigated

The prose may discuss `SEED_LADDER`, `torch` and "selected by THE USER, verbatim". Every census
must be AST-based so the docstring is excluded (memory: grep criteria measure prose).

**sys.path + torch-free top-level imports** (`phase29_prereg.py:45-60`):
```python
import math
import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import mitigation_budget  # noqa: E402  (needs the sys.path insert above)
import mitigation_gate  # noqa: E402  (same)
```
Import probe of 2026-10-01: `'torch' in sys.modules` is False after importing each module below.

| Module | Top-level import? | Why |
|---|---|---|
| `mitigation_gate`, `mitigation_budget`, `mitigation_unit`, `erasure_gate` | OK | stdlib only |
| `phase25_epsilon` | OK | loads `personacore.privacy.accountant`, which is torch-free; state the load in the docstring, as `phase29_prereg.py:27-31` does |
| `phase25_prereg`, `phase26_prereg` | OK | torch-free |
| `phase19_floor` | OK | torch-free; source of the noise-floor record path |
| `phase19_erasure`, `phase18_extraction` | **LAZY ONLY** | `import torch` at module level |
| `phase23_run` | **LAZY ONLY** | `phase23_run.py:105 import teach_persona as tp` (torch) |
| `phase26_canary` | **LAZY ONLY** | `phase26_canary.py:66 INSTRUMENT_GIT_SHA = git_sha()` runs a subprocess at import |

**Date + property certified** (`phase29_prereg.py:66-68`):
```python
# At this commit no `results/phase3[0-4]_*` file existed, tracked or untracked.
COMMITTED = "2026-09-24"
RECORDS_AT_COMMIT = 0
```
For Phase 35 the comment covers `results/phase3[6-9]_*` and `results/phase4[0-5]_*`. The test
asserts `RECORDS_AT_COMMIT == 0` (`test_phase29_prereg.py:287`).

**`_prove` / `_prove_count`** (`phase29_prereg.py:71-83`). Copy these with the prefix changed to
`[phase35_prereg]`. Each prereg owns its own copy; `phase26_prereg.py:72-75` does the same.
```python
def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase29_prereg] {message}")


def _prove_count(name, value):
    """``prove_reproduction``'s register: an ``int`` that is not a ``bool``, or a refusal."""
    _prove(
        isinstance(value, int) and not isinstance(value, bool),
        f"{name} is {value!r}, which is not an int (bool excluded). This formula takes COUNTS; a "
        "float came out of arithmetic and a bool would compare True against 1",
    )
```
Use these for D-11's input validation (`0 <= v <= r <= m`, ints only), in place of Appendix D's
`assert`s.

**By-reference bindings** (`phase29_prereg.py:90-93`, and `:315-334` for pins that are ints or
floats):
```python
RATIO_GRID = mitigation_budget.ADVERSARIAL_RATIO_GRID
F_Y = mitigation_gate.F_Y
GATE_ROUTE = phase20_gate_coverage.corrected_point_verdict
```
Phase 35 binds these by reference. The line numbers are where each constant lives in the
source module:

| Phase 35 needs | Bind to |
|---|---|
| `F_Y` | `mitigation_gate.F_Y` (`mitigation_gate.py:203`, `0.7  # PREFERENCE, not a derivation`) |
| `F_C` | `mitigation_gate.F_C` (`:217`) |
| the D-01 band | `mitigation_gate.dialogue_gap_band` (`:526`, `def dialogue_gap_band(*, control_gap, gap_noise_floor)`) |
| δ | `mitigation_unit.DELTA` (`mitigation_unit.py:171`, `1e-5`) |
| basic composition | `phase25_epsilon.curve_total` (`:271`) |
| the RECIPE-02 flag | `phase25_epsilon.SELECTION_ACCOUNTED` (`:68`, `False`) |
| AUDIT-03 wording | `phase26_prereg.CEILING_CLAUSE` (`:288`) |
| the RECIPE-04 baseline | `mitigation_budget.STEP_BUDGET` (`:508`, `200`) |
| σ values | members of `mitigation_budget.SIGMA_LADDER` (`:770`) |
| K = 16 / 48 | `mitigation_budget.CURVE_K` (`:425`) / `FULL_FIDELITY_K` (`:473`) |

`F_Y`, `F_C` and `DELTA` are floats, so `is` is vacuous on them. The test must check the AST
binding shape (see the test section).

**Single results-path tuple + DERIVED pathspecs** (`phase29_prereg.py:148-161`):
```python
V5_RESULT_PATHS = (
    "results/phase30_calibration.json",  # ARECIPE-02
    ...
    "results/phase33_*",  # RELRN-06..09 legs
    "results/phase34_*",  # RPT-04
)

# DERIVED, not typed: exactly results/phase30_* .. results/phase34_*.
ARTIFACT_PATHSPECS = tuple(sorted({p.split("_", 1)[0] + "_*" for p in V5_RESULT_PATHS}))
```
For Phase 35:
- Name the tuple `V6_RESULT_PATHS`. It needs at least one entry per phase 36..45, so the derived
  set is exactly `results/phase36_*` … `results/phase45_*`.
- Use concrete names where a slot reads an input record and phase globs elsewhere.
- Every slot `input_records` entry must `fnmatch` some `V6_RESULT_PATHS` entry.

**Lazy import inside a function** (`phase29_prereg.py:171-182`):
```python
def replay_windows(n_facts):
    """Replay WINDOWS for ``n_facts``: teach_persona.py's DP call-site expression, by call."""
    import teach_persona  # torch at import — lazy, so this module stays CPU-only

    _prove_count("n_facts", n_facts)
    ...
```
This is the shape for four functions:

| Function | Lazy import | Returns |
|---|---|---|
| `seed_list()` | `phase23_run` | `phase23_run.SEED_LADDER` by identity (D-05) |
| `e1_targets()` | `phase19_erasure` | the rows of `TARGET_RANKING` (`phase19_erasure.py:604`) with `successes == n_questions`; field order from `TARGET_RANKING_FIELDS` (`:389`) = `("slot", "successes", "n_questions", "rate", "exposure_ans1_mean_nll")` |
| `audit02_cut()` | `phase26_canary` | min `epsilon_upper` over the points with `epsilon_upper >= auditor_ceiling`, read from `phase26_canary.RECORD` (`phase26_canary.py:68`, `_ROOT / "results" / "phase26_canary.json"`) |
| the R1a re-derivation | `phase19_erasure` | reads the record at `phase19_erasure.arm_record_path("erased")` (`:2560`, `results/phase19_arm_erased.json`) |

Code sketches for all four: RESEARCH §Code Examples 1–3.

**Record paths. Resolve from module constants, never by typing them:**

| Record | Constant | Fields used (measured) |
|---|---|---|
| `results/phase26_canary.json` | `phase26_canary.RECORD` (lazy) | `auditor_ceiling` = 2.7858978325772576; `points.*.epsilon_upper`; 11 of 15 at or above the ceiling; min = 3.7965357228934966 |
| `results/phase19_arm_erased.json` | `phase19_erasure.arm_record_path("erased")` (lazy) | `len(config.ablated_components)` = 78. **`config.k` = 48 is the attack budget, a trap.** Destroyed % = `(1 - g1/g0)*100`, with `g0 = pre_erasure.dialogue_ppl.adapter_on - pre_erasure.dialogue_ppl.adapter_off` and `g1 = dialogue_ppl.adapter_on - dialogue_ppl.adapter_off`, = 77.6370113463966 exactly |
| `results/phase19_noise_floors.json` | `phase19_floor.EVIDENCE_ARTIFACT["NONTARGET_NOISE_FLOOR"]` (`phase19_floor.py:172-176`, torch-free) | `nontarget_noise_floor.margin_at_gate` = 0.2962962962962963 (D-16) |
| 0/27 and 7/7 | not in any record | `results/phase19_erasure_report.md:17` ("post-erasure: 0/27 questions") and `:146` ("all seven gated non-targets exceed the (b) margin…"). These become the `source` of asserted R1a values. `per_fact.cand_dog_zorp` in the record reads 0/14 (defect C). Do not re-derive 0/27 here; Phase 37 owns that. |

**Structured dict register** (`phase29_prereg.py:274-307`, `NAMED_LIMITATIONS`). This is the model
for `ENTRIES`: a module-level dict of dicts with fixed keys, where the test asserts the key set
exactly (`test_phase29_prereg.py:612`: `assert set(entry) == {...}`). For Phase 35 every entry
has keys exactly `{"value", "derivation", "kind", "source"}`, and `kind` ∈ {`derived`,
`preference`}.

**Reservation → fill by reference** (the slot precedent).

The reservation is `scripts/phase25_prereg.py:496-540`, a dict of rule strings reserved for a
later phase:
```python
CANARY_RESERVATIONS = {
    "committed": COMMITTED,
    "point_records_at_commit": POINT_RECORDS_AT_COMMIT,
    ...
    "audit_target_rule": ( "WHICH point Phase 26 audits, decided here so it cannot be chosen after seeing the data. ..." ),
    ...
}
```
The fill is `scripts/phase26_prereg.py:59-107`. The later prereg binds by reference, names what
it supersedes, owns its own glob, and executes the reserved rule under `_prove`:
```python
SUPERSEDES = (
    "phase25_prereg.CANARY_RESERVATIONS['audit_target_rule']",
    "phase21_filler.GUESSABILITY_WAIVER",
)
ARTIFACT_GLOB = "results/phase26_*"
...
RULE = phase25_prereg.CANARY_RESERVATIONS["audit_target_rule"]
...
def resolve_audit_target(frontier):
    ...
    _prove(result == CONTROL_KEY, "...")
    return result
```
Phase 35 generalizes this shape:
- `SLOTS` holds rule **function objects**, module-level private `_rule_*` defs.
- The only door is `fill(slot, **inputs)`, which `_prove`s that `slot in SLOTS` and then dispatches
  `SLOTS[slot]["rule"]`.
- Owner preregs (`scripts/phase{36..45}_prereg.py`) write `X = phase35_prereg.fill("<slot>", ...)`.

D-02 fixes the four slot fields: name (the dict key), `owner_phase`, `rule`, `input_records`. The
research's extra `binding` and `derivation` keys are optional and at the planner's discretion. If
`binding` is kept, the census uses it; otherwise the census keys on the `fill` call.

Rule requirements:
- `_rule_e2_S` `_prove`s `s <= len(seed_list())`, with the message "STOP and ask Rafael (D-06)".
- `_rule_e3_grid_subset` encodes 4 recipes × σ ∈ {0, 0.5, 1} plus the v4.0 σ=0 control reuse
  condition, verified by SHA-256 (D-17).
- `e1_condition_b_margin` may be locked in the core (D-16), but the slot name must still be
  declared.

The six D-15 slots must all be declared: `e3_recall_threshold`, `e1_condition_b_margin`,
`e1_condition_c_band_inputs`, `e2_noise_floor_estimator`, `e5_rank_moves_and_generation_collapses`
and `e6_decomposition_rule`.

**Basic composition** (`scripts/phase25_epsilon.py:271-294`). Reference it, never re-implement it:
```python
def curve_total(published_point_epsilons, *, delta):
    values = list(published_point_epsilons)
    for index, value in enumerate(values):
        if value is None or not math.isfinite(value):
            raise ValueError(...)
    return math.fsum(values), len(values) * delta
```
Measured: `curve_total([1.5, 2.25, 0.25], delta=mitigation_unit.DELTA)` → `(4.0, 3.0000000000000004e-05)`.
Compare against `3 * 1e-5`, not the literal `3e-05`.

**One-run audit port (D-11).** No analog exists in the repo. Use the stdlib port in RESEARCH
§Code Example 4: `_binom_pmf` via `math.lgamma`, `p_value_one_run`, and a 30-step bisection in
`eps_lower_one_run`. scipy is not installed and must not be added.

**What the module must NOT contain.** Each item is enforced by AST in the test:
- the four target names;
- the seed tuple or its members;
- `3.7965357228934966`, `0.2962962962962963` or `78` as a value that should be read;
- `F_Y` / `F_C` / `K` as literals;
- `assert`;
- a `proposer` or `adopted_by` key anywhere;
- top-level imports of the four lazy modules.

---

### `tests/test_phase35_prereg.py` (test, batch)

**Analog:** `tests/test_phase29_prereg.py` (1093 lines)

**Imports + sys.path** (`test_phase29_prereg.py:19-46`):
```python
import ast
import fnmatch
import json
import pathlib
import re
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import mitigation_budget  # noqa: E402  (scripts/ is not a package)
...
PREREG = "scripts/phase29_prereg.py"
```

**Reuse the helpers. Do not copy them.** The precedent is `tests/test_phase31_budget.py:282`:
```python
from test_phase29_prereg import _assert_frozen_before, _git  # noqa: E402
```
Extend the same import with `_module_targets, _numeric_constants, _planted`, defined at
`test_phase29_prereg.py:426, 437, 526`.

**Import only `_`-prefixed names.** pytest collects any imported `test_*` function a second time.

**Ancestry helper** (`test_phase29_prereg.py:69-106`), used as-is. It:
- refuses a shallow clone;
- takes the earliest add (`adds[-1]`);
- refuses a same-commit prereg/artifact pair;
- runs `merge-base --is-ancestor`;
- counts the pairs it checked and is honest-green with zero tracked files.

**Ancestry test** (`test_phase29_prereg.py:109-117`):
```python
def test_phase29_prereg_is_frozen_before_every_v5_result():
    tracked = sorted(
        {
            path
            for spec in phase29_prereg.ARTIFACT_PATHSPECS
            for path in _git("ls-files", spec).split()
        }
    )
    _assert_frozen_before(PREREG, tracked)
```
**Finding 4 (in-phase inputs).** The Phase 36 budget and the Phase 41 floors are derived from
their own phase's records. Ordering check 4 must subtract each slot's declared `input_records`
before calling `_assert_frozen_before(owner_prereg, ...)`. The per-owner-glob precedent is
`tests/test_phase26_prereg.py:91-92`:
```python
_assert_frozen_before(PREREG, _git("ls-files", phase26_prereg.ARTIFACT_GLOB).split())
```

**Pathspecs derived + disjoint from the previous milestone's tag** (`test_phase29_prereg.py:150-174`):
```python
def test_pathspecs_are_derived_and_cover_results_phase30_to_34():
    p = phase29_prereg
    expected = tuple(f"results/phase3{n}_*" for n in range(5))
    assert p.ARTIFACT_PATHSPECS == expected
    assert p.ARTIFACT_PATHSPECS == tuple(
        sorted({path.split("_", 1)[0] + "_*" for path in p.V5_RESULT_PATHS})
    )
...
    tracked = _git("ls-tree", "-r", "--name-only", "v4.0", "results").split()
    assert tracked, "git ls-tree v4.0 results returned nothing — the disjointness check is blind"
```
For Phase 35, read the disjoint set at the tag **`v5.0`**, which exists locally. Reading HEAD
reddened the phase29 test on its own first record (the dated continuation at `:164-169`).

**`is` identity tests** (`test_phase29_prereg.py:281-287`):
```python
def test_constants_are_by_reference():
    p = phase29_prereg
    assert p.F_Y is mitigation_gate.F_Y
    assert p.RATIO_GRID is mitigation_budget.ADVERSARIAL_RATIO_GRID
    ...
    assert p.RECORDS_AT_COMMIT == 0
```

**AST binding-shape check** for ints and floats, where `is` is vacuous
(`test_phase29_prereg.py:1029-1038`):
```python
def test_d09_pins_are_attribute_references():
    tree = ast.parse((_ROOT / PREREG).read_text(encoding="utf-8"))
    bound = list(_module_targets(tree))
    expected = {name: "phase27_prereg" for name in _D09_PINS} | {"V4_VERDICTS": "mitigation_gate"}
    for name, module in expected.items():
        values = [value for target, value in bound if target == name]
        assert len(values) == 1, (name, len(values))
        value = values[0]
        assert isinstance(value, ast.Attribute) and value.attr == name, name
        assert isinstance(value.value, ast.Name) and value.value.id == module, name
```
Apply it to `F_Y`, `F_C` and `DELTA`. Remember they may sit inside `ENTRIES[...]["value"]`, not
only at module level. If they are bound there, walk the `ENTRIES` dict node in the AST.

**Torch-free subprocess probe** (`test_phase29_prereg.py:290-298`):
```python
def test_the_prereg_imports_without_torch():
    probe = (
        "import sys; sys.path.insert(0, 'scripts'); import phase29_prereg; "
        "print('torch' in sys.modules, 'teach_persona' in sys.modules)"
    )
    out = subprocess.run(
        [sys.executable, "-c", probe], cwd=_ROOT, capture_output=True, text=True, check=True
    )
    assert out.stdout.split() == ["False", "False"], out.stdout
```
Extend the printed tuple to cover `phase19_erasure`, `phase18_extraction`, `phase23_run` and
`phase26_canary`.

**Lazy import inside the test body** (`test_phase29_prereg.py:301-302`, `:1063-1064`):
```python
    import teach_persona  # torch at import — inside the test only
```
Use this for `phase23_run` (seed_ladder test), `phase19_erasure` (e1_targets test) and
`phase26_canary` (audit02 test).

**Planted-copy RED for every AST guard** (`test_phase29_prereg.py:526-586`):
```python
def _planted(tmp_path, source, planted, name):
    """Write the planted copy to tmp_path and read it back; prove the plant changed something."""
    assert planted != source, f"{name}: the plant did not change the source — vacuous"
    copied = tmp_path / name
    copied.write_text(planted, encoding="utf-8")
    return copied.read_text(encoding="utf-8")


def test_ast_gate_retype_guard(tmp_path):
    f_y = mitigation_gate.F_Y
    real = _ROOT / PREREG
    source = real.read_text(encoding="utf-8")
    assert _gate_retype_failures(source, f_y) == []
    ...
    literal = _planted(
        tmp_path, source, source.replace("mitigation_gate.F_Y", repr(f_y), 1), "f_y.py"
    )
    assert any("F_Y literal" in f for f in _gate_retype_failures(literal, f_y))
    assert real.read_text(encoding="utf-8") == source
```
The slot census (checks 1–3: undeclared slot, wrong owner, different rule) must be watched RED the
same way, on planted owner files in `tmp_path`. A real file under `scripts/` would trip the
clean-tree probes.

**Census over a numbered glob** (`test_phase29_prereg.py:589-596`). Use `pathlib.glob` per
number. Never use a shell multi-glob (memory: zsh NOMATCH):
```python
    modules = sorted(p for n in range(29, 35) for p in _SCRIPTS.glob(f"phase{n}_*.py"))
    assert modules, "no scripts/phase29_* .. phase34_* module found — the census is blind"
    ...
    # NON-VACUITY: the matcher fires where the accountant certainly is imported and called.
```
For Phase 35 the census set is `range(36, 46)`. It is **empty today**, so the slot census cannot
use the `assert modules` non-vacuity form. Use planted owner files instead, and have the
real-tree leg be honest-green with zero files.

**`git show` + AST for the D-05 lock.** No direct analog exists. Build it from `_git`
(`test_phase29_prereg.py:52-56`) plus `ast.literal_eval`; see RESEARCH §Code Example 1. Derive the
commit as the last entry of `_git("log", "--diff-filter=A", "--format=%H", "--", "scripts/phase23_run.py").split()`
and assert it starts with `5303819`. The ladder sits at `phase23_run.py:146` today and at line 96
in `5303819`.

**Reads only, never writes** (`test_phase29_prereg.py:16`). The docstring says "Nothing here writes
under results/". Keep that.

**Zero skips.** No `pytest.skip`, `skipif`, `needs_*` or `_MPS_SKIP`. A shallow clone must FAIL via
`_assert_frozen_before`, never skip.

---

### `.planning/research/V6-PREREG-09.md` (doc)

**Analog (partial):** `.planning/research/PITFALLS.md:550` (the Papernot & Steinke mention) and
`:1318` (its link). Only the citation register carries over.

Requirements:
- Write a **new** file. `scripts/phase28_report.py:101,113` reads `.planning/research/SUMMARY.md`
  live, so never edit SUMMARY.md. No code reads any other file in `.planning/research/` (grep,
  2026-10-01).
- Per D-10, every citation carries arXiv ID + version + theorem/algorithm + page. Every claim
  feeding a threshold gets a paraphrase. An inaccessible source reads "não verificado".
- Content: RESEARCH §PREREG-09 (a), covering `2305.08846v1`, Thm 5.2 p. 14, Cor 5.4 pp. 15–16,
  App. D pp. 45–46, PIN 1 at p. 46 and PIN 2 at p. 28. Then §PREREG-09 (b), covering `2110.03620v2`,
  Thm 2 p. 5, Thm 6 p. 7, and hypotheses that fail, giving basic composition with
  `selection_accounted = false`.
- Per D-07 the note holds **no value**. Values live only in the module, so the note points at
  `phase35_prereg` names.

---

## Shared Patterns

### Invariant refusal
**Source:** `scripts/phase29_prereg.py:71-83`. **Apply to:** every rule in `phase35_prereg.py`,
including the S > 5 refusal, slot-name checks, D-11 input checks and the AUDIT-02 premise. Use
`raise SystemExit` via `_prove`, never `assert`. Tests use `pytest.raises(SystemExit)`
(`test_phase29_prereg.py:311-313`).

### By reference, never retyped
**Sources:**
- `phase29_prereg.py:90-93` and `:315-334`;
- `phase26_prereg.py:79-80` (`RULE = phase25_prereg.CANARY_RESERVATIONS["audit_target_rule"]`);
- the anti-pattern D-05 rejects: `scripts/phase27_prereg.py:100-112`
  (`FRESH_SEEDS = (1337, 2024, 1338, 2025, 1339)`, an int copy) together with
  `tests/test_phase27_prereg.py:171`.

**Apply to:** every pin.

### Ancestry freeze
**Source:** `tests/test_phase29_prereg.py:69-117`. **Apply to:** `scripts/phase35_prereg.py`
against the `ARTIFACT_PATHSPECS` derived from `V6_RESULT_PATHS`. Each owner prereg is frozen
against its own `results/phase{NN}_*` minus its declared input records. CI already has
`fetch-depth: 0` (`.github/workflows/ci.yml:28`).

### Literal-census hazards (measured; the planner must design around them)
- **`mitigation_budget.SIGMA_LADDER` = (0.0, 0.5, 0.7, 1.0, …).** σ = 0.5 equals `F_C`, and the
  ladder also contains 0.7 = `F_Y`. A float-literal census for `F_C` would therefore redden a
  typed σ = 0.5 or an E4 `p = 0.5`. Select σ from `SIGMA_LADDER` without typing 0.5 (by index, or
  by a rule over the ladder), and write `p` as `1 / 2`. Alternatively, scope the `F_C`/`F_Y`
  census to the `ENTRIES` subtree and say so.
- **The R1a assertions (k = 78, 0/27, 7/7, 77.6370113463966) are asserted values.** D-01 locks
  them as `value`s. The test re-derives 78 and 77.637… from `results/phase19_arm_erased.json`,
  which is the only re-derivation the record supports. The margin 0.2962962962962963 must be
  **read** from `phase19_noise_floors.json` (D-16), never typed. So any census forbidding
  `0.2962962962962963` must not also forbid the R1a entry's value. Store the margin as a read,
  not a literal.

## Repo-Wide Census Tests the New Files Must Satisfy

Each was read in the test source on 2026-10-01. "Scope" is the file set each census walks.

| # | Census | Location | Scope | Exact constraint on Phase 35 |
|---|---|---|---|---|
| 1 | ISO-06 `inject_lora` register | `tests/test_lora_inject.py:296-304` (`_scanned_files`), `:414-490` | `scripts/*.py` + `src/**/*.py` | `phase35_prereg.py` never calls `inject_lora`. Any call must be in the closed consumer/producer register |
| 2 | Phase-14 call-site census | `tests/test_phase14_scoring.py:563-573`, `:631`, `:744` | `scripts/*.py` + `src` | Never call `build_recall_prompt` or `draw_all` |
| 3 | `os.replace` writers | `tests/test_phase25_driver.py:341-366` | `scripts/*.py` + `src` (AST: `Attribute(value=Name("os"), attr="replace")`) | Must equal `{"phase25_run.py", "phase25_record.py"}`. The module writes nothing and never names `os.replace`, not even lazily |
| 4 | `== 10` wall | `tests/test_phase21_sc5.py:189-197` (`_PATTERNS`), `:258-275` (`_census`) | every `tests/**/*.py` except `test_phase21_sc5.py`, **raw lines including comments and docstrings** | The new test file must contain no match of `(?:==\|!=)\s*10(?![0-9_])`. That also catches `!= 10` and `== 10.0`. Pick other counts, such as the 1000/100/75 pins (which do not match because of the lookahead) |
| 5 | K menu | `scripts/mitigation_gate.py:254` (`K_RUNGS = (48, 24, 16, 8)`), `:917` (`ratchet_k`); tests at `test_phase20_prereg.py:1953-1970` and `test_phase23_budget.py:1256` | any K reaching `ratchet_k` | Any K in a fixture or slot rule is in {8, 16, 24, 48}, never 2 or 4. ERASE-07's K = 16 / 48 should bind `mitigation_budget.CURVE_K` / `FULL_FIDELITY_K` rather than be typed |
| 6 | `mitigation_point_verdict` caller census | `tests/test_phase20_correction.py:1412-1440` | `scripts/**/*.py` + `src` | Never import it from `mitigation_gate`, never call it by name or attribute, never define it |
| 7 | `privacy_n` via the pin | `tests/test_phase21_unit_continuation.py:75-120` | `scripts/*.py` + `src`, both import forms, aliases included | Never reach `mitigation_unit.privacy_n`. Using `mitigation_unit.DELTA` is correct and required |
| 8 | `retention_perplexity` call sites | `tests/test_phase19_erasure.py:1384-1392` | `scripts/*.py` + `src` (`Call` with `func.id == "retention_perplexity"`) | Never call it |
| 9 | `train_never_taught` / `train_arm(` registers | `tests/test_phase23_ctrl.py:79-100` (+ `_TRAIN_ARM_CALL_SITES`) | `scripts/*.py` | Never define or call either |
| 10 | `"descriptive_step_mix"` constant | `tests/test_phase30_calibration.py:247-252` | `scripts/*.py` (`ast.Constant`) | Do not use that string anywhere in the module |
| 11 | D-04 bit-identity tripwire | `tests/test_phase25_prereg.py:265-311`; marker sets at `scripts/phase25_prereg.py:576-587` | **`tests/` and `scripts/`**, per function body | No single function may combine all three: a name in {`equal`, `assert_close`, `assert_allclose`, `allclose`, `sha256`, `hexdigest`}, an identifier containing `sigma_zero`/`sigma0`/`SIGMA_ZERO`, and an identifier containing `seam_off`/`seamoff`/`dp_fn`/`DP_FN`. **Relevant to D-17**: the E3 rule checks σ=0 control reuse "verified by SHA-256", so keep `dp_fn`/`seam_off` names out of that rule and its test |
| 12 | Accountant census | `tests/test_phase29_prereg.py:589-596` (`range(29, 35)`), `tests/test_phase30_points.py:709` (`range(30, 35)`) | `scripts/phase29_*` .. `phase34_*` | **Does not cover phase35.** E3 may import `phase25_epsilon`. Do not widen these ranges |
| 13 | Ubuntu skip pin | `tests/test_phase25_venue.py:324-357` (`_UBUNTU_* = 52 + 3 + 7 + 9 + 1 = 72`; `_M3_*`) | the whole `tests/` tree, run as two child suites (flag set and unset) | The new test has **zero skips**, so this file stays byte-unchanged. The child suites also run the new test under `PERSONACORE_SWEEP_ACTIVE=1`, so it must be green there too. A later MPS-only v6.0 test adds a NAMED constant plus a dated continuation, never an edit |
| 14 | Clean-tree probes (11) | memory note "execute-phase gates": `test_phase25_grid`, `test_phase25_probe2` (tests/); `test_phase25_driver`, `test_phase25_epsilon`, 4× `test_phase25_plots`, `test_phase25_watch` (scripts/); 2 under results/ | untracked or modified files under `tests/`, `scripts/`, `results/` | Run the full suite only on a committed tree. Plant AST REDs in `tmp_path`, never under `scripts/` |
| 15 | Provenance `module_sha256` pins | `results/*.json` pinning `teach_persona.py`, `phase30_points.py` | edits to the pinned modules | Phase 35 edits no existing module, so nothing to register. Do not touch `teach_persona.py`, `phase23_run.py` or `mitigation_gate.py` |
| 16 | Ruff | `make lint` = `ruff check . && ruff format --check .` | all | Keep the `# noqa: E402` comments on post-`sys.path` imports, as phase29 does |

## No Analog Found

| File / component | Role | Data Flow | Reason |
|---|---|---|---|
| `phase35_prereg` one-run-audit port (`p_value_one_run`, `eps_lower_one_run`) | utility | transform | No DP-audit lower-bound code exists. Use RESEARCH §Code Example 4 (stdlib port of arXiv 2305.08846v1 App. D, pp. 45–46). Pins: `(1000, 100, 75, 1e-4, 0.05)` → 0.673 and `(100000, 1510, 1439, 1e-5, 0.05)` → 2.675, each within 1e-3. The δ = 0, v = r closed form must hold within 1e-8 |
| Slot census (checks 1–3 over `scripts/phase{36..45}_*.py`) | test | batch | It is new, so the target set is empty today. Build it from `_module_targets` plus `ast.Call` matching on `Attribute(value=Name("phase35_prereg"), attr="fill")`. Prove non-vacuity on planted files |
| D-05 historic lock (`git show <first-add>:scripts/phase23_run.py` + AST) | test | batch | No test reads a file at a past commit through AST. Compose it from `_git` plus `ast.literal_eval` |

## Metadata

**Analog search scope:** `scripts/phase2[5-9]_*.py`, `scripts/phase1[89]_*.py`, `scripts/phase23_run.py`, `scripts/mitigation_*.py`, `scripts/erasure_gate.py`, `scripts/_addendum.py`, and every `tests/*.py` holding a `glob("*.py")`, `rglob("*.py")` or numbered-phase census (24 sites listed by grep).
**Files scanned:** about 30.
**Probes run (.venv 3.11):**
- the torch-free import of 8 candidate pins;
- `curve_total` on the worked example;
- the R1a field arithmetic (77.6370113463966);
- `margin_at_gate`;
- `len(ablated_components)` = 78 and `config.k` = 48;
- the first add of `phase23_run.py` = `5303819`.

**Pattern extraction date:** 2026-10-01
