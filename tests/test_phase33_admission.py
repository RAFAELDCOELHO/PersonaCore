"""Plan 33-01: the Phase 33 admission driver, CPU-only and torch-free.

What this file proves:
- ``admit`` refuses in the order overwrite -> committed-at-HEAD-but-absent -> dirty, all before
  any digest; the dirty pathspec excludes exactly the record; the record is thin (D-04, D-06,
  D-13). Every admit-path test runs in a scratch git repo with ``_GIT_ROOT`` patched.
- every leg refuses on every non-ADMITTED reading, on an absent, untracked or staged-only record,
  and on a forged ADMITTED one, and its message on a MOOT record does not change with the commit
  (D-01, D-02).
- the limitation is bound from the record, never typed (D-08).
- the once-proofs (three-state, shallow-first), the provenance pins, the by-reference imports,
  the AR-32-02 census and the read-only git surface (ADMIT-01, ADMIT-02, D-05, D-07, D-12).
Nothing here writes under the real results/: a results/phase33_* file would start the ancestry
clock.
"""

import ast
import hashlib
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

import mitigation_budget  # noqa: E402  (scripts/ is not a package)
import phase25_run  # noqa: E402  (same)
import phase27_prereg  # noqa: E402  (same)
import phase29_prereg  # noqa: E402  (same)
import phase33_admission as driver  # noqa: E402  (same)

_DRIVER = _SCRIPTS / "phase33_admission.py"
_SHALLOW = (
    "shallow clone: commit history cannot be read, so this guard cannot tell 'once' from "
    "'never checked'. Set `fetch-depth: 0` on actions/checkout (see .github/workflows/ci.yml)."
)

_ADMITTED = phase29_prereg.VERDICTS[0]
_READINGS = (*phase29_prereg.VERDICTS[1:], "absent")
_LEG_NAMES = tuple(sub for sub, _req in driver.LEGS)
_REFUSAL_CASES = [(leg, reading) for leg in _LEG_NAMES for reading in _READINGS]


def _git(*args, cwd=_ROOT):
    return subprocess.run(
        ("git", *args), cwd=cwd, capture_output=True, text=True, check=True
    ).stdout.strip()


@pytest.fixture(autouse=True)
def _real_results_untouched():
    """Pitfall 4: every test ends with the real results/phase33_* status unchanged."""
    before = _git("status", "--porcelain", "--", "results/phase33_*")
    yield
    assert _git("status", "--porcelain", "--", "results/phase33_*") == before


@pytest.fixture
def scratch(tmp_path, monkeypatch):
    """A scratch repo holding the real frontier bytes, committed; ``_GIT_ROOT`` points at it."""
    repo = tmp_path.resolve() / "repo"
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    for key, value in (("user.email", "t@example.com"), ("user.name", "t")):
        _git("config", key, value, cwd=repo)
    frontier = repo / driver.FRONTIER_PATH
    frontier.parent.mkdir(parents=True)
    frontier.write_bytes((_ROOT / driver.FRONTIER_PATH).read_bytes())
    _git("add", "--", driver.FRONTIER_PATH, cwd=repo)
    _git("commit", "-q", "-m", "frontier", cwd=repo)
    monkeypatch.setattr(driver, "_GIT_ROOT", repo)
    return repo


def _commit_count(repo):
    return int(_git("rev-list", "--count", "HEAD", cwd=repo))


def _forge(path, verdict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"admission": {"verdict": verdict}}), encoding="utf-8")
    return path


def _refusal(argv):
    with pytest.raises(SystemExit) as excinfo:
        driver.main(argv)
    return str(excinfo.value)


def _never(name):
    def _fail(*_a, **_k):
        pytest.fail(f"{name} was called past a refusal")

    return _fail


# ===== admit: refusal order (D-06, D-13) =====


def test_admit_refuses_to_overwrite_before_anything_else(scratch, monkeypatch):
    monkeypatch.setattr(driver, "refuse_if_dirty", _never("refuse_if_dirty"))
    monkeypatch.setattr(phase29_prereg, "admission", _never("admission"))
    record = scratch / driver.RECORD_PATH
    record.write_text("{}", encoding="utf-8")

    message = _refusal(["admit"])

    assert "REFUSING" in message and "exists" in message, message
    assert record.read_text(encoding="utf-8") == "{}"


