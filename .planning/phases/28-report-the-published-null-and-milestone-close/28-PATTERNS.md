# Phase 28: Report, the Published Null, and Milestone Close - Pattern Map

**Mapped:** 2026-09-20
**Files analyzed:** 11 (6 new, 5 modified)
**Analogs found:** 10 / 11 (the ledger JSON has a shape analog only)

Every path and line number below was read from disk in this session. RESEARCH.md §"Reusable
machinery" named the analogs; this file verifies them and excerpts the code to copy. Excerpts are
verbatim from the analog — copy the mechanism, rename the phase.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `scripts/phase28_report.py` (renderer) | utility / CLI script | transform (JSON records + module constants -> Markdown block between sentinels) | `scripts/_addendum.py` (append-only writer, produced-bytes checks) + sentinel convention `tests/test_phase25_correction.py:104-127` | role-match (no template renderer exists yet; first of its kind) |
| `scripts/phase28_report.md.tmpl` (or chosen name) | config / template data | transform input | none — `.planning/REQUIREMENTS.md` `<!-- 23-12-CONTINUATION-BEGIN/END -->` is the only sentinel-bounded prose precedent | partial |
| `results/phase28_ledger.json` | model / data record | batch (hand-authored rows, read by renderer + tests) | `results/phase20_gate_coverage_correction.json` (hand-reasoned correction record with named `cost`/`reason` prose fields) | partial (shape only) |
| `tests/test_phase28_report.py` | test | byte-identity re-render, template scan, obligation resolution, provenance digests | `tests/test_phase25_correction.py` (sentinels + `_span` + AST `_called_names`), `tests/test_phase24_record.py:288-334` (bytes-recompute digests), `tests/test_phase18_docs.py:308-342` (verbatim claim, anchored section) | exact |
| `tests/test_phase28_prereg.py` | test | git ancestry (D-05) | `tests/test_phase27_prereg.py:57-115` (`_git`, `_assert_frozen_before`, shallow refusal) | exact |
| `tests/test_phase28_ledger.py` | test | schema / closed-domain / `len()` counts | `tests/test_phase24_record.py:288-334` (collect-all-drift-then-assert), `tests/test_phase25_driver.py:341-365` (AST census returning a set compared to an exact allowlist) | role-match |
| `tests/test_package.py` (modify: D-25 tomllib test, D-26 rename) | test | git + tomllib | itself, `:28-46` | exact |
| `tests/test_phase25_correction.py` (modify: register `_EARLIER_GUARD_FILES`) | test | AST register | itself, `:375-395` | exact |
| `src/personacore/evaluation/perplexity.py:11-13` (modify: docstring) | utility docstring | — | `tests/test_perplexity.py:119-122` already asserts the true denominator | exact |
| `scripts/phase16_persistence.py:1605` (modify: docstring parenthetical) | utility docstring | — | `tests/test_phase14_scoring.py:517` holds `PERSONA_ALLOWLIST` | exact |
| `docs/REPORT.md` / `README.md` (modify: append section / insert bullets) | docs surface | append-only | `docs/REPORT.md:1316` last `## ` (house style: `*Appended additively. No line above this heading is altered.*`), `README.md:109-147` glance list | exact |

## Pattern Assignments

### `scripts/phase28_report.py` (utility, transform)

**Analog:** `scripts/_addendum.py` — the only append-only Markdown writer; copy its sys.path bootstrap, `_prove` register and produced-bytes checks. Sentinel names from `tests/test_phase25_correction.py:104-105`.

**Imports / bootstrap pattern** (`scripts/_addendum.py:40-47`):
```python
import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import _verdict  # noqa: E402  (needs the sys.path insert above)
```
Phase 28 adds `import json, hashlib, string` (stdlib) and imports `mitigation_gate`, `mitigation_budget`, `mitigation_unit`, `phase25_prereg`, `phase26_prereg` the same `# noqa: E402` way; `from personacore.privacy import accountant` after inserting `_REPO_ROOT / "src"` (shape at `tests/test_phase27_prereg.py:27-29`). No torch import anywhere.

**Error register** (`scripts/_addendum.py:50-53`):
```python
def _prove(condition, message):
    """``SystemExit`` on a broken invariant — phase17/18's register, so callers catch one type."""
    if not condition:
        raise SystemExit(f"[_addendum] {message}")
```

