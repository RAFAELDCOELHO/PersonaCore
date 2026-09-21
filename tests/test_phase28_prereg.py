"""Plan 28-05: the standing expectation is quoted from its pinned commit and precedes every v4.0
result (D-04, D-05; SC1's "recorded before any run" as a CPU test).

Every ``phase28_report.QUOTES`` entry is present under ``_prose.normalized`` in its named source —
``git show <rev>:<path>`` for a ``git:`` source, the HEAD file otherwise. ``EXPECTATION_COMMIT`` is
a STRICT ancestor of the earliest first-add of every tracked ``results/phase2[0-8]_*`` file, with
the first-adds derived from git at test time (never hardcoded) and a shallow clone refused. The
mechanism is ``tests/test_phase27_prereg.py::_assert_frozen_before``'s, copied.
"""

import ast
import pathlib
import re
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
for _sub in ("scripts", "src"):
    if str(_ROOT / _sub) not in sys.path:
        sys.path.insert(0, str(_ROOT / _sub))

import _prose  # noqa: E402  (scripts/ is not a package)
import phase28_report  # noqa: E402

_PHASE27_TEST = _ROOT / "tests/test_phase27_prereg.py"
_V4_ARTIFACTS = "results/phase2[0-8]_*"
_SHALLOW_REFUSAL = (
    "shallow clone: the pre-registration commit objects are absent, so this guard cannot "
    "distinguish 'the ordering holds' from 'the ordering was never checked'. "
    "Set `fetch-depth: 0` on actions/checkout (see .github/workflows/ci.yml)."
)


def _git(*args):
    """Run git inside the repository and return its stdout, raising on a non-zero exit."""
    return subprocess.run(
        ("git", *args), cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def _assert_recorded_before(commit, tracked):
    """``commit`` is a STRICT ancestor of the earliest add of every path in ``tracked``."""
    assert _git("rev-parse", "--is-shallow-repository") == "false", _SHALLOW_REFUSAL
    full = _git("rev-parse", commit)
    assert tracked, "no tracked artifact — green and blind"
    checked = 0
    for artifact in tracked:
        adds = _git("log", "--diff-filter=A", "--format=%H", "--", artifact).split()
        # git log is newest-first, so the commit that ADDED the file is the last entry; taking the
        # earliest add is what makes a delete-and-re-add cycle unable to launder the ordering.
        first_add = adds[-1]
        assert first_add != full, (
            f"{commit} and {artifact} landed in the SAME commit — the expectation must precede "
            "the result STRICTLY (`git merge-base --is-ancestor X X` exits 0)"
        )
        subprocess.run(
            ("git", "merge-base", "--is-ancestor", full, first_add), cwd=_ROOT, check=True
        )
        checked += 1
    assert checked == len(tracked)


# =================================================================================================
# (1) D-04: EVERY QUOTE IS VERBATIM IN ITS SOURCE; THE EXPECTATION FROM THE PINNED COMMIT.
# =================================================================================================


def test_every_quote_is_verbatim_in_its_source():
    misses = []
    for name, (source, text) in phase28_report.QUOTES.items():
        if source.startswith("git:"):
            _, rev, path = source.split(":", 2)
            haystack = _git("show", f"{rev}:{path}")
        else:
            haystack = (_ROOT / source).read_text(encoding="utf-8")
        if _prose.normalized(text) not in _prose.normalized(haystack):
            misses.append(f"{name} <- {source}")
    assert not misses, misses
    pinned = f"git:{phase28_report.EXPECTATION_COMMIT}:"
    assert sum(src.startswith(pinned) for src, _ in phase28_report.QUOTES.values()) >= 2


def test_expectation_restated_at_milestone_level():
    """The key phrases are sliced out of the quotes by pattern, never typed here."""
    l8 = phase28_report.QUOTES["expectation_l8"][1]
    threshold = phase28_report.QUOTES["expectation_threshold"][1]
    fragments = [re.search(r"\d+σ", l8).group(0), re.search(r"σ ≥ [\d.]+", threshold).group(0)]
    assert len(fragments) == 2 and all(fragments)
    for rel in (phase28_report.REQUIREMENTS, phase28_report.ROADMAP):
        text = _prose.normalized((_ROOT / rel).read_text(encoding="utf-8"))
        absent = [f for f in fragments if _prose.normalized(f) not in text]
        assert not absent, (rel, absent)


# =================================================================================================
# (2) D-05: THE EXPECTATION COMMIT PRECEDES EVERY v4.0 RESULT — DERIVED, SHALLOW-REFUSING.
# =================================================================================================


def test_expectation_commit_precedes_every_v4_result():
    """Ancestry only. The quoted file may drift at HEAD (it is restated later in the same file);
    the quote check runs against the pinned commit, so byte-identity between c673b4c and HEAD is
    deliberately NOT required."""
    tracked = _git("ls-files", _V4_ARTIFACTS).split()
    _assert_recorded_before(phase28_report.EXPECTATION_COMMIT, tracked)


def test_ancestry_guard_refuses_a_shallow_clone_message_is_the_phase27_one():
    tree = ast.parse(_PHASE27_TEST.read_text(encoding="utf-8"))
    guard = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_assert_frozen_before"
    )
    theirs = [
        node.value
        for node in ast.walk(guard)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.startswith("shallow clone:")
    ]
    assert len(theirs) == 1
    assert _prose.normalized(_SHALLOW_REFUSAL) == _prose.normalized(theirs[0])


def test_a_planted_later_commit_is_red():
    """Conjunct (ii) watched failing: HEAD is not a strict ancestor of an old first-add."""
    tracked = _git("ls-files", _V4_ARTIFACTS).split()
    with pytest.raises(subprocess.CalledProcessError):
        _assert_recorded_before(_git("rev-parse", "HEAD"), [tracked[0]])
