# Phase 33: Admission and Relearning on Admitted Points - Pattern Map

**Mapped:** 2026-09-28
**Files analyzed:** 6 (1 new module, 1 new test file, 1 new record, 3 hand-edited planning files)
**Analogs found:** 6 / 6

## PINNED ANALOGS — READ, NEVER EDIT

Every analog below that is a script is hashed into a committed `results/*.json` `module_sha256`
(measured with `grep -l "<name>.py" results/*.json`). Copy their patterns into the NEW files only.

| Analog | Pinned in |
|--------|-----------|
| `scripts/phase27_relearn.py` | `phase27_admission.json`, `phase28_ledger.json`, `phase31_probe_point.json`, `phase31_probe_relearn.json`, `phase31_budget.json` |
| `scripts/phase32_frontier.py` | `phase32_frontier.json` |
| `scripts/phase29_prereg.py` | `phase32_frontier.json`, `phase30_calibration.json`, `phase31_budget.json`, all 7 `phase32_point_*.json` (it is also THE pre-registration, D-03) |
| `scripts/phase27_prereg.py` | `phase27_admission.json`, `phase28_ledger.json` (must stay byte-unchanged, ADMIT-01) |
| `scripts/phase25_run.py` | `phase25_frontier.json`, 7 `phase32_point_*.json`, `phase31_probe_*.json` |
| `scripts/mitigation_gate.py` | 6 records incl. `phase32_frontier.json` |
| `src/personacore/provenance.py` | not pinned by path, but covered by every `git_sha`; no reason to edit |

Test analogs (`tests/test_phase27_relearn.py`, `tests/test_phase27_prereg.py`,
`tests/test_phase29_prereg.py`, `tests/test_phase30_points.py`) are not hashed, but the ancestry
guards in `test_phase29_prereg.py` already cover `results/phase33_*`. **Do not edit them.** Copy
their helpers into the new test file (RESEARCH Wave 0: "do not import test modules across files").

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `scripts/phase33_admission.py` | driver (CLI: `admit` + 4 refusal-only legs) | batch / file-I/O (read frontier → write-once record) | `scripts/phase32_frontier.py` (`emit`, `_GIT_ROOT`, derived paths, `PROVENANCE_MODULES`) + `scripts/phase27_relearn.py` (`admit`, `_require_admitted`, `build_parser`/`main`/`DISPATCH`) | exact (the union of the two) |
| `tests/test_phase33_admission.py` | test | request-response (argv → SystemExit) + git-history | `tests/test_phase27_relearn.py` (leg refusal, scratch repo, git surface), `tests/test_phase27_prereg.py` (pinned both ways, no-torch probe), `tests/test_phase29_prereg.py` (`_git`, shallow assert), `tests/test_phase30_points.py` (`_docstring_nodes`) | exact |
| `results/phase33_admission.json` | record (write-once artifact) | file-I/O | `results/phase27_admission.json` (thin-down per D-04) | role-match |
| `.planning/REQUIREMENTS.md` (ADMIT/RELRN checkboxes `:627-635`, traceability `:676-681`) | planning doc | hand edit | RELRN-02..05 rows at `:575-578` (wording shape, minus "apparatus built") | role-match |
| `.planning/ROADMAP.md` § Phase 33 | planning doc | hand edit | Phase 32 section | role-match |
| `.planning/STATE.md` | planning doc | hand edit | current file | role-match |

---

## Pattern Assignments

### `scripts/phase33_admission.py` (driver, write-once + refusal legs)

**Primary analog:** `scripts/phase32_frontier.py` (most recent write-once emitter, torch-free).
**Secondary analog:** `scripts/phase27_relearn.py` (the `admit` + leg shape this phase mirrors).

**Module docstring + import header** — copy `phase32_frontier.py:1-47` shape (two roots, sys.path
shims, `# noqa: E402` sibling imports, `INSTRUMENT_GIT_SHA` at import):
```python
# scripts/phase32_frontier.py:19-47
import argparse
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys

# Never patched: the code this file ships in (module hashes read it).
_ROOT = pathlib.Path(__file__).resolve().parent.parent
# Patchable: the results repository (tests patch it together with phase30_points._ROOT).
_GIT_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
_SRC = str(_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import phase20_gate_coverage  # noqa: E402  (scripts/ is not a package)
...
import phase29_prereg  # noqa: E402  (same)

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402

INSTRUMENT_GIT_SHA = git_sha()
```
Phase 33 imports: `mitigation_budget`, `mitigation_gate`, `phase25_prereg`, `phase25_record`,
`phase25_run`, `phase27_prereg`, `phase29_prereg`. **Never** `phase32_points` (D-12) and never
`phase30_points` (not needed; `phase32_frontier` needed it only for `_tracked_json`).