**Core write pattern — check the PRODUCED bytes, not the construction** (`scripts/_addendum.py:67-100`):
```python
    path = pathlib.Path(path)
    text = path.read_text(encoding="utf-8")

    found = text.count(pending)
    _prove(
        found == 1,
        f"{path} carries {found} occurrence(s) of the placeholder line {pending!r}, and this "
        f"writer replaces EXACTLY ONE. ...",
    )

    before, after = text.split(pending)
    updated = before + recorded + after
    ...
    _prove(
        updated.startswith(before) and addendum.rstrip("\n") in updated,
        f"the rewritten {path} does not carry its original prefix byte-identically, or lost the "
        "addendum it was appending — the append-only property is the whole guarantee this helper "
        "offers and it is checked on the produced bytes, not assumed from the construction",
    )

    path.write_text(updated, encoding="utf-8")
```
Phase 28's `install(path, block)` replaces `pending`/`recorded` with the BEGIN/END pair (`str.count(BEGIN) == str.count(END) <= 1`), keeps `updated.startswith(before)` as its prefix proof, and writes with `Path.write_text` — never `os.replace` (census `tests/test_phase25_driver.py:341-365` allows it only in `phase25_run.py` / `phase25_record.py`).

**Sentinel naming** (`tests/test_phase25_correction.py:104-105`):
```python
def _markers(stem):
    return f"<!-- {stem}-BEGIN -->", f"<!-- {stem}-END -->"
```
Use stems `PHASE28-REPORT` (docs/REPORT.md) and `PHASE28-GLANCE` (README.md).

**Binding resolution** — obligation paths are dotted; resolve with indexing, never `.get()` (contract text `scripts/phase25_prereg.py:420-421`: "A field_path that does not resolve against the assembled artifact is a RED test in Phase 28 — never a licence to paraphrase around it"). Fill via `string.Template(...).substitute(bindings)` so a missing binding raises `KeyError`.

**Provenance in the block** — copy the record-pins-frontier shape at `tests/test_phase27_prereg.py:122-124` for every source record read:
```python
        frontier_bytes = (_ROOT / FRONTIER).read_bytes()
        assert blob["frontier_sha256"] == hashlib.sha256(frontier_bytes).hexdigest()
        assert blob["frontier_bytes"] == (_ROOT / FRONTIER).stat().st_size
```
Renderer emits `sha256` + byte size per source into the block; test recomputes from `read_bytes()`.

**Date stamp:** module constant `PUBLISHED = "2026-09-.."` (D-24). Never `date.today()`, never `git rev-parse HEAD`.

**Post-publish corrections only via** `scripts/_addendum.py:56` `append_addendum(path, addendum, *, pending, recorded)` — both keywords required. Note `tests/test_phase25_correction.py:28-36` measured that `append_addendum` is vacuous on planning `.md` (no `## Verdict`); for `docs/REPORT.md` / `README.md` it is likewise verdict-less, so its only live guard is the placeholder count + prefix check — acceptable for D-20.

---

### `scripts/phase28_report.md.tmpl` (template)

**Analog:** none as a file. Rules that shape it: `${dotted.path}` placeholders only (RESEARCH Pattern 1); the D-19 numeral scan runs over THIS file after stripping `${...}`. Keep every quantity (`n=8`, `K=48`, σ labels) as a placeholder. Exempt grammar: `Phase \d+`, `[A-Z]+-\d+`, ISO dates, 7-40 hex SHAs, `§\d+(\.\d+)?[a-z]?`, citation years. Keep the test's RED probe as a planted template in `tmp_path` (memory: natural RED beats planted RED — write the file first with one numeral, watch RED, then bind it).

---

### `results/phase28_ledger.json` (data record, batch)

**Analog (shape only):** `results/phase20_gate_coverage_correction.json` — a hand-reasoned record whose fields carry the reason in prose beside the data (`"cost": "NAMED, NOT GLOSSED. ..."`). Ledger rows carry D-28's six keys: `id`, `milestone`, `source`, `disposition`, `evidence`, `reason`. Disposition domain closed at six values (D-29). Counts are never stored — tests and renderer use `len()` over filters.

