"""Plan 35-01: the v6.0 pre-registration skeleton and the PREREG-09 research it rests on.

What this file proves, CPU-only:
- the one-run audit port reproduces the two values printed in arXiv 2305.08846v1 (App. D p. 46,
  §7 p. 28) within the declared tolerance, holds the delta = 0, v = r closed form, and a dropped
  delta lands outside the tolerance;
- E3's accounting is basic composition BY REFERENCE, with SELECTION_ACCOUNTED False;
- the research note cites both sources with pages and its first add precedes every commit of
  scripts/phase35_prereg.py (ROADMAP P35 SC5), RED on a planted throwaway repo;
- every entry has exactly the four D-14 fields and none carries a proposer field (runtime + AST,
  RED on planted copies);
- the module imports without torch, and this file has zero skips.

It reads only tracked files and git history and writes nothing under results/. A shallow clone
FAILS, never skips.
"""

import ast
import math
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
_TESTS = str(_ROOT / "tests")
if _TESTS not in sys.path:
    sys.path.insert(0, _TESTS)

import mitigation_unit  # noqa: E402  (scripts/ is not a package)
import phase25_epsilon  # noqa: E402  (same)
import phase35_prereg  # noqa: E402  (same)

from test_phase29_prereg import _git, _planted  # noqa: E402  (underscore names only)

PREREG = "scripts/phase35_prereg.py"
NOTE = ".planning/research/V6-PREREG-09.md"


def _git_in(repo):
    """A git runner bound to `repo`; real-repo and throwaway-repo legs share one check body."""

    def run(*args, check=True):
        return subprocess.run(
            ("git", "-C", str(repo), *args), capture_output=True, text=True, check=check
        )

    return run


def _planted_repo(root, commits):
    """A throwaway repo under `root` (a tmp_path subdirectory): one commit per element of
    `commits`, each a list of (relpath, text) pairs."""
    root.mkdir(parents=True)
    run = _git_in(root)
    run("-c", "init.defaultBranch=main", "init", "-q")
    for index, files in enumerate(commits):
        for relpath, text in files:
            target = root / relpath
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        run("add", *(relpath for relpath, _ in files))
        run(
            "-c",
            "user.name=planted",
            "-c",
            "user.email=planted@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-q",
            "-m",
            f"step-{index}",
        )
    return run


def _insert_at(source, lineno, col_offset, text):
    """Insert `text` at an AST position (1-based line, UTF-8 byte column)."""
    lines = source.splitlines(keepends=True)
    raw = lines[lineno - 1].encode("utf-8")
    lines[lineno - 1] = (raw[:col_offset] + text.encode("utf-8") + raw[col_offset:]).decode("utf-8")
    return "".join(lines)


# =================================================================================================
# (1) THE ONE-RUN AUDIT BOUND (D-11).
# =================================================================================================


def _tolerance():
    return phase35_prereg.ENTRIES["one_run_tolerance"]["value"]


def test_one_run_reproduces_appendix_d_p46():
    pin = phase35_prereg.ONE_RUN_PUBLISHED["app_d_p46"]
    assert _tolerance() == 1e-3
    assert pin["inputs"] == (1000, 100, 75, 1e-4, 0.05)
    assert pin["published"] == 0.673
    assert abs(phase35_prereg.eps_lower_one_run(*pin["inputs"]) - pin["published"]) < _tolerance()


def test_one_run_reproduces_section7_p28():
    pin = phase35_prereg.ONE_RUN_PUBLISHED["sec7_p28"]
    assert _tolerance() == 1e-3
    assert pin["inputs"] == (100000, 1510, 1439, 1e-5, 0.05)
    assert pin["published"] == 2.675
    assert abs(phase35_prereg.eps_lower_one_run(*pin["inputs"]) - pin["published"]) < _tolerance()


def test_one_run_closed_form_at_delta_zero():
    expected = -math.log(0.05 ** (-1 / 16) - 1)
    assert abs(phase35_prereg.eps_lower_one_run(16, 16, 16, 0, 0.05) - expected) < 1e-8


def test_one_run_tolerance_cannot_absorb_a_dropped_delta():
    assert abs(phase35_prereg.eps_lower_one_run(1000, 100, 75, 0, 0.05) - 0.673) > _tolerance()


def test_one_run_reproduction_holds(monkeypatch):
    assert phase35_prereg.one_run_reproduction_holds() is True
    monkeypatch.setattr(phase35_prereg, "eps_lower_one_run", lambda *a: 0.0)
    assert phase35_prereg.one_run_reproduction_holds() is False


@pytest.mark.parametrize(
    "args",
    [
        (100, 50, 51, 1e-5, 0.05),  # v > r
        (100, 101, 50, 1e-5, 0.05),  # r > m
        (True, 1, 1, 1e-5, 0.05),  # m is a bool
        (100, 1.0, 1, 1e-5, 0.05),  # r is a float
        (100, 50, 40, 1e-5, 0),  # beta = 0
        (100, 50, 40, 1e-5, 1),  # beta = 1
        (100, 50, 40, -1e-5, 0.05),  # negative delta
        (100, 50, 40, True, 0.05),  # delta is a bool
    ],
)
def test_one_run_refuses_bad_inputs(args):
    with pytest.raises(SystemExit):
        phase35_prereg.eps_lower_one_run(*args)


