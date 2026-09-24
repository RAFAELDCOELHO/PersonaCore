# Phase 29: v5.0 Pre-Registration and Carried Debt - Pattern Map

**Mapped:** 2026-09-24 (HEAD `95ed328`)
**Files analyzed:** 6 (2 new, 3 modified code/test, 1 set of 11 archived `.md` files)
**Analogs found:** 6 / 6

> **NEW FINDING, contradicts D-18 and RESEARCH §DEBT-03. Surface it to the developer.** All 11
> archived Phase-17 SUMMARYs **already record** `duration` and `completed`, but nested under
> `metrics:` rather than at top level. The validator checks top-level keys only, so it reports them
> missing. Measured from the first `---` block of each file:
>
> | File | `metrics.duration` | `metrics.completed` |
> |---|---|---|
> | 17-01 | 34min | 2026-08-14 |
> | 17-02 | 17min | 2026-08-14 |
> | 17-03 | 19min | 2026-08-14 |
> | 17-04 | 18min | 2026-08-14 |
> | 17-05 | 41min | 2026-08-14 |
> | 17-06 | 28min | 2026-08-14 |
> | 17-07 | 60min | 2026-08-14 |
> | 17-08 | 32min | 2026-08-14 |
> | 17-09 | 70min | 2026-08-14 |
> | 17-10 | 40min | 2026-08-15 |
> | 17-11 | 25min | 2026-08-15 |
>
> The nested `completed` values equal RESEARCH's `--follow` first-add dates in every row. So writing
> `duration: not recorded at the time` would be **false**, because the duration was recorded at the
> time. The honest fix is to copy the nested values to top-level `duration:` / `completed:`, with
> `metrics:` left untouched. The DEBT-03 test can then assert three things: the top-level values
> equal the nested ones, the top-level values equal the `--follow` date, and all 6 validator keys
> are present. The planner should raise this as a D-18 clarification, the same way RESEARCH raised
> Pitfall 6 for D-09.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `scripts/phase29_prereg.py` (NEW) | config/pre-registration module (constants + pure functions) | transform (frontier dict to verdict), no I/O at import | `scripts/phase27_prereg.py` | exact |
| `tests/test_phase29_prereg.py` (NEW) | test (git ancestry + AST + unit) | batch / git subprocess | `tests/test_phase27_prereg.py` | exact |
| `tests/test_phase27_relearn.py` (MODIFY, one test at :182-194) | test (integration, git) | file-I/O in a scratch repo | `tests/test_phase25_driver.py:143-155` (`_scratch_repo`) | exact |
| `scripts/phase16_persistence.py` (MODIFY, add `d28_note()` beside `arm_d_qualifier()` :2025-2060) | utility (runtime verbatim reader) | file-I/O (read) | the same file's `arm_d_qualifier()` :2036-2060 | exact |
| `tests/test_phase16_driver.py` (MODIFY, append d28 tests) | test | unit | `tests/test_phase16_driver.py:1313-1322` + `_context_blockquote` :90-106 | exact |
| `.planning/milestones/v3.0-phases/17-multi-persona-isolation-matrix/17-{01..11}-SUMMARY.md` (MODIFY, frontmatter) | config/doc | none | `.planning/milestones/v4.0-phases/27-relearning-attack/27-01-SUMMARY.md` frontmatter lines 45-46 | exact |

## Pattern Assignments

### `scripts/phase29_prereg.py` (pre-registration, transform)

**Analog:** `scripts/phase27_prereg.py` (631 lines). It is itself in `phase27_relearn.PINNED_MODULES` (`scripts/phase27_relearn.py:61-69`), so read it and never edit it.

**Module docstring register** (lines 1-38): the headings are `WHAT THIS FREEZES.`, `ANCESTRY-GUARDED.` (names the test and the glob), `CPU-ONLY AT IMPORT.` (names the lazy imports), `THE ROUTE, NEVER THE PIN.` and `Threats mitigated:`. Copy those section headings and restate them for v5.0. The docstring must also state the DEBT-04 fact that the accountant is loaded transitively through `phase25_record` (RESEARCH §DEBT-04).