**Paths derived, never typed** — `phase32_frontier.py:49-55`:
```python
FRONTIER_PATH = next(
    p for p in phase29_prereg.V5_RESULT_PATHS if p.startswith("results/phase32_frontier")
)
```
Phase 33 adds `RECORD_PATH = next(p for p in phase29_prereg.V5_RESULT_PATHS if
p.startswith("results/phase33_admission"))` (the tuple at `phase29_prereg.py:148-158` contains
`"results/phase33_admission.json"` AND `"results/phase33_*"` — `startswith("results/phase33_admission")`
matches only the first). Expose `DIRTY_PATHSPEC = ("scripts", "src", "results",
f":(exclude){RECORD_PATH}")` as a module constant (RESEARCH Finding 2).

**Provenance module tuple derived from `__file__`** — `phase32_frontier.py:63-72`:
```python
PROVENANCE_MODULES = tuple(
    pathlib.Path(path).resolve().relative_to(_ROOT).as_posix()
    for path in (
        __file__,
        phase25_verdict.__file__,
        ...
        phase29_prereg.__file__,
    )
)
```
Phase 33 set (RESEARCH Finding 1, traced): `__file__`, `phase29_prereg`, `mitigation_gate`,
`mitigation_budget`, `phase27_prereg`, `phase25_record`, `phase25_prereg`. Do NOT copy
phase27_relearn's hand-typed string tuple (`phase27_relearn.py:59-67`) — that is the anti-pattern.

**`_prove` / `_sha256` / `_rel` helpers** — `phase32_frontier.py:75-78` and
`phase27_relearn.py:101-124`:
```python
def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase32_frontier] {message}")

def _sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()

def _rel(path):
    """Repo-relative when inside the root; the path as given otherwise (tests use tmp dirs)."""
    path = pathlib.Path(path)
    return str(path.relative_to(_ROOT)) if path.is_relative_to(_ROOT) else str(path)
```
Phase 33: prefix `[phase33_admission]`; `_rel` against `_GIT_ROOT` (the patchable root).

**Write-once `admit`** — `phase32_frontier.py:496-552` (order + relative→`_GIT_ROOT` resolution +
review print) and `phase27_relearn.py:361-412` (pathspec excluding the record, provenance block):
```python
# scripts/phase32_frontier.py:496-514
def emit(out_path=FRONTIER_PATH):
    """Write-once: overwrite refusal FIRST, dirty tree SECOND, then all 12 records tracked."""
    out_path = pathlib.Path(out_path)
    if not out_path.is_absolute():
        out_path = _GIT_ROOT / out_path
    _prove(
        not out_path.exists(),
        f"{out_path} exists — REFUSING to overwrite it. The frontier is write-once; corrections "
        "are dated continuations",
    )
    refuse_if_dirty(
        who="phase32_frontier",
        detail=(
            "the frontier publishes git_sha and hashes its route modules from the working tree; a "
            "record written from a dirty tree names a commit it cannot be regenerated from"
        ),
        pathspec=("scripts", "src", "results", f":(exclude){FRONTIER_PATH}"),
        cwd=_GIT_ROOT,
    )
```
```python
# scripts/phase32_frontier.py:533-552 (provenance + atomic write + review print, never commits)
    frontier["provenance"] = {
        "module_sha256": {rel: _sha256(_ROOT / rel) for rel in PROVENANCE_MODULES},
        "git_sha": INSTRUMENT_GIT_SHA,
        "head_at_write": git_sha(),
        "written_utc": _now(),
    }
    phase25_run.atomic_write_json(out_path, frontier)
    ...
        "admission": phase29_prereg.admission(frontier),
    }
    print(json.dumps(review, indent=1), flush=True)
    print(f"[phase32_frontier] wrote {out_path} (NOT committed; D-16 review first)", flush=True)
```
`phase27_relearn.py:398-405` adds `"prereg_committed": phase27_prereg.COMMITTED` → Phase 33 uses
`phase29_prereg.COMMITTED` (`= "2026-09-24"`, `phase29_prereg.py:67`). Drop `torch_version`
(module is torch-free). Drop `--force` / `overwrite=` entirely (D-06 — differs from
`phase27_relearn.py:371-377`).