def test_one_run_p_value_refuses_an_infinite_eps():
    with pytest.raises(SystemExit):
        phase35_prereg.p_value_one_run(100, 50, 40, float("inf"), 1e-5)


# =================================================================================================
# (2) E3 BASIC COMPOSITION, BY REFERENCE (D-12).
# =================================================================================================


def test_composition_is_basic_and_by_reference():
    assert phase35_prereg.CURVE_TOTAL is phase25_epsilon.curve_total
    assert phase35_prereg.SELECTION_ACCOUNTED is False
    assert phase35_prereg.SELECTION_ACCOUNTED is phase25_epsilon.SELECTION_ACCOUNTED
    assert phase35_prereg.DELTA is mitigation_unit.DELTA
    total = phase35_prereg.CURVE_TOTAL([1.5, 2.25, 0.25], delta=mitigation_unit.DELTA)
    assert total == (4.0, 3 * 1e-5)
    with pytest.raises(ValueError):
        phase35_prereg.CURVE_TOTAL([1.5, None], delta=mitigation_unit.DELTA)


# =================================================================================================
# (3) THE RESEARCH NOTE AND ITS ORDERING (D-10, PREREG-09, ROADMAP P35 SC5).
# =================================================================================================


def test_research_note_cites_both_sources_with_pages():
    note = _ROOT / NOTE
    assert note.is_file(), f"{NOTE} is missing"
    text = note.read_text(encoding="utf-8")
    for needed in (
        "2305.08846v1",
        "2110.03620v2",
        "Theorem 5.2",
        "Corollary 5.4",
        "Appendix D",
        "Theorem 2",
        "Theorem 6",
        "p. 46",
        "p. 28",
    ):
        assert needed in text, f"{NOTE} does not cite {needed!r}"
    assert "não verificado" not in text


def _note_ordering_failures(run, note, prereg):
    """Every commit touching `prereg` must have the note's first add as an ancestor (or be it)."""
    failures = []
    if run("rev-parse", "--is-shallow-repository").stdout.strip() != "false":
        failures.append("shallow clone: the ordering cannot be checked (fetch-depth: 0)")
    adds = run("log", "--diff-filter=A", "--format=%H", "--", note).stdout.split()
    if not adds:
        failures.append(f"{note} has no add commit: commit the note first")
    prereg_commits = run("log", "--format=%H", "--", prereg).stdout.split()
    if run("ls-files", prereg).stdout.strip() and not prereg_commits:
        failures.append(f"{prereg} is tracked but has no commit")
    pairs_checked = 0
    for commit in prereg_commits:
        pairs_checked += 1
        if not adds:
            continue
        if run("merge-base", "--is-ancestor", adds[-1], commit, check=False).returncode != 0:
            failures.append(f"{prereg} commit {commit} does not descend from {note}'s first add")
    return failures, pairs_checked


def test_research_note_precedes_every_prereg_commit():
    failures, pairs = _note_ordering_failures(_git_in(_ROOT), NOTE, PREREG)
    assert failures == []
    assert pairs == len(_git("log", "--format=%H", "--", PREREG).split())
    if _git("ls-files", PREREG):
        assert pairs >= 1


def test_research_note_ordering_reds_on_a_planted_repo(tmp_path):
    note, prereg = "note.md", "scripts/p.py"

    green = _planted_repo(tmp_path / "green", [[(note, "n")], [(prereg, "p")]])
    assert _note_ordering_failures(green, note, prereg) == ([], 1)

    reversed_order = _planted_repo(tmp_path / "reversed", [[(prereg, "p")], [(note, "n")]])
    failures, _ = _note_ordering_failures(reversed_order, note, prereg)
    assert failures

    never_added = _planted_repo(tmp_path / "never", [[(prereg, "p")]])
    failures, _ = _note_ordering_failures(never_added, note, prereg)
    assert any("commit the note first" in failure for failure in failures), failures


# =================================================================================================
# (4) ENTRIES: EXACTLY FOUR FIELDS, NO PROPOSER (D-07 as amended by D-14).
# =================================================================================================


def test_entries_have_exactly_the_four_fields():
    entries = phase35_prereg.ENTRIES
    assert entries
    for name, entry in entries.items():
        assert set(entry) == set(phase35_prereg.ENTRY_FIELDS)
        assert set(entry) == {"value", "derivation", "kind", "source"}, name
        assert entry["kind"] in ("derived", "preference"), name
        assert isinstance(entry["derivation"], str) and entry["derivation"].strip(), name
        assert isinstance(entry["source"], str) and entry["source"].strip(), name
    with pytest.raises(TypeError):
        entries["planted"] = {}


def _good_entry():
    return {"value": 1, "derivation": "d", "kind": "derived", "source": "s"}