**Imports + sys.path** (lines 40-56):
```python
import hashlib
import json
import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import erasure_gate  # noqa: E402  (needs the sys.path insert above)
import mitigation_budget  # noqa: E402  (same)
import mitigation_gate  # noqa: E402  (same)
...
import phase25_record  # noqa: E402  (same)
```
For v5.0, import `mitigation_budget`, `mitigation_gate`, `phase20_gate_coverage`, `phase25_record` and `phase27_prereg`. **Do not** import `teach_persona` at module level (torch). **Do not** import `phase25_epsilon` or `personacore.privacy` (DEBT-04 census).

**Date + ancestry-glob + `_prove`** (lines 58-74):
```python
COMMITTED = "2026-09-16"
RECORDS_AT_COMMIT = 0

# The tracked set the ancestry guard reads — a constant the test imports rather than retypes.
ARTIFACT_GLOB = "results/phase27_*"


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase27_prereg] {message}")
```
For v5.0 the single `ARTIFACT_GLOB` becomes the `V5_RESULT_PATHS` tuple (D-03), with `ARTIFACT_PATHSPECS = V5_RESULT_PATHS` typed once (RESEARCH Pattern 2). The prefix is `[phase29_prereg]`.

**By-reference block** (lines 77-93). Every name is an attribute alias, and the test asserts `is`:
```python
MARGIN_K = erasure_gate.MARGIN_K
CURVE_K = mitigation_budget.CURVE_K
FULL_K = mitigation_budget.FULL_FIDELITY_K
F_Y = mitigation_gate.F_Y
V4_VERDICTS = mitigation_gate.V4_VERDICTS
```
v5.0 adds `RATIO_GRID = mitigation_budget.ADVERSARIAL_RATIO_GRID`, `GATE_ROUTE = phase20_gate_coverage.corrected_point_verdict`, and the D-09 relearning pins as `phase27_prereg.RUNGS`, `RELEARN_CAP`, `MAX_STEPS`, `CHECKPOINT_INTERVAL`, `DESIGNATED_SEED`, `FRESH_SEEDS`, `POOLED_SEED_INDEX`, `ATTACKER_CORPUS`, `first_clear`, `z_rule`, `band`, `recovery_gate`, `promote_at_z`, `point_verdict_string` and `cleared_abc`. Per RESEARCH Pitfall 6, pin only the five `never_taught_*` entries of `phase27_prereg.PINNED_BASELINES` (lines 130-181), because the two `control_*` entries are DP adapters.

**Lazy-import function** (lines 213-224). This is the D-04 precedent:
```python
def attacker_corpus_rows():
    """... Imports are LAZY — ``teach_persona`` puts torch in ``sys.modules`` — so the module stays
    CPU-only at import. ..."""
    import phase14_factset
    import teach_persona

    return teach_persona.render_episodes(
        phase14_factset.LOCKED_FACTS, phase14_factset.TAUGHT_FAMILY_IDS
    )
```
`replay_windows(n)` copies this shape and calls the DP expression verbatim from `scripts/teach_persona.py:1970`: `replay_window_budget(stats["n_facts"]) // BLOCK_SIZE`. The replay source is `DIALOG_TRAIN_BIN` / `DIALOG_TRAIN_MASK` at `teach_persona.py:99-100`. The constant is `REPLAY_WINDOWS_PER_FACT = 4` at `teach_persona.py:179`. **Do not write any literal `4` in this module** (RESEARCH Pitfall 1).

**Key wrapping.** The frozen renderer it wraps is `scripts/phase25_record.py:199-227` (`point_key`). That renderer refuses unknown arms through `_axis_for` (:185-196, `AXIS_FOR_ARM` at :161-166 has only `dp_*`/`adv_*`). It refuses non-finite and negative values, and it routes through `phase25_prereg.point_record_path` for the charset check. `parse_point_key` (:230-248) matches `key.startswith(f"{arm}_{axis}")`, so `advr_n8_ratio…` does not start with `adv_n8_ratio` and falls through to `raise SystemExit` (:244). That is the "v4.0 reader refuses v5.0 keys" property D-01 wants. Wrap exactly as RESEARCH Pattern 1: `arm + phase25_record.point_key(twin, ratio)[len(twin):]`. Make `POINT_KEYS()` a function, never a module-level call, following the lazy precedent in `phase25_record.ORDERED_POINT_KEYS()` (:253).