def test_admit_refuses_a_tracked_but_absent_record_before_the_dirty_check(scratch, monkeypatch):
    rel = driver.RECORD_PATH
    record = scratch / rel
    record.write_text("{}", encoding="utf-8")
    _git("add", "--", rel, cwd=scratch)
    _git("commit", "-q", "-m", "record", cwd=scratch)
    monkeypatch.setattr(driver, "refuse_if_dirty", _never("refuse_if_dirty"))
    monkeypatch.setattr(phase29_prereg, "admission", _never("admission"))

    # (a) a plain unlink
    record.unlink()
    assert "tracked but absent" in _refusal(["admit"])

    # (b) a staged deletion: the index and the pathspec both read it as gone, HEAD does not
    _git("checkout", "--", rel, cwd=scratch)
    _git("rm", "-q", "--", rel, cwd=scratch)
    assert _git("ls-files", "--", rel, cwd=scratch) == ""
    assert _git("status", "--porcelain", "--", *driver.DIRTY_PATHSPEC, cwd=scratch) == ""
    message = _refusal(["admit"])
    assert "tracked but absent" in message and "REFUSING" in message, message
    assert not record.exists()


def test_admit_refuses_a_dirty_tree_before_any_digest(scratch, monkeypatch):
    calls = []

    def _dirty(**kwargs):
        calls.append(kwargs)
        raise SystemExit("[provenance] dirty")

    monkeypatch.setattr(driver, "refuse_if_dirty", _dirty)
    monkeypatch.setattr(phase29_prereg, "admission", _never("admission"))

    with pytest.raises(SystemExit):
        driver.admit()

    assert [c["pathspec"] for c in calls] == [driver.DIRTY_PATHSPEC]
    assert calls[0]["cwd"] == scratch
    assert not (scratch / driver.RECORD_PATH).exists()


def test_dirty_pathspec_excludes_only_the_untracked_record(scratch):
    def _check():
        return driver.refuse_if_dirty(
            who="test", detail="d", pathspec=driver.DIRTY_PATHSPEC, cwd=scratch
        )

    (scratch / driver.RECORD_PATH).write_text("{}", encoding="utf-8")
    assert _check() == ""

    sibling = scratch / "results" / "phase33_x.json"
    sibling.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit):
        _check()


def test_admit_writes_the_thin_record_once_in_a_scratch_repo(scratch, capsys):
    before = _commit_count(scratch)
    driver.admit()
    raw = (scratch / driver.FRONTIER_PATH).read_bytes()
    blob = json.loads((scratch / driver.RECORD_PATH).read_text(encoding="utf-8"))

    assert set(blob) == {"admission", "scope", "frontier", "provenance", "limitation"}
    live = phase29_prereg.admission(json.loads(raw))
    assert blob["admission"] == json.loads(json.dumps(live))
    assert blob["scope"] == json.loads(json.dumps(phase29_prereg.relearning_scope(live)))
    assert blob["frontier"]["sha256"] == driver.hashlib.sha256(raw).hexdigest()
    assert blob["frontier"]["bytes"] == len(raw)
    assert blob["frontier"]["path"] == driver.FRONTIER_PATH
    assert blob["provenance"]["prereg_committed"] == phase29_prereg.COMMITTED
    assert _commit_count(scratch) == before
    assert _git("ls-files", "--", driver.RECORD_PATH, cwd=scratch) == ""
    assert capsys.readouterr().out.rstrip().endswith("(NOT committed; D-05 developer review first)")

    assert "exists" in _refusal(["admit"])
    assert _commit_count(scratch) == before


# ===== the legs: a refusal surface only (D-01, D-02) =====


@pytest.mark.parametrize(
    ("leg", "reading"),
    _REFUSAL_CASES,
    ids=[f"{leg}-{reading}" for leg, reading in _REFUSAL_CASES],
)
def test_each_leg_refuses_unless_admitted(tmp_path, leg, reading):
    record = tmp_path / "record.json"
    if reading != "absent":
        _forge(record, reading)

    message = _refusal([leg, "--record", str(record)])

    assert "REFUSING" in message, message
    assert reading in message, message
    assert sorted(p.name for p in tmp_path.iterdir()) == (
        [] if reading == "absent" else [record.name]
    )