No existing ledger to copy. Write JSON with `json.dumps(..., indent=2, sort_keys=True, ensure_ascii=False) + "\n"` so a re-dump is byte-stable (the frontier / admission records are emitted this way; `results/phase20_gate_coverage_correction.json` is 2-space indented with sorted keys).

**Clean-tree trap:** `tests/test_phase25_frontier.py:123` asserts `_git("status", "--porcelain", "results/") == ""`; an untracked ledger reddens it and its siblings. Commit before running the full suite.

---

### `tests/test_phase28_report.py` (test, byte-identity + scans)

**Analog:** `tests/test_phase25_correction.py` (sentinel span + AST names) and `tests/test_phase24_record.py:288-334` (digest recompute).

**Imports / bootstrap** (`tests/test_phase27_prereg.py:10-31`):
```python
import ast
import hashlib
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

import _prose  # noqa: E402  (scripts/ is not a package)
```

**Span slice — the byte-identity comparator** (`tests/test_phase25_correction.py:108-127`):
```python
def _span(relative_path, stem):
    text = _text(relative_path)
    begin, end = _markers(stem)
    for sentinel in (begin, end):
        found = text.count(sentinel)
        assert found == 1, (
            f"{relative_path}: {sentinel} occurs {found} time(s); exactly one is required. A "
            "missing or duplicated sentinel makes the guard scan the wrong text, which is how a "
            "guard passes vacuously"
        )
    assert text.index(begin) < text.index(end), (...)
    return text.split(begin, 1)[1].split(end, 1)[0]
```
Test 1 (D-17): `assert _span("docs/REPORT.md", "PHASE28-REPORT") == phase28_report.render_report()` — plain `==` on bytes/str, NOT `normalized`.

**Prose-in-surface checks route through `normalized`** (`scripts/_prose.py:35-46`; call shape `tests/test_phase26_prereg.py:109`):
```python
        assert _prose.normalized(clause) in _prose.normalized(phase26_prereg.RULE)
```
Use this for: expectation sentence in `git show c673b4c:.planning/research/SUMMARY.md`, §12.5c slice of `results/phase25_operational_note.md`, record strings quoted in the block.

**Anchored section read, never whole-file** (`tests/test_phase18_docs.py:269-281`):
```python
def _anchored_section(text, heading, stop=r"## "):
    found = re.compile(rf"^{re.escape(heading)}\b.*?(?=^{stop}|\Z)", re.M | re.S).search(text)
    return found.group(0) if found else None
```

**AST, not grep, for "routes through normalized"** (`tests/test_phase25_correction.py:130-141`):
```python
def _called_names(relative_path):
    tree = ast.parse(_text(relative_path), filename=relative_path)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute):
                names.add(func.attr)
            elif isinstance(func, ast.Name):
                names.add(func.id)
    return names
```

**Provenance digests — collect all drift, then assert once** (`tests/test_phase24_record.py:318-331`):
```python
    drifted = []
    for name, recorded in pins.items():
        path = _ROOT / name
        assert path.is_file(), f"provenance pins {name}, which does not exist at {path}"
        live = hashlib.sha256(path.read_bytes()).hexdigest()
        if live != recorded:
            drifted.append((name, recorded, live))

    assert not drifted, (
        f"{len(drifted)} of {len(pins)} provenance digests no longer match the files on disk:\n"
        + "".join(f"    {name}\n      recorded {rec_}\n      live     {liv}\n" for name, rec_, liv in drifted)
        ...
```
Docstring there (`:299-301`): digests recomputed from BYTES, never through the emitter's own hash helper.

**Obligation resolution** (D-23) — iterate the tuples at `scripts/phase25_prereg.py:424-477` (7 pairs on disk; CONTEXT said 8 — `len()` it) and `scripts/phase26_prereg.py:354-395` (7 pairs). Wildcard row `points.<key>.verdict.verdict` expands over `canary["audited_point_keys"]`; `<artifact absent>` row is satisfied by `(_ROOT / "results/phase26_canary.json").is_file()`.

**Constants** (SC2): `accountant.sigma_for(4.0, p["composed_steps"], p["delta"]) == 15.289937507119` and `accountant.epsilon_for(16.0, ...) == p["epsilon"]` with `p = frontier["points"]["dp_n8_sigma16p000000"]` (RESEARCH Code Examples, verified). `mitigation_gate.CAPACITY_BRANCHES` must contain `verdicts.capacity_branch` (`scripts/phase25_prereg.py:443`).