**Deviations from the analogs (D-06, D-13):**
1. Refusal order: overwrite → **tracked-but-absent** (new; `git ls-files RECORD_PATH` non-empty
   while `not exists()`) → `refuse_if_dirty(pathspec=DIRTY_PATHSPEC, cwd=_GIT_ROOT)` → frontier
   tracked → digests. All before any `_sha256`.
2. Frontier bytes read once: `raw = (_GIT_ROOT / FRONTIER_PATH).read_bytes()`; record
   `{"path", "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}`.
3. `result = phase29_prereg.admission(json.loads(raw))`; `scope =
   phase29_prereg.relearning_scope(result)` (`phase29_prereg.py:649-664` — SystemExits on
   INCONCLUSIVE, which is correct). Carry both whole: `blob["admission"] = result` (never spell a
   bare `"control_readings"` — see Shared Patterns / censuses). The review print may use the dict
   literal key `"control_readings": result["control_readings"]` — that form is allowed
   (`phase32_frontier.py:543` does exactly this).
4. Limitation (D-08): lines bound from `result["reasons"]` + frontier
   `["verdicts"]["tallies_by_leg"]["advr_n8"]` + `scope["rule"]`; no hand-typed numerals, no
   "never exercised" / "apparatus built".

**`admission()` reference read** — `phase29_prereg.py:637-664` (the scope rule, reused by the
leg message):
```python
SCOPE_RULE = {
    "ADMITTED": "run RELRN-06..09 on each of admitted_point_keys",
    "MOOT": "RELRN-06..09 ship as a MOOT named limitation",
    REFUSED: "RELRN-06..09 ship as a named limitation: the frontier could not be measured",
    CANDIDATE_UNREPLICATED: (...),
    "INCONCLUSIVE": "refuse to proceed: the frontier record is malformed",
}
```

**Leg guard** — `phase27_relearn.py:131-173` (`_require_admitted`):
```python
def _require_admitted(record_path=RECORD):
    path = pathlib.Path(record_path).resolve()
    _prove(
        path.exists(),
        f"{_rel(path)} is absent — REFUSING to run this leg: run `admit` first; every leg is "
        "gated on the COMMITTED record",
    )
    blob = admission(path)
    read = blob["verdict"]["verdict"]
    ...
    _prove(
        read == "ADMITTED",
        f"{_rel(path)} reads {read!r} — REFUSING to run this leg: nothing is admitted "
        f"({reasons[0]})",
    )
    ...
    if path.is_relative_to(_ROOT):
        tracked = subprocess.run(
            ["git", "ls-files", _rel(path)],
            cwd=_ROOT, capture_output=True, text=True, check=True,
        ).stdout.split()
        _prove(
            tracked,
            f"{_rel(path)} is not tracked — REFUSING: a leg runs only against the COMMITTED "
            "record, never a live re-read",
        )
    return blob
```
Phase 33 deviations: record shape is `blob["admission"]["verdict"]` (not `blob["verdict"]["verdict"]`);
no baselines conjunct; `_prove(verdict in phase29_prereg.VERDICTS)`; message uses
`phase29_prereg.SCOPE_RULE[verdict]`; order **exists → verdict → tracked → unconditional
`raise SystemExit(... "v5.0 relearning apparatus was not built" ... "admission read MOOT" ...)`**
(RESEARCH Pattern 2 — verdict before tracked keeps before/after-commit stderr byte-identical,
D-02). No HEAD sha, time, or absolute tmp path in any message. Never returns.

**CLI** — `phase27_relearn.py:1155-1208` (`SUB_MODES`, `DISPATCH`, `build_parser`, `main`):
```python
SUB_MODES = ("admit", "calibrate", "curve", "gate", "structural-proof")   # :70
DISPATCH = {"admit": admit, "calibrate": run_calibrate, ...}               # :1155

def build_parser():
    parser = argparse.ArgumentParser(description=...)
    sub = parser.add_subparsers(dest="mode", required=True)
    admit_parser = sub.add_parser("admit", help="write results/phase27_admission.json once")
    admit_parser.add_argument("--force", action="store_true", ...)   # DROP in Phase 33 (D-06)
    admit_parser.add_argument("--out", default=str(RECORD))
    for mode in SUB_MODES[1:]:
        leg_parser = sub.add_parser(mode, help=f"the {mode} leg — refuses unless ADMITTED")
        leg_parser.add_argument("--record", default=str(RECORD))
        ...

def main(argv=None):
    args = build_parser().parse_args(argv)
    ...
    DISPATCH[args.mode](**kwargs)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```
