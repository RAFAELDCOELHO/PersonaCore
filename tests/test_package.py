"""Install-parity smoke test (ENV-01) and the runtime dependency freeze (STAT-04, RPT-03)."""

import hashlib
import pathlib
import subprocess

import tomllib

_ROOT = pathlib.Path(__file__).resolve().parent.parent

# sha256 of pyproject.toml. STAT-04 freezes the whole file: a new extra, a widened version
# specifier and a new runtime dependency are all the same defect from this test's point of view.
# Updated in the same commit as `[project] license = "MIT"` (explicit reviewed decision; no
# dependency change).
PYPROJECT_SHA256 = "15ffd6b58e289447ac6460bdd6210c04d20d5ff5831f741bb3db3bdc0ca7926f"


def _git(*args):
    """Run git inside the repository and return its stdout, raising on a non-zero exit."""
    return subprocess.run(
        ("git", *args), cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def _deps(rev):
    return tomllib.loads(_git("show", f"{rev}:pyproject.toml"))["project"]["dependencies"]


def test_import_personacore():
    import personacore

    assert personacore is not None


def test_version_is_nonempty_string():
    import personacore

    assert isinstance(personacore.__version__, str)
    assert personacore.__version__ != ""


def test_runtime_dependencies_identical_across_four_milestones():
    """RPT-03 (Phase 28 D-25): zero new runtime dependencies across v1.0, v2.0, v3.0 and HEAD.

    The claim is the EQUALITY of `[project].dependencies` parsed from each tagged pyproject.toml
    with stdlib `tomllib`; the dependency names are deliberately not typed here.
    """
    assert _git("rev-parse", "--is-shallow-repository") == "false", (
        "shallow clone: the tagged pyproject.toml objects are absent, so this guard cannot "
        "distinguish 'the dependencies are identical' from 'the comparison was never made'. "
        "Set `fetch-depth: 0` on actions/checkout (see .github/workflows/ci.yml)."
    )
    tags = set(_git("tag", "-l").split())
    assert tags >= {"v1.0", "v2.0", "v3.0"}, (
        f"milestone tags missing from this clone (have {sorted(tags)}): a tagless clone must "
        "refuse loudly rather than pass vacuously. Set `fetch-depth: 0` on actions/checkout so "
        "tags are fetched."
    )
    head = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "dependencies"
    ]
    by_rev = {rev: _deps(rev) for rev in ("v1.0", "v2.0", "v3.0")}
    by_rev["HEAD"] = head
    assert by_rev["v1.0"] == by_rev["v2.0"] == by_rev["v3.0"] == head, (
        f"[project].dependencies drifted across milestones: {by_rev}. RPT-03 requires zero new "
        "runtime dependencies for a fourth milestone."
    )


def test_pyproject_sha256_pin_detects_any_change():
    """STAT-04 change detector: any byte of pyproject.toml changing turns a committed test red.

    This pin is a CHANGE DETECTOR, not RPT-03's proof — the four-milestone dependency equality is
    `test_runtime_dependencies_identical_across_four_milestones`. 2026-09-01, commit 5065bc5,
    added the single line `license = "MIT"` and re-pinned this constant in the same commit; the
    dependency table did not change — the reviewed decision stands.

    Read as BYTES, never as text: a text read normalizes line endings, so a CRLF rewrite of the
    dependency table would pass a text-mode hash while changing the file on disk.
    """
    actual = hashlib.sha256((_ROOT / "pyproject.toml").read_bytes()).hexdigest()
    assert actual == PYPROJECT_SHA256, (
        f"pyproject.toml changed: expected sha256 {PYPROJECT_SHA256}, got {actual}. "
        "This project has declined scipy in committed code twice (continual/fisher.py, "
        "scripts/phase15_stats.py), and every statistic since v3.0 is hand-rolled stdlib built on "
        "scripts/erasure_gate.py — taking a statistics dependency now would retcon both refusals. "
        "If the file genuinely must change, update PYPROJECT_SHA256 in the SAME commit as an "
        "explicit, reviewed decision — never silently."
    )