---

### `tests/test_phase28_prereg.py` (test, git ancestry — D-05)

**Analog:** `tests/test_phase27_prereg.py:57-115`. Copy verbatim, then swap the artifact glob and add the `git show` conjunct.

**Git helper** (`:57-61`):
```python
def _git(*args):
    """Run git inside the repository and return its stdout, raising on a non-zero exit."""
    return subprocess.run(
        ("git", *args), cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
```

**Shallow-clone refusal + ancestry** (`:74-111`):
```python
def _assert_frozen_before(prereg_artifact, tracked):
    assert _git("rev-parse", "--is-shallow-repository") == "false", (
        "shallow clone: the pre-registration commit objects are absent, so this guard cannot "
        "distinguish 'the ordering holds' from 'the ordering was never checked'. "
        "Set `fetch-depth: 0` on actions/checkout (see .github/workflows/ci.yml)."
    )
    prereg_commits = _git("log", "--format=%H", "--", prereg_artifact).split()
    assert prereg_commits, f"{prereg_artifact} has no commits — green and blind"

    checked = 0
    for artifact in tracked:
        adds = _git("log", "--diff-filter=A", "--format=%H", "--", artifact).split()
        # git log is newest-first, so the commit that ADDED the file is the last entry. Taking the
        # earliest add is what makes a delete-and-re-add cycle unable to launder the ordering.
        first_add = adds[-1]
        for prereg in prereg_commits:
            assert prereg != first_add, (... "SAME commit" ...)
            subprocess.run(
                ("git", "merge-base", "--is-ancestor", prereg, first_add),
                cwd=_ROOT,
                check=True,
            )
            checked += 1

    assert checked == len(prereg_commits) * len(tracked), (...)
    assert bool(checked) == bool(tracked), (...)
```
D-05 differences: `prereg_commits` is the single literal `EXPECTATION_COMMIT = "c673b4c..."` (full SHA via `_git("rev-parse", "c673b4c")`), `tracked = _git("ls-files", "results/phase2[0-8]_*").split()`, plus conjunct (i): `_prose.normalized(SENTENCE) in _prose.normalized(_git("show", f"{EXPECTATION_COMMIT}:.planning/research/SUMMARY.md"))`. CI has `fetch-depth: 0` (`.github/workflows/ci.yml:28`, verified). Local repo is non-shallow; tags `v1.0 v2.0 v3.0 m1-demo-v1` present.

**Caller shape** (`:114-115`):
```python
def test_phase27_prereg_is_frozen_before_every_phase27_result():
    _assert_frozen_before(PREREG, _git("ls-files", phase27_prereg.ARTIFACT_GLOB).split())
```

---

### `tests/test_phase28_ledger.py` (test, schema + closed domain)

**Analog:** collect-then-assert loop from `tests/test_phase24_record.py:318-331` (above); exact-set comparison from `tests/test_phase25_driver.py:358-365`:
```python
    writers = set()
    for path in sorted(_SCRIPTS.glob("*.py")) + sorted((_ROOT / "src").rglob("*.py")):
        ...
    assert writers == {"phase25_run.py", "phase25_record.py"}, sorted(writers)
```
Apply: `assert {row["disposition"] for row in rows} <= DISPOSITIONS` (closed domain), `assert set(row) == REQUIRED_KEYS` per row, and for `FIXED` rows resolve `evidence` test node ids with `subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", node_id])`. `SC3`'s "16 + 6" = `len([r for r in rows if r["milestone"] == "v3.0" and ...])` — never a literal.

**Do not write the literal `== 10`** anywhere in this file (`tests/test_phase21_sc5.py:189-197` census pattern `(?:==|!=)\s*10(?![0-9_])` over `tests/`, comments included).

---

### `tests/test_package.py` (modify — D-25, D-26)

