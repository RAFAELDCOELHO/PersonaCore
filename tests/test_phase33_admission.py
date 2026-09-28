"""Plan 33-01: the Phase 33 admission driver, CPU-only and torch-free.

What this file proves:
- ``admit`` refuses in the order overwrite -> committed-at-HEAD-but-absent -> dirty, all before
  any digest; the dirty pathspec excludes exactly the record; the record is thin (D-04, D-06,
  D-13). Every admit-path test runs in a scratch git repo with ``_GIT_ROOT`` patched.
- every leg refuses on every non-ADMITTED reading, on an absent, untracked or staged-only record,
  and on a forged ADMITTED one, and its message on a MOOT record does not change with the commit
  (D-01, D-02).
- the limitation is bound from the record, never typed (D-08).
Nothing here writes under the real results/: a results/phase33_* file would start the ancestry
clock.
"""

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
import phase33_admission as driver  # noqa: E402  (same)

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