**Admission gate.** The analog is `phase27_prereg.relearning_is_worth_attempting`, lines 330-422, plus `_tally` :330-332, `_verdict` :335-337, `admitted_point_keys` :425-437 and `cleared_counts` :440-459. Copy its structure: INCONCLUSIVE precedence ladder (absent → count ≠ EXPECTED → strings outside `_TALLY_NAMES` → tallies → tallies_by_leg), then ADMITTED, then generated MOOT reasons. v5.0 inserts REFUSED (every point REFUSED) between ADMITTED and MOOT (D-07), and D-08 refused-leg naming in the MOOT reasons. **Rewrite, don't call**: that function hard-codes `EXPECTED_POINTS = 44` (:116), `CONTROL_KEYS = dp_*` (:121) and `phase25_record.ORDERED_POINT_KEYS()` (:431). `VERDICTS` (:119) gains `"REFUSED"`. Derive `EXPECTED_POINTS` as `len(V5_ARMS) * len(RATIO_GRID)`.

**Counts-not-rates threshold** (lines 467-490). Copy these and change only the control source:
```python
def recall_threshold(frontier, leg):
    _prove(leg in LEGS, f"leg {leg!r} is not one of {LEGS}")
    k, n = frontier["verdicts"]["control_readings"][f"dp_{leg}"]["recall_counts"]["taught"]
    _prove_count("k", k)
    _prove_count("n", n)
    _prove(0 <= k <= n and n > 0, f"control taught recall {k}/{n} is not a count out of n > 0")
    return F_Y * (k / n), k, n


def _prove_count(name, value):
    """``prove_reproduction``'s register: an ``int`` that is not a ``bool``, or a refusal."""
    _prove(
        isinstance(value, int) and not isinstance(value, bool),
        ...
    )
```
In v5.0 the `f"dp_{leg}"` becomes `f"advr_{leg}"` (WR-05). `control_is_unlearnable(taught_k, taught_n, heldout_k, heldout_n)` reuses `_prove_count` and restates the route's inequality from `scripts/phase20_gate_coverage.py:641-647`:
```python
    _prove(
        0.0 < y_taught <= 1.0 and 0.0 < y_heldout <= 1.0,
        f"the recall floors came out Y_taught={y_taught}, Y_heldout={y_heldout}; both must lie in "
        "(0.0, 1.0]. ...",
```
The refusal-marker constants live at `scripts/phase25_promotion.py:53-56` (`COVERAGE_FLOOR_REFUSAL_MARKERS`). Import them by reference. Do not retype them.

**GATE-08 reference** (`scripts/mitigation_gate.py:822-829`). This is the D-15 subject. Nothing that depends on D-15 goes in until the ruling:
```python
    if a_ok and b_ok and c_ok and not replicated_at_second_seed:
        reasons.append(
            f"{REPLICATION_PENDING_MARKER} (GATE-08 / D-29): ..."
        )
        return "INCONCLUSIVE", reasons, arm
```

---

### `tests/test_phase29_prereg.py` (test, git + AST + unit)

**Analog:** `tests/test_phase27_prereg.py` (632 lines).

**Header + imports** (lines 1-41). The docstring enumerates what the file proves. It uses `_ROOT`, and inserts `scripts/` and `src/` into `sys.path`, then `import <module>  # noqa: E402  (scripts/ is not a package)`. **Do not copy lines 48-54 (`needs_adapters` skipif).** New tests must not `skipif` (RESEARCH Pitfall 4, `tests/test_phase25_venue.py`).

**`_git` helper** (lines 57-61):
```python
def _git(*args):
    """Run git inside the repository and return its stdout, raising on a non-zero exit."""
    return subprocess.run(
        ("git", *args), cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
```