**Analog:** itself. Keep the bytes rule (`:37`):
```python
    actual = hashlib.sha256((_ROOT / "pyproject.toml").read_bytes()).hexdigest()
    assert actual == PYPROJECT_SHA256, (...)
```
D-26: rename `test_pyproject_unchanged_since_v2_close` (`:28`) and rewrite the message (`:38-46`, which still says "byte-identical at v3.0 close" — false since `5065bc5`). D-25: add
```python
def _deps(rev):
    toml = subprocess.run(["git", "show", f"{rev}:pyproject.toml"], cwd=_ROOT,
                          capture_output=True, text=True, check=True).stdout
    return tomllib.loads(toml)["project"]["dependencies"]
```
and assert `_deps("v1.0") == _deps("v2.0") == _deps("v3.0") == tomllib.loads((_ROOT/"pyproject.toml").read_text())["project"]["dependencies"]`. Precede with the shallow-clone refusal string from `tests/test_phase27_prereg.py:77-81` and `assert set(_git("tag","-l").split()) >= {"v1.0","v2.0","v3.0"}` (RESEARCH A3).

---

### `tests/test_phase25_correction.py` (modify — register)

**Analog:** itself (`:375-395`):
```python
_EARLIER_GUARD_FILES = ("tests/test_phase23_cost.py", "tests/test_phase24_correction.py")

def test_the_register_is_three_files_wide():
    for relative_path in _EARLIER_GUARD_FILES:
        assert (_ROOT / relative_path).is_file(), (...)
        called = _called_names(relative_path)
        assert "normalized" in called, (...)
```
Add the Phase 28 test file(s) to the tuple; the test name says "three files wide" — rename when the tuple grows, per D-26's "a name that asserts something false does not survive". Note the module docstring (`:9-10`) pins "FOUR INSTANCES, THREE GUARD FILES" — update that sentence in the same commit.

---

### `src/personacore/evaluation/perplexity.py:11-13` (modify — D-32 docstring)

Current text (verified):
```
  - A length-L window predicts L-1 transitions: token 0 is context-only, never
    scored. So the denominator is ``corpus_len - n_windows`` (each scored window
    loses its first token as unpredictable).
```
Truth already asserted at `tests/test_perplexity.py:121-122`:
```python
    # For a cleanly tiling corpus this is exactly corpus_len - 1 (only token 0 unscored).
    assert ntok == n_tokens - 1
```
Fix the docstring to match; add a docstring-text test (`"corpus_len - 1" in perplexity.__doc__` and `"corpus_len - n_windows" not in perplexity.__doc__`). Not ancestry-guarded, no `module_sha256` names it (RESEARCH §3 row 11).

### `scripts/phase16_persistence.py:1605` (modify — D-32 docstring)

Current text (verified, inside `build_overwrite_statement` docstring):
```
    new ``draw_all`` call site — ``PERSONA_ALLOWLIST`` stays at exactly two entries and the widened
    D-21 guard in ``tests/test_phase14_scoring.py`` stays green without that file being touched.
```
Bind the count to `len(PERSONA_ALLOWLIST)` from `tests/test_phase14_scoring.py:517` in the new test rather than typing a number. `phase16_persistence.py` is NOT in `V3_ARTIFACT_GLOBS` (`phase16_*.py` is — re-measure: `tests/test_phase16_prereg.py` guards `phase16_*` per `scripts/_prose.py:25-26`; RESEARCH §3 row 3 says no `is-ancestor` test names it. Planner MUST run `pytest tests/test_phase16_prereg.py -q` after the edit before assigning `FIXED`).

---

### `docs/REPORT.md` / `README.md` (append / insert)

**House style for an additive section** (`docs/REPORT.md:1316-1318`):
```
## Figure Corrections to the Section Above (recorded 2026-08-19)

*Appended additively. No line above this heading is altered.*
```
Append AFTER line 1326 (EOF). Section title carries `null-at-both-capacities` verbatim. README bullets go INSIDE `## Results at a glance` (`README.md:109`) before the first existing `- **Held-out recall 0.3483**` bullet (`:111`), zero deletions, no new `## ` heading — `tests/test_phase18_docs.py:354-379` asserts `headings[:N] == baseline` prefix equality over every `## ` heading in both files. Existing README bullet grammar (`:111-122`): bold headline number, inline qualifier, link to the source record and to `docs/REPORT.md#<anchor>` (`tests/test_phase15_docs.py:362-368` `_github_anchor`).

## Shared Patterns

### Prose comparison — the one copy
**Source:** `scripts/_prose.py:35-46`
**Apply to:** every cross-surface prose check in all `tests/test_phase28_*.py`
```python
def normalized(text):
    return " ".join(text.split())
```
Call shape: `_prose.normalized(phrase) in _prose.normalized(text)`. Byte-identity checks use `==` on the raw span instead (D-22; both, no conflict).