def test_entries_refuse_an_unknown_kind_or_missing_field():
    phase35_prereg._prove_entry("ok", _good_entry())
    bad_kind = {**_good_entry(), "kind": "guess"}
    missing_source = {k: v for k, v in _good_entry().items() if k != "source"}
    empty_derivation = {**_good_entry(), "derivation": ""}
    for entry in (bad_kind, missing_source, empty_derivation):
        with pytest.raises(SystemExit):
            phase35_prereg._prove_entry("x", entry)


def _entries_node(tree):
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "_ENTRIES" for target in node.targets
        ):
            return node
    return None


_PROVENANCE_KEYS = ("proposer", "adopted_by")


def _entry_string_failures(source):
    tree = ast.parse(source)
    failures = []
    entries = _entries_node(tree)
    if entries is None:
        return ["no module-level _ENTRIES assignment"]
    for node in ast.walk(entries):
        if isinstance(node, ast.Dict):
            for key in node.keys:
                if isinstance(key, ast.Constant) and key.value in _PROVENANCE_KEYS:
                    failures.append(f"_ENTRIES key {key.value!r} at line {key.lineno}")
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and phase35_prereg.FORBIDDEN_PHRASE in node.value
        ):
            failures.append(f"forbidden phrase at line {node.lineno}")
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key in node.keys:
                if isinstance(key, ast.Constant) and key.value in _PROVENANCE_KEYS:
                    failures.append(f"module dict key {key.value!r} at line {key.lineno}")
    return failures


def _first_inner(entries, wanted_key):
    """(key node, value node) of the first inner-dict item keyed `wanted_key`, in source order."""
    found = []
    for node in ast.walk(entries.value):
        if isinstance(node, ast.Dict) and node is not entries.value:
            for key, value in zip(node.keys, node.values, strict=True):
                if isinstance(key, ast.Constant) and key.value == wanted_key:
                    found.append((key, value))
    assert found, f"no inner {wanted_key!r} key in _ENTRIES"
    return min(found, key=lambda pair: (pair[0].lineno, pair[0].col_offset))


def test_no_proposer_or_adopted_by_in_any_entry(tmp_path):
    for name, entry in phase35_prereg.ENTRIES.items():
        for banned in _PROVENANCE_KEYS:
            assert banned not in entry, name
    for banned in _PROVENANCE_KEYS:
        with pytest.raises(SystemExit) as refused:
            phase35_prereg._prove_entry("x", {**_good_entry(), banned: "Rafael"})
        assert banned in str(refused.value)

    real = _ROOT / PREREG
    before = real.read_bytes()
    source = before.decode("utf-8")
    tree = ast.parse(source)
    entries = _entries_node(tree)
    assert entries is not None, "meta-guard: _ENTRIES not found, the walk would be vacuous"
    assert _entry_string_failures(source) == []

    kind_key, _ = _first_inner(entries, "kind")
    planted_key = _insert_at(source, kind_key.lineno, kind_key.col_offset, '"proposer": "Rafael", ')
    ast.parse(planted_key)
    assert _entry_string_failures(_planted(tmp_path, source, planted_key, "key.py"))

    _, derivation = _first_inner(entries, "derivation")
    assert isinstance(derivation, ast.Constant) and isinstance(derivation.value, str)
    planted_phrase = _insert_at(
        source, derivation.lineno, derivation.col_offset + 1, phase35_prereg.FORBIDDEN_PHRASE
    )
    ast.parse(planted_phrase)
    assert _entry_string_failures(_planted(tmp_path, source, planted_phrase, "phrase.py"))

    assert real.read_bytes() == before


# =================================================================================================
# (5) CPU-ONLY AT IMPORT, AND ZERO SKIPS (D-13 / PREREG-08).
# =================================================================================================

_HEAVY = (
    "torch",
    "teach_persona",
    "phase19_erasure",
    "phase18_extraction",
    "phase23_run",
    "phase26_canary",
)


def test_the_prereg_imports_without_torch():
    probe = (
        "import sys; sys.path.insert(0, 'scripts'); import phase35_prereg; "
        f"print(*[name in sys.modules for name in {_HEAVY!r}])"
    )
    out = subprocess.run(
        [sys.executable, "-c", probe], cwd=_ROOT, capture_output=True, text=True, check=True
    )
    assert out.stdout.split() == ["False"] * len(_HEAVY), out.stdout


_SKIP_ATTRS = ("skip", "skipif", "importorskip", "xfail")


def _skip_failures(source):
    failures = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Attribute) and node.attr in _SKIP_ATTRS:
            failures.append(f"{node.attr} at line {node.lineno}")
        elif isinstance(node, ast.Name) and node.id == "_MPS_SKIP":
            failures.append(f"_MPS_SKIP at line {node.lineno}")
    return failures


def test_no_skips_in_this_file(tmp_path):
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert _skip_failures(source) == []
    planted = source + '\n\ndef test_planted():\n    pytest.skip("x")\n'
    assert _skip_failures(_planted(tmp_path, source, planted, "skip.py"))