Phase 33: legs take only `--record`; a module tuple maps leg → RELRN id (D-16), e.g.
`LEGS = (("calibrate", ...), ("curve", "RELRN-06"), ("gate", "RELRN-07"), ("structural-proof",
"RELRN-08"), ...)` — planner fixes the exact mapping; RELRN-09 (disjoint fixture) must be named
by some leg. No `--leg`/`--out-dir`/`--baseline` (nothing runs).

**Git surface:** only `["git", "ls-files", ...]` argv literals (the `admit` tracked-but-absent
check and the leg tracked conjunct) — both in `phase25_run.READ_ONLY_GIT_ACTIONS =
("ls-files", "show", "rev-parse", "status")` (`phase25_run.py:753`). `refuse_if_dirty` runs
`status` inside `provenance.py`, not in this module.

---

### `tests/test_phase33_admission.py` (test)

**Header / imports** — `tests/test_phase29_prereg.py:17-58` (no torch import, unlike
`test_phase27_relearn.py:30`):
```python
import ast
import json
import pathlib
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

import phase29_prereg  # noqa: E402  (scripts/ is not a package)

def _git(*args):
    """Run git inside the repository and return its stdout, raising on a non-zero exit."""
    return subprocess.run(
        ("git", *args), cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
```

**Shallow-first assert** — copy the message from `tests/test_phase29_prereg.py:73-77`:
```python
    assert _git("rev-parse", "--is-shallow-repository") == "false", (
        "shallow clone: the pre-registration commit objects are absent, so this guard cannot "
        "distinguish 'the ordering holds' from 'the ordering was never checked'. "
        "Set `fetch-depth: 0` on actions/checkout (see .github/workflows/ci.yml)."
    )
```
Put it first in EVERY git-history test (D-07; `test_phase27_prereg.py:118` lacks it — do not copy
that omission).

**Pinned both ways (D-07 part 3)** — `tests/test_phase27_prereg.py:118-131`:
```python
def test_the_record_is_pinned_to_the_frontier_both_ways():
    tracked = _git("ls-files", RECORD)
    if (_ROOT / RECORD).exists():
        blob = json.loads((_ROOT / RECORD).read_text(encoding="utf-8"))
        frontier_bytes = (_ROOT / FRONTIER).read_bytes()
        assert blob["frontier_sha256"] == hashlib.sha256(frontier_bytes).hexdigest()
        assert blob["frontier_bytes"] == (_ROOT / FRONTIER).stat().st_size
        added = _git("log", "--diff-filter=A", "--format=%H", "--", RECORD)
        assert bool(tracked) == bool(added)
    else:
        assert not tracked, f"{RECORD} is tracked but absent from the working tree"
    # BOTH states: a re-emitted frontier reddens Phase 27 by construction (T-27-03).
    assert len(_git("log", "--oneline", "--", FRONTIER).splitlines()) == 1
```
Phase 33: fields nest under `blob["frontier"]["sha256"/"bytes"]`; RECORD/FRONTIER taken from the
driver module's derived constants; add shallow assert first, three states (absent /
written-untracked / committed), `merge-base --is-ancestor` frontier→record in the committed state,
and live re-derivation `json.loads(json.dumps(phase29_prereg.admission(frontier))) ==
blob["admission"]` (+ scope). Single-commit test: use RESEARCH Finding 5's
`test_the_record_was_committed_exactly_once_alone` body verbatim.