**Ancestry guard.** Copy `_assert_frozen_before` from lines 74-111 **unchanged** (copy precedent, RESEARCH Alternatives). It checks four things: the repo is not shallow, `prereg != first_add`, `merge-base --is-ancestor`, and `checked == commits × tracked` plus `bool(checked) == bool(tracked)`. The call site changes from line 114-115 to:
```python
def test_phase29_prereg_is_frozen_before_every_v5_result():
    tracked = sorted({p for spec in phase29_prereg.ARTIFACT_PATHSPECS
                      for p in _git("ls-files", spec).split()})
    _assert_frozen_before("scripts/phase29_prereg.py", tracked)
```

**Torch-free import probe** (lines 133-142). Copy it and change the probed names to `torch`, `teach_persona`:
```python
def test_the_prereg_imports_without_torch():
    probe = (
        "import sys; sys.path.insert(0, 'scripts'); import phase27_prereg; "
        "print('torch' in sys.modules, 'teach_persona' in sys.modules, "
        "'phase18_extraction' in sys.modules)"
    )
    out = subprocess.run(
        [sys.executable, "-c", probe], cwd=_ROOT, capture_output=True, text=True, check=True
    )
    assert out.stdout.split() == ["False", "False", "False"], out.stdout
```

**By-reference `is` test** (lines 150-168). Copy the shape and assert `p.F_Y is mitigation_gate.F_Y`, `p.RATIO_GRID is mitigation_budget.ADVERSARIAL_RATIO_GRID`, `p.GATE_ROUTE is phase20_gate_coverage.corrected_point_verdict`, and each D-09 pin `is phase27_prereg.<name>`.

**Torch-side equality inside the test** (lines 171-184). The lazy import happens inside the test body. The `REPLAY_WINDOWS_PER_FACT` AST guard needs the real value, so it lives here:
```python
def test_pinned_seeds_equal_seed_ladder():
    import phase18_extraction as x18  # torch at import — inside the test only
    import teach_persona as tp
```

**AST literal scan** (lines 335-345). This is the shape for the D-04/D-05 "not re-typed" guards:
```python
    source = (_ROOT / PREREG).read_text(encoding="utf-8")
    floats = [
        node.value
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Constant) and isinstance(node.value, float)
    ]
    assert not [value for value in floats if f"{value:.6f}" == f"{x:.6f}"], floats
```

**Mutation-proved guard on a tmp copy** (`tests/test_phase27_relearn.py:392-406`). Every AST guard proves its own RED this way. The real file is never touched:
```python
    planted = source.replace('"baseline": args.baseline', '"baselne": args.baseline')
    assert planted != source, "no gate kwarg to misspell — the demonstration is vacuous"
    copied = tmp_path / "phase27_relearn_misspelled.py"
    copied.write_text(planted, encoding="utf-8")
    failures = _kwargs_trace_failures(copied.read_text(encoding="utf-8"))
    ...
    assert _DRIVER.read_text(encoding="utf-8") == source
```
Factor each guard as `_x_failures(source) -> list` so the same function runs on the real source (expected `[]`) and on the planted copy (expected non-empty).

**Admission-branch tests.** The analogs are lines 192-267 (`_forge`, `test_the_gate_admits_only_pass`, `test_partial_or_inconsistent_frontier_is_inconclusive`). v4.0 deep-copies the 22 MB frontier. **v5.0 must instead build a minimal 12-point dict in the test** (RESEARCH Pattern 7), because no v5.0 frontier exists. Keep the consistent-forgery idea from `_forge` :192-205: flipping a verdict moves both `tallies` and `tallies_by_leg`.

**Route differential (PREREG-03).** The analog is `_route_kwargs` at lines 288-301 plus `test_every_frontier_verdict_re_derives_through_the_route` at :304-327, which calls `phase20_gate_coverage.corrected_point_verdict(**kwargs)` under `pytest.raises(SystemExit)`. For the v5.0 differential, take one stored `adv_n64_ratio0p000000` entry. Recall is a rate, so zero the control count and assert that the SystemExit text contains both `promotion.COVERAGE_FLOOR_REFUSAL_MARKERS`. Then set it to 1/n and assert there is no floor refusal. Loading the frontier as a module-scope fixture (:64-66) is acceptable in the test. It is the same pattern as `artifact()`.