def test_each_leg_refuses_unless_admitted_even_on_a_forged_admitted_record(tmp_path):
    record = _forge(tmp_path / "record.json", _ADMITTED)
    for leg in _LEG_NAMES:
        message = _refusal([leg, "--record", str(record)])
        assert "REFUSING" in message and "were not built" in message, message
    assert [p.name for p in tmp_path.iterdir()] == [record.name]


def test_a_leg_refuses_unless_admitted_on_an_untracked_record_in_a_scratch_repo(scratch):
    rel = driver.RECORD_PATH
    _forge(scratch / rel, _ADMITTED)
    for leg in _LEG_NAMES:
        message = _refusal([leg])
        assert "not tracked" in message and "REFUSING" in message, message

    _git("add", "--", rel, cwd=scratch)  # staged, not committed: HEAD still lacks it
    for leg in _LEG_NAMES:
        assert "not tracked" in _refusal([leg])


def test_the_leg_message_is_identical_before_and_after_the_commit(scratch):
    rel = driver.RECORD_PATH
    _forge(scratch / rel, phase29_prereg.VERDICTS[1])
    before = {leg: _refusal([leg]) for leg in _LEG_NAMES}
    _git("add", "--", rel, cwd=scratch)
    _git("commit", "-q", "-m", "record", cwd=scratch)
    after = {leg: _refusal([leg]) for leg in _LEG_NAMES}

    assert before == after
    assert all(phase29_prereg.VERDICTS[1] in m for m in after.values())


# ===== the limitation (D-08) =====


def _frontier():
    return json.loads((_ROOT / driver.FRONTIER_PATH).read_text(encoding="utf-8"))


def test_the_limitation_is_bound_from_the_record_not_typed(tmp_path):
    frontier = _frontier()
    result = phase29_prereg.admission(frontier)
    scope = phase29_prereg.relearning_scope(result)
    tallies = frontier["verdicts"]["tallies_by_leg"]
    own_leg, measured_leg = phase29_prereg.ADVR_ARMS[1], phase29_prereg.ADVR_ARMS[0]

    lim = driver.limitation(result, frontier, scope)
    own = [r for r in result["reasons"] if r.startswith(f"{own_leg} ")]
    assert own and lim["legs"][own_leg] == own[0]
    line = lim["legs"][measured_leg]
    for key, n in tallies[measured_leg].items():
        assert f"{n} {key}" in line, (key, line)
    assert f"of {sum(tallies[measured_leg].values())}" in line
    assert lim["scope_rule"] == scope["rule"]
    text = json.dumps(lim)
    for banned in ("never exercised", "apparatus built", "mitigation held"):
        assert banned not in text

    # natural binding: perturb one count per key; a template that dropped the key would not move
    perturbed_lines = set()
    for key in ("INCONCLUSIVE", "REFUSED"):
        copy = _frontier()
        copy["verdicts"]["tallies_by_leg"][measured_leg][key] += 1
        path = tmp_path / f"frontier_{key}.json"
        path.write_text(json.dumps(copy), encoding="utf-8")
        reread = json.loads(path.read_text(encoding="utf-8"))
        perturbed_lines.add(driver.limitation(result, reread, scope)["legs"][measured_leg])
    assert line not in perturbed_lines and len(perturbed_lines) == 2


def test_every_leg_names_one_relrn_requirement():
    requirements = [req for _sub, req in driver.LEGS]
    assert set(requirements) == {"RELRN-06", "RELRN-07", "RELRN-08", "RELRN-09"}
    assert len(requirements) == len(set(requirements)) == len(driver.LEGS)


# ===== called exactly once, pinned both ways (ADMIT-02, D-07) =====


def _assert_not_shallow():
    assert _git("rev-parse", "--is-shallow-repository") == "false", _SHALLOW


def test_the_record_was_committed_exactly_once_alone():
    _assert_not_shallow()
    record = driver.RECORD_PATH
    tracked = _git("ls-files", "--", record).split()
    commits = _git("log", "--format=%H", "--", record).split()
    if not (_ROOT / record).exists():
        assert not tracked and not commits, "record absent from disk but known to git"
        return
    if not tracked:  # D-05 review checkpoint: written, not yet committed
        assert commits == [], "an untracked record has history — it was deleted after a commit"
        return
    assert len(commits) == 1, commits
    touched = _git("show", "--name-only", "--format=", commits[0]).split()
    assert touched == [record], touched