### Shallow-clone refusal
**Source:** `tests/test_phase27_prereg.py:77-81` (twin `tests/test_phase18_docs.py:1026-1030`)
**Apply to:** `test_phase28_prereg.py`, D-25 in `test_package.py`, any test that reads `git show`/`git log`.

### Digests from bytes, never text
**Source:** `tests/test_package.py:33-37`, `tests/test_phase24_record.py:299-301`, `tests/test_phase27_prereg.py:122-124`
**Apply to:** renderer provenance block, `test_phase28_report.py` provenance test, ledger evidence pins.

### AST census over new files — what will bite `scripts/phase28_report.py` and `tests/test_phase28_*.py`
| Census | Location | Rule for new files |
|--------|----------|--------------------|
| `os.replace` | `tests/test_phase25_driver.py:341-365` (`scripts/*.py` + `src/**`) | write with `Path.write_text`; never `os.replace` |
| `mitigation_point_verdict` | `tests/test_phase20_correction.py:1421-1444` (`scripts/**` + `src/**`, calls AND `from mitigation_gate import ...`) | never call/import it; quote `epsilon_report.rendered[key]` |
| `== 10` wall | `tests/test_phase21_sc5.py:189-197` (regex over `tests/`, comments included) | do not write `== 10` / `!= 10` |
| `train_arm(` | `tests/test_phase23_resume.py:60-77` `_TRAIN_ARM_CALL_SITES` (prose counts) | do not write the token `train_arm(` even in docstrings |
| `normalized` register | `tests/test_phase25_correction.py:375-395` | add new guard files to `_EARLIER_GUARD_FILES` |
| heading prefix | `tests/test_phase18_docs.py:210-254, 354-379` | REPORT section at EOF; README bullets add no `## ` |
| clean tree | `tests/test_phase25_frontier.py:123` `git status --porcelain results/`; `tests/test_phase25_grid.py:646` over `tests/` | commit ledger + tests before the full suite |
| frontier one-commit | `tests/test_phase27_prereg.py:130` | never touch `results/phase25_frontier.json` |
| torch-free import probe | `tests/test_phase27_prereg.py:133-140` | renderer must import without torch; copy the probe for `phase28_report` |

### Dotted-path resolution (the contract's own shape)
**Source:** `scripts/phase25_prereg.py:414-477`, `scripts/phase26_prereg.py:352-395` (data), RESEARCH Pattern 1 (code)
**Apply to:** renderer bindings and the obligation test. Index with `[]`, never `.get()`; `KeyError` is the RED.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `scripts/phase28_report.md.tmpl` | template | transform input | No template renderer exists in the repo (`grep string.Template\|jinja\|format_map scripts/` -> none). Use `string.Template` `${...}` per RESEARCH; sentinel + `normalized` discipline from `tests/test_phase25_correction.py` is the closest governing precedent. |
| `results/phase28_ledger.json` | data record | batch | No hand-authored ledger exists; `results/phase20_gate_coverage_correction.json` shows only the prose-beside-data field style. Schema is D-28's. |

## Metadata

**Analog search scope:** `scripts/_prose.py`, `scripts/_addendum.py`, `scripts/phase25_prereg.py:410-515`, `scripts/phase26_prereg.py:348-396`, `tests/test_phase27_prereg.py:1-140`, `tests/test_package.py`, `tests/test_phase25_correction.py:1-60,95-225,360-440`, `tests/test_phase24_record.py:280-334`, `tests/test_phase18_docs.py:205-260,269-281,300-379,984-1063`, `tests/test_phase15_docs.py:335-429`, `tests/test_phase25_driver.py:341-385`, `tests/test_phase21_sc5.py:168-227`, `tests/test_phase23_resume.py:58-77`, `tests/test_phase20_correction.py:1415-1445`, `tests/test_perplexity.py:112-126`, `src/personacore/evaluation/perplexity.py:1-30`, `scripts/phase16_persistence.py:1598-1611`, `docs/REPORT.md` tail + headings, `README.md:105-150`, `.github/workflows/ci.yml:28`
**Files scanned:** 21
**Pattern extraction date:** 2026-09-20