**DEBT-04 accountant census.** The analog is `tests/test_phase20_correction.py:1377-1458` (`test_mitigation_point_verdict_has_no_caller_outside_this_module`). It matches calls on both `.id` and `.attr`:
```python
            called = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
```
It also censuses imports through `ast.ImportFrom` alias names (:1409-1417). It asserts non-vacuity (`inside_sanctioned >= 1`, :1451), which is the `bool(checked) == bool(tracked)` register. For v5.0, glob `scripts/phase29_*.py` … `phase34_*.py`. Forbid `Import`/`ImportFrom` of `personacore.privacy*` and `phase25_epsilon`, and `Name`/`Attribute` in `{epsilon_for, sigma_for, delta_closed, delta_quadrature}`. Prove non-vacuity by running the matcher on `scripts/phase25_epsilon.py`, which must fire. **No `sys.modules` assertion**: importing `phase25_record` loads the accountant (`scripts/phase25_record.py:82` `import phase25_epsilon`).

**DEBT-03 frontmatter test.** Put it in this file per RESEARCH. There is no in-repo frontmatter parser analog. Use stdlib: split on the first two `---` lines and read top-level `^key:` lines. Assert all 6 keys `phase, plan, subsystem, tags, duration, completed`. Assert top-level `completed` equals `_git("log", "--follow", "--diff-filter=A", "--format=%ad", "--date=short", "--", path).split()[-1]`. Also assert the top-level values equal the nested `metrics.duration` / `metrics.completed` (see the finding at top).

---

### `tests/test_phase27_relearn.py` — DEBT-01 (edit :182-194 only)

**Current offender** (lines 182-194). It writes into the real repo:
```python
def test_a_leg_refuses_an_untracked_record_inside_the_repo():
    rel = "results/phase27_admission_probe_never_committed.json"
    probe = _ROOT / rel
    ...
        probe.write_text(json.dumps(_record("ADMITTED")), encoding="utf-8")
        with pytest.raises(SystemExit) as excinfo:
            relearn._require_admitted(probe)
    ...
    assert "not tracked" in str(excinfo.value) and "REFUSING" in str(excinfo.value)
```

**Scratch-repo analog** (`tests/test_phase25_driver.py:143-155`):
```python
def _scratch_repo(tmp_path):
    """A real git repository in ``tmp_path`` with `.gitignore` mirroring the project's."""
    root = tmp_path / "scratch"
    (root / "results").mkdir(parents=True)
    ...
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    for key, value in (("user.email", "t@example.com"), ("user.name", "t")):
        subprocess.run(["git", "-C", str(root), "config", key, value], check=True)
```
An initial commit is not needed. `git ls-files` works on an empty repo.

**Why a monkeypatch suffices** (`scripts/phase27_relearn.py:114-117, 131-172`). `_rel` and `_require_admitted` read the module global `_ROOT` at call time (`path.is_relative_to(_ROOT)`, `cwd=_ROOT`), so `monkeypatch.setattr(relearn, "_ROOT", scratch)` needs no driver edit. `phase27_relearn.py` is in its own `PINNED_MODULES` (:61-69), so **edit only the test**. `_require_admitted` calls `path.resolve()`, so build `scratch` from `tmp_path.resolve()` or the `is_relative_to` check misses on the macOS `/private` symlink. Always pass the probe path explicitly. `relearn.RECORD` still points at the real root (RESEARCH Pitfall 7).

**Reuse for the no-touch guard.** Reuse the existing helpers `_git` (:98-101, returns raw stdout, no strip) and `_real_tree_strays()` (:792-806). Take a `{rel: sha256}` snapshot of `_git("ls-files", "results/phase27_*").split()` before and after. Both snapshots and `_real_tree_strays()` must be unchanged, and `_git("status", "--porcelain", "--", "results/phase27_*")` must be empty. `_record("ADMITTED")` (:119-124) still forges the record. The autouse `clean_tree` fixture (:109-116) is unaffected.

---

### `scripts/phase16_persistence.py` — DEBT-02 `d28_note()`