**Leg refusal parametrised (D-02)** — `tests/test_phase27_relearn.py:55-58, 119-163`:
```python
_LEG_MODES = ("calibrate", "curve", "gate", "structural-proof")
_REFUSAL_CASES = [
    (mode, reading) for mode in _LEG_MODES for reading in ("MOOT", "INCONCLUSIVE", "absent")
]

def _forge(directory, verdict, **kw):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "phase27_admission.json"
    path.write_text(json.dumps(_record(verdict, **kw)), encoding="utf-8")
    return path

@pytest.mark.parametrize(
    ("mode", "verdict"),
    _REFUSAL_CASES,
    ids=[f"{mode}-{verdict}" for mode, verdict in _REFUSAL_CASES],
)
def test_each_leg_refuses_unless_admitted(tmp_path, monkeypatch, mode, verdict):
    ...
    with pytest.raises(SystemExit) as excinfo:
        relearn.main(argv)
    message = str(excinfo.value)
    assert "REFUSING" in message, message
    assert verdict in message, message
```
Phase 33: `_LEG_MODES` read from the driver's tuple (not retyped); readings
`("MOOT", phase29_prereg.REFUSED, phase29_prereg.CANDIDATE_UNREPLICATED, "INCONCLUSIVE",
"absent")` + a separate forged-ADMITTED case (tmp_path, outside repo → tracked conjunct skipped
→ must still refuse with the "not built" message). Forged record shape:
`{"admission": {"verdict": v, "reasons": [...], "admitted_point_keys": [...]}}`. No monkeypatch
stubs needed (no body); assert `tmp_path` holds only the forged file.

**Untracked inside a scratch repo** — `tests/test_phase27_relearn.py:182-210`:
```python
    scratch = tmp_path.resolve() / "repo"
    subprocess.run(["git", "init", "-q", "-b", "main", str(scratch)], check=True)
    for key, value in (("user.email", "t@example.com"), ("user.name", "t")):
        subprocess.run(["git", "-C", str(scratch), "config", key, value], check=True)
    (scratch / "results").mkdir()
    monkeypatch.setattr(relearn, "_ROOT", scratch)
    ...
    assert "not tracked" in str(excinfo.value) and "REFUSING" in str(excinfo.value)
    ...
    assert _git("status", "--porcelain", "--", "results/phase27_*").strip() == ""
```
Phase 33: patch `_GIT_ROOT` (not `_ROOT`). Reuse the same scratch-repo scaffold for the D-06
pathspec tests (record untracked → `refuse_if_dirty(pathspec=DIRTY_PATHSPEC, cwd=scratch)` returns
`""`; sibling untracked `results/phase33_x.json` → SystemExit) and the D-13 tracked-but-absent
refusal (commit record in scratch, `unlink`, `admit` refuses before dirty). End-of-test assert the
real `results/phase33_*` porcelain is unchanged.

**Git surface read-only** — `tests/test_phase27_relearn.py:507-545` (`_git_argv_subcommands` +
`test_the_drivers_git_surface_is_read_only`, with the planted `git add` natural non-vacuity
copy in `tmp_path`). Copy verbatim, including `_enclosing_function` (lines just above 507);
expected list becomes the `ls-files` sites in Phase 33's own functions.

**Torch-free / no phase32_points import probe** — `tests/test_phase27_prereg.py:133-142`:
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
Phase 33: `import phase33_admission; print('phase32_points' in sys.modules, 'torch' in sys.modules)`.

**By-reference asserts (ADMIT-01)** — `tests/test_phase29_prereg.py:283-286`:
```python
    assert p.F_Y is mitigation_gate.F_Y
    assert p.RATIO_GRID is mitigation_budget.ADVERSARIAL_RATIO_GRID
```
Phase 33: `driver.phase29_prereg.SCOPE_RULE is phase29_prereg.SCOPE_RULE`, etc.; and the
`mitigation_budget` membership justification via `phase29_prereg.RATIO_GRID is
mitigation_budget.ADVERSARIAL_RATIO_GRID`.

**D-12 AST census docstring exemption** — `tests/test_phase30_points.py:590-604`:
```python
def _docstring_nodes(tree):
    """The first-statement string Expr of the Module and of every def/class: exempt prose."""
    owners = [tree] + [
        n
        for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    return {
        id(owner.body[0].value)
        for owner in owners
        if owner.body
        and isinstance(owner.body[0], ast.Expr)
        and isinstance(owner.body[0].value, ast.Constant)
        and isinstance(owner.body[0].value.value, str)
    }
```
Copy it; the matcher itself is RESEARCH "Code Examples → D-12 AST census". Natural RED source:
`tests/test_phase32_points.py:32` (`import phase32_points as p32`) copied into `tmp_path`.

**Ancestry (free, do not duplicate):** `tests/test_phase29_prereg.py:109-117`
(`test_phase29_prereg_is_frozen_before_every_v5_result`) already sweeps `results/phase33_*`
via `phase29_prereg.ARTIFACT_PATHSPECS` (`phase29_prereg.py:161`).

---

### `results/phase33_admission.json` (write-once record)