def test_the_record_is_pinned_to_the_frontier_both_ways():
    _assert_not_shallow()
    record, frontier_path = driver.RECORD_PATH, driver.FRONTIER_PATH
    frontier_commits = _git("log", "--format=%H", "--", frontier_path).split()
    assert len(frontier_commits) == 1, frontier_commits
    tracked = _git("ls-files", "--", record)
    if not (_ROOT / record).exists():
        assert not tracked, f"{record} is tracked but absent from the working tree"
        return
    blob = json.loads((_ROOT / record).read_text(encoding="utf-8"))
    raw = (_ROOT / frontier_path).read_bytes()
    assert blob["frontier"]["sha256"] == hashlib.sha256(raw).hexdigest()
    assert blob["frontier"]["bytes"] == len(raw)
    live = phase29_prereg.admission(json.loads(raw))
    assert blob["admission"] == json.loads(json.dumps(live))
    assert blob["scope"] == json.loads(json.dumps(phase29_prereg.relearning_scope(live)))
    if tracked:
        record_commit = _git("log", "--format=%H", "--", record).split()[-1]
        subprocess.run(
            ("git", "merge-base", "--is-ancestor", frontier_commits[0], record_commit),
            cwd=_ROOT,
            check=True,
        )


def test_phase27_prereg_is_byte_unchanged():
    _assert_not_shallow()
    rel = pathlib.Path(phase27_prereg.__file__).resolve().relative_to(_ROOT).as_posix()
    assert len(_git("log", "--format=%H", "--", rel).split()) == 1
    assert subprocess.run(("git", "diff", "--quiet", "HEAD", "--", rel), cwd=_ROOT).returncode == 0


# ===== by reference, and the reach of admission() (ADMIT-01, D-03, D-04) =====


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


def test_the_contract_is_imported_by_reference():
    assert driver.phase29_prereg is phase29_prereg
    assert phase29_prereg.RATIO_GRID is mitigation_budget.ADVERSARIAL_RATIO_GRID
    tree = ast.parse(_DRIVER.read_text(encoding="utf-8"))
    docs = _docstring_nodes(tree)
    defined = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    assert not defined & {"admission", "relearning_scope", "recall_threshold"}, defined
    typed = [
        n.value
        for n in ast.walk(tree)
        if isinstance(n, ast.Constant)
        and n.value in (driver.RECORD_PATH, driver.FRONTIER_PATH)
        and id(n) not in docs
    ]
    assert typed == []


def _trace_admission():
    """``(file, function)`` for every Python call under scripts/ during admission + scope."""
    frontier = json.loads((_ROOT / driver.FRONTIER_PATH).read_text(encoding="utf-8"))
    scripts = str(_SCRIPTS) + "/"
    calls = set()

    def _profile(frame, event, _arg):
        if event == "call" and frame.f_code.co_filename.startswith(scripts):
            rel = pathlib.Path(frame.f_code.co_filename).relative_to(_ROOT).as_posix()
            calls.add((rel, frame.f_code.co_name))

    sys.setprofile(_profile)
    try:
        phase29_prereg.relearning_scope(phase29_prereg.admission(frontier))
    finally:
        sys.setprofile(None)
    return calls


def test_admission_reaches_recall_threshold():
    prereg = pathlib.Path(phase29_prereg.__file__).relative_to(_ROOT).as_posix()
    assert (prereg, "recall_threshold") in _trace_admission()


def test_provenance_trace_is_inside_the_pinned_modules():
    files = {rel for rel, _fn in _trace_admission()}
    assert files and files <= set(driver.PINNED_MODULES), files - set(driver.PINNED_MODULES)
    assert "scripts/mitigation_gate.py" in files


def test_provenance_digests_match_live_bytes():
    record = _ROOT / driver.RECORD_PATH
    if not record.exists():
        assert _git("ls-files", "--", driver.RECORD_PATH) == ""
        assert all((_ROOT / rel).is_file() for rel in driver.PINNED_MODULES)
        return
    pins = json.loads(record.read_text(encoding="utf-8"))["provenance"]["module_sha256"]
    assert set(pins) == set(driver.PINNED_MODULES)
    for rel, digest in pins.items():
        assert digest == hashlib.sha256((_ROOT / rel).read_bytes()).hexdigest(), rel