**Analog, the same file** (lines 2025-2060):
```python
_CONTEXT_PATH = (
    _REPO_ROOT / ".planning" / "milestones" / "v3.0-phases"
    / "16-weight-vs-prompt-persistence-control" / "16-CONTEXT.md"
)
ARM_D_QUALIFIER_ANCHOR = "- **D-25:**"


def arm_d_qualifier():
    """D-25's user instruction, VERBATIM, read from ``16-CONTEXT.md`` — see the comment above."""
    _prove(_CONTEXT_PATH.exists(), ...)
    body = _CONTEXT_PATH.read_text(encoding="utf-8").split(ARM_D_QUALIFIER_ANCHOR, 1)
    _prove(len(body) == 2, f"{ARM_D_QUALIFIER_ANCHOR!r} is absent from {_CONTEXT_PATH}")
    lines = []
    for line in body[1].splitlines():
        stripped = line.strip()
        # A slice rather than the str prefix METHOD: ...
        if stripped[:1] == ">":
            lines.append(stripped.lstrip(">").strip())
        elif lines:
            break
    _prove(lines, f"no blockquote follows {ARM_D_QUALIFIER_ANCHOR!r} in {_CONTEXT_PATH}")
    return " ".join(lines).strip('"')
```
Extract the body into `_blockquote_after(anchor)`, then define `arm_d_qualifier = _blockquote_after(ARM_D_QUALIFIER_ANCHOR)` and `d28_note = _blockquote_after(D28_NOTE_ANCHOR)`, both as `def`s, with `D28_NOTE_ANCHOR = "- **D-28:**"`. The anchor exists at `16-CONTEXT.md:267`. Keep `arm_d_qualifier()`'s output byte-identical (asserted at `tests/test_phase16_driver.py:1319`).

**Source guards that bite this file:**
- `tests/test_phase16_driver.py:643-646` forbids the substrings `startswith`, `endswith`, `fuzz`, `levenshtein`, `SequenceMatcher` and `difflib` **anywhere in the source, comments included**. Keep the `stripped[:1] == ">"` idiom, and do not name those tokens in new comments.
- `:629` requires `source.count("0.125") == 1`.

---

### `tests/test_phase16_driver.py` — DEBT-02 tests (append)

**Analog: the helper** (lines 90-106, `_context_blockquote(anchor)`). This is the test-side twin parser. `startswith` is allowed in the test file:
```python
def _context_blockquote(anchor):
    body = _CONTEXT_PATH.read_text(encoding="utf-8").split(anchor, 1)[1]
    lines = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith(">"):
            lines.append(stripped.lstrip(">").strip())
        elif lines:
            break
    assert lines, f"no blockquote follows {anchor!r} in 16-CONTEXT.md"
    return " ".join(lines).strip('"')
```
**Analog: the test** (lines 1313-1322):
```python
def test_report_carries_every_verbatim_clause(monkeypatch, tmp_path):
    text = _render(monkeypatch, tmp_path)
    for anchor in ("- **D-03:**", "- **D-07:**", "- **D-25:**"):
        clause = _context_blockquote(anchor)
        assert clause in text, f"{anchor} is not reproduced verbatim in the report"
    assert driver.arm_d_qualifier() == _context_blockquote("- **D-25:**")
```
The driver is loaded through `importlib.util.spec_from_file_location` (:47-54, `driver = _load_driver()`). New tests use `driver.d28_note()`. Add these:
1. `driver.d28_note() == _context_blockquote("- **D-28:**")`.
2. `hashlib.sha256(driver.d28_note().encode()).hexdigest() == "171725c69ff06241882a0d165c02172d80721b3b33d55ddf7c8bef8609ad4210"` (RESEARCH measured this. Re-measure on the implemented function before pinning).
3. The published report `results/phase16_persistence_report.md` lacks the kernel, and the prereg's `NAMED_LIMITATIONS` carries the D-28 entry. Test both directions.

`hashlib` is not currently imported in this test file (imports at :23-30). Add it.

---

### 11 × `17-NN-SUMMARY.md` — DEBT-03 (hand edit)