**Analog:** `results/phase27_admission.json` (1 line, compact JSON via
`phase25_run.atomic_write_json` → `json.dumps(blob, sort_keys=True)`), thinned per D-04.
Its `provenance.module_sha256` keys (hand-typed, 7 entries incl. torch-side modules) are the
shape to AVOID copying; Phase 33 derives its keys from `__file__` (see above).

Top-level keys (D-04): `admission` (verbatim result), `scope` (relearning_scope output),
`frontier` {path, sha256, bytes}, `provenance` {module_sha256, git_sha, head_at_write,
prereg_committed[, written_utc]}, `limitation`. Not carried: baselines, disjointness, budget,
rows. Produced only by `admit`; never by a test (fixtures in `tmp_path` / scratch repo).

---

### `.planning/REQUIREMENTS.md` / `ROADMAP.md` / `STATE.md` (hand edits)

**Analog wording:** `REQUIREMENTS.md:575-578` (RELRN-02..05 rows). Keep the `**NOT SATISFIED —
named limitation:**` lead; replace "apparatus built and guarded, never exercised" with
"admission read MOOT … only the refusal surface exists" (D-08/D-09), citing
`results/phase33_admission.json` and PREREG-02.

Targets (measured): checkboxes `REQUIREMENTS.md:627-635` (ADMIT-01/02, RELRN-06..09), status
cells `:676-681` (currently `Pending`). ADMIT ticks only after the record commit + D-02/D-07
proofs. Snapshot all three files before, diff after; zero `gsd-sdk` mutation handlers; then run
`.venv/bin/python scripts/phase28_report.py check` and
`pytest tests/test_phase28_report.py tests/test_phase28_prereg.py tests/test_phase25_correction.py -q`
(these read the planning files live).

---

## Shared Patterns

### Write-once record discipline
**Source:** `scripts/phase32_frontier.py:496-552`, `scripts/phase27_relearn.py:361-412`
**Apply to:** `admit`
Overwrite refusal → (Phase 33: tracked-but-absent) → `refuse_if_dirty` with record excluded →
digests → one `phase25_run.atomic_write_json` → print "(NOT committed; review first)". Never
`git add/commit`. Claude commits the record alone only after developer "approved".

### Dirty-tree refusal
**Source:** `src/personacore/provenance.py:46-79` (`refuse_if_dirty(*, who, detail, pathspec=(),
cwd=None)`) — untracked counts as dirty; `:(exclude)` supported; git failure raises.
**Apply to:** `admit` only.

### Atomic write
**Source:** `scripts/phase25_run.py:118` `atomic_write_json(path, blob)`.
**Constraint:** `tests/test_phase25_driver.py::test_os_replace_appears_only_in_the_two_phase25_writers`
forbids any new `os.replace`.

### Error handling
**Source:** `_prove(condition, message)` → `SystemExit(f"[<module>] {message}")`, never `assert`
(`phase32_frontier.py:75-78`). Every refusal message contains `REFUSING`.

### Repo-wide censuses the new files must pass (RESEARCH Finding 6)
- `_wr05_failures` (`tests/test_phase30_points.py`): no Name/Attribute `control_readings`; string
  `"control_readings"` only as dict-literal key or `x["control_readings"]` subscript.
- `test_no_v5_module_uses_the_accountant`: no `personacore.privacy*` / `phase25_epsilon`.
- `test_phase21_sc5`: no `== 10` anywhere in the new test file (comments included).
- No `pytest.skip`/`skipif` (ubuntu skip-count pin).
- Do not write `train_arm(`, `train_never_taught`, `inject_lora`, `retention_perplexity(`,
  `mitigation_point_verdict` anywhere in the new module (incl. docstrings for the first two).
- ruff: line-length 100, rules E, F, W, I.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| (none) | — | — | Every piece has a committed analog. Two parts are new logic with no in-repo precedent, specified in RESEARCH instead: the tracked-but-absent refusal (D-13, Finding 2) and the three-state single-commit test (Finding 5 code block). |

## Metadata

**Analog search scope:** `scripts/phase25_run.py`, `phase27_relearn.py`, `phase29_prereg.py`,
`phase32_frontier.py`, `src/personacore/provenance.py`, `tests/test_phase27_relearn.py`,
`test_phase27_prereg.py`, `test_phase29_prereg.py`, `test_phase30_points.py`, `results/*.json`
(pin census), `.planning/REQUIREMENTS.md`
**Files scanned:** 12
**Pattern extraction date:** 2026-09-28