# ===== AR-32-02: no phase33 module reuses phase32_points (D-12) =====


def _phase32_points_imports(source):
    tree = ast.parse(source)
    docs = _docstring_nodes(tree)
    hits = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            hits += [
                f"import {a.name} at line {n.lineno}"
                for a in n.names
                if a.name == "phase32_points" or a.name.startswith("phase32_points.")
            ]
        elif isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] == "phase32_points":
            hits.append(f"from {n.module} import at line {n.lineno}")
        elif isinstance(n, ast.Constant) and n.value == "phase32_points" and id(n) not in docs:
            hits.append(f"string 'phase32_points' at line {n.lineno} (importlib/sys.modules)")
    return [f"{h} — AR-32-02 (32-SECURITY.md): fix CR-01/WR-01/WR-05 first" for h in hits]


def test_no_phase33_module_imports_phase32_points(tmp_path):
    modules = sorted(_SCRIPTS.glob("phase33_*.py"))
    assert modules, "census blind: no scripts/phase33_*.py"
    for path in modules:
        assert _phase32_points_imports(path.read_text(encoding="utf-8")) == [], path

    # natural RED: an existing importer, copied
    natural = tmp_path / "natural.py"
    natural.write_text(
        (_ROOT / "tests/test_phase32_points.py").read_text(encoding="utf-8"), encoding="utf-8"
    )
    hits = _phase32_points_imports(natural.read_text(encoding="utf-8"))
    assert hits and all("AR-32-02" in h for h in hits), hits

    # no natural occurrence of these two forms exists anywhere, so they are tmp-copy plants
    driver_source = _DRIVER.read_text(encoding="utf-8")
    for name, plant in (
        ("from_import.py", "\nfrom phase32_points import emit\n"),
        ("importlib.py", '\nimport importlib\n_P = importlib.import_module("phase32_points")\n'),
    ):
        planted = tmp_path / name
        planted.write_text(driver_source + plant, encoding="utf-8")
        hits = _phase32_points_imports(planted.read_text(encoding="utf-8"))
        assert len(hits) == 1 and "AR-32-02" in hits[0], (name, hits)


def test_phase33_imports_neither_phase32_points_nor_torch():
    probe = (
        "import sys; sys.path.insert(0, 'scripts'); import phase33_admission; "
        "print('phase32_points' in sys.modules, 'torch' in sys.modules)"
    )
    out = subprocess.run(
        [sys.executable, "-c", probe], cwd=_ROOT, capture_output=True, text=True, check=True
    )
    assert out.stdout.split() == ["False", "False"], out.stdout


# ===== admit never commits: the git surface is read-only (D-05) =====


def _enclosing_function(tree, node):
    """The innermost ``FunctionDef`` lexically containing ``node``, or ``'<module>'``."""
    best = None
    for candidate in ast.walk(tree):
        if not isinstance(candidate, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if candidate.lineno <= node.lineno <= candidate.end_lineno:
            if best is None or candidate.lineno > best.lineno:
                best = candidate
    return best.name if best is not None else "<module>"


def _git_argv_subcommands(path):
    """Every ``(subcommand, lineno, enclosing_function)`` of a ``["git", ...]`` literal."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.List, ast.Tuple)) or not node.elts:
            continue
        first = node.elts[0]
        if not (isinstance(first, ast.Constant) and first.value == "git"):
            continue
        for element in node.elts[1:]:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                found.append((element.value, element.lineno, _enclosing_function(tree, element)))
                break
    return found


def test_the_drivers_git_surface_is_read_only(tmp_path):
    found = _git_argv_subcommands(_DRIVER)
    assert all(sub in phase25_run.READ_ONLY_GIT_ACTIONS for sub, _lineno, _fn in found), found
    assert [(sub, fn) for sub, _lineno, fn in found] == [("rev-parse", "_committed")]

    planted = tmp_path / "phase33_admission_planted.py"
    planted.write_text(
        _DRIVER.read_text(encoding="utf-8")
        + '\n\ndef _planted():\n    subprocess.run(["git", "add", "x"])\n',
        encoding="utf-8",
    )
    offenders = [
        (sub, fn)
        for sub, _lineno, fn in _git_argv_subcommands(planted)
        if sub not in phase25_run.READ_ONLY_GIT_ACTIONS
    ]
    assert offenders == [("add", "_planted")]