**Format analog:** `.planning/milestones/v4.0-phases/27-relearning-attack/27-01-SUMMARY.md` frontmatter lines 45-46. These are top-level keys:
```yaml
duration: 24min
completed: 2026-09-16
```
**Current Phase-17 shape** (17-01, lines 46-50). The same fields are nested:
```yaml
metrics:
  duration: 34min
  tasks: 3
  files: 4
  completed: 2026-08-14
```
Add top-level `duration:` / `completed:` lines just before the closing `---`, copying the nested values (table at top). Edit by hand. Never use `gsd-sdk frontmatter.set`. The acceptance check is read-only: `gsd-sdk query frontmatter.validate <file> --schema summary`. No test or script reads these bytes (RESEARCH §DEBT-03).

## Shared Patterns

### Refusal = `_prove` → `SystemExit`
**Source:** `scripts/phase27_prereg.py:71-74`, `scripts/_addendum.py:50-53`
**Apply to:** `phase29_prereg.py` (every invariant). Never use `assert` in `scripts/`. The message prefix is `[module_name]`.

### Stdlib-at-import, torch lazily
**Source:** `scripts/phase27_prereg.py:19-24, 213-224`, test probe `tests/test_phase27_prereg.py:133-142`
**Apply to:** `phase29_prereg.py` and its import-probe test.

### By-reference constants asserted with `is`
**Source:** `scripts/phase27_prereg.py:77-93`, `tests/test_phase27_prereg.py:150-168`
**Apply to:** grid, `F_Y`, gate route, D-09 relearning pins, refusal markers.

### Ancestry freeze + continuation
**Source:** `tests/test_phase27_prereg.py:74-115`. After freeze, corrections go through `scripts/_addendum.py::append_addendum(path, addendum, *, pending, recorded)` (:56-100).
**Apply to:** `phase29_prereg.py`. Edits are legal only until the first `results/phase3*` commit.

### AST census, never grep
**Source:** `tests/test_phase20_correction.py:1377-1458` (both `.id` and `.attr`, import aliases, non-vacuity), `tests/test_phase27_prereg.py:338-344` (constant scan)
**Apply to:** the D-04 replay-literal, D-05 grid/gate re-typing and DEBT-04 accountant guards.

### Watched RED on a tmp copy
**Source:** `tests/test_phase27_relearn.py:392-406`
**Apply to:** every new AST guard.

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| (DEBT-03 frontmatter parser inside `test_phase29_prereg.py`) | test helper | parse | No in-repo YAML-frontmatter reader exists (`tests/test_phase23_cost.py:808` only mentions frontmatter in prose). Use stdlib line parsing and do not add a dependency. |
| (D-15 promotion execution, conditional on option 1) | driver | batch | RESEARCH D-15: no second-seed/K=48 execution code exists in `scripts/`. Only the decision rule `mitigation_gate.promote_to_full_fidelity` (:963) / `ratchet_k` (:917) imports cleanly. |

## Hazards the planner must carry (repo censuses that bite new files)
- `tests/test_phase21_sc5.py:189-196` flags the text `== 10` / `!= 10` in any `tests/*.py`, comments included.
- `tests/test_phase20_correction.py:1377`: never import or call `mitigation_point_verdict` from `scripts/`.
- `tests/test_phase25_driver.py:359`: no `os.replace` outside `phase25_run.py` / `phase25_record.py`.
- `tests/test_phase25_prereg.py:271`: no function pairing sigma-zero and seam-off markers with equal/sha256.
- There must be no literal `4` anywhere in `phase29_prereg.py` (D-04 guard). This includes `range(4)` and slices.
- Do not edit these PINNED modules: `phase27_prereg.py`, `phase27_relearn.py`, `teach_persona.py`, `mitigation_gate.py` (`scripts/phase27_relearn.py:61-69`), nor `phase25_record.py`, `phase25_promotion.py` or `phase20_gate_coverage.py`.
- No `results/phase3*` file may be written during Phase 29, test probes included. Use `tmp_path` only.

## Metadata

**Analog search scope:** `scripts/`, `tests/`, `.planning/milestones/v3.0-phases/17-*`, `.planning/milestones/v4.0-phases/27-*`
**Files scanned:** ~16
**Pattern extraction date:** 2026-09-24
